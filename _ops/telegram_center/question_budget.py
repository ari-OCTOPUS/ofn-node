#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""question_budget — بودجهٔ ۳۰ سؤال/هفتهٔ اختاپوس از مالک (رأی ۲۴ منشور).

«هفته‌ای تا ۳۰ سؤال از مالک — برای بهتر مدیریت‌کردنِ همه‌چیز؛ انتخابِ سؤال‌ها
تصمیمِ خودش؛ چارچوب: اهدافِ مشترک (اهدافِ خودمون)، نه فقط اجرای دستور.»

مدل:
  · store: `STATE_DIR/telegram/question-budget.json`
    {"week": "YYYY-WNN", "used": int, "seq": int, "queue": [item, …]}
    item = {"id","q","context","goal","created","asked":bool,"asked_ts",
            "answer":str|None,"answered_ts"}
  · هفتهٔ ISO با isocalendar (نه strftime %V — روی ویندوز قابل‌اتکا نیست).
  · rollover: هفتهٔ نو ⇒ used=0؛ سؤال‌های queued ِ نپرسیده در صف می‌مانند.
  · «ثبت را گیت نکن، تحویل را»: submit همیشه ثبت می‌کند؛ فرستادنِ DM و گرفتنِ
    جواب کارِ لِینِ wiring است (پشتِ فلگ `OCTOPUS_TG_QBUDGET`، الگویِ callback:
    `qb:ans:<id>`) — این ماژول هیچ‌چیز نمی‌فرستد.

مرزها: صفر ارسال، صفر شبکه؛ نوشتنِ اتمی tmp+os.replace؛ ساعت تزریق‌پذیر
(`now=`)؛ state از `opslib.STATE_DIR` (تست‌ها با harness ایزوله‌اند).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent

WEEK_CAP = 30                                # رأی ۲۴ — سقفِ هفتگی
FLAG = "OCTOPUS_TG_QBUDGET"                  # فقط تحویل را گیت می‌کند، نه ثبت را


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _week_key(now: "float | None" = None) -> str:
    now = float(now if now is not None else time.time())
    y, w, _ = datetime.fromtimestamp(now).isocalendar()
    return f"{y}-W{int(w):02d}"


def _path() -> Path:
    try:
        import sys as _s
        if str(_HERE.parent) not in _s.path:
            _s.path.insert(0, str(_HERE.parent))
        import opslib
        base = Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        base = _HERE.parent / "state"
    return base / "telegram" / "question-budget.json"


def _load(now: "float | None" = None) -> dict:
    """store + rollover ِ هفتهٔ ISO (ذخیره نمی‌کند — ذخیره با عملِ mutating)."""
    d = {"week": _week_key(now), "used": 0, "seq": 0, "queue": []}
    try:
        raw = json.loads(_path().read_text("utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("queue"), list):
            d = raw
    except (OSError, ValueError):
        pass
    wk = _week_key(now)
    if d.get("week") != wk:                  # هفتهٔ نو: مصرف صفر، صف می‌ماند
        d["week"] = wk
        d["used"] = 0
    d.setdefault("used", 0)
    d.setdefault("seq", 0)
    d.setdefault("queue", [])
    return d


def _save(d: dict) -> bool:
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


def _find(d: dict, qid: str) -> "dict | None":
    for it in d.get("queue", []):
        if it.get("id") == qid:
            return it
    return None


# ── API ────────────────────────────────────────────────────────────────────
def submit(question: str, *, context: str = "", goal: str = "",
           now: "float | None" = None) -> "dict | None":
    """سؤالِ نو از سمتِ اختاپوس. بودجه داشت ⇒ status=asked و مصرف++؛
    نداشت ⇒ status=queued برای هفتهٔ بعد. خروجی: {"status","item","remaining"}."""
    q = str(question or "").strip()[:400]
    if not q:
        return None
    now = float(now if now is not None else time.time())
    d = _load(now)
    d["seq"] = int(d.get("seq", 0)) + 1
    has_budget = int(d.get("used", 0)) < WEEK_CAP
    item = {"id": f"Q-{d['seq']}", "q": q,
            "context": str(context or "")[:300],
            "goal": str(goal or "")[:200],
            "created": now, "asked": bool(has_budget),
            "asked_ts": now if has_budget else None,
            "answer": None, "answered_ts": None}
    if has_budget:
        d["used"] = int(d.get("used", 0)) + 1
    d["queue"].append(item)
    if not _save(d):
        return None
    return {"status": "asked" if has_budget else "queued",
            "item": dict(item), "remaining": WEEK_CAP - int(d["used"])}


def used(now: "float | None" = None) -> int:
    return int(_load(now).get("used", 0))


def remaining(now: "float | None" = None) -> int:
    return max(0, WEEK_CAP - used(now))


def pending(now: "float | None" = None) -> "dict | None":
    """قدیمی‌ترین سؤالِ نپرسیده — فقط وقتی بودجه هست. تحویل با wiring است؛
    بعد از ارسالِ موفق باید `mark_asked` صدا شود تا بودجه مصرف شود."""
    d = _load(now)
    if int(d.get("used", 0)) >= WEEK_CAP:
        return None
    for it in d.get("queue", []):
        if not it.get("asked"):
            return dict(it)
    return None


def mark_asked(qid: str, *, now: "float | None" = None) -> "dict | None":
    """سؤالِ صف‌شده تحویل شد ⇒ asked=True و مصرفِ بودجه. بودجه نبود ⇒ None
    (fail-closed: تحویلِ بی‌بودجه ثبت نمی‌شود که سقف دور نخورد)."""
    now = float(now if now is not None else time.time())
    d = _load(now)
    it = _find(d, str(qid))
    if it is None or it.get("asked"):
        return None
    if int(d.get("used", 0)) >= WEEK_CAP:
        return None
    it["asked"] = True
    it["asked_ts"] = now
    d["used"] = int(d.get("used", 0)) + 1
    return dict(it) if _save(d) else None


def record_answer(qid: str, answer_text: str, *,
                  now: "float | None" = None) -> "dict | None":
    """جوابِ مالک روی سؤال (wiring از ریپلای یا `qb:ans:<id>` می‌گیرد)."""
    a = str(answer_text or "").strip()[:600]
    if not a:
        return None
    now = float(now if now is not None else time.time())
    d = _load(now)
    it = _find(d, str(qid))
    if it is None:
        return None
    it["answer"] = a
    it["answered_ts"] = now
    return dict(it) if _save(d) else None


# ── رندر (متن، نه ارسال) — برای لِینِ wiring ───────────────────────────────
def question_text(item: dict) -> str:
    ctx = str(item.get("context") or "").strip()
    goal = str(item.get("goal") or "").strip()
    lines = [f"❓ <b>{item.get('id', '؟')}</b> — سؤالِ اختاپوس", "",
             str(item.get("q") or "")[:400]]
    if ctx:
        lines.append(f"زمینه: {ctx[:200]}")
    if goal:
        lines.append(f"هدف: {goal[:150]}")
    lines.append("\nبرای جواب به همین پیام ریپلای کن.")
    return "\n".join(lines)


def answer_callback_data(qid: str) -> str:
    """قراردادِ callback ِ لِینِ wiring: `qb:ans:<id>` (≤۶۴ بایت)."""
    return f"qb:ans:{qid}"[:64]
