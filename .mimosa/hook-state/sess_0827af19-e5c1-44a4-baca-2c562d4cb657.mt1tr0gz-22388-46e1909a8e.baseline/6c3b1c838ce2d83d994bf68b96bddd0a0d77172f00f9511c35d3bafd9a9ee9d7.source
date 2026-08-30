#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mission_kernel — پروندهٔ واحدِ مأموریت: timeline/resume/fsck، فقط‌خواندنی.

سنجه‌ها رفتاری‌اند و روی state ِ ساختگیِ ایزوله (پارامترِ state_dir) — صفر
تماس با درختِ زنده. مهم‌ترین ناوردی: kernel **هیچ‌چیز نمی‌نویسد** و این را
با عکسِ قبل/بعدِ دایرکتوری می‌سنجیم، نه با ادعا.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import harness  # noqa: E402  (فقط برای run؛ kernel به env نیاز ندارد)
import mission_kernel as mk  # noqa: E402

CYC = "2026-07-31#1"
PID = f"{CYC}:kmk"
AID = "act:0123456789abcdef"


def _mkstate(*, receipt=True, verdict=True, memory=True, journal=True,
             mission=True) -> Path:
    st = Path(tempfile.mkdtemp(prefix="mk-state-"))
    (st / "prereg.jsonl").write_text(json.dumps({
        "schema": "prereg.v1", "cycle_id": CYC, "prereg_id": PID,
        "goal_key": "kmk", "direction": "جهت", "method_index": 0,
        "ts": "2026-07-31T10:00:00"}) + "\n", "utf-8")
    if journal:
        (st / "journal.jsonl").write_text(json.dumps({
            "schema": "test_cycle.v1", "cycle_id": CYC, "prereg_id": PID,
            "goal_key": "kmk"}) + "\n", "utf-8")
    if mission:
        (st / "missions.jsonl").write_text(json.dumps({
            "mission_id": "MIS-20260731-abc123", "cycle_id": CYC,
            "prereg_id": PID, "task_id": AID, "trace_id": "t" * 32,
            "status": "done"}) + "\n", "utf-8")
    if receipt:
        (st / "action-ledger.jsonl").write_text(json.dumps({
            "schema": "action-receipt.v1", "action_id": AID,
            "idempotency_key": f"{AID}:{'a' * 32}", "status": "EXECUTED"})
            + "\n", "utf-8")
    if verdict:
        (st / "verdicts.jsonl").write_text(json.dumps({
            "schema": "cycle_verdict.v1", "cycle_id": CYC, "prereg_id": PID,
            "verdict": "PASS", "reason": "target-met"}) + "\n", "utf-8")
    if memory:
        (st / "memory-consolidated.json").write_text(
            json.dumps({"cycle_ids": [CYC]}), "utf-8")
    return st


def _snapshot(st: Path) -> list:
    return sorted((p.name, p.stat().st_size) for p in st.rglob("*"))


# ── timeline ────────────────────────────────────────────────────────────────
def t_a_complete_cycle_yields_a_complete_timeline_with_joined_ids():
    st = _mkstate()
    tl = mk.timeline(CYC, state_dir=st)
    assert tl["complete"] is True and tl["gaps"] == [], tl
    ids = tl["ids"]
    assert ids["prereg_id"] == PID and ids["action_id"] == AID, ids
    assert ids["receipt_status"] == "EXECUTED", ids
    assert ids["verdict"] == "PASS" and ids["mission_status"] == "done", ids


def t_receipt_present_but_verdict_absent_is_pending_evaluation():
    """«ناتمام» با «گیرکرده» فرق دارد: بعد از receipt، نبودِ حکم یعنی هنوز
    due نشده — نه خرابی."""
    st = _mkstate(verdict=False, memory=False)
    rs = mk.resume_status(CYC, state_dir=st)
    assert rs["state"] == "PENDING_EVALUATION", rs
    assert rs["stopped_at"] == "verdict", rs


def t_a_cycle_that_died_before_the_mission_ledger_shows_the_exact_stage():
    st = _mkstate(mission=False, receipt=False, verdict=False, memory=False)
    rs = mk.resume_status(CYC, state_dir=st)
    assert rs["state"] == "INCOMPLETE", rs
    assert rs["stopped_at"] == "mission", rs


def t_unknown_cycle_is_honest_all_gaps():
    st = _mkstate()
    tl = mk.timeline("2020-01-01#0", state_dir=st)
    assert tl["complete"] is False and len(tl["gaps"]) == len(mk.STAGES), tl


# ── fsck ────────────────────────────────────────────────────────────────────
def t_fsck_is_green_on_a_consistent_chain():
    st = _mkstate()
    r = mk.fsck(state_dir=st)
    assert r["ok"] is True and r["problems"] == [], r
    assert r["legacy_unlinked"] == 0, r


def t_fsck_catches_a_done_mission_without_a_receipt():
    st = _mkstate(receipt=False)
    r = mk.fsck(state_dir=st)
    assert r["ok"] is False, r
    kinds = {p["kind"] for p in r["problems"]}
    assert "mission-done-without-receipt" in kinds, r


def t_fsck_catches_a_verdict_whose_prereg_never_existed():
    st = _mkstate()
    with open(st / "verdicts.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"cycle_id": "2026-07-31#2",
                            "prereg_id": "2026-07-31#2:ghost",
                            "verdict": "PASS"}) + "\n")
    r = mk.fsck(state_dir=st)
    assert r["ok"] is False, r
    kinds = {p["kind"] for p in r["problems"]}
    assert "verdict-prereg-missing" in kinds, r


def t_fsck_separates_legacy_unlinked_from_broken():
    """ردیفِ قدیمی بدونِ cycle_id واقعیتِ تاریخی است نه خرابی — نباید قرمز
    شود، باید شمرده شود."""
    st = _mkstate()
    with open(st / "missions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"mission_id": "MIS-legacy", "task_id": AID,
                            "trace_id": "u" * 32, "status": "done"}) + "\n")
    r = mk.fsck(state_dir=st)
    assert r["ok"] is True, r
    assert r["legacy_unlinked"] == 1, r


def t_corrupt_lines_are_skipped_not_fatal():
    st = _mkstate()
    with open(st / "missions.jsonl", "a", encoding="utf-8") as f:
        f.write("{broken\n")
    tl = mk.timeline(CYC, state_dir=st)
    assert tl["complete"] is True, tl


# ── ناوردیِ فقط‌خواندنی ─────────────────────────────────────────────────────
def t_the_kernel_never_writes_anything():
    st = _mkstate()
    before = _snapshot(st)
    mk.timeline(CYC, state_dir=st)
    mk.resume_status(CYC, state_dir=st)
    mk.fsck(state_dir=st)
    assert _snapshot(st) == before, "kernel ِ «فقط‌خواندنی» چیزی نوشت!"


def t_missing_state_dir_is_honest_emptiness_not_an_exception():
    ghost = Path(tempfile.mkdtemp(prefix="mk-ghost-")) / "nope"
    tl = mk.timeline(CYC, state_dir=ghost)
    assert tl["complete"] is False and len(tl["gaps"]) == len(mk.STAGES), tl
    r = mk.fsck(state_dir=ghost)
    assert r["ok"] is True and r["checked"]["prereg"] == 0, r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mission_kernel: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
