from langgraph.graph import StateGraph, START, END

from src.nodes import (
    assemble_latex,
    evaluate_score,
    finalize_output,
    generate_resume,
    parse_inputs,
    prepare_feedback,
    score_resume,
)
from src.state import ResumeState


def build_graph() -> StateGraph:
    """
    Build the TailorCV LangGraph pipeline.

    Flow:
        START → parse_inputs → generate_resume → assemble_latex → score_resume
              → evaluate_score ─┬─ "finalize" → finalize_output → END
                                └─ "retry"    → prepare_feedback → generate_resume (loop)
    """
    graph = StateGraph(ResumeState)

    # Add nodes
    graph.add_node("parse_inputs", parse_inputs)
    graph.add_node("generate_resume", generate_resume)
    graph.add_node("assemble_latex", assemble_latex)
    graph.add_node("score_resume", score_resume)
    graph.add_node("prepare_feedback", prepare_feedback)
    graph.add_node("finalize_output", finalize_output)

    # Edges
    graph.add_edge(START, "parse_inputs")
    graph.add_edge("parse_inputs", "generate_resume")
    graph.add_edge("generate_resume", "assemble_latex")
    graph.add_edge("assemble_latex", "score_resume")

    # Conditional: score check → finalize or retry
    graph.add_conditional_edges(
        "score_resume",
        evaluate_score,
        {
            "finalize": "finalize_output",
            "retry": "prepare_feedback",
        },
    )

    graph.add_edge("prepare_feedback", "generate_resume")
    graph.add_edge("finalize_output", END)

    return graph.compile()
