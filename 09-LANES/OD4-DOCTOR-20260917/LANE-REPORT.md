# LANE-REPORT — OD4-DOCTOR-20260917

GOV_VERSION=V8 · LADDER=L2 · mode: BUILD + OFFLINE RUN (read-only) · lead: main session (ZCode)
HOLD: zero wiring implementation · no HALT file created/deleted/armed · no service/timer/systemd/env/budget change · no live-node access · no write outside `receipts/`
authority: owner card OD-4 (2026-09-17) — order steps 1 and 2 only

## What was done

Built the halt-oracle coverage doctor and ran it once offline, as OD-4's order steps 1
and 2 require. **No wiring was implemented** (that is step 4 and is not authorized).

| # | Owner deliverable | Artifact |
|---|---|---|
| 1 | doctor spec | `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` §9 AS-BUILT added |
| 2 | offline result report | `09-LANES/OD4-DOCTOR-20260917/REPORT-DOCTOR-OFFLINE-RUN.md` |
| 3 | coverage receipt JSON | `_ops/halt_oracle_doctor/receipts/PRE-coverage-<ts>.json` + `PRE-result-<ts>.json` + `mismatches-<ts>.jsonl` |
| 4 | exact wiring recommendation | run report §6 — **conditional on §5.1** |

### Built

`F:\backup\_ops\halt_oracle_doctor\` — 7 modules + harness, **1,570 lines**, stdlib only,
zero lines of `ofn` code touched.

### The result

**3 consumers · 3 path-`WIRED` · 0 covered by the canonical halt oracle (all `DOC_ONLY`).**

| Consumer | Evidence the doctor extracted |
|---|---|
| `A-1` `ofn/node.py:publish_to_telegram` | `kill_switch_active=self.killed` |
| `B-1` `ofn/adapters/router.py:ask` | gates on path: `_charge()@164` |
| `B-2` `ofn/assistant_update.py:main` | first brain call at line 28 |

4 mismatches, all `owner_action_required`: 1 `path_divergence`
(documented `F:/ofn-node/HALT` ≠ computed `/home/ari/ofn/HALT-ALL` = D-3, produced by the
tool rather than asserted) + 3 `coverage_gap`. `mutations_performed: 0`, `node_observation: NOT_PERFORMED`.

### Verification

- **Certification: 0 static violations**, canonicalization self-test PASS against a
  frozen vector, allowlisted predicate import proven transport-free at runtime.
- **Harness: 36 tests / 6 tiers, all green** (T1 resolver 7 · T2 predicate 6 ·
  T3 coverage 3 · T4 safety-negative 11 · T5 non-mutation canary 5 · T6 determinism+guard 4).
- **14 halt-reading sites found, 0 parse failures.** Independently re-confirms the
  audit's "exactly 5 modules consume `master_halted()`" by a different method.

## What remains

- **§5.1 of the run report — the one blocking read.** `ofn/kernel/start_permit.py:136
  decide_start` and `ofn/kernel/stale_class.py:335 admit_refresh` call `is_halted` on a
  value they receive. **Where that raw value comes from is `UNVERIFIED`.** If a live path
  feeds them a real file read, the PRE receipt understates current coverage and must be
  regenerated before any wiring. This is a *read* task, not a wiring task.
- **Half B (on-node) not built, not run.** Which file each *running service* resolves,
  and its real state, needs on-node observation — not authorized. Every receipt says so.
- **Wiring (order step 4): NOT AUTHORIZED, NOT STARTED.** Three approved edits with an
  exact diff plan exist (`CHANGE-PREP-PACKET.md` §1/§2.2); the acceptance gate is run
  report §6.2.
- **POST receipt** must be produced with the same command + same declared HOME, and must
  show the same 3 consumers at `WIRED` with `any_label_changed == false`.

## What failed (all caught and fixed; each is a real trap)

1. **The safety check refused its own package — three times, correctly.** R5 flagged its
   own rule definition (→ one *documented* file-level exemption); R2 rejected
   `from ofn.kernel import halt` and `from ofn.kernel.halt import is_halted` (→ the check
   now resolves the effective module per alias); R5 flagged the negative test that plants
   a forbidden literal (→ the test builds the string from parts, so **no second exemption
   was needed** — the bad fix of exempting the test file was avoided).
2. **Git-Bash silently rewrote a POSIX argument** into `C:/Program Files/Git/home/ari`,
   producing a plausible but **wrong** oracle path on the first run. Fixed with a
   fail-closed guard + a test. A silently wrong answer is the exact failure mode this
   tool exists to detect.
3. **`ofn/helpers/brainport.py` carries a U+FEFF BOM** → `ast.parse` raised. The doctor
   now reads as `utf-8-sig` and treats an unparsable file as a recorded unknown, never a
   silent skip. *Second BOM artifact in two days.*
4. **`pathlib` mis-modelled a Linux path on Windows** → resolution is now pure POSIX
   string joining, independent of the host OS.
5. **My own test error:** the F2 fixture asserted `/srv/ofn/HALT-ALL` for `HOME=/srv/ofn`
   when `OFN_ROOT` always appends `"ofn"`. The test was wrong, not the code; corrected and
   annotated in place.
6. **A heredoc backslash trap bit again** (`\\n` arriving as a real newline) and split a
   test line. Repaired by building the backslash with `chr(92)` — see the existing trap
   memory; this is the same family as traps 11/26/28/38/42.

## Evidence paths

- Doctor: `_ops/halt_oracle_doctor/{canon,safety_check,resolver,coverage,doctor}.py` ·
  harness `_ops/halt_oracle_doctor/tests/test_doctor.py` ·
  receipts `_ops/halt_oracle_doctor/receipts/`.
- Run report: `09-LANES/OD4-DOCTOR-20260917/REPORT-DOCTOR-OFFLINE-RUN.md`.
- Spec as-built: `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` §9.
- Prior audit + packet: `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/` ·
  `09-LANES/OD4-HALT-COVERAGE-WIRING-PREP-20260917/`.
- Owner card: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/OWNER-CARD-OD4-2026-09-17.md`.

## Boundaries — attested

| Boundary | State |
|---|---|
| `F:\ofn-node` unchanged | **held** — HEAD `0da921b1b9eecdfc92346ebb38813055f39f1e2c`; the 7 guarded files byte-identical across a full run (asserted by test T5) |
| No HALT file created/deleted/armed | **held** — asserted before/after; arming is refused by test |
| No live-node access | **held** — `node_observation: NOT_PERFORMED` |
| No write outside `receipts/` | **held** — `_guard_write()` refuses; negative-tested |
| No partial implementation | **held** — zero wiring code written |
| No new human reviewer needed | **held** — self-certifying, Class A |

## Rollback

Additive files plus four edited documents; no code, no state, no external effect.

```bash
cd F:/backup
# new:      _ops/halt_oracle_doctor/            (7 modules + harness + receipts)
#          09-LANES/OD4-DOCTOR-20260917/        (this report + run report)
# edited:  09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md  (§9 appended)
git revert <checkpoint-sha>          # restores the edited spec; then remove the two new dirs
# AGENTS.md §7: move to 99-ARCHIVE/ with an archive_ prefix rather than rm -rf
```

Nothing under `F:\ofn-node` was modified, so there is no code rollback. No flag, timer,
service, budget, gate, HALT file, ledger row, or node was touched.

## Validators

Run for this lane. Explicit counts in the commit message. As before, `_ops/` and
`09-LANES/` are **outside both validators' rc-carrying layers**, so a green does not
cover these artifacts; they were self-checked against the validators' own
`check_note()` instead, and `receipts/*.json` is validated as JSON (not as a note).
No validator was modified.
