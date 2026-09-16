#!/usr/bin/env python3
"""Tests for lead_leg_inbox.py: create, dedup, list, get, atomicity.

$0 offline, stdlib-only, no network.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# -- env before any import --------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("lead-leg-inbox")

# Use _ops_self (worktree-local) for legs dir so new modules in this tree resolve.
# harness.REAL_VAULT only has committed code — lead_leg_inbox.py is new here.
_OPS_SELF = Path(__file__).resolve().parent.parent  # _ops/ (worktree)
_LEGS = _OPS_SELF / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import lead_leg_inbox  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_inbox_dir() -> Path:
    """Create a fresh temp dir and patch lead_leg_inbox to use it."""
    d = Path(tempfile.mkdtemp(prefix="lead-inbox-test-"))
    inbox = d / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    lead_leg_inbox._LEAD_INBOX_DIR = inbox
    return inbox


def _enable():
    os.environ["OCTOPUS_WIRE_LEAD_INBOX"] = "1"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def t_gate_off_returns_disabled():
    """When OCTOPUS_WIRE_LEAD_INBOX is not "1", all functions return disabled."""
    old = os.environ.pop("OCTOPUS_WIRE_LEAD_INBOX", None)
    try:
        r = lead_leg_inbox.register_lead("hello")
        assert r["ok"] is False and r["reason"] == "gate_off", r

        assert lead_leg_inbox.list_leads() == []
        assert lead_leg_inbox.get_lead("LD-000000000000") is None
    finally:
        if old is not None:
            os.environ["OCTOPUS_WIRE_LEAD_INBOX"] = old


def t_create_lead_writes_json():
    """register_lead creates a JSON file with correct schema."""
    _enable()
    inbox = _fresh_inbox_dir()

    r = lead_leg_inbox.register_lead("Need painting for 3-bedroom house")
    assert r["ok"] is True, r
    assert r["status"] == "new", r
    assert r["lead_id"].startswith("LD-"), r

    # Verify file exists and has correct schema
    fp = inbox / f"{r['lead_id']}.json"
    assert fp.is_file(), f"file not found: {fp}"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert data["lead_id"] == r["lead_id"]
    assert data["raw_text"] == "Need painting for 3-bedroom house"
    assert data["source"] == "telegram"
    assert data["status"] == "new"
    assert data["contact"] is None
    assert data["estimate"] is None
    assert data["trace_id"] is None
    assert "_nkey" in data  # internal key present


def t_create_lead_custom_source():
    """register_lead with source='email' stores the source correctly."""
    _enable()
    inbox = _fresh_inbox_dir()

    r = lead_leg_inbox.register_lead("Quote request from website", source="email")
    assert r["ok"] is True, r

    fp = inbox / f"{r['lead_id']}.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert data["source"] == "email"


def t_empty_text_fails():
    """register_lead with empty/whitespace text returns error."""
    _enable()
    _fresh_inbox_dir()

    for txt in ("", "   ", "\t\n"):
        r = lead_leg_inbox.register_lead(txt)
        assert r["ok"] is False, f"should fail for {repr(txt)}"
        assert r["reason"] == "empty_text", r


def t_dedup_within_24h():
    """Two calls with identical text within 24h return the same lead_id (dup)."""
    _enable()
    inbox = _fresh_inbox_dir()

    r1 = lead_leg_inbox.register_lead("Paint my apartment")
    assert r1["ok"] is True and r1["status"] == "new", r1

    r2 = lead_leg_inbox.register_lead("Paint my apartment")
    assert r2["ok"] is True, r2
    assert r2["status"] == "dup", r2
    assert r2["lead_id"] == r1["lead_id"], "should return same lead_id"

    # Only one file should exist
    files = list(inbox.glob("LD-*.json"))
    assert len(files) == 1, f"expected 1 file, got {len(files)}"


def t_dedup_normalization():
    """Dedup ignores case and extra whitespace."""
    _enable()
    inbox = _fresh_inbox_dir()

    r1 = lead_leg_inbox.register_lead("Paint my apartment")
    assert r1["status"] == "new", r1

    r2 = lead_leg_inbox.register_lead("  PAINT  MY   APARTMENT  ")
    assert r2["status"] == "dup", r2
    assert r2["lead_id"] == r1["lead_id"]


def t_dedup_different_text_creates_new():
    """Different text creates a new lead, not a dup."""
    _enable()
    inbox = _fresh_inbox_dir()

    r1 = lead_leg_inbox.register_lead("Paint my apartment")
    r2 = lead_leg_inbox.register_lead("Need electrician for house rewiring")
    assert r2["ok"] is True and r2["status"] == "new", r2
    assert r2["lead_id"] != r1["lead_id"]

    files = list(inbox.glob("LD-*.json"))
    assert len(files) == 2, f"expected 2 files, got {len(files)}"


def t_list_leads_all():
    """list_leads() returns all leads sorted by created_ts desc."""
    _enable()
    inbox = _fresh_inbox_dir()

    r1 = lead_leg_inbox.register_lead("Lead A")
    time.sleep(0.01)  # ensure different timestamps
    r2 = lead_leg_inbox.register_lead("Lead B")
    time.sleep(0.01)
    r3 = lead_leg_inbox.register_lead("Lead C")

    leads = lead_leg_inbox.list_leads()
    assert len(leads) == 3, f"expected 3, got {len(leads)}"
    # Newest first
    assert leads[0]["lead_id"] == r3["lead_id"], "newest first"
    assert leads[1]["lead_id"] == r2["lead_id"]
    assert leads[2]["lead_id"] == r1["lead_id"]
    # Internal key should be stripped
    assert "_nkey" not in leads[0]


def t_list_leads_filtered_by_status():
    """list_leads(status='new') only returns leads with that status."""
    _enable()
    inbox = _fresh_inbox_dir()

    r1 = lead_leg_inbox.register_lead("New lead")
    # Manually change one lead's status to simulate processing
    fp = inbox / f"{r1['lead_id']}.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    data["status"] = "contacted"
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    new_leads = lead_leg_inbox.list_leads(status="new")
    assert len(new_leads) == 0, "should be 0 new leads"

    contacted_leads = lead_leg_inbox.list_leads(status="contacted")
    assert len(contacted_leads) == 1, "should be 1 contacted lead"
    assert contacted_leads[0]["status"] == "contacted"


def t_get_lead_found():
    """get_lead returns the lead dict when found."""
    _enable()
    inbox = _fresh_inbox_dir()

    r = lead_leg_inbox.register_lead("Find me")
    got = lead_leg_inbox.get_lead(r["lead_id"])
    assert got is not None, "should find the lead"
    assert got["lead_id"] == r["lead_id"]
    assert got["raw_text"] == "Find me"
    assert got["status"] == "new"
    assert "_nkey" not in got, "internal key should be stripped"


def t_get_lead_not_found():
    """get_lead returns None for a non-existent lead_id."""
    _enable()
    _fresh_inbox_dir()

    got = lead_leg_inbox.get_lead("LD-nonexistent000")
    assert got is None


def t_atomicity_no_partial_write():
    """If the write directory doesn't exist, parents are created (atomic mkdir+write)."""
    _enable()
    bad_dir = Path(tempfile.mkdtemp(prefix="lead-atomic-")) / "nested" / "deep" / "inbox"
    lead_leg_inbox._LEAD_INBOX_DIR = bad_dir

    # Should succeed — _atomic_write_json creates parents via mkdir(parents=True)
    r = lead_leg_inbox.register_lead("Atomic test")
    assert r["ok"] is True, r
    assert bad_dir.is_dir(), "parent dirs should be created"
    assert (bad_dir / f"{r['lead_id']}.json").is_file()


def t_corrupt_file_skipped_in_list():
    """A corrupt JSON file in the inbox is silently skipped by list_leads."""
    _enable()
    inbox = _fresh_inbox_dir()

    # Register a valid lead
    r = lead_leg_inbox.register_lead("Valid lead")
    # Write a corrupt file
    (inbox / "LD-corruptfile.json").write_text("{not valid json}", encoding="utf-8")

    leads = lead_leg_inbox.list_leads()
    # Only the valid lead should appear (corrupt file skipped)
    assert len(leads) == 1, f"expected 1, got {len(leads)}"
    assert leads[0]["lead_id"] == r["lead_id"]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    failed = harness.run([
        ("gate_off_returns_disabled", t_gate_off_returns_disabled),
        ("create_lead_writes_json", t_create_lead_writes_json),
        ("create_lead_custom_source", t_create_lead_custom_source),
        ("empty_text_fails", t_empty_text_fails),
        ("dedup_within_24h", t_dedup_within_24h),
        ("dedup_normalization", t_dedup_normalization),
        ("dedup_different_text_creates_new", t_dedup_different_text_creates_new),
        ("list_leads_all", t_list_leads_all),
        ("list_leads_filtered_by_status", t_list_leads_filtered_by_status),
        ("get_lead_found", t_get_lead_found),
        ("get_lead_not_found", t_get_lead_not_found),
        ("atomicity_no_partial_write", t_atomicity_no_partial_write),
        ("corrupt_file_skipped_in_list", t_corrupt_file_skipped_in_list),
    ])
    total = 13
    print(f"\n{'PASS' if failed == 0 else 'FAIL'} test_lead_leg_inbox "
          f"({total - failed}/{total} green, {failed} red)")
    sys.exit(1 if failed else 0)
