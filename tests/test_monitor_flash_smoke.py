"""Browser smoke: wood-floor monitor overlay flashes when agents are working."""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_URL = os.environ.get(
    "AGENT_OFFICE_MONITOR_SMOKE_URL",
    "http://127.0.0.1:8000/static/monitor-flash-smoke.html",
)

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
    pg.set_default_timeout(20_000)
    yield pg
    pg.close()


def _open_smoke(page: Page) -> None:
    resp = page.goto(SMOKE_URL)
    if resp is None or resp.status >= 400:
        pytest.skip(f"Smoke page not available at {SMOKE_URL} (start UI on :8000)")
    page.wait_for_function("() => window.__monitorFlashReady === true", timeout=15_000)


@pytest.mark.parametrize("role", ["pm", "architect", "designer", "developer", "qa"])
def test_monitor_flash_per_desk(page: Page, role: str) -> None:
    _open_smoke(page)
    result = page.evaluate(
        """async (role) => await window.MonitorFlashSmoke.testRole(role)""",
        role,
    )
    assert result["ok"] is True, result.get("detail", role)


def test_monitor_flash_run_all(page: Page) -> None:
    _open_smoke(page)
    summary = page.evaluate("""async () => await window.MonitorFlashSmoke.runAll()""")
    assert summary["passed"] == summary["total"], summary.get("results")
