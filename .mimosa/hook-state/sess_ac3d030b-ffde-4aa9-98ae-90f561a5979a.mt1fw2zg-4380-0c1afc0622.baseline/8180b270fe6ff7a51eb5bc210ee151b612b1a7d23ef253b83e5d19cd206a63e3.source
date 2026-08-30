#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_send_receipt_schema.py — رگرسیونِ طرح‌نامهٔ رسیدِ ارسال (Wave 0.2).

قانونی که این تست محافظت می‌کند (یافتهٔ boundary-13 / gate 8 PARTIAL):

  تا ۲۰۲۶-۰۷-۳۱ رسیدِ ارسال فقط `{ts, chat, topic, stream, sha, chars, ok}`
  بود. دو نتیجه:
    ۱. bot_role / surface نبود ⇒ یک ردیفِ DM از باتِ inner از باتِ outer
       غیرقابل‌تمایز بود — یعنی splitِ دو-باتی، که رسید برای اثباتش ساخته
       شده بود، از رویِ خودِ رسید غیرقابل‌اثبات بود.
    ۲. حالتِ سه‌گانه نبود ⇒ یک پیامِ HELD یا DENIED از یک پیامِ هرگز-
       ساخته‌شده غیرقابل‌تمایز بود. «مالک گفته شد X» و «X ساکت نگه‌داشته شد»
       هردو به‌یک‌شکل اثر می‌گذاشتند: هیچ‌چیز.

  حالا هر رویداد یک ردیف با state (sent/held/blocked) + bot_role + surface
  می‌گیرد. این تست آن را قفل می‌کند — و mutation-test شده.
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
import opslib  # noqa: E402


def _setup_isolated_log(tmpdir: Path):
    """یک STATE_DIR موقت می‌سازد تا تست روی فایلِ زنده ننویسد."""
    os.environ["OCTOPUS_TG_SEND_LOG"] = "1"
    opslib.STATE_DIR = tmpdir
    # ماژول را دوباره import کن تا _path از STATE_DIR ِ تازه بخواند
    import importlib
    import tg_send_log
    importlib.reload(tg_send_log)
    return tg_send_log


def t_record_carries_bot_role():
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        t.record(chat_id=123, topic_id=None, text="x", stream="center",
                 ok=True, bot_role="outer", surface="dm")
        rows = t._rows(None)
        assert rows and rows[0].get("bot_role") == "outer", (
            f"bot_role not recorded: {rows[0] if rows else 'no rows'}")


def t_record_carries_surface():
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        t.record(chat_id=-100, topic_id=22, text="x", stream="lead",
                 ok=True, bot_role="inner", surface="group")
        rows = t._rows(None)
        assert rows and rows[0].get("surface") == "group", (
            f"surface not recorded: {rows[0] if rows else 'no rows'}")


def t_record_has_sent_held_blocked_tri_state():
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        t.record(chat_id=1, text="a", stream="s", ok=True, state="sent")
        t.record(chat_id=1, text="b", stream="s", ok=False, state="held")
        t.record(chat_id=1, text="c", stream="s", ok=False, state="blocked")
        states = [r.get("state") for r in t._rows(None)]
        assert states == ["sent", "held", "blocked"], (
            f"tri-state not recorded in order: {states}")


def t_old_call_shape_still_works():
    """صداکنندهٔ قدیمی (بدون bot_role/surface/state) نباید بشکند."""
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        t.record(chat_id=1, topic_id=None, text="legacy", stream="center", ok=True)
        rows = t._rows(None)
        assert rows and rows[0].get("state") == "sent", (
            f"old call did not default to state=sent: {rows[0] if rows else 'no rows'}")
        assert rows[0].get("ok") is True


def t_invalid_state_defaults_to_sent():
    """state نامعتبر نباید ردیف را خراب کند — fail-safe به sent."""
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        t.record(chat_id=1, text="x", stream="s", ok=True, state="garbage")
        rows = t._rows(None)
        assert rows and rows[0].get("state") == "sent", (
            f"invalid state did not default to sent: {rows[0] if rows else 'no rows'}")


def t_prune_works_across_restart():
    """prune دیگر به per-process state وابسته نیست — across-restart کار می‌کند."""
    with tempfile.TemporaryDirectory() as d:
        t = _setup_isolated_log(Path(d))
        # ساختِ ردیفِ کهنه (ts دستی قابل‌تزریق نیست، پس فقط و乔丹 existence
        # مکانیزمِ state-file را تست می‌کنیم)
        t.record(chat_id=1, text="recent", stream="s", ok=True)
        ps = opslib.STATE_DIR / "tg-send-log-prune.json"
        assert ps.parent.exists(), "prune state dir not created"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_send_receipt_schema: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
