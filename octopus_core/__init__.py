"""octopus_core — هسته مرکزی اختاپوس.

ماژول‌ها:
  event_bus              — سیستم عصبی (pub/sub lightweight)
  capability_registry    — قابلیت‌نامهٔ داینامیک
  actuator               — قلب اجرا / motor cortex (shadow → dry_run → live)
  telemetry              — sensory loop / حلقهٔ حسی
  health                 — unified heartbeat / نبض ارگانیسم

طراحی:
  • stdlib-only — هیچ dependency خارجی
  • threading-safe (قفل‌گذاری)
  • file-based persistence (JSONL + JSON)
  • zero network calls (actuator هنوز wiring بیرونی ندارد)
"""
from __future__ import annotations

__all__ = [
    "event_bus",
    "capability_registry",
    "actuator",
    "telemetry",
    "health",
]
