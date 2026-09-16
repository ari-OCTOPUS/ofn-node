---
type: runbook
status: active
tags: [octopus, protocol, surgical, safety-check, audit-log, pre-registration]
updated: 2026-09-16
parent: "[[OCTOPUS-SAFETY-MAP-v1]]"
project: "[[OCTOPUS]]"
---

# SURGICAL PROTOCOL v1

`GOV_VERSION=V8 · LADDER=L2 · audience: any agent about to change the organism`
`mandatory: yes · bypass: none · date: 2026-09-16`

A mandatory workflow for an agent that is about to make a change. It exists because
the failure this project actually suffers is not a rogue agent — it is an agent (or
a human) believing a control is in force when the live path never consults it.

**The protocol has one rule above all others: verify before executing, and write
down what you verified.** Every step produces an artifact. A step with no artifact
did not happen.

> This protocol binds *changes*. Reading, and producing reports, do not require it.

---

## Step 0 — Declare (before touching anything)

Write, at the top of your audit log (§9):

```
GOV_VERSION=V8 · LADDER=L2
lane: <LANE-NAME>-<YYYYMMDD>
worktree: <path>
effect_class: A (internal, reversible) | B (deploy) | RED (owner-only)
pathways_touched: <P-n from OCTOPUS-SAFETY-MAP-v1 §4, or NONE>
```

Then answer the three boundary questions (`OCTOPUS-SAFETY-MAP-v1` §5.4):

1. Which pathway am I on, and is the control I am relying on in the **Actual
   control** column — or only in **Claimed control**?
2. If this goes wrong, what bites, and has that stop been verified *on this pathway*?
3. If I am wrong about "this is covered", how would I find out? If the answer is
   *silently*, **stop and raise an owner card**.

If `effect_class` is B or RED, stop here — this protocol is not sufficient; Class B
additionally requires the independent witness, and RED requires the owner.

**Artifact:** audit log opened.

---

## Step 1 — Isolate (work on a copy, never the live tree)

No edit is made in a place where it can be half-applied.

```bash
# preferred: a fresh worktree, no checkout surprises
git -C F:/backup worktree add --no-checkout -b codex/<lane> F:/wt-<lane> HEAD

# if the target is the live runtime repo:
cd F:/ofn-node && git status --porcelain   # must be clean before you start
git rev-parse HEAD                          # record this sha — it is your pre-image
```

Rules:

- Record the **pre-image**: commit sha + `git status --porcelain` output + sha256 of
  every file you intend to touch. Without a pre-image there is no rollback, and
  "receipt or rollback" is unsatisfiable.
- Never work directly on the live tree. Never operate on a live node's filesystem.
- One lane, one worktree, one concern. A file owned by another lane is a **stop
  condition** — log it and halt.

**Artifact:** pre-image block (sha, status, file hashes) in the audit log.

---

## Step 2 — Read the plan's own logic back (formal check against the megaplan)

Do not execute a plan you have not re-derived. Load the governing plan
(`plans/MEGAPLAN-*.md`, `plans/MP-IMPLEMENT-*.md`, or the lane's `MEGAPROMPT-*.md`)
and extract, mechanically, its **declared** content into a checklist:

| Extract | From where | Check |
|---|---|---|
| Declared invariants | megaplan's invariant table (e.g. L1–L8) | each must be satisfiable **and** testable; an invariant with no test is not an invariant |
| Declared falsifier | megaplan §5 | the falsifier must be stated **before** the run, and it must be *falsifiable* — if no outcome could refute it, reject the plan |
| Declared scope | "what this does not do" section | every item must be checkable (a path, a flag, a host) |
| Declared rollback | rollback section | must name an exact command and an exact artifact |
| Declared acceptance criteria | acceptance section | each must have an artifact, not a claim |

Then, for each row, record `SATISFIABLE / UNSATISFIABLE / UNTESTABLE / NOT FOUND`.
**A plan with an untestable invariant, or a falsifier that nothing could refute, is
rejected at this step — before any code is written.** Report the rejection; do not
repair the plan silently by inventing the missing parts.

If the plan claims a structural fact about the live code (e.g. "`Node.propose` has no
production callers"), **re-derive it with your own command** and record
`CONFIRMED / REFUTED` plus the command. Where a plan's claim is refuted, the plan's
inputs are wrong and that is a finding, not an inconvenience.

**Artifact:** the extracted checklist with per-row verdicts and commands.

---

## Step 3 — Build the safety-check function (before any code execution)

Before executing anything — including before running your own new code — the change
must pass a single **fail-closed** function. Failure is an exception with a named
reason, never a warning. The function answers: *can this change produce an effect
outside its declared boundary?*

Minimum checks (extend per lane):

| # | Check | Refuse if |
|---|---|---|
| 1 | **Import surface** | a forbidden module is imported transitively — `socket`, `subprocess`, `urllib`, `http`, `ssl`, `smtplib`, `imaplib`, `requests`, `paramiko`, `ftplib`, `multiprocessing` |
| 2 | **Protected-surface import** | any `ofn.kernel.*`, `ofn.adapters.*`, `ofn.agents.*`, `ofn.node`, `ofn.run`, `ofn.budget.*` is imported by an offline instrument |
| 3 | **Dynamic execution** | `eval`, `exec`, `compile`, `__import__`, `os.system`, `os.popen` appear |
| 4 | **Write scope** | a write handle targets a path outside the declared output directory |
| 5 | **Secret / flag literals** | a secret-shaped literal, or any wire / halt / gate flag name, appears |
| 6 | **Environment reads** | the code reads a process env var (offline instruments take configuration as arguments) |
| 7 | **Path scope** | the diff touches a file outside the declared lane scope, or any B0 / `unresolved` zone file |
| 8 | **Diff class** | the change is not additive where the plan declared it additive |

**The function must be negative-tested.** For every check, plant a deliberate
violation and assert the refusal. A safety check with only green tests is not a
safety check — `fake_executor` and `RunGate` are green tests with no live consumer,
which is exactly the failure this protocol exists to catch.

Every control inspected must be reported with one of four verdicts — **`WIRED` /
`TESTED_ONLY` / `DOC_ONLY` / `UNVERIFIED`**. A boolean safe/unsafe output is a
failed implementation: it hides the distinction that matters.

**Artifact:** the check's output block, including the negative-test results.

---

## Step 4 — If the change needs a measurement, pre-register first

Any claim produced by running code requires pre-registration, written and committed
**before** the first run:

- hypothesis, null hypothesis, and the **falsifier**
- arms (including a **control**), scenarios, seeds
- metric with an interval, and the pass bar
- `retries = 0`
- void conditions
- `prereg_sha256`, committed before the first receipt (`git log` proves the order)

Rules that are not negotiable:

- **Never change a threshold after seeing a result.** If a denominator or threshold
  must change, the run is **void** — write a new prereg and start over, and say so.
- **Never drop the control arm.** A candidate-vs-baseline comparison with no control
  is the comparison that was already falsified once in this project.
- **A failing result is a successful outcome** (`AGENTS.md` §2). Report it first.
- **No bare percentages.** Every rate carries its interval. Small n is
  `UNDERPOWERED`, never "improved".

**Artifact:** `PREREG.json` + its commit sha.

---

## Step 5 — Execute, then stop

- Run once per preregistered condition. `retries = 0`.
- Write receipts only into the declared output directory. Nothing leaves the machine.
- On crash: record it and stop. **Do not "fix and retry"** — a post-hoc fix converts
  an honest failure into a quiet one.
- Never run a live-ablation of a control to see whether it bites. That is an
  incident, not an experiment.

**Artifact:** receipts, each carrying `mode` and `superiority_claim`.

---

## Step 6 — Verify the result, and only then claim it

Before any claim is written:

1. Do the numbers reproduce? Same tree + same seeds ⇒ identical digest.
2. Is the control arm present in the output?
3. Does each claim carry an interval and a denominator?
4. Does the capability grade respect the ceiling (`AGENTS.md` §2: nothing above **E3**
   without a scaffold-variation measurement)?
5. Is anything in the result a **simulated** artifact? If so, it carries
   `mode: SIMULATED` and cannot be cited as a real effect.
6. Has anything been claimed that a **structural fact** already settles? A reading
   result presented as a discovery is the same error as an observation presented as
   a capability.

**Artifact:** the claim list, each with grade and evidence path.

---

## Step 7 — Exit

1. Lane report at `F:\backup\09-LANES\<LANE>-<DATE>\LANE-REPORT.md`, header
   `GOV_VERSION=V8 · LADDER=L2`, sections: what was done / what remains / what
   failed / evidence paths / rollback. **No report, no completion** (`AGENTS.md` §9).
2. Run both vault validators and publish **explicit pass/fail counts**:
   `F:\backup\04 - Architect System\scripts\validate_frontmatter.py` and
   `find_broken_links.py`. "No errors" is not a green result. Never modify a
   validator to make it green.
3. `git status` — confirm the diff is the class it was declared to be.
4. Rollback documented with the exact command, verified to be available.
5. Owner decisions raised but not taken (`AGENTS.md` §6) → `07-HANDOFF/` as
   `status: open, requires: owner_decision`.

**Artifact:** lane report + validator counts + rollback command.

---

## Step 8 — Audit log (the exit condition of the protocol)

The audit log is not a narrative. It is the machine-checkable record of what was
verified at each step. One block per step, appended, never rewritten.

```json
{
  "lane": "EMERGENCE-SAFE-SURGERY-20260916",
  "gov": {"version": "V8", "ladder": "L2"},
  "effect_class": "A",
  "pathways_touched": ["P-12"],
  "steps": [
    {"step": 1, "name": "isolate", "pre_image_sha": "<git sha>",
     "pre_image_files_sha256": {"<path>": "<sha256>"},
     "working_tree": "clean", "result": "OK"},
    {"step": 2, "name": "plan_logic_check",
     "invariants": [{"id": "L2", "verdict": "SATISFIABLE", "test": "<test name>"}],
     "falsifier": {"stated": "control >= candidate on S1", "falsifiable": true},
     "plan_claims_reverified": [{"claim": "Node.propose has no prod caller",
       "command": "grep -rn ...", "verdict": "CONFIRMED"}],
     "result": "OK"},
    {"step": 3, "name": "safety_check",
     "checks": [{"id": 1, "name": "import_surface", "verdict": "PASS"},
                {"id": 2, "name": "protected_surface", "verdict": "PASS"}],
     "negative_tests": [{"id": 1, "planted": "<temp module>", "refused": true}],
     "control_verdicts": {"<control>": "WIRED|TESTED_ONLY|DOC_ONLY|UNVERIFIED"},
     "result": "OK"},
    {"step": 4, "name": "prereg", "prereg_sha256": "<sha>",
     "commit_sha": "<sha>", "committed_before_first_receipt": true},
    {"step": 5, "name": "execute", "retries": 0, "receipts": ["<path>"],
     "crashes": []},
    {"step": 6, "name": "claim_gate",
     "claims": [{"text": "<claim>", "grade": "E3", "interval": true,
                 "mode": "SIMULATED", "evidence": "<path>"}],
     "rejected_claims": [{"text": "<claim>", "reason": "<why>"}]},
    {"step": 7, "name": "exit", "lane_report": "<path>",
     "validators": {"frontmatter": "N pass / M fail",
                    "broken_links": "N pass / M fail"},
     "rollback": "<exact command>"}
  ],
  "outcome": "COMPLETE | BLOCKED_BY_SAFETY | VOID | FAILED_FALSIFIER",
  "blockers": [],
  "owner_decisions_raised": ["OD-1"]
}
```

**Rules for the log:**

- Append-only. Never edit a written block; write a new one.
- Every `verdict` field must cite the command or path that produced it.
- `rejected_claims` is **mandatory even when empty** — it is the evidence that the
  claim gate was actually applied. An empty list and a missing list mean different
  things.
- If the run is void, `outcome: VOID` and no numbers are reported from it.
- If a rule in §4/§5 of the safety map had to be broken to proceed, the outcome is
  `BLOCKED_BY_SAFETY`. **There is no other legitimate way to end that way.**

---

## Appendix A — Stop conditions (halt and log; do not work around)

1. The target is a file owned by another lane.
2. The change requires editing a B0 / `unresolved` zone file.
3. A required control turns out to be `DOC_ONLY` on the live path.
4. The pre-image cannot be taken.
5. A safety check cannot be made fail-closed.
6. A measurement would need live ablation to be meaningful.
7. A secret would need to be read, printed, or committed.
8. The only way forward is to change a threshold after seeing a result.

## Appendix B — Anti-patterns, each observed in this project

| Anti-pattern | Where it was seen |
|---|---|
| A control that is tested but not wired | `RunGate` (tests only); `halt_latch.py` ("not wired") |
| A module claiming to be the only path when a second path exists | `gates.py:3` vs `node.py:3036` |
| The answer embedded in the experiment | `agents.py:32` `SECRET_PATTERN` |
| n replicated from one instance | 100 seeds, one maze |
| A flag treated as a safety boundary after being declared decorative | `OFN_WIRE_OUTBOUND` deleted 2026-09-03 |
| Two artifacts both called canonical, with different byte rules | `ledger.canonical()` vs `fixture_run.py:68` |
| A documented stop that reads a path nothing else reads | `F:\ofn-node\HALT` |
| An unverified jail treated as a sandbox | `LAB-DOCTOR-CONTRACT.yaml` — `NOT_A_VERIFIED_HARD_SANDBOX` |

## Appendix C — One-line version

> Read the real code. Re-derive the plan's claims. Isolate. Check safety before
> running. Pre-register the measurement. Run once. Report the control arm first.
> Log every verdict with its evidence. Raise what is not yours to decide.

---

## خلاصه برای مالک

پروتکل جراحی نوشته شد: هر ایجنتی که می‌خواهد چیزی را در اکتپوس تغییر دهد، باید
این هشت گام را به ترتیب برود و برای هر گام یک سند بگذارد.

سه گام مهم‌ترند:
- **گام ۲:** قبل از اجرا، خودِ نقشه را دوباره بخواند و ادعاهایش را با دستور خودش
  تست کند. اگر نقشه غلط بود، همان‌جا رد شود — نه اینکه بی‌صدا درستش کند.
- **گام ۳:** یک تابع «سنجش ایمنی» که *قبل از* اجرای هر کد جواب می‌دهد و اگر
  شک داشت، **متوقف** می‌کند (نه هشدار). این تابع خودش هم باید با تست‌های منفی
  آزمایش شود.
- **گام ۸:** گزارش تصمیم‌گیری — برای هر گام، دقیقاً چه چیزی و با چه دستوری بررسی
  شد، و چه ادعاهایی **رد** شد. فهرست ادعاهای ردشده حتی اگر خالی باشد باید بنویسد.

در پایان، هشت شرط توقف و هشت اشتباه تکرارشدهٔ همین پروژه به‌عنوان پیوست آمده تا
ایجنت بعدی دوباره تکرارشان نکند.
