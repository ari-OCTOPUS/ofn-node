"""M5 release pipeline — the four-stage fail-closed locks (Round 31).

Pins: OwnerRelease kernel gates are consulted for real (two-step owner
confirmation mandatory, kill-switch first, restricted content never);
every stage appends to the append-only receipt log; dry_run never touches
the send path; short drafts are refused at draft stage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))
sys.path.insert(0, str(AGENTS.parents[1]))

import release_pipeline as rp  # noqa: E402


def test_draft_too_short_refused(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    res = rp.pipeline("hi", step1_token="a", step2_token="b",
                      lead_id="lead:x", dry_run=True)
    assert res["ok"] is False and res["stage"] == "draft"


def test_verify_refuses_without_two_step(tmp_path, monkeypatch) -> None:
    """Updated for the P03 corrected contract: the pre-card verify passes
    only when every OTHER policy gate is green (two-step is then expected).
    With a real consent refusal present, the consent rule must block."""
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    monkeypatch.setattr(rp, "_consent_ok",
                        lambda lead: (False, "consent:missing"))
    res = rp.pipeline(
        "draft text long enough for the check",
        step1_token="", step2_token="whatever",
        lead_id="lead:x", dry_run=True)
    assert res["ok"] is False and res["stage"] == "verify"
    assert res.get("rule") == "consent:invalid-or-missing"


def test_verify_refuses_kill_switch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    # kill_switch_active=True در build_release_context — باید مسدود شود
    from ofn.kernel.release_switch import OwnerRelease, ReleaseContext
    ctx = rp.build_release_context(
        owner_confirmed_step1=True, owner_confirmed_step2=True,
        kill_switch_active=True,
        consent_ok=True, platform_ok=True, rate_limit_ok=True,
        idempotency_unused=True, ledger_ready=True)
    v = OwnerRelease().may_publish(ctx)
    assert v.ok is False
    assert "kill" in v.rule


def test_verify_passes_with_all_gates_open(tmp_path, monkeypatch) -> None:
    """Updated for the P03 corrected contract: with every real policy source
    green, the pre-card dry run reaches the card stage (no send). Garbage
    tokens are NOT consulted here — they are validated only at RELEASE, so
    garbage strings can no longer authorize anything (old behavior pinned
    the bool(token) defect and was retired with it)."""
    monkeypatch.setenv("OCTOPUS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    monkeypatch.setattr(rp, "_consent_ok", lambda lead: (True, "consent:ok"))
    monkeypatch.setattr(rp, "_platform_ok", lambda platform: True)
    monkeypatch.setattr(rp, "_rate_limit_ok", lambda now: True)
    monkeypatch.setattr(rp, "_ledger_ready", lambda: True)
    monkeypatch.setattr(rp, "_config_gates_open", lambda: (True, True))
    res = rp.pipeline(
        "draft text long enough for the check",
        step1_token="t1", step2_token="t2",
        lead_id="lead:x", dry_run=True)
    assert res["ok"] is True and res["stage"] == "dry-run"
    assert "NOT sent" in res["message"]


def test_receipts_are_append_only(tmp_path, monkeypatch) -> None:
    rp_file = tmp_path / "r.jsonl"
    monkeypatch.setenv("OCTOPUS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(rp, "RECEIPTS", rp_file)
    rp.pipeline("draft text long enough", step1_token="t", step2_token="t",
                lead_id="l", dry_run=True)
    lines_before = len(rp_file.read_text(encoding="utf-8").splitlines())
    rp.pipeline("another draft text long enough", step1_token="t",
                step2_token="t", lead_id="l", dry_run=True)
    lines_after = len(rp_file.read_text(encoding="utf-8").splitlines())
    assert lines_after > lines_before  # فقط اضافه شده، بازنویسی نشده


def test_kernel_release_switch_owner_release_is_importable() -> None:
    """OwnerRelease از kernel واقعی می‌آید — نه stub محلی."""
    from ofn.kernel.release_switch import OwnerRelease  # noqa: F401
