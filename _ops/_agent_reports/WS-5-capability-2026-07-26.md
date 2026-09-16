# WS-5 · CAPABILITY — what is the next real power, ranked by evidence?

**Agent-day:** 2026-07-26 (clock start 18:35, report written ~18:42)
**Scope:** read-and-measure pass only. No behaviour changed. All probes ran against isolated temp `STATE_DIR`/`OPS_DIR`; the live organism was never written to.

---

## 1. VERDICT

Four of the five candidate capabilities are **real, healthy, and OFF** — they are not decorative. Each one's flag-gate was verified to actually flip the code path (probe: `os.environ[FLAG]='1'` → gated branch executes and writes a real artifact to an isolated inbox). The single highest-value next power is **OCTOPUS_WIRE_LEAD_CANDIDATES** (the absent flag), because it is the one gate between a real customer (owner-typed Telegram text, already correctly detected by `owner_menu.looks_like_lead()`) and the healthy lead scorer — and it is *not even a key in flags.cmd*, so it can never be armed by editing flags alone; the canonical trust-engine path returns `None` at `owner_menu.py:76` and falls back to a frozen inbox that contains only a template (VERIFIED: `state/legs/lead-inbox/` holds exactly `_TEMPLATE-discovery-lead.json`, zero real leads ever scored). Second is **OCTOPUS_WIRE_HARVEST** (AusTender ingestion → lead-inbox), which I proved end-to-end with an injected synthetic release: flag off → `written:0` no-op; flag on → `written:1`, a real lead JSON written with `source:"austender"` that the scorer consumes. Third is **OCTOPUS_WIRE_MISSION_RUNNER** (owner-triggered isolated test execution): I proved `code.apply`/`code.rollback` are *structurally* excluded (`ALLOWLIST` at `mission_runner.py:55`), a real run writes a `run.json` artifact, and the `center.py:1210` flag-gate flips `wired` False→True. **OCTOPUS_WIRE_ROMAJAN_PROBES** is the one ON capability (flag=1 + `ACTIVATION-C6-RESEARCH.flag` present) and is genuinely producing (`state/c6/hypothesis-queue.jsonl` mtime 17:08 today) — it is a research/epistemics path, not a money/lead path, so it ranks below the lead-flow capabilities on "next real power." **CRITICAL caveat (§5):** `OCTOPUS-flags.cmd` mtime is 17:26:29; `ORGANISM-STATE.code` boot is 17:05:27 — flags.cmd was edited **21 minutes AFTER boot**. The running organism sourced flags.cmd at boot, so **none of the on-disk flag values are guaranteed live until a restart.** Every "turn it on" recommendation below requires a restart to take effect.

---

## 2. Capability table

Flags parsed by me (not trusted from docs): `re.findall(r'^\s*set\s+(\w+)=(.*)$', raw, re.M)` → **95 keys** (the brief said ~84; ground-truth doc said ~84; actual parse = 95). `OCTOPUS_WIRE_MISSION_RUNNER` appears **twice** in the file (both =0) — a duplicate key, harmless because both values agree.

| Capability | Flag value (parsed) | What turns on (file:line) | What it can NEVER do | Smallest proof test (VERIFIED) | Verdict |
|---|---|---|---|---|---|
| **LEAD_CANDIDATES** | **ABSENT** from flags.cmd (95 keys; confirmed by grep across repo) | `owner_menu.py:76` `_register_lead_canonical` → `legs.lead_candidate_inbox.submit_candidate`; also gated at `lead_candidate_inbox.py:37,48` | Send anything outward. `lead_candidate_inbox.py:162` hardcodes `external_send_allowed: False`; only owner→LANGAR→EffectorGate can ever send (`:17-18`). `outreach_allowed:true` is a per-candidate *verdict* field, not a send. | flag absent → `_register_lead_canonical(...)` returns `None` (the disease); flag=1 → returns `{ok:true, status:"accepted", lead_id:..., receipt_event_id:...}` and writes 1 candidate JSON + 1 `lead.candidate.received` receipt to isolated inbox. | **#1 next power.** Real, starved, and the flag doesn't exist. |
| **HARVEST** | `0` | `wiring.py:1848` `harvest_beat` (called live by `organism.py:839`, `brain_worker.py:408`) → `legs/harvest_austender.py:harvest()` | Send/spend/use a secret. Keyless GET-only to `api.tenders.gov.au`; writes only to local `state/legs/lead-inbox`. `harvest_austender.py:62` `check_flag()`; kill-switch at `wiring.py:1850`. | flag off → `harvest()` `{written:0, note:"not set — no-op"}`; flag on + injected `get_json` returning 1 release → `{written:1}` + a `*.json` lead file with `source:"austender"` written to isolated inbox. | **#2 next power.** Feeds the same starved scorer. |
| **MISSION_RUNNER** | `0` (duplicated key, both 0) | `center.py:1210` `wired = ... == "1" and runner_mod is not None` → `mission_runner.run_mission(mid)` | Apply/patch/rollback to the live tree. `ALLOWLIST = ("code.plan","code.test","code.diff","doctor.review","epistemics.review")` (`mission_runner.py:55`); `code.apply`/`code.patch`/`code.rollback`/`evolution.*`/`mission.next` are excluded (`:11`). Tests run only in a worktree (`:242`). | `dry_run` with actions `[code.plan, code.apply, code.rollback]` → `todo:[code.plan]`, `skipped:[(code.apply,owner-gated),(code.rollback,owner-gated)]`; real run of `code.plan` → `ok:true`, `run.json` artifact written; `center.py:1210` logic: flag off → `wired:False`, flag on → `run_mission` called. | **#3 next power.** Owner-triggered green/red test evidence, zero apply. |
| **LEAD_DRAFT** | `0` | `wiring.py:518` `_lead_draft_chain` (in `leg_beat`) + `wiring.py:2095` `lead_quote.create_quote` (in `lead_discovery_beat`) | Send/mark_paid/reconcile. `lead_quote.py:187-188` writes `draft_only:True, sent:False`; `mark_sent` (`:381-391`) is a local flag flip, "no real send." | flag off → `_lead_draft_chain` not called (gate `flag(...)` False); flag on → called. `create_quote` source-guaranteed `sent:False` (my stub leg returned `ok:False "draft تولید نشد"` — needs a real `lead_leg`, but the no-send guarantee is structural in source). | Real but lower rank: it only fires *after* a lead is minted, so it is downstream of #1/#2. |
| **POCKETSMITH** (read) | `0` | `legs/pocketsmith_api.py:_get` (GET-only); consumed by `budget/approval_channel.py:1921-1924` and `legs/accountant.py:243-248,314` | Write. `pocketsmith_api.py` has **no `method=` / POST/PUT/PATCH/DELETE** — only `_get` (default GET). | flag off → `_flag_on()` False; flag on + injected `urlopen` → `_get` returns `{ok:true, status:200, data:[...]}`; `urlopen` called with method `GET`, key in `X-Developer-Key` header not URL. **NB:** `POCKETSMITH_API_KEY` is PRESENT in this env (len 128 via env_loader), so the flag is the *only* gate. | Real, but read-only accounting sync — rank below lead-flow. |
| **PS_WRITEBACK** (write side of PocketSmith) | `0` | `legs/ps_writeback.py:flush` (called by `accountant.py:337`); gated at `:49,97,152,479` | Write anything but `labels`. `_PUT_PATH_RE = ^/transactions/[0-9]+$` (`:60`); `_WRITABLE_FIELDS = {"labels"}` (`:10`); only GET+PUT (`:153`); **per-item owner vote required, fail-closed** (`:13-15`); idempotent GET-before-PUT (`:18`). | flag off → `flush()` `{wired:False, written:0, "صفر شبکه"}`; `_request("POST",...)` blocked; `_request("PUT","/accounts/1",...)` blocked (bad path); `_request("PUT","/transactions/1",{amount:999})` blocked (bad field). | Real outward write, but triple-gated + owner-voted — safe; rank with POCKETSMITH. |
| **ROMAJAN_PROBES** (the one ON capability) | `1` | `c6_probes.py:19` + `romajan_bridge.py:35` `enabled()` → reads `F:\romajan` ledgers → appends to `state/c6/hypothesis-queue.jsonl` (consumed by `c6_producer.py:81,133`) | Send/spend. Local file I/O only. Dual-gate: flag=1 **AND** `ACTIVATION-C6-RESEARCH.flag` file must exist (`romajan_bridge.py:40-45`). | flag=1 + ACTIVATION absent → `enabled()` False; flag=1 + ACTIVATION present → True; flag=0 → False. Live: ACTIVATION file PRESENT (mtime 25-07 16:37), `state/c6/` actively written (mtime 17:08 today). | ON and producing. Research path, not money/lead — ranked below on "next power." |

---

## 3. Three highest-value concrete next steps (each with its smallest proof test)

Each is additive + flag-gated + default-off; each requires an organism **restart** to take effect (flags.cmd is sourced at boot).

1. **Add `OCTOPUS_WIRE_LEAD_CANDIDATES=0` to flags.cmd, then the owner arms it to `1` and restarts.** This is the single gate between owner-typed Telegram lead text and the scorer. Smallest proof: after restart, owner types a Persian lead sentence in Telegram; within one beat, a non-template `*.json` appears in `state/legs/lead-inbox/` with `candidate_type:"consented_inbound"` and a `lead.candidate.received` receipt in `events.jsonl`. One week later: `find state/legs/lead-inbox -name "*.json" | grep -v _TEMPLATE | wc -l` is > 0 and growing.

2. **Arm `OCTOPUS_WIRE_HARVEST=1` and restart** (only after #1, so the inbox has a consumer ready; and acknowledging the docstring's own warning that AusTender `contractPublished` is a *weak* paint-lead source — 1 paint hit per 400 contracts/28 days, VERIFIED live 2026-07-17). Smallest proof: after restart, within `CHRONO_HARVEST_EVERY_N_BEATS` (default 720 ≈ 12h) the beat fires `harvest_beat`; check `state/legs/lead-inbox/` for a file with `source:"austender"`. One week later: ≥1 harvested candidate present and scored (score visible in `lead_discovery` state), even if most are low-relevance — that proves the pipe is wet.

3. **Arm `OCTOPUS_WIRE_MISSION_RUNNER=1` and restart.** Lets the owner trigger isolated test runs from Telegram (`ms:test` action). Smallest proof: owner creates a mission with `code.test`, taps test; a `run.json` artifact appears under `.mission-runs/<run-id>/` with `status:"done"` or `"failed"` and per-test `exit` codes; the live tree is untouched (verify `git status` clean). One week later: ≥1 green run recorded in mission state with real test evidence, zero apply actions attempted.

---

## 4. What I could NOT determine (required section)

- **Whether `OCTOPUS_WIRE_ROMAJAN_PROBES` is actually live in the *running* organism.** The on-disk flags.cmd (mtime 17:26) has it =1, but the organism booted at 17:05. The 25-07 backup (74 keys) had ROMAJAN_PROBES **ABSENT**; the current file (95 keys) added it =1. So the version at boot may or may not have contained it. The `state/c6/` queue is active (mtime 17:08, 3 min after boot), which is consistent with ROMAJAN being live at boot — but I cannot prove which flags.cmd revision was on disk at 17:05. Resolution requires the owner to confirm via `live_commands.py:259` (the `ROMAJAN_PROBES` env read in the live Telegram menu) after a clean restart.
- **The real-world AusTender hit-rate for paint leads** beyond the docstring's 2026-07-17 measurement (1/400). I did not make a live network call (would have spent a real API request and the brief said measure, not act). The docstring's own claim is SAYS, not re-VERIFIED today.
- **Whether `create_quote` produces a valid draft with a real `lead_leg`** — my probe used a stub leg and got `ok:False "draft تولید نشد"`. The `sent:False`/`draft_only:True` no-send guarantee is structural in source (`lead_quote.py:187-188`) and VERIFIED by reading, but I did not prove a *successful* draft end-to-end. This needs a real `lead_leg` packet.
- **The exact set of keys the running organism actually has in `os.environ` at boot.** I parsed the on-disk file; the running process's env is not directly inspectable from here. The boot-time flags.cmd revision is uncertain (see first bullet).
- **Whether `OCTOPUS_WIRE_LEAD_OUTCOME` (flag=1) actually records outcomes** — it is on, and `wiring.py:2110` queues leads for `_record_lead_decisions`, but with LEAD_DRAFT off no leads are ever minted, so the outcome recorder's queue is starved. I did not independently exercise it. This is downstream of the same disease (starved inbox), not a separate finding.
- **The 21 keys present in current flags.cmd but absent in the 25-07 backup** (e.g. `OCTOPUS_WIRE_BLACKBOX_MAP`, `OCTOPUS_WIRE_COHERENCE`, `OCTOPUS_WIRE_IDENTITY_EQ`, `OCTOPUS_WIRE_COLLAB_CODING`, `OCTOPUS_WIRE_THESIS_QUEUE`, `OCTOPUS_TG_*`, etc.) — I did not measure these; they are out of the WS-5 candidate set. Several are =1 on disk but, per the boot/mtime caveat, may not be live.

---

## 5. Predictions registered and outcomes

**Prediction (registered 18:35:49, BEFORE reading any flag values or branching code):**
> HARVEST=0, MISSION_RUNNER=0, POCKETSMITH=0, LEAD_DRAFT=0, LEAD_CANDIDATES=ABSENT, ROMAJAN_PROBES=0. "If by 18:50 any parsed value contradicts the above, my wiring is wrong."

**Outcomes (parsed 18:36):**
- HARVEST=0 ✓, MISSION_RUNNER=0 ✓, POCKETSMITH=0 ✓, LEAD_DRAFT=0 ✓, LEAD_CANDIDATES ABSENT ✓ — 5 of 6 correct.
- **ROMAJAN_PROBES: I predicted 0, parsed value is 1 → PREDICTION REFUTED.** Root cause of my error: I anchored on the §5 gotcha ("an arming script skipped ROMAJAN_PROBES as 'already there' — it was set to 0") as if it described the current state. That gotcha describes a *past* event; the flag has since been set to 1. Lesson honoured: parse the VALUE, not presence, not a story about the value. The dual-gate (`enabled()` also requires the ACTIVATION file) means flag=1 alone is not the whole story — VERIFIED both conditions hold live.

**Secondary prediction implicit in the brief's ground truth:**
> "OCTOPUS_WIRE_LEAD_CANDIDATES is checked in code but absent from flags.cmd." — VERIFIED: my parse of 95 keys does not contain it; grep across the whole repo confirms no `set OCTOPUS_WIRE_LEAD_CANDIDATES` line. The code branch at `owner_menu.py:76` therefore always returns `None` in any organism that sources this flags.cmd. This is the same disease as "presence ≠ value" but one level worse: "presence in code ≠ presence in flags" — the gate cannot be opened by editing flags.cmd, because the key is not there to edit.

---

### Evidence trail (all file paths absolute)

- Flags file: `F:\backup\_ops\OCTOPUS-flags.cmd` (95 keys parsed; mtime 17:26:29)
- Boot record: `F:\backup\_ops\state\ORGANISM-STATE.code` (`booted: 2026-07-26T17:05:27`)
- Pre-edit backup: `F:\backup\_ops\OCTOPUS-flags.cmd.bak-2026-07-25` (74 keys; ROMAJAN_PROBES absent)
- Starved inbox (live): `F:\backup\_ops\state\legs\lead-inbox\_TEMPLATE-discovery-lead.json` (only file present)
- Active ROMAJAN output (live): `F:\backup\_ops\state\c6\hypothesis-queue.jsonl` (mtime 17:08 today)
- Gate sites: `owner_menu.py:76`, `wiring.py:518,1848,2095`, `center.py:1210`, `mission_runner.py:55`, `lead_candidate_inbox.py:162`, `pocketsmith_api.py:56`, `ps_writeback.py:60,97,153`, `romajan_bridge.py:40-45`
