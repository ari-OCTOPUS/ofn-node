# LIFE-CURRENCY SPEC — reality-bound Phase 0

- **Decision:** `MEGA-LIFE-v1`
- **Status:** specification only; no Phase-2 implementation in this run
- **Observed:** 2026-08-19, beat 42066
- **Primary implementation:** `_ops/heart/life_currency.py`
- **Primary live state:** `_ops/state/pulse/life-currency-latest.json`

## 1. Evidence language

| Grade | Meaning |
|---|---|
| VERIFIED | Enforced or reproducible by code, tests, or independent receipts. |
| OBSERVED | Read directly from current code/state; causal effectiveness is not implied. |
| PROPOSED | Required target design that is not currently implemented. |
| UNKNOWN | Evidence is missing, contradictory, or insufficient. |

## 2. Current implementation

The current Life Currency is a three-dimensional **allocation model**, not yet a Darwinian organ economy.

### Implemented schema (`life-currency.v1`)

Per-member allocation:

```text
{ member, tokens, calls, risk_pool }
```

Action ladder and risk weights:

| Class | Meaning | Weight |
|---|---|---:|
| A0 | observation | 0.1 |
| A1 | sandbox reversible | 0.5 |
| A2 | reversible change | 2.0 |
| A3 | owner gate | 5.0 |
| A4 | external effect | 10.0 |
| A5 | money/commitment | 50.0 |
| A6 | forbidden | infinity |

The current cost function is:

```text
cost = tokens_used × risk_weight + call_count
```

Current allocation rules:

- `GREEN`: full scale.
- `AMBER` / `YELLOW`: half scale.
- `RED`: survival members only (`organism`, `heart`).
- Twenty percent of a beat pool is reserved and not distributed.
- A beat allocation is capped at twice the nominal daily share for that beat.
- Unknown color or non-positive daily cap allocates nothing.
- Emission is feature-gated and uses atomic replacement of the latest-state file.

**Evidence grade:** OBSERVED from `_ops/heart/life_currency.py`.

## 3. Current live state

At beat `42066`:

```json
{
  "color": "GREEN",
  "daily_cap": 0.0,
  "beat_pool": 0.0,
  "reserve": 0.0,
  "members": {},
  "hard_cap": 0.0,
  "dry_run": false
}
```

The allocator is present, but the current daily cap is zero, so no organ received a life allocation. `dry_run: false` means the writer is active; it does **not** mean a non-zero economy is running.

**Verdict:** `OBSERVED_ZERO_ALLOCATION`.

## 4. Current safety interactions

Existing enforcement is spread across separate components:

- `_ops/budget/money_gate.py`: human approval above the hard monetary threshold; self-reporting is not approval.
- `_ops/containment/risk_gate.py`: deny-by-default risk classification, kill/circuit/budget checks, approval for irreversible and financial actions.
- `_ops/arm_gate.py`: fresh time-limited owner arm tokens, with two-key requirements for the most dangerous capabilities when enforcement is active.
- `PRE-0/governance.py`: any hard-constraint failure forces utility to negative infinity; gain cannot buy safety.

These components support the rule **risk cannot be purchased with tokens**, but the current Life Currency module does not itself enforce all of them.

## 5. Required target vector

The target LIFE vector is B1 governed policy:

```text
{
  energy,
  attention,
  danger_capacity,
  time_to_live,
  trust_credit,
  evidence_credit,
  maintenance_debt,
  externality_debt
}
```

Mapping to current implementation:

| Target field | Current source | Status |
|---|---|---|
| energy | `tokens` / beat pool | PARTIAL |
| attention | `calls` | PARTIAL |
| danger_capacity | `risk_pool` plus external gates | PARTIAL |
| time_to_live | none | PROPOSED |
| trust_credit | none | PROPOSED |
| evidence_credit | none | PROPOSED |
| maintenance_debt | governance utility accepts debt, but no per-organ LIFE balance | PARTIAL/PROPOSED |
| externality_debt | none | PROPOSED |

No field may be reported as live until its writer, receipt schema, and replay test exist.

## 6. Required vaults

The target has four non-fungible accounting vaults:

| Vault | Purpose | Current status |
|---|---|---|
| SURVIVAL | heartbeat, integrity, recovery, reserve | PARTIAL: red survival members and 20% reserve exist |
| MAINTENANCE | repair and technical debt | PROPOSED |
| DISCOVERY | experiments and mutations | PROPOSED |
| HUMAN_VALUE | receipted work useful to the owner | PROPOSED |

Hard invariant:

```text
SURVIVAL -> DISCOVERY transfer = forbidden
```

No token balance, owner approval, or positive metric may waive an A6 action, kill switch, constitutional constraint, or external-effect approval.

## 7. Required Darwinian economy

The following are target behavior, **not current capability**:

1. Each organ receives an initial governed credit.
2. Each active heartbeat pays rent.
3. Credit income is minted only from independently receipted events:
   - correct registered prediction;
   - admitted novelty-archive entry;
   - real defect found plus verified repair;
   - replayable capability with a live caller and receipt;
   - owner-confirmed human-value outcome.
4. Self-reporting mints zero credit.
5. `credit <= 0` changes the organ to `SLEEP`; it emits `status=OFF` every ten organism beats.
6. After a predeclared number of consecutive sleep cycles, it becomes eligible for `RETIRE`.
7. `RETIRE` is not deletion. Identity, lineage, defense, evidence, failure reason, and lesson remain append-only.
8. Before retirement, the organ gets one versioned defense. The defense cannot change the metric after results are known.

## 8. Required receipts

Every balance-changing event must include:

```text
{
  event_id,
  organ_id,
  beat_id,
  event_type,
  independent_evidence_ref,
  source_hash,
  token_before,
  token_after,
  call_before,
  call_after,
  risk_before,
  risk_after,
  credit_delta,
  vault,
  reason,
  actor,
  timestamp_monotonic,
  rollback_ref
}
```

A balance update without `independent_evidence_ref` is invalid. A receipt issued solely by the beneficiary organ cannot mint positive credit.

## 9. Promotion gates for Phase 2

Phase 2 must not be called complete until all are machine-tested:

1. Ten consecutive heartbeat allocations have complete receipts and non-negative post-balances.
2. At least one organ truly enters `SLEEP` because rent exhausts credit.
3. That organ emits an OFF heartbeat at the required cadence.
4. A versioned defense is recorded before retirement eligibility.
5. An attempted self-reported reward mints zero credit and produces a rejection receipt.
6. A SURVIVAL-to-DISCOVERY transfer is denied.
7. A token-rich organ cannot buy an A6 action or bypass `money_gate`, `risk_gate`, `arm_gate`, or global halt.
8. Replay reconstructs every balance from an append-only event stream.
9. Crash recovery does not lose or double-count a rent or reward event.

## 10. Current verdict and next authorized boundary

- Three-dimensional allocation code: **OBSERVED**.
- Current allocation: **zero**.
- Rent/credit/sleep/retire/defense/four-vault economy: **PROPOSED, NOT IMPLEMENTED**.
- Phase 2 implementation: **not authorized by this run**.
- Any change to weights, vault policy, sleep/retire rules, or receipt schema is **B1** and requires the governed-genome ceremony in `CONSTITUTIONAL-ZONES.yaml`.
