# Architecture — Nervous-System Recovery

```text
Scanner Agents
   ↓ evidence-only receipts
Evidence Normalizer     receipt_v2 / test_discovery / capability_parser
   ↓ canonical Finding / Test / Capability
Reality Governor        wave0_governor.audit_wave0
   ↓ hard gates + confidence + staleness
Repair Planner          repair_planner.dag  (applies=false)
   ↓ dependency DAG + bounded patches
Verifier                test_nervous_recovery.py
```

Invariant: a finding is not reality without a hashed evidence ref. A capability is not VERIFIED without declaration + call path + recent observation + receipt.

GitHub is not the source of truth for this vault; germline + local commits are.
