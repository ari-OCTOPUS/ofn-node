# NEXT-AGENT HANDOFF — OCTOPUS live + Telegram-execute wave

You are continuing work on **OCTOPUS**, a live multi-agent "organism" (Python under `F:\backup\_ops`, inside an
agent-first Obsidian vault). Owner = **آری/ari** (Persian-speaking, Sydney). Speak Persian back to him. He is
high-trust/hands-off but the system now moves REAL money via a metered LLM (Fugu/Sakana), so treat money / outbound /
self-mod / halt / approval changes as owner-gated.

## HARD SECURITY RULES (never violate)
- NEVER read, echo, print, or write API keys / secrets / seeds / wallet addresses — not in chat, notes, HANDOFF, or logs.
  Secrets live ONLY in `F:\backup\.env` (gitignored). `.agentignore` forbids `*.env`, `*key*`, `*secret*`, `*wallet*`,
  `*seed*`, `*.pem`, `.git/`, `_code/`, `_Archive/`, `_Duplicates/`, `secrets-export/`.
- The assistant CANNOT write to `F:\backup` (permission-denied on destructive/write ops). Design + hand exact
  commands/code to the owner; HE executes writes to `F:\backup`. You CAN read it, and write to worktrees/scratchpad.
- Money / outbound / self-mod / halt-semantics / approval / emit-contract changes stay owner-gated ("proposal lane").
  Do NOT auto-flip activation flags. Do NOT auto-merge to master.
- Worktree discipline: `F:\backup` = the LIVE tree (main worktree, branch `master`). Paths like `F:\backup\...`
  silently hit LIVE, not a worktree. Always `git worktree list` and verify path resolution before edits.

## WHAT IS ALREADY TRUE (verified this session)
1. **Octopus is LIVE.** `RUN-ORGANISM.bat` loops `python -X utf8 organism.py` (running: cmd.exe). organism.py
   loads `.env`, builds the Telegram channel (`wiring.make_telegram_channel`, organism.py:204), and runs a daemon
   thread `telegram-poll` → `_chan.run_forever` (organism.py:206-211).
2. **Fugu/Sakana LLM works & is metered.** `ask('deep', …)` returned
   `{ok:True, text:'…', tier:'primary', model:'fugu', cost_usd:0.001425}`. Budget caps (budgets.yaml): Fugu metered
   cap_monthly=100 AUD, global CEIL_MONTH=30, per-day≈2, human_gate_aud=20. Tri-brain router: local ollama
   `qwen2.5:1.5b` ($0) / secondary GLM (Z.ai, **dead — needs ZAI_API_KEY / GLM_API_KEY in .env**) / primary Fugu.
3. **Key-name mismatch is patched by owner:** `.env` sets BOTH `FUGU_API_KEY` and `SAKANA_API_KEY` to the same value
   (env_loader/model_router read FUGU_API_KEY at model_router.py:55; debate/client.py reads SAKANA_API_KEY at :174).
   A clean fix (owner-gated) is to make model_router.keys_present() and client.py agree on ONE var name.
4. **Wave 0 reliability commit is live** = `6a38af8` on master (master_halted / HALT-ALL / raise_/clear_halt_all /
   panic / resume / events-unknown→fail-loud / capability marker / σ-freeze fuse fix). Gate: 137/137 relevant tests
   green (test_master_halt 5/5, test_panic_command 4/4, test_tg_restart 8/8); only 2 pre-existing env-sensitive
   `cartographer_wiring` reds remain (they read the LIVE-tree STOP-ORGANISM; isolate with ORG_ROOT).
5. **Live/money gates:** `opslib.live_gate_open(flag)` = date-shield 2026-07-21 OR `ACTIVATION-GO-LIVE.flag`, AND a
   per-activation flag. GO-LIVE flag EXISTS → shield already bypassed. Real money-moves ALSO need
   `capability_gate.is_open` = capability_ok AND `LIVE-ENABLED.flag` AND approval. `LIVE-ENABLED.flag` currently
   ABSENT → money settle fail-closed (safe). The canonical org-wide halt check used everywhere in wiring.py is
   `opslib.STOP_ORGANISM.exists() or opslib.halted()`.

## THE TELEGRAM SURFACE — GROUND TRUTH (read carefully, this is where the bugs are)
- There are (at least) TWO command surfaces. Only ONE is live:
  - **LIVE** = base class `TelegramApprovalChannel` in `F:\backup\_ops\budget\approval_channel.py`, inside organism.py.
    Poll loop `poll_once` (approval_channel.py:228-335). Owner allowlist enforced at :291 (only
    `TELEGRAM_OWNER_CHAT_ID`). Text → `handle_command` (:320 → def at :924). Buttons → `dispatch_callback`
    (:308 → def at :502).
  - **DEAD** = `F:\backup\_ops\telegram_center\center.py` (tg-center) — NOT running; richer command map but only
    `/now` + ok/no/later are wired; ok/no/later only RECORD a verdict, don't execute. Ignore for the live path.
  - **DANGER / must locate** = `F:\backup\4d_system\brain\telegram_bot_unified.py` — a SECOND executor a safety
    agent flagged as "already executes, weaker/ungated." Likely the source of the **409 dual-poller** that eats the
    owner's button presses (poll_once alerts on 409 at approval_channel.py:248-252) AND a genuine ungated-execution
    risk. FIRST JOB: find whether it's running/scheduled, and shut it down so there is exactly ONE canonical surface.

- What `handle_command` (live) does today: `/start /status /overview /blueprint /brain /doctor /money /school /safety
  /alerts /upgrades /queue /reentry /reveal` → **render a tab / show text (READ-ONLY)**. `/stop`→kill_switch (executes),
  `/panic`→panic_all (executes), `/resume`→resume_all (executes), `/lead …`, `/claim …`, `/conflict …` → writes.
  So the owner's complaint "commands don't execute / read-only" = the **operational verbs** (`/doctor /school /money
  /consolidate /ingest`) only DISPLAY a tab; they don't RUN the job.

- `dispatch_callback` (buttons) DOES execute the money-settle path: `app:approve:<effect_id>:<token>` → `_do_approve`
  (correctly gated by pending-meta + one-time anti-forgery token, :522-536). `menu:/home:/rfc:/card:/pg:/act:` are the
  other button routers.

## THE REAL FINDINGS (after 3 adversarial workflows — supersede earlier guesses)
- **The execute-buttons ALREADY EXIST** in Telegram: `doctor:run / consolidate:run / school:learn / ingest:crypto|acct`
  (verb allowlist approval_channel.py:1370-1374; action buttons ~:1879-1884). Pressing one routes
  `dispatch_callback → _dispatch_act → _run_act` (:1646); for every `OOB_VERBS` verb (:1383) `_run_act` ONLY calls
  `_append_request` (:1516) → writes one line to `state/cockpit-requests.jsonl` (INV-7: never run inline on the poll
  thread). **BUT no consumer of that queue was ever built** — organism.py never reads it (only cockpit_readmodel
  tail-displays it). THAT is the "read-only" bug. Fix = build the missing beat-thread consumer (respects INV-7).
- **DBG-A was a NON-ISSUE — do NOT "fix" it.** Injecting a halt-based `kill_check` into make_telegram_channel
  PERMANENTLY wedges the poll thread: run_forever is `while not self._killed()` (approval_channel.py:367) so a halt
  makes /panic EXIT the loop and /resume can never arrive. The poll thread MUST stay alive under halt. Halt is already
  enforced by (1) organism loop exit on STOP/master_halt (organism.py:259), (2) the new consumer's own halt gate,
  (3) money = capability+token gated. Leaving the poll thread alive under halt enables no money/outbound/self-mod
  (buttons only queue; money needs the T-2 card).
- **DBG-B / 409:** the dangerous unified 4d bot is ALREADY disabled (`telegram_bot_unified.py.DISABLED-409-FIX`,
  2026-07-12). The live 409 = **center.py via RUN-TG-CENTER.bat** long-polling the SAME `TELEGRAM_BOT_TOKEN` as the
  organism's approval_channel. Fix is operational, not code: **do not run RUN-TG-CENTER.bat** (and don't launch the
  older `4d_system/brain/telegram_bot.py` either — same token). Verified organism/wiring/run_all don't import center.

## THE TASK THE OWNER ASKED FOR: make Telegram buttons actually EXECUTE (not read-only)
A fully hardened, adversarially-reviewed patch already exists at
`…/scratchpad/PATCH-tg-execute-v2.md` (read it — apply it in the WORKTREE, not live F:\backup). Summary:
- **Patch A** — new `wiring.cockpit_requests_beat()` consumes `cockpit-requests.jsonl` on the BEAT thread, behind
  default-OFF `OCTOPUS_TG_EXEC`, halt-gated, with: first-activation fast-forward (no backlog replay), truncation reset,
  AT-MOST-ONCE cursor (persist before exec → drop-not-duplicate), per-beat cap, complete-line-only advance,
  single-consumer lock (split-brain guard), ✅/⚠️ chat ack. Safe verb set = **doctor + consolidate ONLY** for v1.
- **Patch B** — call it from the organism loop after the consolidation_beat block (~organism.py:384).
- **school DEFERRED** (SensoryBus.ingest needs an `Observation` dataclass, not a dict — add once verified).
- **ingest EXCLUDED** (ingest_raw.run writes/overwrites .md notes in the owner's vault project folders — risky).
- **Patch C DROPPED** (see DBG-A above).
- **Patch D** — key-name ALIAS only (add `env_key_alias` FUGU_API_KEY/GLM_API_KEY; never rename — would orphan the
  owner's existing SAKANA/ZAI keys).
Money / outbound / self-mod stay on the approval-card + anti-forgery-token path (`app:approve:…` → `_do_approve`).
Get the owner's explicit yes before adding ANY new executing verb beyond doctor+consolidate.

## HOW TO WORK
- Verify every claim against the real files before you change anything (this handoff may drift). Use ripgrep directly.
- Test with the suite: `cd F:\backup\_ops && python -X utf8 run_all.py` (isolate cartographer reds with ORG_ROOT).
  There is NO STOP-ORGANISM file normally; if a run shows ~11 odd fails, check for a stray STOP-ORGANISM artifact.
- 3D viewer of the system (optional context) lives at `F:\3D\octopus-3d` (Vite + Babylon.js; `npm run dev`); its
  `public/data/scan.json` is an extracted 151-node graph, and `vite.config.js` has an `/api/octopus-live` middleware.
- End of session: update touched PROJECT.md `## Active Context` / `## Progress`, rewrite `01 - Dashboard/HANDOFF.md`
  (wikilinks only, no secrets), and run both validators in `04 - Architect System/scripts/`.
