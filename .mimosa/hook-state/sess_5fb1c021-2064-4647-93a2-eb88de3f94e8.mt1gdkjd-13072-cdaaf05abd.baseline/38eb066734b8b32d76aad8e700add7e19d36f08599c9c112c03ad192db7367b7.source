#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_proposal_decision — تصمیمِ مالک روی پیشنهاد، از خودِ کاکپیت.

    زمینه (۲۰۲۶-۰۸-۰۵): کاکپیت شش پیشنهادِ منتظر را **نشان می‌داد** ولی در
    کلِ سیستم هیچ اقدامِ تأیید/ردی وجود نداشت — نه در مینی‌اپ، نه در
    `ALLOWED_ACTIONS`. یعنی صفحه ساختاراً تماشا بود و مالک درست می‌گفت
    «عملگرا نیست». GO ِ صریحِ مالک برای ساختِ این دو اقدام.

    ادعاهای زیرِ آزمون (هرکدام با جهشِ کُشنده روی لنگرِ یکتا):
      · تأیید/رد یک ردیفِ **تازه** اضافه می‌کند (append)، ردیفِ قبلی را
        دست نمی‌زند — منشور §۰.۱ «هرگز حذف نکن». تاریخچهٔ تصمیم خودش داده
        است: بدونش نمی‌شود گفت چند روز طول کشید.
      · بعد از تصمیم، پیشنهاد از صفِ `get_approvals_state` بیرون می‌رود —
        یعنی نوشتن و خواندن **واقعاً** به هم وصل‌اند، نه هرکدام جدا سبز.
      · تصمیمِ دوباره ⇒ BLOCKED، نه ردیفِ دومِ متناقض.
      · پیشنهادِ ناموجود ⇒ BLOCKED، نه ردیفِ یتیم.
      · نبودِ پایگاه ⇒ BLOCKED با دلیل، نه استثنا.

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("proposal-decision")

_COLS = ("event_id, idempotency_key, correlation_id, mission_id, proposal_id, "
         "leg_id, lead_id, event_type, verdict, value_aud_claimed, occurred_at, "
         "recorded_at, schema_version, payload_json")

OWNER = {"is_owner": True}


def _sandbox(rows=(("P-1", "lead", "delivered", None, "2026-07-23T04:00:00Z"),)):
    """پایگاهِ outcomes ِ موقت با اسکیمای واقعی + انبارِ ops ِ موقت."""
    d = Path(tempfile.mkdtemp(prefix="prop-"))
    (d / "_ops" / "state" / "outcomes").mkdir(parents=True)
    db = d / "_ops" / "state" / "outcomes" / "outcomes.db"
    c = sqlite3.connect(str(db))
    c.execute(f"CREATE TABLE outcomes({_COLS.replace(', ', ' TEXT, ')} TEXT)")
    for pid, leg, et, vd, ts in rows:
        c.execute("INSERT INTO outcomes(event_id,proposal_id,leg_id,event_type,"
                  "verdict,occurred_at) VALUES(?,?,?,?,?,?)",
                  (f"evt_{pid}_{et}", pid, leg, et, vd, ts))
    c.commit(); c.close()
    rt = d / "rt"; rt.mkdir()
    for k, v in (("OCTOPUS_OPS_RUNTIME_DIR", str(rt)),
                 ("OCTOPUS_OPS_DB_PATH", str(rt / "o.sqlite3")),
                 ("OCTOPUS_OPS_AUDIT_PATH", str(rt / "a.jsonl")),
                 ("OCTOPUS_OPS_IDEMPOTENCY_PATH", str(rt / "i.sqlite3")),
                 ("OCTOPUS_OUTCOMES_DB", str(db))):
        os.environ[k] = v
    from agi2027_control.ops_actions import OpsActionEngine
    return OpsActionEngine(root=d), db


def _rows(db):
    c = sqlite3.connect(str(db))
    try:
        return c.execute("SELECT proposal_id,event_type,verdict FROM outcomes "
                         "ORDER BY occurred_at").fetchall()
    finally:
        c.close()


def t_approve_appends_and_never_rewrites():
    """حکم **اضافه** می‌شود؛ ردیفِ delivered دست‌نخورده می‌ماند."""
    eng, db = _sandbox()
    before = _rows(db)
    r = eng.execute("proposal.approve", {"proposal_id": "P-1"}, OWNER, action_id="p1")
    eng.close()
    assert r.get("ok") is True, f"تأیید نشد: {r!r}"
    after = _rows(db)
    assert len(after) == len(before) + 1, f"ردیف اضافه نشد: {before} → {after}"
    assert before[0] in after, "ردیفِ قبلی بازنویسی شد — منشور می‌گوید هرگز حذف نکن"
    assert ("P-1", "owner-decision", "approved") in after, after


def t_reject_is_recorded_the_same_way():
    eng, db = _sandbox()
    r = eng.execute("proposal.reject", {"proposal_id": "P-1"}, OWNER, action_id="p2")
    eng.close()
    assert r.get("ok") is True, r
    assert ("P-1", "owner-decision", "rejected") in _rows(db)


def t_the_decision_actually_leaves_the_queue():
    """ادعای باربر: نوشتن و خواندن واقعاً به هم وصل‌اند.

    بدونِ این، هر دو طرف جدا سبز می‌شوند و مالک تپ می‌زند و پیشنهاد
    همان‌جا می‌ماند — همان «زدم و هیچ نشد» که این پروژه بارها خورده.
    """
    eng, db = _sandbox()
    import miniapp_state as ms
    saved = ms.STATE_DIR
    ms.STATE_DIR = db.parent.parent          # …/_ops/state
    try:
        assert ms.get_approvals_state()["count"] == 1, "صفِ اولیه یک نبود"
        eng.execute("proposal.approve", {"proposal_id": "P-1"}, OWNER, action_id="p3")
        assert ms.get_approvals_state()["count"] == 0, "بعد از تأیید هنوز در صف است"
    finally:
        ms.STATE_DIR = saved
        eng.close()


def t_deciding_twice_is_blocked_not_contradicted():
    eng, _ = _sandbox()
    eng.execute("proposal.approve", {"proposal_id": "P-1"}, OWNER, action_id="p4")
    second = eng.execute("proposal.reject", {"proposal_id": "P-1"}, OWNER, action_id="p5")
    eng.close()
    assert second.get("ok") is False, f"تصمیمِ متناقضِ دوم پذیرفته شد: {second!r}"
    assert second.get("reason") == "already_decided", second


def t_unknown_proposal_is_blocked_not_orphaned():
    eng, db = _sandbox()
    n = len(_rows(db))
    r = eng.execute("proposal.approve", {"proposal_id": "P-NOPE"}, OWNER, action_id="p6")
    eng.close()
    assert r.get("ok") is False and r.get("reason") == "proposal_not_found", r
    assert len(_rows(db)) == n, "برای پیشنهادِ ناموجود ردیفِ یتیم ساخت"


def t_missing_store_is_blocked_with_a_reason():
    """نبودِ پایگاه ⇒ BLOCKED ِ صادق، نه استثنا و نه موفقیتِ جعلی."""
    eng, db = _sandbox()
    os.environ["OCTOPUS_OUTCOMES_DB"] = str(db) + ".gone"
    r = eng.execute("proposal.approve", {"proposal_id": "P-1"}, OWNER, action_id="p7")
    eng.close()
    assert r.get("ok") is False, r
    assert r.get("reason") == "outcomes_db_missing", r


def t_both_decisions_are_allowlisted():
    from agi2027_control.ops_actions import ALLOWED_ACTIONS
    for a in ("proposal.approve", "proposal.reject"):
        assert a in ALLOWED_ACTIONS, f"{a} در allowlist نیست"


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_proposal_decision: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
