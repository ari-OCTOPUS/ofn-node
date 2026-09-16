# DecisionLog — research-spec-compiler cognitive organ

Append-only. Machine verdicts from `rsc.py run` on REAL data; each traces to an ADR.

| date | ADR | hypothesis | verdict | primary [FACT] |
|---|---|---|---|---|
| 2026-07-13 | ADR-001 | H-OWN-03 WM bottleneck (absolute bar) | **REJECTED** | transfer 0.520 < 0.67 kill line |
| 2026-07-13 | ADR-002 | Drake census over sim universes | **OPTIMIZE** | f_transfer 0.600 |
| 2026-07-14 | ADR-003 | RTA geometry (principle #7) | **OPTIMIZE** | ρ 0.662 (shuffle null 0.022) |
| 2026-07-14 | ADR-004 | H-OWN-03 v2 (relative bar) | **OPTIMIZE** | paired_gain 0.169 |
| 2026-07-14 | ADR-005 | Homeostasis MPC self-model | **OPTIMIZE** | advantage_ood 0.029 |
| 2026-07-14 | ADR-006 | Consolidation = library learning | **INTEGRATE** | schema_vs_replay +0.045 |
| 2026-07-14 | ADR-007 | Central Law governance (3 gates) | accepted | — (firewall, not an experiment) |
| 2026-07-14 | ADR-008 | Hybrid cortex on real body | **OPTIMIZE** | bottleneck_advantage 0.036 |

## Discipline notes (why these are trustworthy)

- Every verdict is a machine output of a preregistered `decision_rule` on a REAL
  run (not synthetic mocks; `[REAL run — …]` provenance).
- Each experiment passed an adversarial review; confirmed findings were applied
  before finalizing. Notably ADR-008's FIRST gate was a blocker (a trivially-
  clearable absolute-accuracy metric); it was re-gated on the falsifiable
  quantity and the verdict honestly fell from an inflated INTEGRATE to OPTIMIZE.
- pilot/confirmatory seed separation with frozen parameters throughout.

## Standing firewall (ADR-007)

The economy gate may reorder WHICH experiment runs next; it may NEVER bend a
verdict. Products built on these capabilities must carry scope-honest claims
(sell "learned feature gating" / "RTA scores", never "consciousness").
