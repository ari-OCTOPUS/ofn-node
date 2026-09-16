# ADR-035 Re-arm Evidence — 2026-08-12

Owner verdict: «هردو» = set `OCTOPUS_NEURAL_LEARNED_APPLY=1` **and** restore executable apply.

## What changed

| Layer | Change |
|---|---|
| ADR | `ADR-035-neural-learned-apply-rearm.md` (supersedes ADR-034 apply containment) |
| Flag | `_ops/OCTOPUS-flags.cmd` → `OCTOPUS_NEURAL_LEARNED_APPLY=1` |
| Wiring | `emit_pain_assessment` dual-mode: APPLY=0 proposal; APPLY=1 executable halt/throttle |
| Consumers | `organism.py` / `brain_worker.py` set skip only when `executable=True` |
| Registry | `neural-learned-apply` → ARMED · gate_internal · may_gate=true · production_apply_enabled=true |
| Tests | `test_adr035_neural_rearm.py` + dual-mode updates to ADR-034 / frontier / protective suites |

## Preserved

- PainAssessment immutable record
- `request_protective_halt` PolicyGate path
- learned_pressure **cap**
- effect-shadow / pain-assessment JSONL
- No EXTERNAL_SEND / LIVE-ENABLED / money from this path

## Rollback

1. `set OCTOPUS_NEURAL_LEARNED_APPLY=0` in `OCTOPUS-flags.cmd`
2. Restart organism / brain_worker so flags reload

## Live closeout (2026-08-12 ~07:26–07:38)

| Check | Result |
|---|---|
| Organism restart | pid 25108→**10460** · started `2026-08-12T07:26:00` |
| `flags-loaded-*.json` APPLY | organism/cortex/center/live/gateway all **`1`** |
| First live pain-assessment | `07:26:04` · adr=**ADR-035** · `learned_apply_flag=true` · pain=0.165 · action=none |
| Beat after restart | beat 32248+ · `protective_skip=false` (pain below thr — correct) |
| Codepath probe (organism flags) | high→`protective_halt` executable · critical→`throttle` executable · low→none |
| Artifact | `ADR-035-LIVE-VERIFY.json` |

## Verification checklist

- [x] `python _ops/tests/test_adr035_neural_rearm.py` → 7/7
- [x] `python _ops/tests/test_adr034_neural_demote.py` → 10/10
- [x] `python _ops/tests/test_organism_protective.py` → 9/9
- [x] `python _ops/scripts/validate_signals_registry.py` → ok
- [x] Related: frontier / neural_loop_close / hebbian / truthmap / pain_calibration green
- [x] Restart organism → `flags-loaded-organism.json` shows APPLY=1
- [x] All limbs flags APPLY=1 (center/cortex/live/gateway restarted)
- [x] Executable path proven under live flags (probe → `ADR-035-LIVE-VERIFY.json`)
- [x] Live healthy beat does **not** skip when pain < threshold (skip=false @ pain≈0.16–0.21)
