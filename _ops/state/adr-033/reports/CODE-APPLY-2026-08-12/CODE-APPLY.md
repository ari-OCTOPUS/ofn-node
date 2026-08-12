---
type: evidence
created: 2026-08-12
topic: code-apply-lowrisk
---

# CODE APPLY (low-risk) — verdict → apply_approved → worker

## Chain (truth)

`lead_effect_gate` is **not** on this path. Live analogue:

```
verdict (HITL ✅ or auto-lowrisk stamp)
  → code_autonomy.apply_approved  (8 gates = effect gate)
  → _git_apply_canary             (worker write + baseline/canary suite)
```

Drivers (organism boot):
- `OCTOPUS_WIRE_CODE_APPLY=1` → thread `code-apply` (`run_forever` / `consume_approvals`)
- `OCTOPUS_WIRE_CODE_BRAIN=1` + `OCTOPUS_CODE_BRAIN` → `code_brain` feeds tasks
- `OCTOPUS_CODE_AUTOAPPLY_LOWRISK=1` → stamp + `apply_approved` when low-risk

## Hardening 2026-08-12

- `code_brain.tick_once`: `low_risk_patch` **before** auto stamp
- `OCTOPUS_CODE_APPLY_REFRACTORY_S` (default 3600, set **300**)
- `OCTOPUS_CODE_SHADOW_SUITE_TIMEOUT_S=2400` (was 1800 default; last live fail = TimeoutExpired)
- pending patch `code-7f23376b44` (`_ops/cortex/discoveries.py`) verified `low_risk=true` (4 lines)

## Live apply (2026-08-12)

| Step | Result |
|---|---|
| risk | `low_risk=true` (4 lines, `discoveries.py`) |
| approval stamp | auto-lowrisk |
| git commit | **`75c1288`** landed (`mark_nudged(high_water)`) |
| canary receipt | `TimeoutExpired` (race: parallel apply + 2400s ceiling) |
| WT after timeout | rolled back; **restored to HEAD** |
| hardening | apply lock · baseline cache · `LOWRISK_FAST_CANARY=1` · timeout 3600 · refractory 300 · pre-check low_risk in code_brain |

### Truth of chain
`verdict → code_autonomy.apply_approved (effect gate) → _git_apply_canary (worker)`  
Not `lead_effect_gate`.
