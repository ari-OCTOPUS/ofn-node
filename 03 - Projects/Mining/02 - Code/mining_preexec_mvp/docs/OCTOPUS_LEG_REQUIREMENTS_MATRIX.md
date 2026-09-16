# Requirements Matrix — Octopus Mining Leg v1.0

> Date: 2026-07-12  
> Scope: verify that the Mining module is attached as an Octopus leg with two brains and Telegram visibility.  
> Mode: **pre-execution / report-only / propose-only**. This document is not execution approval.

---

## 0. User-facing requirement re-derivation

The requested module must:

1. Add a **design and plan** inside the Mining module.
2. Attach that design/plan to the Mining leg so future agents do not treat it as a loose note.
3. Model the Mining leg as having **two brains**:
   - Hardware control brain.
   - Newborn coin discovery brain.
4. Connect the leg to the already-built **Octopus** system.
5. Connect its status/digest to **Telegram**.
6. Make it a real **leg/submodule** of Octopus, not only a document.
7. Preserve Mining governance:
   - no wallet/seed/private-key access;
   - no SSH/direct deploy;
   - no start/stop mining;
   - no buy/sell/withdraw;
   - electricity gate;
   - D2 survival/death-watch only.
8. Correctly align with the Coin Hunter brief:
   - frontier/newborn pre-listing PoW coins;
   - accumulation, not USD profitability;
   - Orange Pi fleet as compute/mining/node fleet;
   - ESP32 as nervous system, not miners;
   - Telegram as human gate;
   - AI/reporting as proposal-only.

---

## 1. Requirement verification

| # | Requirement | Implemented handling | Verification status |
|---|---|---|---|
| R1 | Design and plan inside module | `docs/OCTOPUS_LEG_DESIGN.md` | ✅ done |
| R2 | Design attached to module/leg | Referenced from `MANIFEST.yaml`, `README.md`, `ROADMAP.md`, `INDEX.md` | ✅ done |
| R3 | Two-brain leg | `_ops/legs/mining_leg.py` defines `HardwareControlBrain` + `CoinDiscoveryBrain` | ✅ done |
| R4 | Hardware-control brain | Provides electricity/fleet/thermal status and proposal-only `fleet_health` | ✅ done, execution intentionally absent |
| R5 | Newborn coin discovery brain | Provides algorithm classification, candidate scoring, death-watch proposal | ✅ done, read-only draft |
| R6 | Octopus submodule | `wiring.make_mining_leg()` + `wiring.mining_beat()` + `organism.py` state block | ✅ done |
| R7 | Telegram connection | `telegram_center.render._collect_legs()` maps `ORGANISM-STATE.mining` into the `mining` digest; `center.LEG_KEYS` already has `mining` | ✅ done |
| R8 | Default safe activation | `OCTOPUS_WIRE_MINING` default-off and intentionally outside `PAPER_FULL_FLAGS` | ✅ done |
| R9 | STOP/HALT first | `mining_beat()` checks `STOP_ORGANISM` and `opslib.halted()` before touching the leg | ✅ done |
| R10 | Zero secrets | `TaskPacket.secrets=()` | ✅ done |
| R11 | No wildcard read access | `MINING_NOTES` is a fixed allowlist | ✅ done |
| R12 | No outward methods | No `send`, `publish`, `pay`, `trade`, `ssh`, `deploy`, `withdraw` methods on `MiningLeg` | ✅ structural |
| R13 | Electricity gate | `ELECTRICITY_CEILING_USD_KWH = 0.05`; grid above ceiling -> red halt; unknown -> amber fail-closed; solar/free -> green | ✅ done |
| R14 | D2 death-watch only | `CoinDiscoveryBrain.death_watch()` abandons only on dev dead, chain stalled, community dead | ✅ done |
| R15 | Payback not kill criterion | Death-watch ignores payback/liquidity as abandon triggers | ✅ done |
| R16 | No market-profitability drift | Design doc marks Coin Hunter as accumulation/survival/exit, not known-coin profitability | ✅ done |
| R17 | ESP32 not miners | Design doc states ESP32 = watchdog/sensors/mesh/deadman/oracles | ✅ done |
| R18 | Orange Pi role | Design doc states Orange Pi = mining/node/orchestrator/benchmark fleet | ✅ done |
| R19 | Tests | `_ops/tests/test_mining_leg.py`, `_ops/tests/test_mining_wiring.py` | ✅ added; run still required |

---

## 2. Edge cases and fail-closed behavior

| Edge case | Expected behavior | Current handling |
|---|---|---|
| `OCTOPUS_WIRE_MINING` unset/0 | No leg is built, no beat runs | `make_mining_leg()` and `mining_beat()` return `None` |
| Owner explicitly sets `OCTOPUS_WIRE_MINING=1` | Leg builds as incubating/report-only | `money_link=incubating` because `MINING` is not in budgets |
| STOP file exists | Beat returns `None` | `STOP_ORGANISM.exists()` checked first |
| Global halt active | Beat returns `None` | `opslib.halted()` checked first |
| No hardware registry yet | Amber/fail-closed, no execution | electricity gate returns safe=false, mood=🟡 |
| Unknown electricity | Amber/fail-closed | node id listed under `unknown` |
| Expensive grid electricity | Red halt | unsafe nodes listed |
| Solar/free electricity | Green | safe=true |
| Missing algorithm | Not viable; manual review | `classify_algo()` returns category `unknown` |
| GPU/ASIC-dominated algo | Red / not ARM viable | SHA256, kHeavyHash, Ethash, Kawpow etc. rejected |
| Unknown algo | Manual review | `needs_manual_review` |
| Incomplete death-watch | Amber; no abandon | missing fields listed |
| D2 death criterion true | Red abandon proposal | abandon=true proposal only |
| Payback/liquidity poor | Does not abandon | not part of `death_watch()` |
| Telegram state missing | Default grey leg digest | render keeps `_LEG_DEFAULT` |
| Telegram state present | Mining digest shows fleet/electricity/hashrate | `_collect_legs()` maps `organism.mining` |
| Any leg exception | Does not kill organism | `mining_beat()` catches and alerts |

---

## 3. Files created or changed for this requirement

### New files

```text
_ops/legs/mining_leg.py
_ops/tests/test_mining_leg.py
_ops/tests/test_mining_wiring.py
03 - Projects/Mining/02 - Code/mining_preexec_mvp/docs/OCTOPUS_LEG_DESIGN.md
03 - Projects/Mining/02 - Code/mining_preexec_mvp/docs/OCTOPUS_LEG_REQUIREMENTS_MATRIX.md
```

### Updated files

```text
_ops/wiring.py
_ops/organism.py
_ops/telegram_center/render.py
03 - Projects/Mining/MANIFEST.yaml
03 - Projects/Mining/DecisionLog.md
03 - Projects/Mining/INDEX.md
03 - Projects/Mining/02 - Code/mining_preexec_mvp/README.md
03 - Projects/Mining/02 - Code/mining_preexec_mvp/docs/ROADMAP.md
```

---

## 4. What remains deliberately not implemented

```yaml
not_implemented_by_design:
  - ssh_to_node
  - deploy_to_node
  - start_mining
  - stop_mining
  - pool_target_write
  - wallet_access
  - seed_access
  - private_key_access
  - buy
  - sell
  - withdraw
  - autonomous_allocation_switch
  - direct_telegram_execution_command
```

Reason: current project phase is still pre-execution; the leg is a visibility/proposal limb, not an execution limb.

---

## 5. Commands for final verification

From the vault root:

```bash
cd "F:\backup\_ops"
python -m pytest tests\test_mining_leg.py tests\test_mining_wiring.py
python -m py_compile legs\mining_leg.py wiring.py organism.py telegram_center\render.py
```

If pytest is unavailable, run the equivalent project test runner after ensuring `_ops` and `_ops/legs` are on `PYTHONPATH`.

---

## 6. Final gate statement

```yaml
mining_octopus_leg:
  design_inside_module: true
  attached_to_project_docs: true
  octopus_leg_code: true
  two_brains: true
  telegram_digest: true
  default_execution: false
  default_wire_flag: OCTOPUS_WIRE_MINING=0
  wallet_access: false
  ssh_deploy: false
  miner_control: false
  financial_execution: false
  tests_added: true
  final_test_run_required: true
```
