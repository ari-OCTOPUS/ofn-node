"""
brain/notify.py — لایه‌ی پیام‌رسانی و Decision Packet (قراردادِ Hybrid Agent).

هرگاه سیستم به انسان نیاز داشت (Tier 2 اطلاع / Tier 3 تأیید / هشدار / milestone)،
یک Decision Packet با قالبِ قراردادیِ hybrid-agent-prompt.md می‌سازد:

  [ALERT TYPE] · [CONTEXT] · [WHY NOW] · [OPTIONS] · [RECOMMENDATION] · [CONSEQUENCE]

مقصدها:
  • Telegram (اگر TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID در .env تنظیم باشد)
  • صفِ محلیِ پایدار (outputs/decision_packets.jsonl) — همیشه، برای ممیزی و نمایش در داشبورد

صادقانه: پاسخِ approve/reject از داخلِ داشبورد انجام می‌شود (این نسخه پاسخِ تلگرام را
poll نمی‌کند)؛ روی Tier 3 سیستم در حالتِ امن pause می‌ماند تا انسان تصمیم بگیرد.
"""
from __future__ import annotations

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

ALERT_TYPES = {"approve", "notify", "blocked", "warning", "summary"}

# ضدِ اسپم: حداقل فاصله بین دو ارسالِ تلگرام
_MIN_SEND_INTERVAL = 20.0
_last_send = [0.0]


def _queue_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "decision_packets.jsonl"


def is_configured() -> bool:
    """آیا تلگرام تنظیم شده؟ (توکن + chat id در env)"""
    return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
                and os.getenv("TELEGRAM_CHAT_ID", "").strip())


def format_packet(alert_type: str, context: str, why_now: str,
                  recommendation: str, consequence: str,
                  options: list[str] | None = None) -> str:
    """قالبِ قراردادیِ پیام (کوتاه و ساختاریافته)."""
    opts = options or ["approve", "reject", "modify", "more-analysis", "defer"]
    return (
        f"[{alert_type.upper()}]\n"
        f"📍 CONTEXT: {context}\n"
        f"⏰ WHY NOW: {why_now}\n"
        f"🔀 OPTIONS: " + " / ".join(f"{i+1}.{o}" for i, o in enumerate(opts)) + "\n"
        f"💡 RECOMMENDATION: {recommendation}\n"
        f"⚠️ CONSEQUENCE: {consequence}"
    )


def _send_telegram(text: str) -> tuple[bool, str]:
    """ارسالِ واقعی به تلگرام. throttled؛ خطا هرگز سیستم را نمی‌شکند."""
    if not is_configured():
        return False, "not-configured"
    now = time.time()
    if now - _last_send[0] < _MIN_SEND_INTERVAL:
        return False, "throttled"
    _last_send[0] = now
    try:
        import requests
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text[:4000]},
            timeout=15,
        )
        if r.status_code == 200 and r.json().get("ok"):
            return True, "sent"
        return False, f"http {r.status_code}"
    except Exception as e:
        # فقط نوعِ خطا لاگ می‌شود — پیامِ کاملِ خطاهای شبکه‌ای (مثلاً
        # "Max retries exceeded with url: /bot<TOKEN>/...") توکن را به
        # outputs/system.log نشت می‌داد.
        logger.warning("telegram send failed: %s", type(e).__name__)
        return False, f"error: {type(e).__name__}"


def send_packet(alert_type: str, context: str, why_now: str,
                recommendation: str, consequence: str,
                options: list[str] | None = None) -> dict:
    """
    ساخت + ثبتِ پایدار + ارسالِ (در صورتِ امکان) یک Decision Packet.
    همیشه در صفِ محلی ذخیره می‌شود (ممیزی)؛ تلگرام best-effort است.
    """
    if alert_type not in ALERT_TYPES:
        alert_type = "notify"
    text = format_packet(alert_type, context, why_now, recommendation, consequence, options)

    packet = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "alert_type": alert_type,
        "context": context,
        "why_now": why_now,
        "recommendation": recommendation,
        "consequence": consequence,
        "delivered": "pending",
    }

    sent, detail = _send_telegram(text)
    packet["delivered"] = "telegram" if sent else f"queued ({detail})"
    # UNWIRED VOTE 4 honesty: queued(not-configured) is not delivery to owner
    packet["reached_owner"] = bool(sent)

    # ثبتِ پایدار — از میانِ guardrails (فقط outputs/)
    try:
        from brain import guardrails
        ok, _ = guardrails.assert_safe_write(_queue_path())
        if ok:
            with open(_queue_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(packet, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("packet persist failed: %s", e)

    logger.info("decision packet [%s] → %s: %s", alert_type, packet["delivered"], context[:60])
    return packet


# ════════════════════════════════════════════════════════════════════════
#  Digest — دسته‌کردنِ پیام‌ها به ≤ چند بار در روز (تصمیمِ مالک: روزی ۲–۳ بار)
#
#  در اجرای ماهانه‌ی بی‌مراقب، هر رویداد یک پیامِ تلگرام نمی‌شود؛ پکت‌ها صف
#  می‌شوند و flush_digest آن‌ها را در یک پیامِ ترکیبی، حداکثر NOTIFY_MAX_PER_DAY
#  بار در روز و با فاصله‌ی زمانی، می‌فرستد. مواردِ بحرانی (approve/halt) با
#  force=True می‌توانند فوری بروند ولی باز هم در سقفِ روزانه می‌مانند.
# ════════════════════════════════════════════════════════════════════════

def _digest_path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "notify_digest.json"


def _max_per_day() -> int:
    try:
        return max(1, int(os.getenv("NOTIFY_MAX_PER_DAY", "3")))
    except ValueError:
        return 3


def _load_digest() -> dict:
    p = _digest_path()
    today = datetime.now().strftime("%Y-%m-%d")
    if not p.exists():
        return {"date": today, "sent_today": 0, "last_send": 0.0, "queue": []}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("date") != today:            # روزِ جدید → شمارنده صفر
            d = {"date": today, "sent_today": 0, "last_send": 0.0,
                 "queue": d.get("queue", [])}
        d.setdefault("queue", [])
        return d
    except Exception:
        return {"date": today, "sent_today": 0, "last_send": 0.0, "queue": []}


def _save_digest(d: dict) -> None:
    p = _digest_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, p)
    except Exception as e:
        logger.warning("digest save failed: %s", e)


def queue_for_digest(alert_type: str, context: str, why_now: str,
                     recommendation: str, consequence: str) -> None:
    """یک پکت را به صفِ digest اضافه می‌کند (بدونِ ارسالِ فوری)."""
    d = _load_digest()
    d["queue"].append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "alert_type": alert_type if alert_type in ALERT_TYPES else "notify",
        "context": context, "why_now": why_now,
        "recommendation": recommendation, "consequence": consequence,
    })
    d["queue"] = d["queue"][-100:]        # سقفِ صف
    _save_digest(d)


def flush_digest(force: bool = False) -> dict:
    """اگر زمانش رسید، صفِ digest را در یک پیامِ ترکیبی می‌فرستد.

    قواعد: حداکثر NOTIFY_MAX_PER_DAY بار در روز؛ فاصله‌ی ~۲۴/سقف ساعت بین ارسال‌ها
    (مگر force). صف همیشه در jsonlِ ممیزی هست؛ این فقط ارسالِ تلگرام را کم‌نویز می‌کند.
    """
    d = _load_digest()
    if not d["queue"]:
        return {"sent": False, "reason": "صف خالی"}

    cap = _max_per_day()
    if not force and d["sent_today"] >= cap:
        return {"sent": False, "reason": f"سقفِ روزانه ({cap}) پر — در صف می‌ماند"}

    min_gap = (24.0 / cap) * 3600.0
    if not force and (time.time() - d.get("last_send", 0.0)) < min_gap:
        return {"sent": False, "reason": "فاصله‌ی زمانی هنوز نرسیده"}

    n = len(d["queue"])
    header = f"📬 خلاصه‌ی خودمختار ({n} رویداد) — {d['date']}"
    lines = [header, ""]
    for pk in d["queue"][-15:]:
        lines.append(f"[{pk['alert_type'].upper()}] {pk['context'][:80]}")
        if pk.get("recommendation"):
            lines.append(f"   💡 {pk['recommendation'][:80]}")
    text = "\n".join(lines)

    sent, detail = _send_telegram(text)
    if sent:
        d["sent_today"] = int(d.get("sent_today", 0)) + 1
        d["last_send"] = time.time()
        d["queue"] = []
        _save_digest(d)
        return {"sent": True, "count": n, "sent_today": d["sent_today"],
                "reached_owner": True}
    # نفرستاد (تنظیم‌نشده/throttle) — صف را نگه دار
    _save_digest(d)
    return {"sent": False, "reason": detail, "queued": n, "reached_owner": False}


def digest_status() -> dict:
    d = _load_digest()
    return {"date": d["date"], "sent_today": d.get("sent_today", 0),
            "cap": _max_per_day(), "queued": len(d.get("queue", []))}


def recent_packets(limit: int = 8) -> list[dict]:
    """آخرین Packetها (جدیدترین اول) برای نمایش در داشبورد."""
    p = _queue_path()
    if not p.exists():
        return []
    try:
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        out = []
        for ln in reversed(lines[-limit * 2:]):
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []


def clear_packets() -> int:
    p = _queue_path()
    if not p.exists():
        return 0
    n = len(p.read_text(encoding="utf-8").strip().splitlines())
    p.unlink()
    return n


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("telegram configured:", is_configured())
    pk = send_packet(
        "summary", "تستِ لایه‌ی پیام‌رسانی",
        "بررسیِ صحتِ قالب و صف", "هیچ اقدامی لازم نیست", "هیچ",
    )
    print("delivered:", pk["delivered"])
    print("recent:", len(recent_packets()))
