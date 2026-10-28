from typing import Any, Literal

from pydantic import BaseModel, Field

from llm import invoke_json
from skill_loader import load_cursor_skills_text
from memory import (
    list_workspace_files,
    load_private_memory,
    load_shared,
    load_soul,
    write_workspace_files,
)


class ScopeEscalation(BaseModel):
    """Send work back when the approved scope/plan does not match what is needed."""

    target: Literal["pm", "designer", "developer"]
    reason: str


ProjectType = Literal[
    "ui_ux",
    "fullstack_web",
    "backend_service",
    "api_only",
    "cli_tool",
    "data_script",
    "mixed",
]


class ArchitectureBrief(BaseModel):
    message_to_pm: str
    project_type: ProjectType
    summary: str
    delivery_shape: str
    recommended_stack: list[str] = Field(default_factory=list)
    system_components: list[str] = Field(default_factory=list)
    needs_designer: bool = True
    needs_ui_ux: bool = True
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    pm_discussion_points: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class ScopeAgreement(BaseModel):
    project_type: ProjectType
    aligned_summary: str
    needs_designer: bool
    skip_design_reason: str = ""
    technical_approach: str
    architect_response: str
    scope_locked: bool = False
    scope_resolved: bool = True
    risks: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class ArchitectScopeReply(BaseModel):
    message: str
    agrees_with_pm: bool = True
    project_type: ProjectType | None = None
    needs_designer: bool | None = None
    summary: str = ""
    memory_notes: list[str] = Field(default_factory=list)


class PmDiscovery(BaseModel):
    """Pre-plan intake: questions for the supervisor before drafting the contract plan."""

    message: str
    questions_for_human: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    goal: str
    requirements: list[str]
    scope: str
    out_of_scope: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    questions_for_human: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class DesignSpec(BaseModel):
    product_intent: str
    scope_ok: bool = True
    escalation: ScopeEscalation | None = None
    user_flows: list[str] = Field(default_factory=list)
    screens: list[str] = Field(default_factory=list)
    interaction_notes: list[str] = Field(default_factory=list)
    ui_copy: list[str] = Field(default_factory=list)
    accessibility: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class FileChange(BaseModel):
    path: str
    content: str


DevTestKind = Literal["unit", "component", "integration", "contract"]


class DevTestRecord(BaseModel):
    """Developer-owned automated test file (must also appear in files[])."""

    kind: DevTestKind
    path: str
    description: str = ""
    covers: str = ""


class Implementation(BaseModel):
    summary: str
    scope_ok: bool = True
    escalation: ScopeEscalation | None = None
    files: list[FileChange] = Field(default_factory=list)
    dev_tests: list[DevTestRecord] = Field(default_factory=list)
    tests_to_run: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    severity: str
    title: str
    detail: str


class TestMatrixRow(BaseModel):
    requirement: str
    test_case: str
    steps: str = ""
    expected: str = ""
    status: Literal["pass", "fail", "not_run", "manual"] = "not_run"
    evidence: str = ""


class AcCoverageRow(BaseModel):
    criterion: str
    met: bool
    evidence: str = ""


class AcVerification(BaseModel):
    all_ac_met: bool
    summary: str
    coverage: list[AcCoverageRow] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    return_to: Literal["developer", "qa"] = "developer"
    memory_notes: list[str] = Field(default_factory=list)


class QaReport(BaseModel):
    passed: bool
    summary: str
    scope_ok: bool = True
    escalation: ScopeEscalation | None = None
    test_plan: str = ""
    test_matrix: list[TestMatrixRow] = Field(default_factory=list)
    automation_files: list[FileChange] = Field(default_factory=list)
    tests_to_execute: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    missing_tests: list[str] = Field(default_factory=list)
    memory_notes: list[str] = Field(default_factory=list)


def _system(agent: str) -> str:
    soul = load_soul(agent)
    private = load_private_memory(agent)
    shared = load_shared()
    skills = load_cursor_skills_text(agent)
    skills_block = f"\n\n{skills}" if skills else ""
    return (
        f"You are the {agent.upper()} agent in a supervised multi-agent office.\n"
        "Follow your soul, private memory, and shared project knowledge.\n"
        "This call is a new session: the chat history is empty.\n"
        "Earlier mistakes and context exist only in private memory and shared lessons. Apply them. Do not repeat a recorded mistake.\n"
        "If this turn reveals a mistake or a constraint the next session must keep, add one short sentence to memory_notes.\n"
        "Do not claim to have taken an action that this runtime did not actually perform.\n"
        "Do not request production access, credentials, or unrestricted tools.\n\n"
        f"{soul}\n\n"
        "## Private memory\n\n"
        f"{private or '(empty)'}\n\n"
        "## Shared knowledge\n\n"
        f"{shared or '(empty)'}"
        f"{skills_block}"
    )


def run_pm_discovery(task: str) -> dict[str, Any]:
    return invoke_json(
        "pm",
        _system("pm"),
        (
            "Discovery mode (before the full plan): read this new task brief.\n"
            "Ask the human supervisor 1–4 short questions when the answer would change scope, "
            "acceptance criteria, or delivery shape (e.g. one HTML file vs multi-page, styling level, "
            "browser targets, data persistence).\n"
            "If the brief is already specific enough for a small prototype slice, leave "
            "questions_for_human empty and list working assumptions in assumptions.\n"
            "Write message as a direct note to the supervisor (2–4 sentences).\n\n"
            f"Task brief:\n{task}"
        ),
        PmDiscovery,
    )


def _brief_context(brief_answers: str, brief_assumptions: list[str]) -> str:
    parts: list[str] = []
    if brief_answers.strip():
        parts.append(f"Human briefing answers:\n{brief_answers.strip()}")
    if brief_assumptions:
        parts.append("PM working assumptions:\n" + "\n".join(f"- {a}" for a in brief_assumptions))
    return "\n\n".join(parts)


def run_architect_scope(
    task: str,
    brief_answers: str = "",
    brief_assumptions: list[str] | None = None,
) -> dict[str, Any]:
    ctx = _brief_context(brief_answers, brief_assumptions or [])
    extra = f"\n\n{ctx}" if ctx else ""
    return invoke_json(
        "architect",
        _system("architect"),
        (
            "Classify this assignment with the PM before they write the plan.\n"
            "Choose project_type: ui_ux (screens-first), fullstack_web, backend_service, "
            "api_only, cli_tool, data_script, or mixed.\n"
            "Set needs_designer=false when there is no meaningful UI/UX design work "
            "(CLI, pure backend, batch scripts, API-only with no UI slice).\n"
            "List pm_discussion_points the PM should confirm or adjust.\n"
            "Write message_to_pm as what you say to the PM in the scope huddle (2–4 sentences).\n\n"
            f"Task brief:\n{task}{extra}"
        ),
        ArchitectureBrief,
    )


def _dialogue_block(dialogue: list[dict[str, Any]] | None) -> str:
    if not dialogue:
        return ""
    lines = []
    for item in dialogue:
        if item.get("phase") != "scope":
            continue
        who = item.get("from", "?")
        text = (item.get("text") or "").strip()
        if text:
            lines.append(f"{who}: {text}")
    if not lines:
        return ""
    return "Scope huddle transcript:\n" + "\n".join(lines)


def run_architect_scope_reply(
    task: str,
    architecture_brief: dict[str, Any],
    scope_agreement: dict[str, Any],
    dialogue: list[dict[str, Any]] | None,
    brief_answers: str = "",
    brief_assumptions: list[str] | None = None,
) -> dict[str, Any]:
    ctx = _brief_context(brief_answers, brief_assumptions or [])
    extra = f"\n\n{ctx}" if ctx else ""
    transcript = _dialogue_block(dialogue)
    trans = f"\n\n{transcript}" if transcript else ""
    return invoke_json(
        "architect",
        _system("architect"),
        (
            "Continue the scope huddle with the PM. Reply to their last message.\n"
            "Set agrees_with_pm=true when you accept their project_type and needs_designer.\n"
            "If you disagree, set agrees_with_pm=false and explain in message; optionally set "
            "project_type or needs_designer to your recommendation.\n\n"
            f"Task:\n{task}{extra}{trans}\n\n"
            f"Your prior brief:\n{architecture_brief}\n\n"
            f"PM's latest scope proposal:\n{scope_agreement}"
        ),
        ArchitectScopeReply,
    )


def run_pm_scope_alignment(
    task: str,
    architecture_brief: dict[str, Any],
    brief_answers: str = "",
    brief_assumptions: list[str] | None = None,
    *,
    dialogue: list[dict[str, Any]] | None = None,
    scope_agreement: dict[str, Any] | None = None,
    architect_agrees: bool = True,
    force_lock: bool = False,
) -> dict[str, Any]:
    ctx = _brief_context(brief_answers, brief_assumptions or [])
    extra = f"\n\n{ctx}" if ctx else ""
    transcript = _dialogue_block(dialogue)
    trans = f"\n\n{transcript}" if transcript else ""
    lock_hint = (
        "\n\nYou MUST set scope_locked=true now (turn limit). Note any remaining disagreement in risks."
        if force_lock
        else ""
    )
    agree_hint = ""
    if scope_agreement and not architect_agrees:
        agree_hint = (
            "\n\nThe Architect disagreed with your last proposal. Adjust or defend, then either "
            "align (scope_locked=true) or set scope_resolved=false to continue the huddle."
        )
    return invoke_json(
        "pm",
        _system("pm"),
        (
            "Scope alignment with the Architect (before the full plan).\n"
            "Review the architect's brief, agree or adjust project_type and needs_designer, "
            "and write architect_response as your reply to the architect (2–5 sentences).\n"
            "aligned_summary should be the single sentence both of you agree on for delivery shape.\n"
            "Set scope_locked=true when you and the Architect are aligned and planning can start.\n"
            "Set scope_resolved=false only if the Architect must confirm a change you made.\n"
            "If you override needs_designer, explain in skip_design_reason.\n"
            f"{lock_hint}{agree_hint}\n\n"
            f"Task:\n{task}{extra}{trans}\n\n"
            f"Architect brief:\n{architecture_brief}"
        ),
        ScopeAgreement,
    )


def run_pm(
    task: str,
    feedback: str = "",
    *,
    architecture_brief: dict[str, Any] | None = None,
    scope_agreement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra = f"\n\nHuman feedback to incorporate:\n{feedback}" if feedback else ""
    scope_bits: list[str] = []
    if scope_agreement:
        scope_bits.append(f"Aligned scope with Architect:\n{scope_agreement}")
    if architecture_brief:
        scope_bits.append(f"Architecture brief:\n{architecture_brief}")
    scope_block = "\n\n".join(scope_bits)
    if scope_block:
        scope_block = f"\n\n{scope_block}\n\nHonor needs_designer and project_type from scope agreement."
    return invoke_json(
        "pm",
        _system("pm"),
        (
            f"Create a concise implementation plan for this task:\n{task}{extra}{scope_block}\n\n"
            "Acceptance criteria must be concrete and testable by QA without interpretation — "
            "the supervisor will review and sign them off in a meeting before design starts."
        ),
        Plan,
    )


def run_designer(task: str, plan: dict[str, Any], feedback: str = "") -> dict[str, Any]:
    extra = f"\n\nHuman or QA feedback:\n{feedback}" if feedback else ""
    return invoke_json(
        "designer",
        _system("designer"),
        (
            f"Task:\n{task}\n\nApproved or current plan:\n{plan}\n"
            "Produce a practical specification for the Developer.\n"
            "For web/UI work: screens, flows, copy, and interaction notes.\n"
            "For non-UI work (console apps, CLI scripts, pure Java/Python CLIs, batch jobs, APIs with no UI): "
            "do NOT set scope_ok=false. Document product_intent, operational user_flows (run commands), "
            "screens as ['Console output'] if needed, and interaction_notes for stdout/stderr and errors.\n"
            "Only escalate to PM (scope_ok=false, escalation.target=pm) when acceptance criteria contradict "
            "the brief or are untestable — not because the task has no graphical UI."
            f"{extra}"
        ),
        DesignSpec,
    )


def run_developer(
    thread_id: str,
    task: str,
    plan: dict[str, Any],
    design: dict[str, Any],
    feedback: str = "",
) -> dict[str, Any]:
    existing = list_workspace_files(thread_id)
    extra = f"\n\nFeedback to address:\n{feedback}" if feedback else ""
    result = invoke_json(
        "developer",
        _system("developer"),
        (
            f"Task:\n{task}\n\nPlan:\n{plan}\n\nDesign spec:\n{design}\n\n"
            f"Existing workspace files:\n{existing or '(none)'}\n"
            "Implement a small, complete prototype. Prefer a few focused files. "
            "Each file path must be relative to the thread workspace root "
            "(example: index.html, not workspace/thread/index.html). "
            "Do not invent secrets. "
            "Your entire reply must be valid JSON — if code is long, split across files but keep each "
            "files[].content modest so the JSON is not truncated. "
            "Match the plan stack (e.g. HTML/JS for web slices — do not switch to PHP unless the plan says so).\n\n"
            "You must add automated tests appropriate to the workspace layout and stack:\n"
            "- unit — pure functions, modules, classes (no I/O or DOM unless mocked).\n"
            "- component — UI widgets, DOM behavior, or CLI command handlers in isolation.\n"
            "- integration — multiple modules, file I/O, HTTP handlers, or scripts end-to-end locally.\n"
            "- contract — request/response shapes, API schemas, or CLI stdout contracts vs acceptance criteria.\n"
            "Place files under conventional folders when possible (e.g. tests/unit/, tests/component/, "
            "tests/integration/, tests/contract/, or __tests__/ for JS; tests/ for Python). "
            "Match existing project structure if the workspace already has one.\n"
            "Every dev_tests[] entry must reference a path you include in files[] with real test code. "
            "List runnable commands in tests_to_run (pytest, unittest, node --test, bash ./test.sh, etc.). "
            "Skip a kind only when truly N/A for this slice; say why in summary.\n"
            "If the plan or design spec scope is wrong, set scope_ok=false and escalation "
            "(target pm or designer) with a clear reason; do not write code for out-of-scope work."
            f"{extra}"
        ),
        Implementation,
    )
    esc = result.get("escalation")
    if esc and esc.get("target"):
        result["written"] = []
        return result
    written = write_workspace_files(thread_id, result.get("files") or [])
    result["written"] = written
    return result


def run_qa(
    thread_id: str,
    task: str,
    plan: dict[str, Any],
    design_spec: dict[str, Any],
    implementation_summary: str,
) -> dict[str, Any]:
    files = list_workspace_files(thread_id)
    listing = "\n\n".join(f"## {path}\n```\n{content}\n```" for path, content in files.items()) or "(no files)"
    return invoke_json(
        "qa",
        _system("qa"),
        (
            f"Task:\n{task}\n\nPlan / acceptance criteria:\n{plan}\n\n"
            f"Design spec:\n{design_spec or '(none)'}\n\n"
            f"Developer summary:\n{implementation_summary}\n\n"
            f"Workspace files:\n{listing}\n\n"
            "You are QA: produce a test plan, test matrix, and judgment for release.\n"
            "1. Write test_plan (markdown) covering scope, approach, and risks.\n"
            "2. Fill test_matrix rows mapped to acceptance criteria (status pass/fail/not_run/manual with evidence).\n"
            "3. Prefer running Developer-authored tests from dev_tests / tests/ when present; "
            "add automation_files only for extra QA-only checks. Paths relative to workspace root.\n"
            "4. List tests_to_execute: allowlisted shell commands the runtime will run after your report "
            "(python -m pytest, python -m unittest, bash ./test.sh, npm test, node script.js).\n"
            "5. Map every plan acceptance_criteria item to at least one test_matrix row with evidence.\n"
            "6. Set passed=true only if criteria are met and there are no high-severity issues.\n"
            "If failures are due to wrong scope or acceptance criteria (not implementation bugs), "
            "set scope_ok=false and escalation (target pm, designer, or developer) with a clear reason."
        ),
        QaReport,
    )


def run_pm_ac_verification(
    task: str,
    plan: dict[str, Any],
    test_results: dict[str, Any],
    implementation_summary: str,
) -> dict[str, Any]:
    ac = plan.get("acceptance_criteria") or []
    return invoke_json(
        "pm",
        _system("pm"),
        (
            f"Task:\n{task}\n\n"
            f"Signed-off acceptance criteria (your contract with QA and the supervisor):\n{ac}\n\n"
            f"QA test report (passed flag, test_matrix, validation_runs, findings, summary):\n{test_results}\n\n"
            f"Developer implementation summary:\n{implementation_summary}\n\n"
            "QA handed test results to you before human release. As PM, confirm every acceptance criterion "
            "is met using only QA evidence (matrix rows, validation runs, findings).\n"
            "Fill coverage[] with one row per acceptance criterion (met + evidence citing QA).\n"
            "Set all_ac_met=true only when each AC has clear passing evidence and QA passed is credible.\n"
            "If implementation is incomplete, set all_ac_met=false and return_to=developer.\n"
            "If QA evidence is fine but tests must be re-run without code changes, set return_to=qa.\n"
            "If the plan or AC were wrong but code matches the plan, set all_ac_met=false, return_to=developer, explain in gaps."
        ),
        AcVerification,
    )
