# OCTOPUS-U02 CONNECTOR-GAP hook FLAG_DRIFT — 2026-08-23

**Status: PASS_WITH_HOLDS**

## Problem
`WIRING.json` had `connector_gap_hook=true` with loader-only surface
(`evidence_plane/connector_gap_loader.py`) and **no** organism/wiring/organs beat
consumer → UNDISCOVERED **U02 FLAG_DRIFT**.

## Measure (before)
- Hook true in `_ops/organs/WIRING.json` (+ bak lineage)
- Loader + `__init__` re-exports: `load_registry` / `mark_oauth_gaps`
- Zero `*.py` readers of `connector_gap_hook` / `enabled("connector_gap_hook")`
- Registry pack: CG-001/002/003 **WAITING_OWNER_OAUTH** (U04)
- Related: U04 owner OAuth HOLD — do not invent credentials

## Decision
**Path A/C hybrid** (safer durable close matching architecture intent):
keep hook **true**, wire minimal **advisory** consumer; do **not** disarm
(Path B) because loader+registry+marks_gap_until_oauth were intentionally armed.

## Repair
1. Bak: `WIRING.json.bak-u02-20260823`, `run_session.py.bak-u02-20260823`
2. NEW `organs/connector_gap.py` — `beat()` gated on `enabled("connector_gap_hook")`
3. Wire into `organs/run_session.py` (import + call + `CONNECTOR-GAP-ADVISORY.json` + report field)
4. Document consumer on `WIRING.hooks.connector_gap` (mode=advisory, live=false, u04 hold)

## Prove
- `enabled(connector_gap_hook)=True` and `beat()` → `consumer_fired=True`, `flag_drift=False`
- OAuth gaps CG-001/002/003 still WAITING_OWNER_OAUTH; `metrics_allowed=false`; no LIVE claims
- Flag-off path returns `reason=flag-off` without emit
- `run_session.connector_gap_beat` import OK
- No Telegram broadcast / money / PWM / invented OAuth

## Holds
- **U04 OAuth** remains owner HOLD (GA4/GSC/Ads)
- Organism hot-path unchanged (sidecar organs session consumer)
- U03 synthesis packs still separate

## Evidence
`F:\backup\06-EVIDENCE\OCTOPUS-U02-CONNECTOR-GAP-HOOK-2026-08-23\`
