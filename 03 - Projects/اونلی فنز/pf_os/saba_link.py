#!/usr/bin/env python3
"""saba_link.py — پلِ مستقیمِ من (pf_os) ↔ creator.

سه جهتِ ارتباطی، همه از طریقِ فایل (طبقِ الگوی file-based pub/sub پروژه):

  1. من ← creator (INITIATIVE): نوشتنِ brief/نوتیف به studio/for_saba.json.
     creator در saba_studio::inbox_page این فایل را می‌خواند و در /inbox نشان می‌دهد.
     این یعنی من می‌توانم به creator پیام بفرستم — نه فقط از operator رد بشه.

  2. creator ← من (DRAFT): خواندنِ studio/drafts.json. وقتی creator draft ثبت می‌کند،
     من آن را می‌بینم و می‌توانم پیشنهادِ قیمت/زمان/ترند بدهم (propose-only).

  3. نوتیفِ خودکار: send_notify() برای رویدادهای مهم (halt، warmup، capacity).

قراردادِ فایل‌ها (طبقِ saba_studio موجود):
  - for_saba.json: list of {"date": str, "text": str, "read": bool}
  - drafts.json: list of {draft_id, title, status, ...}
  - HALT: file existence = halt
  - capacity.json: {"hours": float, "date": str}

نامتغیرِ PII: هرگز نام/شهر/محتوا در for_saba.json نمی‌نویسیم. فقط metadata و
پیام‌های content-free.

$0 آفلاین، stdlib-only، fail-soft.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from . import config


# ─── مسیرها (studio/ — همان‌جا که saba_studio انتظار دارد) ───────────────────
def _studio_dir() -> Path:
    """مسیرِ studio. قابل‌تزریق برای تست."""
    env = os.environ.get("PF_STUDIO_DIR")
    if env:
        return Path(env)
    return Path(config.PF_ROOT) / "studio"


def _for_saba_path() -> Path:
    return _studio_dir() / "for_saba.json"


def _drafts_path() -> Path:
    return _studio_dir() / "drafts.json"


def _halt_path() -> Path:
    return _studio_dir() / "HALT"


def _capacity_path() -> Path:
    return _studio_dir() / "capacity.json"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _load(path: Path, default):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def _atomic_write(path: Path, data) -> bool:
    """نوشتنِ atomic با .tmp + replace (هم‌الگوی content_studio)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        os.replace(tmp, path)
        return True
    except Exception:  # noqa: BLE001
        return False


# ═════════════════════════════════════════════════════════════════════════════
# ۱) من ← صبا: نوشتنِ brief / نوتیف
# ═════════════════════════════════════════════════════════════════════════════

def send_to_saba(text: str, kind: str = "note") -> bool:
    """ارسالِ یک پیام به صبا (از طریق for_saba.json). صبا در /inbox می‌بیند.

    args:
      text: متنِ پیام. باید content-free (نام/شهر/محتوا ممنوع — فرستنده مسئول).
      kind: "brief" | "notify" | "note" | "warning" — فقط برای لاگ/فیلتر.

    برمی‌گرداند True اگر نوشته شد.
    """
    if not text or not text.strip():
        return False
    text = text.strip()[:500]  # کپ
    p = _for_saba_path()
    msgs = _load(p, [])
    if not isinstance(msgs, list):
        msgs = []
    msgs.append({"date": _now(), "text": text, "kind": kind, "read": False})
    # کپ به ۵۰ پیام (هم‌الگوی to_ari.json در saba_studio)
    msgs = msgs[-50:]
    return _atomic_write(p, msgs)


def send_brief(lines: list[str]) -> bool:
    """ارسالِ بریفِ هفتگی/روزانه به صبا. lines = فهرستِ خطوط (content-free)."""
    if not lines:
        return False
    body = "📋 <b>بریفِ سیستم</b>\n━━━━━━━━━━\n" + "\n".join(lines[:12])
    return send_to_saba(body, kind="brief")


def send_notify(reason: str, detail: str = "") -> bool:
    """نوتیفِ خودکار برای رویدادِ مهم. مثلاً warmup/capacity/halt-state."""
    body = f"🔔 {reason}"
    if detail:
        body += f"\n{detail}"
    return send_to_saba(body, kind="notify")


def send_warning(channel: str, reason: str = "") -> bool:
    """هشدار (مثلاً platform warning از طرفِ گاورنر). content-free."""
    return send_to_saba(
        f"⚠️ هشدار روی کانال {channel}" + (f": {reason}" if reason else ""),
        kind="warning")


# ═════════════════════════════════════════════════════════════════════════════
# ۲) صبا ← من: خواندنِ drafts / HALT / capacity
# ═════════════════════════════════════════════════════════════════════════════

def pending_drafts() -> list[dict]:
    """درفت‌های در انتظارِ تأیید. صبا این‌ها را ثبت کرده، اپراتور هنوز تأیید نکرده."""
    data = _load(_drafts_path(), [])
    if not isinstance(data, list):
        return []
    return [d for d in data if isinstance(d, dict) and d.get("status") == "pending"]


def saba_halted() -> bool:
    """آیا صبا halt زده؟"""
    return _halt_path().exists()


def saba_capacity() -> dict:
    """ظرفیتِ اعلامیِ صبا (ساعت/هفته)."""
    return _load(_capacity_path(), {})


def inbox_for_saba() -> list[dict]:
    """پیام‌های موجود در for_saba.json (از همه: من + operator)."""
    data = _load(_for_saba_path(), [])
    return data if isinstance(data, list) else []


# ═════════════════════════════════════════════════════════════════════════════
# ۳) snapshot برای /api/saba و /api/health
# ═════════════════════════════════════════════════════════════════════════════

def snapshot() -> dict:
    """وضعیتِ کاملِ پلِ من↔صبا."""
    return {
        "writable": os.access(str(_studio_dir()), os.W_OK),
        "studio_dir": str(_studio_dir()),
        "pending_drafts": len(pending_drafts()),
        "saba_halted": saba_halted(),
        "saba_capacity_hours": saba_capacity().get("hours"),
        "messages_in_inbox": len(inbox_for_saba()),
        "unread_in_inbox": sum(
            1 for m in inbox_for_saba() if not m.get("read", False)),
    }


# ═════════════════════════════════════════════════════════════════════════════
# ۴) reply_on_draft — پردازشِ draft صبا (propose-only)
# ═════════════════════════════════════════════════════════════════════════════

def _draft_text(draft: dict) -> str:
    """متنِ معناییِ درفت را برای مغز جمع می‌کند (title + یادداشت/کپشن اگر باشد).

    این متن فقط ورودیِ مغز است (که خودش PII را scrub می‌کند) — هرگز مستقیم در
    for_saba.json نوشته نمی‌شود. نامتغیرِ PII حفظ می‌ماند.
    """
    parts = []
    for key in ("title", "note", "caption", "desc", "description", "text", "body"):
        v = draft.get(key)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    return " ".join(parts).strip()


def _honest_intent_ack(intent: str) -> str:
    """پیامِ صادقانه‌ی intent-محور: وقتی مغز موضوع را تشخیص داد ولی پاسخِ کامل
    نداد (مثلاً متن PII داشت و scrub شد). هرگز ادعا نمی‌کند مغز قیمت/زمان را
    «محاسبه کرد» — فقط می‌گوید موضوع دیده شد و اپراتور از مغز می‌گیرد.
    """
    seen = {
        "price": "موضوعِ قیمت رو دیدم",
        "schedule": "موضوعِ زمان‌بندی رو دیدم",
        "trend": "موضوعِ ترند رو دیدم",
        "boundary": "پیامِ محدوده/استراحت رو دیدم",
    }.get(intent, "درفتت رو دیدم")
    return (f"🌟 رسید! {seen} — اپراتور جوابِ دقیق رو از مغز می‌گیره "
            "و برات می‌فرسته.")


def on_new_draft(draft: dict, brain=None) -> Optional[str]:
    """وقتی صبا درفت ثبت می‌کند، یک پیشنهادِ گرم به for_saba.json بفرست.

    propose-only: فقط پیامِ پیشنهاد می‌نویسد، هرگز publish/send نمی‌کند.
    brain: اختیاری (BrainCore). اگر باشد، مغز *واقعاً* روی محتوای درفت اجرا
           می‌شود (_classify_saba_intent + respond_to_saba). پیشنهاد از خروجیِ
           واقعیِ مغز ساخته می‌شود؛ و تنها وقتی از «کارِ مغز» حرف می‌زنیم که مغز
           واقعاً پاسخ داده باشد — در غیرِ این‌صورت پیامِ صادقانه‌ی fallback
           (بدون ادعای محاسبه‌ی مغز).

    برمی‌گرداند: متنِ پیشنهاد ارسال‌شده، یا None اگر چیزی نفرستاد.
    """
    title = str(draft.get("title", "")).strip()
    if not title:
        return None
    # هرگز عنوانِ raw در پیام نمی‌رود — پیامِ پیش‌فرضِ صادقانه (هیچ ادعایی از مغز).
    suggestion = (
        "🌟 درفتِ جدیدت رسید! پیشنهادِ من: یه بافرِ ≥۷ روزه، و اپراتور "
        "قیمت/زمانِ دقیق رو از مغز می‌گیره.")
    if brain is not None:
        # مغز را *واقعاً* روی محتوای درفت اجرا کن (نه فقط hasattr).
        # مغز خودش PII را scrub می‌کند و خروجی‌اش content-free است.
        draft_text = _draft_text(draft) or title
        intent = None
        brain_reply = None
        try:
            if hasattr(brain, "_classify_saba_intent"):
                intent = brain._classify_saba_intent(draft_text)
            if hasattr(brain, "respond_to_saba"):
                brain_reply = brain.respond_to_saba(draft_text)
        except Exception:  # noqa: BLE001 — مغز نباید pf_os را بکُشد (fail-soft)
            brain_reply = None
        if brain_reply and str(brain_reply).strip():
            # مغز *واقعاً* پاسخ داد → همان پاسخِ content-free را پیشنهاد بده.
            suggestion = "🌟 رسید! " + str(brain_reply).strip()
        elif intent and intent != "unknown":
            # مغز موضوع را تشخیص داد ولی پاسخِ کامل نداد → ackِ صادقانه‌ی intent-محور.
            suggestion = _honest_intent_ack(intent)
        # در غیرِ این‌صورت suggestion همان پیش‌فرضِ صادقانه می‌ماند.
    send_to_saba(suggestion, kind="draft_ack")
    return suggestion
