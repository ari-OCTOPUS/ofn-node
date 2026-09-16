---
type: interface
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
tags: [ziman, octopus, architecture]
created: 2026-07-12
updated: 2026-07-12
---

# BIOLOGY CONTRACT — Ziman ↔ Heart ↔ Nerves ↔ Evolutionary Doctor

## Parent relationship

Ziman remains an isolated OCTOPUS limb. It is now a **subordinate consumer** of the organism's biological control plane:

```text
Heart (rhythm/setpoint only)
        ↓
Neural SignalHub / spinal cord (advisory snapshot)
        ↓
ZimanLeg (propose-only)
        ↓ anomaly trace, content-free
Evolutionary Doctor (sandbox RFC only)
        ↓
human-append approval gate
```

## Accepted constitutional rules

1. **Heart is regulator, not commander.** Ziman reads rhythm; it cannot write heart parameters.
2. **Nerves are advisory.** `SignalHub` carries snapshots; it has no effector authority.
3. **Doctor is propose-only.** It may diagnose and generate sandbox-tested RFCs; it cannot auto-merge.
4. **Human append is mandatory** for every merge, production change, publish, spend, price, or customer communication.
5. **STOP / protective mode wins** over all Ziman work.
6. **σ ≤ 1.** Values above one create a critical cancer-risk anomaly and protective mode.
7. **No self-preservation objective.** `lambda_persist` remains negative; uptime is not a reward.
8. **No PII or secret crosses the limb boundary.** Doctor receives only content-free anomaly codes.
9. **Cognition ≠ effect.** Diagnosis, proposals and Telegram previews do not execute an external action.
10. **D4 remains authoritative.** No campaign proposal exceeds verified capacity.

## Runtime implementation

- `_ops/legs/ziman_biology.py` — read-model + assessment + SignalHub + Doctor trace.
- `_ops/legs/ziman_leg.py` — accepts only safe `ziman-biology.v1` snapshots.
- `_ops/wiring.py` — `ziman_beat(..., doctor=...)` calls `biology_beat`.
- `_ops/organism.py` — injects the existing evolutionary doctor into the Ziman beat.
- `_ops/tests/test_ziman_biology.py` — offline invariants.

## Explicit non-capabilities

Ziman cannot:

- change heart setpoint or beat period;
- alter neural policy;
- merge Doctor RFCs;
- publish, send, DM, pay, spend, deploy or change public price;
- write canonical memory;
- read outside its allowlist.

## Rollback

1. Set `OCTOPUS_WIRE_ZIMAN=0` to disable the full limb seam.
2. Remove Doctor injection from the single `organism.py` call if biology diagnosis must be isolated.
3. The adapter is additive; no product data migration is required.
