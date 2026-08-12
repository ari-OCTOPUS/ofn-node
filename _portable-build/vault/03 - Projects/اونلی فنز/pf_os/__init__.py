#!/usr/bin/env python3
"""pf_os — Project-F OS: یک OS مستقلِ ماژولار برای پا/دامنه‌ی Project-F.

لایه‌ها (همه additive، flag-off، $0 آفلاین، stdlib-only):
  config        — env + fallbacks + flag()
  cortex_client — POST :8772/ask به cortexِ مرکزی + heuristic fallback
  events        — wrapper روی _ops/events.py (logger، نه bus)
  brain         — مغزِ ماژولار (BrainCore + LearningBus + Guard) [فاز ۲]
  loop          — حلقه‌ی tick مستقل [فاز ۳]
  api           — REST API روی stdlib http.server [فاز ۴]
  bridge        — نوشتنِ events به saba-bridge.jsonl [فاز ۵]

نامتغیرها:
  - هیچ PII/هویت/محتوا/پلتفرم به cortex یا saba-bridge نمی‌رود (content-free).
  - هر اکشنِ بیرونی propose-only است (publish/send/pay نیاز به verdict انسانی دارد).
  - همه‌ی رفتارِ نو پشتِ flag است (default OFF = بایت‌به‌بایتِ امروز).
  - صفر dependency بیرونی.
"""
from __future__ import annotations

__version__ = "0.1.0"

from . import config  # noqa: F401
from . import cortex_client  # noqa: F401
from . import events  # noqa: F401

# ─── اندام‌های نسخهٔ به‌روز (انطباق اختاپوس 2026-07-22) ───────────────────────
# همه additive، $0، stdlib-only. import اختیاری/fail-soft تا اگر یکی مشکل داشت،
# لایه‌های پایه (config/events) نشکنند و pf_os همچنان بالا بیاید.
try:
    from . import event_bus  # noqa: F401   — سیستم عصبی (taxonomy+trace+health)
    from . import telemetry  # noqa: F401   — حلقهٔ حسی ساخت‌یافته
    from . import capabilities  # noqa: F401 — registry + دلیل خاموشی پویا
    from . import actuator  # noqa: F401     — motor cortex (shadow/dry-run/live-locked)
    from . import eval_loop  # noqa: F401    — حلقهٔ eval→learn
    _OCTOPUS_ORGANS = ["event_bus", "telemetry", "capabilities", "actuator", "eval_loop"]
except Exception:  # noqa: BLE001 — fail-soft: پایه بدون اندام‌های نو هم کار کند
    _OCTOPUS_ORGANS = []

__all__ = ["config", "cortex_client", "events", "__version__"] + _OCTOPUS_ORGANS
