"""
TailorCV — FastAPI Backend
Serves the web UI and handles resume processing via the LangGraph pipeline.
"""

import asyncio
import json
import re
import uuid
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.graph import build_graph
from src.nodes import get_llm, _invoke_with_retry
from src.prompts import ATS_SCORE_PROMPT

app = FastAPI(title="TailorCV")

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/generate")
async def generate_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    model: str = Form("claude-sonnet-4-6"),
    base_url: str = Form("https://f5ai.pd.f5net.com/api"),
    api_key: str = Form(""),
    instructions: str = Form(""),
    threshold: int = Form(80),
    max_iterations: int = Form(3),
):
    """Process resume PDF + JD and stream progress events."""
    pdf_bytes = await resume.read()
    resume_text = extract_text_from_pdf(pdf_bytes)

    if not resume_text.strip():
        return StreamingResponse(
            _error_stream("Could not extract text from PDF. Ensure it's not a scanned image."),
            media_type="text/event-stream",
        )

    # Set API key in env if provided
    import os
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    job_id = uuid.uuid4().hex[:8]

    async def event_stream():
        yield _sse({"type": "status", "message": "Parsing resume PDF...", "step": "parse"})
        await asyncio.sleep(0.3)
        yield _sse({"type": "status", "message": f"Extracted {len(resume_text.split())} words from resume", "step": "parse_done"})
        await asyncio.sleep(0.2)
        yield _sse({"type": "status", "message": "Analyzing job description...", "step": "analyze_jd"})
        await asyncio.sleep(0.3)
        yield _sse({"type": "status", "message": "Scoring original resume against job description...", "step": "before_score"})

        # Score the ORIGINAL resume before optimization
        before_score = 0
        before_report = ""
        try:
            loop_pre = asyncio.get_event_loop()
            before_score, before_report = await loop_pre.run_in_executor(
                None, lambda: _score_original_resume(resume_text, job_description, model, base_url)
            )
            yield _sse({"type": "status", "message": f"Original ATS Score: {before_score}/100", "step": "before_score_done"})
        except Exception as e:
            yield _sse({"type": "status", "message": f"Could not score original resume: {e}", "step": "before_score_done"})

        await asyncio.sleep(0.2)
        yield _sse({"type": "status", "message": "Building LangGraph pipeline...", "step": "build"})
        await asyncio.sleep(0.2)

        graph = build_graph()
        initial_state = {
            "resume_text": resume_text,
            "job_description": job_description,
            "custom_instructions": instructions,
            "model_name": model,
            "base_url": base_url,
            "latex_sections": {},
            "full_latex": "",
            "ats_score": 0,
            "ats_report": "",
            "feedback": "",
            "iteration": 0,
            "max_iterations": max_iterations,
            "threshold": threshold,
        }

        yield _sse({"type": "status", "message": "Generating ATS-optimized resume...", "step": "generate"})

        final_state = None
        try:
            # Use a queue so the background thread can push events as each node finishes
            queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def run_pipeline():
                try:
                    for event in graph.stream(initial_state, stream_mode="updates"):
                        loop.call_soon_threadsafe(queue.put_nowait, ("event", event))
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
                except Exception as exc:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))

            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            executor.submit(run_pipeline)

            while True:
                msg_type, payload = await queue.get()

                if msg_type == "error":
                    yield _sse({"type": "error", "message": f"Pipeline error: {payload}"})
                    executor.shutdown(wait=False)
                    return

                if msg_type == "done":
                    break

                # msg_type == "event"
                event = payload
                for node_name, updates in event.items():
                    if node_name == "generate_resume":
                        iteration = updates.get("iteration", "?")
                        yield _sse({"type": "status", "message": f"Iteration {iteration}: Resume generated ✓", "step": "generated"})
                    elif node_name == "assemble_latex":
                        yield _sse({"type": "status", "message": "Assembling LaTeX document...", "step": "assemble"})
                    elif node_name == "score_resume":
                        score = updates.get("ats_score", 0)
                        yield _sse({"type": "status", "message": f"ATS Score: {score}/100", "step": "score"})
                    elif node_name == "prepare_feedback":
                        yield _sse({"type": "status", "message": "Score below threshold — preparing feedback for retry...", "step": "feedback"})
                    elif node_name == "finalize_output":
                        yield _sse({"type": "status", "message": "Finalizing output ✓", "step": "finalize"})

                for updates in event.values():
                    if final_state is None:
                        final_state = dict(initial_state)
                    if updates:
                        final_state.update(updates)

            executor.shutdown(wait=False)

        except Exception as e:
            yield _sse({"type": "error", "message": f"Pipeline error: {str(e)}"})
            return

        # Save output
        tex_path = OUTPUT_DIR / f"resume_{job_id}.tex"
        tex_path.write_text(final_state["full_latex"], encoding="utf-8")

        # Parse ATS report for keywords
        matched, missing = _parse_keywords(final_state.get("ats_report", ""))

        yield _sse({
            "type": "result",
            "ats_score": final_state["ats_score"],
            "before_score": before_score,
            "before_report": before_report,
            "ats_report": final_state["ats_report"],
            "latex": final_state["full_latex"],
            "iterations": final_state["iteration"],
            "matched_keywords": matched,
            "missing_keywords": missing,
            "download_id": job_id,
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/download/{job_id}")
async def download_tex(job_id: str):
    # Sanitize job_id to prevent path traversal
    if not re.match(r'^[a-f0-9]{8}$', job_id):
        return HTMLResponse("Invalid job ID", status_code=400)
    tex_path = OUTPUT_DIR / f"resume_{job_id}.tex"
    if not tex_path.exists():
        return HTMLResponse("File not found", status_code=404)
    return FileResponse(str(tex_path), filename="resume.tex", media_type="application/x-tex")


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _error_stream(msg: str):
    yield _sse({"type": "error", "message": msg})


def _score_original_resume(resume_text: str, job_description: str, model_name: str, base_url: str) -> tuple[int, str]:
    """Score the original resume text against the JD using the same ATS scoring prompt."""
    from langchain_core.messages import HumanMessage, SystemMessage
    llm = get_llm(model_name, base_url)
    prompt = ATS_SCORE_PROMPT.format(
        job_description=job_description,
        resume_latex=resume_text,
    )
    messages = [
        SystemMessage(content="IMPORTANT: Do NOT search for information. Do NOT use any tools. You are an expert ATS Resume Analyst. Evaluate the resume against the job description. Start your response with 'OVERALL_SCORE: ' followed by a number 0-100."),
        HumanMessage(content=prompt),
    ]
    report = _invoke_with_retry(llm, messages)
    score = 0
    for pattern in [
        r"OVERALL_SCORE:\s*(\d+)",
        r"Overall Score:\s*(\d+)\s*/\s*100",
        r"(\d+)\s*/\s*100",
    ]:
        match = re.search(pattern, report, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 < score <= 100:
                break
    return score, report


def _parse_keywords(report: str) -> tuple[list[str], list[str]]:
    """Extract matched and missing keywords from the ATS report."""
    matched = []
    missing = []

    matched_match = re.search(r"\*\*Matched Keywords?:\*\*\s*(.+?)(?:\n\*\*|\n---|\n##|\Z)", report, re.DOTALL)
    if matched_match:
        matched = [k.strip() for k in matched_match.group(1).split(",") if k.strip()]

    missing_match = re.search(r"\*\*Missing Keywords?:\*\*\s*(.+?)(?:\n\*\*|\n---|\n##|\Z)", report, re.DOTALL)
    if missing_match:
        missing = [k.strip() for k in missing_match.group(1).split(",") if k.strip()]

    return matched, missing


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
