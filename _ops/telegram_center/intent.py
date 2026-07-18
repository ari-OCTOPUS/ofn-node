#!/usr/bin/env python3
"""intent.py — طبقه‌بندِ نیتِ پیامِ آزادِ مالک برای «مرکزِ تلگرام» (telegram_center).

نقش: یک تابعِ خالصِ stdlib-only که متنِ آزادِ مالک را به یک نیتِ قابل‌اجرایِ امن
تبدیل می‌کند — بدونِ هیچ اجرای مستقیم. این ماژول هیچ‌چیز جز خواندنِ ورودی و
گرداندنِ یک dict انجام نمی‌دهد: نه شبکه، نه نوشتن، نه import-time اثر.

قراردادِ خروجی (همهٔ مصرف‌کننده‌ها به همین شکل تکیه می‌کنند):

    {
      "intent": "status|budget|revenue|pause_leg|resume_leg|scan_metadata|"
                "approvals|help|unknown",
      "leg":    "lead|ziman|mining|crypto|accounting|studio_pf|knowledge|"
                "cartographer|None",
      "confidence": 0.0..1.0,
      "danger": "read|low|medium|high",   # ریسکِ نیت برای gating
    }

چرا این لایه جدا است (نه inline در center):
  - تست‌پذیریِ خالص (بدون client/clock/state).
  - ارتقای آینده به LLM پشتِ فلگِ `OCTOPUS_TG_LLM_ASK=1` بدونِ لمسِ center.
  - یک منبعِ حقیقت برای callbackهای `lg:*`/`map:*`/`mn:*` (همان قراردادِ render).

$0 · stdlib-only · import-time خالص · Persian-aware. مصرف‌کننده: center._handle_ask.
"""
from __future__ import annotations

# ─── جداولِ کلیدواژه (خالص، بدون I/O) ───────────────────────────────────────────
# ترتیبِ مهم است: intentهای خاص‌تر (pause/resume) قبل از عام (status/help) بررسی
# می‌شوند تا «لید رو مکث کن» به pause_leg برود، نه به status («کن» شبیه nothing).

_INTENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # danger=low: مکث/ادامه فقط کارت می‌سازند، اجرا بعد از کلیک؛ لذا خود classify read است.
    ("pause_leg",     ("مکث", "متوقف", "نگه دار", "نگهدار", "توقف", "pause", "stop", "hold")),
    ("resume_leg",    ("ادامه", "شروع کن", "ری‌استارت", "resume", "restart", "continue")),
    ("scan_metadata", ("نقشه", "اسکن", "اسکنش", "manifest", "metadata", "کشف کن",
                       "چی توشه", "چی داریم", "چی توی", "نقشه‌برداری", "نقشه برداری")),
    ("approvals",     ("تأیید", "تصمیم", "صف", "approval", "approve", "decide", "منتظر")),
    ("budget",        ("بودجه", "تخصیص", "سرمایه", "budget", "allocate")),
    ("revenue",       ("درآمد", "پول", "مالی", "فروش", "revenue", "money", "income", "aud")),
    ("status",        ("وضعیت", "چطوری", "چطور", "الان", "حالت", "status", "now", "how")),
    ("help",          ("کمک", "راهنما", "منو", "help", "menu", "guide")),
)

# نقشهٔ intent → خطر (gating در center با این تصمیم می‌گیرد کارت بسازد یا اجرا کند).
_INTENT_DANGER: dict[str, str] = {
    "status":        "read",
    "help":          "read",
    "budget":        "read",      # صفحهٔ bg فقط نمایش می‌دهد؛ اعمال pw:ba جدا است
    "revenue":       "read",
    "approvals":     "read",      # نمایشِ صف؛ تأیید/رد از ap:ok/no می‌گذرد
    "scan_metadata": "read",      # فقط metadata، محتوا نه؛ کارتِ map:start پیشنهاد
    "pause_leg":     "low",       # برگشت‌پذیر ولی state را عوض می‌کند
    "resume_leg":    "low",
    "unknown":       "read",
}

# نامِ نمایشیِ پاها در callback (content-free — هرگز نامِ واقعیِ کسب‌وکار).
_LEG_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lead",         ("lead", "لید", "نقاش", "نقاشی")),
    ("ziman",        ("ziman", "گالری", "gallery", "زیمان")),
    ("mining",       ("mining", "ماینینگ", "min")),
    ("crypto",       ("crypto", "کریپتو", "etoro", "ایتورو")),
    ("accounting",   ("accounting", "حساب", "اکانتینگ")),
    ("studio_pf",    ("studio", "استودیو", "project-f", "project f", "پروژه اف")),
    ("knowledge",    ("knowledge", "دانش")),
    ("cartographer", ("cartographer", "نقشه‌بردار", "نقشه بردار")),
    ("system",       ("سیستم", "system")),
)


def _contains(haystack_lower: str, needles: tuple[str, ...]) -> str | None:
    """اولین needle که در haystack پیدا شد (case-insensitive برای ASCII)."""
    for n in needles:
        if n.isascii():
            if n.lower() in haystack_lower:
                return n
        elif n in haystack_lower or n in haystack_lower.lower():   # فارسی: حساس به case نیست
            return n
    return None


def detect_leg(text: str) -> str | None:
    """حدسِ content-free از نامِ پا. فقط whitelist؛ ۰ یا ۲+ hit → None (ابهام).

    ابهام عمداً None برمی‌گرداند تا center کارتِ انتخابِ پا بسازد، نه حدسِ کور."""
    low = str(text or "").lower()
    hits = [k for k, vals in _LEG_ALIASES if _contains(low, vals) is not None]
    return hits[0] if len(hits) == 1 else None


def classify(text: str) -> dict:
    """متنِ آزاد → نیتِ امن. خالص، قطعی، fail-soft (ورودیِ خراب → unknown).

    confidence:
      1.00 وقتی کلیدواژهٔ 明確 + یک پا پیدا شود (مثلاً «لید رو مکث کن»).
      0.85 وقتی کلیدواژهٔ نیت پیدا شد (بدون پا).
      0.40 برای unknown (احتیاط: کارتِ پیشنهاد).
    """
    raw = str(text if text is not None else "")
    low = raw.lower()
    if not raw.strip():
        return {"intent": "unknown", "leg": None, "confidence": 0.0, "danger": "read"}

    leg = detect_leg(raw)

    # اولویت‌بندی: نخستین intentی که match شود برنده (ترتیبِ _INTENT_KEYWORDS مهم است).
    matched_intent = "unknown"
    for intent, kws in _INTENT_KEYWORDS:
        if _contains(low, kws) is not None:
            matched_intent = intent
            break

    if matched_intent == "unknown":
        # حتی unknown ممکن است پا را شناسایی کند → کارتِ «این پا؟» پیشنهاد
        conf = 0.50 if leg else 0.40
    elif leg:
        conf = 1.00
    else:
        conf = 0.85

    return {
        "intent": matched_intent,
        "leg": leg,
        "confidence": round(conf, 2),
        "danger": _INTENT_DANGER.get(matched_intent, "read"),
    }


def is_read_only(intent_name: str) -> bool:
    """آیا این نیت فقط خواندنی است؟ center با این تصمیم می‌گیرد که می‌تواند مستقیم
    صفحه نشان دهد یا باید حتماً کارتِ تأیید بسازد. helper برای خوانایی در center."""
    return _INTENT_DANGER.get(str(intent_name or ""), "read") == "read"


if __name__ == "__main__":
    # فقط دمو (خالص، هیچ I/O ِ واقعی)
    import json
    for sample in ("وضعیت الان چطوره؟", "لید رو مکث کن", "نقشه بکش", "درآمد چقدره؟",
                   "بودجه", "ziman رو ادامه بده", "چی توشه؟", "یه چیز عجیب"):
        print(json.dumps({"q": sample, **classify(sample)}, ensure_ascii=False))
