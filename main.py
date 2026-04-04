"""
TailorCV — LangGraph-powered ATS Resume Tailoring Pipeline

Usage:
    python main.py                                         # uses sample data
    python main.py --resume path/to/resume.txt --jd path/to/jd.txt
    python main.py --resume resume.txt --jd jd.txt --instructions "Focus on backend skills"
    python main.py --threshold 85 --max-iterations 3
"""

import argparse
import os
import sys
from pathlib import Path

from src.graph import build_graph


def load_text(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="TailorCV: ATS-optimized resume tailoring with LangGraph"
    )
    parser.add_argument(
        "--resume",
        default="data/sample_resume.txt",
        help="Path to the resume text file",
    )
    parser.add_argument(
        "--jd",
        default="data/sample_jd.txt",
        help="Path to the job description text file",
    )
    parser.add_argument(
        "--instructions",
        default="",
        help="Optional custom instructions for resume tailoring",
    )
    parser.add_argument(
        "--output",
        default="output/resume.tex",
        help="Output path for the generated LaTeX file",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=80,
        help="Minimum ATS score to accept (0-100, default: 80)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum generation attempts (default: 2)",
    )
    parser.add_argument(
        "--model",
        default="anthropic:claude-sonnet-4-6",
        help="Model name in provider:model format (default: anthropic:claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Custom API base URL (for corporate/proxy endpoints)",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="API key (alternative to environment variables)",
    )

    args = parser.parse_args()

    # Validate API key based on provider (only if not provided via --api-key)
    if not args.api_key:
        if args.base_url:
            # Custom endpoint uses OPENAI_API_KEY
            if not os.environ.get("OPENAI_API_KEY"):
                print("Error: Set the OPENAI_API_KEY environment variable for custom endpoints.")
                print("  export OPENAI_API_KEY='your-api-key-here'")
                print("  Or use --api-key flag")
                sys.exit(1)
        else:
            provider = args.model.split(":")[0] if ":" in args.model else "google_genai"
            api_key_map = {
                "google_genai": "GOOGLE_API_KEY",
                "google": "GOOGLE_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            required_key = api_key_map.get(provider, f"{provider.upper()}_API_KEY")
            if not os.environ.get(required_key):
                print(f"Error: Set the {required_key} environment variable.")
                print(f"  export {required_key}='your-api-key-here'")
                print(f"  Or use --api-key flag")
                sys.exit(1)

    resume_text = load_text(args.resume)
    jd_text = load_text(args.jd)

    print("=" * 60)
    print("TailorCV — ATS Resume Tailoring Pipeline")
    print("=" * 60)
    print(f"Resume:         {args.resume}")
    print(f"Job Description: {args.jd}")
    print(f"ATS Threshold:  {args.threshold}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Model:          {args.model}")
    print("=" * 60)

    # Build and run the graph
    graph = build_graph()

    initial_state = {
        "resume_text": resume_text,
        "job_description": jd_text,
        "custom_instructions": args.instructions,
        "model_name": args.model,
        "base_url": args.base_url,
        "api_key": args.api_key,
        "latex_sections": {},
        "full_latex": "",
        "ats_score": 0,
        "ats_report": "",
        "feedback": "",
        "iteration": 0,
        "max_iterations": args.max_iterations,
        "threshold": args.threshold,
    }

    print("\nRunning pipeline...\n")

    # Stream events and accumulate final state
    final_state = None
    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, updates in event.items():
            if node_name == "generate_resume":
                iteration = updates.get("iteration", "?")
                print(f"  [Iteration {iteration}] Resume generated")
            elif node_name == "assemble_latex":
                print("  [Assemble]    LaTeX document assembled")
            elif node_name == "score_resume":
                score = updates.get("ats_score", 0)
                print(f"  [ATS Score]   {score}/100")
            elif node_name == "prepare_feedback":
                print("  [Feedback]    Preparing improvement feedback for retry...")
            elif node_name == "finalize_output":
                print("  [Finalize]    Resume finalized")
        # Merge updates into running state
        for updates in event.values():
            if final_state is None:
                final_state = dict(initial_state)
            if updates:
                final_state.update(updates)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_state["full_latex"], encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"OUTPUT SAVED: {output_path}")
    print(f"ATS SCORE:    {final_state['ats_score']}/100")
    print(f"ITERATIONS:   {final_state['iteration']}")
    print(f"{'=' * 60}")

    # Print ATS report
    print(f"\n{'=' * 60}")
    print("ATS SCORE REPORT")
    print(f"{'=' * 60}")
    print(final_state["ats_report"])

    print(f"\nTo compile the LaTeX file to PDF:")
    print(f"  pdflatex {output_path}")


if __name__ == "__main__":
    main()
