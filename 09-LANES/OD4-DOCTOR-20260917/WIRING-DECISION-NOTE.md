---
type: proposal
status: draft
tags: [octopus, od-4, halt-oracle, wiring, pre-post, decision-note, no-implementation]
updated: 2026-09-17
project: "[[OCTOPUS]]"
---

# WIRING DECISION NOTE — OD-4 (doctor-backed, PRE/POST frozen)

`GOV_VERSION=V8 · LADDER=L2 · mode: DECISION NOTE ONLY — NOTHING IMPLEMENTED`
`authority: owner card OD-4 (2026-09-17), stage boundaries: no change to ofn/**, HALT, budget, flags, systemd, timers, or any live node`
`baseline: PRE receipt committed below · POST not produced · wiring NOT started`

> This note decides **which files would change** and **what the PRE/POST protocol is**.
> It changes nothing. No `ofn` file was touched; no test ran on a production path; no
> external action or side effect was produced.

## 1. Deliverable 2 — the two additional halt sites are RESOLVED (not left UNVERIFIED)

The owner's stop condition was *"if the new paths cannot be fully resolved from available
evidence, leave them as `UNVERIFIED` and do not proceed."* **They are fully resolved, so
the condition does not fire — and the resolution is that they do not belong in the
wiring at all.**

| | `P-1` `ofn/kernel/start_permit.py:136` `decide_start` | `P-2` `ofn/kernel/stale_class.py:335` `admit_refresh` |
|---|---|---|
| Reads the halt **file**? | **No** — receives `halt_raw` | **No** — receives `halt` (bool or raw flag) |
| The kernel's own statement | `start_permit.py:125`: *"`halt_raw` is the flag file contents (or None if absent). **The kernel does not read the file.**"* | `stale_class.py:313-322`: `halt` is a caller-supplied bool or raw flag |
| Production callers (repo-wide, tests excluded) | **0** | **0** |
| Imported by any production module? | **No** — only a docstring mention in `arm_isolate.py:11` ("owned by an open change") | Imported by `fresh_pin.py:39`, but **only for `FRESH/KINDS/STALE/UNKNOWN/_fold/_is_sealed`** — not for `admit_refresh` |
| Exported from `ofn.kernel`? | No | No |
| Exercises | 4 test files only | 4 test files only |
| **Coverage state** | **`TESTED_ONLY`** | **`TESTED_ONLY`** |
| Produces an effect? | **No — kernel decision primitive, no egress** | **No** |
| **In OD-4 scope?** | **No** | **No** |

**Why they were flagged in the first place, and why that flag is now closed.** The site
scan saw two more `is_halted` call sites and could not see where their input came from.
Tracing it shows the input is a **parameter** — these are kernel-pure primitives awaiting
a caller. The kernel supplies the *decision*; whoever owns the scheduler supplies the
*file contents*. That is a deliberate layering, and it means **they are not consumers of
the canonical oracle in the coverage sense: they do not read it.**

**Notable (informational, no action):** three kernel-level start-gate seams now have no
production caller — `RunGate` (`adapters/run_gate.py`), `decide_start`, and
`admit_refresh`. All three read as "the scheduler should call this". Consistent with an
out-of-repo consumer, which this lane cannot inspect. **Recorded as a bounded unknown at
the caller level; the in-repo resolution above is complete.**

### 1.1 Consequence for the decisions that were waiting on this
The previously-blocking item ("if a live path feeds them a real file read, the PRE
receipt must be regenerated") is **closed negative**: no live path feeds them anything,
because no production code calls them. The PRE baseline therefore stands.

## 2. Deliverable 3 + 4 — consumer map updated, PRE receipt refreshed

The doctor now **discovers** these two sites itself (not hardcoded) and reports them
**outside** the approved three-consumer scope, so OD-4's invariant stays exact:

```
A-1  ofn/node.py:publish_to_telegram      path=WIRED  coverage=DOC_ONLY   kill_switch_active=self.killed
B-1  ofn/adapters/router.py:ask           path=WIRED  coverage=DOC_ONLY   gates on path _charge()@164
B-2  ofn/assistant_update.py:main         path=WIRED  coverage=DOC_ONLY   first brain call at line 28
P-1  ofn/kernel/start_permit.py:decide_start   coverage=TESTED_ONLY  reads_file=False  callers=0  in_od4_scope=False
P-2  ofn/kernel/stale_class.py:admit_refresh   coverage=TESTED_ONLY  reads_file=False  callers=0  in_od4_scope=False
```

**The approved 3-consumer invariant did not move:** `consumers_total = 3`,
`covered_by_canonical_oracle = 0`, `mismatch_count = 4` (unchanged — the primitives add
no `coverage_gap` rows because they are not egress consumers). Asserted by test.

| Refreshed PRE artifact | sha256 (16) | bytes |
|---|---|---|
| `receipts\PRE-coverage-20260916T225200Z.json` | `36a446f2c41229a5` | 4212 |
| `receipts\PRE-result-20260916T225200Z.json` | `fa8772cce5cbc91a` | 10316 |
| `receipts\mismatches-20260916T225200Z.jsonl` | `4cd0b60f3b9e696b` | 2149 |

### 2.1 ⚠ A hole in my own FIRST receipt, found and fixed

The first PRE pinned `git rev-parse HEAD` as its runtime identity **while reading files
from the working tree**. Re-checking showed that of the **11 distinct files** in the
halt-site scan, **4 were not in a clean tracked state**:

| File | State |
|---|---|
| `ofn/agents/release_pipeline.py` | tracked but **modified** — and itself one of the five oracle consumers |
| `ofn/agents/followup_worker.py` | **never tracked** — also one of the five oracle consumers |
| `ofn/kernel/stale_class.py` | **never tracked** — this is `P-2` |
| `ops/ign1_telegram_ignite.py` | **never tracked** — the literal `<root>/HALT` site |

So the commit did not describe four of the files the receipt was about, and a POST
compared against it would not have been reproducible from the commit alone.

**Fix — a content-level baseline** (`_ops/halt_oracle_doctor/baseline.py`): the receipt
now records a **sha256 per analysed file (15 files)** and states the POST rule as
*"every digest identical except the files the change intended to touch."* This is
strictly more precise than HEAD pinning and it **detects a concurrent lane's edit
automatically** (`verdict: BASELINE_MOVED`).

`tracked` status is deliberately **not** claimed: determining it requires running git,
which the safety rules forbid (no subprocess, and git carries hooks/aliases). The
manifest is content-based by design, which is the sound comparison anyway.

*Context worth recording: `ofn/` currently has **65 dirty entries** from parallel lanes
(including `release_pipeline.py`). The live runtime tree is not fully tracked in git, so
"the commit" has never been a complete description of what runs.*

### 2.2 Fresh PRE artifacts (superseding §2's earlier hashes)

| Refreshed PRE artifact | sha256 (16) | bytes |
|---|---|---|
| `receipts\PRE-coverage-20260916T225200Z.json` | `36a446f2c41229a5` | 4212 |
| `receipts\PRE-result-20260916T225200Z.json` | `fa8772cce5cbc91a` | 10316 |
| `receipts\mismatches-20260916T225200Z.jsonl` | `4cd0b60f3b9e696b` | 2149 |

PRE pins `ofn-node` at **`0da921b1b9eecdfc92346ebb38813055f39f1e2c`**.
Harness: **51 tests / 8 tiers, all green** (added `T7_KernelPrimitives`, 8 tests —
including a positive control that a caller flips the label to `WIRED`, proving the scan
measures rather than reports a constant).

## 3. Deliverable 5 — PRE/POST protocol decision (frozen)

The owner required a clear PRE/POST decision **before** any wiring. This is that decision.

### 3.1 The protocol, frozen

| Element | Value | Why frozen |
|---|---|---|
| PRE phase | **the receipt above**, committed before any change | it is the baseline the POST is compared against |
| POST command | same command, same `--declared-home /home/ari`, same `--documented-oracle`, `--phase POST` | a different HOME produces a different oracle path and an incomparable receipt |
| Success criterion | exactly the 3 consumers move `DOC_ONLY → WIRED`; `out_of_scope_consumers.any_label_changed == false` | this is the scope lock — anything else is scope creep |
| Pinning | **content manifest**, not the commit: every one of the 15 recorded digests must be identical except the 4 intended files | HEAD alone proved insufficient — 4 of 11 scanned files were modified or untracked (§2.1) |
| Comparison verdict | `BASELINE_MOVED` if any file outside the intended set changed → re-run PRE and draw no conclusion | this is the concurrent-lane detector |

```bash
# PRE (already run and committed)
MSYS_NO_PATHCONV=1 python -m _ops.halt_oracle_doctor.doctor --repo F:/ofn-node \
  --declared-home /home/ari --documented-oracle F:/ofn-node/HALT --phase PRE

# POST (only after the edits; same arguments, phase POST)
MSYS_NO_PATHCONV=1 python -m _ops.halt_oracle_doctor.doctor --repo F:/ofn-node \
  --declared-home /home/ari --documented-oracle F:/ofn-node/HALT --phase POST
```

### 3.2 What INVALIDATES the PRE (any one ⇒ re-run PRE before wiring)

1. `ofn-node` HEAD moves off `0da921b1…` (it demonstrably moves — parallel lanes commit).
2. Any of the 3 consumer functions changes, or a **new** consumer appears.
3. `P-1`/`P-2` gain a production caller (the doctor would flip them to `WIRED`).
4. `opslib.py`'s `HALT_FLAG` expression changes (the canonical oracle moves).
5. **Any file outside the 4 intended ones changes content** (the manifest catches this mechanically — `BASELINE_MOVED`), noting that 65 files under `ofn/` are currently dirty from parallel lanes
6. The documented oracle path in `AGENTS.md` is corrected (the `path_divergence` mismatch
   disappears and one of the 4 mismatches is resolved rather than wired).

## 4. Exactly which files would change

**Four files. No new file. No new module, gate class, flag, timer, or daemon.**

| # | File | Change | Consumer moved |
|---|---|---|---|
| 1 | `ofn/node.py` | `+:3607` `kill_switch_active=self.killed or _halt_oracle_active()`; `+1` import; `+4`-line fail-closed helper | `A-1` → `WIRED` |
| 2 | `ofn/adapters/router.py` | `ask()`: halt admission check before the rung loop; `+1` constructor param + attribute | `B-1` → `WIRED` |
| 3 | `ofn/run.py` | `:548` pass `halt_oracle=opslib.master_halted` to `ModelRouter(...)` | (`B-1` wiring) |
| 4 | `ofn/assistant_update.py` | `main()`: halt check before `RemoteBrain(...)` | `B-2` → `WIRED` |

Oracle for all four: the **existing** `ofn/budget/opslib.py:28 master_halted()` — never a
second HALT path literal (that would recreate D-3).

**Must remain byte-identical** (`release_switch.py` included explicitly, because its
`kill_switch_active` check is already first and unconditional — only the *input* changes):
`ofn/kernel/release_switch.py` · `ofn/kernel/callbudget.py` · `ofn/kernel/quota.py` ·
`ofn/adapters/ledger.py` · `ofn/kernel/hash_chain.py` · `ofn/agents/consent_gate.py` ·
`ofn/agents/consent_store.py` · `data/gates.json` · `BUDGET.json` ·
`tools/install_systemd.sh` · every `deploy/systemd/*` unit · every `HALT*` path · every
`OCTOPUS_WIRE_*` / `OFN_WIRE_*` occurrence.

**Explicitly NOT in the change set:** `P-1` and `P-2`. Wiring halt into a primitive that
has no caller and reads no file would add a gate nothing reaches — a `DECLARED ≠ WIRED`
control, which is the exact failure this whole lane series documents.

## 5. Status — what this note does NOT do

| Item | State |
|---|---|
| Wiring implemented | **NO** — zero lines changed in `ofn/**` |
| POST receipt produced | **NO** — nothing to measure yet |
| Test run on a production path | **NO** |
| External action / side effect | **NONE** |
| HALT / budget / flags / systemd / timers / node | **untouched** |
| Doctor as pre-wiring truth source | **kept** — PRE committed, doctored-into the repo, harness green |

**Gate for the wiring lane:** the owner's "clear decision about PRE/POST" is now on
record (§3). Remaining pre-conditions before step 4: none technical, beyond re-running PRE
if §3.2 fires. Deployment stays a separate Class B step requiring the independent witness.
