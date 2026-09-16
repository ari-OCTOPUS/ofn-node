---
type: prompt
status: draft
tags: [octopus, megaprompt, probe-harness, pre-registration, safety-map]
updated: 2026-09-16
project: "[[OCTOPUS]]"
---

# MP-IMPLEMENT — EMERGENCE-SAFE-SURGERY v1

`MISSION-ID: OCTOPUS-EMERGENCE-SAFE-SURGERY-IMPLEMENT-20260916`
`GOV_VERSION=V8 · LADDER=L2 · mode: EXECUTE (additive, offline, reversible)`
`production_authorized=false · owner_vote_required=false (GOV-FREEDOM-V2 §2: sandbox/experiment)`

> **Read this whole file before doing anything.** Preparing or reading this document
> is not execution and not authorization. Execute the work packages in order. Do not
> reorder them, do not skip OP-2, and do not begin OP-6 before OP-3 is committed.

---

## 0. Mission in one paragraph

Build the smallest offline instrument that can tell a **wired** control from a
**decorative** one, and use it to test one hypothesis honestly. The prior
experiment's headline (97/100 vs 0/100) does not survive inspection because the
answer was hardcoded, the hidden state was readable, and the environment never
varied across seeds. Your instrument must make those three defects *impossible to
repeat silently*. You will add one directory. You will edit nothing that already
exists. If the hypothesis fails, that is a **successful outcome** and you report it
as one.

**Deliverable:** `F:\backup\_ops\probe_harness_v0\` + a lane report + a receipt set.
**Not a deliverable:** any change to `ofn/**`, any live-node contact, any
performance claim.

---

## 1. Entry conditions — the three-level absence scan (mandatory)

Before writing a line, establish what already exists. Run each and record output:

1. `ls F:\backup\_ops\probe_harness_v0` → must not exist. If it exists, **STOP** and
   report `LANE_ALREADY_OCCUPIED`; do not merge into someone else's work.
2. Search for prior art you are required to reuse rather than rebuild:
   - `F:\ofn-node\octopus_observation\` — stdlib-only fixture pipeline
     (`fixture_run.py`: fixture → producers → scorer → verifier → canonical receipt
     with `receipt_sha256`). **This is the designated reuse target** for receipt
     shape and canonicalization style. Read all of it before designing.
   - `F:\ofn-node\ofn\adapters\fake_executor.py`, `ofn/adapters/sender_dryrun.py` —
     patterns for honest fakes.
   - `F:\backup\_ops\coding_sandbox\` — **read it, do not use it** (see §4 rule R-6).
   - `F:\backup\09-LANES\QD-LAB-GENERALIZATION-20260908\package\octopus_qd_lab\` —
     prior art for preregistered offline batteries with receipts.
3. Declare your lane and write it in the lane report header before any other work:
   `GOV_VERSION=V8 · LADDER=L2`.

**Reuse rule:** if `octopus_observation` can give you a piece, use it and make the
diff smaller. The instruction is to *shrink*, never to build a framework.

---

## 2. OP-1 — Read the real architecture (no opinions yet)

Read, and record in your report what you actually saw:

- `F:\ofn-node\ofn\kernel\gates.py` — `admit()` and its "only path" claim.
- `F:\ofn-node\ofn\node.py:2254` `Node.propose`, and `:3036` `Node._gate_enqueue`.
- `F:\ofn-node\ofn\adapters\ledger.py` — `canonical()`, `event_hash()`, `verify()`.
- `F:\ofn-node\ofn\kernel\halt.py`, `ofn/adapters/halt_flag.py`, `ofn/adapters/run_gate.py`, `ofn/budget/opslib.py`.
- `F:\ofn-node\octopus_observation\fixture_run.py` (whole file).
- `F:\backup\plans\MEGAPLAN-EMERGENCE-SAFE-SURGERY-v1.md` — the plan you are executing.

---

## 3. OP-2 — Adversarially verify the megaplan's claims (DO NOT SKIP)

The planning agent asserted structural facts. **Your job is to try to falsify them.**
A claim you confirm by an independent command is worth ten you copy. For each row,
run your own command and record: confirmed / refuted / could not check.

| # | Claim to test | Suggested check |
|---|---|---|
| C-1 | `Node.propose` has zero production callers | `grep -rn "\.propose(" --include=*.py F:/ofn-node \| grep -v tests` |
| C-2 | `admit()` is reachable only via `propose` / `owner_decide` | `grep -rn "admit(" --include=*.py F:/ofn-node/ofn` |
| C-3 | `RunGate(` is constructed only in tests | `grep -rn "RunGate(" --include=*.py F:/ofn-node` |
| C-4 | `_gate_enqueue`'s only check is `self.killed` | read the function body |
| C-5 | Kill-switch path fragmentation; `F:\ofn-node\HALT` absent | `ls`, plus grep for `HALT-ALL`, `<root>/HALT`, `_halt_path` |
| C-6 | Two different "canonical" rules (compact vs default separators) | compare `ledger.canonical()` with `fixture_run.py`'s hashing line |
| C-7 | Deceptive-grid env is identical across seeds | `make_S0_reference` ignores seed; grep `self.rng` in `env_factory.py` |
| C-8 | Deceptive-grid candidate hardcodes the answer and reads hidden state | `agents.py:32,356`, and `self.env.secret_doors` |

**If you refute any claim, that is a finding — report it and adjust the plan's
inputs; do not silently proceed.** Write each result into the lane report with the
exact command you ran.

---

## 4. Iron rules (violation = STOP and report)

- **R-1 — Additive only.** Create `F:\backup\_ops\probe_harness_v0\` and its lane
  report. **Edit no existing file.** `git status` at the end must show additions
  only. If you believe an existing file must change, STOP and raise a decision card.
- **R-2 — No live path.** Never import `ofn.kernel.*`, `ofn.adapters.*`,
  `ofn.agents.*`, `ofn.node`, `ofn.run`, `ofn.budget.*`. The safety check (§6.3)
  enforces this and must fail closed.
- **R-3 — No egress, ever.** No network, no socket, no subprocess, no ssh, no
  Telegram, no SMTP/IMAP, no paid model API, no broker. No new dependency — stdlib
  only (plus `pytest` already present for tests).
- **R-4 — No live nodes.** Do not touch `.138`, `.180`, `.182`, the ESP32, or any
  device. Do not restart a service or timer.
- **R-5 — No effects.** No send, call, payment, order, invoice, or financial read.
  Do not touch `BUDGET.json`, `data/gates.json`, `HALT*`, or any wire flag — in
  either direction.
- **R-6 — Do not rely on the existing sandbox.** `LAB-DOCTOR-CONTRACT.yaml` records
  all 10 hard-sandbox requirements as `UNKNOWN_NOT_VERIFIED` with verdict
  `NOT_A_VERIFIED_HARD_SANDBOX`. **A harness with no escape surface is safer than
  one guarded by an unverified jail.** Build the former; do not wrap the latter.
- **R-7 — No secrets.** Never print, copy, or commit a secret. Key names only.
- **R-8 — No receipt rewriting.** Receipts are append-only. Never edit a receipt
  after it is written; write a new one.
- **R-9 — Do not inflate.** No capability claim above what the run shows. A fixture
  result is not a performance claim. Capability grade ceiling for v0 is **E3** until
  a scaffold-variation measurement exists (`AGENTS.md` §2).
- **R-10 — `retries = 0`.** One run per preregistered condition. No re-running to
  get a better number. If a run crashes, that is a result; fix nothing and report.

---

## 5. OP-3 — Pre-registration BEFORE any arm executes

Write `_ops/probe_harness_v0/PREREG.json`, then commit it **before** running
anything. It must contain, frozen:

- `prereg_id`, `created_at_utc`, `author`
- `hypothesis` (H1 verbatim from the megaplan §5), `null_hypothesis`, `falsifier`
- `arms`: A (baseline), B (candidate), C (control) — with the exact module/path of each
- `scenarios`: S0 reference, **S1 held-out (the claim is made here)**
- `seeds`: the explicit list
- `metric`: success rate **with Wilson 95% interval** + median TTD among successes
- `pass_bar`: candidate Wilson-95% lower bound > control rate on S1
- `retries`: `0`
- `void_conditions`: what invalidates the run (see L2 below)
- `prereg_sha256`

Then, and only then, write the code. `git log` must show the PREREG commit before
the first receipt file — that ordering is the whole point.

---

## 6. OP-4 — Build the package (the one small change)

```
F:\backup\_ops\probe_harness_v0\
├── __init__.py
├── canon.py            # one canonical JSON + sha256 rule, pinned by a frozen vector
├── receipt.py          # receipt schema; mode=SIMULATED; superiority_claim=null
├── scenarios.py        # structure GENERATED FROM SEED (never constant)
├── arms.py             # A baseline / B candidate (loaded by path) / C control
├── harness.py          # orchestrate arms × seeds; emit receipts; write only here
├── safety_check.py     # §6.3 fail-closed self-certification
├── PREREG.json         # OP-3
├── receipts/           # the ONLY writable directory
└── tests/
    └── test_probe_harness_v0.py
```

### 6.1 Invariants you must implement and test

| ID | Invariant |
|---|---|
| **L1** | Candidate cannot reach hidden state: observation interface exposes observations only; candidate exposes its declared interface only. |
| **L2** | **Seed varies the environment.** Two seeds ⇒ two different structure digests, asserted as a test. If this ever fails, the run is **VOID**. |
| **L3** | PREREG committed before first receipt (verify by `git log`). |
| **L4** | S1 held-out results reported separately; a claim on S0 alone is not a result. |
| **L5** | No secret pattern or answer key is a literal anywhere in a candidate or in `scenarios.py`. |
| **L6** | Two modes (`normal`, `drill`); divergence ⇒ `EVAL_AWARENESS_SUSPECTED` reported as a result, never averaged. |
| **L7** | One canonical rule, pinned by a literal expected digest. Must detect the compact-vs-default separator divergence (D-6). |
| **L8** | No escape surface; enforced by §6.3 and negative-tested. |

### 6.2 Arm C is mandatory

The candidate-vs-baseline comparison alone is the claim that was already falsified
once. **A run whose output lacks arm C is incomplete and must be reported as
incomplete.** If C ≥ B, say so first, in the first sentence of your results.

### 6.3 `safety_check.py` — fail closed, with a named reason

Runs before any arm executes, and as a test. It must refuse if any file in the
package does any of:

1. imports `socket`, `subprocess`, `urllib`, `http`, `ssl`, `smtplib`, `imaplib`,
   `requests`, `paramiko`, `ftplib`, or multiprocessing;
2. imports any protected live surface (`ofn.kernel.*`, `ofn.adapters.*`,
   `ofn.agents.*`, `ofn.node`, `ofn.run`, `ofn.budget.*`);
3. calls `eval`, `exec`, `compile`, `__import__`, `os.system`, `os.popen`;
4. opens a write handle outside `receipts/`;
5. contains a secret-shaped literal, or the name of a wire / halt / gate flag;
6. reads a process environment variable (v0 is pure — configuration is passed in).

It must also emit, for every control it inspects, one of exactly four verdicts:
`WIRED` / `TESTED_ONLY` / `DOC_ONLY` / `UNVERIFIED`. **A boolean safe/unsafe output
is a failed implementation** — see megaplan §2.

---

## 7. OP-5 — Self-certification (negative tests, not just green tests)

`AGENTS.md` §2: nothing rises above E3 without scaffold variation. A test that only
passes on the designed input proves nothing. Implement, at minimum:

1. **Canonicalization parity** — a frozen literal digest (L7).
2. **Seed-variation** — two seeds differ (L2). This is the check that would have
   caught the original experiment's central defect.
3. **Hidden-state unreachability** — a test that plants an attempt to read the
   answer key and asserts the harness refuses/never exposes it (L1).
4. **Safety-check negative test** — plant each of the six violations in a temp
   module and assert `FailClosedError`, one case per rule. Six red cases, not one.
5. **PREREG ordering** — assert the prereg file exists and its hash matches before
   results are written (L3).
6. **Determinism** — same tree + same seeds ⇒ identical `receipt_sha256`.

Report the **explicit pass/fail count**. "No errors" is not a green result.

---

## 8. OP-6 — Execute (retries = 0)

- Run arms A, B, C × preregistered seeds × S0 and S1, in both modes.
- Write one receipt per condition into `receipts/`. Nothing outside `receipts/` is
  written. Nothing leaves the machine.
- Do **not** tune anything after seeing a result. If a threshold or denominator
  needs changing, the run is void — write a new PREREG and start over, and say so.
- On crash: record it, stop, report. Do not "fix and retry".

---

## 9. OP-7 — Report honestly

In this exact order:

1. **The falsifier outcome first.** Did H1 survive or fail? If arm C ≥ B, that is
   sentence one.
2. Numbers **with intervals**. Never a bare percentage.
3. Arm C's result. Always.
4. The four-state verdict table from `safety_check.py`.
5. Confirmed / refuted results of OP-2's claim table, with the commands you ran.
6. Scope limits, restated from megaplan §5 — modules not organism, simulated
   fixtures, no live causality, no organism-level eval-awareness.
7. `NOT FOUND` items with the searches you ran. Never fill a gap with a guess.

---

## 10. OP-8 — Exit (mandatory)

1. Lane report at `F:\backup\09-LANES\<LANE>-20260916\LANE-REPORT.md`, header line
   `GOV_VERSION=V8 · LADDER=L2`, sections: what was done / what remains / what
   failed / evidence paths / rollback. No report, no completion (`AGENTS.md` §9).
2. Run both vault validators and report **explicit pass/fail counts**:
   `F:\backup\04 - Architect System\scripts\validate_frontmatter.py` and
   `find_broken_links.py`. Do not modify a validator to make it green.
3. `git status` — confirm additions only.
4. Commit with `agent-checkpoint: <summary>` if more than ~5 files changed.

---

## 11. Acceptance criteria for this prompt

All ten, each with an artifact:

1. `probe_harness_v0/` exists; `git status` shows **additions only**.
2. OP-2 claim table complete, with commands and confirmed/refuted per row.
3. `PREREG.json` committed **before** the first receipt (proven by `git log`).
4. Safety check passes and **fails closed** on all six planted violations.
5. Canonicalization parity test green against a frozen digest.
6. Two seeds produce two different structure digests, asserted.
7. S1 held-out results exist and are reported separately from S0.
8. Arm C is present in the output.
9. Every receipt carries `mode: SIMULATED` and `superiority_claim: null`.
10. Lane report + validator counts published; rollback documented.

---

## 12. What "done" does not mean

Finishing this prompt does **not** establish that the organism has emergent
capability, that any module is superior to exploration, or that the live path is
safe. It establishes exactly one thing: there is now an instrument that can
distinguish a wired control from a decorative one, and it has been run once, under
pre-registration, with its result reported whether or not it was the hoped-for one.

---

## 13. Owner prompt (copy-paste to the executing agent)

> You are the coding agent for lane `EMERGENCE-SAFE-SURGERY-20260916`.
> Read `F:\backup\plans\MP-IMPLEMENT-EMERGENCE-SAFE-SURGERY-v1.md` in full and
> execute OP-0 through OP-8 in order. Do not skip OP-2 (adversarially verify the
> planning agent's claims, including the two structural ones about `Node.propose`
> and `RunGate`). Add exactly one directory — `F:\backup\_ops\probe_harness_v0\` —
> and edit no existing file. Register your seed/arms/thresholds in `PREREG.json`
> and commit it before running anything. `retries = 0`. If arm C (novelty control)
> beats the candidate, say that in your first sentence and stop claiming anything.
> Never contact a live node, never import the live `ofn` package, never touch a flag,
> gate, budget, or halt file. If the work cannot proceed without breaking one of
> those rules, write `BLOCKED_BY_SAFETY` and stop.
