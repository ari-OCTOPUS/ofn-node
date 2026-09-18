# LANE-REPORT — D-S0-HUNT

Lane: **D-S0-HUNT**. Measured 2026-09-03T20:34:54+10:00 on `DESKTOP-KA9RFN5` (Wi-Fi `192.168.0.191`, `Get-NetIPAddress` this session). Laptop vault, not board 180.

Owner pick this increment: **آشپزخانهٔ خاموش** — keep `demand_harvest` / `buynsw-harvester` separate from `ofn.run`. Books incomplete — no accounting. Stove not lit.

## 1. What was done

- Read `AGENTS.md`, `OFN-LOCAL-ARCHITECTURE.md`, Lane B `FOUR-SHELLS-MAP.md` (read-only).
- Static read of `F:\ofn-node\ofn\run.py` imports, `ofn/agents/*harvest*`, `h1_buysw*`, `tools/buynsw-harvester/`, `demand_harvest.py`. Grep DEAD SOURCE / demand.harvest / buynsw (no secrets).
- Wrote `09-LANES/D-S0-HUNT/harvest_boundary_probe.py` (AST + regex, no ofn import, no network).
- Ran it: `receipts/harvest-boundary-20260903T1033Z.json`.
- Wrote `HARVEST-VS-RUN.md`.

## 2. What remains

- 8791 three-tenant contradiction still `resolution: null` (this-host ingest_server vs code ziman vs 138 `ofn.run`).
- `F:\ofn-node` still `[behind 2]` vs local `origin/fix/demand-harvest` pointer — `local_behind_remote_unverified` (no fetch).
- HEAD this session: `34e63a04c5df4a948361f48b306e2a3f5188d42f` branch `fix/demand-harvest` (`git rev-parse`).
- Prior doctor pytest increment still on disk (`DOCTOR-LANE-TEST-RECEIPT.md`); not re-run.

## 3. What failed

- First probe print hit `UnicodeEncodeError` (cp1252 vs `→` in a JSON quote). File not written that run. Probe then writes JSON first and prints ASCII. Second run `exit_code=0`.
- Nothing started; no harvest/run failure because they were not invoked.

## 4. Evidence paths

| Claim | Value | Source | Status |
|---|---|---|---|
| `run.py` harvest/imap/buynsw imports | none · `wired_into_run=false` | `receipts/harvest-boundary-20260903T1033Z.json` | verified |
| AST import count | 55 | same | verified |
| DEAD SOURCE hits / files | 14 / 9 | same | verified |
| `demand_harvest` bytes / `__main__` | 13259 / absent | `Get-Item` + probe | verified |
| local ports/flags in `demand_harvest.py` | none | probe | verified |
| `ingest_server.py` on this tree | absent | probe + `Test-Path` | verified |
| 8791 this-host tenant | harvester ingest_server | B `FOUR-SHELLS-MAP.md` | prior B; not re-listened |
| 8791 code tenant | ziman `8791` | `ofn/config.py:283` | verified |
| 8791 on 138 | `python3 -m ofn.run` | B SSH-RO | prior B; no SSH this session |
| started this session | none | probe `started` + this report | verified |

## 5. Rollback

Move `HARVEST-VS-RUN.md`, `harvest_boundary_probe.py`, `receipts/harvest-boundary-20260903T1033Z.json`, and this report to `99-ARCHIVE/archive_D-S0-HUNT-harvest-vs-run-20260903/` (AGENTS.md §7). Revert the HANDOFF pin if added. Do not `rm -rf`. No ofn-node files were written. No process to stop.

## 6. Owner would have to authorize next

Still closed unless asked: start harvester / `ofn.run` / ingest_server, fetch the behind-2 commits, enable any `OCTOPUS_WIRE_*` / `OFN_WIRE_*`, bind `0.0.0.0`, send, merge, commit, collapse the three 8791 tenants into one story.
