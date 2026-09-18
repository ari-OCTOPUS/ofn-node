# TERRITORY-REPORT — smalls deep-scan (OCTOPUS-DEEP-SCAN-250-20260915)

GOV_VERSION=V8 · LADDER=L2 · read-only scan · outputs written only under `09-LANES/OCTOPUS-DEEP-SCAN-250-20260915/raw/`

## Scope
Previously never deep-scanned small territories + a SEASON-LEFTOVER sweep across `01 - Dashboard/` and `06-EVIDENCE/` for 2026-09-07..2026-09-15 promises never closed.

## Result
- Findings written: **35** total → `raw/smalls-findings.json` (JSONL, 35 valid objects)
  - Small territories: **SML-1..SML-20** (20, quota >=15 met)
  - SEASON_LEFTOVER sweep: **SE-1..SE-15** (15, quota >=10 met)
- Classes used: OPEN_WORK, ABANDONED, RULING_UNEXECUTED, DOC_RUNTIME_DISCREPANCY, DEBT_HIDDEN, SEASON_LEFTOVER.
- Every finding carries a path + line/snippet anchor; no synthetic data; contradicted claims recorded with both values.

## Headline findings
1. **SE-3 (U3 R3 C5)** — `verified_cash = $0.00`, Ziman store live with 251+ checkout checks and zero orders; combined with **SE-14** (ziman-gift.com NXDOMAIN, owner renewal card unanswered since 09-08) the season's revenue lane targets a possibly dead domain.
2. **SE-5 (U3 R2 C5)** — organism now self-produces and self-deploys patches while its containment rollback plan is admitted untested.
3. **SE-8/SE-9** — SEASON-CORRECTION (owner order, commit 686550b): phase-1 >=30 fresh leads not evidenced anywhere; GO-date contradiction 09-21 vs GO-EXT2-10-07 unreconciled.
4. **SE-10** — DEEP-SCAN-250 owner contract (100 carried + ~150 new + >=40 SEASON_LEFTOVER) exceeds this executed scan's quota (~30); flagged honestly — a later owner-voted scope reduction would dissolve it.
5. **SML-2/SML-3** — TCB #3 PATCHED-UNSIGNED and P10 daily_cap bug (life_currency.py:170, daily_pool->0.0) sit open in 06-RISKS with nothing after 2026-08-20 in the territory.

## Coverage (honest per-territory)

- COUNCIL_REPORTS/: read: 8/85 files (A01 register csv, A01/A02 exec summaries + findings headers), excluded: 77 (wave-01 bulk: per-agent boilerplate sections, raw jsonl/csv/pcap-style snapshots read only where stub register anchored a finding)
- OCTOPUS-PRIME/: read: 3/59 files (EXECUTION-STATE.json, directory manifest, erratum skim), excluded: 56 (phase-0 log files (.log), test JSONs, audit mds superseded by later _ops line; only the frozen milestone anchored a finding)
- 06-Maps/: read: 0/0 files, excluded: 0 (directory empty)
- 06-RISKS/: read: 1/1 files (OPEN-GATES.md in full)
- 05-Finance/: read: 0/0 files, excluded: 0 (directory empty)
- 05-Screenshots/: read: 0/0 files, excluded: 0 (directory empty)
- 10-Telegram/: read: 0/0 files, excluded: 0 (directory empty)
- PRE-0/: read: 2/13 files (EXECUTION-BOARD.md in full; RFC-NEURAL-LOOP-CLOSE grep-only, no finding), excluded: 11 (constitution/protocol docs with no open-item register; single-file scan of a small territory, finding quota met elsewhere)
- nervous-system/: read: 5/62 files (EXTRACTOR-RUNBOOK.md, PAYLOAD-SIZE-REPORT.md, directory ls of extract_*.py, refresh-live-data.bat listed, security-scan-report.json listed), excluded: 57 (generated *-data.js payloads and extractor scripts read only via runbook cross-check)
- _memory/: read: 3/25 files (OCTOPUS/NOW.md in full, HEARTBEAT.md first 60 lines, AUTOBIOGRAPHY directory manifest), excluded: 22 (22 daily autobiography files — diaristic, machine/appended history, no open-item register)
- _build/: read: 1/187 files (_build/lead-naghshi-portable/.env checked and confirmed UNTRACKED by git ls-files — no finding raised), excluded: 186 (PDFs/JPGs binary assets of the AiFarm-Lead portable bundle — out of md/json scan scope)
- _Templates/: read: 0/9 files, excluded: 9 (blank templates with no claims to verify)
- 01-TRUTH/: read: 6/14 files (CURRENT-TRUTH.md, CONTRADICTIONS.md, SEASON-5-2026-09-04.md, SEASON-5-BOARD-MIRROR.md in full; ZIMAN-SEASON redirect line 4; ADMIN-CHECKLIST header), excluded: 8 (older dated state snapshots 08-15 and single-policy docs superseded by redirects)
- 02-LifeOS/: read: 0/0 files, excluded: 0 (directory empty)
- 00-INDEX/: read: 2/2 files (OCTOPUS-CURRENT-STATE.md + its .bak; both same stale content)
- Excalidraw/: read: 0/1 files, excluded: 1 (drawing file, no textual claims)
- agent-prompts/: read: 4/83 files (MEGAPROMPT-CAPABILITY-GAP-2026-09-08, MEGAPROMPT-CONNECT-ALL-2026-09-08 headers+phase A, directory manifest of all 83, grep anchors), excluded: 79 (older 07/08 megaprompts superseded by 09-09..15 handoffs; DISCOVERY-PHASE1 series concluded 2026-08-18)
- 07-HANDOFF/ (open-item sweep): read: 8/92 files (OWNER-DIRECTIVE-2026-09-11, MEGAPROMPT-NEXT-AGENT-2026-09-11, MEGAPROMPT-TRANSFORMATION-REVENUE-2026-09-11, GAP-VERIFY-IDENTITY-STOP, SPINE-EVENTENVELOPE-PR-BLOCKED, EX1-CRITERION-OWNER-QUESTION, OWNER-APPROVALS-2026-09-08 tail, ENGINEERING-ENTRYPOINT list), excluded: 84 (dated state/STATE files 09-02..09-07 superseded by 09-11 directive; entrypoint chain; lane-scoped memos)
- SEASON sweep 01 - Dashboard/: read: 3/18 files (OCTOPUS-VITAL-DATA-2026-09-08.md top ~100 lines with 4 dated 09-15 blocks; UNLOCK-PLAN-2026-09-08.md; UNLOCK-REGISTRY-2026-09-08.md), excluded: 15 (html dashboards, .base files, .bak, older board dirs pre-season)
- SEASON sweep 06-EVIDENCE/: read: git-log mediated — 15 commits 2026-09-07..09-15 read in full (commit messages as receipts: 66f4ac5, 686550b, 48575c2, 40a84a0, ff2ec4a, 5e48573, etc.); excluded: 500+ evidence dirs (read-only via runtime commits per truth-hierarchy level 1; no file bodies opened)

## Method notes
- Runtime output (git log, ls, sha checks) used as truth-hierarchy level 1; file reads as level 2; no chat evidence used.
- OP-2 disposition patch verified as actually transferred: commit 1807ff4 present in `git log -- _ops/budget/approval_channel.py` — so no finding raised for the OP-2 transfer itself (SE-12 covers the fuel-fix half of the same directive, which is NOT evidenced).
- Three territories are empty directories (06-Maps, 05-Finance, 05-Screenshots, 10-Telegram, 02-LifeOS — five total counting 02-LifeOS): empty-shell structure debt noted here rather than as findings.
- All timestamps in findings: retrieved_at_utc 2026-09-15T20:00:00Z (session window).

## Rollback
Delete the two files under `09-LANES/OCTOPUS-DEEP-SCAN-250-20260915/raw/`; no other writes were made; runtime untouched.
