---
type: handoff
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: local-complete-test-pending
created: 2026-07-12
updated: 2026-07-12
tags: [ziman, octopus, biology, heart, doctor, nerves, completion]
---

# ZIMAN BIOLOGY COMPLETION HANDOFF

## Summary

Ziman is now connected as an OCTOPUS limb under the organism's biological control plane:

```text
Heart read-model
  → Neural SignalHub / nerves
  → ZimanLeg propose-only state
  → content-free anomaly trace
  → Evolutionary Doctor RFC path
  → human-append approval gate
```

This is a **local/propose-only completion**, not a live external launch.
No Telegram live activation, no publish, no send, no spend, no price approval and no customer action occurred.

## Implemented Runtime Surfaces

| Surface | File | Status |
|---|---|---|
| Ziman limb | `_ops/legs/ziman_leg.py` | built |
| Biology adapter | `_ops/legs/ziman_biology.py` | built |
| Wiring seam | `_ops/wiring.py::make_ziman_leg`, `ziman_beat(..., doctor=...)` | built |
| Organism injection | `_ops/organism.py` → `ziman_beat(..., doctor=_doctor_inst)` | built |
| Heart contract | `10-Interfaces/BIOLOGY-CONTRACT.md` | documented |
| Neural contract | `SignalHub` advisory snapshot | used read-only |
| Doctor contract | Doctor RFC-only / human-append | used as injected dependency |
| State output | `_ops/state/ORGANISM-STATE.ziman` | atomic write path |

## Accepted Laws

1. Ziman cannot write heart setpoints, period, rhythm or policy.
2. Ziman cannot alter neural policy; nerves are advisory only.
3. Evolutionary Doctor can generate RFCs only; no auto-merge.
4. Human append approval is mandatory for material changes.
5. STOP / protective mode overrides Ziman.
6. Sigma greater than 1 creates critical anomaly and protective mode.
7. Lambda-persist remains negative; uptime/self-preservation is not rewarded.
8. Doctor receives content-free anomaly traces only.
9. No PII/secrets cross the limb boundary.
10. D4 capacity-first remains authoritative.

## Tests Added / Registered

| Test file | Scope |
|---|---|
| `_ops/tests/test_ziman_leg.py` | limb isolation, D4, no effectors |
| `_ops/tests/test_ziman_wiring.py` | make_ziman_leg, ziman_beat, biology doctor injection |
| `_ops/tests/test_ziman_biology.py` | heart/nerves/doctor laws |
| `_ops/tests/test_ziman_phase2.py` | validators and inventory/product rules |
| `ziman-agent/tests/test_product.py` | local product/ATP/JSON card behavior |

`_ops/tests/run_all.py` now includes the Ziman test family and uses pytest for pytest-style tests.

## Execution Commands

Local Ziman agent tests:

```bat
cd /d "F:\backup\03 - Projects\Ziman Galerry\ziman-agent"
START-ZIMAN.bat
```

Octopus wiring and biology tests:

```bat
cd /d F:\backup\_ops
RUN-ZIMAN-OCTOPUS-TESTS.bat
```

Direct pytest form:

```bat
cd /d F:\backup
python -m pytest _ops\tests\test_ziman_leg.py _ops\tests\test_ziman_wiring.py _ops\tests\test_ziman_biology.py _ops\tests\test_ziman_phase2.py -q
```

## Known Non-Completion Items Requiring Owner Data

These are not code blockers; they require real owner inputs:

1. Inventory classification scope: A / B / C.
2. Real product family counts C1-C4.
3. Product photo-to-ID confirmations.
4. Capacity revalidation; legacy 30/week remains conflicted/unverified.
5. Any public price approval.
6. Any Telegram live token/owner allowlist activation.

## Rollback

All changes are additive. Rollback options:

1. Set `OCTOPUS_WIRE_ZIMAN=0`.
2. Delete `_ops/legs/ziman_biology.py` to remove the biology adapter.
3. Revert the single organism call to `ziman_beat(_ziman_leg, beat=...)` without `doctor=_doctor_inst`.
4. Remove Ziman test files from `run_all.py` if emergency isolation is needed.

## Final Local Status

`LOCAL-COMPLETE / TEST-RUN-PENDING / NO-EXTERNAL-ACTION`
