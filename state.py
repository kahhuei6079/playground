from typing import Any, Literal, Optional, TypedDict


class FileChange(TypedDict):
    path: str
    content: str


class Finding(TypedDict, total=False):
    severity: str
    title: str
    detail: str


class OfficeState(TypedDict, total=False):
    task: str
    thread_id: str
    current_agent: str
    feedback: str

    brief_message: str
    brief_questions: list[str]
    brief_assumptions: list[str]
    brief_answers: str
    brief_confirmed: bool

    architecture_brief: dict[str, Any]
    scope_agreement: dict[str, Any]
    scope_locked: bool
    architect_agrees: bool
    dialogue: list[dict[str, Any]]

    plan: dict[str, Any]
    plan_approved: bool
    skip_plan_approval: bool
    return_to_after_pm: str

    design_spec: dict[str, Any]

    implementation_summary: str
    files_written: list[str]
    retry_count: int
    release_rejection_count: int
    scope_escalation_count: int
    escalation_from: str
    escalation: dict[str, Any]

    test_results: dict[str, Any]
    qa_passed: bool
    ac_verification: dict[str, Any]
    ac_verified: bool

    release_approved: bool
    release_triage: bool
    continue_run: bool
    status: Literal[
        "planning",
        "awaiting_brief",
        "scoping",
        "awaiting_plan_approval",
        "designing",
        "implementing",
        "testing",
        "verifying_ac",
        "awaiting_release",
        "released",
        "blocked",
        "revising",
    ]
    history: list[str]
    activity: list[dict[str, Any]]
