"""Run allowlisted validation commands in a thread workspace."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from memory import workspace_for

MAX_OUTPUT = 12_000
TIMEOUT_SEC = 90

_ALLOWED = [
    re.compile(r"^python -m pytest(\s+[\w./:-]+)*$"),
    re.compile(r"^python -m unittest(\s+[\w./:-]+)*$"),
    re.compile(r"^python [\w./-]+\.py(\s+[\w./:-]+)*$"),
    re.compile(r"^bash \./[\w./-]+\.sh$"),
    re.compile(r"^npm (run )?test(\s+[\w:-]+)?$"),
    re.compile(r"^node [\w./-]+\.js(\s+[\w./:-]+)*$"),
]


def _command_allowed(cmd: str) -> bool:
    cmd = cmd.strip()
    if not cmd:
        return False
    if any(ch in cmd for ch in (";", "|", "&", ">", "<", "`", "$(")):
        return False
    return any(pat.match(cmd) for pat in _ALLOWED)


def discover_validation_commands(root: Path) -> list[str]:
    cmds: list[str] = []
    if list(root.glob("test_*.py")) or list(root.glob("**/tests/test_*.py")):
        cmds.append("python -m pytest -q")
    for name in ("test.sh", "run_tests.sh"):
        if (root / name).is_file():
            cmds.append(f"bash ./{name}")
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            if (data.get("scripts") or {}).get("test"):
                cmds.append("npm test")
        except (json.JSONDecodeError, OSError):
            pass
    return cmds


def run_validation(thread_id: str, extra_commands: list[str] | None = None) -> list[dict[str, Any]]:
    root = workspace_for(thread_id)
    commands: list[str] = []
    seen: set[str] = set()
    for cmd in list(extra_commands or []) + discover_validation_commands(root):
        cmd = cmd.strip()
        if not cmd or cmd in seen:
            continue
        if not _command_allowed(cmd):
            continue
        seen.add(cmd)
        commands.append(cmd)
    return [_run_one(cmd, root) for cmd in commands]


def _run_one(cmd: str, cwd: Path) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
        )
        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-MAX_OUTPUT:],
            "stderr": (proc.stderr or "")[-MAX_OUTPUT:],
            "passed": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": cmd,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Timed out after {TIMEOUT_SEC}s",
            "passed": False,
        }
    except OSError as exc:
        return {
            "command": cmd,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(exc),
            "passed": False,
        }


def matrix_markdown(matrix: list[dict[str, Any]]) -> str:
    lines = [
        "# Test matrix",
        "",
        "| Requirement | Test case | Steps | Expected | Status | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in matrix:
        lines.append(
            "| {requirement} | {test_case} | {steps} | {expected} | {status} | {evidence} |".format(
                requirement=_cell(row.get("requirement")),
                test_case=_cell(row.get("test_case")),
                steps=_cell(row.get("steps")),
                expected=_cell(row.get("expected")),
                status=_cell(row.get("status")),
                evidence=_cell(row.get("evidence")),
            )
        )
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")


def assess_validation_coverage(thread_id: str, report: dict[str, Any]) -> dict[str, Any]:
    """Fail closed when tests were expected but nothing ran."""
    root = workspace_for(thread_id)
    validations = list(report.get("validation_runs") or [])
    requested = [c.strip() for c in (report.get("tests_to_execute") or []) if str(c).strip()]
    discoverable = discover_validation_commands(root)
    has_py_tests = bool(list(root.glob("test_*.py")) or list(root.glob("**/tests/test_*.py")))
    has_shell = any((root / n).is_file() for n in ("test.sh", "run_tests.sh"))
    has_npm = (root / "package.json").is_file()

    if validations:
        failed = [v for v in validations if not v.get("passed")]
        if failed:
            return {
                "kind": "failed_runs",
                "escalate_to": "developer",
                "reason": "Automated validation commands failed; Developer must fix before QA can pass.",
            }
        return {"kind": "ok"}

    if requested:
        return {
            "kind": "blocked_commands",
            "escalate_to": "pm",
            "reason": (
                "QA listed tests_to_execute but the runtime could not run them (not allowlisted or missing). "
                "PM must align acceptance criteria with runnable commands; Developer must add the test harness."
            ),
        }

    if discoverable or has_py_tests or has_shell or has_npm:
        return {
            "kind": "not_executed",
            "escalate_to": "developer",
            "reason": (
                "The workspace has tests or scripts but no validation command ran. "
                "Developer must add/fix tests and tests_to_run; QA will re-run validations."
            ),
        }

    ac_count = len((report.get("test_matrix") or []))
    if ac_count and not validations:
        return {
            "kind": "manual_only",
            "escalate_to": "pm",
            "reason": (
                "Acceptance criteria were checked manually but no automated validation ran. "
                "PM should add testable AC or require Developer-owned automated tests."
            ),
        }
    return {"kind": "ok"}


def enrich_qa_report(thread_id: str, report: dict[str, Any]) -> dict[str, Any]:
    from memory import write_workspace_files

    automation = report.get("automation_files") or []
    if automation:
        report["automation_written"] = write_workspace_files(thread_id, automation)

    validations = run_validation(thread_id, report.get("tests_to_execute"))
    report["validation_runs"] = validations

    findings = list(report.get("findings") or [])
    for run in validations:
        if run.get("passed"):
            continue
        findings.append(
            {
                "severity": "high",
                "title": f"Validation failed: {run.get('command', 'command')}",
                "detail": (run.get("stderr") or run.get("stdout") or "Command exited with an error.")[:600],
            }
        )
    report["findings"] = findings
    if any((f.get("severity") or "").lower() == "high" for f in findings):
        report["passed"] = False

    report["qa_artifacts_written"] = persist_qa_artifacts(thread_id, report)
    report["validation_assessment"] = assess_validation_coverage(thread_id, report)
    assessment = report["validation_assessment"]
    if assessment.get("kind") != "ok":
        report["passed"] = False
        findings.append(
            {
                "severity": "high",
                "title": f"Validation gap: {assessment.get('kind')}",
                "detail": assessment.get("reason", "Tests could not be verified."),
            }
        )
        report["findings"] = findings
    return report


def persist_qa_artifacts(thread_id: str, report: dict[str, Any]) -> list[str]:
    from memory import write_workspace_files

    files: list[dict[str, str]] = []
    plan = (report.get("test_plan") or "").strip()
    if plan:
        files.append({"path": "qa/TEST_PLAN.md", "content": plan if plan.startswith("#") else f"# Test plan\n\n{plan}"})
    matrix = report.get("test_matrix") or []
    if matrix:
        files.append({"path": "qa/TEST_MATRIX.md", "content": matrix_markdown(matrix)})
    validations = report.get("validation_runs") or []
    if validations:
        lines = ["# Validation runs", ""]
        for run in validations:
            status = "PASS" if run.get("passed") else "FAIL"
            lines.append(f"## {status}: `{run.get('command', '')}`")
            if run.get("stdout"):
                lines.append(f"\n```\n{run['stdout']}\n```\n")
            if run.get("stderr"):
                lines.append(f"\nstderr:\n```\n{run['stderr']}\n```\n")
        files.append({"path": "qa/VALIDATION_RUNS.md", "content": "\n".join(lines)})
    if not files:
        return []
    return write_workspace_files(thread_id, files)
