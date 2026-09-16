# Contracts

## Observation quality

VALID | STALE | MISSING | CONFLICTING | WARMUP | UNLOCATED | FUTURE_DATA | UNIT_MISMATCH | RESTART_ARTIFACT_SUSPECTED

## Bitemporal

`occurred_at <= recorded_at <= decision_time` else FUTURE_DATA (ineligible).

## Eligibility

Only VALID enters Homeostatic computation. Others remain in `excluded_evidence`.

UNKNOWN/MISSING is never coerced to 0 (`never_zero_from_unknown`).

latest-only + historical_claim → UNLOCATED (cannot prove beat 42784 from overwritten latest.json).

## Setpoints

`shadow_homeostasis/homeostasis.py` `SETPOINTS_V1`

## Skill weights

`shadow_homeostasis/metacontrol.py` `SCORE_WEIGHTS_V1`

## Modes

BLOCK | ADVISORY | SHADOW. No ACTION. GAP-001 OPEN. D6 caps judge_reliability at ADVISORY.

`executable` always false.
