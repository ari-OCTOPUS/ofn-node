---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [megaprompt, neural, learning, handoff]
created: 2026-07-26
updated: 2026-07-26
---

# مگاپرامپت — «یادگیری را مفید کن»

> کپی کن، به ایجنتِ بعدی بده. خودبسنده است.
> هر عدد از درختِ زندهٔ `F:\backup` خوانده شده، نه از حافظه.

```
You are continuing work on a Persian-language agent-first Obsidian vault at
F:\backup which also runs a live "organism" (_ops/). One job, one deliverable.

════════════════════════════════════════════════════════════════════
§-1 — PREAMBLE: yesterday's load-bearing error. Learn from it first.
════════════════════════════════════════════════════════════════════
Yesterday an agent (WS-2) "confirmed" by grep that `OCTOPUS_WIRE_NEURAL` is
absent from OCTOPUS-flags.cmd and concluded: the brain is off. **That was
wrong.** In this codebase absence means ON (§2). Two other readers, including
the owner's own audit, inherited the same conclusion.

The lesson is not "grep carefully". It is: **when your tool disagrees with the
system's mechanism, the tool still returns a clean pass and the answer is still
wrong.** grep for a flag's presence is the wrong instrument for the question
"is this on".

So for EVERY flag you reason about, use three sources:
  1. parse flags.cmd yourself — `re.findall(r'^\s*set\s+(\w+)=(.*)$', raw, re.M)`
  2. check whether the key is in `wiring.PAPER_FULL_FLAGS` (absence there means
     the profile will NOT raise it, so absence in flags.cmd really is off)
  3. mtime-check the artifact the feature writes, against
     `state/ORGANISM-STATE.code.booted`
If the three disagree, STOP and write it into 00 - Inbox/AGENT_QUESTIONS.md.

════════════════════════════════════════════════════════════════════
§0 — HARD RULES. Violating one invalidates your work.
════════════════════════════════════════════════════════════════════
 1. NEVER DELETE. Only move. Retired -> _Archive.
 2. Never touch .git internals, any _code folder, or any file with a secret.
 3. New behaviour is ADDITIVE + FLAG-GATED + DEFAULT-OFF, even a bug fix.
 4. `git add -A` is FORBIDDEN at the repo root — STOP-* files must stay
    untracked. Stage explicit paths only.
 5. Do NOT read _ops/state/OWNER-PROFILE* — this repo's own code marks it
    private (cockpit_readmodel.py:10).
 6. The venture in "03 - Projects/اونلی فنز" is content-free for agents: never
    open, list or echo "08 - Partner (PII)" or any Identity/* path, never output
    a persona name or location. Module paths are fine.
 7. If a rule blocks you: STOP and add the question to
    00 - Inbox/AGENT_QUESTIONS.md. Never route around a prohibition.

════════════════════════════════════════════════════════════════════
§1 — YOUR JOB, IN ONE SENTENCE
════════════════════════════════════════════════════════════════════
Make ONE learning output change ONE real decision — and prove, with logged
evidence over a shadow period, that it decides better than the fixed formula it
augments. If the evidence says it does not, say so and ship nothing.

That last clause is the job too. "The learned signal was not better" is a
complete and valuable deliverable.

════════════════════════════════════════════════════════════════════
§2 — GROUND TRUTH, all VERIFIED 2026-07-26 by running it
════════════════════════════════════════════════════════════════════

THE NEURAL STACK IS ON. Three separate readers (two workstream agents and the
owner's own audit) concluded it was OFF because `OCTOPUS_WIRE_NEURAL` is absent
from `OCTOPUS-flags.cmd`. **In this codebase absence means ON.**
`organism.py:284` calls `wiring.apply_profile()` at boot; `resolve_profile()`
defaults to "paper-full" (`wiring.py:121`) and `OCTOPUS_PROFILE` is itself absent
so the default holds; `apply_profile()` then does
`for f in PAPER_FULL_FLAGS: if f not in os.environ: os.environ[f] = "1"`.
PAPER_FULL_FLAGS contains NEURAL, BCM, SPARSE, CONSOLIDATION, SPECTRAL, FISHER.
A flag explicitly set to 0 stays down; an ABSENT flag gets raised.
Physical proof: `_ops/neural/hebbian.json` and `consolidation.json` were both
written after the 17:05:27 boot. Note the path — **`_ops/neural/`, not
`_ops/state/neural/`**; both prior agents looked in the wrong directory.

NOTHING READS THE LEARNING. Q3 noise test, run for real:
`wiring.protective_override()` given a result carrying 50 random Hebbian pairs,
a random BCM theta, 20 noise insights, 30 latent keys and a random sparse count
returns **byte-identical** output to the clean case. Only `pain.level` and
`reflexes[].severity` move it, and both come from Nociceptor and ReflexArc —
fixed formulas over raw sensors, not learning. This is VERIFIED by injection.

THE VOCABULARY WAS JUST REPAIRED (commit e7f7d42). Before: exactly two possible
signals (`green_mode`, `stable`), so the associator could learn exactly one pair
by construction — `hebbian.json` held ONE pair after 2235 co-occurrences.
Now, behind `OCTOPUS_HEBBIAN_RICH` (default OFF), `wiring._hebbian_signals()`
emits **deviation only, never the normal state**:
    calm          -> []
    budget tight  -> [budget_tight]
    stressed      -> [rhythm_red, sigma_high, budget_tight, budget_depleted,
                      afferent_starved, errors_high]
    input starved -> [rhythm_amber, afferent_starved]
A healthy uneventful organism emits nothing and the associator decays.
An adversarial test (`_ops/tests/test_hebbian_signals.py`, 8/8) enforces this:
`t_no_partition_group_guarantees_a_signal_every_tick` exists because the FIRST
version of that function emitted banded signals (low/mid/high) and a partition
fires exactly one member every tick, so that member co-occurs with everything
and inflates strength while carrying zero information. Do not reintroduce it.

OTHER LEARNING OBJECTS, measured: `bcm-weights.json` has 0 keys after 59 steps
because the latent space it prunes was never populated;
`latent-vectors.json` and `sparse-predictor.json` **do not exist on disk**;
`consolidation.json` has 530 records whose newest entry carries
`latent_vector: null` and a single insight string. Encoders are deterministic
and correct and have no consumer that persists their output.

════════════════════════════════════════════════════════════════════
§3 — THE SAFETY INVARIANT. Non-negotiable.
════════════════════════════════════════════════════════════════════
**A learned value may only RAISE caution, never lower it.**

Concretely: a learned signal may cause an earlier halt, a longer epoch, a
smaller batch, an extra owner card. It may NEVER suppress a reflex, raise a
pain threshold, shorten a cooldown, unlock a gate, or make an effector fire that
the fixed formula would have blocked. Write that as an assertion in code, not a
comment — a test must fail if a learned path can ever produce a less-cautious
outcome than the fixed path on the same input.

Reason: `protective_override` is documented as structural — "orchestrator
cannot ignore it" (`wiring.py`). Everything today that broke did so because a
guard's input was wrong while the guard itself looked correct. A learned input
to a safety gate is exactly that risk with extra steps.

════════════════════════════════════════════════════════════════════
§4 — THE METHOD YOU MUST USE: SHADOW FIRST
════════════════════════════════════════════════════════════════════
Do NOT wire a learned value straight into a live decision. Do this instead:

 1. Pick ONE decision. Justify the pick with evidence, not taste. Candidates,
    with what is already known about each:
      · protective_override action — the only neural path that changes
        behaviour today. Highest value, highest risk, covered by §3.
      · governor epoch length — already reads pressure; `governor_epoch.py`.
      · the nudge/digest cadence — which of the 6 beats fires, and when.
      · model_router tier choice — `TASK_TIERS` is static today.
    A decision nobody can observe is not a decision; if you cannot name the
    file:line that acts on it, pick another.

 2. Compute BOTH: the existing fixed outcome, and the learned-augmented one.
    Act on the fixed one. Log both, with the inputs, to an append-only stream
    (suggest `state/neural/shadow-decisions.jsonl`).

 3. Define the scoring rule BEFORE you collect data, and write it into the file
    header. What would make the learned version *better*? Fewer false halts?
    Earlier true halts? Name the metric and the threshold that would convince
    you, and the one that would convince you it is WORSE.

 4. Register a prediction with a clock time before you look at results. On
    2026-07-26 a cadence bug was found only because someone wrote "if X does not
    exist by 14:13, my wiring is wrong" and honoured it.

 5. Report the comparison. Only if the learned version wins by your own
    pre-registered rule do you propose wiring it — and even then, behind a new
    default-off flag, with the §3 assertion in place.

════════════════════════════════════════════════════════════════════
§5 — THE HONEST OBSTACLE YOU WILL HIT
════════════════════════════════════════════════════════════════════
`OCTOPUS_HEBBIAN_RICH` is OFF, so the rich vocabulary has produced ZERO data.
And with deviation-only signals, a healthy organism emits nothing — which is
correct behaviour and also means a calm week produces an empty table.

So before anything else, answer: **how long until there is enough data to judge?**
Look at the historical stress/error/budget series already on disk
(`state/cortex/stress-latest.json`, `governor-alerts.md`, `state/cardiac-*`)
and estimate the deviation rate. If the honest answer is "at this event rate the
table needs six weeks", say that plainly — that is a finding, and it changes the
whole plan. Do not fabricate a shorter horizon to have something to ship.

If the rate is too low, the correct deliverable may be a REPLAY: feed the
historical series through `_hebbian_signals()` offline and build the table from
data that already exists. That is legitimate and much faster. It is also the
only way to get a baseline without waiting.

**THE REPLAY TRAP.** `_hebbian_signals()` now emits a deviation-only vocabulary,
but every historical series on disk was recorded while the OLD two-word
vocabulary was running. Replaying old raw sensors through the new function
produces signals that were **never actually emitted** — it reconstructs a
counterfactual past, not a measured one. The underlying sensor readings are real;
the signals derived from them are not history.
If you do it, label the output **synthetic-by-replay, not measured**, everywhere
it appears, and list it in §4 of your report (could-not-determine). A
counterfactual baseline is useful for sizing and useless as evidence that the
learned decision was better — do not let it cross that line.

**AND THE OBVIOUS ALTERNATIVE IS EMPTY.** "Just count data written after commit
e7f7d42" yields exactly zero rows: `OCTOPUS_HEBBIAN_RICH` is absent from
flags.cmd **and** absent from `wiring.PAPER_FULL_FLAGS` (VERIFIED 2026-07-26),
so unlike the neural flags its absence really does mean off, and the rich
vocabulary has never run. There is no post-commit data and there will be none
until someone arms that flag and the organism restarts.
So your honest options are exactly three, and you must state which you chose:
  (a) ask the owner to arm OCTOPUS_HEBBIAN_RICH, restart, and wait — real data,
      slow, and the horizon is what §5 asks you to estimate
  (b) replay, clearly labelled synthetic-by-replay — fast, sizing only
  (c) both, kept strictly separate and never pooled into one number

**ONE MORE LIVE DATUM YOU SHOULD KNOW.** As of 19:30 on 2026-07-26,
`neural/hebbian.json` is being REWRITTEN every tick while `co_occurrences` stays
frozen at 2235. That is `decay()` running: even the OLD two-word vocabulary is
emitting nothing right now, because the organism is currently neither
rhythm GREEN nor sigma<0.8. A fresh mtime is not evidence of learning. Check the
counter, not the timestamp — the same mistake in a smaller costume.

════════════════════════════════════════════════════════════════════
§6 — GOTCHAS THAT COST REAL TIME. Read or repeat them.
════════════════════════════════════════════════════════════════════
· flags.cmd is `source`d at process BOOT. Editing it changes NOTHING until a
  restart. Compare `state/ORGANISM-STATE.code.booted` against the file mtime
  before ever claiming a flag is live.
· Python does not source flags.cmd. Parse it yourself:
  `re.findall(r'^\s*set\s+(\w+)=(.*)$', raw, re.M)`.
· Checking a flag by PRESENCE is not checking its VALUE — and in this repo,
  absence may mean ON via the profile (§2). Check both.
· `python -m pytest tests/test_x.py` collects ZERO tests and exits 0 — a
  guaranteed false green. Run files directly and read the exit code.
· Test function prefixes are NOT uniform: most files use `t_*`,
  test_llm_intent.py uses `test_*`. Wrong prefix = never collected, still green.
· `_ops/tests/test_tg_power.py` really creates `_ops/STOP-ORGANISM`. Running the
  full suite while the organism is up can put it to sleep. Skip it and say so.
· `code_autonomy.shadow_test` runs the full 327-file suite in a worktree and
  exceeded 500s on 2026-07-26; when killed, its `finally` never ran and a git
  worktree LEAKED into %TEMP%. Check `git worktree list` before and after.
· ANTIVIRUS locks .git/objects — `git add` and `git commit` fail with
  "Permission denied". Retry in a loop up to ~6 times.
· Never rewrite a .bat that is currently executing: cmd.exe reads it by byte
  offset. Two are still LF-damaged and deliberately untouched for that reason:
  RUN-CORTEX.bat, telegram_center/RUN-TG-CENTER.bat.
· The local brain enforces OLLAMA_MIN_INTERVAL_S = 20s live. Two rapid calls
  make the second look like a dead brain. It is not.
· `model_router.ask(task, prompt, ...)` — task is the FIRST positional arg.
  Paid tier (sakana/fugu) works, 2.3-22s, cost_usd=0 on a flat plan.

════════════════════════════════════════════════════════════════════
§7 — WHAT TO HAND BACK
════════════════════════════════════════════════════════════════════
One markdown file at `_ops/_agent_reports/LEARNING-USEFUL-<date>.md`:

 1. The decision you picked and the file:line that acts on it.
 2. Your pre-registered scoring rule, verbatim, with its timestamp.
 3. The shadow comparison: how many decisions, how often they differed, and
    which was better by your own rule.
 4. Your verdict — including "the learned version was not better", which is a
    complete result, not a failure.
 5. What you could NOT determine. Required section.
 6. Every prediction you registered and its outcome, including refuted ones.

Label every claim VERIFIED / SAYS / INFERRED / NOT VERIFIED. Absence of an error
is not a pass — get an exit code or an explicit count. When something is silent,
feed it a synthetic input to prove it CAN speak before reading silence as health.

YOUR DELIVERABLE IS EVIDENCE, NOT A WIRE. Ship the wire only if the evidence
earns it.
```

---

## چرا این پرامپت این شکل است

**شادو-اول** تنها روشِ صادقانه است: مقایسه با فرمولِ ثابت قبل از جایگزینی، با
قاعدهٔ امتیازدهیِ **پیش‌ثبت‌شده**. وگرنه هر نتیجه‌ای بعداً توجیه می‌شود.

**ناوردیِ ایمنی** (§۳) غیرقابلِ‌مذاکره است: مقدارِ یادگرفته فقط می‌تواند
**احتیاط را بالا ببرد**. هرچه امروز شکست، به این دلیل بود که ورودیِ یک گارد غلط
بود درحالی‌که خودِ گارد درست به نظر می‌رسید. وزنِ یادگرفته روی یک گیتِ ایمنی
همان ریسک است با قدم‌های بیشتر.

**§۵ مانعِ واقعی را از قبل می‌گوید**: با سیگنالِ انحراف-محور، هفتهٔ آرام یعنی
جدولِ خالی. اگر جوابِ صادقانه «شش هفته طول می‌کشد» باشد، همان یافته است — و
راهِ درستش replayِ سریِ تاریخیِ روی دیسک است، نه انتظار.

