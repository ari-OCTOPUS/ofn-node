# LANE-REPORT — OCTOPUS-DIGEST-DB-INVESTIGATION-20260918

GOV_VERSION=V8 · LADDER=L2 · read-only investigation (Elaheh's P0 brief via Ari). Nothing written/moved/migrated/restarted; no DB copied; paths+counts only, no PII.

## Answer
**The digest runs on no schedule anywhere in the fleet.** No active digest timer on 100/114/138/160/180/182/193, no Windows task or digest artifact on the laptop. The only digest units that exist (138: `octopus-owner-digest-morning/evening`) are `disabled/inactive` **and** run a different script (`ofn/agents/owner_digest_emit.py`, no painting/LeadStore use). The 114-row DB with the 10 call outcomes lives on `elahe-X550CC` (outside the fleet; unverified from here). → Scenario (C) refined: **no automated host at all**; the call list is manual.

## Two defects found (beyond the brief)
1. `tools/owner_digest.py --db` defaults to a **bare relative** `painting.sqlite` → resolved against CWD; sqlite3 **creates** a missing file and the schema seeds → a silently EMPTY call list with no error. Canonical `ofn/config.py: <state_dir>/painting.sqlite` is not used by the digest.
2. The runtime copy on 138 has **no `_MOBILE_RE`** at all in `tools/owner_digest.py` → even a run on 138 would lack the regex fix (the 138↔main lineage divergence).

## Fleet DB census (path → rows)
138: empty 2026-08-07 backup = 0 rows · 160/193: pytest fixtures (ERR, other schema) · 100/114/180/182 + laptop: none found · elahe-X550CC: 114 rows (reported, unreachable from here).

## Deliverables
`INVESTIGATION-painting-sqlite-digest-source.md` — full evidence table, the resolution mechanism, migration status (unverifiable on fleet copies), and a **convergence plan as a proposal only** (choose host → 114-row DB as source of truth → copy with owner approval + hash/diff of painting_call_log → fail-closed digest: absolute path + refuse on 0 rows + print resolved path/counts → timer on the chosen host only).

## Rollback
additive: delete the folder + revert the commit. No runtime touched.
