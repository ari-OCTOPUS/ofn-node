# FLAGS-AUTHORITY-REPORT — OCTOPUS-flags.cmd (read-only census)

- source: `_ops/OCTOPUS-flags.cmd` — **gitignored** (`.gitignore:40`), untracked, `call`-ed by every launcher
- **NO secret values are printed here** — only OCTOPUS_WIRE_* names + their 0/1 arm state.
- non-WIRE lines that appear to carry a secret value (KEY/TOKEN/…): **1** (counted, never shown)
- total WIRE flags: 29 · armed(=1): 27 · **LIVE-EFFECT armed: 6**

| flag (OCTOPUS_WIRE_) | armed | class | consumers |
|---|:--:|---|--:|
| ACCT_BEAT | 1 | operational | 8 |
| ACCT_REVIEW_LLM | 1 | operational | 6 |
| APPLY_MERGE | 🔴1 | LIVE-EFFECT (external/irreversible) | 17 |
| BIO | 1 | operational | 32 |
| DEBATE | 1 | operational | 11 |
| DOCTOR_KNOB_RFC | 1 | operational | 5 |
| DOCTOR_PERSIST | 1 | safety-critical | 6 |
| DOCTOR_SELFKNOW | 1 | safety-critical | 6 |
| EPISTEMICS | 1 | operational | 23 |
| HARVEST | 0 | operational | 9 |
| HEART | 1 | operational | 33 |
| HEART_WORK | 1 | operational | 10 |
| HUMAN_APPEND_GUARD | 1 | safety-critical | 11 |
| LEAD_DISCOVERY | 1 | operational | 21 |
| LEAD_DRAFT | 0 | operational | 16 |
| MENU_V2 | 1 | operational | 10 |
| MERGE_APPLIES_KNOB | 🔴1 | LIVE-EFFECT (external/irreversible) | 6 |
| MINING | 1 | operational | 33 |
| MISSION_RUNNER | 🔴1 | LIVE-EFFECT (external/irreversible) | 11 |
| NEEDS_NUDGE | 1 | operational | 8 |
| POCKETSMITH | 🔴1 | LIVE-EFFECT (external/irreversible) | 22 |
| PROPOSAL_BUTTONS | 1 | safety-critical | 14 |
| PS_WRITEBACK | 🔴1 | LIVE-EFFECT (external/irreversible) | 17 |
| PULSE | 1 | operational | 10 |
| RUNNER_APPLY | 🔴1 | LIVE-EFFECT (external/irreversible) | 3 |
| SCHEDULER | 1 | operational | 13 |
| SELFHEAL | 1 | operational | 12 |
| STRUCTLOG | 1 | operational | 10 |
| WEB_RESEARCH | 1 | operational | 7 |

## ⚠️ LIVE-EFFECT flags currently ARMED (owner-disarm candidates)
- `OCTOPUS_WIRE_APPLY_MERGE=1` — LIVE-EFFECT (external/irreversible) — 17 consumer file(s)
- `OCTOPUS_WIRE_MERGE_APPLIES_KNOB=1` — LIVE-EFFECT (external/irreversible) — 6 consumer file(s)
- `OCTOPUS_WIRE_MISSION_RUNNER=1` — LIVE-EFFECT (external/irreversible) — 11 consumer file(s)
- `OCTOPUS_WIRE_POCKETSMITH=1` — LIVE-EFFECT (external/irreversible) — 22 consumer file(s)
- `OCTOPUS_WIRE_PS_WRITEBACK=1` — LIVE-EFFECT (external/irreversible) — 17 consumer file(s)
- `OCTOPUS_WIRE_RUNNER_APPLY=1` — LIVE-EFFECT (external/irreversible) — 3 consumer file(s)

> Do NOT change these here. If disarm is wanted during Phase-0 surgery, that is an
> OWNER action on the live flags file, with explicit per-flag approval.
