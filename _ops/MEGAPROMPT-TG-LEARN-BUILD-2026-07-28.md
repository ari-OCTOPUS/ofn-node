---
type: deliverable
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [handoff, megaprompt, agent, telegram, learning-loop, code-autonomy]
created: 2026-07-28
updated: 2026-07-28
supersedes_partially: "MEGAPROMPT 2026-07-25 §3.1, §3.2, §4.3, P4"
---

# مگاپرامپت — تلگرام به‌عنوانِ اندامِ کاملِ «یاد بگیر و بساز»

> کپی کن، به ایجنت بده، تمام. خودبسنده است.
> مأموریت در یک جمله: **تلگرام تنها سطحی شود که ارگانیسم از آن یاد می‌گیرد و
> از آن کد می‌سازد — یکدست، قابلِ ابطال، و بدونِ هیچ سکوتِ مبهم.**
>
> ⚠️ این سند در جلسه‌ای نوشته شد که `device_bash` نداشت: هیچ تستی، هیچ `git`ی و
> هیچ پروبِ شبکه‌ای اجرا نشد. هر عدد یا از خواندنِ مستقیمِ فایل آمده (`VERIFIED`)
> یا صریحاً `NOT VERIFIED` علامت خورده. §0.5 را قبل از هر کاری بخوان.

---

```
════════════════════════════════════════════════════════════════════════════
§0 — THE HARD RULES. Violating any one invalidates your work.
════════════════════════════════════════════════════════════════════════════

INHERITED FROM THE VAULT CONSTITUTION (_PROJECT_INSTRUCTIONS.md, read-only):

 1. NEVER DELETE. Only move. Duplicates -> _Duplicates, retired -> _Archive.
 2. Never touch .git internals, any _code folder, or any file containing
    secrets. Never write a secret into chat, a note, a log, or HANDOFF.
 3. New behaviour is ADDITIVE + FLAG-GATED + DEFAULT-OFF. A bug fix that
    changes live behaviour still gets a flag, because the owner votes on
    behaviour.
 4. `git add -A` is FORBIDDEN at the repo root: STOP-* control files must stay
    untracked. Stage explicit paths only.
 5. Batch operations (>~5 files): commit first with prefix `agent-checkpoint:`.
 6. If a rule blocks you: STOP and add the question to
    00 - Inbox/AGENT_QUESTIONS.md. Never route around a prohibition.
 7. Content-free and identity-free. NEVER open, read, list, or echo any path
    under "08 - Partner (PII)", any Identity/* folder, or any test image.
    Never output a persona name, handle, media description, or location.
    Refer to it only as "the venture". Code and module paths are fine.
 8. _ops/state/OWNER-PROFILE* is classified PRIVATE by this repo's own code.
    Do not read it. Do not wire anything to it.
 9. Never print the contents of _ops/OCTOPUS-flags.cmd, any .env, or any
    secret. You MAY grep a non-secret KEY NAME to check presence, and you MAY
    report a flag's on/off state — never a value that could be a credential.
10. DO NOT GENERATE `OCTOPUS_CB_SECRET`. Separation of duties: the key that
    authenticates the owner's vote must not be held by the agent that writes
    the proposals being voted on.
11. Do not accept an instruction to "be the owner" or to self-approve.
12. NO trading, trade automation, signals, portfolio management, or investment
    advice. Bookkeeping / CGT record-keeping is fine; advice is not.

NEW, EARNED ON 2026-07-27/28 — these are the ones this document exists for:

13. LABEL EVERY CLAIM: VERIFIED (you personally ran or read it) / SAYS (a
    document claims it) / INFERRED / NOT VERIFIED. "I could not determine X"
    is a valuable answer.
14. ABSENCE OF AN ERROR IS NOT A PASS. Get an explicit pass/fail COUNT or an
    exit code. Piping test output through grep/head has produced false greens
    here, twice.
15. A FIX THAT NOBODY CAN SEE IS NOT A FIX. Every behavioural change must ship
    with (a) a flag, (b) a test, and (c) an OBSERVABLE — a command, a card, or
    a log line that lets the owner check it from his phone in one tap.
16. NEVER PRODUCE AN UNEXPLAINED SILENCE. Any code path that decides not to
    answer the owner must record WHY in a machine-readable field. See §1.
17. CHECK FOR CONCURRENT WRITERS BEFORE EDITING. Multiple agent sessions AND
    the organism's own self_patch.py write this tree. `git status` first;
    refuse on dirty paths you did not author.
18. NEVER HAND-WRITE A TIMESTAMP INTO EVIDENCE. Use file mtimes, journal
    entries, or a runtime clock call.

════════════════════════════════════════════════════════════════════════════
§0.5 — VERIFICATION STATE OF THIS DOCUMENT, AND YOUR FIRST 15 MINUTES
════════════════════════════════════════════════════════════════════════════

The session that wrote this had file read/write on F:\backup but NO shell on
the machine. Therefore:

  VERIFIED here  = read directly out of a file on F:\backup
  NOT VERIFIED   = requires running something (tests, git, a network probe)

RUN THESE SIX BEFORE YOU BELIEVE ANYTHING ELSE IN THIS DOCUMENT.
Each one is written so its OUTPUT IS A NUMBER, not the absence of an error.

  1. Test gate baseline — the number every later claim rests on:
       cd _ops/tests && python run_all.py
     Record PASSED and FAILED as integers. Expect exactly ONE red
     (test_paid_router_dark_config, VQ-GUARD-001). Anything else is yours.
     If run_all.py does not print explicit counts, THAT IS BLIND SPOT #7 —
     fix it first (§3.7), because every other gate in this document depends
     on being able to read a real number here.

  2. Does the running center have the topic flag?
       python -c "import json;d=json.load(open(r'_ops/state/telegram/center-config.json'));print(d['last_offset'])"
     then, in Telegram, inside the 🦑system topic, send:  /now
     Reply lands in the topic  -> flag is LIVE.
     Reply lands in General    -> flag armed but NOT LOADED -> restart center.
     No reply anywhere         -> new problem; go to §3.1.
     Passive alternative (free): center fires autonomously ~every 10 min.
       Wait for the next stream=center row in _ops/state/tg-send-log.jsonl:
       topic non-null -> LIVE. topic null AFTER a confirmed restart -> the
       defect is in the free-form code path, not the env -> §6 fix-bug.
       Do not restart-loop.

  3. Has the owner EVER voted?
       python -c "import sqlite3;c=sqlite3.connect(r'_ops/state/doctor/rfc-verdicts.db');print(c.execute('select count(*) from rfc_decision').fetchone())"
     0 rows = the learning loop has never closed. Everything in §5 is theory.

  4. Is the card channel actually able to mint a token?
       python -c "import sys;sys.path.insert(0,r'_ops');from outcomes import pending_card_recovery as p;print(p.card_delivery_ready())"
     (False,'no-secret') = OCTOPUS_CB_SECRET missing -> §7.1, owner-only.

  5. Concurrent writers:
       git status --porcelain
     Non-empty = someone else is mid-flight. Read _ops/COMMIT-PATHS-*.txt and
     _ops/SESSION-*.md before touching anything listed there.

  6. Flag drift — armed vs loaded:
     There is currently NO way to answer this. That is BLIND SPOT #11 and it
     is the highest-leverage small fix in this document (§3.11). Until it
     exists, assume EVERY flag edited after the last process start is dead.

════════════════════════════════════════════════════════════════════════════
§1 — THE ONE IDEA, EXTENDED
════════════════════════════════════════════════════════════════════════════

The 2026-07-25 session found nine defects that were one disease: A CLAIM THAT
COULD NOT BE FALSE. phi at its own ceiling read as death. sigma=1.00 on an
edgeless graph. A regex matching its own unfilled template.

Tonight the same disease was found in the INTERFACE, and it is worse there,
because the owner is the instrument that was blinded:

   FROM THE OWNER'S PHONE, THESE THREE ARE BYTE-IDENTICAL:

     A. the message never reached the bot
     B. the bot answered, and the answer landed in a topic he isn't looking at
     C. the bot answered, and a quality guard discarded the answer silently

   All three render as: nothing happens.

Evidence (VERIFIED, _ops/state/telegram/ask-brain.jsonl, 2026-07-27):
   12:59:27  topic="lead"    ok=true   218 chars   -> case B
   13:06:15  topic="system"  ok=false  chars=5     -> case C  (`too-short-answer`)
   20:06:00  topic=""        ok=true   196 chars   -> worked
   20:10:32  topic=""        ok=true   387 chars   -> worked

Case C is the important one. The guard was RIGHT — a 5-character answer is
garbage. But it converted a correct refusal into an indistinguishable silence.
A guard that emits silence instead of a reason erases itself from observation.

CARRY THIS LENS. Before you fix anything, ask: "could this claim be false?
what observation would falsify it?" If the answer is nothing, THAT is the bug.
And its interface twin: "if this path fails, what does the owner SEE?" If the
answer is nothing, that is also the bug.

════════════════════════════════════════════════════════════════════════════
§2 — LIVE STATE, VERIFIED 2026-07-28 ~00:10 Sydney
════════════════════════════════════════════════════════════════════════════

TELEGRAM CENTER — _ops/state/telegram/center-config.json  (VERIFIED, read)
   chat_id              -1004475788460  (forum supergroup)
   topics               10 mapped: lead 22, ziman 23, mining 24, crypto 25,
                        accounting 26, studio_pf 27, system 28, knowledge 29,
                        cartographer 65, mirror 205
   commands_set         9
   last_offset          223883081   (was 223882986 at 09:58 -> +95 updates)
   status_message_id    66
   last_digest          9 legs all stamped 22:03:40; mirror 13:59:56

   => The pipe is ALIVE and consuming updates. The 2026-07-27 09:58 finding
      of "zero updates since restart" was a true snapshot and is now STALE.

PAID BRAIN — _ops/state/paid-calls.jsonl, 108 rows  (VERIFIED, parsed)
   ok / fail            91 / 17
   TimeoutError         16 — ALL of them dated 2026-07-25
   last failure of any  2026-07-27T15:59:16  RemoteDisconnected (real vendor)
   since then           17 consecutive successes
   latest               2026-07-28T00:06:12  ok  21815 ms  1200 tokens_out
   provider/model       sakana / fugu, subscription=max, cost_usd 0.0

   => The three-link death chain from the previous megaprompt §3.1 IS DEAD.
      Do not re-diagnose it. Do not "fix" it again.

   CORRECTED THROUGHPUT MODEL (VERIFIED, regression over all 91 successes):
      real     ms = 5393 + 12.54 * tokens_out      (~80 tok/s)
      previous ms = 3811 + 25.2  * tokens_out      (~40 tok/s, from 3 samples)
   The old fit OVER-PREDICTED latency by ~1.7x at 1200 tokens. The advice
   "lower max_tokens 1200 -> 600" rested on it. Live output reaches 1200
   tokens and completes in ~22 s against a 45 s wall.

FLAGS — _ops/OCTOPUS-flags.cmd  (VERIFIED by name+state only, no values echoed)
   OCTOPUS_TG_TOPIC_REPLY                  = 1
   OCTOPUS_GOV_LAPSED_DEADLINE_HONEST      = 1
   OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL  = 1
   OCTOPUS_WIRE_COHERENCE                  = 1
   OCTOPUS_WIRE_C6_RESEARCH                = 1
   OCTOPUS_WIRE_APPLY_MERGE                = 0     <-- SEE §3.4. THIS IS THE
                                                       LEARNING LOOP'S OFF SWITCH.
   PAID_HTTP_TIMEOUT_S                     = 45
   OCTOPUS_GOVERNOR_MAX_TOKENS             = absent (code default applies)
   OCTOPUS_TG_MERGED_DIGEST                = absent
   file hygiene: 646 CRLF, 0 lone-LF, 28144 bytes  (the §9 LF gotcha did NOT
   happen — keep it that way, edit this file byte-level in Python only)

TELEGRAM SEND LOG — _ops/state/tg-send-log.jsonl, 162 rows  (VERIFIED, parsed)
   schema               {ts, chat, topic, stream, chars, sha, ok}
   ok                   162 / 162 — the transport has never failed
   destinations         group -1004475788460: 107   private DM 6150431610: 55
   topic-addressed      59 of 107 group sends
   NOT topic-addressed  48 group sends, ALL stream=center, 59,456 chars,
                        2026-07-27 12:44:45 -> 2026-07-28 00:25:36
   => "The bot never answers me" and "the transport is broken" are BOTH false.
      The bot answers constantly. 48 of those answers are in the wrong room.
      See BS-2. This is the single most consequential VERIFIED finding tonight.

CENTER PROCESS AGE — _ops/state/tg-center-watchdog-log.txt (VERIFIED, 4 lines)
   2026-07-25T22:37:02  centre+loop both down - launching RUN-TG-CENTER.bat
   2026-07-26T09:32:05  centre+loop both down - launching RUN-TG-CENTER.bat
   2026-07-27T14:27:06  STOP-TG-CENTER present - not reviving centre
   2026-07-27T16:07:04  STOP-TG-CENTER present - not reviving centre
   => No launch since 2026-07-26. Any flag armed after that is not loaded.
      NOT VERIFIED: whether the centre was started manually afterwards
      (RUN-TG-CENTER.bat was MODIFIED 2026-07-27 12:39, which is not a run).

CODE — mtimes (VERIFIED). A CONCURRENT SESSION IS ACTIVE:
   _ops/initiative.py                  2026-07-28 ~00:06
   _ops/COMMIT-PATHS-2026-07-27.txt    2026-07-28 ~00:00   (68 paths, ~25 tests)
   _ops/telegram_center/center.py      2026-07-27 22:56:21 (130 KB)
   _ops/SESSION-2026-07-27-W1-W5.md    2026-07-27 ~23:40   (30 KB)
   _ops/self_patch.py                  2026-07-27 ~22:03
   _ops/capability_registry.py         2026-07-27 ~19:23

KEY CODE FACTS (VERIFIED by reading center.py / tg_api.py):
   tg_api.py:267    send(text, *, topic_id=None, keyboard=None, ...)
   tg_api.py:279    topic_id -> body["message_thread_id"]
   tg_api.py:296    every send is recorded via _ops/tg_send_log.py ->
                    _ops/state/tg-send-log.jsonl  (20958 bytes, live)
   center.py:92     TOPIC_REPLY_FLAG = "OCTOPUS_TG_TOPIC_REPLY"
   center.py:542    leg digest send uses topic_id=topics.get(leg)  [always]
   center.py:616    _topic_key(msg) -> which leg's topic the owner asked in
   center.py:636    _reply_thread(msg) -> None unless flag on AND
                    msg["is_topic_message"] is true (deliberately narrow)
   center.py:660    _is_owner: fail-closed allowlist
   center.py:705    OWNER_AUTH capture: records the owner's authorisation
                    text, ACKs it, and DOES NOT EXECUTE. Correct. See §3.15.

════════════════════════════════════════════════════════════════════════════
§3 — THE BLIND SPOTS. Sixteen. Each with a falsifying test.
════════════════════════════════════════════════════════════════════════════

Format: SYMPTOM / EVIDENCE / FALSIFYING TEST / FIX SHAPE / OWNER?

--- BS-1  THE THREE SILENCES ------------------------------------------ [P1]
SYMPTOM   Owner cannot distinguish "not received" / "answered elsewhere" /
          "answer discarded". All render as nothing.
EVIDENCE  ask-brain.jsonl 2026-07-27 (VERIFIED, see §1).
TEST      Invariant: over any 24 h window,
             count(inbound owner text messages)
               == count(outbound messages causally keyed to them)
          Nothing today emits the right-hand side. Build the counter first;
          the invariant is the deliverable, not the fix.
FIX       Every owner message gets exactly ONE reply, always. When the answer
          is withheld, send the REASON, not silence:
            "نتوانستم جواب بدهم — دلیل: too-short-answer. دوباره بپرس یا /live"
          Add `reply_reason` to the ask-brain schema. Flag:
          OCTOPUS_TG_NEVER_SILENT, default off.
OWNER?    No. Agent work. But the wording is owner-facing — read
          _ops/tg/card_render.py's docstring before writing any of it.

--- BS-2  THE TOPIC ASYMMETRY ----------------------------------------- [P1]
SYMPTOM   Digests arrive in the right topic; answers to the owner's own
          questions land in General.
EVIDENCE  **VERIFIED AT RUNTIME, WITH A NUMBER** — _ops/state/tg-send-log.jsonl,
          162 rows. Cross-tab of destination x topic x stream:

            where  topic?    stream       count
            DM     NO-topic  (unlabelled)   48     correct — DMs have no topic
            DM     NO-topic  center          7     correct
            GROUP  topic     center         18     correct (incl. the 9-leg
                                                   digest burst at 22:03:40)
            GROUP  topic     brain/doctor/heart/needs/discovery/cortisol  41
                                                   100% topic-addressed
            GROUP  NO-topic  center         48     <-- THESE LAND IN GENERAL

          48 messages, 59,456 characters, window 2026-07-27 12:44:45 ->
          2026-07-28 00:25:36, still firing roughly every 10 minutes.
          Every other stream in the system is 100% topic-addressed. The defect
          is confined to stream=center's group output — exactly the path that
          answers the owner.

          Process age: _ops/state/tg-center-watchdog-log.txt has FOUR lines and
          its last LAUNCH is 2026-07-26T09:32:05. (The 2026-07-27 session read
          this as "today 09:32" — it was a day earlier.) The other two lines are
          2026-07-27T14:27:06 and 16:07:04, both "STOP-TG-CENTER present - not
          reviving centre". flags.cmd was edited 2026-07-27 ~16:26. INFERRED:
          the live process predates the flag and cannot have loaded it.
TEST      §0.5 step 2 (one `/now` inside 🦑system). Then a static test:
          assert every `self._client.send(` inside a message-handling path
          passes `topic_id=self._reply_thread(msg)`. Grep-based test, cheap,
          and it prevents regression by construction.
FIX       Verify + restart if needed (runbook:
          _ops/RUNBOOK-TG-CENTER-RESTART.md). Then the static test. Then the
          INVARIANT so this can never silently regress: every send whose chat
          is the forum group MUST carry a topic, unless its stream is on an
          explicit, named exception list. Expose the counter on /trace:
          "group sends without topic, last 24 h" — expected 0. ok=True only
          proves Telegram accepted the message; this counter is what proves
          it landed in the right room. The 48-row window lived exactly in
          the gap between those two claims.
OWNER?    Restart is his call. The test and the invariant are yours.

--- BS-3  26 INLINE CARD BUILDERS, ONE UNUSED RENDERER ---------------- [P1]
SYMPTOM   _ops/tg/card_render.py exists with 86/86 tests and ZERO consumers.
          _ops/budget/approval_channel.py builds ~26 cards inline. Every card
          the owner votes on has slightly different shape, wording, and
          affordances. This is literally the "یکدست نیست" the owner named.
EVIDENCE  SAYS (previous megaprompt P2). Re-verify with:
             rg -n "def .*card|send\(" _ops/budget/approval_channel.py | wc -l
TEST      A test that enumerates card builders and asserts each one routes
          through card_render. Start it as a WARNING list, not a hard fail,
          so it can land before the migration.
FIX       Migrate ONE AT A TIME, behind a flag, RFC card FIRST (it is the one
          that unblocks §5). The renderer's constraints will REJECT the
          current text — that is the point, not a bug.
OWNER?    No.

--- BS-4  THE LEARNING LOOP'S OFF SWITCH ------------------------------ [P0]
SYMPTOM   Even a perfect vote changes nothing.
EVIDENCE  VERIFIED: OCTOPUS_WIRE_APPLY_MERGE = 0 in flags.cmd, while
          doctor.py's code default is "1". The explicit 0 wins. So the apply
          phase is OFF live.
TEST      grep the flag; then check `rfc_decision` row count (§0.5 step 3).
FIX       None available to you — this is a behaviour vote.
OWNER?    YES. §7.2. This is the single biggest blocker to "learn and build".

--- BS-5  THE RFC QUEUE CAN SILENTLY EMPTY ---------------------------- [P3]
SYMPTOM   `_sweep_stale_rfcs` only re-submits submitted-no-channel /
          submit-failed / submitted. `stale-input` is deliberately excluded.
          Correct (they were byte-identical duplicates) but it means the queue
          can reach zero and nothing announces it.
EVIDENCE  SAYS (previous megaprompt §3.2, doctor.py:239). NOT VERIFIED here.
TEST      A `queue_depth` observable: runnable / needs-experiment / blocked /
          awaiting-vote, surfaced on the cockpit AND as `/queue` in Telegram.
FIX       Emit the depth every beat; alert at zero. A queue nobody can count
          is an unfalsifiable claim of progress.
OWNER?    No.

--- BS-6  ZERO OWNER VOTES, EVER -------------------------------------- [P0]
SYMPTOM   rfc_decision had 0 rows as of 2026-07-25. The entire self-learning
          thesis rests on a table that has never been written to.
EVIDENCE  SAYS. OCTOPUS_CB_SECRET is now reported present in .env (SAYS,
          2026-07-27 session) — value never seen, never to be seen.
TEST      §0.5 steps 3 and 4.
FIX       If (False,'no-secret'): §7.1. If ready: send exactly ONE real RFC
          card (RFC-aa01e8ff, the CHRONO_NUDGE_EVERY_N_BEATS knob) and let the
          owner tap it. One real row ends the theory.
OWNER?    Partly — he must tap. You must not tap for him (§0 rule 11).

--- BS-7  THE TEST GATE CANNOT BE READ BY A MACHINE ------------------- [P0]
SYMPTOM   run_all.py runs each test as a bare `python test_x.py` subprocess.
          Neither pytest nor unittest ends up in sys.modules, "am I under
          test?" detection silently returns "live", and the summary is prose.
          A self-patching organism that parses prose WILL read a false green
          and merge broken code.
EVIDENCE  SAYS (previous megaprompt §6). MUST BE RE-VERIFIED — run_all.py was
          edited in the concurrent session (it is in COMMIT-PATHS).
TEST      run_all.py must write _ops/state/test-report.json:
             {"schema":"test-report.v1","ts":...,"passed":N,"failed":M,
              "errors":[{"file":...,"exit":...}], "duration_s":...,
              "baseline_passed":B}
          and exit non-zero when failed > expected_red.
FIX       This is a PREREQUISITE for §6. No apply gate may exist until a gate
          can be read as an integer. Additive: keep the human output as-is,
          add the JSON.
OWNER?    No.

--- BS-8  NO WRITE LEASE. THREE WRITERS, ONE TREE. -------------------- [P1]
SYMPTOM   Concurrent agent sessions + self_patch.py all write F:\backup with
          no coordination. Tonight center.py, initiative.py and output_critic.py
          were all modified within a 3-hour window by something other than me.
EVIDENCE  VERIFIED (mtimes, §2).
TEST      A lease file _ops/state/WRITE-LEASE.json {owner, paths[], expires}.
          Any writer (agent or self_patch) checks it, refuses on overlap, and
          logs the refusal. Falsifiable: a test that simulates two writers.
FIX       Lease + mandatory `git status --porcelain` precondition + a refusal
          log. self_patch.py must honour it too, or the lease is theatre.
OWNER?    No.

--- BS-9  OUTBOUND IS INVISIBLE TO THE OWNER -------------------------- [P2]
SYMPTOM   _ops/state/tg-send-log.jsonl records chat_id, topic_id and outcome
          for every send — and nothing surfaces it. The owner cannot ask
          "did you actually send me something in the last hour, and where?"
EVIDENCE  VERIFIED: tg_api.py:296 writes it; the file is 20958 bytes and live.
TEST      New command `/trace [n]` -> last n sends: time, topic name, ok,
          kind. This is the direct antidote to BS-1 and costs almost nothing.
FIX       Read-only command. Content-free (kind, not text).
OWNER?    No.

--- BS-10  COMMAND DRIFT ---------------------------------------------- [P2]
SYMPTOM   center-config says commands_set=9. One slice of _handle_message
          already shows at least 16 handler keys (/now /budget /revenue
          /missions /menu /start /live /id /eq /box /code /doctrine /deal
          /lead /verdicts /stuck — plus more below the slice I read).
          So the menu Telegram shows and the commands that exist have drifted.
EVIDENCE  VERIFIED (config field + code read). Exact handler count NOT VERIFIED.
TEST      setMyCommands payload MUST be derived from the same registry that
          defines the handlers. A test asserts:
             set(registered_commands) == set(handler_keys) - set(hidden)
FIX       _ops/capability_registry.py is already the right home (it was edited
          today). Make it the single source; derive both the Telegram menu and
          the docs from it. See §4.
OWNER?    No.

--- BS-11  FLAG DRIFT IS UNOBSERVABLE --------------------------------- [P1]
SYMPTOM   flags.cmd is sourced at boot. Editing it changes NOTHING until a
          restart, and no surface anywhere says "N flags are armed but not
          loaded". Every session in this project has been bitten by this.
EVIDENCE  VERIFIED reasoning; the specific drift is INFERRED.
TEST      THE FLAG DRIFT PROBE — the highest ROI small fix in this document:
            1. on boot, snapshot the OCTOPUS_* env into
               _ops/state/flags-loaded.json with the boot mtime of flags.cmd
            2. a read-only probe re-parses flags.cmd and diffs it against the
               snapshot
            3. output: {"drifted":[{"name":..,"loaded":..,"armed":..}],"count":N}
            4. surface N on the cockpit AND as `/flags` in Telegram
          Falsifiable by construction: arm a flag, don't restart, expect N=1.
FIX       Read-only, fail-soft, default-on is arguably safe but ship it
          default-off per §0 rule 3. Plus the zero-cost half, which needs no
          flag at all: on boot the center appends ONE line to the watchdog
          log — "FLAGS-LOADED name=state ..." (names and on/off states ONLY,
          never values, §0 rule 9). Then "the process predates the flag" is
          READ off a log line instead of inferred from mtimes — tonight's
          entire BS-2 investigation was exactly that inference.
OWNER?    No. Ship this early — it makes every other fix in this doc checkable.

--- BS-12  NO SINGLE SEND PATH ---------------------------------------- [P1]
SYMPTOM   Handlers call self._client.send directly, each deciding topic,
          scrub, and error handling for itself. That is why BS-2 could exist
          in 20+ places at once.
EVIDENCE  VERIFIED: ~20 distinct `self._client.send(` call sites visible in
          center.py's message-handling region.
TEST      One helper: `self._say(text, msg=..., kind=..., keyboard=...)` that
          ALWAYS resolves topic via _reply_thread, ALWAYS scrubs, ALWAYS logs,
          and RETURNS a result the caller must consume. Then a grep-test that
          fails if a raw `.send(` appears in a handler.
FIX       Mechanical, low risk, high yield. Do it AFTER BS-2 is verified so
          you are not moving a bug around.
OWNER?    No.

--- BS-13  CODE AUTONOMY HAS NO ROLLBACK STORY (UNVERIFIED) ----------- [P1]
SYMPTOM   _ops/self_patch.py (31 KB) and _ops/cortex/code_autonomy.py exist
          and were both touched today. Whether a bad patch can be reverted
          automatically, and by what authority, is NOT VERIFIED.
EVIDENCE  File existence only.
TEST      Read both. Answer in writing: (a) what is the revert command,
          (b) who may issue it, (c) what happens if the test gate is
          unreachable, (d) is there a STOP file that halts patching.
FIX       If any answer is "nothing", that is a P0 before §6 proceeds. An
          organism that can write code but not un-write it is a one-way door.
OWNER?    No, but the authority question in (b) is his.

--- BS-14  C6 IS SINGLE-SHOT ------------------------------------------ [P2]
SYMPTOM   The research loop runs whatever contract it is handed, then the
          queue is empty. There is no hypothesis PRODUCER (C2). "متنوع"
          (diverse) is impossible with one source of tasks.
EVIDENCE  SAYS (previous megaprompt P3). OCTOPUS_WIRE_C6_RESEARCH is now =1
          (VERIFIED) so the consumer is armed and starving.
TEST      queue_depth > 0 sustained over 24 h without human seeding.
FIX       A complete design exists in
          _program-deliverables/C6-substance-2026-07-25/. Wire it to
          _ops/outcomes/thesis_queue.py::select(), which already returns
          runnable rows with experiment keys. See §6 for the diversity matrix.
OWNER?    No.

--- BS-15  THE OWNER'S DECISION HAS NO EXIT ROUTE --------------------- [P2]
SYMPTOM   center.py:705 correctly RECORDS an `OWNER_AUTH: ...` message and
          ACKs it, and correctly does NOT execute (flipping a flag from chat
          text would be a forgeable auto-deployer). But there is no defined
          path from a recorded authorisation to an actual queued action.
          Result: the owner's decisions accumulate in a log nobody drains.
EVIDENCE  VERIFIED (code read); _ops/state/owner-auth.jsonl exists, 313 bytes.
TEST      Every row in owner-auth.jsonl must reach a terminal state:
          queued -> applied | rejected | expired. Count rows with no terminal
          state. Today that count is almost certainly = all of them.
FIX       A drain: OWNER_AUTH rows become entries in a deployment queue that
          the NEXT AGENT SESSION reads in its first 15 minutes. Human still
          executes; the agent just stops losing the instruction.
OWNER?    No, but the authority ladder is his (§7.4).

--- BS-16  LOG TIME IS NOT CLOCK TIME -------------------------------- [P2]
SYMPTOM   The 2026-07-27 session read the watchdog's last launch line,
          2026-07-26T09:32:05, as "today 09:32" and built "the centre was
          restarted today, so the flag is loaded" on top of it. It was a
          full day earlier. The LOG was right; the READER silently converted
          an absolute timestamp into a relative one and lost a day.
EVIDENCE  VERIFIED — _ops/state/tg-center-watchdog-log.txt (4 lines, §2),
          and the correction is recorded in appendix 1 ("ری‌استارتِ ۰۹:۳۲
          امروز" -> یک روز اشتباه). Every downstream inference that used
          "restarted today" inherited the error.
TEST      A verdict lint: no evidence document may contain a relative-time
          word ("today", "yesterday", "just", "~ago") next to a claim unless
          an absolute ISO timestamp AND the reader's own clock reading sit
          beside it. Every temporal claim must carry evidence-age =
          now - timestamp, computed, not felt. Falsifiable: run the lint on
          this project's own session reports; the 2026-07-27 report fails it.
FIX       The lint, plus a habit written into §0's spirit: when you cite a
          log time, cite your own clock in the same sentence. The watchdog
          log already writes absolute ISO — the failure was on the read
          side, so the fix belongs on the read side.
OWNER?    No.

════════════════════════════════════════════════════════════════════════════
§4 — THE UNIFICATION BLUEPRINT (یکدست‌سازی). SIX SINGLE SOURCES OF TRUTH.
════════════════════════════════════════════════════════════════════════════

The owner asked for ONE thing above all: make it uniform. Uniformity here is
not cosmetic — it is what makes the system checkable. Six declarations, each
with a test that fails when something bypasses it.

  1. ONE SEND PATH        `_say()` in center.py.
                          Nothing in a handler calls client.send directly.
                          Test: grep-test, no raw `.send(` in handlers.

  2. ONE CARD RENDERER    _ops/tg/card_render.py.
                          Every interactive card is built by it.
                          Test: enumerate builders, assert routing.

  3. ONE CALLBACK CONTRACT
                          _ops/telegram_center/callback_token.py mints and
                          verifies. One namespace scheme. One expiry rule.
                          Test: forged token -> 'bad-token'; wrong owner ->
                          'wrong-owner'; replay -> idempotent (already proven
                          end-to-end on 2026-07-25 with a throwaway secret).

  4. ONE VERDICT LEDGER   rfc-verdicts.db :: rfc_decision.
                          approvals.jsonl carries `origin` (live|test) and is
                          an audit trail, NOT a decision source.
                          Test: no row with actor=owner may exist without a
                          matching rfc_decision row. (14 synthetic rows were
                          found once — never again.)

  5. ONE CAPABILITY REGISTRY
                          _ops/capability_registry.py declares: commands,
                          cards, flags, coding capabilities. The Telegram menu
                          (setMyCommands), the docs, and `/menu` are all
                          DERIVED from it. Nothing is declared twice.
                          Test: derived == declared, for all four kinds.

  6. ONE OBSERVABILITY SURFACE
                          Four read-only commands, all content-free:
                            /flags   armed vs loaded, drift count   (BS-11)
                            /trace   last n sends: when/where/ok (BS-9) PLUS
                                     the topic-required invariant counter of
                                     BS-2: group sends without topic, 24 h
                            /queue   RFC + thesis queue depth       (BS-5)
                            /gate    last test-report.json numbers  (BS-7)
                          Rule: every future behavioural flag MUST appear in
                          at least one of these four before it may be armed.

════════════════════════════════════════════════════════════════════════════
§5 — THE LEARN LOOP, LINK BY LINK, WITH ITS LIVE STATE
════════════════════════════════════════════════════════════════════════════

  observe -> propose -> CARD -> owner taps -> verdict -> APPLY -> measure -> thesis

  L1 observe    coherence.py + doctor + probes         ARMED (WIRE_COHERENCE=1)
  L2 propose    doctor RFCs -> rfcs.json               ALIVE (10 RFCs, 1 open)
  L3 card       prepare_rfc_card + callback_token      BLOCKED IF no secret
                                                        -> §0.5 step 4
  L4 tap        owner presses a button in Telegram     NEVER HAPPENED (0 rows)
  L5 verdict    persist_rfc_verdict -> rfc_decision    proven in a probe only
  L6 apply      doctor Phase 5 / apply-merge           **OFF** (flag = 0)
  L7 measure    outcome vs prediction                  no input yet
  L8 thesis     thesis_queue record_evidence           16 rows, rules enforced

THE CHAIN IS HEALTHY EVERYWHERE EXCEPT L4 AND L6, AND BOTH ARE THE OWNER'S.

Your job is NOT to force L4/L6. Your job is to make the loop so obviously
ready that one tap closes it, and to make the readiness itself falsifiable:

  a `/loop` command (or a section in /gate) that prints, as booleans:
      secret_present   card_renderable   channel_live   apply_armed
      open_rfcs   verdicts_recorded   applied_patches
  Every false is a named blocker with the exact thing that unblocks it.
  When all seven are true and applied_patches is still 0 after 48 h, THAT is a
  falsified claim and belongs in the thesis ledger, not in a status message.

════════════════════════════════════════════════════════════════════════════
§6 — THE BUILD LOOP: "قوی، متنوع، کامل"
════════════════════════════════════════════════════════════════════════════

The owner asked that the system's CODING ability be strong, diverse and
complete. Decompose it honestly — these are three different properties and
each has its own gate.

STRONG  = a change it writes is more likely to be right than wrong, and this
          is MEASURED, not asserted.
  · Prerequisite: BS-7. No apply gate before a machine-readable test report.
  · Gate: apply only if  failed == 0  AND  passed >= baseline_passed.
    Never "no error appeared".
  · Adversarial review before apply. Precedent: on 2026-07-25, 25 agents
    verified 12 audit findings and produced 1 CONFIRMED / 11 PARTIAL /
    0 REFUTED — the facts held, the SEVERITIES were inflated. So the reviewer's
    job is severity, not existence. Bake that into the reviewer prompt.
  · Every patch carries a PREDICTION (what measurable thing changes, by how
    much, by when) recorded BEFORE apply. A patch with no prediction is an
    unfalsifiable claim and must be refused entry, exactly like a thesis row
    with no kill condition.

DIVERSE = it can perform more than one KIND of change. Today it effectively
          has one (edit a Python file in _ops). Define the matrix explicitly,
          and give each cell its own gate, its own card, and its own test:

    kind              example                        extra gate
    ----------------  -----------------------------  --------------------------
    add-test          cover an untested branch       must FAIL before the fix
    fix-bug           behaviour change               flag + test + observable
    add-module        a new probe or organ           registry entry required
    refactor          no behaviour change            byte-identical outputs on a
                                                     recorded fixture set
    revert            undo a prior patch             always allowed, no vote
    document          SOT / registry / handoff       validators must pass
    tune-parameter    a knob in budgets.yaml/flags   owner vote, never agent

  Note the asymmetry: REVERT needs no permission, TUNE needs the owner. That
  asymmetry is the safety property. Encode it in the registry, not in prose.

COMPLETE = the loop closes without a human in the middle of the MECHANICS
          (the human stays in the middle of the DECISIONS).
  · task source (BS-14 / C2) -> proposal -> card -> vote -> lease (BS-8) ->
    patch -> test report (BS-7) -> apply (BS-4) -> outcome card -> thesis row
  · Every arrow above must emit an event with a schema. An arrow with no
    event is where the loop will silently break, and you will not find out.
  · Rollback (BS-13) must be answerable in one sentence before any of this
    is armed.

WORKSPACE DISCIPLINE — non-negotiable:
  The organism must NOT patch the live tree while it is running. Options, in
  order of preference: a git worktree; a copy + swap; or, at minimum, a lease
  (BS-8) plus a hard refusal when _ops/STOP-ORGANISM exists. Note the known
  hazard: running the test suite creates _ops/STOP-ORGANISM and
  RESTART-REQUESTED via test_tg_power — so the gate itself can put the
  organism to sleep. Isolate REAL_VAULT / ORG_ROOT in every test.

════════════════════════════════════════════════════════════════════════════
§7 — OWNER-ONLY. Surface these; never do them yourself.
════════════════════════════════════════════════════════════════════════════

 7.1  OCTOPUS_CB_SECRET — reportedly now present in .env (SAYS). If §0.5
      step 4 still returns 'no-secret', give him a one-line command to
      generate one himself. YOU MUST NOT GENERATE IT (§0 rule 10).
 7.2  OCTOPUS_WIRE_APPLY_MERGE is 0. Until he votes it to 1, the organism can
      propose forever and change nothing. Present it as a behaviour choice
      with its risk stated plainly, not as a bug to be fixed.
 7.3  RESTART of the telegram center — needed if §0.5 step 2 lands in General.
      Only the center, not the whole organism. Step-by-step, including the
      soft path (kill only the center python; the launcher loop re-sources
      flags.cmd on every respawn, so the new process comes up flagged in
      ~10 s) and the double-launch hazard:
      _ops/RUNBOOK-TG-CENTER-RESTART.md.
 7.4  The authority ladder for code autonomy: which of the seven change kinds
      in §6 may proceed on a single tap, which need a typed confirmation, and
      which are forbidden. Present the table; do not choose for him.
 7.5  `deadline: 2026-07-20` in _ops/budget/budgets.yaml:25 — still lapsed
      (SAYS). Extend, remove, or declare finished. Related and also his:
      PROJECT_F has floor 3 / human_priority 2.0 while PAINTING (the only
      revenue leg) has floor 1 / 1.0. Present the table; change nothing.
 7.6  VQ-LEAD-001/002 — channel and segment for the first real lead
      experiment. Until then no MONEY_ATTRIBUTION row can exist and fitness
      stays in shadow forever.
 7.7  VQ-GUARD-001 — the one intentional red test. Do NOT rewrite the guard
      to go green.
 7.8  Duplicate FUGU_API_KEY in .env — hygiene, not blocking. Never echo it.
 7.9  The 48 messages sitting in General (BS-2): keep them, delete them, or
      pin one pointer in General to the correct topic. Owner's call; the
      organism must not silently edit chat history either way.

════════════════════════════════════════════════════════════════════════════
§8 — WORK QUEUE, IN ORDER, WITH A DONE-CONDITION THAT IS A NUMBER
════════════════════════════════════════════════════════════════════════════

 W0  §0.5's six verifications.                    DONE = six numbers written down.
 W1  BS-7 test-report.json.                       DONE = a JSON with integer
                                                  passed/failed and a non-zero
                                                  exit on unexpected red.
 W2  BS-11 flag drift probe + /flags.             DONE = arm a flag without
                                                  restarting; probe reports
                                                  drift count 1.
 W3  BS-2 verify topic reply; then the static     DONE = the grep-test fails on
     test that no handler send bypasses           a deliberately reverted line.
     _reply_thread.
 W4  BS-1 never-silent + reply_reason.            DONE = inbound count ==
                                                  ack count over 24 h.
 W5  BS-9 /trace.                                 DONE = it shows the sends
                                                  from W3's test.
 W6  BS-12 single `_say()` path.                  DONE = zero raw .send( in
                                                  handlers; suite still green.
 W7  BS-3 card_render adoption, RFC card FIRST.   DONE = one real RFC card
                                                  rendered by card_render and
                                                  delivered.
 W8  BS-6 send that one card. Owner taps.         DONE = rfc_decision count 1.
 W9  BS-8 write lease honoured by self_patch.     DONE = a two-writer test
                                                  produces a logged refusal.
 W10 BS-13 answer the four rollback questions.    DONE = four sentences, in
                                                  _ops/ARCHITECTURE-SOT.md.
 W11 BS-14 C2 hypothesis producer.                DONE = queue_depth > 0 for
                                                  24 h with no human seeding.
 W12 BS-10 registry-derived command menu.         DONE = derived == declared
                                                  test passes.
 W13 BS-5 /queue, BS-15 owner-auth drain.         DONE = zero owner-auth rows
                                                  without a terminal state.
 W14 §6 diversity matrix encoded in the registry. DONE = seven kinds, each with
                                                  a gate and a test.

 GATE ZERO — registered 2026-07-28: W1 precedes EVERYTHING, and it is still
 unearned. The session that wrote this document had no device_bash, so
 run_all.py has never once produced a test-report.json for this tree. Until
 D1 is a number you have read yourself, no apply gate may exist — a gate
 that cannot be read manufactures false green — and nothing in §6 is armed,
 tuned, or merged, no matter how small the diff looks.
 Do NOT start W7 before W1. Do NOT start any of §6 before W1 and W10.
 A gate you cannot read is worse than no gate: it manufactures false green.

════════════════════════════════════════════════════════════════════════════
§9 — GOTCHAS. Read this or repeat them.
════════════════════════════════════════════════════════════════════════════

INHERITED, ALL STILL TRUE:
 · ANTIVIRUS locks .git/objects on this drive. `git add` fails with
   "Permission denied" then "fatal: adding files failed". Retry in a loop up
   to ~6 times with a few seconds' sleep. It has succeeded on attempt 3.
 · PIPING `git add` OUTPUT THROUGH `head` SENDS SIGPIPE and kills the add
   mid-way, silently staging nothing. Redirect to /dev/null or consume fully.
 · The Edit tool converts .cmd/.bat files to LF, which breaks cmd parsing.
   OCTOPUS-flags.cmd is currently 646 CRLF with ZERO lone LF (VERIFIED
   2026-07-28). Edit it BYTE-LEVEL in Python and re-count afterwards.
 · flags.cmd is sourced at boot; budgets.yaml is cached in-process. Editing
   either changes NOTHING until a restart. Say so EVERY time. (W2 exists so
   you never have to say it from memory again.)
 · `_locate`-style "first candidate that has the key" logic reads STALE
   snapshots. Rank candidates by mtime and record evidence age.
 · Python 3.11+ parses COMPACT ISO dates: date.fromisoformat("20260720")
   works. A test asserting that string is malformed is a wrong test.
 · REAL_VAULT / ORG_ROOT default to the LIVE tree. run_all genuinely creates
   _ops/STOP-ORGANISM and RESTART-REQUESTED via test_tg_power.
 · Worktrees under %USERPROFILE%\.claude\worktrees hold STALE copies. Confirm
   every path starts with F:\backup.

NEW, FROM 2026-07-27/28:
 · A THREE-POINT FIT IS NOT A MODEL. The paid-brain throughput model was
   built from 3 samples and extrapolated 2.5x beyond its range; it was wrong
   by 1.7x and a real recommendation was built on it. With 91 points the true
   rate is ~80 tok/s. Before you build a spec from samples, print n.
 · A SNAPSHOT IS NOT A TREND. "Zero updates since restart" was TRUE at 09:58
   and FALSE by 12:57. State the observation window with every counter claim.
 · SOME SESSIONS HAVE NO SHELL ON THE MACHINE. If `device_bash` is absent you
   can still read and write files but you cannot run tests, git, or probes.
   Say so at the top of your report and mark everything NOT VERIFIED that
   needed execution. Do not quietly downgrade to guessing.
 · A GUARD THAT EMITS SILENCE ERASES ITSELF. `too-short-answer` was a correct
   refusal that became an indistinguishable failure. Any refusal must be
   observable to the person it affects.

════════════════════════════════════════════════════════════════════════════
§10 — DEFINITION OF DONE. Six falsifiable claims.
════════════════════════════════════════════════════════════════════════════

The mission ("the system learns from Telegram and builds") is COMPLETE when
all six of these are true and each is checkable by a command, not an opinion:

  D1  test-report.json exists and `failed` is an integer.
  D2  /flags reports drift_count = 0 immediately after a restart, and > 0
      immediately after arming a flag without one.
  D3  Every owner message in a 24 h window has exactly one keyed reply,
      including the refusals — inbound == acks.
  D4  rfc_decision has at least one row whose actor is genuinely the owner
      and whose origin is `live`.
  D5  At least one patch exists that was proposed by the organism, voted in
      Telegram, gated on failed==0 && passed>=baseline, applied, and recorded
      against a PREDICTION made before the apply.
  D6  At least one thesis row changed status on the strength of D5's outcome —
      including, and especially, if it was FALSIFIED.

  D6 is the real one. A system that only ever confirms itself has not learned
  anything; it has only accumulated. The first falsified row is the proof that
  the loop is real.
```

---

## پیوست ۱ — تصحیح‌های مگاپرامپتِ ۲۰۲۶-۰۷-۲۵

برای اینکه ایجنتِ بعدی وقتش را روی چیزی که دیگر خراب نیست تلف نکند:

| ادعای ۲۵ جولای | وضعیتِ ۲۸ جولای | برچسب |
|---|---|---|
| «مغزِ پولی همین حالا دارد می‌میرد؛ ۱۶ تایم‌اوت» | مرده نیست. هر ۱۶ تایم‌اوت مالِ ۲۵ جولای است. آخرین خطا ۲۷ جولای ۱۵:۵۹ `RemoteDisconnected` و بعدش ۱۷ موفقیتِ پیاپی | **VERIFIED** |
| «`ms = 3811 + 25.2·t`، ۴۰ tok/s» | با ۹۱ نمونه: `ms = 5393 + 12.54·t`، ~۸۰ tok/s. ۱.۷ برابر بیش‌برآورد | **VERIFIED** |
| «`max_tokens` را ۱۲۰۰→۶۰۰ کن» | بر مدلِ غلط سوار بود. زنده ۱۲۰۰ توکن را در ~۲۲ ثانیه تمام می‌کند؛ `OCTOPUS_GOVERNOR_MAX_TOKENS` اصلاً ست نشده | **VERIFIED** |
| «ری‌استارت تنها کارِ باقی‌مانده است» | ری‌استارت شد (۰۹:۳۲ و ~۱۶:۰۷). کارِ باقی‌مانده حالا `WIRE_APPLY_MERGE=0` است | VERIFIED / INFERRED |
| «`OCTOPUS_WIRE_APPLY_MERGE` پیش‌فرضِ کد `"1"` و مسلح است» | در flags.cmd صریحاً **`=0`** است → زنده خاموش | **VERIFIED** |
| «`OCTOPUS_WIRE_COHERENCE` پیش‌فرض خاموش، سیم‌کشی‌نشده (P4)» | `=1` | **VERIFIED** |
| «`ACTIVATION-C6-RESEARCH` کارِ نکردهٔ مالک (§۴.۳)» | فلگ `=1` و فایلِ `.flag` موجود است | **VERIFIED** |
| «`OCTOPUS_CB_SECRET` هیچ‌کجا نیست» | حالا در `.env` هست | SAYS |
| «پیام‌های تو به بات نمی‌رسد» (جلسهٔ ۰۹:۵۸) | می‌رسد. `last_offset` ‎+۹۵ رفته جلو و بات چهار بار جواب ساخت | **VERIFIED** |
| «ری‌استارتِ ۰۹:۳۲ **امروز**» | ۰۹:۳۲ ِ **۲۶ جولای** بود — یک روز اشتباه. آخرین launch در watchdog همان است | **VERIFIED** |
| «بات جواب نمی‌دهد» | می‌دهد، پشتِ سرِ هم. ۴۸ پیام / ۵۹٬۴۵۶ نویسه در ۱۲ ساعت به **General** رفته — نه اینکه نیامده باشد، در اتاقِ اشتباه است | **VERIFIED** |
| «۹ دیجست شاید فرستاده نشده باشد» | فرستاده شد — burst ساعت ۲۲:۰۳:۴۰ با تاپیک‌های ۲۲…۲۹ و ۶۵ | **VERIFIED** |
| «stream=center هرگز تاپیک نمی‌گذارد» (فرضیهٔ خودم، وسطِ کار) | غلط — ۱۸ ارسالِ center تاپیک دارد. نقص فقط در خروجیِ آزادِ center به گروه است | **REFUTED (خودم)** |

---

## پیوست ۲ — یک صفحه برای مالک

**مسئله در یک جمله:** سه اتفاقِ کاملاً متفاوت — «نرسید»، «جواب در General افتاد»،
«گارد جواب را دور ریخت» — از گوشیِ تو یک شکل دارند: سکوت. تا وقتی این سه از هم
جدا نشوند، هیچ گزارشی از این سیستم قابلِ اعتماد نیست.

**یک چیز که فقط تو می‌توانی، و همه‌چیز به آن بند است:**
`OCTOPUS_WIRE_APPLY_MERGE` روی **۰** است. یعنی ارگانیسم می‌تواند تا ابد پیشنهاد
بدهد، تو می‌توانی تا ابد رأی بدهی، و **هیچ‌چیز عوض نمی‌شود**. این یک باگ نیست —
یک رأیِ رفتاری است که هنوز نداده‌ای.

**سه‌شنبه، اولین کار، ۳۰ ثانیه:** داخلِ تاپیکِ 🦑system بنویس `/now`.
جواب همان‌جا آمد → یک مشکل کمتر. در General افتاد → راهنمای قدم‌به‌قدم در
`_ops/RUNBOOK-TG-CENTER-RESTART.md` (مسیرِ نرم: فقط پروسهٔ پایتونِ مرکز را بکش —
لانچر خودش با فلگ‌های تازه برمی‌گرداندش).

**اگر هیچ کاری نکنی:** دیجست‌ها سرِ وقت می‌آیند، مغزِ پولی سالم می‌ماند، و
سیستم دقیقاً به همین اندازه باقی می‌ماند — چون حلقهٔ یادگیری‌اش در آخرین حلقه
خاموش است و کسی متوجهش نمی‌شود.
