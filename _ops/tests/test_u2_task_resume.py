#!/usr/bin/env python3
"""U2 — same-task resume (lane U2-RESUME-20260907، سند مأموریت v4.1 §۱۱/§۱۵).

چه چیزی قفل می‌شود:
  ۱) سؤالِ دارایِ blocked_task_id بعد از پاسخِ مالک، دقیقاً یک‌بار wake می‌سازد
     (رویدادِ پایدارِ task.resume با idempotency_key؛ V4-A11/A05).
  ۲) پاسخِ تکراری/دوباره‌ریپلای، wake دوم نمی‌سازد.
  ۳) سؤالِ عادی (بدون task) resume ندارد — رفتار قدیمی دست‌نخورده.
  ۴) owner_reply_ok فقط chat_id ِ مالکِ شناخته‌شده را می‌پذیرد (fail-closed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS / "telegram_center"), str(_OPS / "budget"), str(_OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import events  # noqa: E402
import opslib  # noqa: E402
import question_budget as qb  # noqa: E402


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(opslib, "STATE_DIR", tmp_path)
    (tmp_path / "telegram").mkdir(exist_ok=True)
    monkeypatch.setattr(events, "LOG", tmp_path / "events.jsonl")


def _resume_events(tmp_path) -> list[dict]:
    p = tmp_path / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text("utf-8").splitlines()
            if l.strip() and json.loads(l).get("event_name") == "task.resume"]


def test_question_carries_task_fields_and_single_resume(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    r = qb.submit("آیا موجودی تازه کردی؟", context="shelf", goal="ziman",
                  blocked_task_id="leg.ziman.shelf-restock", blocker_version="v3")
    assert r and r["item"]["blocked_task_id"] == "leg.ziman.shelf-restock"
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    rec = qb.record_answer(qid, "آره، پنج مورد اضافه شد")
    assert rec is not None and rec["answer"].startswith("آره")
    rz = qb.take_resume(qid)
    assert rz is not None
    assert rz["schema"] == "task_resume.v1"
    assert rz["blocked_task_id"] == "leg.ziman.shelf-restock"
    assert rz["question_id"] == qid
    ev = _resume_events(tmp_path)
    assert len(ev) == 1
    assert ev[0]["idempotency_key"] == f"resume:{qid}"
    assert ev[0]["approval_state"] == "approved"
    assert "leg.ziman.shelf-restock" in ev[0]["summary"]


def test_duplicate_reply_never_wakes_twice(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    r = qb.submit("q?", blocked_task_id="task-x", blocker_version="v1")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    qb.record_answer(qid, "بله")
    assert qb.take_resume(qid) is not None
    # ریپلای دوباره روی همان سؤال (replay/duplicate):
    qb.record_answer(qid, "بله — تکراری")
    assert qb.take_resume(qid) is None
    assert len(_resume_events(tmp_path)) == 1


def test_plain_question_has_no_resume(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    r = qb.submit("سؤال عادی بدون task؟")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    qb.record_answer(qid, "جواب")
    assert qb.take_resume(qid) is None
    assert _resume_events(tmp_path) == []


def test_resume_requires_an_answer_first(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    r = qb.submit("قبل از جواب؟", blocked_task_id="task-y", blocker_version="v1")
    qid = r["item"]["id"]
    qb.mark_asked(qid)
    assert qb.take_resume(qid) is None      # هنوز پاسخی ثبت نشده
    qb.record_answer(qid, "حالا جواب")
    assert qb.take_resume(qid) is not None


def test_owner_reply_ok_fail_closed():
    assert qb.owner_reply_ok(6150431610, 6150431610) is True
    assert qb.owner_reply_ok(1111111111, 6150431610) is False   # شخص ثالث
    assert qb.owner_reply_ok(6150431610, None) is False         # مالک نامعلوم
    assert qb.owner_reply_ok(None, 6150431610) is False
