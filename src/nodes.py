import re
import time

from langchain.chat_models import init_chat_model

from src.prompts import ATS_RESUME_PROMPT, ATS_SCORE_PROMPT, LATEX_PREAMBLE
from src.state import ResumeState

MAX_RETRIES = 3
RETRY_BASE_DELAY = 15  # seconds


def get_llm(model_name: str = "google_genai:gemini-2.5-flash-lite"):
    return init_chat_model(model_name, temperature=0.3)


def _invoke_with_retry(llm, prompt: str) -> str:
    """Invoke the LLM with automatic retry on rate-limit (429) errors."""
    for attempt in range(MAX_RETRIES):
        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"  [Rate limit] Waiting {wait}s before retry ({attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait)
            else:
                raise
    # Final attempt — let it raise if it fails
    response = llm.invoke(prompt)
    return response.content.strip()


def parse_inputs(state: ResumeState) -> dict:
    """Validate that resume and JD are present and initialize iteration tracking."""
    resume = state.get("resume_text", "").strip()
    jd = state.get("job_description", "").strip()

    if not resume:
        raise ValueError("Resume text is required.")
    if not jd:
        raise ValueError("Job description is required.")

    return {
        "iteration": state.get("iteration", 0),
        "max_iterations": state.get("max_iterations", 2),
        "custom_instructions": state.get("custom_instructions", ""),
        "feedback": state.get("feedback", ""),
    }


def generate_resume(state: ResumeState) -> dict:
    """Call the LLM with the ATS resume prompt to generate LaTeX sections."""
    llm = get_llm(state.get("model_name", "google_genai:gemini-2.5-flash-lite"))

    feedback_section = ""
    if state.get("feedback"):
        feedback_section = (
            "#### Previous ATS Evaluation Feedback (MUST address these):\n"
            f"{state['feedback']}\n\n"
            "You MUST incorporate the above feedback to improve the ATS score. "
            "Focus especially on missing keywords and the top improvement suggestions."
        )

    prompt = ATS_RESUME_PROMPT.format(
        job_description=state["job_description"],
        resume=state["resume_text"],
        custom_instructions=state.get("custom_instructions", "None"),
        feedback_section=feedback_section,
    )

    latex_body = _invoke_with_retry(llm, prompt)

    # Strip markdown code fences if present
    latex_body = re.sub(r"^```(?:latex)?\s*", "", latex_body)
    latex_body = re.sub(r"\s*```$", "", latex_body)

    return {
        "latex_sections": {"body": latex_body},
        "iteration": state.get("iteration", 0) + 1,
    }


def assemble_latex(state: ResumeState) -> dict:
    """Combine the LaTeX preamble with generated body into a full document."""
    body = state.get("latex_sections", {}).get("body", "")

    # If the body already contains \documentclass, use it as-is
    if r"\documentclass" in body:
        full_latex = body
    else:
        full_latex = LATEX_PREAMBLE + "\n" + body

    # Fix double-backslash LaTeX commands from LLM output
    full_latex = full_latex.replace("\\\\textbf", "\\textbf")
    full_latex = full_latex.replace("\\\\textit", "\\textit")
    full_latex = full_latex.replace("\\\\href", "\\href")
    full_latex = full_latex.replace("\\\\underline", "\\underline")

    # Ensure document ends properly
    if r"\end{document}" not in full_latex:
        full_latex += "\n\\end{document}\n"

    return {"full_latex": full_latex}


def score_resume(state: ResumeState) -> dict:
    """Call the LLM with the ATS scoring prompt to evaluate the generated resume."""
    llm = get_llm(state.get("model_name", "google_genai:gemini-2.5-flash-lite"))

    prompt = ATS_SCORE_PROMPT.format(
        job_description=state["job_description"],
        resume_latex=state["full_latex"],
    )

    report = _invoke_with_retry(llm, prompt)

    # Extract numeric score from the report
    score = 0
    score_match = re.search(r"OVERALL_SCORE:\s*(\d+)", report)
    if score_match:
        score = int(score_match.group(1))
    else:
        # Fallback: look for "Overall Score: XX / 100"
        score_match = re.search(r"Overall Score:\s*(\d+)\s*/\s*100", report)
        if score_match:
            score = int(score_match.group(1))

    return {
        "ats_score": score,
        "ats_report": report,
    }


def evaluate_score(state: ResumeState) -> str:
    """Decide whether to finalize or re-generate based on ATS score and iteration count."""
    score = state.get("ats_score", 0)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)

    if score >= 80 or iteration >= max_iterations:
        return "finalize"
    return "retry"


def prepare_feedback(state: ResumeState) -> dict:
    """Extract feedback from the ATS report to guide the next iteration."""
    return {
        "feedback": state.get("ats_report", ""),
    }


def finalize_output(state: ResumeState) -> dict:
    """Final node — the full_latex is ready. No-op passthrough."""
    return {}
