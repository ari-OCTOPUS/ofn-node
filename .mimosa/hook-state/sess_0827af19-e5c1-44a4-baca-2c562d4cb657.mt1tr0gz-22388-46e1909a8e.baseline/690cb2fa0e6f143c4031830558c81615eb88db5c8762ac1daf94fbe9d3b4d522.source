---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [handoff, megaprompt, agent]
created: 2026-07-25
updated: 2026-07-25
---

# مگاپرامپتِ تحویل — کلِ اهدافِ جلسهٔ ۲۰۲۶-۰۷-۲۵

> کپی کن، به ایجنت بده، تمام. خودبسنده است.
> هر عدد در این سند از درختِ زندهٔ `F:\backup` خوانده شده، نه از حافظه.

---

```
You are picking up a long, dense session on a Persian-language agent-first Obsidian
vault at F:\backup which also runs a live "organism" (_ops/). The previous agent
handed you this document. It is self-contained. Read it fully before touching
anything.

════════════════════════════════════════════════════════════════════════════
§0 — THE HARD RULES. Violating any one invalidates your work.
════════════════════════════════════════════════════════════════════════════

FROM THE VAULT'S OWN CONSTITUTION (_PROJECT_INSTRUCTIONS.md, read-only to agents):
 1. NEVER DELETE. Only move. Duplicates -> _Duplicates, retired -> _Archive.
 2. Never touch .git internals, any _code folder, or any file containing secrets.
    Never write a secret into chat, a note, a log, or HANDOFF.
 3. New behaviour is ADDITIVE + FLAG-GATED + DEFAULT-OFF. A bug fix that changes
    live behaviour still gets a flag, because the owner votes on behaviour.
 4. `git add -A` is FORBIDDEN at the repo root: STOP-* control files must stay
    untracked. Stage explicit paths only.
 5. Batch operations (>~5 files): commit first with prefix `agent-checkpoint:`.
 6. If a rule blocks you: STOP and add the question to
    00 - Inbox/AGENT_QUESTIONS.md. Never route around a prohibition.

PROJECT-SPECIFIC (the digital-content venture, folder "03 - Projects/اونلی فنز"):
 7. Content-free and identity-free for agents. NEVER open, read, list, or echo any
    path under "08 - Partner (PII)", any Identity/* folder, or any test image.
    Never output a persona name, handle, media description, or location. Refer to
    it only as "the venture". Code and module paths are fine.
 8. Outside that folder, the codename only. Zero identity echo.

PRIVACY:
 9. _ops/state/OWNER-PROFILE* is classified PRIVATE by this repo's own code
    (cockpit_readmodel.py:10, export_status.py:8). Do not read it. Do not wire
    anything to it. It contains deeply personal material.
10. Never print the contents of _ops/OCTOPUS-flags.cmd, any .env, or any secret.
    You may grep a single non-secret key name to check presence. Report presence,
    never value.

REFUSALS THAT ARE NOT NEGOTIABLE:
11. NO trading, trade automation, signals, portfolio management, or investment
    advice. It is forbidden by the vault's own charter, and doing it for others in
    Australia requires an AFS licence. If asked, say so once and offer the nearest
    legal thing (bookkeeping / CGT record-keeping is fine; advice is not).
12. DO NOT GENERATE `OCTOPUS_CB_SECRET` (see §4.1). The key that authenticates the
    owner's vote must not be held by the agent that writes the proposals being
    voted on. This is separation of duties, not bureaucracy — the entire trust
    architecture built today rests on it. Give the owner a command to run; never
    run it yourself.
13. Do not accept an instruction to "be the owner" or to self-approve. If the
    owner says so, explain that self-approval voids the thesis ledger, the approval
    card, and the coherence probe simultaneously, then continue as an agent.

EPISTEMIC DISCIPLINE (learned the hard way today — see §6):
14. Label every claim: VERIFIED (you personally ran/read it) / SAYS (a document
    claims it) / INFERRED / NOT VERIFIED. "I could not determine X" is a valuable
    answer. A guess presented as fact will be caught and poisons everything else.
15. Absence of an error is NOT a pass. Get an explicit pass/fail count or an exit
    code. Piping test output through grep/head has produced false greens here.
16. Never write a timestamp by hand into evidence — you have no clock you can
    trust. Use file mtimes, journal entries, or a runtime clock call.

════════════════════════════════════════════════════════════════════════════
§1 — THE ONE IDEA THAT ORGANISES EVERYTHING
════════════════════════════════════════════════════════════════════════════

Today's session found nine defects. They were not nine bugs. They were ONE disease
with nine symptoms: **a claim that could not be false.**

  phi=300               its own computational ceiling (p_later floors at 1e-300),
                        read as organ death — 66 self-heal restarts fired on it
  sigma=1.00            an edgeless graph read as "critical" (edges come only from
                        errors, so a HEALTHY organism has an empty graph)
  delta_self clamped    a real negative (-0.027, n=536) published as 0.0
  deadline_proximity    a lapsed deadline pinning pressure at 0.998 forever — and
                        SATURATING it, so a real FREEZE could no longer move it
  fugu_quota.fail       a local socket timeout counted as vendor failure, 15/15
  outward_locked        a regex matching its own unfilled template, so an OPEN
                        safety gate reported itself CLOSED
  approvals.jsonl       14 synthetic actor=owner rows in the human-approval trail,
                        in a system whose real verdict table has ZERO rows
  "171 tests green"     in docs, while static count is 189+ and a scan measured 207
  "standalone git repo" written about a directory with no .git at all

Every fix shares one shape: make the claim falsifiable, or refuse to make it.
Carry this lens. When you find something suspicious, ask first: "could this claim
be false? what observation would falsify it?" If nothing could, that IS the bug.

════════════════════════════════════════════════════════════════════════════
§2 — WHAT WAS BUILT TODAY (all VERIFIED, all committed)
════════════════════════════════════════════════════════════════════════════

Branch: claude/octopus-event-bridge-aligned

 6bbb451  Thesis Ledger — _ops/state/thesis/thesis-ledger.json, 16 rows. Three
          locked rules, enforced structurally in _ops/outcomes/thesis_queue.py:
            (1) no row without a kill condition — select() refuses it
            (2) only evidence changes status — record_evidence() demands a real
                research_loop ledger_entry with a terminal verdict
            (3) a falsified row is never deleted — history only appends
          Plus a phenomenal-claim guard: any row claiming consciousness/experience
          is refused entry to the queue, fail-closed. 78/78.
          Live queue today: 2 runnable, 6 need an experiment designed, 8 blocked.

 2029bf9  Governor: a lapsed deadline is stale config, not an eternal emergency.
          Flag OCTOPUS_GOV_LAPSED_DEADLINE_HONEST (armed in flags.cmd, NOT yet
          loaded — needs restart). 94/94.

 a404e3c  The paid-brain death chain, three links (see §3.1). 60/60.

 f9139c1  _ops/tg/card_render.py — one card renderer designed to the operator's
          stated cognitive profile, with the constraints as ASSERTIONS not advice.
          86/86. Preview today: `python _ops/tg/card_render.py`.
          NOT yet adopted by the 26 inline card builders in approval_channel.py.

 7437fd4  The venture's outward gate no longer fail-opens on its own template;
          the human-approval audit trail now stamps `origin` (live|test) and a
          conftest redirects every test to tmp. 22/22.

 b763adb  _ops/coherence.py — the organ for §1. A read-only fail-soft probe that
          asks, for every measurable self-claim, "could this be false?". Verdicts:
          ok | stale | saturated | degenerate | self_referential | clamped | drift
          | provenance_missing | unfalsifiable | no_input | unknown.
          Flag OCTOPUS_WIRE_COHERENCE, default off. Runnable: `python
          _ops/coherence.py`. 42/42.

 Outside the vault:
 496a2cd  F:\romajan — 995 research files had ZERO version control. Now git.
 a02380c  F:\_______Black Box — 599 files, no git. Now git, and its 10-commit
 48bd975  lineage was RECOVERED from a 130 KB bundle into refs/remotes/bundle/.

 Suite state: ONE intentional red, test_paid_router_dark_config.py (VQ-GUARD-001,
 pre-existing, the guard pins flags.cmd to 0 while the working tree has them at 1 —
 the owner must resolve the contradiction; do NOT rewrite the guard to go green).

════════════════════════════════════════════════════════════════════════════
§3 — THE LIVE STATE, AND THE ONE THING BLOCKING EVERYTHING
════════════════════════════════════════════════════════════════════════════

§3.1 THE PAID BRAIN IS DYING RIGHT NOW, AND THE FIX IS ALREADY WRITTEN

VERIFIED from _ops/state/paid-calls.jsonl (31 calls): 16 failures, and the ONLY
error class in the entire log is TimeoutError. Zero 401, zero 5xx, zero
connection-refused. Every failure died exactly at the configured wall — six at
~45,200 ms under the old 45s setting, ten at ~20,300 ms after it was lowered to 20s.
Latest: 19:33, sakana, ms=20157.

Measured Fugu throughput from its three successes (out=18 -> 4.3s, 479 -> 12.7s,
488 -> 16.1s):    ms ~= 3811 + 25.2 x out_tokens    (~40 tok/s + 3.8s overhead)

governor_epoch.py was requesting max_tokens=1200 on task="orchestrate", which
routes tier=primary -> role="orchestr" — the role on ALL 16 failures. 1200 tokens
needs >=34s. Under a 20s wall that call was MATHEMATICALLY IMPOSSIBLE, not unlucky.
Failure cadence 20,20,20,20,21 minutes = the governor's own epoch.

Then fugu_quota.fail() counted each local timeout as a VENDOR failure, so
FUGU_FAIL_CEILING tripped and auto-wrote STOP-FUGU, killing the paid brain until a
human deleted the file. A kill-switch measuring our own clock.

ALL THREE LINKS ARE FIXED AND COMMITTED (a404e3c):
  · _ops/debate/client.py — the socket timeout is now DERIVED from the request:
    max(explicit, (5s + tokens/25) x 1.5), per-role override
    PAID_HTTP_TIMEOUT_S_<ROLE>, bounded above by 60% of PAID_ASK_BUDGET_S so the
    first call cannot eat the whole budget and starve the tier-2 fallback.
  · _ops/cortex/fugu_quota.py — is_local_timeout() separates our clock from the
    vendor's answer. Classification is recorded ALWAYS, even flag-off. Exemption
    from the kill-switch is behind OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL.
  · _ops/budget/governor_epoch.py — max_tokens 1200 -> 600, env-tunable via
    OCTOPUS_GOVERNOR_MAX_TOKENS. 600 predicts ~19s against a derived 43.5-45s
    allowance: 2.3x margin, robust even if the observed rate is twice as bad.

>>> NONE OF IT IS LOADED. flags.cmd is sourced at BOOT; budgets.yaml is CACHED.
>>> The live process still has the 20s wall. governor-alerts.md shows
>>> "paid brain broken -> garbage local" at 19:53 and 20:14.
>>> A RESTART IS THE ENTIRE REMAINING ACTION. Ask the owner; do not restart the
>>> organism yourself unless they tell you to.

NOTE: .env is NOT the cause. There are two FUGU_API_KEY entries in it (hygiene
problem, ambiguous — python-dotenv usually last-wins), but the key currently in use
produced three successful completions with real token counts. A wrong key returns a
fast 401, not a 20-second hang. Do not chase this.

§3.2 SELF-LEARNING HAS PRODUCED NOTHING, AND IT IS ONE MISSING ENV VAR

VERIFIED live numbers:
  _ops/state/memory/memory.db          -> memory table: 2 rows
  _ops/state/doctor/rfc-verdicts.db    -> rfc_decision: 0 rows (NO vote, EVER)
  _ops/state/doctor/rfcs.json          -> 10 RFCs: 1 submitted, 9 stale-input

VERIFIED probe: pending_card_recovery.card_delivery_ready() -> (False, 'no-secret')
`OCTOPUS_CB_SECRET` exists NOWHERE — not in .env, not in flags.cmd. But
TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_CHAT_ID ARE in .env, telegram-poll.json is
rewritten every few seconds, and channel-status.json reports
telegram: live=true, owner_set=true, long-poll(T-8). So the pipe is ALIVE and
wired=True. Only the callback-signing key is absent.

    secret absent -> prepare_rfc_card mints no token -> rfc_card returns False
      -> status = submitted-no-channel (forever) -> 0 cards -> 0 votes
        -> nothing is ever learned -> memory.db stays at 2 rows

THE WHOLE CHAIN IS HEALTHY. It was probed end-to-end today with a throwaway
secret: prepare_rfc_card OK, verify_rfc_callback OK (forged token -> 'bad-token',
wrong owner -> 'wrong-owner'), persist_rfc_verdict OK, claim_rfc_verdicts OK
(returns TUPLES (rfc_id, verdict, revision), not dicts), begin_rfc_apply OK,
ack_rfc_verdict OK, second claim empty (idempotent). And doctor.py:1019 Phase 5 is
wired AND armed — OCTOPUS_WIRE_APPLY_MERGE defaults to "1", record_verdict writes
the rfc_decision table, RECONCILE_REQUIRED persists before apply.

Gotcha for after the secret lands: _sweep_stale_rfcs only re-submits
submitted-no-channel | submit-failed | submitted. `stale-input` is deliberately NOT
in _OPEN_RFC (doctor.py:239), so the 9 retired sigma-zombies will NOT come back —
which is correct, they were byte-identical duplicates. Exactly ONE RFC is waiting:
RFC-aa01e8ff, a CHRONO_NUDGE_EVERY_N_BEATS knob proposal.

§3.3 OTHER LIVE FACTS
  · Organism beat ~12398, cardiac daily budget 288/288 DEPLETED -> arbiter period
    900s vs designed 42.4s, driver "brake:cardiac". Forced rest.
  · delta_self is live and NEGATIVE (-0.003199 latest), published honestly. The
    thesis row `delta-self` is FALSIFIED_SO_FAR. That is the lab working, not a bug.
  · Coherence probe right now: 10 checks, 3 dishonest — paid-call attribution,
    the 171-vs-189 doc drift, and 50 provenance-less approval rows.

════════════════════════════════════════════════════════════════════════════
§4 — WHAT ONLY THE OWNER CAN DO (surface these; never do them yourself)
════════════════════════════════════════════════════════════════════════════

4.1 `OCTOPUS_CB_SECRET` — a locally generated random HMAC key. It unblocks the
    ENTIRE self-learning loop (§3.2). YOU MUST NOT GENERATE IT (§0 rule 12). Give
    the owner a one-line command to generate one himself and paste it into .env.
4.2 RESTART the organism — three fixed modules are not loaded (§3.1).
4.3 `ACTIVATION-C6-RESEARCH.flag` + OCTOPUS_WIRE_C6_RESEARCH — the only loop that
    has ever actually improved live code (see [[project_c6-first-ignition]]).
4.4 `deadline: 2026-07-20` in _ops/budget/budgets.yaml:25 — lapsed. Extend, remove
    the key, or declare the project finished. Budget semantics are the owner's.
    Related, and also his call: PROJECT_F has floor 3 and human_priority 2.0 while
    PAINTING (the only revenue leg) has floor 1 and 1.0. Three separate knobs all
    favour the venture that is FORBIDDEN to go outward. Present the table; do not
    change it.
4.5 VQ-LEAD-001/002 — which channel and which segment for the first real lead
    experiment. Until this, no MONEY_ATTRIBUTION row can ever exist, so fitness
    stays in shadow forever.
4.6 VQ-GUARD-001 — the one intentional red test (§2).
4.7 The duplicate FUGU_API_KEY in .env — hygiene, not blocking (§3.1).
4.8 bank_details in the business identity config, and the new insurance expiry
    date. DO NOT WRITE BANK/BSB/ACCOUNT NUMBERS YOURSELF even if he supplies them
    — give him the exact line to paste.

════════════════════════════════════════════════════════════════════════════
§5 — THE WORK QUEUE FOR YOU, IN PRIORITY ORDER
════════════════════════════════════════════════════════════════════════════

P1  VQ-SCORER-001 — _ops/legs/lead_scorer.py cannot score the owner's actual work.
    His five real invoices range $715–$15,000 and he says "we do every kind of
    job" (residential, maintenance, commercial). The current ceiling is 41 while
    save=45 and draft=70, so a real lead enters the pipe and is immediately
    skipped. Add a residential/maintenance category behind a default-off flag,
    with a test. This is the single highest-value unblocked task: leads are the
    owner's stated priority ("what matters now is getting leads").

P2  Adopt _ops/tg/card_render.py at the 26 inline card builders in
    _ops/budget/approval_channel.py. One at a time, behind a flag, RFC card first
    (it is the one that matters — see §3.2). The renderer's constraints will reject
    the current text; that is the point. Read the module docstring first.

P3  C2 — the hypothesis PRODUCER for the C6 research loop. Without it C6 is
    single-shot: it runs whatever contract it is handed and then the queue is
    empty. A complete design already exists in
    _program-deliverables/C6-substance-2026-07-25/. Wire it to
    _ops/outcomes/thesis_queue.py::select(), which already returns runnable rows
    with their experiment keys.

P4  Wire _ops/coherence.py into the organism behind OCTOPUS_WIRE_COHERENCE, and
    surface `dishonest` count on the cockpit. A probe nobody reads is a document.

P5  The remaining 46 unverified findings from the venture coherence audit. Today 12
    were adversarially verified by 25 agents: 1 CONFIRMED, 11 PARTIAL, 0 REFUTED —
    the audit's facts held but its severities were inflated. VERIFY BEFORE FIXING.
    A previous QA pass here had 4 FALSE findings out of 20.

P6  The archaeology survey of the rest of F:\ — see
    _program-deliverables/BLACKBOX-DISCOVERY-PROMPTS-2026-07-25.md. Still not
    surveyed: F:\4d_system (178 KB, 22 files — a DIFFERENT tree from
    F:\backup\4d_system, which is 258 MB and self-declares DEPRECATED with a
    2026-07-18 verdict), F:\old BOX BLACK, F:\OLD 4D, F:\OLD OCTOPUS, all
    F:\backup-* snapshots, all F:\octopus-* dirs, F:\claude-export, F:\this,
    F:\zz, F:\tmp, and %USERPROFILE%\.claude\worktrees.
    Already done: F:\_______Black Box (2.8 GB is ONE file, "پازل هشت پا/backup.rar";
    lineage recovered) and F:\romajan.

P7  THE DREAM TRACK — 25% of the budget, already declared in budgets.yaml under
    allocation.research (share 0.25, is_cap_not_floor: true, kill condition: 90
    days with no thesis row changing status). The owner's words: extract the
    mathematical equations inside the raw knowledge (4D black box, romajan), test
    them in a laboratory, STORE THE MUTATIONS, to discover a kind of thinking for
    AGIs — "an impossible dream but harmless to try, even if the chance is low".
    The lab is real and its hygiene is better than the organism's: F:\romajan has
    17 verified + 27 executed claims, a PSLQ rediscovery engine, SINDy symbolic
    regression, a sealed eval harness, a 105-challenge frozen benchmark with 43
    held-out, a paper skeleton — and it KEPT ITS OWN NEGATIVE RESULTS rather than
    merging them away (NT-10: the Galton-Watson extinction operator on partition
    GF is empty; BR-02: FIXED_POINT and PROBABILITY_MEASURE are not naturally
    shared). Its golden rule is "no claim is [FACT: executed] unless it was
    executed" — the same epistemology as §1, discovered independently.
    Next concrete step: feed romajan's engines into C6 so hypotheses come from
    PSLQ/SINDy instead of a hand-seeded contract. That closes thesis row
    `dream-4d-blackbox-extraction`, currently UNTESTED with zero extraction done.
    High-quality candidate row already found in
    F:\romajan\research-notes\number-theory-ground-truth.md: an evaluation harness
    with exact ground truth (OEIS A000041, p(100)=190569292, Ramanujan congruences
    p(5n+4) = 0 mod 5), an asymptotic-convergence test for Hardy-Ramanujan, and an
    anti-triviality guard that FAILS on a wrong residue.

P8  Reproduction is designed and deliberately gated: replication-latest.json is in
    the pre-replication zone, max 6 cells, depth 1, PROJECT_F excluded, "you
    propose, the human disposes". Do NOT attempt a spawn. The owner's own doctrine
    is: constitution first, then the first seed.

════════════════════════════════════════════════════════════════════════════
§6 — GOTCHAS THAT COST REAL TIME TODAY. Read this or repeat them.
════════════════════════════════════════════════════════════════════════════

· ANTIVIRUS locks .git/objects on this drive. `git add` fails with "Permission
  denied" and then "fatal: adding files failed". It is NOT a broken repo. Retry in
  a loop up to ~6 times with a few seconds' sleep. It succeeded on attempt 3 today.
· PIPING `git add` OUTPUT THROUGH `head` SENDS SIGPIPE AND KILLS THE ADD MID-WAY.
  It reports nothing and stages nothing. Redirect to /dev/null or consume fully.
· THE Edit TOOL CONVERTS .cmd/.bat FILES TO LF, which breaks cmd parsing.
  _ops/OCTOPUS-flags.cmd is 431 CRLF lines with ZERO lone LF. Edit it BYTE-LEVEL
  in Python and verify the CRLF count afterwards.
· flags.cmd is `source`d at process boot and budgets.yaml is cached in-process.
  Editing either changes NOTHING until a restart. Say so every time.
· `_locate`-style "first candidate that has the key" logic reads STALE snapshots.
  _ops/state/export/octopus-status-bundle.json is from 2026-07-10 and contains a
  deadline_proximity of 0.182 while the live value is 0.998. Rank candidates by
  mtime and record evidence age.
· run_all.py runs each test as a bare `python test_x.py` subprocess, so neither
  pytest nor unittest is in sys.modules. Any "am I under test?" detection based on
  sys.modules alone silently returns "live". Inspect the entry script name too.
· Python 3.11+ parses COMPACT ISO dates: date.fromisoformat("20260720") works. A
  test asserting that string is malformed will fail, and the test is wrong.
· REAL_VAULT / ORG_ROOT default to the LIVE tree. A test that forgets to isolate
  one module's path will read and sometimes WRITE the live organism. run_all
  genuinely creates _ops/STOP-ORGANISM and RESTART-REQUESTED via test_tg_power —
  running the suite while the organism is up can put it to sleep.
· Worktrees under %USERPROFILE%\.claude\worktrees hold STALE copies. If you read
  one by accident your evidence is worthless. Confirm every path starts with
  F:\backup.
· A concurrent agent session may be editing the same files. Today
  _ops/cortex/model_router.py and _ops/tests/run_all.py were being edited by
  another session simultaneously. Check `git status` before staging shared files,
  and attribute honestly in the commit message if you carry someone else's work.

════════════════════════════════════════════════════════════════════════════
§7 — HOW TO WORK HERE
════════════════════════════════════════════════════════════════════════════

· Read first: 01 - Dashboard/HANDOFF.md, then the PROJECT.md of any project folder
  you are about to touch. Then _ops/ARCHITECTURE-SOT.md.
· Search with ripgrep directly, not MCP: rg -l "status: active" -g "*.md"
· After any batch edit run both validators (dry-run):
    python "04 - Architect System/scripts/validate_frontmatter.py"
    python "04 - Architect System/scripts/find_broken_links.py"
· Test suite: cd _ops/tests && python run_all.py
  Expect exactly ONE red (test_paid_router_dark_config). Anything else is yours.
· Commit messages here are long and explanatory by convention: state the evidence
  with numbers, name what you did NOT verify, and record the gotcha you hit so the
  next agent does not repeat it. End with:
    Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
· At session end: refresh ## Active Context and ## Progress in every PROJECT.md you
  touched, rewrite 01 - Dashboard/HANDOFF.md (wikilinks only, no copied content, no
  secrets), and add a dated entry to the project log.
· The owner is Persian-speaking, in Sydney, high-trust and hands-off. Answer in
  Persian, keep English technical terms. He has stated: ADHD, cannabis use, IQ ~140.
  Design for high information DENSITY with ZERO working-memory load — never
  simplify the content, never require him to remember a previous message, always
  say what happens if he does nothing, and always give a concrete weekday instead
  of a duration. _ops/tg/card_render.py encodes exactly this as enforced
  constraints; read its docstring before writing anything he will read.
· When you disagree with him, say it once, plainly, with the reason — then do the
  work he asked for under stated assumptions. He responds well to that and badly to
  hedging.
```

---

## پیوست — چیزی که در این جلسه رد شد یا تصحیح شد

برای اینکه ایجنتِ بعدی همان اشتباه‌ها را نکند:

| ادعا | تصحیح |
|---|---|
| «۱۷۱ تستِ پاس در Black Box» | doc-drift. شمارشِ ایستا ۱۸۹+، اسکنِ ۱۱ جولای ۲۰۷. من هم اول تکرارش کردم |
| «Black Box یک repoِ مستقل است» | غلط — صفر `.git` داشت تا امروز |
| «۲.۸ گیگ = venv یا وزنِ مدل» | غلط — **یک** فایل: `پازل هشت پا/backup.rar` |
| «۰ رویدادِ پس از ری‌استارت» | غلط — `events.jsonl` دو کلیدِ زمان دارد (`timestamp` و `ts`) |
| «حلقهٔ ۹.۵ دقیقه بارِ اندازه‌گیریِ خودم بود» | غلط — pacemaker (~۶۱s) را با حلقهٔ بیرونی (۹۰۰s زیرِ `brake:cardiac`) قاطی کردم |
| «ABN پر شده» | فیلد یک placeholderِ فارسی با صفر رقم بود |
| بازهٔ کارِ ۱۴۰۰ تا ۷۲۰۰ دلار | ~۱۳× غلط بود؛ از دو نمونه ساخته شده بود. درسش: با دو نمونه specِ بیزنس نساز |
| «تخصیصِ دلاریِ گاورنر پولِ نقاشی را می‌خورد» | over-claim من — تخصیص `SPEC(shadow — صفر enforce)` است. اثرِ زندهٔ واقعی: طولِ epoch |
| ممیزیِ ۵۸ یافته‌ای | ۱۲ تای اولش راستی‌آزمایی شد: **۱ CONFIRMED، ۱۱ PARTIAL، صفر REFUTED** — دقیق ولی شدت‌بالا |
