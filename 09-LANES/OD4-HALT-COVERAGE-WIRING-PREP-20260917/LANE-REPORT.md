# LANE-REPORT — OD4-HALT-COVERAGE-WIRING-PREP-20260917

GOV_VERSION=V8 · LADDER=L2 · mode: SPEC + PREP ONLY (zero implementation) · lead: main session (ZCode)
HOLD: no patch applied · no diff written to any file · no service restarted · no flag edited · no HALT file touched · no systemd/timer change · no live-node contact
authority: owner ruling OD-4 Option B, 2026-09-17
status: **STOPPED at the owner's evidence rule** — the named target for effect (b) did not resolve

## What was done

Executed the OD-4 Option-B directive as a **spec-and-prep lane only**. Ran the
consumer trace myself with recorded commands (no claim rests on a docstring or a test
result), produced the three requested artifacts, and **stopped before implementation**
because the owner's own evidence rule fires.

### Deliverables

| # | Owner asked for | Artifact |
|---|---|---|
| 1 | Spec only: doctor spec + offline fixture harness | `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` §8 (added), §2 item 6 (cross-ref) |
| 2 | Zero live changes | attestation block in `CHANGE-PREP-PACKET.md` §6 |
| 3 | Cached verification that only two consumers map to the two effects | `09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CONSUMER-MAP.json` (JSON validated) |
| 4 | Change-prep packet: exact diff plan, test cases, rollback, no-scope-leak proof | `09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CHANGE-PREP-PACKET.md` |
| 5 | Report output only | this report + the three above; no side effects |

### Cached verification result — the two effects do NOT both have one consumer

| Effect | Consumers found | Owner instruction expected | Agrees? |
|---|---|---|---|
| **E-A** Telegram send (`telegram_channel.py:65`) | **1** — `node.py:3607` (`ReleaseContext.kill_switch_active`) | 1 | **yes** |
| **E-B** text-model spend (`remote_brain.py:88`) | **2** — `ModelRouter.ask` (`router.py:130`) **and** `assistant_update.py:32` (direct `RemoteBrain.answer`, bypasses the router entirely) | 1 | **no** |

Evidence for each (`CONSUMER-MAP.json` carries the command + observed output):
- `grep -rn "\.publish("` over `ofn/ tools/ ops/ scripts/` → exactly one production line, `node.py:3637`. `pilot_daily.py` uses the **read-only** adapter.
- `grep -rn "\.answer(" ofn/ | grep -v tests` → `assistant_update.py:32` and `router.py:171` only.
- `ofn-assistant-update.timer` → `OnCalendar=*-*-* 04:10:00`, `ExecStart=/usr/bin/python3 -m ofn.assistant_update` — **live daily**.
- `ModelRouter(build_brains(cfg), node.quota, ...)` at `run.py:548`; `router.py:214` calls `self._quota.check` — `NodeQuota`, not `CallBudget`.
- `grep -n call_budget ofn/node.py` → only `:326, :422, :1707-1720, :3587, :3643` — i.e. diagnostics, owner-ask submit, studio reading, and the **Telegram publish** slot.

### ⚠ The blocking finding (BQ-1)

**The owner named `callbudget.py` as the text-model budget path. It gates neither live
model-egress consumer.** Wiring the oracle there would produce a change that passes its
own tests, reads as instruction-compliant, and stops nothing — the `DECLARED ≠ WIRED`
pattern applied to the instruction itself.

Per the owner's evidence rule ("if any consumer path is not resolvable within the audit
scope, record it as UNVERIFIED and stop before partial implementation"), **no
implementation was produced.** The packet carries both variants — b1 (the named target,
rejected with proof) and b2 (the corrected target, recommended) — and is explicitly
gated on BQ-1.

### Also verified while tracing

- `ofn/kernel/__init__.py` imports the whole kernel package, which is contractually pure
  (`tests/test_kernel_purity.py`: stdlib only, no I/O/clock/env/filesystem). This is what
  makes it legitimate for the doctor's Tier-2 fixtures to import the **real**
  `ofn.kernel.halt` predicate instead of reimplementing it — with a bounded allowlist and
  a mechanical runtime guard, and any second `ofn` import a stop condition.
- Exact rule strings for test assertions: `RULE_KILL = "release:kill-switch-active"`,
  `RULE_OK = "release:ok"`, `RULE_LEDGER = "ledger:not-ready"` (`release_switch.py:63-73`).
  `OwnerRelease.may_publish` checks the kill switch **first and unconditionally**
  (`:79-82`) — so effect A needs no change to the release gate at all, only a more
  truthful input.

## What remains

- **BQ-1 must be answered before anything is implementable.** If the owner reaffirms
  `callbudget.py`, the packet must be rewritten and the ineffectiveness recorded as an
  accepted limitation — not presented as a fix.
- **BQ-2** — for `assistant_update.py:32`: add the halt check at the direct site
  (recommended, minimal) or route it through the router (larger; changes its budget
  behaviour, which this scope excluded).
- **Doctor: spec complete (incl. fixture harness), NOT BUILT.** OD-1 clause 3 authorizes
  a read-only build. The owner's OD-4 constraint requires machine-readable pre/post
  receipts before any change — the doctor is what captures the *pre* evidence, so it
  should precede implementation.
- **Effect-A packet is ready to implement the moment BQ-1 is answered** (its site is
  unaffected by BQ-1; only effect B is blocked).

## What failed

- **The instruction's premise for effect (b) is wrong** — recorded as a finding, not
  worked around. This is the second premise correction in this lane series (the first was
  my own D-1 severity).
- **One attestation caveat, stated rather than glossed.** `git -C F:/ofn-node status
  --porcelain` on the target set returns the four target files **clean**, but also
  `?? BUDGET.json`. That file is **untracked and never tracked** (`git log -- BUDGET.json`
  → empty), so git provides no hash comparison for it — I cannot *prove* it is unchanged
  by hash, only attest that this lane issued **read-only** commands (`grep`, `sed`, `ls`,
  `cat`) against `F:\ofn-node` and no write. Flagged so the next agent knows the
  difference between "verified unchanged" and "attested unchanged".
- **No worktree created** (`AGENTS.md` §8 deviation, consistent with the two prior lanes
  in this series). Worked in-place at `F:\backup`; deliverables are additive documents.
- **Three items remain UNVERIFIED by construction**: on-node runtime path resolution
  (forbidden), deployed env values (not read, not contacted), and whether an out-of-repo
  `octopus-*` unit invokes a model or send path. All three are listed in
  `CONSUMER-MAP.json.unresolved`.
- **Not audited**: `octopus_recovery/`, `shadow_homeostasis/`, `octopus_observation/`,
  `web/` beyond the egress-primitive grep (none found).

## Evidence paths

- Machine-readable consumer trace with per-claim commands:
  `09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CONSUMER-MAP.json`
  (JSON validated: 2 effects, 2 blocking questions, 3 unresolved, 0 live changes).
- Change-prep packet: `…/CHANGE-PREP-PACKET.md` (§1 effect A diff, §2 effect B variants,
  §3 test cases T1–T9, §4 no-scope-leak proof, §5 rollback, §6 attestation).
- Doctor spec + fixture harness: `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` §8.
- Prior audit: `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md`.
- Owner rulings: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-RULING-OD1-2026-09-17.md`;
  OD-4 card `07-HANDOFF/OPEN-DECISION-HALT-COVERAGE-2026-09-17.md`.

## Validators

Run on this lane's artifacts. Explicit counts in the commit message.

**Known scope limitation (unchanged):** `plans/`, `07-HANDOFF/`, `09-LANES/` and
`06-EVIDENCE/` are **outside both validators' rc-carrying layers**, so a green does not
cover these files. They were self-checked against the validators' own
`check_note()`/`load_schema()` instead. No validator was modified. Per the standing rule,
convention-vs-schema conflicts are reported to the owner, never resolved by rewriting a
guard.

One deliberate exception: `CONSUMER-MAP.json` is a machine-readable data artifact, not a
vault note, and is intentionally **frontmatter-free** (it is validated as JSON, not as a
note).

## Rollback

Additive documents only; no code, no state, no external effect.

```bash
cd F:/backup
# new this lane (3 files + 2 edits):
#   09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CONSUMER-MAP.json
#   09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/CHANGE-PREP-PACKET.md
#   09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/LANE-REPORT.md
# edits: HALT-ORACLE-DOCTOR-SPEC.md (§2 cross-ref + §8), OD-4 card (status open->decided)
git revert <checkpoint-sha>     # restores the two edited files; then remove the new dir
# AGENTS.md §7: archive with an archive_ prefix rather than rm -rf, if keeping them
```

Nothing under `F:\ofn-node` was modified, so there is no code rollback. No flag, timer,
service, HALT file, ledger row, or node was touched.

---

## ADDENDUM 2026-09-17 — owner card OD-4 applied

The owner card (`06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-CARD-OD4-2026-09-17.md`,
recorded verbatim) **approved the corrected targets that this lane's trace produced** and
**rejected `callbudget.py`** as a wiring target. Outcome of applying it:

| Item | Before the card | After |
|---|---|---|
| BQ-1 (target for effect B) | open, blocking | **CLOSED** — router admission point + `assistant_update.py:32`, as traced |
| BQ-2 (`assistant_update`) | open, recommendation | **CLOSED** — owner chose the **direct call site** (the lane's recommendation) |
| `callbudget.py` | named by the directive | **REJECTED by owner**; formally out of OD-4 scope |
| Packet §1 / §2.2 diffs | proposed | **no rework needed** — already the approved shape |
| Wiring implementation | blocked | **still NOT AUTHORIZED** — blocked on owner order steps 1–3 |

### What the card added to the deliverables

1. **`CHANGE-PREP-PACKET.md` §0** — approved-target table, BQ closure, and the
   rationale kept as an audit trail rather than deleted.
2. **§0.5 COVERAGE PROOF** (the card's success definition, *"prove coverage, not just
   path correctness"*): a pre/post coverage matrix using only the four authorized labels
   — **3 consumers, 3 path-`WIRED`, 0 covered by the canonical oracle today (all three
   `DOC_ONLY`)**, targeting `DOC_ONLY → WIRED` for exactly those three and **no other
   consumer's label may change**.
3. **§0.5.3 pre/post receipt contract** (owner order step 3) — `octopus.halt-coverage-receipt.v1`,
   with `PRE` mandatory before any wiring lands, exactly three consumer rows,
   `out_of_scope_consumers.any_label_changed == false`, and `mutations_performed: 0`.
4. **§7 rewritten** — the owner's four-step order encoded as the gate table, plus a
   scope lock and the explicit "no live ablation" test rule.
5. **`CONSUMER-MAP.json` → revision 2** — coverage labels per consumer, owner-card
   decisions, BQ status, the receipt contract, and the stop-condition resolution.

### Stop-condition resolution (reported, not assumed)

The card's rule is *"if any consumer path is still UNVERIFIED, stop and report instead of
guessing."* Recorded precisely: **no consumer path is UNVERIFIED** — the consumer sets
for both effects are fully resolved and all three consumers are path-`WIRED`. The three
UNVERIFIED items (U-1 on-node path resolution and file state, U-2 deployed env values,
U-3 out-of-repo units) are **runtime/environmental, not structural**. The stop condition
does **not** fire, and those unknowns are precisely what the doctor's Half B captures —
which is why the owner's order sequences the doctor before the wiring.

### One honest note on vocabulary

The four authorized coverage labels contain no value for "verified absent, and not even
documented as applying here" — the literal state of B-2, which has **no budget gate at
all**. `DOC_ONLY` was used and the gap flagged in the packet rather than stretching the
label. A fifth label (e.g. `ABSENT`) would be the owner's call, not this lane's.

### Attestation for the addendum

Still **zero** implementation: no wiring code written, no file under `F:\ofn-node`
modified, no service restarted, no flag edited, no HALT file touched, no systemd/timer
change, no node contacted. This addendum produced documents only.
