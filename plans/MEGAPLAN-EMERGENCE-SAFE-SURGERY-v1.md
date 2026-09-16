---
type: proposal
status: draft
tags: [octopus, emergence, safety-map, probe-harness, causal, pre-registration]
updated: 2026-09-16
project: "[[OCTOPUS]]"
---

# MEGAPLAN — EMERGENCE-SAFE-SURGERY v1

`MISSION-ID: OCTOPUS-EMERGENCE-SAFE-SURGERY-20260916`
`GOV_VERSION=V8 · LADDER=L2 · mode: DOCS-ONLY (no code touched) · production_authorized=false`
`author: planning lane · date: 2026-09-16 · status: DRAFT-FOR-OWNER-ACK`

> Preparing this document is not execution and not authorization. Nothing in this
> file has been run. The single change described in §6 has **not** been implemented.

---

## 0. Why this plan exists, and what it refuses to do

The instruction was: read the real directory and the real architecture first, then
produce one megaplan and one small execution prompt — do not touch the organism
with prior assumptions or heavy architecture.

So this plan refuses four things up front:

| Refused | Why |
|---|---|
| Building WTA / PredictorBrain / new memory / Event Spine | No evidence yet that any of them is the binding constraint. Adding surface before measuring is how the vault grew 63 locks and still has unknowns. |
| Any edit to a live module (`ofn/**`, executor, gates, ledger, flags, autonomy) | The one change is additive and lives outside the live repo. |
| Running anything against the live path to "see what happens" | Live ablation of a safety surface is not an experiment, it is an incident. |
| Re-deriving by experiment what reading already proves | See §2. The headline finding is obtainable statically; dressing it up as a simulation would be theatre. |

The plan's first real job is therefore **not** "measure how intelligent the organism
is". It is: *build an instrument that can tell a wired control from a decorative one.*
Everything below follows from that.

---

## 1. Reality map — the decision path as it actually is

All paths are under `F:\ofn-node` (live runtime). Everything in this section was read
directly from disk in this session; nothing is quoted from notes or chat.

### 1.1 The claimed path

`ofn/kernel/gates.py` opens with a hard claim:

> "`admit()` is the only path from 'a leg wants to do X' to 'X is permitted'.
> If a second path ever appears, the guarantees in this package stop holding —
> not gradually, but immediately, because every other module assumes this
> function ran."

The check order inside `admit()` is deliberate: kill switch → quota → risk →
human sovereignty. `executable()` (`gates.py:107`) is the second half and answers
"may this run *now*", because approval state decays.

### 1.2 The path that actually runs

| Step | Real implementation | Wiring status |
|---|---|---|
| (a) input | `ofn/adapters/http_api.py:387` `ApiApp.handle()`; webhooks `ofn/node.py:3058`; Telegram inbound `ofn/agents/glass_runner.py`; IMAP `ofn/agents/imap_listener.py:281` | **WIRED** (served by `ofn.service`, `run.py:609`) |
| (b) retrieval | `ofn/adapters/facts.py:199` `FactStore.evidence`; `ofn/adapters/ledger.py:136` `Ledger.read` | **WIRED** |
| (c) proposal | `ofn/worker.py:189` `Worker.step` → `ofn/adapters/router.py:130` `ModelRouter.ask` | **WIRED** |
| (c′) proposal (kernel flavour) | `ofn/node.py:2254` `Node.propose` | **NOT CALLED in production** — see below |
| (d) gate | `ofn/kernel/gates.py:29` `admit()` | **reachable only from `Node.propose`** (`node.py:2263`) and `owner_decide` (`node.py:3361`) |
| (d′) gate actually on the outbound path | `ofn/node.py:3036` `Node._gate_enqueue` | **WIRED** — but its only check is `self.killed` |
| (e) receipt | `ofn/adapters/ledger.py` SQLite, hash-chained | **WIRED** |
| (f) outcome | `ofn/worker.py:273` `THINK_DONE`; `node.py:3639` `TELEGRAM_PUBLISHED`; `ofn/agents/lead_effect_gate.py` `unknown_outcomes()` | **WIRED / PARTIAL** |

### 1.3 The decisive gap (statically provable)

```
$ grep -rn "\.propose(" --include=*.py . | grep -v "^./tests/"
(none)

$ grep -rn "admit(" --include=*.py ofn/
ofn/node.py:2263:        d = admit(action, pack, self.quota,
```

`Node.propose` — the only production-shaped caller of `admit()` — is called from
**tests only** (`tests/test_node.py:201,212,218`, `tests/test_shell_contract.py:415`).
The live outbound path instead uses `_gate_enqueue`, whose own docstring says:

> "This does NOT re-run admit/risk/quota — these paths are all RED and already
> require human approval downstream. The gate here is specifically the kill
> switch, which is the one thing a direct enqueue was missing."

That is a defensible engineering decision *and* it falsifies the module-level claim
that there is exactly one path. Both things are true. A future agent reading
`gates.py` alone would conclude policy covers every action. It does not.

**Method note that matters for the whole plan:** absence of a call site is
*provable*. Correlation is not. Static structural absence is the only causal claim
available without intervention, which is exactly why this finding does not need an
experiment — and why an experiment that pretended to discover it would be false.

---

## 2. The dominant failure class: DECLARED ≠ WIRED

Five independent instances, all verified this session. They are different
subsystems, same shape.

| # | Surface | Declares | Reality | Evidence |
|---|---|---|---|---|
| 1 | Policy choke point | "the only path … a second path would break the guarantees" | a second path exists and says so in its own docstring | `kernel/gates.py:3-6` vs `node.py:3036-3054` |
| 2 | Scheduler kill switch | `RunGate` reads the flag *before* run creation; in-flight → HELD; restart never resends | `RunGate(` is constructed **only in tests** (`tests/test_run_gate.py:50`, `test_chaos_owner_absent.py:148`, `test_halt_starts_not_inflight.py:41`, `test_reject_log.py:116`) | grep | 
| 3 | Halt latch | a second witness so flag/latch disagreement is visible | file self-declares "Not wired into `halt_flag` or `run_gate`" | `kernel/halt_latch.py:16` |
| 4 | Wire flags | flags gate outbound wiring | `tools/install_systemd.sh:19` bakes `Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1` into the units; and `OFN_WIRE_OUTBOUND` was deleted 2026-09-03 as *decorative* | installer + `config.py:31` |
| 5 | Deceptive-grid capability claim | the hypothesis engine beat baseline 97 vs 0 | the answer was hardcoded into the candidate and the environment never varied | §3.2 |

**Consequence for the owner:** the risk is not only "the agent does something
forbidden". It is that a control *looks* present — documented, unit-tested, in the
architecture bible — while the live path does not consult it. Protection that reads
as present but does not bite is worse than an absent control, because it suppresses
the question.

**Consequence for the instrument:** the probe harness must output, for every
control it touches, one of exactly four verdicts — `WIRED`, `TESTED_ONLY`,
`DOC_ONLY`, `UNVERIFIED`. A boolean "safe/unsafe" would reproduce the disease.

---

## 3. The prior experiment, read honestly

### 3.1 What is solid

`F:\backup\_ops\hypothesis_engine\experiments\results.csv` — 600 rows, git-tracked
(commit `1d4f381`). Recomputed in this session from the raw CSV:

| Arm | Environment | Discovered | Median TTD among successes |
|---|---|---|---|
| `A_prior` | deceptive | **0/100** | — (never succeeded) |
| `B_hyp` | deceptive | **97/100** | 1769.0 |
| `C_novel` | deceptive | **100/100** | **1529.5** |
| `A_prior` | benign | 100/100 | 309.0 |
| `B_hyp` | benign | 100/100 | 393.0 |
| `C_novel` | benign | 100/100 | 1295.5 |

The user's stated premise is exactly right, and the project's own honest caveat
already says so: `architecture/capabilities-registry.yaml:98` — *"Not superior to
novelty search … 97% vs 0% …"*. The engine was retired 2026-08-16
(`experiments/STATUS.md`), canonical live: none.

### 3.2 Why the win does not survive inspection

Four code-level confounds, each read directly:

1. **The answer is handed to the candidate.** `experiments/agents.py:32`
   `SECRET_PATTERN = [(0,1),(0,1),(-1,0)] * 3  # (2E,1N)×3` is byte-identical to the
   environment's `DEFAULT_SECRET_PATTERN` (`env_factory.py:22`), and
   `agents.py:356-359` injects it as B's own hypothesis. The only uncertain number
   is `p_e = 0.2`; the answer itself is a constant.
2. **The candidate reads the hidden state directly.** `agents.py:322,384,405,424`
   iterate `self.env.secret_doors` — the environment's private answer key — to
   "detect" doors. The `HypothesisBrain` never sees the environment; it scores a
   scripted sweep.
3. **The environment is identical for all 100 seeds.** `make_S0_reference(seed)`
   builds `_default_config()` and ignores `seed` for layout
   (`env_factory.py:290-293`); `self.rng` (line 111) is used only for noise and
   action-failure rates (lines 178-208), never for walls, doors, or optima. The
   "100 runs" are 100 noise-replicas of **one** maze. `n=100` is therefore not
   n=100.
4. **The doors were placed to be found by the sweep** — the results document admits
   it: *"درها با sweep سیستماتیک طراحی‌شدهٔ ما هم‌راستا هستند"*.

**The correct current statement** (already close to the project's own): the engine
may rescue a particular class of deceptive environment from blind exploitation, but
superiority over plain exploration is **not established** — and the control won.
The generating code for the honest version exists (`make_S1_unseen`,
`env_factory.py:296`) and **has never been run**: no `benchmark_results/`, no
`summary.json`, no JSONL anywhere on disk.

---

## 4. Damage points — where execution can exceed the sandbox

"The sandbox" here means the set of controls that are supposed to bound an action.
A damage point is a place where the bound is thinner than it reads.

| ID | Damage point | Damage if wrong | Class |
|---|---|---|---|
| **D-1** | `_gate_enqueue` reaches the outbox with **only** `self.killed` as a check (`node.py:3036-3054`). Its safety rests on an *assumption*: "these paths are all RED and already require human approval downstream." | An enqueue path that is not actually RED, or whose downstream approval is skippable, sends with no policy evaluation. | **REVIEW_ONLY** — never probe on live infrastructure |
| **D-2** | Dev-time hooks (`.cursor/hooks/deny_egress.py`, `deny_secret_read.py`, `deny_destructive.py`, `guard_flags.py`) bind an **editor process**. A bare shell, a `python` invocation, or a systemd unit is not covered by them. | Agent reaches the network or reads a secret from a context the hooks do not police, while the hooks create a feeling of coverage. | STATIC + DOC |
| **D-3** | Kill-switch **path fragmentation.** `<root>/HALT` (`ops/ign1_telegram_ignite.py:28`), `~/ofn/HALT-ALL` (`ofn/budget/opslib.py:20`, self-declared «تک‌oracle»), and a **caller-supplied** path for `RunGate._halt_path` (`adapters/run_gate.py:35`) and `halt_log.py:228`. `AGENTS.md` GOV-V7 names `F:\ofn-node\HALT` — **that file does not exist.** | Arming the *documented* switch flips a file nothing reads. Because `halt.py:26` defines **absent = RUNNING**, the failure is **silent, not fail-closed**. This is the single most serious item found. | DOC/REVIEW → owner decision (see §9) |
| **D-4** | `ofn/adapters/fake_executor.py` writes `execution_receipts.jsonl` receipts shaped like real ones. | A simulated receipt is cited later as evidence of a real effect. | Mitigation by label (below) |
| **D-5** | `LAB-DOCTOR-CONTRACT.yaml`: all 10 hard-sandbox requirements are `UNKNOWN_NOT_VERIFIED`; `verdict: NOT_A_VERIFIED_HARD_SANDBOX`; `gate_3` blocked. | Untrusted candidate code run under a jail that is *asserted* but not *verified* escapes through a property nobody tested. | **Design rule: do not depend on it.** |
| **D-6** | Two `canonical` notions. `ledger.canonical()` uses compact separators `(",",":")`; `octopus_observation/fixture_run.py:68` hashes `json.dumps(..., sort_keys=True, ensure_ascii=False)` with **default** separators. Both call themselves canonical. | A cross-artifact hash comparison silently passes or fails for the wrong reason; the byte-identity claim the ledger depends on is not actually shared. | STATIC |
| **D-7** | `install_systemd.sh:19` bakes `OCTOPUS_WIRE_LEAD_OUTBOUND=1` into every agent unit. | Reading the flag as a safety boundary is wrong in the deployed configuration; the real boundary is consent + effect gate + caps. | STATIC |
| **D-8** | The probe harness itself, if built carelessly, becomes a new egress path ("just a test script"). | The instrument becomes the escape. | **Prevented by design — §6.3** |

### 4.1 The positive findings (protection that is real)

Recording what actually holds is as important as recording what does not:

- `ofn/adapters/receipt.py:93` `grants_send()` → **structurally False**, and raises
  `FailClosedError` if the payload even *mentions* a send/ready state.
- `ofn/kernel/hash_chain.py:46` `grants_send()` → **structurally False**;
  `halt_blocks_chain()` → False (HALT stops starts, not in-flight linking).
- `ofn/adapters/halt_flag.py:24` `halt_flag_active()` → missing file = RUNNING;
  **symlink, unreadable, non-UTF-8, or unparsable = HALTED.** Fail-closed on
  everything it cannot verify. (The defect in D-3 is the *path*, not the predicate.)
- The live publish path carries real downstream controls — release gate
  (`kernel/release_switch.py:122`), consent, platform matrix, ledger-verify before
  send (`node.py:3597`), call budget.
- `Node.publish_to_telegram` will only exit through an outbox item marked
  `approved_manual`.

This asymmetry — fail-closed predicates, structurally-false grants, real downstream
gates, *and yet* a documented path that nothing reads — is exactly why the
instrument must report four states instead of one verdict.

---

## 5. The falsifiable hypothesis

**H1 — the emergence question, honestly posed.**

> On **held-out** deceptive layouts (structure generated from the seed, hidden
> pattern randomized, hidden state unreachable from the candidate's observation
> interface), the candidate's success advantage over a **novelty-exploration
> control** is ≤ 0.

- **H0 (null):** candidate ≥ control on held-out layouts.
- **Falsifier:** if the control ≥ candidate on the held-out set, or if the
  candidate's Wilson 95% lower bound ≤ the control's rate, then the honest
  conclusion is **"exploration, not inference"**, the capability stays at **≤ E3**,
  and no claim of emergent capability is recorded.
- **Pre-registered pass bar:** candidate Wilson-95% lower bound > control rate on
  S1-held-out, at fixed seed count, `retries = 0`, thresholds frozen before the run.

**H2 — the instrument question.**

> For every control the harness touches, exactly one of `WIRED` / `TESTED_ONLY` /
> `DOC_ONLY` / `UNVERIFIED` is mechanically derivable, and re-running the harness
> on an unchanged tree reproduces the same verdicts.

**Explicitly *not* a hypothesis — already established by reading:** §1.3 and §2.
These are structural facts. Recording them as experimental findings would inflate
the instrument's value dishonestly.

**Scope limits of v0 (stated now so nobody over-reads it later):**

1. v0 measures **modules**, not the organism. It never starts `ofn.service`.
2. v0 uses **simulated** fixtures. No claim about real-world performance follows.
3. v0 **cannot** establish causality on the live path; that would require live
   ablation, which is forbidden.
4. v0 therefore cannot measure organism-level eval-awareness. It can only detect
   candidate-level drill-sensitivity (§6.2 L6) — a weaker, narrower property.

---

## 6. The one small change

### 6.1 Scope

**One additive directory. Zero edits to any existing file.**

```
F:\backup\_ops\probe_harness_v0\        <- NEW, standalone, offline
```

Rationale for placement: `_ops/` is the vault's established home for offline
experiments with declared `risk_class: read` (the retired hypothesis engine lives
there; `_ops/coding_sandbox/` lives there). Nothing under `ofn/**` is touched, so
no live surface, no deploy, no Class B, no witness step is involved.

Rationale for size: the honest minimum that can both **run an arm comparison** and
**refuse its own escape**. If the implementer can satisfy an invariant by reusing
something that already exists, the instruction is to reuse and shrink, not to
build.

### 6.2 Test-design invariants — each one closes a defect found in §3.2

| ID | Invariant | Closes |
|---|---|---|
| **L1** | Hidden state must be **unreachable** from the candidate. The observation interface exposes only observations. A static check asserts the candidate module contains no reference to the environment's private answer attributes. | `env.secret_doors` read (confound 2) |
| **L2** | **Seed must vary the environment.** Assert the structure digest differs across at least two seeds. Two seeds → two different mazes, or the run is void. | fixed layout (confound 3) — this is the cheapest decisive check |
| **L3** | **Pre-registration before execution.** `PREREG.json` (metric, arms, seeds, thresholds, falsifier, retries=0) written and sha256-pinned **before** the first real run. Changing it after seeing results voids the run. | post-hoc thresholds |
| **L4** | **Held-out structures only.** S0 = reference reproduction; the *claim* is made on S1 (unseen, shuffled). Reporting only S0 is not a result. | co-designed environment |
| **L5** | **The solution pattern must not be a constant** anywhere in the candidate or the fixture. Secret structures are generated from the seed. | hardcoded `SECRET_PATTERN` (confound 1) |
| **L6** | **Two-mode run.** The same fixture is run in `normal` and `drill` framing; divergence is reported as a first-class result (`EVAL_AWARENESS_SUSPECTED`), never averaged away. | the "disciplined only during tests" lens |
| **L7** | **Canonicalize + hash, with the rule pinned by a literal test vector.** The harness states one canonical rule and asserts it against a frozen expected digest, so drift in either `canonical` notion is caught rather than assumed away. | D-6 |
| **L8** | **No escape surface.** The harness has no network, no subprocess, no third-party import, no writes outside its own `receipts/`. Enforced by a fail-closed static check over the whole package (§6.3). | D-5, D-8 — and deliberately does **not** inherit the unverified jail |

### 6.3 The safety-check function (the harness's own gate)

A single fail-closed function that runs **before any arm executes**, and again as a
test. It must refuse, with a named reason, if any file in the package (transitively)
does any of:

1. imports a forbidden module — `socket`, `subprocess`, `urllib`, `http`, `ssl`,
   `smtplib`, `imaplib`, `requests`, `paramiko`, `ftplib`, `asyncio.subprocess`,
   `multiprocessing`;
2. imports the protected live surfaces — any `ofn.kernel.*`, `ofn.adapters.*`,
   `ofn.agents.*`, `ofn.node`, `ofn.run`, `ofn.budget.*`;
3. calls `eval` / `exec` / `compile` / `__import__` / `os.system` / `os.popen`;
4. opens a path for writing outside an allowlisted receipts directory;
5. contains a literal that matches a secret-looking pattern, or the name of any
   wire / halt / gate flag;
6. reads an environment variable at all (v0 is pure — configuration is passed in,
   never inherited).

Failure is `FailClosedError`, not a warning. A harness that cannot certify itself
does not run — the same rule the project already applies to the reflex contract.

### 6.4 The three arms

| Arm | Role | Implementation |
|---|---|---|
| **A — baseline** | simplest defensible prior / greedy policy | no learning, no exploration bonus |
| **B — candidate** | the module under test, behind a narrow declared interface | loaded **by path**; the harness never imports it at module import time |
| **C — control** | novelty / random exploration | required, not optional — this is the arm that killed the original claim |

**Reported per arm:** success rate with Wilson 95% interval, median TTD among
successes, and wasted steps. **Never** a bare percentage without its interval.

### 6.5 Causal map, with honest edge labels

Promotion rule: an edge is `CAUSAL` only with (a) a replay reproducing the effect,
(b) an ablation where removing the node changes the outcome, or (c) a **structural
proof** (the callee is not on the path). Otherwise it stays `CORRELATED_ONLY`.

| Edge | Status | Basis |
|---|---|---|
| `propose` → `admit()` → gate → receipt | **CAUSAL**, but **absent from the live path** | (c) structural: zero production callers |
| input → retrieval → proposal | `CORRELATED_ONLY` | no replay yet |
| `_gate_enqueue` → outbox | **CAUSAL**, thin | read directly |
| gate → receipt | **CAUSAL** | `ledger.append` under `BEGIN IMMEDIATE`; `verify()` recomputes |
| receipt → outcome | `CORRELATED_ONLY` | `unknown_outcomes()` exists; reconciliation history shows the join is fragile |
| halt → starts | **PARTIAL** | real for the survival loop (`opslib`); `RunGate` not constructed in production |
| receipt → send authorization | **CAUSAL-NEGATIVE** | `grants_send()` structurally False — a genuine, verified negative |

### 6.6 Rollback

Trivial and complete, because the change is one new directory:

1. `git status` in `F:\backup` shows only additions under `_ops/probe_harness_v0/`
   (plus the `plans/` documents).
2. Rollback = remove that directory. No live service, no flag, no timer, no ledger
   row, no DB migration is involved.
3. Pre-image receipt: file list + sha256 of every file in the package, taken before
   the first run, so the receipts can prove the instrument did not change mid-run.
4. Kill: the harness has no scheduled execution. It runs only when a human types the
   command. Nothing to disarm.

---

## 7. Acceptance criteria

Green means all eight, each with an artifact, not a claim:

1. `PREREG.json` exists, is sha256-pinned, and its `git log` timestamp precedes the
   first receipt.
2. The safety-check function passes in a **self-test** and **fails closed** on a
   deliberately planted violation (negative test).
3. Canonicalization parity test green against a literal frozen digest (L7).
4. Two seeds produce two different structure digests (L2).
5. Held-out S1 results exist, are reported separately from S0, and carry intervals.
6. The control arm C is present in the output. A report without C is incomplete.
7. Every receipt carries `mode: SIMULATED` and `superiority_claim: null`.
8. The harness is reproducibly re-runnable: same tree → same verdicts.

**A run that fails the falsifier is a successful outcome**, per `AGENTS.md` §2
("lowering a grade is a successful outcome, not a failure").

---

## 8. What this plan deliberately does not do

- Does not touch `ofn/**`, `data/gates.json`, `BUDGET.json`, `HALT`, any timer, or
  any systemd unit.
- Does not contact `.138`, `.180`, `.182`, the ESP32, or any live node.
- Does not send, pay, order, invoice, or read financial data.
- Does not restart a service, add a dependency, listener, daemon, or broker.
- Does not read secrets, rewrite receipts, or push/merge/force-push.
- Does not attempt to measure the organism. v0 measures modules, and says so.

If a question can only be answered by breaking one of those, the correct verdict is
`BLOCKED_BY_SAFETY` — not a workaround.

---

## 9. Owner decisions required

Per `AGENTS.md` §6 these are registered in `07-HANDOFF/`, not decided here.

**OD-1 — kill-switch path fragmentation (D-3).** Three file conventions exist and
the one named in `AGENTS.md` GOV-V7 does not exist. Because absent = RUNNING, arming
the documented switch is **silent**. Options: (a) make `~/ofn/HALT-ALL` the single
documented oracle and correct the governance text; (b) additionally make a mismatch
loud, e.g. a doctor probe that reports which halt files exist and which is read;
(c) do nothing and record the risk. Fixing this touches either governance text or a
live module, so it is owner-gated either way.

**OD-2 — placement of the safety map.** Vault convention puts a governance artifact
of lasting value beside `CONSTITUTIONAL-ZONES.yaml` / `LIVE-ORGANISM-MAP.json` at
the vault root; the instruction was `plans/`. It currently lives in `plans/` only.
Relocation is cosmetic and reversible.

**OD-3 — whether `declared ≠ wired` becomes a standing gate.** If it does, every
future capability claim must carry a wiring verdict, and some existing claims in
the architecture bible would drop a grade. That is a governance choice, not a
technical one.

---

## 10. Related documents

- `plans/MP-IMPLEMENT-EMERGENCE-SAFE-SURGERY-v1.md` — the execution prompt.
- `plans/EMERGENCE-SAFE-SURGERY-DISCOVERY-REPORT.md` — what was found/not found, rejected options, verdict.
- `plans/OCTOPUS-SAFETY-MAP-v1.md` — the formal safety map and risk scorecard.
- `plans/SURGICAL-PROTOCOL-v1.md` — the mandatory workflow for the executing agent.

---

## خلاصه برای مالک

تحقیق تمام شد. سه نکتهٔ مهم:

۱. آزمایش قبلی (۹۷ در برابر ۰) درست نقل شده، ولی بردش واقعی نیست: پاسخِ معما داخلِ
خودِ برنامه نوشته شده بود، برنامه کلیدِ مخفیِ محیط را مستقیم می‌خواند، و محیط در هر
۱۰۰ اجرا یکی بود. کنترلِ کنجکاوی ساده ۱۰۰ از ۱۰۰ برد و سریع‌تر بود.

۲. مشکل اصلی جای دیگری است: چند «کنترلِ ایمنی» در سندها و تست‌ها وجود دارد ولی در
مسیر واقعی صدا زده نمی‌شود. یعنی محافظت شبیه حصار است، ولی حصار در مسیر نیست.

۳. یک نکتهٔ جدی: کلید توقف در سه جای مختلف تعریف شده و فایلی که در سندها نوشته شده
وجود ندارد. اگر کسی همان را فعال کند، توقف **بی‌صدا** بی‌اثر می‌ماند.

برنامه: یک ابزار کوچک و آفلاین بسازیم که بگوید کدام کنترل واقعاً کار می‌کند
(وصل‌شده) و کدام فقط در کاغذ و تست هست. هیچ کدی تغییر نکرده و هیچ چیزی روی نودها
اجرا نشده. سه تصمیم مالک در انتهای سند آمده.
