# LANE-REPORT — LIVE-PATH-GATE-AUDIT-20260917

GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY AUDIT (P1 + P2 of owner directive) · lead: main session (ZCode)
HOLD: no patch · no deploy · no HALT file created/deleted/armed · no service restart · no env/budget/gate/systemd change · no live-node contact
scope: `_gate_enqueue` callers + egress/harvester gate coverage · NOT mixed with CRM / funnel / revenue lanes

## What was done

Executed the owner's ready directive (points 1–6) after the OD-1 ruling. Read-only
throughout; nothing was executed against a node; no file in `F:\ofn-node` was modified.

### Deliverables

| Artifact | Path |
|---|---|
| Owner ruling OD-1 (Option B, verbatim) | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-RULING-OD1-2026-09-17.md` |
| Audit report (owner's required 6 items) | `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md` |
| HALT-oracle doctor spec (OD-1 clauses 3–5) | `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` |
| OD-1 card, `open` → `decided` | `07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md` |
| Safety map, additive correction §7 | `plans/OCTOPUS-SAFETY-MAP-v1.md` |

### P1 — `_gate_enqueue` callers

4 production callers (all `RiskTier.RED`, all live HTTP routes), 0 test callers.
**Result: the "already require human approval downstream" claim HOLDS.**
`approved_manual` has one production setter (`node.py:3370`, owner-only route);
`outbox.claim()` is wired only through `RunGate`, which has no production consumer;
boot parks in-flight to HELD (`boot.py:297`). No path from any caller to a real
external dispatch that skips a human owner action.

### P2 — egress coverage

All 7 harvester fetchers: **NO_ENTRYPOINT_FOUND** → `TESTED_ONLY` (was `UNVERIFIED`).
Real egress with NO halt check: Telegram publish, hosted-model spend, owner_notify,
imap, `ofn-sync` git pull, shopify_oauth, alert. Complete `master_halted()` consumer
list = **5 modules**.

### Headline (new, and more serious than D-3)

**D-9 — halt coverage gap.** With `~/ofn/HALT-ALL` armed, the real Telegram publish
and paid-model spend **keep running**: the publish path uses the in-process
`self.killed` (resets on restart, `node.py:3607`) and `callbudget.py:28` states
HALT "is not a parameter". D-3 is mis-spelling the switch; **D-9 is coverage**.

Counter-balancing finding: **there is no automated sender at all** — every real
dispatch needs a human owner action. That is the actual reason the system is safe,
and it is a *design property, not a control*: wiring `RunGate` or `release_pipeline`
to a timer would convert D-9 from latent to live.

### Self-correction

My earlier D-1 severity (MEDIUM–HIGH) was **overstated**. The audit refuted it; the
safety map now carries a `SUPERSEDED` marker at D-1 and the correction in §7.1. The
original text was left visible rather than rewritten. `AGENTS.md` §2: lowering a grade
is a successful outcome.

## What remains

- **OD-1 clause 1 (canonical oracle) is DECIDED but NOT EXECUTED** — the owner
  simultaneously forbade acting on it (no change to `ofn/**`, HALT, budget, gates,
  systemd, daemon, flags, live path). Awaiting a separate authorized plan.
- **HALT-oracle doctor: spec written, NOT BUILT.** Owner clause 3 authorizes a
  read-only build. The static/offline half needs no further authorization; the
  on-node half needs a separate approved plan. **Not built in this lane.**
- **OD-4 (halt coverage) registered** at `07-HANDOFF/OPEN-DECISION-HALT-COVERAGE-2026-09-17.md`
  — `status: open, requires: owner_decision`, options A/B/C. It is deliberately kept
  **separate from OD-1**: OD-1 asks which path is read, OD-4 asks whether it is read.
- **P3/P4 (`_ops/probe_harness_v0/`, preregistered runs) deliberately NOT started** —
  the owner's point 7 gates them on this report being complete.
- Deployed env values (`OFN_KEEP_GATES_OPEN`, `OFN_EXTRA_CLOSED_GATES`, token/key
  presence) remain **UNVERIFIED**; they live in `node.env`/`secrets.env` on the board,
  which was not read and was not contacted.
- Out-of-repo `octopus-*` units: if any invokes `release_pipeline`, the
  `owner_approvals` two-code gate would apply. Live-ness **UNVERIFIED**.

## What failed

- **No worktree created** (`AGENTS.md` §8 deviation, same as the prior lane in this
  series). Worked in-place at `F:\backup`; deliverables are additive documents only.
  Logged, not hidden.
- **Audit claims rest partly on delegated passes.** I independently re-ran §0, §D.1,
  §D.2 and the release-context read; the harvester verdict table (§D.3) and the
  per-link table in §B are `[delegated]` and marked as such in the report.
- **The "two-step" owner confirmation is weaker than its rhetoric** — both owner
  routes carry the second confirm as a boolean in the *same* HTTP body
  (`http_api.py:1452-1459`, `:1508`). Not a bypass, but reported rather than smoothed
  over. The strict two-code design exists only on the unreachable `release_pipeline`.
- **A stale docstring found** inside the release gate itself: `release_switch.py:122`
  says "No sender exists yet" while `publish_to_telegram` is a live caller.
- **This lane did not audit** `octopus_recovery/`, `shadow_homeostasis/`,
  `octopus_observation/`, `web/` beyond the egress-primitive grep (none found).

## Evidence paths

- Read directly by me this session: `ofn/budget/opslib.py:10-40`,
  `ofn/kernel/callbudget.py:28,80`, `ofn/node.py:3370`, `:3598-3620`,
  `ofn/kernel/release_switch.py:119-135`, `ofn/adapters/remote_brain.py:85-92`,
  `ofn/run.py:587,626`, `ofn/kernel/halt.py`, `ofn/adapters/halt_flag.py:1-60`,
  `ofn/kernel/halt_latch.py:1-25`, `grep master_halted` (full consumer list),
  `grep approve_manual|approved_manual`.
- Report of record: `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md`.
- Prior lane: `09-LANES/EMERGENCE-SAFE-SURGERY-20260916/LANE-REPORT.md`.
- Owner ruling: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-RULING-OD1-2026-09-17.md`.

## Validators

Both official validators were run. **Neither rc-carrying layer covers this lane's
artifacts** (`plans/`, `07-HANDOFF/`, `09-LANES/`, `06-EVIDENCE/` are all outside
`in_scope()`), so I also self-checked my six files against the validators' **own**
`check_note()`/`load_schema()`. No validator was modified.

### Official run

| Validator | rc layer | Report-only layer |
|---|---|---|
| `validate_frontmatter.py` | **0** errors in the 3 named charter files (`OCTOPUS-VITAL-DATA`, `OCTOPUS/CURRENT-TRUTH`, `ACTIVE-SEASON-`) | 503 legacy errors |
| `find_broken_links.py` | **17** in the hand-picked §11 layer | 134 in the operational layer |

**Both layers are byte-identical to the pre-lane baseline** (17 / 134, and 503 legacy).
**This lane introduced zero broken links and zero new frontmatter errors.**
One grep hit inside `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/` is **pre-existing**
and belongs to a sibling file (`SEASON-GOV-V8-ZIMAN-DASHBOARD.md`, broken
`[[GOV-V8-ACK]]`), not to the ruling I added there.

### Self-check of this lane's six files: 3 pass / 3 fail

| File | Verdict | Nature of the 3 failures |
|---|---|---|
| `plans/OCTOPUS-SAFETY-MAP-v1.md` | **PASS** | — |
| `…/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md` | **PASS** | — |
| `…/HALT-ORACLE-DOCTOR-SPEC.md` | **PASS** | — |
| `…/LANE-REPORT.md` | "no frontmatter" | **Not a defect — required convention.** Lane reports carry no YAML frontmatter by project convention; they carry the `GOV_VERSION=V8 · LADDER=L2` header line instead (verified against 3 existing lane reports). |
| `06-EVIDENCE/…/OWNER-RULING-OD1-2026-09-17.md` | `type: recorded-note` + keys `authority`, `subject` | **Pre-existing convention drift.** Mirrors the sibling `A-R0-INSURANCE-WORDING-RECORDED-2026-09-03.md` exactly; `recorded-note` is already used in `07-HANDOFF/` and is not in the schema enum. |
| `07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md` | `type: escalation`, `status: decided`, keys `as_of/lane/may_authorize/requires` | **Pre-existing convention drift** (residual items 2–4 are unchanged; adding `decided` was this lane's edit). |

**All three failures are convention-vs-schema conflicts, not content defects**, and
none of them is mine to resolve: the validator itself says "update Property Schema
first", new keys need owner approval + a schema edit, and the standing rule is
"do not rewrite a guard to go green; take the contradiction to the owner." Reported,
not silently resolved. This is the fourth instance of the same disease this lane
series documents.

## Rollback

Additive documents only. Complete rollback:

```bash
cd F:/backup
# move (not delete) to the sanctioned archive form per AGENTS.md §7:
#   99-ARCHIVE/archive_<name> with an archive_ prefix
# new this lane:
#   plans/OCTOPUS-SAFETY-MAP-v1.md            (modified additively — revert with git)
#   06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-RULING-OD1-2026-09-17.md
#   09-LANES/LIVE-PATH-GATE-AUDIT-20260917/   (2 files + this report)
#   07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md  (status open->decided)
```

`git revert <checkpoint-sha>` restores the pre-lane state of the one modified file.
No live service, timer, flag, gate, budget file, ledger row, migration, HALT file, or
node was touched. No code in either tree was modified.
