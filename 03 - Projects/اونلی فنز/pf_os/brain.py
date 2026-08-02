#!/usr/bin/env python3
"""brain.py — مغزِ ماژولارِ Project-F OS (BrainCore).

این مغز، پلِ اصلیِ pf_os به Saba (گفتگوی دوطرفه) و به cortex مرکزی (LLM) است.
دو کارِ کانونی:
  1. respond_to_saba(text) — پاسخِ هوشمند به متنِ آزادِ صبا. سابقاً در saba_studio
     این قرارداد بود (line 380). اینجا واقعی می‌شود.
  2. think(...) — فراخوانیِ cortex برای هر task، با fallback صادقانه به heuristic.

معماری (طبقِ پلانِ تصویب‌شده‌ی فاز ۲):
  - ۱۰ ThinkingBrain موجود (در dual_brain_v3) به‌عنوان fallback heuristic نگه داشته می‌شوند.
  - برای هر سوال، اول cortex (POST :8772/ask) صدا زده می‌شود.
  - LLM خروجی به structured thought تبدیل می‌شود.
  - Guard واقعی (نه bypass).

نامتغیرِ PII (حیاتی — قاعده‌ی قفل‌شده‌ی #۷):
  هرگز نام/شهر/محتوا/پلتفرم به cortex نمی‌رود. قبل از هر فراخوانیِ LLM، متن scrub
  می‌شود. فقط intent/metadata/سؤالِ کلی می‌رود، نه محتوای draft.

$0 آفلاین، stdlib-only، fail-soft.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import config, cortex_client
from . import events as _ev

# import dual_brain_v3 (fallback heuristic) — اختیاری
_PROJ = config.PF_ROOT
_BRAIN = str(Path(_PROJ) / "brain")
if _BRAIN not in sys.path:
    sys.path.insert(0, _BRAIN)

_DualBrainV3 = None
_COMPLIANCE_RULES = []
_ETHICS_RULES = []
try:
    from dual_brain_v3 import (  # type: ignore
        DualBrainV3, COMPLIANCE_RULES, ETHICS_RULES, FORBIDDEN_TERMS,
    )
    _DualBrainV3 = DualBrainV3
    _COMPLIANCE_RULES = list(COMPLIANCE_RULES)
    _ETHICS_RULES = list(ETHICS_RULES)
except Exception:  # noqa: BLE001 — fallback نیست؟ heuristic-off، ولی مغز کار می‌کند
    FORBIDDEN_TERMS = []


# ─── PII scrubbing (طبقِ dual_brain_v3::FORBIDDEN_TERMS + langar::OpsecGuard) ──
# این نقاطِ کلیدیِ قراردادِ containment هستند. هرگز محتوای raw به cortex نرود.
# معادل‌های فارسی/فینگلیش (لِین B · 2026-08-03).
# چرا اینجا و نه فقط از FORBIDDEN_TERMS: (۱) تطبیق substring روی `.lower()` است و
# `str.lower()` روی فارسی بی‌اثر — «a trip to Sydney» reject می‌شد ولی «سفر به
# سیدنی» مستقیم به cortex می‌رفت؛ (۲) importِ بالای این فایل fail-soft است
# (`except` → `FORBIDDEN_TERMS = []`)، پس اگر dual_brain_v3 لود نشود کلِ scrub
# بی‌دندان می‌ماند. این فهرست به هیچ importی وابسته نیست.
# **هیچ نامِ شخصیِ تازه‌ای اینجا اضافه نمی‌شود** — سطرِ نام‌ها دست‌نخورده است.
# «استرالیا/استرالیایی» عمداً نیست — کشوری و مجاز.
_FA_SCRUB_TERMS = [
    "تهران", "خاورمیانه", "سیدنی", "sidney", "sydeny",
    "ایران", "ایرانی", "پارسی", "پرشین", "فارسی", "farsi", "irani", "persion",
    "انلی فنز", "اونلی فنز", "اونلی‌فنز", "فنسلی",
    "آدرس", "اسم واقعی", "ایمیل", "شماره تلفن", "نام واقعی",
    "بیت کوین", "بیت‌کوین", "پی پال", "پی‌پال", "پیپال", "حواله",
    "رمزارز", "کارت به کارت", "کریپتو",
]

_SCRUB_TERMS = list(FORBIDDEN_TERMS) + [
    "anar", "amber", "yalda", "arch",  # brand candidates
    "ari", "saba",  # operator/creator names
] + _FA_SCRUB_TERMS

# نرمال‌سازِ سبکِ فارسی — خالص، stdlib، خودبسنده (عمداً import نمی‌شود: هر گارد
# باید مستقل بایستد؛ importِ fail-soft یعنی گاردی که بی‌صدا بی‌دندان می‌شود).
_FA_TRANS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "‌": "", "ـ": ""})


def _fa_norm(text: str) -> str:
    """کوچک‌سازی + یکسان‌سازیِ ی/ک عربی + حذفِ نیم‌فاصله/کشیده."""
    return str(text or "").translate(_FA_TRANS).lower()


def scrub_for_cortex(text: str) -> str:
    """Scrub متن قبل از فرستادن به cortex. PII/محتوا/هویت حذف، intent باقی.

    قاعده‌ی صلب: متنِ خالصِ صبا (که ممکن است عنوانِ draft/احساس/سؤال باشد)
    هرگز به cortex نمی‌رود. ما فقط یک سؤالِ کلی/عملیاتی می‌سازیم.
    """
    if not text:
        return ""
    # نرمال‌سازی فقط برای **تشخیص**؛ متنِ برگشتی همان ورودیِ خام است.
    # نگاشت روی لاتین بی‌اثر ⇒ رفتارِ واژه‌های لاتین بایت‌به‌بایت دست‌نخورده.
    t = _fa_norm(text)
    # اگر هر کلمه‌ی ممنوعه‌ای در متن است، reject کلی
    for term in _SCRUB_TERMS:
        if term and _fa_norm(term) in t:
            return ""  # سیگنال به caller: scrub نتوانست، fallback بزن
    # محدود کردن طول (هرگز بیش از ۲۰۰ کاراکتر)
    return str(text).strip()[:200]


# ─── BrainCore ────────────────────────────────────────────────────────────────

@dataclass
class BrainResponse:
    """خروجیِ ساختاریافته‌ی مغز."""
    ok: bool
    text: str
    source: str = "fallback"        # "cortex" | "heuristic" | "fallback"
    tier: str = "none"
    ms: int = 0
    reason: str = ""
    thought: dict = field(default_factory=dict)


class BrainCore:
    """مغزِ ماژولارِ pf_os. دو رابطِ اصلی:
      - respond_to_saba(text) → str | None   (قراردادِ saba_studio:380)
      - think(task, prompt) → BrainResponse   (رابطِ عمومیِ API/loop)
    """

    def __init__(self, heuristic=None):
        # heuristic = DualBrainV3 (اختیاری). اگر نباشد، فقط cortex + ساده‌پاسخ.
        self._heuristic = heuristic or _DualBrainV3() if _DualBrainV3 else heuristic
        self._last_saba_response: dict = {}
        self._ticks = 0

    # ── رابطِ گفتگو با صبا (قراردادِ saba_studio:380) ──
    def respond_to_saba(self, text: str) -> Optional[str]:
        """پاسخِ هوشمند به متنِ آزادِ صبا.

        خروجی: رشته‌ی پاسخ (همیشه content-free، گرم، حرفه‌ای) یا None اگر
        نمی‌تواند پاسخ بدهد (در این صورت saba_studio به fallbackِ خودش می‌رود).

        رفتار:
          - اگر متن scrub نشد (PII) → پاسخِ محترمانه + None برای fallback.
          - اگر cortex online و پاسخ داد → پاسخِ LLM.
          - در غیر این صورت → پاسخِ heuristic از intent.
        """
        self._ticks += 1
        _ev.emit("task.started", status="ok",
                 summary="saba-ask", duration_ms=0)
        t0 = time.monotonic()
        try:
            intent = self._classify_saba_intent(text)
            # scrubbed prompt برای cortex (هرگز محتوای raw)
            scrubbed = scrub_for_cortex(text)
            if not scrubbed:
                # PII/محتوا در متن یا غیرقابل-درک — هرگز پاسخِ محتوایی نده (نامتغیرِ PII).
                # حالت‌ها: (الف) متن PII دارد (scrub reject) یا (ب) متن خالی/بی‌معنی است.
                # در هر دو حالت، saba_studio به fallbackِ نرم خودش می‌رود.
                _ev.emit("task.blocked", status="ok",
                         summary=f"saba-ask: scrub-reject:{intent}")
                return None  # saba_studio به fallback می‌رود

            # ساختِ promptِ عملیاتی (نه محتوای draft):
            # فقط intent + سؤالِ کلی درباره‌ی فرآیند (نه درباره‌ی محتوای خاص)
            op_prompt = self._build_operational_prompt(intent, scrubbed)
            r = cortex_client.ask("saba_chat", op_prompt, max_tokens=200)
            ms = int((time.monotonic() - t0) * 1000)
            if r.get("ok") and r.get("text", "").strip():
                response = self._shape_for_saba(r["text"], intent)
                self._last_saba_response = {
                    "intent": intent, "source": "cortex",
                    "tier": r.get("tier", "?"), "ms": ms,
                }
                _ev.emit("task.completed", status="ok",
                         summary=f"saba-ask:cortex:{intent}",
                         duration_ms=ms)
                return response
            # fallback به heuristic
            response = self._heuristic_saba_response(intent)
            self._last_saba_response = {
                "intent": intent, "source": "heuristic",
                "reason": r.get("reason", ""), "ms": ms,
            }
            _ev.emit("task.completed", status="ok",
                     summary=f"saba-ask:heuristic:{intent}",
                     duration_ms=ms)
            return response
        except Exception as e:  # noqa: BLE001 — مغز نباید استودیو را بکُشد
            ms = int((time.monotonic() - t0) * 1000)
            _ev.emit("task.failed", status="failed",
                     summary=f"saba-ask:err:{type(e).__name__}",
                     duration_ms=ms)
            return None  # fallback به saba_studio

    def _classify_saba_intent(self, text: str) -> str:
        """intent classification ساده (heuristic، $0). خروجی:
        price | schedule | trend | boundary | general | unknown
        """
        if not text:
            return "unknown"
        t = str(text).strip().lower()
        if any(w in t for w in ("قیمت", "price", "چقدر", "تی‌یر", "tier", "$", "دلار")):
            return "price"
        if any(w in t for w in ("کی", "when", "ساعت", "زمان", "امروز", "فردا", "time")):
            return "schedule"
        if any(w in t for w in ("ترند", "trend", "مد", "ایده", "idea", "hot")):
            return "trend"
        if any(w in t for w in ("محدوده", "boundary", "خسته", "استراحت", "halt", "stop", "نه")):
            return "boundary"
        if any(w in t for w in ("سلام", "hi", "hello", "چطوری", "ممنون", "مرسی")):
            return "general"
        return "general"

    def _build_operational_prompt(self, intent: str, scrubbed: str) -> str:
        """ساختِ promptِ عملیاتی برای cortex. هرگز محتوای draft را پاس نمی‌دهد.

        مثال (price): «خالقِ محتوای faceless feet-only می‌پرسد قیمتِ PPV چیست.
        یک راهنماییِ کوتاهِ ۲-۳ جمله‌ای درباره‌ی قیمت‌گذاریِ contextual بده.»
        """
        prompts = {
            "price": ("A faceless feet-only content creator is asking about PPV pricing. "
                      "Give a 2-3 sentence warm, practical guidance on contextual pricing "
                      "(no real numbers needed)."),
            "schedule": ("A creator asks about posting schedule. Give 2-3 sentence warm "
                         "guidance on optimal timing."),
            "trend": ("A creator asks about trends. Give 2-3 sentence warm guidance on "
                      "how to spot and use seasonal trends."),
            "boundary": ("A creator mentions boundaries or feeling tired. Respond warmly "
                         "with 2-3 sentences affirming their right to rest."),
            "general": ("A creator said something casual. Respond warmly in 2-3 short "
                        "sentences, asking how you can help."),
        }
        return prompts.get(intent, prompts["general"])

    def _shape_for_saba(self, llm_text: str, intent: str) -> str:
        """شکل‌دهی نهایی پاسخِ LLM برای صبا: گرم، کوتاه، content-free."""
        t = (llm_text or "").strip()
        if not t:
            return self._heuristic_saba_response(intent)
        # محدود کردن به ۳۵۰ کاراکتر (تلگرام-friendly)
        if len(t) > 350:
            t = t[:347] + "…"
        # اگر LLM از کلمه‌ی ممنوعه‌ای استفاده کرد، scrub
        tl = _fa_norm(t)
        for bad in _SCRUB_TERMS:
            if bad and _fa_norm(bad) in tl:
                return self._heuristic_saba_response(intent)
        return t

    def _heuristic_saba_response(self, intent: str) -> str:
        """پاسخِ heuristic گرم برای هر intent. همیشه content-free."""
        return {
            "price": ("💰 برای قیمت، بهتره اول تمِ این هفته + بافرِ محتوا رو ببینیم. "
                      "اپراتور از مغز قیمتِ دقیق رو می‌گیره و برات می‌فرسته. 🌸"),
            "schedule": ("🗓 بهترین زمانِ پست معمولاً عصر‌ها‌ست. تمِ هفته + ۱ ست تازه "
                         "یه شروعِ خوبه. برای تقویمِ دقیق، «📅 تقویم» رو بزن."),
            "trend": ("🔎 ترندهای فصلی معمولاً چند هفته زودتر themselves نشون می‌دن. "
                      "برای ایدهٔ دقیقِ امروز، «🌟 امروز چیکار کنم» رو بزن."),
            "boundary": ("✋ محدوده‌ت همیشه مقدمه. هر وقت خواستی استراحت کنی، "
                         "«/halt» کافیه — همه‌چی وایمیسه. 🌿"),
            "general": ("سلامِ گرم 🌸 برای شروعِ درفت «📤» رو بزن، یا یکی از دکمه‌های "
                        "منو. هر سؤالی داری بپرس."),
        }.get(intent, "🌸 از منو یه دکمه بزن، یا برای ثبتِ درفت «📤».")

    # ── رابطِ عمومیِ think (برای loop/api) ──
    def think(self, task: str, prompt: str, max_tokens: int = 300) -> BrainResponse:
        """فراخوانیِ cortex با fallbackِ صادقانه. برای API endpoint /api/brain/ask.

        خروجی همیشه BrainResponse سالم — هیچ‌وقت exception بیرون نمی‌رود.
        """
        t0 = time.monotonic()
        scrubbed = scrub_for_cortex(prompt)
        if not scrubbed:
            return BrainResponse(
                ok=False, text="", source="fallback", ms=0,
                reason="scrub-reject (PII or empty)")
        r = cortex_client.ask(task, scrubbed, max_tokens=max_tokens)
        ms = int((time.monotonic() - t0) * 1000)
        if r.get("ok"):
            return BrainResponse(
                ok=True, text=r.get("text", ""), source="cortex",
                tier=r.get("tier", "?"), ms=ms)
        return BrainResponse(
            ok=False, text="", source="fallback", tier=r.get("tier", "none"),
            ms=ms, reason=r.get("reason", ""))

    # ── state snapshot (برای /api/health) ──
    def status(self) -> dict:
        return {
            "heuristic_loaded": self._heuristic is not None,
            "compliance_rules": len(_COMPLIANCE_RULES),
            "ethics_rules": len(_ETHICS_RULES),
            "cortex": cortex_client.health(),
            "ticks": self._ticks,
            "last_saba_response": dict(self._last_saba_response),
        }
