# CHRONOS-FABLE OS — Roadmap
_Derived from DOC-C §5 + DOC-06 phased strategy. evidence: A/I._

## Phased build (substrate-first; anti-meta-escalation)
| Phase | Content | Exit criterion |
|---|---|---|
| **0 (now)** | Ship L0 substrate (Event-Bus/LANGAR, HLC, pacemaker, TINV-7). No hybrid work before this. | heartbeat live; HLC on every event; age_tick only on human-append |
| **1** | L13 checkpoint + `replay(from,to)` | any leg's state reconstructable at any beat < 5s |
| **2** | L4 memory ladder + eviction + Vault schema | Research leg survives 100+ cycles without context overflow; cache rebuildable from log |
| **3** | L3 mortal sub-legs + metabolic spawn accounting | ≥2 parallel sub-legs on a breadth-first task, no TINV-2/3 violation |
| **4** | L7 anchored trace-grader (+ gap-report) | ≥1 doctor fix settled by human-append with measurable eval lift |
| **5 (deferred)** | interop (A2A/MCP at the boundary) | only on real external-leg need |

## 30 / 60 / 90 (operator-facing)
- **30d:** L0 + L1 + L8 guards green on MOCK; L13 checkpoint. Ingest RES-001 + 2–3 more corpus files via L10 template.
- **60d:** L4 memory + L3 sub-legs; L9 project_registry live (read-only money); vertical slice on the most revenue-relevant project end-to-end.
- **90d:** L7 evolution loop anchored; L11 Telegram control; first Weekly Evolution Report; resolve ≥1 money_link.

## Kill / stop criteria
- Any guard bypass in audit (irreversible effect without human-append) → halt, root-cause before proceeding.
- Meta-escalation detected (redesign before Phase-0 ships) → revert to substrate.
- A capability enters without a declared cost → reject (INV-07).
- Rabbit-hole: research time > budget with no money_link progress → park the bet.

## Milestones tied to Missing Evidence
- Upload `OCTOPUS_CHRONO_ARCHITECTURE.md` → finalize L0 SQL schema + age_tick rule (MER-1 → READY).
- Upload Survival-Stack original → finalize Vault fields + routing (MER-2 → READY).
- Upload `lab seed data.json` → build quantitative experiment registry (MER-3 → READY).
