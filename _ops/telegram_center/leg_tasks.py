#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""leg_tasks — لایهٔ Task ِ گروهِ پاها (مدلِ مصوبِ مالک، ۲۰۲۶-۰۷-۳۰ شب).

    هر Topic = فقط یک پا · هر پیامِ مالک = یک کار · هر پا = یک کارتِ پین‌شدهٔ زنده

چهار وضعیت، نه بیشتر: QUEUED · WORKING · BLOCKED · DONE.
(لغو = DONE با نتیجهٔ «لغو شد» — وضعیتِ پنجم نمی‌سازیم.)

مرزها:
  · این ماژول **هیچ‌چیز نمی‌فرستد** و هیچ اثرِ بیرونی ندارد — فقط state ِ
    کارها و متنِ کارت/رسید. ارسال با مرکز است، اجرا با موتورِ هر پا.
  · موتورِ اجرای امروز: مغزِ read-only (ask_brain، محلی-اول) — مرکز در هر
    ضربان حداکثر یک کارِ WORKING از هر پا را به آن می‌دهد. هیچ ارسالِ
    بیرونی/خرجی از این مسیر ممکن نیست؛ pre-نویس‌ها فقط کارتِ تأیید در DM
    می‌سازند (مسیرِ approval ِ موجود).
  · اعتماد/درصد **جعل نمی‌شود** — اگر موتور عددِ سنجیده ندهد، رسید «—» می‌گوید.
  · state در `opslib.STATE_DIR/telegram/legs/` — harness ِ تست‌ها خودکار
    ایزوله‌اش می‌کند.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent

QUEUED, WORKING, BLOCKED, DONE = "QUEUED", "WORKING", "BLOCKED", "DONE"
_STATES = (QUEUED, WORKING, BLOCKED, DONE)
_CAP = 200                                   # سقفِ کارهای نگه‌داشته در هر پا

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# سؤال از کار جدا می‌شود: سؤال همان لحظه جواب می‌گیرد (مسیرِ موجودِ چت)،
# کار وارد صف می‌شود. علامت‌ها صریح‌اند نه حدسِ معنایی.
_QUESTION = re.compile(r"[؟?]\s*$|^(چرا|چی|چه|چطور|کی|کجا|آیا|الان)\b")


def _dir() -> Path:
    override = os.environ.get("OCTOPUS_LEG_TASKS_DIR", "").strip()
    if override:
        return Path(override)
    try:
        import sys as _s
        if str(_HERE.parent) not in _s.path:
            _s.path.insert(0, str(_HERE.parent))
        import opslib
        return Path(opslib.STATE_DIR) / "telegram" / "legs"
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state" / "telegram" / "legs"


def _path(leg: str) -> Path:
    safe = re.sub(r"[^a-z0-9_]", "", str(leg or "").lower()) or "unknown"
    return _dir() / f"{safe}-tasks.json"


def _load(leg: str) -> dict:
    try:
        d = json.loads(_path(leg).read_text("utf-8"))
        if isinstance(d, dict) and isinstance(d.get("tasks"), list):
            return d
    except (OSError, ValueError):
        pass
    return {"seq": 0, "tasks": []}


def _save(leg: str, d: dict) -> bool:
    try:
        p = _path(leg)
        p.parent.mkdir(parents=True, exist_ok=True)
        d["tasks"] = d.get("tasks", [])[-_CAP:]
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


def is_question(text: str) -> bool:
    return bool(_QUESTION.search(str(text or "").strip()))


# ── چرخهٔ عمر ──────────────────────────────────────────────────────────────
def add(leg: str, text: str, *, now: float | None = None) -> "dict | None":
    """پیامِ مالک → کارِ QUEUED. خروجی خودِ task است (برای کارتِ «ثبت شد»)."""
    now = float(now if now is not None else time.time())
    body = str(text or "").strip()[:600]
    if not body:
        return None
    d = _load(leg)
    d["seq"] = int(d.get("seq", 0)) + 1
    t = {"id": f"TASK-{d['seq']}", "text": body, "state": QUEUED,
         "created": now, "updated": now, "result": None, "evidence": None,
         "question": None}
    d["tasks"].append(t)
    return dict(t) if _save(leg, d) else None


def _find(d: dict, task_id: str) -> "dict | None":
    for t in d.get("tasks", []):
        if t.get("id") == task_id:
            return t
    return None


def set_state(leg: str, task_id: str, state: str, *, result=None,
              evidence=None, question=None,
              now: float | None = None) -> "dict | None":
    """گذارِ وضعیت — فقط به یکی از چهار وضعیتِ مصوب. گذارِ نامعتبر → None."""
    if state not in _STATES:
        return None
    now = float(now if now is not None else time.time())
    d = _load(leg)
    t = _find(d, task_id)
    if t is None:
        return None
    t["state"] = state
    t["updated"] = now
    if result is not None:
        t["result"] = str(result)[:400]
    if evidence is not None:
        t["evidence"] = str(evidence)[:800]
    if question is not None:
        t["question"] = str(question)[:300]
    return dict(t) if _save(leg, d) else None


def cancel(leg: str, task_id: str, *, now: float | None = None):
    return set_state(leg, task_id, DONE, result="لغو شد", now=now)


def claim_next(leg: str, *, now: float | None = None) -> "dict | None":
    """قدیمی‌ترین WORKING را بده (موتور در هر ضربان یکی برمی‌دارد).
    اگر WORKING نبود ولی QUEUED ِ startشده... نه — شروع فقط با دکمهٔ مالک."""
    d = _load(leg)
    for t in d.get("tasks", []):
        if t.get("state") == WORKING:
            return dict(t)
    return None


def start_next(leg: str, *, now: float | None = None) -> "dict | None":
    """قدیمی‌ترین QUEUED → WORKING («قدم بعدی» ِ مالک — همان اختیارِ دکمهٔ
    «شروع»، فقط بدونِ نامِ کار). QUEUED نبود → None."""
    d = _load(leg)
    for t in d.get("tasks", []):
        if t.get("state") == QUEUED:
            return set_state(leg, t["id"], WORKING, now=now)
    return None


def resolve_blocked(leg: str, task_id: str, answer: str, *,
                    now: float | None = None) -> "dict | None":
    """رفعِ مانع: جوابِ مالک به کارتِ 🚧 → همان کار برمی‌گردد به WORKING.

    بدونِ این، اطلاعاتِ تکمیلیِ مالک خودش یک TASK ِ نو می‌شد و کارِ
    BLOCKED برای همیشه گیر می‌مانْد. فقط روی BLOCKED اثر دارد (fail-closed:
    ریپلای به کارِ تمام‌شده چیزی را زنده نمی‌کند)."""
    a = str(answer or "").strip()
    if not a:
        return None
    now = float(now if now is not None else time.time())
    d = _load(leg)
    t = _find(d, task_id)
    if t is None or t.get("state") != BLOCKED:
        return None
    t["text"] = (str(t.get("text") or "") +
                 f"\n➕ اطلاعات مالک: {a[:300]}")[:600]
    t["state"] = WORKING
    t["question"] = None
    t["updated"] = now
    return dict(t) if _save(leg, d) else None


def record_feedback(leg: str, task_id: str, verdict: str, *, reason: str = "",
                    now: float | None = None) -> "dict | None":
    """رأیِ کیفیِ مالک روی خروجیِ یک کار (فاز ۲ بند ۱۱ — ۰۷-۳۱).

    به همان پا و همان کار سنجاق می‌شود، نه مجوزِ عمومی. علاوه بر خودِ task،
    یک خطِ append-only در `<leg>-feedback.jsonl` می‌نشیند تا بعداً درسِ
    per-leg از آن ساخته شود (خواندنش کارِ لایهٔ یادگیری است، نه این‌جا)."""
    if verdict not in ("good", "bad"):
        return None
    now = float(now if now is not None else time.time())
    d = _load(leg)
    t = _find(d, task_id)
    if t is None:
        return None
    t["feedback"] = {"v": verdict, "reason": str(reason or "")[:40], "ts": now}
    if not _save(leg, d):
        return None
    try:
        fp = _dir() / f"{_path(leg).stem.replace('-tasks', '')}-feedback.jsonl"
        with fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"task": task_id, "v": verdict,
                                "reason": str(reason or "")[:40], "ts": now,
                                "text": str(t.get("text") or "")[:120]},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass                                     # ثبتِ jsonl هرگز مسیر را نمی‌کشد
    return dict(t)


def queue(leg: str) -> list:
    d = _load(leg)
    return [dict(t) for t in d.get("tasks", []) if t.get("state") != DONE]


def recent_done(leg: str, n: int = 5) -> list:
    d = _load(leg)
    done = [t for t in d.get("tasks", []) if t.get("state") == DONE]
    return [dict(t) for t in done[-max(1, n):]][::-1]


# ── رندرها (متن، نه ارسال) ─────────────────────────────────────────────────
def _fa(n) -> str:
    return str(n).translate(_FA)


def _age(ts, now: float) -> str:
    try:
        m = max(0, int((now - float(ts)) / 60))
    except (TypeError, ValueError):
        return "؟"
    return f"{_fa(m)} دقیقه قبل" if m < 60 else f"{_fa(m // 60)} ساعت قبل"


def card_text(leg: str, *, paused: bool, now: float | None = None,
              kpi: "int | None" = None) -> str:
    """کارتِ پین‌شدهٔ زنده — دقیقاً قالبِ مصوب. فقط ویرایش می‌شود، سیل نمی‌سازد.

    `kpi` = هدفِ روزانهٔ مالک (فاز ۲ بند ۱۳). فقط وقتی مالک هدف گذاشته خط
    می‌گیرد — KPI ِ بی‌هدف عددسازی است، نه سنجه."""
    now = float(now if now is not None else time.time())
    d = _load(leg)
    tasks = d.get("tasks", [])
    working = [t for t in tasks if t.get("state") == WORKING]
    blocked = [t for t in tasks if t.get("state") == BLOCKED]
    queued = [t for t in tasks if t.get("state") == QUEUED]
    day0 = now - 86400
    today = [t for t in tasks if float(t.get("updated", 0)) >= day0]
    done_today = [t for t in today if t.get("state") == DONE
                  and t.get("result") != "لغو شد"]

    if paused:
        status = "⏸ متوقف (با دکمهٔ ادامه برمی‌گردد)"
    elif blocked:
        status = "🚧 نیازمندِ تو"
    elif working:
        status = "در حال کار"
    elif queued:
        status = "در صف — با «شروع» راه می‌افتد"
    else:
        status = "بیکار — پیامت را به کار تبدیل می‌کنم"

    cur = working[0]["text"][:60] if working else (
        blocked[0]["text"][:60] if blocked else "—")
    total_today = len([t for t in today if t.get("state") in
                       (WORKING, DONE)]) or len(today)
    lines = [f"🦵 <b>{leg}</b>", "",
             f"وضعیت: {status}",
             f"کار فعلی: {cur}",
             f"پیشرفت: {_fa(len(done_today))}/{_fa(max(total_today, len(done_today)))}",
             *([f"KPI امروز: {_fa(len(done_today))}/{_fa(int(kpi))}"]
               if isinstance(kpi, int) and kpi > 0 else []),
             f"نتیجه معتبر: {_fa(len(done_today))}",
             f"مانع: {blocked[0].get('question') or '—' if blocked else '—'}",
             f"در صف: {_fa(len(queued))}",
             f"آخرین فعالیت: {_age(max((t.get('updated', 0) for t in tasks), default=0), now) if tasks else '—'}"]
    return "\n".join(lines)


def card_keyboard(leg: str) -> list:
    """چهار دکمه — نه بیشتر. ≤۶۴ بایت."""
    return [[{"text": "▶️ ادامه", "callback_data": f"tk:c:{leg}"[:64]},
             {"text": "📋 صف", "callback_data": f"tk:q:{leg}"[:64]}],
            [{"text": "⏸ توقف", "callback_data": f"tk:p:{leg}"[:64]},
             {"text": "✅ نتیجه", "callback_data": f"tk:r:{leg}"[:64]}]]


def intake_text(t: dict) -> str:
    return (f"📥 کار ثبت شد: <b>{t['id']}</b>\n{t['text'][:160]}")


def intake_keyboard(leg: str, t: dict) -> list:
    return [[{"text": "شروع", "callback_data": f"tk:s:{leg}:{t['id']}"[:64]},
             {"text": "لغو", "callback_data": f"tk:x:{leg}:{t['id']}"[:64]}]]


def receipt_text(t: dict) -> str:
    """رسیدِ پایانِ کار — خرج و ارسالِ بیرونی همیشه حقیقتِ این مسیرند:
    موتورِ read-only است، پس «صفر» و «انجام نشد» ادعا نیست، ساختار است."""
    conf = "—"                                   # عددِ اعتمادِ جعلی ممنوع
    ev = (t.get("evidence") or "").strip()
    return (f"✅ <b>{t['id']}</b> تمام شد\n\n"
            f"نتیجه: {(t.get('result') or '—')[:200]}\n"
            f"اعتماد: {conf}\n"
            f"شاهد: {(ev[:220] + '…') if len(ev) > 220 else (ev or '—')}\n"
            f"خرج: صفر\n"
            f"ارسال بیرونی: انجام نشد")


def receipt_keyboard(leg: str, t: dict) -> list:
    """دو دکمهٔ رأیِ کیفی روی هر رسید (بند ۱۱) — بازخورد به همان کار سنجاق."""
    return [[{"text": "✅ خوب بود", "callback_data": f"tk:g:{leg}:{t['id']}"[:64]},
             {"text": "❌ بد بود", "callback_data": f"tk:b:{leg}:{t['id']}"[:64]}]]


# کدهای دلیلِ «بد بود» — بسته و کوتاه تا در ۶۴ بایتِ callback جا بگیرد.
FEEDBACK_REASONS = {
    "d": "داده اشتباه", "i": "نتیجه بی‌ربط", "w": "شاهد ضعیف",
    "l": "خیلی طولانی", "a": "اقدام اشتباه",
}


def bad_feedback_keyboard(leg: str, t: dict) -> list:
    rows, row = [], []
    for code, label in FEEDBACK_REASONS.items():
        row.append({"text": label,
                    "callback_data": f"tk:br:{leg}:{t['id']}:{code}"[:64]})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def blocked_text(t: dict) -> str:
    return (f"🚧 <b>{t['id']}</b> — برای ادامه اطلاعات کافی ندارم.\n\n"
            f"نیاز دارم:\n{(t.get('question') or 'توضیحِ بیشتر')[:200]}")


def blocked_keyboard(leg: str, t: dict) -> list:
    return [[{"text": "با اطلاعات فعلی ادامه بده",
              "callback_data": f"tk:s:{leg}:{t['id']}"[:64]}],
            [{"text": "لغو", "callback_data": f"tk:x:{leg}:{t['id']}"[:64]}]]


def blockers_text(leg: str) -> str:
    """فهرستِ موانعِ باز — پاسخِ «مانع چیست». مانعی نبود → همین را صادقانه بگو."""
    rows = [t for t in _load(leg).get("tasks", [])
            if t.get("state") == BLOCKED]
    if not rows:
        return "🚧 مانعی ثبت نشده."
    lines = ["🚧 <b>موانع باز</b>"]
    for t in rows[:8]:
        q = (t.get("question") or "توضیحِ بیشتر لازم است")[:120]
        lines.append(f"· {t['id']}: {q}")
    lines.append("\nبرای رفع، به کارتِ 🚧 همان کار ریپلای کن و اطلاعات را بنویس.")
    return "\n".join(lines)


def daily_report_text(leg: str, *, now: float | None = None) -> str:
    """گزارشِ روزانهٔ یک پا از حقیقتِ Taskها (پنجرهٔ ۲۴ ساعت).

    قراردادِ سکوت: هیچ کاری در پنجره لمس نشده ⇒ "" — دایجست پیامِ خالی
    نمی‌سازد. خرج/ارسال ادعای اندازه‌گیری نیست؛ ساختارِ موتورِ read-only است."""
    now = float(now if now is not None else time.time())
    tasks = _load(leg).get("tasks", [])
    day0 = now - 86400
    touched = [t for t in tasks if float(t.get("updated", 0) or 0) >= day0]
    if not touched:
        return ""
    created = [t for t in touched if float(t.get("created", 0) or 0) >= day0]
    done = [t for t in touched if t.get("state") == DONE
            and t.get("result") != "لغو شد"]
    cancelled = [t for t in touched if t.get("state") == DONE
                 and t.get("result") == "لغو شد"]
    blocked = [t for t in tasks if t.get("state") == BLOCKED]
    queued = [t for t in tasks if t.get("state") == QUEUED]
    lines = [f"🦵 <b>خلاصه روزانه {leg}</b>", "",
             f"ثبت‌شده: {_fa(len(created))}",
             f"تکمیل: {_fa(len(done))}",
             f"لغوشده: {_fa(len(cancelled))}",
             f"مسدود: {_fa(len(blocked))}",
             f"در صف: {_fa(len(queued))}"]
    if blocked:
        q = (blocked[0].get("question") or "—")[:100]
        lines.append(f"بزرگ‌ترین مانع: {q}")
    if done:
        best = (done[-1].get("result") or "—")[:100]
        lines.append(f"آخرین نتیجه: {best}")
    fb = [t.get("feedback") for t in tasks
          if isinstance(t.get("feedback"), dict)
          and float(t["feedback"].get("ts", 0) or 0) >= day0]
    if fb:
        good = sum(1 for f in fb if f.get("v") == "good")
        lines.append(f"بازخورد تو: 👍 {_fa(good)} · 👎 {_fa(len(fb) - good)}")
    lines += ["خرج: صفر", "ارسال بیرونی: انجام نشد"]
    return "\n".join(lines)


# ── حکمِ نتیجهٔ موتور ──────────────────────────────────────────────────────
_STUCK = re.compile(r"نمی‌دانم|نمیدانم|اطلاعاتِ? کافی|مشخص نیست|UNKNOWN", re.I)


def judge_engine_answer(answer: str) -> tuple:
    """(state, question|None) — جوابی که صریح می‌گوید داده کم است ⇒ BLOCKED."""
    a = str(answer or "").strip()
    if not a:
        return (BLOCKED, "موتور جوابی نداد")
    if _STUCK.search(a):
        return (BLOCKED, a[:200])
    return (DONE, None)
