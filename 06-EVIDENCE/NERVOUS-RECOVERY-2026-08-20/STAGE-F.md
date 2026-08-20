---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, capability]
---

# Stage F — capability immunity (10 EFFECTORS)

Parser: AST of `_ops/effector_registry.py` (sha256 in WAVE0-GATES.json).
Observation: `receipt_backed=false` for these sensors in cost-receipts (they are not model.call.paid).
VERIFIED requires declaration + callable + recent receipt + test — **none meet receipt**.

Status is computed by `_ops/nervous_recovery/capability_immune.py`. Re-run cards at audit time; counts live in `CAPABILITY-INVENTORY.json`.

| capability | registry | truth | evidence |
|---|---|---|---|
| bcm.learned_pressure | armed-apply | DECLARED_UNOBSERVED | effector_registry + wiring.py |
| bcm.weights_bidirectional | display-only | DORMANT | no actuator |
| hebbian.associations | display-only | DORMANT | no actuator |
| consolidation.insights | wired | DECLARED_UNOBSERVED | callable, no cost-receipt |
| deep_dive.smallest_fix | partial | DECLARED_UNOBSERVED | propose-only |
| c6.hypothesis_producer | wired | DECLARED_UNOBSERVED | callable, no cost-receipt |
| self_model.pathology | display-only | DORMANT | no actuator |
| effect_shadow.would_throttle | shadow | DORMANT | no actuator |
| vault_bridge.rag_evidence | wired | DECLARED_UNOBSERVED | callable, no cost-receipt |
| latent_space.vector | display-only | DORMANT | no actuator |

None are VERIFIED: cost-receipts use `model.call.paid`, not these effector ids. Structural `test_effector_registry.py` is not a per-capability live test.

| rule | meaning |
|---|---|
| VERIFIED | declaration + actuator + recent receipt + test |
| DECLARED_UNOBSERVED | declared+callable, no attributable receipt |
| DORMANT | no actuator / dead-output / unreachable path |
| BLOCKED | explicit hard prerequisite (none of the 10) |

C-048..C-053 remain **candidates** in `reality-ledger.jsonl`. Not copied to CONTRADICTIONS.md.
