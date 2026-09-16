# ADR-034 Controlled Restart — AFTER

- captured_at: 2026-08-11T21:13:20+10:00
- restart_script: `_ops/RESTART-ALL.ps1`
- acceptance_gate: FAILED initially (`organism : no fresh state` within 120s); organism PID was live; fresh `ORGANISM-STATE` appeared ~21:13:00 (beat 31652). Flags already equal across limbs at gate time.

## Processes (new)

| Process | PID | Start time (local) |
|---|---|---|
| organism | **15916** | 2026-08-11 **21:10:38** |
| brain_worker | — | still not a standalone process (in-organism neural path) |
| cortex | 22976 | 21:09:40 |
| center | 21968 | 21:10:05 |
| gateway | 14904 | 21:10:15 |
| live | 21528 | 21:10:17 |

PID map vs before: organism 23724→15916; cortex 9164→22976; center 22532→21968; gateway 9476→14904; live 4352→21528.

## Effective flags (post-reload)

| Flag | organism | live | center | cortex |
|---|---|---|---|---|
| OCTOPUS_NEURAL_LEARNED_APPLY | **0** | **0** | **0** | **0** |
| OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL | **1** | **1** | **1** | **1** |
| flag count | 316 | 316 | 316 | 316 |

## Legacy protective_skip

| Before | After first fresh tick |
|---|---|
| skip=true, mode=true, reason=`pain=0.38>0.35 [+learned=0.25:rhythm_amber]…` | **skip=false**, mode cleared, proposal absent (live pain below thr) |
| Treated as LEGACY, not pass/fail | New writer: organism PID 15916 `_write_state`; neural path did **not** re-assert skip |

## High-pain tick assertion (consumer contract)

Input: `pain.level=0.95` via `wiring.protective_override` (same dict organism consumes).

| Check | Result |
|---|---|
| action | `protective_proposal` |
| override / executable | False / False |
| shadow_alert | True |
| protective_halt | **not** emitted |
| simulated `_protective_skip` | stays **False** |
| live ORGANISM-STATE protective_skip | **False** |

## Invariants locked (until Stage 2–3 complete)

```
OCTOPUS_NEURAL_LEARNED_APPLY=0
OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL=1
neural-learned-apply.evidence_level=SHADOW
neural-learned-apply.authority.allowed_effect=trace_only
neural-learned-apply.authority.may_gate=false
neural-learned-apply.production_apply_enabled=false
```
