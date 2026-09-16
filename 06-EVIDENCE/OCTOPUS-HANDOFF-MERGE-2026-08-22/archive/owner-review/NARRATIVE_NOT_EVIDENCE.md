# Narrative is not evidence

Obsidian vault and `SEASON-REPORT.md` are narrative copies for the laptop agent.

Do not cite them in the verification chain unless their digest is listed in `MANIFEST.json`.

Live files under `/var/lib/octopus/state/` and hashed artifacts in this owner-review pack are the source of truth.

Correction (KEEP_WAVE0_LOCKED):

- GAP-001 = OPEN / TESTED_FAIL (not PASSED)
- T0 = DEGRADED (would_decide=block)
- skill score 0.0 = model_is_the_baseline; T4 not executed
- Doctor FAIL with blocking_checks; do not issue OA-T7
- Checkpoint seq-266 may be signed; that still does not close GAP-002 in `open-gaps.json`
- After 2026-08-17T04:57Z the vault `obsidian-octopus` (Season Report / Plan / Doctor) is the narrative briefing; still not evidence

- phrase: `octopus-audit-ledger checkpoint anchored at seq=266` (do not write `ledger head = 266`)
- full seq 266 hash: `sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2`
- MANIFEST digest is not a signature and not provenance
