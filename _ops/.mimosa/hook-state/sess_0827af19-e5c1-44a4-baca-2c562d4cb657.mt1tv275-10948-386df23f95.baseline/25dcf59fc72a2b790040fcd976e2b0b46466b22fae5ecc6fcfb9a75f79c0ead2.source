#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_consolidate_shadow — تثبیتِ حافظه (episodic→semantic): درست کار می‌کند؟

سه ادعا (هرکدام سنجهٔ رفتاریِ باربر):
  ۱) **فلگ خاموش = no-op واقعی** — n_in=0, n_semantic=0, صفر نوشتن (نه «سبز
     به‌خاطرِ نبودِ خطا»). این دقیقاً همان چیزی است که امروز در پروسهٔ زنده
     رخ می‌دهد: CORTEX_CONSOLIDATE ست نیست → هر tick صفر کار.
  ۲) **فلگ روشن = تثبیتِ واقعی** — events تزریق‌شده → نوتِ سِمانتیک با
     salience>0 نوشته شد + آرشیوِ verbatim + cursor جلو رفت.
  ۳) **idempotency** — اجرایِ دوم روی همان events → صفر نوتِ نو (cursor کار کرد).

ریاضیِ تأییدشده (Generative Agents / Park ۲۰۲۳):
  salience = recency × importance × relevance
  recency  = 0.5^(age_h / halflife_h)
مهم: این تست consolidate.py را **لمس نمی‌کند** — فقط ثابت می‌کند وقتی فلگ روشن
بشه، درست کار می‌کنه. روشن‌کردنِ فلگ رأیِ مالک است (posture D).
"""
import json
import os
import sys
import time
from pathlib import Path

# ── هارنس: یک state-dir موقت پین می‌کند قبل از import (طوری که module-level
#    constantsِ consolidate به tmp اشاره کنند، نه به درختِ زنده) ──────────────
import harness
ENV = harness.setup("consolidate-shadow")

# نتایجِ harness.setup — OCTOPUS_STATE_DIR/OPS_DIR روی tmp نشسته
_LIVE_OPS = Path(__file__).resolve().parent.parent              # _ops واقعی (src)
_OPS = Path(os.environ.get("OPS_DIR", _LIVE_OPS))              # ممکن است tmp باشد
_STATE = Path(os.environ.get("OCTOPUS_STATE_DIR", _OPS / "state"))
_STATE.mkdir(parents=True, exist_ok=True)

# مهم: import از _ops واقعی (src)، نه از tmpِ هارنس (که cortex/ ندارد).
for _p in (str(_LIVE_OPS / "budget"), str(_LIVE_OPS), str(_LIVE_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import consolidate as c  # noqa: E402


class _Flag:
    def __init__(self, val):
        self.val = val

    def __enter__(self):
        self.old = os.environ.get("CORTEX_CONSOLIDATE")
        if self.val is None:
            os.environ.pop("CORTEX_CONSOLIDATE", None)
        else:
            os.environ["CORTEX_CONSOLIDATE"] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop("CORTEX_CONSOLIDATE", None)
        else:
            os.environ["CORTEX_CONSOLIDATE"] = self.old


def _reset_and_inject(events_log: Path, events: list[dict]) -> None:
    """یک events.jsonl تازه با رویدادهای داده‌شده بساز (پاک‌کردنِ کامل برای ایزوله‌سازی)."""
    events_log.parent.mkdir(parents=True, exist_ok=True)
    with open(events_log, "w", encoding="utf-8") as fh:   # 'w' = پاک‌کردن + نوشتن
        for ev in events:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _make_events(now: float, n: int = 5) -> list[dict]:
    """n رویداد: ترکیبی از incident/completed/heartbeat (اهمیت‌های متفاوت)."""
    return [
        {"ts": now - 100, "event_name": "incident.opened", "agent_id": "test-agent",
         "summary": "test incident for consolidate", "status": "alert",
         "approval_state": "", "next_action": "investigate", "trace_id": "t1"},
        {"ts": now - 200, "event_name": "task.failed", "agent_id": "test-agent",
         "summary": "test failure", "status": "failed", "trace_id": "t2"},
        {"ts": now - 300, "event_name": "task.completed", "agent_id": "test-agent",
         "summary": "test completion", "status": "ok", "trace_id": "t3"},
        {"ts": now - 400, "event_name": "system.heartbeat", "agent_id": "test-agent",
         "summary": "heartbeat", "status": "", "trace_id": ""},
        {"ts": now - 500, "event_name": "task.started", "agent_id": "test-agent",
         "summary": "start", "status": "", "trace_id": "t5"},
    ][:n]


def _clean_outputs() -> None:
    """خروجی‌هایِ نوت/آرشیو/cursor/events را پاک کن برای ایزوله‌سازیِ هر تست."""
    for p in (c.SEMANTIC, c.ARCHIVE, c.CURSOR, c.EVENTS_LOG):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


# ════════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش = no-op واقعی (امروزِ زنده)
# ════════════════════════════════════════════════════════════════════════════════
def t_flag_off_is_real_noop():
    """فلگ خاموش → n_in=0, n_semantic=0, archived=0 حتی با events موجود."""
    _clean_outputs()
    now = time.time()
    now = time.time()
    _reset_and_inject(c.EVENTS_LOG, _make_events(now))
    with _Flag(None):
        out = c.consolidate_once(now=now)
    assert out["flag"] is False, out
    assert out["n_in"] == 0, f"فلگ خاموش ولی n_in={out['n_in']} (no-op نیست!)"
    assert out["n_semantic"] == 0, out
    assert out["archived"] == 0, out
    # هیچ فایلِ semantic/archive نباید ساخته شده باشه
    assert not c.SEMANTIC.exists(), "فلگ خاموش نباید semantic بنویسد"
    assert not c.ARCHIVE.exists(), "فلگ خاموش نباید archive بنویسد"


# ════════════════════════════════════════════════════════════════════════════════
# (۲) فلگ روشن = تثبیتِ واقعی (ریاضیِ salience)
# ════════════════════════════════════════════════════════════════════════════════
def t_flag_on_consolidates_with_salience():
    """فلگ روشن → events → نوتِ سِمانتیک با salience>0 + آرشیوِ verbatim."""
    _clean_outputs()
    now = time.time()
    _reset_and_inject(c.EVENTS_LOG, _make_events(now, n=5))
    with _Flag("1"):
        out = c.consolidate_once(now=now)
    assert out["flag"] is True, out
    assert out["n_in"] == 5, f"باید ۵ رویداد بخورد: {out}"
    assert out["n_semantic"] > 0, f"باید حداقل یک نوتِ سِمانتیک بسازد: {out}"
    assert out["archived"] == 5, f"آرشیو باید ۵ خط verbatim داشته باشد: {out}"
    # نوتِ سِمانتیک واقعاً نوشته شد
    assert c.SEMANTIC.exists(), "semantic_memory.jsonl باید ساخته شود"
    notes = [json.loads(ln) for ln in c.SEMANTIC.read_text("utf-8").splitlines() if ln.strip()]
    assert len(notes) == out["n_semantic"], notes
    # ریاضیِ salience تأیید می‌شود: هر نوت salience>0 و ≤1 دارد
    for note in notes:
        assert 0.0 < note["salience"] <= 1.0, note
        assert note["schema"] == "semantic-memory.v1", note


def t_archived_is_verbatim_copy():
    """آرشیو = کپیِ verbatimِ خامِ events (حفظِ اصل، §۱ — هرگز حذف).

    نکته: consolidate خودش یک رویدادِ dashboard (agent=memory-consolidate) به
    events.jsonl اضافه می‌کند (رفتارِ صحیح، نه نشت). سنجهٔ واقعی: رویدادهایِ
    *اصلیِ تزریق‌شده* هنوز در events.jsonl حاضرند (آرشیو کپی است، نه move)."""
    _clean_outputs()
    now = time.time()
    evs = _make_events(now, n=3)
    _reset_and_inject(c.EVENTS_LOG, evs)
    with _Flag("1"):
        c.consolidate_once(now=now)
    # آرشیو باید خطوطِ خامِ verbatim باشد (کپیِ کاملِ رویدادهای تزریق‌شده)
    assert c.ARCHIVE.exists(), "archive باید ساخته شود"
    archived = [json.loads(ln) for ln in c.ARCHIVE.read_text("utf-8").splitlines() if ln.strip()]
    assert len(archived) == 3, archived
    # اصل: رویدادهایِ اصلی هنوز در events.jsonl حاضرند (حذف نشدند — آرشیو کپی است)
    all_events = [json.loads(ln) for ln in c.EVENTS_LOG.read_text("utf-8").splitlines() if ln.strip()]
    original_summaries = {e["summary"] for e in evs}
    present_summaries = {e.get("summary", "") for e in all_events}
    missing = original_summaries - present_summaries
    assert not missing, f"رویدادهایِ اصلی حذف شدند (آرشیو move است نه copy!): {missing}"


# ════════════════════════════════════════════════════════════════════════════════
# (۳) idempotency — cursor کار می‌کند (اجراهایِ تکراری صفر نوتِ نو)
# ════════════════════════════════════════════════════════════════════════════════
def t_cursor_makes_it_idempotent():
    """اجرایِ دوم روی همان events → صفر نوتِ نو (cursor جلو رفت)."""
    _clean_outputs()
    now = time.time()
    _reset_and_inject(c.EVENTS_LOG, _make_events(now, n=3))
    with _Flag("1"):
        first = c.consolidate_once(now=now)
        second = c.consolidate_once(now=now + 1)
    assert first["n_in"] == 3, first
    assert second["n_in"] == 0, f"اجراهایِ تکراری باید صفر باشه (idempotent): {second}"
    assert second["n_semantic"] == 0, second


def t_salience_math_incident_beats_heartbeat():
    """ریاضی: incident.opened (importance=1.0) از system.heartbeat (0.05) برجسته‌تر است."""
    now = time.time()
    inc = {"ts": now - 10, "event_name": "incident.opened", "agent_id": "x",
           "summary": "inc", "status": "alert", "trace_id": "t1", "next_action": "go"}
    hb = {"ts": now - 10, "event_name": "system.heartbeat", "agent_id": "x",
          "summary": "hb", "status": "", "trace_id": "", "next_action": ""}
    s_inc = c._salience(inc, now)
    s_hb = c._salience(hb, now)
    assert s_inc > s_hb, f"incident ({s_inc}) باید از heartbeat ({s_hb}) برجسته‌تر باشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_consolidate_shadow: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
