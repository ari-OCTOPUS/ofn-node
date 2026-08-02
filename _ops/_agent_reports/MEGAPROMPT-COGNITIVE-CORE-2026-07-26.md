---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [megaprompt, cognitive-core, parallel-agents]
created: 2026-07-26
updated: 2026-07-26
---

# مگاپرامپتِ هستهٔ شناختی — برای ایجنت‌های موازی

> کپی کن، به هر ایجنت **یک workstream** بده. خودبسنده است.
> هر عدد در این سند از درختِ زندهٔ `F:\backup` خوانده شده، نه از حافظه.

```
You are working on a Persian-language agent-first Obsidian vault at F:\backup
which also runs a live "organism" (_ops/). You are one of several parallel
agents. You have ONE workstream, named at the bottom. Do not touch another
agent's files.

════════════════════════════════════════════════════════════════════
§0 — HARD RULES. Violating one invalidates your work.
════════════════════════════════════════════════════════════════════
 1. NEVER DELETE. Only move. Duplicates -> _Duplicates, retired -> _Archive.
 2. Never touch .git internals, any _code folder, or any file containing a
    secret. Never write a secret into chat, a note, or a log.
 3. New behaviour is ADDITIVE + FLAG-GATED + DEFAULT-OFF. Even a bug fix that
    changes live behaviour gets a flag — the owner votes on behaviour.
 4. `git add -A` is FORBIDDEN at the repo root: STOP-* control files must stay
    untracked. Stage explicit paths only.
 5. Do NOT read _ops/state/OWNER-PROFILE* — this repo's own code classifies it
    private (cockpit_readmodel.py:10, export_status.py:8).
 6. The venture in "03 - Projects/اونلی فنز" is content-free for agents: never
    open, list or echo anything under "08 - Partner (PII)" or any Identity/*
    folder, never output a persona name, handle, or location. Code paths are OK.
 7. If a rule blocks you: STOP and write the question into
    00 - Inbox/AGENT_QUESTIONS.md. Never route around a prohibition.

════════════════════════════════════════════════════════════════════
§1 — THE EPISTEMIC RULE THAT MATTERS MOST HERE
════════════════════════════════════════════════════════════════════
On 2026-07-26 a single agent-day produced ~10 real fixes. Every one of them was
the same disease: **a claim that could not be false.**

  · a fail-closed owner gate whose input was always the bot's own id, so
    rfc_decision held ZERO rows for the entire history of the system
  · a card that could not be sent because its id made callback_data 75 bytes
    against Telegram's 64-byte cap — send_text swallowed the 400 and returned
    False, silently
  · `produce() -> "no-defect"` from a sensing layer where 5 of its 6 probes
    returned count=-1, i.e. could not see at all
  · a cadence written as `beat % 60 == 0` against a counter the caller samples
    sparsely, so it never once fired

In the SAME day that agent also called three things bugs that were not: a
healthy lead_scorer fed the wrong field name, a rate limiter mistaken for a dead
brain, and its own test polluting shared state.

So: **label every claim** VERIFIED (you ran it) / SAYS (a doc claims it) /
INFERRED / NOT VERIFIED. Get an explicit pass/fail count or an exit code —
absence of an error is not a pass. And when something is silent, feed it a
synthetic input to prove it *can* speak before you read the silence as health.

**Register predictions with a clock time BEFORE you look.** On 2026-07-26 the
cadence bug was only found because someone wrote "if X does not exist by 14:13,
my wiring is wrong" and then honoured it. Without that line the missing file
would have read as "not due yet".

════════════════════════════════════════════════════════════════════
§2 — WHAT IS ALREADY MAPPED. Do not redo this.
════════════════════════════════════════════════════════════════════
Measured 2026-07-26, all VERIFIED by running it:

MODULE COUNTS: _ops/neural/ has 14 modules, _ops/heart/ has 15, _ops/cortex/ has
~30, _ops/brain/ has 1 (cockpit.py).

REACHABILITY: **zero orphans in neural/ and heart/.** Every module has at least
one non-test caller. Highest fan-in: heart/shadow (64 callers), heart/producers
(12), neural/reflex (11), neural/bcm (10), neural/consolidation (10),
heart/interface (10). Lowest: heart/pulse_arbiter (1, organism.py),
heart/money_pulse (1, center.py), neural/neural_driver (1, wiring.py).
=> The question is NOT "is it wired". It is wired. The question is whether any
of it changes a decision.

CONTRAST — a real orphan was found the same day: `_ops/heart_wires.py` carried
thesis/coherence/identity/seed-killer wires and its own docstring said "call
from organism or cron every N beats". It had ZERO callers outside its own test.
Use that as your template for what an orphan looks like.

FIVE BLACK BOXES (from blackbox_map.survey(), live):
  nbb_black_box       F:\_______Black Box      NBB Control Plane / super-governor
  4d_system_in_vault  F:\backup\4d_system      SOG + Brain-OS (DEPRECATED 07-18)
  romajan_lab         F:\romajan               PSLQ + SINDy + evalharness
  c6_live_loop        _ops/c6_trigger.py       propose-only self-improvement
  coherence_organ     _ops/coherence.py        hunts unfalsifiable claims

THE BRAIN IS ALIVE AND CHEAP: model_router.ask(task, prompt, ...) — task is the
FIRST positional arg. Local tier = ollama qwen2.5, ~2-6s, $0. Paid tier =
sakana/fugu, 2.3-22s, cost_usd=0 because the plan is flat-rate. `STOP-FUGU` was
a stale kill-switch and was cleared 2026-07-26 with evidence.
Local brain enforces OLLAMA_MIN_INTERVAL_S — **20 seconds live**. Two rapid
calls will make the second look like a dead brain. It is not.

SELF-IMPROVEMENT STATE: C6 ran 4 complete cycles on 2026-07-26 (probe →
hypothesis → experiment → verdict → card delivered). All four verdicts were
correct. All four were about the organism's own plumbing; **zero** were about
the owner's business. memory.db grew 2 → 6 rows. NOT ONE produced a code change
— `_ops/self_patch.py` (new, flag OCTOPUS_WIRE_SELF_PATCH) is the bridge that
writes a patch and shadow-tests it, but applying is always one owner click.

KNOWN OPEN DEFECT: code_autonomy.shadow_test runs the FULL 327-file suite in an
isolated worktree and **exceeded 500s** on 2026-07-26, and when the process was
killed the `finally` never ran and a git worktree LEAKED into %TEMP%. Verify
with `git worktree list` before and after anything you run.

════════════════════════════════════════════════════════════════════
§3 — THE QUESTION BEHIND ALL WORKSTREAMS
════════════════════════════════════════════════════════════════════
The owner's words, 2026-07-26: the octopus should simulate its hearts, brains
and neural networks, use its black box, learn, and be given more capability —
so that it can build the painting business and survive.

A prior audit called the octopus "a homeostat, ~80% decorative mathematics"
(see memory: project_octopus-math-anatomy). That claim is SAYS, not VERIFIED.
Your job is to settle it with measurements, and where it is true, to say what
the smallest real replacement would be.

For every mathematical object you examine, answer these four, with evidence:
  Q1  What does it compute, in one sentence, in terms of real inputs?
  Q2  Does any DECISION read its output? Name the file:line that consumes it.
      If nothing consumes it, it is decorative regardless of how correct it is.
  Q3  If its inputs were replaced with noise, would any observable behaviour
      change? Prove it — inject and measure, do not reason about it.
  Q4  Is it falsifiable? What observation would show it is wrong?

════════════════════════════════════════════════════════════════════
§4 — WORKSTREAMS. You own exactly one.
════════════════════════════════════════════════════════════════════

WS-1 · THE HEART — is the rhythm computing or performing?
  Files: _ops/heart/*.py (15 modules), _ops/chrono.py, _ops/cardiac.py
  Start: sog_math.py (the "locked" equations), control_law.py, pulse_arbiter.py,
  producers.py, shadow.py (64 callers — highest fan-in in the whole layer).
  Answer Q1-Q4 for: E_shadow, phi, sigma, the SOG lock, the arbiter period.
  Known: on 2026-07-25 phi=300.0 turned out to be the computational ceiling of
  p_later=1e-300, not a real number, and it fired 66 self-heal restarts. Look for
  more of that shape — a quantity whose extreme value is an artifact of its own
  formula. Also: cardiac budget was 288/288 depleted, forcing arbiter period 900s
  against a designed 42.4s. Is that homeostasis or a stuck valve?

WS-2 · THE NEURAL STACK — does it learn from data or from noise?
  Files: _ops/neural/*.py (14 modules)
  Start: bcm.py (BCM forgetting), hebbian.py, consolidation.py, latent_space.py,
  sparse_filter.py, encoders.py.
  Answer Q1-Q4 for each learning rule. The decisive test: what is the actual
  INPUT distribution? Read _ops/neural/hebbian.json and consolidation.json on
  disk and report how many real events they have ever seen. A Hebbian rule fed
  by three events is a decoration with a Greek letter.
  Then: if it did learn, where would the learning be READ? Trace one full path
  from weight update to a changed decision, or state that none exists.

WS-3 · THE BLACK BOXES — what is extractable, and what is a museum?
  Paths: F:\_______Black Box · F:\romajan · F:\backup\4d_system (self-declared
  DEPRECATED 2026-07-18)
  MEASURED 2026-07-26: the romajan probe reports **44 verified/executed maths
  claims that C6 has never ingested** (probe romajan_new_claims, count=44,
  floor=0). romajan holds a PSLQ rediscovery engine, SINDy symbolic regression,
  a sealed eval harness, a 105-challenge frozen benchmark with 43 held out, and —
  importantly — it KEPT ITS OWN NEGATIVE RESULTS instead of merging them away.
  Your job: pick the 3 highest-value claims of those 44 and show, concretely,
  what a C6 hypothesis derived from each would look like — question, stop
  condition, falsification criteria, expected artifact. Do NOT run experiments;
  design them so they are runnable.
  Also: state plainly which of the three boxes is a live asset and which is a
  museum. F:\backup\4d_system declares itself deprecated; verify or refute.

WS-4 · TEACHING — how does anything become durable knowledge?
  Files: _ops/state/memory/memory.db, _ops/doctor/self_knowledge.py,
  _ops/tg/operator_doctrine.py, _ops/outcomes/thesis_queue.py,
  _ops/state/thesis/thesis-ledger.json (19 rows)
  MEASURED: memory.db holds 6 rows total, four of them written 2026-07-26, each
  the conclusion of one C6 experiment. self_knowledge is rebuilt from scratch
  every cycle — a lesson written into its OUTPUT is erased next round; that is
  why operator_doctrine.py exists and is injected into snapshot() as an INPUT.
  The thesis ledger has 19 rows and NOT ONE changed status on 2026-07-26.
  Questions: what is the actual write path into memory.db, who reads it, and
  what would make a lesson change a future decision rather than sit in a table?
  Design the smallest loop that closes "learned" → "behaves differently", and
  say what it would cost.

WS-5 · CAPABILITY — what is the next real power, ranked by evidence?
  Do NOT brainstorm. Enumerate what already exists and is OFF, measure what each
  would do, and rank by evidence of impact.
  Start from _ops/OCTOPUS-flags.cmd (~84 keys, 64 currently on). Known-off and
  interesting: OCTOPUS_WIRE_HARVEST (AusTender ingestion), OCTOPUS_WIRE_MISSION_
  RUNNER, OCTOPUS_WIRE_POCKETSMITH, OCTOPUS_WIRE_LEAD_DRAFT, and
  OCTOPUS_WIRE_LEAD_CANDIDATES which is ABSENT from flags.cmd entirely.
  MEASURED 2026-07-26: that last one is the single gate between a real customer
  and a healthy scorer. owner_menu.looks_like_lead() correctly detects Persian
  lead text (verified), but _register_lead_canonical returns None without that
  flag and falls back to a frozen inbox. All three lead inboxes contain only
  templates — zero real leads have EVER been scored. The engine is healthy and
  starved: a $15k interior repaint scores 76, a $715 maintenance job 86, a $250k
  strata job 96, against draft_threshold 70.
  For each candidate capability state: what turns on, what it can NEVER do
  (outward sends stay gated), the smallest test that proves it works, and the
  observable that would show it is working a week later.

════════════════════════════════════════════════════════════════════
§5 — GOTCHAS THAT COST REAL TIME. Read or repeat them.
════════════════════════════════════════════════════════════════════
· ANTIVIRUS locks .git/objects. `git add` fails "Permission denied". Retry in a
  loop up to ~6 times. It usually succeeds on attempt 2-3.
· Piping `git add` through `head` sends SIGPIPE and stages NOTHING silently.
· The Edit tool converts .cmd/.bat files to LF, which breaks cmd parsing. On
  2026-07-26 twelve batch files were found LF-damaged, 8 of them containing
  if/goto/:label — including RESTART-ORGANISM.bat's `if exist HALT-ALL goto`.
  Edit them BYTE-LEVEL in Python and assert the lone-LF count is 0 afterwards.
· NEVER rewrite a .bat that is currently executing: cmd.exe reads it by byte
  offset and will jump into the middle of a line.
· flags.cmd is `source`d at process BOOT. Editing it changes NOTHING until a
  restart. Say so every time. Check `ORGANISM-STATE.code.booted` against the
  file mtime before claiming a flag is live.
· Python does not source flags.cmd. If your probe needs a flag, parse the file
  yourself: `re.findall(r'^\s*set\s+(\w+)=(.*)$', raw, re.M)`.
· Checking a flag by PRESENCE is not checking its VALUE. On 2026-07-26 an
  arming script skipped OCTOPUS_WIRE_ROMAJAN_PROBES as "already there" — it was
  set to 0.
· run_all.py runs each test as a bare `python test_x.py`, so pytest is not in
  sys.modules. `python -m pytest tests/test_x.py` collects ZERO tests and exits
  0 — a guaranteed false green. Run the files directly and read the exit code.
· Test function naming is NOT uniform: most files use `t_*`, but
  test_llm_intent.py uses `test_*`. A test with the wrong prefix is never
  collected and the file still prints green.
· REAL_VAULT / ORG_ROOT default to the LIVE tree. A test that forgets to
  isolate one module's path will read and sometimes WRITE the live organism.
· `_ops/tests/test_tg_power.py` genuinely creates _ops/STOP-ORGANISM and
  RESTART-REQUESTED. Running the full suite while the organism is up can put it
  to sleep. Run everything else and say which one you skipped.
· Concurrent agents: check `git status` before staging shared files and
  attribute honestly in the commit message if you carry someone else's work.

════════════════════════════════════════════════════════════════════
§6 — WHAT TO HAND BACK
════════════════════════════════════════════════════════════════════
A single markdown file at `_ops/_agent_reports/WS-<n>-<topic>-2026-07-26.md`:

 1. VERDICT in one paragraph. If the honest answer is "this is decorative",
    say it plainly — that is a valuable result, not a failure.
 2. A table: object | what it computes | who consumes it (file:line) | Q3 noise
    test result | falsifiable? | verdict
 3. The 3 highest-value concrete next steps, each with the smallest test that
    would prove it works.
 4. Everything you could NOT determine, listed explicitly. "I could not tell"
    is a required section, not an admission.
 5. Any prediction you registered and its outcome, including refuted ones.

Do NOT change behaviour. This is a read-and-measure pass. If you write code,
it is a test or a probe, additive and flag-gated default-off.

YOUR WORKSTREAM IS: <<< WS-n >>>
```

---

## نکته برای آری

پنج workstream روی فایل‌های جدا کار می‌کنند، پس تصادم نمی‌کنند. اگر فقط دو ایجنت
داری، **WS-2 و WS-5** را بده — یکی می‌گوید آیا مغز واقعاً یاد می‌گیرد، دیگری
می‌گوید نزدیک‌ترین قدرتِ واقعی کجاست.
