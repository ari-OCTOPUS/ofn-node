#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hold_policy — ماشینِ حالتِ رأیِ مالک VQ-TG-HOLD-001 (۲۰۲۶-۰۷-۳۰).

متنِ رأی، فشرده:
  · CRITICAL یا گذار به قرمز        → فوری (DM ِ باتِ اختاپوس)
  · نیازمندِ تصمیم/approval          → فوری با کارت (لایهٔ بالادست؛ این‌جا نمی‌رسد)
  · doctor/heart/needs ِ نو/تغییرکرده → تجمیع در digest؛ حداکثر ساعتی یک‌بار
  · تکراری / وضعیتِ بی‌تغییر         → HOLD + dedupe؛ فقط شمارش در پالس
  · بازگشت از قرمز به سبز            → recovery receipt ِ کوتاه، فوری
  · backlog ِ قدیمی                  → **هرگز replay نمی‌شود**

جایگاه در لوله: `surface_policy.route` برای جریانِ محیطی این‌جا را صدا می‌زند و
حکم را به سه مقصدی که مصرف‌کنندهٔ موجود (`approval_channel.send_text`) می‌فهمد
ترجمه می‌کند: DM (فوری) · HOLD (ثبت، بدونِ ارسال). digest از مسیرِ سوم می‌رود:
این ماژول آیتم را در بافر می‌نویسد و **مرکز** (پروسهٔ دیگر) ساعتی یک‌بار با
کلاینتِ inner ِ خودش flush می‌کند — همان الگوی outbox ِ doctor_link، بدونِ
poller یا اتصالِ تازه.

⛔ این ماژول **هیچ‌چیز نمی‌فرستد** و **هرگز آرشیوِ ناگفته‌های قدیمی را
نمی‌خواند** (فایلِ آرشیو فقط مالِ surface_policy است). نخواندنِ آن فایل،
ضمانتِ ساختاریِ «صفر replay ِ backlog» است — نه یک if؛ و گاردی در
test_tg_hold_policy نامِ آن فایل را در این سورس ممنوع کرده.

dedupe (درسِ «شمارنده در کلیدِ dedup»): امضا از اسکلتِ متن ساخته می‌شود —
رقم‌ها (لاتین و فارسی)، درصد و ساعت حذف می‌شوند تا «همان وضعیت با عددِ تازه»
تکراری شمرده شود، ولی هر تغییرِ واقعیِ متن امضای نو بگیرد.

fail-safe: هر خطای state ⇒ برای پیامِ بحرانی «ارسال»، برای بقیه «digest» —
هرگز HOLD روی خطا، چون HOLD ِ خطا یعنی گم‌شدنِ بی‌صدا.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ── مقصدهای حکم ────────────────────────────────────────────────────────────
SEND = "send"          # فوری به DM (بحرانی/گذار/escalation/recovery)
DIGEST = "digest"      # به بافر؛ مرکز ساعتی flush می‌کند
HOLD = "hold"          # تکراری/بی‌تغییر — فقط ثبت و شمارش

DIGEST_INTERVAL_S = 3600.0          # «حداکثر یک پیام در ساعت»
_STATE_CAP = 200                    # سقفِ جریان‌های دنبال‌شده (ضدِ رشدِ بی‌پایان)


def _state_dir() -> Path:
    """خانهٔ state — از `opslib.STATE_DIR` تا harness ِ تست‌ها خودکار ایزوله‌اش
    کند (درسِ «همهٔ مسیرهای تحتِ آزمون را ایزوله کن»). env صریح بر همه مقدم؛
    نبودِ opslib ⇒ همان `_ops/state/telegram` ِ زنده."""
    override = os.environ.get("OCTOPUS_HOLD_POLICY_DIR", "").strip()
    if override:
        return Path(override)
    try:
        import sys as _s
        if str(_HERE.parent) not in _s.path:
            _s.path.insert(0, str(_HERE.parent))
        import opslib
        return Path(opslib.STATE_DIR) / "telegram"
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state" / "telegram"


def _state_path() -> Path:
    return _state_dir() / "hold-policy-state.json"


def _buffer_path() -> Path:
    return _state_dir() / "digest-buffer.jsonl"


def _viewed_path() -> Path:
    return _state_dir() / "held-viewed.json"


def _urgent_path() -> Path:
    return _state_dir() / "urgent-outbox.jsonl"


# ── امضا و شدت ─────────────────────────────────────────────────────────────
_NUMS = re.compile(r"[0-9۰-۹]+([.,:/][0-9۰-۹]+)*\s*[%٪]?")
_WS = re.compile(r"\s+")

_CRIT = re.compile(r"🔴|⛔|🆘|CRITICAL|critical|بحران|قرمز|HALT|halted|"
                   r"protective[- ]halt|circuit.?breaker", re.I)
_OK = re.compile(r"🟢|\bOK\b|\bok\b|سبز|سالم|recovered|بازگشت", re.I)


def signature(text: str) -> str:
    """امضای اسکلتِ متن — عدد/درصد/ساعت حذف تا شمارنده کلید را نچرخاند."""
    t = _NUMS.sub("#", str(text or ""))
    t = _WS.sub(" ", t).strip().lower()
    return hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:24]


def severity(text: str) -> str:
    """critical | ok | normal — از نشانه‌های صریح، نه حدسِ معنایی.

    قرمز بر سبز مقدم است: پیامی که هر دو نشانه را دارد («از سبز به قرمز رفت»)
    بحرانی است."""
    t = str(text or "")
    if _CRIT.search(t):
        return "critical"
    if _OK.search(t):
        return "ok"
    return "normal"


# ── state ──────────────────────────────────────────────────────────────────
def _load_state() -> dict:
    try:
        d = json.loads(_state_path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(d: dict) -> bool:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        streams = d.get("streams") or {}
        if len(streams) > _STATE_CAP:                    # هرسِ قدیمی‌ترین‌ها
            keep = sorted(streams.items(),
                          key=lambda kv: kv[1].get("ts", 0))[-_STATE_CAP:]
            d["streams"] = dict(keep)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False                                     # fail-soft؛ حکم قبلاً داده شده


def _buffer_append(stream: str, text: str, sev: str, now: float) -> bool:
    """آیتمِ digest — متنِ کامل ذخیره نمی‌شود (سرخطِ کوتاه‌شده کافی است؛
    echo ِ حساس هم ساختاراً محدود می‌شود)."""
    try:
        p = _buffer_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        head = _WS.sub(" ", str(text or "").strip())[:160]
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "stream": str(stream or "")[:40],
                                "sev": sev, "head": head},
                               ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


# ── حکم ────────────────────────────────────────────────────────────────────
def classify(stream, text, *, now: float | None = None) -> dict:
    """حکمِ یک پیامِ محیطیِ نو. خروجی:
    ``{"action": SEND|DIGEST|HOLD, "reason": str, "severity": str,
       "receipt": str|None}``

    `receipt` فقط برای بازگشتِ قرمز→سبز پر می‌شود: متنِ کوتاهی که به‌جای
    پیامِ کامل فوری می‌رود (خودِ پیام به digest می‌رود تا حجم نگیرد).
    """
    now = float(now if now is not None else time.time())
    s = str(stream or "unnamed").strip().lower() or "unnamed"
    sev = severity(text)
    sig = signature(text)

    st = _load_state()
    streams = st.setdefault("streams", {})
    prev = streams.get(s) or {}
    prev_sev = prev.get("sev")
    prev_sig = prev.get("sig")

    unchanged = (sig == prev_sig and sev == prev_sev)

    if unchanged:
        # «وضعیتِ بدونِ تغییر دوباره ارسال نشود» — حتی بحرانی: فقط transition
        # یا escalation (= امضای نو) دوباره می‌رود.
        decision = {"action": HOLD, "reason": f"duplicate:{sev}",
                    "severity": sev, "receipt": None}
    elif sev == "critical":
        why = "escalation" if prev_sev == "critical" else "transition-to-red"
        decision = {"action": SEND, "reason": why, "severity": sev,
                    "receipt": None}
    elif sev == "ok" and prev_sev == "critical":
        decision = {"action": SEND, "reason": "recovery", "severity": sev,
                    "receipt": f"🟢 {s}: بازگشت از قرمز به سبز"}
    else:
        decision = {"action": DIGEST, "reason": "new-or-changed",
                    "severity": sev, "receipt": None}

    # ثبتِ حالتِ تازه — شکستِ ثبت حکم را عوض نمی‌کند (fail-soft).
    streams[s] = {"sig": sig, "sev": sev, "ts": now}
    _save_state(st)
    if decision["action"] == DIGEST:
        _buffer_append(s, text, sev, now)
    return decision


# ── submit: نقطهٔ ورود از surface_policy.hold ─────────────────────────────
def submit(stream, text, *, now: float | None = None) -> dict:
    """طبقه‌بندی + سپردن به مقصدِ درست. خروجیِ classify + ``recorded``.

    SEND   → یک ردیف در urgent-outbox (مرکز در ضربانِ بعد با inner می‌فرستد).
             برای recovery فقط receipt ِ کوتاه فوری می‌رود و متنِ کامل به بافرِ
             digest — «یک recovery receipt ِ کوتاه»، نه دو پیام.
    DIGEST → classify خودش بافر کرده؛ همین.
    HOLD   → ثبتِ آرشیو با صداکننده است (surface_policy._archive).
    """
    now = float(now if now is not None else time.time())
    d = classify(stream, text, now=now)
    recorded = True
    if d["action"] == SEND:
        body = d["receipt"] if d.get("receipt") else str(text or "")
        recorded = _urgent_append(stream, body, d["reason"], now)
        if d.get("receipt"):                    # متنِ کامل حجم نگیرد ولی گم هم نشود
            _buffer_append(str(stream or ""), text, d["severity"], now)
        if not recorded:
            # fail-safe: اگر outbox ننوشت، دستِ‌کم حکم را برگردان تا صداکننده
            # آرشیو کند — پیامِ بحرانیِ گم‌شده بدترین خروجی است.
            d = dict(d, action=HOLD, reason="urgent-outbox-write-failed")
            recorded = False
    return dict(d, recorded=recorded)


def _urgent_append(stream, text, reason, now: float) -> bool:
    try:
        p = _urgent_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        head = str(text or "")[:800]
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "stream": str(stream or "")[:40],
                                "reason": str(reason)[:40], "text": head},
                               ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def urgent_pending(*, now: float | None = None, cap: int = 5) -> list:
    """ردیف‌های outbox که هنوز flush نشده‌اند — حداکثر ``cap`` در هر ضربان
    (ضدِ طوفان). فقط ردیف‌های بعد از نشانگرِ آخرین flush."""
    now = float(now if now is not None else time.time())
    st = _load_state()
    last = float(st.get("last_urgent_flush", 0.0) or 0.0)
    out = []
    try:
        for line in _urgent_path().read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and float(d.get("ts", 0) or 0) > last:
                out.append(d)
    except OSError:
        pass
    return out[:max(1, int(cap))]


def mark_urgent_flushed(upto_ts: float) -> bool:
    """نشانگر را تا ts ِ آخرین ردیفِ فرستاده‌شده جلو ببر — idempotent."""
    st = _load_state()
    if float(upto_ts) <= float(st.get("last_urgent_flush", 0.0) or 0.0):
        return True
    st["last_urgent_flush"] = float(upto_ts)
    return _save_state(st)


# ── flush ِ digest (مصرف‌کننده: مرکز، ساعتی یک‌بار) ─────────────────────────
def digest_due(*, now: float | None = None) -> bool:
    """آیا از آخرین flush یک ساعت گذشته و چیزی در بافر هست؟"""
    now = float(now if now is not None else time.time())
    st = _load_state()
    last = float(st.get("last_digest_flush", 0.0) or 0.0)
    if now - last < DIGEST_INTERVAL_S:
        return False
    return bool(_pending_items(last))


def _pending_items(since: float) -> list:
    out = []
    try:
        for line in _buffer_path().read_text("utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and float(d.get("ts", 0) or 0) > since:
                out.append(d)
    except OSError:
        pass
    return out


def flush_digest(*, now: float | None = None, cap: int = 12) -> "str | None":
    """متنِ digest ِ ساعتی — یا None اگر سررسید/محتوایی نیست.

    فقط آیتم‌های **بعد از آخرین flush** — پس backlog ِ پیش از تولدِ این سیاست
    ساختاراً هرگز وارد نمی‌شود (آن فایلِ دیگری است که این ماژول نمی‌خواند).
    صداکننده (مرکز) مسئولِ ارسال با کلاینتِ inner است.

    (۲۰۲۶-۰۷-۳۱، رفعِ inner-5) — تا امروز این تابع نشانگرِ flush را **قبل از**
    بازگشتِ متن جلو می‌برد. اگر ارسالِ مرکز شکست می‌خورد، آن آیتم‌ها همیشه پشتِ
    نشانگر می‌ماندند و دیگر بازنمی‌گشتند — نامتقارن با مسیرِ urgent (که فقط بعد
    از ارسالِ موفق mark می‌زند). حالا این تابع متن را می‌سازد ولی نشانگر را
    **جلو نمی‌برد**؛ صداکننده باید بعد از ارسالِ موفق `mark_digest_flushed`
    را صدا بزند."""
    now = float(now if now is not None else time.time())
    st = _load_state()
    last = float(st.get("last_digest_flush", 0.0) or 0.0)
    if now - last < DIGEST_INTERVAL_S:
        return None
    items = _pending_items(last)
    if not items:
        return None
    by_stream: dict = {}
    for it in items:
        by_stream.setdefault(it.get("stream") or "?", []).append(it)
    lines = ["🩺 <b>دایجستِ سلامت</b> — ساعتی یک‌بار"]
    for s in sorted(by_stream):
        rows = by_stream[s]
        head = str(rows[-1].get("head") or "")[:80]
        lines.append(f"· <b>{s}</b> ×{_fa(len(rows))} — {head}")
        if len(lines) >= cap:
            lines.append("…")
            break
    return "\n".join(lines)


def mark_digest_flushed(now: float | None = None) -> bool:
    """نشانگرِ flush ِ digest را جلو ببر — فقط بعد از ارسالِ موفق (رفعِ inner-5).

    تقارن با `mark_urgent_flushed`: نشانگر فقط وقتی جلو می‌رود که مرکز پیام را
    واقعاً فرستاده باشد. اگر ارسال شکست بخورد، آیتم‌ها در flushِ بعدی دوباره
    بازمی‌گردند."""
    now = float(now if now is not None else time.time())
    try:
        st = _load_state()
        st["last_digest_flush"] = now
        _save_state(st)
        return True
    except Exception:  # noqa: BLE001
        return False


# ── نمای «🔇 ناگفته‌ها» (رأی §۶) ────────────────────────────────────────────
def held_view(held_rows: list, *, now: float | None = None, cap: int = 10) -> str:
    """خلاصه و دسته‌بندی — نه متن. حداکثر ۱۰ موردِ تازه؛ echo ِ حساس ممنوع
    (فقط نامِ جریان + سن). خواندن، وضعیت را HELD_VIEWED می‌کند نه sent."""
    now = float(now if now is not None else time.time())
    rows = [r for r in (held_rows or []) if isinstance(r, dict)]
    if not rows:
        return "🔇 چیزی نگه‌داشته نشده."
    by_stream: dict = {}
    for r in rows:
        by_stream.setdefault(str(r.get("stream") or "?"), 0)
        by_stream[str(r.get("stream") or "?")] += 1
    lines = [f"🔇 <b>ناگفته‌ها</b> — {_fa(len(rows))} مورد · وضعیت: HELD_VIEWED"]
    for s, n in sorted(by_stream.items(), key=lambda kv: -kv[1])[:6]:
        lines.append(f"· {s} ×{_fa(n)}")
    fresh = rows[-cap:]
    if fresh:
        lines.append("تازه‌ترین‌ها (فقط جریان و زمان — متن echo نمی‌شود):")
        for r in reversed(fresh):
            age = _age_fa(r.get("ts"), now)
            lines.append(f"  – {str(r.get('stream') or '?')[:24]} · {age}")
    _mark_viewed(now)
    return "\n".join(lines)


def _mark_viewed(now: float) -> None:
    try:
        p = _viewed_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"status": "HELD_VIEWED", "ts": now}), "utf-8")
    except OSError:
        pass                                             # نما هرگز نمی‌شکند


def _age_fa(ts, now: float) -> str:
    try:
        if isinstance(ts, str):                          # opslib.now_iso
            from datetime import datetime
            ts = datetime.fromisoformat(ts).timestamp()
        m = max(0, int((now - float(ts)) / 60))
    except (TypeError, ValueError):
        return "؟"
    if m < 60:
        return f"{_fa(m)} دقیقه پیش"
    return f"{_fa(m // 60)} ساعت پیش"


def _fa(n) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
