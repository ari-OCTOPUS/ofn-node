---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, interface, adr]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P2 — interfaceِ typed قلب + ratifyِ ADR-001

> gate خروج: **interface-locked**. پیش‌نیاز: HH-P0 (قفل ریاضی) و HH-P1 (producerها) — چون فیلدها باید به سیگنال‌های واقعی اشاره کنند، نه خیالی.

## مأموریت

مرزِ سختِ ADR-001 را به کدِ typed تبدیل کن — «Doctor setpoint می‌نویسد، نه نرخ» را ساختاراً غیرقابل‌نقض کن — و ADR-001 موجود را **ratify** کن (append، هرگز بازنویسی؛ supersede-chain کثیف نشود).

## زمین (ADR-001 §مرز سخت — verbatim)

```text
# Doctor → Heart  (فقط setpoint، هرگز نرخِ اسکالر)
HeartParams { target_sigma, viable_band:(lo,hi), epoch_seq,
              target_mass_scale, daily_beat_cap, baroreflex_gain }
# Heart → Doctor  (فقط سیگنال؛ read-only از منظرِ Doctor)
HeartSignal { beat_seq, period_s (tempo), sigma_now, baro_factor (arousal) }
# منبعِ حقیقتِ σ — بیرونِ هر دو، در LANGAR:
sigma_now ← از رویدادهای CONFIRMED محاسبه می‌شود، نه ادعای Doctor
```

تفسیرِ hybrid (master-plan بخش ۱): `viable_band` = **باندِ هدفِ velocity** (واحد: item/ساعت از velocity_meter) — SOG/Doctor باند می‌دهد؛ نرخ (period) از dynamics *ظاهر* می‌شود.

## تحویل‌دادنی‌ها

1. **`_ops/heart/interface.py`** (stdlib، frozen dataclasses):
   - `HeartParams(target_sigma: float, viable_band_lo: float, viable_band_hi: float, epoch_seq: int, target_mass_scale: float = 1.0, daily_beat_cap: int = 288, baroreflex_gain: float = 0.0)` + `validate()` (کران‌های مطلق: band مثبت و `lo≤hi`؛ `target_sigma≤1.0` — قانونِ اساسیِ σ-cap؛ cap مثبت) + `to_json/from_json`.
   - `HeartSignal(beat_seq: int, period_s: float, sigma_now: float | None, baro_factor: float = 1.0)` — دقیقاً چهار فیلدِ ADR؛ متادیتای اضافه (velocity/cpi/Δ_self) در `HeartTelemetry` جدا (additive، ADR دست‌نخورده).
   - **هیچ فیلدِ rate/bpm/period در HeartParams وجود ندارد** — این همان anti-patternِ «نرخ‌دادن» است؛ ساختاراً حذف.
   - `write_setpoint(params, path)` / `read_setpoint(path)` — اتمیک، fail-soft؛ سینک: `_ops/state/pulse/heart-setpoint-latest.json`.
2. **ratifyِ ADR-001**: به انتهای `06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged.md` یک بخشِ تاریخ‌دارِ append کن: «Ratified in code — 2026-07-10: interface در `_ops/heart/interface.py`؛ viable_band=velocity-band (hybrid)؛ σ همچنان فقط از CONFIRMED (`replication.sigma_state`)؛ فرمالیسم فعلی allostatic، FHN=milestone M-♥.» + `updated:` امروز. **هیچ سطرِ موجود عوض نمی‌شود.**
3. **تست** در `_ops/tests/test_heart_loop.py`: validate ردِ band منفی/وارونه و σ>1؛ round-trip json؛ ساختاری: `HeartParams.__dataclass_fields__` هیچ نامی شبیه `rate|bpm|period` ندارد.

## خطوطِ قرمز

ADR بازنویسی نمی‌شود (فقط append) · σ هرگز از ادعای Doctor/Heart، فقط `replication.sigma_state` روی ledger · frozen dataclass (immutable setpoint؛ تغییر = نوشتنِ setpointِ نو با epoch_seq جدید) · stdlib-only.
