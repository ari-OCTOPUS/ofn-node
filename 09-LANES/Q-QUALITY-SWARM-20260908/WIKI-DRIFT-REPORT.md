---
type: report
lane: Q-QUALITY-SWARM-20260908
created: 2026-09-08
verified_at: 2026-09-08T05:30:00Z
gov: V8
ladder: L2
---

# WIKI-DRIFT-REPORT

Live vantage: laptop vault `F:\backup`, `git rev-parse HEAD` this session.  
Stale or wrong wiki numbers are marked **STALE** / **SUPERSEDED**, not deleted.

Contradiction format: claim · value_a · source_a · value_b · source_b · resolution · status.

## 1. HEAD commit

Two reads of the same wiki file in one session (file is dirty / auto-updated):

| When | Wiki HEAD | Live git | Mark |
|---|---|---|---|
| First read this session | `74cc733` (`OCTOPUS/CURRENT-TRUTH.md` auto-generated `2026-09-08T04:58:05Z`) | `ba1e7beff14d320076ca7f4f1fccbff6718c3e53` | **STALE** at that timestamp |
| `wiki_drift_check.py` `2026-09-08T05:37:03Z` | `ba1e7be` | same live hash | auto-block **caught up**; 04:58Z snapshot remains historical |

- value_a: `74cc733` · source_a: CURRENT-TRUTH auto block 04:58:05Z
- value_b: `ba1e7be` · source_b: `git rev-parse HEAD` this session
- resolution: auto-block moved during session · status: **open** (two timestamps, both kept)

## 2. Beat / members

| When | Wiki beat | Live organism beat | Mark |
|---|---|---|---|
| First read | 65620 (CURRENT-TRUTH 04:58Z) | 65655 | **STALE** at 04:58Z |
| 05:37:03Z check | 65655 | 65655 | auto-block matched |
| VITAL-DATA §1 | `~64600+` | 65655 | **STALE** |

- members_present: wiki 11 (CURRENT-TRUTH) · live this session **unverified**
- VITAL-DATA `~64600+` vs ORGANISM-STATE 65655 · status: **open**

## 3. Board count

| Field | Wiki / owner | Live measured | Mark |
|---|---|---|---|
| Mining fleet | 162 nodes (16 OPI + 140 ESP32 + 2 FPGA), all off | `mining_os.fleet.nodes_total: 0`, `status_known: false` | not a silent pick: **both true in different senses** |

- value_a: 162 owner-confirmed · `03 - Projects/Mining/Hardware Registry & Runbook.md` 2026-07-28
- value_b: 0 wired · `_ops/state/ORGANISM-STATE.json` `mining_os.fleet` generated `2026-09-08T05:28:40Z`
- resolution: owner-stated inventory vs unwired miner OS · status: **open**
- Engineering entrypoint: live physical callers laptop + 138 + 180; `182` retired as agent not hardware (`07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md`). Do not equate 162 mining nodes with those three hosts.

## 4. Test counts (documents vs this session)

Rule: a test_count is **unverified** unless `pytest` ran in this session (`10-evidence-grading`).

| Wiki claim | Source | This session | Mark |
|---|---|---|---|
| 27/27 U2 v3 | VITAL-DATA §1; HANDOFF | not re-run | **unverified** (quoted) |
| 25/25 skill guard | HANDOFF | not re-run | **unverified** |
| 15/15 Airtasker | VITAL-DATA additive block | not re-run | **unverified** |
| 209/209 Project-F | `اونلی فنز/PROJECT.md` Progress 2026-08-01 | not re-run | **STALE** date; count unverified |
| 845 tests sprawl | GAP inventory G24 2026-08-23 | not re-run | **STALE** inventory date |
| 3/3 C2 | VITAL-DATA | not re-run | **unverified** |

New tests in this lane were run after write; counts live in `LANE-REPORT.md`.

## 5. Brier

| Claim | Value | Source | Live / other | Mark |
|---|---|---|---|---|
| ACD «Brier=0.037 misleading» | 0.037 | `agent-prompts/MEGAPROMPT-CAPABILITY-GAP-2026-09-08.md` | cortex `brier: 0.035766` (`_ops/state/cortex/cortex-state.json`; calibration file blocked by secret hook this session) | **open** (0.037 vs 0.035766); n=1503, ungraded=497 in `upgrades-digest.json` |
| L2 STRATEGY_BRIER v1 | 0.34565 | `09-LANES/L2/LANE-REPORT.md` | not re-scored | historical E2, not «current wiki HEAD» |
| L2 STRATEGY_BRIER v2 | 0.237387 | same | not live winner | retained v1+v2 by design |
| MEMABL persistence vs kNN | 0.258 vs 0.279 | GOV-V8 body | not re-run | historical |

Do not treat 0.035766 as «better calibration» without the graded/ungraded split. ACD text already warns Brier on unresolved is misleading.

## 6. Ziman domain (wiki self-conflict)

| value_a | source_a | value_b | source_b | status |
|---|---|---|---|---|
| `ziman-gift.com` NXDOMAIN, sales impossible | VITAL-DATA §2 row 3; Ziman PROJECT.md Open blockers 2026-09-07 | `.com.au` Shopify primary live; 13:15 local-cache 404 vs 15:55 authority-DNS 200 | VITAL-DATA season blocks 2026-09-08 | **open**; older NXDOMAIN line is **SUPERSEDED** for `.com` vs `.com.au` but the §2 table was **not** updated |

## 7. NOW.md / labels.json

| Claim | Wiki/tool | Live | Mark |
|---|---|---|---|
| NOW.md is generated from labels.json | `_ops/scripts/render_now.py` | `docs/NOW.md` **absent**; `_ops/state/labels.json` **absent** | **STALE/missing renderer inputs** |
| DEEP-SCAN: NOW.md append-loop ~300 markers | `09-LANES/DEEP-SCAN-10ASPECTS-20260907/LANE-REPORT.md` | path `docs/NOW.md` not found this session | **SUPERSEDED** if that NOW.md was another path; not re-opened |

## 8. Coherence auto number

CURRENT-TRUTH auto: coherence **0.953** · source auto-block 04:58Z. No independent recompute this session · **unverified**.

## Machine repeat

`tools/wiki_drift_check.py` re-reads these sources and writes `_ops/state/wiki-drift-latest.json`. `docs/NOW.md` auto-section is filled only by that tool / `render_now.py`.
