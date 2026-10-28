"""Browser smoke tests for every workflow handoff in workflow-handoffs.json."""

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "static" / "workflow-handoffs.json"
SMOKE_URL = os.environ.get(
    "AGENT_OFFICE_SMOKE_URL",
    "http://127.0.0.1:8000/static/animation-smoke.html",
)

MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
PARCEL_CASES = MANIFEST["parcel"]
MEETING_CASES = MANIFEST["meetings"]


pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, sync_playwright  # noqa: E402


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser) -> Page:
    pg = browser.new_page()
    pg.set_default_timeout(12_000)
    yield pg
    pg.close()


def _open_smoke(page: Page) -> None:
    resp = page.goto(SMOKE_URL)
    if resp is None or resp.status >= 400:
        pytest.skip(f"Smoke page not available at {SMOKE_URL} (start UI: python main.py ui)")
    page.wait_for_function("() => window.__smokeReady === true", timeout=15_000)


@pytest.mark.parametrize("handoff", PARCEL_CASES, ids=lambda h: h["id"])
def test_workflow_parcel_handoff(page: Page, handoff: dict) -> None:
    _open_smoke(page)
    result = page.evaluate(
        """async (h) => {
          window.OfficeWorld.endMeeting?.();
          return await window.runWorkflowScenario(h.id);
        }""",
        handoff,
    )
    assert result["ok"] is True, result.get("detail", handoff["id"])


@pytest.mark.parametrize("meeting", MEETING_CASES, ids=lambda m: m["id"])
def test_workflow_meeting_gate(page: Page, meeting: dict) -> None:
    _open_smoke(page)
    result = page.evaluate(
        """async (m) => {
          window.OfficeWorld.endMeeting?.();
          return await window.runWorkflowScenario(m.id);
        }""",
        meeting,
    )
    assert result["ok"] is True, result.get("detail", meeting["id"])


def test_workflow_manifest_counts(page: Page) -> None:
    """Harness exposes the same manifest the tests use."""
    _open_smoke(page)
    counts = page.evaluate(
        """() => ({
          parcel: window.WORKFLOW_HANDOFF_MANIFEST.parcel.length,
          meetings: window.WORKFLOW_HANDOFF_MANIFEST.meetings.length,
        })"""
    )
    assert counts["parcel"] == len(PARCEL_CASES)
    assert counts["meetings"] == len(MEETING_CASES)
