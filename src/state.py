from typing import TypedDict


class ResumeState(TypedDict):
    resume_text: str
    job_description: str
    custom_instructions: str
    model_name: str
    base_url: str
    latex_sections: dict[str, str]
    full_latex: str
    ats_score: int
    ats_report: str
    feedback: str
    iteration: int
    max_iterations: int
