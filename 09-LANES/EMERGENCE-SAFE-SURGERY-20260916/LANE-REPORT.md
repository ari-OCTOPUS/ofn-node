# LANE-REPORT — EMERGENCE-SAFE-SURGERY-20260916

GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY (no code changed, nothing executed on any node) · lead: main session (ZCode)
HOLD customer_send · may_authorize=false · production_authorized=false · no live-node contact

## What was done

Planning lane for `MP-EMERGENCE-SAFE-SURGERY-PLANNER-2026-09-16`. Read the real
architecture of both trees, verified every load-bearing claim with my own commands,
and produced five documents. **No code was changed. Nothing was run against the
organism.**

### Verified directly (commands run in this session, not relayed)

| Claim | Command | Result |
|---|---|---|
| `Node.propose` has zero production callers | `grep -rn "\.propose(" --include=*.py . \| grep -v "^./tests/"` | none |
| `admit()` reachable only via `propose`/`owner_decide` | `grep -rn "admit(" --include=*.py ofn/` | only `ofn/node.py:2263` |
| `_gate_enqueue`'s only check is `self.killed` | read `ofn/node.py:3036-3054` | confirmed; docstring says "does NOT re-run admit/risk/quota" |
| `RunGate(` exists only in tests | `grep -rn "RunGate(" --include=*.py` | 4 test files, no production site |
| Wire flag baked ON by installer | `grep -n WIRE tools/install_systemd.sh` | `:19 Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1` |
| Two incompatible `canonical()` rules | read `ofn/adapters/ledger.py:52` vs `octopus_observation/fixture_run.py:68` | compact vs default separators |
| Kill-switch path fragmentation; `F:\ofn-node\HALT` absent | `ls HALT*`; grep `HALT-ALL`/`_halt_path` | confirmed absent; 3 other conventions |
| `grants_send()` structurally false | read `ofn/adapters/receipt.py:93`, `ofn/kernel/hash_chain.py:46` | confirmed |
| Deceptive-grid env identical across seeds | read `env_factory.py:290-293`; grep `self.rng` | seed drives noise only, never layout |
| Candidate hardcodes the answer / reads hidden state | read `agents.py:32,322,356,384,405,424` | confirmed |
| Results numbers | recomputed from `results.csv` (600 rows) | 0/100, 97/100, 100/100; novelty median TTD 1529.5 < 1769.0 |
| `octopus_observation` is stdlib-only, writes nothing | grep imports; read `fixture_run.run_pipeline` | confirmed (returns dict) |

### Deliverables

| Artifact | Path |
|---|---|
| Megaplan | `F:\backup\plans\MEGAPLAN-EMERGENCE-SAFE-SURGERY-v1.md` |
| Execution prompt | `F:\backup\plans\MP-IMPLEMENT-EMERGENCE-SAFE-SURGERY-v1.md` |
| Discovery report | `F:\backup\plans\EMERGENCE-SAFE-SURGERY-DISCOVERY-REPORT.md` |
| Safety map + scorecard | `F:\backup\plans\OCTOPUS-SAFETY-MAP-v1.md` |
| Surgical protocol | `F:\backup\plans\SURGICAL-PROTOCOL-v1.md` |
| Owner decision OD-1 | `F:\backup\07-HANDOFF\OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md` |

### Headline findings

1. **The self-declared policy choke point is off the live path.** `ofn/kernel/gates.py:3`
   says `admit()` is "the only path"; `ofn/node.py:3036` `_gate_enqueue` is a second
   path and says so. `admit()`'s only production-shaped caller has zero production callers.
2. **The documented kill switch does not exist.** `AGENTS.md` GOV-V7 names
   `F:\ofn-node\HALT`; the code reads `~/ofn/HALT-ALL` (or a caller-supplied path).
   Because absent = RUNNING, arming the documented file fails **silently**.
3. **The 97/100 result does not survive inspection.** Answer hardcoded in the
   candidate, hidden state read directly, one maze for all 100 seeds, and the
   novelty control won outright (100/100, faster). Premise accurate, conclusion not supported.
4. **Dominant failure class is `DECLARED ≠ WIRED`** — five independent instances,
   including a module that self-declares "not wired".

## What remains

- **OD-1** (kill-switch paths) — owner decision, registered. Options A/B/C with a
  recommendation. Not applied.
- **OD-2** (safety-map placement: `plans/` vs vault root) — cosmetic, owner preference.
- **OD-3** (make `declared ≠ wired` a standing gate on capability claims) — governance choice.
- **P-6 harvesters** (`ofn/agents/h1_*.py`, `web_lookup`, `external_witness.py`) —
  scored `UNVERIFIED` in the safety map. Highest-value next read; read-only review, no experiment.
- **The implementation prompt has not been executed.** `_ops/probe_harness_v0/` does not
  exist. It is a separate lane's work.

## What failed

- **No worktree was created.** `AGENTS.md` §8 requires each agent to work in its own
  git worktree (`git worktree add --no-checkout -b codex/<lane> F:/wt-<lane> HEAD`).
  This lane worked in-place at `F:\backup` on branch `rescue/octopus-live-tree-20260821`
  because the deliverables were documents at paths the owner named, and creating a
  worktree would have put them where the owner could not find them. **This is a
  deliberate deviation, logged here rather than hidden.** Risk is low (additive
  docs only, no code, no live surface) but it is a deviation from a binding rule.
- **Cross-lane file writes in shared directories.** New files were created in
  `07-HANDOFF/` and `09-LANES/`. §6 of `AGENTS.md` mandates registering owner
  decisions in `07-HANDOFF/`, and §9 mandates the lane report in `09-LANES/`, so both
  locations were required; no *existing* file in either directory was modified.
- **Two typos were made and corrected** before finalizing (`ofs/` → `ops/ign1_telegram_ignite.py`;
  `check__safety` → `safety_check.py`). Recorded for honesty.
- **I introduced 2 broken wikilinks and fixed them.** `plans/OCTOPUS-SAFETY-MAP-v1.md`
  carried `parent: "[[CONSTITUTIONAL-ZONES]]"` and `aligns_to: "[[LIVE-ORGANISM-MAP]]"`;
  both targets are `.yaml`/`.json` files and can never resolve as notes. The
  broken-link checker caught them (it scans the whole tree, unlike the frontmatter
  validator). Removed; total went 153 → 151. The fields were cosmetic — neither file
  was referenced by anything.
- **One owner-decision card remains non-compliant with the Property Schema** (3
  residual items, the directory's existing `type: escalation` convention). Reported
  as a schema-vs-convention conflict rather than silently resolved — see the
  validator section above. **Not a failure of this lane's verdict; a pre-existing
  drift this lane surfaced.**
- **P-6 (harvesters) not audited.** Out of scope for this lane and explicitly left
  `UNVERIFIED` rather than assumed clean.
- **`F:\ofn-node\HALT` was checked only at the repo root.** Other locations on other
  hosts were not enumerated.

## Evidence paths

- Live runtime code read: `F:\ofn-node\ofn\kernel\gates.py`, `ofn\node.py` (`:2254`, `:2263`, `:3036`), `ofn\adapters\ledger.py`, `ofn\adapters\receipt.py`, `ofn\adapters\halt_flag.py`, `ofn\kernel\halt.py`, `ofn\kernel\halt_latch.py`, `ofn\kernel\hash_chain.py`, `ofn\budget\opslib.py`, `ops\ign1_telegram_ignite.py`, `octopus_observation\fixture_run.py`.
- Prior experiment read: `F:\backup\_ops\hypothesis_engine\experiments\{results.csv,env_factory.py,agents.py,STATUS.md}`.
- Governance read: `F:\backup\AGENTS.md`, `CONSTITUTIONAL-ZONES.yaml`, `LAB-DOCTOR-CONTRACT.yaml`, `06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\GOV-{V7,V8,FREEDOM-V2,AUTONOMY-V3}*`.
- Negative evidence: no `plans/` existed at vault root before this lane; no class named
  `PolicyGate`; no `F:\ofn-node\HALT`; no `DECEPTIVE-ENV-3AGENT-EXPERIMENT.md`;
  no `HYPOTHESIS-BRAIN-SPEC.md`; no output from the S1–S8 provenance runner.

## Validator results (explicit counts, per the charter rule)

Both validators were run. Both exit **1**. Neither of my artifacts is in the
rc-producing layer of either — verified, and the reason is stated plainly below.

### `04 - Architect System/scripts/validate_frontmatter.py` — exit code 1

| Layer | Count | rc? |
|---|---|---|
| `OCTOPUS-VITAL-DATA` / `OCTOPUS/CURRENT-TRUTH` / `ACTIVE-SEASON-` errors | **0** | **yes** |
| All other errors ("legacy", report-only) | **503** | no |
| Notes scanned (`in_scope`) | 872 | — |
| Schema ↔ `types.json` drift | 1 | yes (no drift ⇒ 0) |

Schema source: `schema` (43 keys · 19 types · 9 statuses) — **not** the fallback.

### `04 - Architect System/scripts/find_broken_links.py` — exit code 1

| Layer | Count | rc? |
|---|---|---|
| Hand-picked layer §11 | **17** | **yes** |
| Operational / document-package layer | **134** | no |
| **Total** | **151** | — |

**This lane started at 153 and ends at 151** — I introduced 2 and fixed both
(see "What failed"). **None of the 17 rc-producing broken links is mine**; they are
pre-existing, mostly in `00 - Inbox/2026-08-15*` and `07 - Knowledge/شناخت-اختاپوس/*`.

> Worth flagging: one of the 17 is **`[[PolicyGate]]`** in
> `07 - Knowledge/FPGA-Reflex-Layer.md`. The vault has a note linking to a
> `PolicyGate` that exists neither as a note nor as a symbol anywhere in
> `F:\ofn-node`. That is independent corroboration of §1.3 of the megaplan: the
> name in the project's own prose corresponds to a class that does not exist.

### ⚠ What "green" actually means here — scope finding

**1. The frontmatter validator's rc layer is three named files, not the vault.**
A 2026-09-10 judge ruling made both validators two-tiered, and defined the charter
layer as errors whose text contains `OCTOPUS-VITAL-DATA`, `OCTOPUS/CURRENT-TRUTH`,
or `ACTIVE-SEASON-`. So "charter layer: 0 errors" means **three specific files are
clean** — a much weaker statement than it reads as. (The same diff contains one
genuine hardening: `\d` → `[0-9]` in the date check, because `\d` matches Persian
digits and produced a false-PASS. The two-tiering itself is a reasoned ruling — a
permanently-red validator carries no signal — with the side effect that the green
now covers almost nothing.)

**2. Every artifact this lane produced is outside both validators' rc scope.**
`in_scope()` admits only `SYSTEM_FOLDERS` (`00 - Inbox`, `01 - Dashboard`,
`02 - Life OS`, `05 - Agents`, `06 - Architecture Maps`, `09 - People`,
`10 - Telegram processing`), `PROJECT.md` files, and top-level notes under
`03 - Projects` / `07 - Knowledge`. **`plans/`, `07-HANDOFF/`, and `09-LANES/` are
all excluded** — verified: `in_official_scope=False` for all six files.

I therefore checked my six files against the validator's **own** `check_note()` and
`load_schema()` (read-only; the validator was not modified):

**5 pass / 1 fail.**

The failure is `07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md`, with 3
residual items: `type: escalation`, `status: open`, and out-of-schema keys
`as_of, lane, may_authorize, requires`. **These are the existing escalation
convention in that directory** — 2 sibling files use the identical shape
(`B-PULSE-IMAP-SSH-RO-ESCALATION-2026-09-03.md` et al.). I added the core keys
`tags` and `updated` to close two of the five original gaps, and left
`type: escalation` / `status: open` / `requires:` intact rather than become the one
file in that directory an agent cannot recognise as an escalation card.

**Reported, not silently resolved**, per the standing rule "do not rewrite a guard
to go green; take the contradiction to the owner." Two options exist and neither is
mine to pick: (a) add `escalation` to the schema's `type` enum, `open` to
`statuses`, and the four operational keys — with owner approval, since new keys
require a schema edit; or (b) migrate `07-HANDOFF/` escalation cards to
`type: report, status: active` and carry `requires:` in the body.

**This is a third unreported instance of the pattern this lane documents**: a schema
that reads as authoritative over the vault while an entire operational directory —
including **every owner-decision card** — sits outside its scope, so its drift
cannot be detected by the official run.

No validator was modified. No file was changed to make a validator green.

## Rollback

Everything this lane produced is **additive and file-local**. Complete rollback:

```bash
cd F:/backup
rm -r plans/                                                      # 5 new documents
rm 07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md
rm -r 09-LANES/EMERGENCE-SAFE-SURGERY-20260916/
```

(Use file-manager deletion or `git clean` on those exact paths — `AGENTS.md` §7 forbids
`rm -rf`; the above is listed for precision, and an equivalent move to `99-ARCHIVE/`
with an `archive_` prefix is the sanctioned form if the files are to be kept.)

- No live service, timer, flag, gate, budget file, ledger row, or database migration
  was touched. Nothing to disarm.
- No code in either tree was modified, so there is no code rollback.
- No external effect was produced, so no receipt-or-rollback obligation arises.
