"""Sanity checks for workflow-handoffs.json (animation contract with graph.py)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "static" / "workflow-handoffs.json").read_text(encoding="utf-8"))

VALID_AGENTS = {"pm", "architect", "designer", "developer", "qa", "human"}


def test_manifest_has_expected_scale():
    assert len(MANIFEST["parcel"]) >= 20
    assert len(MANIFEST["meetings"]) == 3
    assert len(MANIFEST["playthrough"]) >= 10


def test_parcel_entries_are_well_formed():
    ids = set()
    for p in MANIFEST["parcel"]:
        assert p["id"] not in ids
        ids.add(p["id"])
        assert p["from"] in VALID_AGENTS and p["to"] in VALID_AGENTS
        assert p["direction"] in ("forward", "return")
        assert p.get("phase")


def test_meeting_entries_are_well_formed():
    modes = {"", "ac_signoff", "release"}
    for m in MANIFEST["meetings"]:
        assert m["mode"] in modes
        assert m.get("lines")


def test_playthrough_references_known_ids():
    known = {p["id"] for p in MANIFEST["parcel"]} | {m["id"] for m in MANIFEST["meetings"]}
    for step in MANIFEST["playthrough"]:
        assert step in known, f"Unknown playthrough step: {step}"
