---
type: report
status: active
tags: [octopus, od-4, doctor, halt-oracle, coverage, offline-run, pre-receipt]
updated: 2026-09-17
project: "[[OCTOPUS]]"
---

# DOCTOR — OFFLINE RUN RESULT + WIRING RECOMMENDATION

`GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY / OFFLINE · lane: OD4-DOCTOR-20260917`
`authority: owner card OD-4 (2026-09-17) — order step 1 "Build doctor first", step 2 "Run doctor once offline"`
`WIRING: NOT IMPLEMENTED · NOT AUTHORIZED YET (order step 4)`

## 0. Bottom line

The doctor is **built, certified, and has run once offline**. It confirms the audit's
conclusion from the code itself, and it produces the coverage map OD-4 asked for.

> **3 consumers · 3 path-`WIRED` · 0 covered by the canonical halt oracle (all three `DOC_ONLY`)**
>
> `A-1` Telegram send → `kill_switch_active=self.killed`
> `B-1` router model admission → gates on path: `_charge()@164` (no halt oracle)
> `B-2` assistant_update direct call → first brain call at line 28 (no gate at all)

**4 mismatches emitted, all `owner_action_required`**: 1 `path_divergence` + 3
`coverage_gap`. `mutations_performed: 0`. No node was contacted.

## 1. What was built

`F:\backup\_ops\halt_oracle_doctor\` — 7 modules + harness, **1,570 lines**, stdlib only,
zero `ofn` code touched.

| File | Lines | Role |
|---|---|---|
| `canon.py` | 76 | the single canonicalization rule, pinned by a frozen digest |
| `safety_check.py` | 233 | fail-closed self-certification (R0–R6) + the one allowlisted import |
| `resolver.py` | 314 | halt-site discovery, declared-HOME path resolution, file-state classification |
| `coverage.py` | 255 | AST analysis of the three approved consumers → coverage labels |
| `doctor.py` | 309 | orchestrator, CLI, receipt emission, write-scope guard, shell-mangle guard |
| `tests/test_doctor.py` | 363 | the offline fixture harness (6 tiers) |
| `__init__.py` | 20 | boundaries stated as doc |

Invocation (Git-Bash needs `MSYS_NO_PATHCONV=1` — see §5.3):

```bash
MSYS_NO_PATHCONV=1 python -m _ops.halt_oracle_doctor.doctor \
    --repo F:/ofn-node --declared-home /home/ari \
    --documented-oracle F:/ofn-node/HALT --phase PRE
```

## 2. Certification (runs BEFORE any analysis)

| Check | Result |
|---|---|
| Static rules R0-parse, R1-module, R2-protected, R3-dynamic-exec, R5-flag-literal, R6-env-read | **0 violations** |
| Canonicalization self-test vs frozen vector | **PASS** (rule `octopus.canon.compact-sortkeys-utf8/1`) |
| Allowlisted predicate import purity | **PASS** — `ofn.kernel.halt` imported; no transport module in `sys.modules` |
| `mutations_performed` | **0** on every receipt |

**The one bounded exception, verified not trusted.** The doctor imports exactly one
`ofn` module — `ofn.kernel.halt` — because *testing a reimplementation proves nothing*.
The exception is checked mechanically at runtime: after the import, no module under
`socket/ssl/http/urllib.request/sqlite3/subprocess/select/asyncio` may be in
`sys.modules`. Also checked, not assumed: `ofn.kernel` is import-pure (no `os`,
`pathlib`, `io`, `socket`) — the only non-trivial import anywhere in the kernel is
`ofn/kernel/auth.py:35` `import urllib.parse`, which is query-string unquoting and adds
only `{ipaddress, math, urllib, urllib.parse}` to `sys.modules`.

**Stated limitation, not hidden:** R5 (flag-family literals) does not self-scan
`safety_check.py`, because the rule's own definition must contain the pattern it
forbids. That is the only file-level exemption, and it is recorded in every receipt.

## 3. The offline run — coverage map

| Consumer | Effect | Path | **Coverage** | Evidence extracted from the code |
|---|---|---|---|---|
| `ofn/node.py:publish_to_telegram` (`A-1`) | Telegram send | `WIRED` | **`DOC_ONLY`** | `kill_switch_active=self.killed` |
| `ofn/adapters/router.py:ask` (`B-1`) | model spend | `WIRED` | **`DOC_ONLY`** | gates on path: `_charge()@164` |
| `ofn/assistant_update.py:main` (`B-2`) | model spend | `WIRED` | **`DOC_ONLY`** | first brain call at line 28 |

`path_correctness` is a **declared input** carried from the 2026-09-17 audit with its
source named in the receipt — it is not re-derived here and not presented as the
doctor's own finding. `coverage` is the doctor's finding.

### 3.1 Canonical oracle (computed, not hardcoded)

Read from `ofn/budget/opslib.py` by AST: `HALT_FLAG = OFN_ROOT / "HALT-ALL"` with
`OFN_ROOT = HOME / "ofn"`. For the declared `HOME=/home/ari` this resolves to
**`/home/ari/ofn/HALT-ALL`**, plus the `HALT_SURVIVAL_LOOP=1` env override.
The path moves when the declared HOME moves — asserted by a test, so a hardcoded answer
would fail.

**`path_divergence` (high, owner-action):** documented oracle `F:/ofn-node/HALT`
(the name in `AGENTS.md` GOV-V7) **≠** the oracle the code computes. That is D-3,
produced by the tool rather than asserted in prose.

### 3.2 Every halt-reading site (14 found, 0 parse failures)

| What it reads | Sites |
|---|---|
| `opslib.master_halted()` — **the canonical oracle** | `capability_token.py:87` · `followup_worker.py:38` · `outbound_worker.py:214,451` · `quote_pipeline.py:79` · `release_pipeline.py:106,184` |
| `is_halted` (pure predicate) on a caller-supplied value | `halt_flag.py:39,47` (the reader itself) · `halt_log.py:228` · **`kernel/stale_class.py:335`** · **`kernel/start_permit.py:136`** |
| literal `<root>/HALT` path constant | `ops/ign1_telegram_ignite.py:28` |
| caller-supplied path (`self._halt_path`) | `run_gate.py:35` — **no production constructor** |

**Independent confirmation:** `master_halted()` has exactly **5 consuming modules** —
the same count the audit reached by a different method.

**New lead, flagged not concluded:** `ofn/kernel/start_permit.py:136 decide_start` and
`ofn/kernel/stale_class.py:335 admit_refresh` call `is_halted` on a value they receive.
**Where that raw value comes from is NOT resolved by this pass → `UNVERIFIED`.**
If a live path feeds them a real file read, part of effect B is halted differently than
this PRE receipt states, and the receipt must be regenerated before wiring (§5.1).

## 4. Offline fixture harness — 36 tests, 6 tiers, all green

```
T1_ResolverFixtures           7   F1 canonical resolution · F2 moves with declared HOME
                                   · F3 absent==RUNNING · F4 divergence emitted (D-3 as a test)
                                   · F5 present/unparsable classified · F6 symlink→HALTED
                                   · F7 directory→HALTED
T2_PredicateFixtures          6   the REAL is_halted: absent · on-words · off-words
                                   · unparsable fails ON (never silently off)
                                   · classifier uses the real predicate when given it
                                   · mirror is LABELLED when the predicate is absent
T3_CoverageFixtures           3   uncovered + covered both reported · summary counts only true
                                   coverage · missing code → UNVERIFIED, never a guess
T4_SafetyCheckNegativeTests  11   one planted violation per rule, each must refuse
                                   · plus: the allowlisted exception must actually PASS
                                   · plus: an unparsable module is a violation, not a pass
T5_NonMutationCanary          5   arming a HALT path is refused · receipts-only writes allowed
                                   · no HALT file exists after a full run · guarded live-path
                                   files byte-identical across a run · receipts declare 0 mutations
T6_DeterminismAndShellGuard   4   two runs agree except timestamps · shell-rewritten path
                                   refused · literal POSIX path accepted · canon self-test green
```

`Ran 36 tests · OK · 0 failures · 0 errors`. Run:
`python _ops/halt_oracle_doctor/tests/test_doctor.py`

**The canary is the load-bearing test.** It hashes `ofn/node.py`,
`ofn/adapters/router.py`, `ofn/assistant_update.py`, `ofn/kernel/callbudget.py`,
`ofn/kernel/release_switch.py`, `ofn/budget/opslib.py`, `data/gates.json` before and
after a full doctor run and asserts byte-identity, and asserts no `HALT*` file exists
afterwards. A "read-only" tool that can arm a switch is worse than no tool; this
proves this one cannot.

## 5. Findings from building it (each one a real trap, all fixed)

### 5.1 Two kernel sites read halt without a resolved source — `UNVERIFIED`, lead

> **RESOLVED 2026-09-17 (same day) — see `WIRING-DECISION-NOTE.md` §1.** The source was
> traced: both functions **receive a parameter** and the kernel contract states it does
> not read the file (`start_permit.py:125`); neither has **any production caller or
> importer**; `stale_class` is imported only for its classifier, not for `admit_refresh`.
> Both are therefore **`TESTED_ONLY`**, **not oracle consumers**, and **out of OD-4
> scope**. The blocking condition is closed **negative** — nothing feeds them from a live
> path, so the PRE baseline stands. The doctor now discovers and reports both itself
> (verified by test), so a future caller would flip them to `WIRED` automatically.
See §3.2. **This is the one item that blocks a clean POST receipt.** It is a *read*
task, not a wiring task.

### 5.2 The safety check refused its own package three times — and it was right each time
1. R5 flagged the rule's own definition (a pattern-based rule must state its pattern) →
   resolved with **one documented file-level exemption**, not a weakened rule.
2. R2 rejected `from ofn.kernel import halt` and `from ofn.kernel.halt import is_halted`
   because only the module *path* `ofn.kernel.halt` was allowlisted →
   the check now resolves the **effective module per alias**, so `from X import Y` is
   judged as `X.Y`.
3. R5 flagged the **negative test** that plants a forbidden literal → the test now
   builds the string from parts, so the rule applies uniformly and no second exemption
   was needed. *(Bad fix avoided: exempting the test file.)*

### 5.3 Git-Bash silently rewrote a POSIX argument into a Windows path
`--declared-home /home/ari` reached native Python as `C:/Program Files/Git/home/ari`,
which produced a **plausible but wrong** canonical oracle path on the first run. The
doctor now refuses a `--declared-home` that is not an absolute POSIX path, and the
harness asserts that refusal. A silently wrong answer is the exact failure mode this
tool exists to find, so it must not emit one.

### 5.4 `ofn/helpers/brainport.py` carries a U+FEFF BOM
`ast.parse` on plain `utf-8` raised `SyntaxError: invalid non-printable character
U+FEFF`. The doctor now reads Python source as `utf-8-sig` and treats an unparsable
file as a **recorded unknown**, not a silent skip. *Second BOM artifact found in two
days — see `06-EVIDENCE/OBSIDIAN-SURFACES-AUDIT-2026-09-17.md` §3.1 for the first.*

### 5.5 `pathlib` on Windows mis-modelled the Linux path
`Path("/home/ari") / "ofn"` produced a drive-qualified path. Resolution is now pure
string joining with POSIX separators — modelling a Linux board path must not depend on
the host OS.

## 6. Exact wiring recommendation (owner order step 4 — NOT executed here)

**Recommendation: DO NOT WIRE YET. First close the one `UNVERIFIED` lead (§5.1), then
wire the three approved sites, then produce the POST receipt.**

Rationale: §5.1 shows two kernel decision points read halt on a value whose source this
pass could not resolve. If either is fed by a real file read on a live path, then the
PRE receipt understates current coverage, and a wiring change made against a stale
baseline could double-gate or mis-scope. The owner's order puts the doctor before the
wiring precisely so the baseline is trustworthy, so the baseline gets closed first.

### 6.1 The three edits (all approved; oracle = existing `opslib.master_halted()`)

| # | File | Change | Coverage transition |
|---|---|---|---|
| A | `ofn/node.py` `:3607` | `kill_switch_active=self.killed or _halt_oracle_active()` (+1 import, +4-line fail-closed helper) | `A-1` `DOC_ONLY → WIRED` |
| B-1 | `ofn/adapters/router.py` `ask()` | halt check at the model **admission point**, injected as `halt_oracle=opslib.master_halted` at `run.py:548` | `B-1` `DOC_ONLY → WIRED` |
| B-2 | `ofn/assistant_update.py` `main()` | halt check **at the direct call site**, before `RemoteBrain(...)` | `B-2` `DOC_ONLY → WIRED` |

**Unchanged, by requirement:** `release_switch.py` (its `kill_switch_active` check is
already first and unconditional — only the *input* changes), `consent`, `ledger`,
`callbudget.py`, budget thresholds, every flag, systemd, timers, HALT files.

### 6.2 The acceptance gate for wiring

1. §5.1's two sites resolved; PRE receipt **regenerated** if coverage differs.
2. Wiring applied to exactly those 3 sites; `git status` shows only those 3 files.
3. POST receipt produced with **the same command and the same declared HOME**.
4. POST must show: the same 3 consumers at `WIRED`, and
   `out_of_scope_consumers.any_label_changed == false`.
5. Tests T1–T9 from `CHANGE-PREP-PACKET.md` §3 green, including T2's exact rule string
   `release:kill-switch-active` and T4's `refused_code == "route:halt"` with **zero**
   `RemoteBrain.answer` calls.
6. Deployment is a separate Class B step requiring the independent witness.

## 7. Boundaries — attestation

| Boundary (owner card) | State |
|---|---|
| No change to code, HALT, budget, systemd, timer, or live path | **held** — `F:\ofn-node` HEAD `0da921b1b9eecdfc92346ebb38813055f39f1e2c`, unchanged; no `HALT*` file exists |
| No access to the live node | **held** — node state is `NOT_PERFORMED` in the receipt; the only file-state row is labelled *local checkout proxy* |
| No new human reviewer needed | **held** — self-certifying, Class A |
| No partial implementation | **held** — zero wiring code written |
| No write outside `receipts/` | **held** — `_guard_write()` refuses; negative-tested |
| No live ablation | **held** — nothing armed, and arming is refused by test |

## 8. Deliverables of this lane

| # | Owner asked | Artifact |
|---|---|---|
| 1 | doctor spec | `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` (+ as-built note) |
| 2 | offline result report | **this file** |
| 3 | coverage receipt JSON | `_ops/halt_oracle_doctor/receipts/PRE-coverage-<ts>.json` + `PRE-result-<ts>.json` + `mismatches-<ts>.jsonl` |
| 4 | exact wiring recommendation | §6 above (blocked on §5.1) |

## 9. What the doctor still cannot do — stated so nothing is over-read

1. **Half B (on-node) is NOT performed.** Which file each *running service* actually
   resolves, and its real state, needs on-node observation — not authorized.
   The receipt says so in the `node_observation` field.
2. **The file-state classifier mirrors documented policy**, labelled per row. It proves
   what the doctor does, not what `halt_flag_active` does at runtime. Proving that is
   what Half B is for.
3. **It measures coverage, never causality.** It shows whether the oracle is on a path;
   it cannot show that a halted run would have been stopped.
4. **Two sites remain `UNVERIFIED`** (§5.1) and one has no production constructor
   (`run_gate.py:35`).
