# OCTOPUS-U03 SYNTHESIS-NODE-PACKS hook UNWIRED — 2026-08-23

**Status: PASS_WITH_HOLDS**

## Problem
`WIRING.json` had `synthesis_node_packs_hook=true` with pointer enabled
(`evidence_plane/SYNTHESIS-NODE-PACKS.pointer.json`) and packs on disk, but **no**
organism/wiring/organs beat consumer → UNDISCOVERED **U03 UNWIRED**.

## Measure (before)
- Hook true in `_ops/organs/WIRING.json` (+ bak lineage)
- Pointer enabled; packs_dir with BUSINESS / SENSORIUM / LAPTOP + HASHES.sha256
- Zero organs beat readers of `synthesis_node_packs_hook`
- Related: pack open_questions / U24 laptop gates remain owner surfaces

## Decision
**Path A/C hybrid** (safer durable close matching U02 architecture):
keep hook **true**, wire minimal **advisory** consumer; do **not** disarm
(Path B) because pointer+packs were intentionally armed.

## Repair
1. Bak: `WIRING.json.bak-u03-20260823`, `run_session.py.bak-u03-20260823`
2. NEW `organs/synthesis_node_packs.py` — `beat()` gated on `enabled("synthesis_node_packs_hook")`
3. Wire into `organs/run_session.py` (import + call + `SYNTHESIS-NODE-PACKS-ADVISORY.json` + report field)
4. Document consumer on `WIRING.hooks.synthesis_node_packs` (mode=advisory, live_promote=false)

## Prove
- `enabled(synthesis_node_packs_hook)=True` and `beat()` → `consumer_fired=True`, `flag_drift=False`
- 3/3 packs present; HASHES match; `live_promote_claimed=false`
- Flag-off path returns `reason=flag-off` without emit
- `run_session.synthesis_node_packs_beat` import OK
- No Telegram broadcast / money / PWM / invented pack contents / invented secrets/URLs

## Holds
- Pack **open_questions** remain (6 total) — advisory surfaces counts only
- Organism hot-path unchanged (sidecar organs session consumer)
- No LIVE promote

## Evidence
`F:\backup\06-EVIDENCE\OCTOPUS-U03-SYNTHESIS-NODE-PACKS-2026-08-23\`
