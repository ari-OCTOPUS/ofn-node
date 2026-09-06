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
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    res = rp.pipeline(
        "draft text long enough for the check",
        step1_token="", step2_token="whatever",
        lead_id="lead:x", dry_run=True)
    assert res["ok"] is False and res["stage"] == "verify"
    assert "owner" in res.get("rule", "") or "two" in res.get("rule", "")


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
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "r.jsonl")
    res = rp.pipeline(
        "draft text long enough for the check",
        step1_token="t1", step2_token="t2",
        lead_id="lead:x", dry_run=True)
    assert res["ok"] is True and res["stage"] == "dry-run"
    assert "NOT sent" in res["message"]


def test_receipts_are_append_only(tmp_path, monkeypatch) -> None:
    rp_file = tmp_path / "r.jsonl"
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
