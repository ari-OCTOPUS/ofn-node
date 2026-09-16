# ADR-036 — Math Control Spine (معادلات → pulse + soft effects)

- **Status:** ACCEPTED — owner verdict 2026-08-12 («سقف اختیار خیلی نرم؛ سایه جلوی اثر را نگیرد»)
- **Date:** 2026-08-12
- **Supersedes:** — (افزونهٔ ADR-033/035؛ مستقل)
- **Preserves:** `may_authorize=false` در معادلات · PolicyGate مرجع · ledger/age_tick دست‌نخورده · run_all/registry قفل
- **Evidence:** `_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/00-DISCOVERY-REPORT.md` (§۲ C2)
- **Owner verdicts:** `_ops/owner-verdicts.yaml` → `math_control_spine=1` · `math_autotune_knobs=1`

## Problem (پیشینهٔ C2)

`math_control/spine.py` و رأی‌های `owner-verdicts.yaml` و `organism.py`/`cortex/improve.py`
به ADR-036 ارجاع می‌دادند ولی فایل ADR وجود نداشت. این سند آن شکاف را می‌بندد و
**حکم واقعی تصمیم** را ثبت می‌کند — بدون تغییر هیچ کد/flag (همه‌چیز از قبل زنده بود).

## Decision

1. **Spine = gatherer read-only:** معادلات زنده (hebbian, bcm, spectral σ, organism slice,
   identity, SOG VoI) هر tick جمع می‌شوند → snapshot + parallel observe telemetry.
2. **Soft effects فقط:** خروجی spine از جنس `effects` (مثل `protective_skip`,
   `autotune_propose`, `improve_rank_bias`, `schedule_bias_hint`) است —
   **هیچ‌کدام gate/policy/ledger را نمی‌نویسد**.
3. **AUTO_KNOBS سفید:** با `OCTOPUS_MATH_AUTOTUNE_KNOBS=1` فقط knobهای سفید
   (`CORTEX_THINK_EVERY_N`, `CHRONO_NUDGE_EVERY_N_BEATS`, `HEART_SAMPLE_INTERVAL_S`)
   و نیازمند `ACT_AUTO`. هرگز کد/پول/ارسال.
4. **observe موازی است نه گیت:** `_observe_append` به `state/pulse/math-control-observe.jsonl`
   fail-soft است؛ شکستش هیچ اثری روی tick ندارد (`shadow_blocks_effects=false`).

## Flags

| Flag | Default | معنا |
|------|---------|------|
| `OCTOPUS_MATH_CONTROL_SPINE` | 1 (verdict) | spine enabled |
| `OCTOPUS_MATH_AUTOTUNE_KNOBS` | 1 (verdict) | AUTO_KNOBS سفید مجاز |

## Capability truth

| Field | Value |
|---|---|
| Capability | math-control-spine |
| truth_status | TESTED |
| evidence_level | SHADOW→ARMED (رأی مالک؛ اثر soft فقط) |
| production_apply_enabled | **true** (فقط soft effects) |
| allowed_effect | bounded_ranking_bias / autotune_propose |
| may_gate | **false** (هرگز gate) |
| may_mutate_ledger / may_trigger_tool / external | false |

## Fail-closed / boundaries

- `may_authorize=false` در همهٔ معادلات و spine.
- هیچ `EXTERNAL_SEND / LIVE-ENABLED / money` از این مسیر.
- `rank_bias` کران‌دار (بازهٔ محدود)؛ `suggest_knob_deltas` bounded.
- Ledger/age_tick/PolicyGate دست‌نخورده. Rollback: flag `=0` در flags.cmd + restart.

## Non-claims

هیچ ادعای AGI/آگاهی. معادلات سیگنال می‌دهند؛ تصمیم نهایی از PolicyGate/مالک.

## Sources

- `_ops/math_control/spine.py` (collect/effects/suggest_knob_deltas)
- `_ops/math_control/__init__.py`
- `_ops/organism.py` (inline ref)
- `_ops/cortex/improve.py` (AUTO_KNOBS integration)
- `_ops/owner-verdicts.yaml` (math_control_spine / math_autotune_knobs)
- `_ops/state/pulse/math-control-observe.jsonl` (telemetry)
