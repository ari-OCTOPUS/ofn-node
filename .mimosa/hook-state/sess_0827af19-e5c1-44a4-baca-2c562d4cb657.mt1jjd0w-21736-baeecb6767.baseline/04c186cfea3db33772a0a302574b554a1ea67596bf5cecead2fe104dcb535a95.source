"""_ops/synapse — اندامِ سیناپس: نقطه‌ی اتصالِ ریاضیِ SOG به تله‌متریِ خودِ ارگانیسم.

همه‌ی ماژول‌ها: propose-only · پیش‌فرضِ خاموش (flag-gated) · fail-closed.
هیچ‌کدام روی genome/، ledger.jsonl، state/، .env یا budget نمی‌نویسند.
خروجی فقط در _ops/synapse/out/ است.

ماژول‌ها:
  sense               — SENSE: E_shadow/Δ_self proxy روی جریانِ رویدادِ خودِ ارگانیسم.
  trajectory_monitor  — P3: تشخیصِ ناهنجاریِ زنجیره‌ای (burst/novel-chain/egress).
  egress_policy       — P1: سیاستِ egress deny-by-default (policy-as-data، wiring=tapِ مالک).
"""

__all__ = ["sense", "trajectory_monitor", "egress_policy"]
__version__ = "0.1.0"
