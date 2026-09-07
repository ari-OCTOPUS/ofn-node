#!/usr/bin/env python3
"""U2 v3 tests — same-task resume with leg-pinned resolution + version auto-check + retryable failure."""
from __future__ import annotations
import json, sys
from pathlib import Path
_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS / "telegram_center"), str(_OPS / "budget"), str(_OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import events  # noqa: E402
import opslib  # noqa: E402
import question_budget as qb  # noqa: E402


def _iso(tmp_path, monkeypatch):
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    (tmp_path / "telegram").mkdir(exist_ok=True)
    monkeypatch.setattr(events, "LOG", tmp_path / "events.jsonl")


def _resume_events(tmp_path):
    p = tmp_path / "events.jsonl"
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text("utf-8").splitlines()
            if l.strip() and json.loads(l).get("event_name") == "task.resume"]


def test_question_carries_task_fields_and_single_resume(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    r = qb.submit("آیا؟", context="shelf", goal="ziman",
                  blocked_task_id="leg.ziman.shelf-restock", blocker_version="v3", leg="ziman")
    assert r["item"]["leg"] == "ziman"
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    rec = qb.record_answer(qid, "آره")
    assert rec is not None
    rz = qb.take_resume(qid)
    # بدون leg_tasks module در test-isolation، resolver پیدا نمی‌شود → retryable
    assert rz is not None
    assert rz["retryable"] is True  # answer NOT consumed; can retry


def test_duplicate_reply_wakes_once_or_retryable(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    r = qb.submit("q?", blocked_task_id="task-x", blocker_version="v1", leg="lead")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    qb.record_answer(qid, "بله")
    rz1 = qb.take_resume(qid)
    # v3: without real leg_tasks, resolver fails → retryable (NOT consumed)
    assert rz1 is not None and rz1.get("retryable") is True
    # answer NOT consumed → second call also gives retryable (not None)
    qb.record_answer(qid, "دوباره")
    rz2 = qb.take_resume(qid)
    assert rz2 is not None  # still retryable, not permanently consumed


def test_plain_question_no_resume(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    r = qb.submit("سؤال عادی بدون task؟")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    qb.record_answer(qid, "جواب")
    assert qb.take_resume(qid) is None


def test_stale_version_auto_blocked(tmp_path, monkeypatch):
    """v3: take_resume auto-finds newer question for same task → stale blocked."""
    _iso(tmp_path, monkeypatch)
    # v1 question
    r1 = qb.submit("نسخه ۱؟", blocked_task_id="task-stale", blocker_version="v1", leg="ziman")
    q1 = r1["item"]["id"]
    qb.mark_asked(q1)
    qb.record_answer(q1, "پاسخ قدیمی")
    # v2 question for the SAME task
    r2 = qb.submit("نسخه ۲؟", blocked_task_id="task-stale", blocker_version="v2", leg="ziman")
    q2 = r2["item"]["id"]
    qb.mark_asked(q2)
    # answering v1 (which has an answer) should be blocked as stale
    rz = qb.take_resume(q1)
    assert rz is not None and rz.get("rejected") is True
    assert "قدیمی" in rz.get("reject_reason", "") or "نسخه" in rz.get("reject_reason", "")


def test_current_version_answer_not_stale(tmp_path, monkeypatch):
    _iso(tmp_path, monkeypatch)
    r1 = qb.submit("v1؟", blocked_task_id="task-cur", blocker_version="v1", leg="ziman")
    q1 = r1["item"]["id"]
    qb.mark_asked(q1)
    r2 = qb.submit("v2؟", blocked_task_id="task-cur", blocker_version="v2", leg="ziman")
    q2 = r2["item"]["id"]
    qb.mark_asked(q2)
    qb.record_answer(q2, "پاسخ به نسخه جاری")
    rz = qb.take_resume(q2)
    # بدون real leg_tasks → retryable (نه رد نسخه‌ای)
    assert rz is not None and rz.get("rejected") is not True


def test_no_leg_returns_retryable_not_silent_success(tmp_path, monkeypatch):
    """v3: question without leg → resolver can't work → retryable with reason."""
    _iso(tmp_path, monkeypatch)
    r = qb.submit("بدون پای؟", blocked_task_id="task-noleg")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    qb.record_answer(qid, "بله")
    rz = qb.take_resume(qid)
    assert rz is not None and rz.get("retryable") is True
    assert rz.get("reject_reason") is not None


def test_owner_reply_ok_fail_closed():
    assert qb.owner_reply_ok(123, 123) is True
    assert qb.owner_reply_ok(111, 123) is False
    assert qb.owner_reply_ok(123, None) is False
    assert qb.owner_reply_ok(None, 123) is False
