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
           blocked_task_id: str = "", blocker_version: str = "",
           now: "float | None" = None) -> "dict | None":
    """سؤالِ نو از سمتِ اختاپوس **فقط ثبت می‌شود** — بودجه هنگامِ **تحویل**
    مصرف می‌شود (`mark_asked`)، نه این‌جا.

    ⚠️ ۲۰۲۶-۰۷-۳۱ (بلاکرِ B2 دیباگ): نسخهٔ اول این‌جا `asked=True` می‌گذاشت و
    بودجه را همین‌جا می‌سوزاند. نتیجهٔ ساختاری: تنها آیتم‌های `asked=False`
    وقتی ساخته می‌شدند که سقف پر شده باشد، و `pending()` دقیقاً در همان حالت
    کوتاه می‌آمد ⇒ **`pending()` در کلِ هفته همیشه None** و هیچ سؤالی هرگز به
    مالک نمی‌رسید. این همان درسِ ثبت‌شدهٔ «ثبت را گیت نکن، تحویل را» است.

    خروجی: {"status","item","remaining"} —
      queued   = در صف، بودجهٔ همین هفته را دارد (ضربانِ بعدی تحویلش می‌دهد)
      deferred = سقفِ هفته پر است؛ در صف می‌مانَد تا rollover ِ هفتهٔ بعد."""
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
            # U2 (2026-09-07, task_resume.v1): سؤالِ متولدشده از یک taskِ مسدود،
            # همان task را نشانه می‌رود تا پاسخِ مالک «همان کار» را بیدار کند.
            "blocked_task_id": str(blocked_task_id or "")[:120],
            "blocker_version": str(blocker_version or "")[:60],
            "created": now, "asked": False, "asked_ts": None,
            "answer": None, "answered_ts": None, "resumed_ts": None}
    d["queue"].append(item)
    if not _save(d):
        return None
    return {"status": "queued" if has_budget else "deferred",
            "item": dict(item), "remaining": WEEK_CAP - int(d.get("used", 0))}


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


# ── U2 (2026-09-07, task_resume.v1): پاسخ مالک → ادامهٔ همان task ──────────
TASK_RESUME_SCHEMA = "task_resume.v1"


def owner_reply_ok(chat_id, owner_chat_id) -> bool:
    """احرازِ پاسخ‌دهنده — فقط chat_id ِ مالکِ شناخته‌شده (fail-closed).
    ریپلایِ شخصِ ثالث/گروه، جوابِ پروژه را بازنویسی/ادامه نمی‌دهد (V4-A11)."""
    return bool(owner_chat_id) and str(chat_id) == str(owner_chat_id)


def take_resume(qid: str, *, now: "float | None" = None) -> "dict | None":
    """پاسخِ ثبت‌شدهٔ سؤالِ دارایِ blocked_task_id را **دقیقاً یک‌بار** به wake
    تبدیل می‌کند (idempotent: دوباره = None) و یک رویدادِ پایدارِ task.resume
    با idempotency_key می‌سازد. پاسخِ تکراری/قدیمی هرگز wake دوم نمی‌سازد."""
    now = float(now if now is not None else time.time())
    d = _load(now)
    it = _find(d, str(qid))
    if it is None or not it.get("blocked_task_id") or not it.get("answer"):
        return None
    if it.get("resumed_ts"):
        return None                     # قبلاً یک‌بار ادامه داده‌ایم
    it["resumed_ts"] = now
    payload = {"schema": TASK_RESUME_SCHEMA, "question_id": it["id"],
               "blocked_task_id": it.get("blocked_task_id", ""),
               "blocker_version": it.get("blocker_version", ""),
               "answered_ts": it.get("answered_ts"), "resumed_ts": now}
    ok = _save(d)
    try:                                # رسیدِ پایدار (fail-soft، بی‌محتوا)
        import sys as _sys
        _par = Path(__file__).resolve().parents[1]
        if str(_par) not in _sys.path:
            _sys.path.insert(0, str(_par))
        import events
        events.emit("task.resume", "question_budget",
                    summary=f"پاسخِ مالک روی {it['id']} — ادامهٔ {it.get('blocked_task_id', '')}",
                    status="completed",
                    next_action="gate recheck via leg engine",
                    approval_state="approved",
                    idempotency_key=f"resume:{it['id']}")
    except Exception:  # noqa: BLE001
        pass
    return payload if ok else None


# ── رندر (متن، نه ارسال) — برای لِینِ wiring ───────────────────────────────
def _esc(s: str) -> str:
    """⚠️ ۰۷-۳۱ (لِینِ ASKS): از وقتی `question_producers` هست، متنِ سؤال از
    artifactهای واقعی می‌آید — خطِ GOALS، متنِ Task، توضیحِ لید. این‌ها می‌توانند
    `<` یا `&` داشته باشند و مرکز با parse_mode=HTML می‌فرستد ⇒ یک `<` ِ
    بی‌گناه کلِ پیام را رد می‌کرد (نه خطا، نه پیام — سکوت). فقط تکه‌های
    داده‌ای escape می‌شوند؛ `<b>` ِ خودِ قالب دست‌نخورده می‌ماند."""
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def question_text(item: dict) -> str:
    ctx = str(item.get("context") or "").strip()
    goal = str(item.get("goal") or "").strip()
    lines = [f"❓ <b>{_esc(item.get('id', '؟'))}</b> — سؤالِ اختاپوس", "",
             _esc(str(item.get("q") or "")[:400])]
    if ctx:
        lines.append(f"زمینه: {_esc(ctx[:200])}")
    if goal:
        lines.append(f"هدف: {_esc(goal[:150])}")
    lines.append("\nبرای جواب به همین پیام ریپلای کن.")
    return "\n".join(lines)


def answer_callback_data(qid: str) -> str:
    """قراردادِ callback ِ لِینِ wiring: `qb:ans:<id>` (≤۶۴ بایت)."""
    return f"qb:ans:{qid}"[:64]
