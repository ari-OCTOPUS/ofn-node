---
title: "Octopus -- Phase 5: Neural Connection Map"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
depends_on: Phase 1-3
---

# Phase 5: Neural Connection Map

**Audit scope:** Map every meaningful inter-module connection in the Octopus multi-agent organism. Classify each connection by type, directionality, strength, frequency, fragility, observability, and failure impact. Identify critical paths, single points of failure, unobserved connections, and misleading connections.

**Evidence base:** Direct codebase analysis of `organism.py`, `wiring.py`, `governor_epoch.py`, `doctor.py`, `telemetry.py`, `fitness.py`, `chrono.py`, `neural_driver.py`, `nociceptor.py`, `reflex.py`, `unified_bus.py`, `live_loop.py`, `cardiac.py`, `germline.py`, `watchdog.py`, `approval_channel.py`, `money_gate.py`, `organ_gate.py`, `capability_gate.py`, `opslib.py`, `budgets.yaml`, `channel-status.json`, `fitness-latest.json`.

---

## 1. CONNECTION_TABLE

### Legend

| Field | Values |
|---|---|
| Type | `command` / `data` / `event` / `approval` / `memory` / `monitoring` / `economic` / `safety` |
| Direction | `uni` (unidirectional) / `bi` (bidirectional) |
| Strength | `core` (system cannot function without) / `supporting` (degrades gracefully) / `weak` (cosmetic/diagnostic) |
| Frequency | `every tick` (~5 min) / `daily` / `hourly` / `event-driven` / `once` |
| Fragility | `robust` (has fallback/retry) / `fragile` (no fallback) / `single-point` (one process/file/port) |
| Observability | `visible` (in logs/state/ledger) / `hidden` (in-memory only) |
| Failure impact | `none` / `degraded` / `critical` |

---

### C1: organism.py -> wiring.py (command: boot subsystems)

- **Source:** `organism.py` L166-199
- **Target:** `wiring.py` (`apply_profile`, `make_doctor`, `make_telegram_channel`, `make_unified_bus`, `make_lead_leg`, `make_neural_stack`, `make_live_loop`, `make_rhythm`, `make_circadian`, `make_sprint_runner`, `make_school_bridge`, `make_sensory_bus`, `make_idea_graph`)
- **Type:** command
- **Direction:** uni
- **Strength:** core
- **Frequency:** once (at boot)
- **Fragility:** fragile (any import error kills all downstream wiring; caught by outer try/except L202-203 which logs alert but continues with None objects)
- **Observability:** visible (`organism wiring: {_wire}` heartbeat L201; `wire_summary()` in ORGANISM-STATE.json)
- **Failure impact:** degraded (wiring failure is non-fatal per L202-203: `opslib.alert([f"organism wiring failed (non-fatal): {_e}"])` -- all `_wire` objects remain None, organism runs in bare mode)

**Evidence:** `organism.py:166-199` calls `_w.apply_profile()`, `_w.wire_summary()`, `_w.make_telegram_channel()`, `_w.make_doctor()`, `_w.make_unified_bus()`, `_w.make_lead_leg()`, `_w.make_neural_stack()`, `_w.make_live_loop()`, conditionally `_w.make_rhythm()`, `_w.make_circadian()`, `_w.make_sprint_runner()`, `_w.make_school_bridge()`, `_w.make_sensory_bus()`, `_w.make_idea_graph()`.

---

### C2: organism.py -> governor_epoch.py (command: run_epoch)

- **Source:** `organism.py` L283
- **Target:** `governor_epoch.py` (`run_epoch`)
- **Type:** command
- **Direction:** uni
- **Strength:** core
- **Frequency:** every tick (when `now >= next_epoch_at`; allostatic interval, default 60 min base)
- **Fragility:** fragile (no fallback -- exception caught by outer try/except L386-388 which logs to governor-alerts.md and continues)
- **Observability:** visible (epoch file written to `budget/epochs/epoch-*.json`; `last_epoch`, `pressure`, `next_epoch_minutes` in ORGANISM-STATE.json; `ALLOCATION_SHADOW` note in genome ledger)
- **Failure impact:** degraded (single epoch failure does not kill loop; next epoch recalculated)

**Evidence:** `organism.py:282-287`: `rec = governor_epoch.run_epoch(); next_epoch_at = now + rec["next_epoch_minutes"] * 60`. Protected by `_protective_skip` gate.

---

### C3: organism.py -> doctor.py (command: doctor_beat)

- **Source:** `organism.py` L308-311
- **Target:** `wiring.py` -> `doctor.py` (`doctor_beat` -> `Doctor.run_cycle`)
- **Type:** command
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** daily (every N beats, default `CHRONO_DOCTOR_EVERY_N_BEATS=1440`, i.e., ~24h at 60s beat)
- **Fragility:** robust (fail-soft: wiring.py L286-293 catches exception, returns None; organism.py L311 catches and alerts)
- **Observability:** visible (`doctor_beat error (non-fatal)` alert on failure; DOCTOR_RFC_DRAFT/DOCTOR_SANDBOX/DOCTOR_SUBMIT notes in ledger if successful)
- **Failure impact:** none (doctor is additive advisory; organism continues without it)

**Evidence:** `organism.py:308-311`: `_doctor_result = _w.doctor_beat(_doctor_inst, _cstat.get("beat", 0))`. `wiring.py:279-293`: `doctor_beat()` calls `doctor.run_cycle(beat=beat, trace=trace)` only when `beat % every_n == 0`.

---

### C4: organism.py -> telemetry.py (data: snapshot)

- **Source:** `organism.py` L220
- **Target:** `telemetry.py` (`snapshot`, `reconcile`)
- **Type:** data
- **Direction:** uni
- **Strength:** core
- **Frequency:** every tick
- **Fragility:** robust (failure caught by outer exception handler L386-388)
- **Observability:** visible (telemetry-latest.json written; `conflicts` list in ORGANISM-STATE.json; CONFLICT alerts in ledger)
- **Failure impact:** critical (if telemetry fails, organism cannot compute epoch, fitness, heartbeat -- but the outer catch L386-388 logs and continues to next tick)

**Evidence:** `organism.py:220-221`: `snap = telemetry.snapshot(); conflicts = telemetry.reconcile(snap)`. These are the first non-trivial calls in every tick loop.

---

### C5: organism.py -> fitness.py (command: compute)

- **Source:** `organism.py` L290-291
- **Target:** `fitness.py` (`compute`)
- **Type:** command
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** daily (once per `opslib.today()` change)
- **Fragility:** robust (failure caught by outer exception handler L386-388)
- **Observability:** visible (fitness-latest.json written with `authoritative` flag; `fitness_authoritative` in ORGANISM-STATE.json)
- **Failure impact:** none (fitness is advisory shadow until 28 days of data per verdict session 16)

**Evidence:** `organism.py:289-291`: `fit = fitness.compute()` inside `if opslib.today() != last_daily` block.

---

### C6: organism.py -> chrono.py (command: start_pacemaker)

- **Source:** `organism.py` L204-209
- **Target:** `chrono.py` (`start_pacemaker_thread`)
- **Type:** command
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** once (at boot)
- **Fragility:** robust (chrono import failure caught L46-49: `chrono = None; print(f"organism: chrono load failed ...")`; start_pacemaker failure caught L208-209 with alert)
- **Observability:** visible (`chrono pacemaker start failed: {e}` alert; chrono status included in ORGANISM-STATE.json pulse field)
- **Failure impact:** none (organism explicitly continues without chrono: "without heartbeat we continue" L49)

**Evidence:** `organism.py:46-49` (import guard), `L204-209` (start_pacemaker with try/except). `chrono.py` exports `start_pacemaker_thread(doctor, dispatcher)`.

---

### C7: wiring.py -> ALL subsystems (command: create)

- **Source:** `wiring.py` (factory functions)
- **Target:** doctor, telegram, unified_bus, lead_leg, neural_stack, live_loop, rhythm, circadian, sprint_runner, school_bridge, sensory_bus, idea_graph
- **Type:** command
- **Direction:** uni
- **Strength:** core (for subsystems that are enabled)
- **Frequency:** once (at boot)
- **Fragility:** robust (each factory has its own try/except; failure returns None, organism runs in degraded mode)
- **Observability:** visible (`wire_summary()` dict in ORGANISM-STATE.json shows which flags are on/off)
- **Failure impact:** degraded (individual subsystem failures are isolated; organism continues with None references)

**Evidence:** `wiring.py` L108-199: `make_doctor()`, `make_telegram_channel()`, `make_unified_bus()`, `make_lead_leg()`, `make_live_loop()`, `make_neural_stack()`, `make_rhythm()`, `make_circadian()`, `make_sprint_runner()`, `make_school_bridge()`, `make_sensory_bus()`, `make_idea_graph()`. Each wrapped in try/except returning None on failure.

---

### C8: doctor.py -> approval_channel.py (approval: submit RFC)

- **Source:** `doctor.py` L420-437 (`submit_for_approval`)
- **Target:** `approval_channel.py` (`TelegramApprovalChannel.rfc_card`)
- **Type:** approval
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** daily (whenever doctor.run_cycle produces an RFC)
- **Fragility:** fragile (if channel is None, RFC enters `submitted-no-channel` status -- permanent pending; if channel.wired is False, send silently fails)
- **Observability:** visible (RFC status in `doctor._rfcs` dict; `DOCTOR_SUBMIT` note in ledger; `submitted-no-channel` status logged)
- **Failure impact:** none (RFC remains in pending state, can be submitted later when channel connects)

**Evidence:** `doctor.py:424-426`: `if self._channel is None: rfc.status = "submitted-no-channel"; return False`. `approval_channel.py:715-730`: `rfc_card()` returns False if `not self.wired`.

---

### C9: governor_epoch.py -> budgets.yaml (data: read caps)

- **Source:** `governor_epoch.py` L110 (`opslib.load_budgets()`)
- **Target:** `budgets.yaml`
- **Type:** data
- **Direction:** uni
- **Strength:** core
- **Frequency:** every tick (called inside `allocate_dry` which runs every epoch)
- **Fragility:** single-point (corrupt YAML = RuntimeError in `opslib.load_budgets()` L125 -> FREEZE in organ_gate -> organism halt)
- **Observability:** visible (budget values in epoch JSON output; FREEZE.flag if unreadable)
- **Failure impact:** critical (budgets.yaml is single source of truth for all caps, floors, weights; corruption triggers FREEZE)

**Evidence:** `governor_epoch.py:110`: `b = opslib.load_budgets()`. `opslib.py:117-127`: `load_budgets()` raises RuntimeError if YAML missing global/projects. `organ_gate.py:72-75`: catches budgets unreadable -> `opslib.freeze()`.

---

### C10: governor_epoch.py -> fitness.py (data: read scores)

- **Source:** `governor_epoch.py` L83-102 (`_fitness_dry`)
- **Target:** `fitness.py` (conceptual -- governor uses its own internal fitness proxy, NOT `fitness.py`)
- **Type:** data
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** every tick (inside `allocate_dry`)
- **Fragility:** robust (hardcoded neutral values: `value=0.5, efficiency=0.5` per L94-95 comments)
- **Observability:** visible (fitness scores per organ in epoch JSON allocation output)
- **Failure impact:** none (governor has its own internal fitness proxy `_fitness_dry()` that uses neutral placeholders until real fitness data matures)

**Evidence:** `governor_epoch.py:83-102`: `_fitness_dry()` computes fitness internally with neutral values (`value = 0.5`, `efficiency = 0.5`). Comment L86: "fitness numeric until ~4 weeks of data is only shadow".

---

### C11: doctor.py -> sandbox (command: run tests)

- **Source:** `doctor.py` L352-389 (`run_sandbox`)
- **Target:** subprocess (temp directory)
- **Type:** command
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** daily (when doctor.run_cycle fires)
- **Fragility:** robust (sandbox in tempdir; timeout 120s; cleanup in finally block; failure sets `sandbox-skip` status)
- **Observability:** visible (`DOCTOR_SANDBOX` note in ledger with test exit/stdout/stderr)
- **Failure impact:** none (sandbox failure does not prevent RFC submission; just adds critic concern)

**Evidence:** `doctor.py:352-389`: `run_sandbox()` creates `tempfile.mkdtemp(prefix=f"doctor-sandbox-{rfc.rfc_id}-")`, runs suite_cmd with `timeout=120`, cleanup via `shutil.rmtree(sandbox_dir, ignore_errors=True)` in finally.

---

### C12: neural_driver.py -> nociceptor.py (data: pain signal)

- **Source:** `neural_driver.py` L69-71 (`NeuralDriver.evaluate`)
- **Target:** `nociceptor.py` (`Nociceptor.measure`)
- **Type:** data
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** every tick (when `OCTOPUS_WIRE_NEURAL=1`)
- **Fragility:** robust (Nociceptor.measure has no external dependencies; pure computation)
- **Observability:** visible (pain_level included in neural_beat result -> protective_override decision logged)
- **Failure impact:** none (neural stack is additive advisory)

**Evidence:** `neural_driver.py:65-79`: `evaluate()` calls `self.nociceptor.measure(budget_pct=..., freeze_active=..., afferent_ratio=..., sigma=...)` then `self.reflex.evaluate(snap.to_dict())`. `wiring.py:572-606`: `neural_beat()` calls `driver.evaluate()`.

---

### C13: neural_driver.py -> reflex.py (data: reflex)

- **Source:** `neural_driver.py` L79
- **Target:** `reflex.py` (`ReflexArc.evaluate`)
- **Type:** data
- **Direction:** uni
- **Strength:** supporting
- **Frequency:** every tick (when `OCTOPUS_WIRE_NEURAL=1`)
- **Fragility:** robust (pure computation, no external deps)
- **Observability:** visible (reflex actions included in neural_beat result; critical reflexes trigger `protective_override` logged as `NEURAL OVERRIDE`)
- **Failure impact:** degraded (without reflex evaluation, protective halt would not trigger -- but neural stack failure is non-fatal)

**Evidence:** `neural_driver.py:79`: `reflexes = self.reflex.evaluate(snap.to_dict())`. `wiring.py:613-643`: `protective_override()` checks `pain > 0.7` and `critical reflexes` to trigger protective_halt.

---

### C14: unified_bus.py -> ledger (data: append events)

- **Source:** `unified_bus.py` L68-80 (`UnifiedBus.publish`)
- **Target:** genome ledger (LANGAR, via `opslib.genome_ledger()`)
- **Type:** memory
- **Direction:** uni
- **Strength:** core (when bus is active)
- **Frequency:** event-driven (every publish call)
- **Fragility:** fragile (fail-closed: if ledger write fails, publish returns entry from ledger only; if ledger itself is None, calls `opslib.genome_ledger()`)
- **Observability:** visible (all events in genome ledger `ledger.jsonl`; hash-chain preserved)
- **Failure impact:** degraded (individual publish failure does not crash bus; chrono checkpoint is secondary)

**Evidence:** `unified_bus.py:68-80`: `publish()` calls `lg.append(event_type, payload, actor=actor, is_human=is_human, beat=beat)` first (genome ledger = source of truth), then chrono checkpoint.

---

### C15: live_loop.py -> unified_bus.py (event: subscribe)

- **Source:** `live_loop.py` L59-62 (`LiveLoop.__init__`)
- **Target:** `unified_bus.py` (`UnifiedBus.subscribe`)
- **Type:** event
- **Direction:** bi (subscribe + callback)
- **Strength:** supporting
- **Frequency:** once (at boot, subscriptions registered)
- **Fragility:** robust (bus failure returns `_InMemoryBus()` fallback L44; subscriber failure is caught in `_notify` L62)
- **Observability:** hidden (advisory signals stored in `self._advisory_signals` list, never persisted to disk)
- **Failure impact:** none (advisory signals are non-enforcer; loss means no cosmetic advisory data)

**Evidence:** `live_loop.py:59-62`: subscribes to `RHYTHM`, `SPECTRAL`, `AFFERENT`, `DOCTOR` event types. `unified_bus.py:50-53`: `subscribe(callback, event_type)`. `unified_bus.py:55-63`: `_notify()` catches subscriber exceptions silently.

---

### C16: cardiac.py -> organism.py (data: effective_period)

- **Source:** `organism.py` L392-402
- **Target:** `cardiac.py` (`effective_period`)
- **Type:** data
- **Direction:** uni (cardiac advises, organism consumes)
- **Strength:** weak (advisory; organism defaults to TICK_SECONDS if cardiac unavailable)
- **Frequency:** every tick (when `OCTOPUS_WIRE_BIO=1`)
- **Fragility:** robust (failure caught L401-402: `pass`; organism falls back to `TICK_SECONDS`)
- **Observability:** visible (`cardiac` field in ORGANISM-STATE.json via `cardiac_mod.status_snapshot()` L382)
- **Failure impact:** none (organism uses fixed TICK_SECONDS=300s when cardiac is off)

**Evidence:** `organism.py:392-402`: `if _cardiac_mod is not None: _eff = _cardiac_mod.effective_period(base_period_s=TICK_SECONDS, budget=..., baro=...); _sleep_s = _eff["period_s"]`. Cardiac import guarded at L59-64.

---

### C17: germline.py -> organism.py (data: lag_alarm)

- **Source:** `organism.py` L234-235 (`_w.enrich_state_with_germline(germ)`)
- **Target:** `germline.py` (`lag_alarm`)
- **Type:** data
- **Direction:** uni
- **Strength:** supporting (safety-vital monitoring, not functional)
- **Frequency:** every tick (always on -- no flag required per wiring.py L13)
- **Fragility:** robust (fallback to `opslib.germline_lag_hours()` if germline import fails; CRIT-tier alert L100-103)
- **Observability:** visible (`germline_lag_h` and `germline_alert` in ORGANISM-STATE.json; CRIT alerts via `opslib.alert()`)
- **Failure impact:** none (germline lag is read-only enrichment; organism continues regardless)

**Evidence:** `wiring.py:80-104`: `enrich_state_with_germlime()` imports germline, calls `lag_alarm()`, falls back to `opslib.germline_lag_hours()`. Always called (no flag). `organism.py:234-235`: `_w.enrich_state_with_germline(germ)` called unconditionally every tick.

---

### C18: watchdog.py -> organism.py (monitoring: port check)

- **Source:** `watchdog.py` (`should_revive`)
- **Target:** organism port 8771
- **Type:** monitoring
- **Direction:** uni
- **Strength:** weak (external revival tool, not part of organism loop)
- **Frequency:** periodic (Scheduled Task, external to organism)
- **Fragility:** robust (pure logic, no side effects; `_port_alive()` uses socket connection test)
- **Observability:** visible (returns `(should, reason)` tuple; PS1 script logs output)
- **Failure impact:** none (watchdog only revives; failure to revive = organism stays dead, no damage)

**Evidence:** `watchdog.py:39-60`: `should_revive()` checks: (1) STOP flags yield, (2) port alive = no action, (3) no state file = first-birth guard (no auto-launch). `watchdog.py:35`: `ORGANISM_PORT = 8771`.

---

### C19: telegram -> approval_channel -> doctor (approval: T-2 settle)

- **Source:** `approval_channel.py` L363-405 (`dispatch_callback` -> `_do_approve`)
- **Target:** `doctor.py` (via `on_human_judgment` -> `gate.settle` -> recorded approval)
- **Type:** approval
- **Direction:** bi (telegram receives human click -> dispatches to gate -> gate settles -> approval recorded for doctor)
- **Strength:** core (only path for irreversible/money effects per TINV-7)
- **Frequency:** event-driven (human click on Telegram)
- **Fragility:** fragile (currently dead: `channel-status.json` shows telegram `live: false, mode: stub(no-creds)`; `NotWiredStub` returns None for all approvals; EffectorGate injection from chrono is optional)
- **Observability:** visible (quarantine log, `human_judgment` ledger note with `is_human=1`, `age_tick+1`, pending/approved status in `_pending` dict)
- **Failure impact:** critical for live mode (no approval = no settle = all money effects blocked -- which is the intended fail-closed behavior for paper phase)

**Evidence:** `approval_channel.py:126-158`: `TelegramApprovalChannel.__init__` receives `gate` and `ledger` from chrono. `approval_channel.py:388-405`: `_do_approve()` calls `_on_human_judgment(judgment, gate=self._gate, ledger=self._ledger)` then `self._settle_effect(effect_id)`. `channel-status.json:12-21`: telegram is `"live": false, "mode": "stub(no-creds)"`.

---

### C20: money_gate -> organ_gate -> budget/opslib (safety: dual-lock)

- **Source:** `capability_gate.py` L94-104 (`require`)
- **Target:** `money_gate.check()` + `capability_gate.is_open()` + `organ_gate.reserve()`
- **Type:** safety
- **Direction:** uni
- **Strength:** core (only path for any real money spend)
- **Frequency:** event-driven (before every LLM call or money effect)
- **Fragility:** robust (three independent gates, each fail-closed; any deny = total deny)
- **Observability:** visible (`organ-gate-log.jsonl` records every reserve/settle; capability marker in `CAPABILITY-OK.flag`; money gate denial logged)
- **Failure impact:** critical (denial = money blocked -- intended fail-closed behavior; no bypass exists)

**Evidence:** `capability_gate.py:94-104`: `require()` calls `is_open()` (3 conditions AND: capability_ok + live_enabled + per-action approval) then `money_gate.check()` (human_gate threshold + approval match). `money_gate.py:34-46`: `check()` uses `human_gate_aud()` from budgets.yaml (min of YAML value and hardcoded 20.0). `organ_gate.py:60-80`: `reserve()` checks STOP/FREEZE/organ exists/monthly cap, then calls `budget_gate.reserve()`.

---

### C21: organism.py -> opslib.py (data: shared state/paths)

- **Source:** `organism.py` L38 (import), multiple calls
- **Target:** `opslib.py` (STATE_DIR, BUDGETS_YAML, STOP_ORGANISM, heartbeat, halted, frozen, now_iso, today, load_budgets, LockedJson, etc.)
- **Type:** data
- **Direction:** bi (organism reads state/flags, writes via opslib helpers)
- **Strength:** core
- **Frequency:** every tick
- **Fragility:** single-point (import error in opslib = organism crash at L38; no fallback for opslib itself)
- **Observability:** visible (all opslib writes go to state files, heartbeat, ledger, alerts)
- **Failure impact:** critical (opslib is imported at module level L38; `ImportError` would prevent organism from starting entirely)

**Evidence:** `organism.py:38`: `import opslib` is at module level (not in try/except). Used for: `STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"` (L53), `opslib.heartbeat()` (L151), `opslib.STOP_ORGANISM.exists()` (L216), `opslib.halted()` (L216), `opslib.now_iso()` (L54), `opslib.today()` (L289), `opslib.load_budgets()` (via governor), `opslib.LockedJson()` (L135).

---

### C22: organism.py -> port 8771 (monitoring: single-instance lock)

- **Source:** `organism.py` L144-148
- **Target:** `127.0.0.1:8771` (exclusive socket bind)
- **Type:** monitoring
- **Direction:** uni
- **Strength:** core
- **Frequency:** once (at boot)
- **Fragility:** single-point (port conflict = immediate clean exit L147: `return 0`; no retry, no fallback port)
- **Observability:** visible (console message: "another instance running on port -- exit clean")
- **Failure impact:** critical for startup (organism refuses to start if port is taken -- by design, prevents duplicate instances)

**Evidence:** `organism.py:51`: `PORT = 8771`. `organism.py:144-148`: `_serve(port)` binds exclusive; `OSError` catch -> `print(f"organism: another instance on {port} -- clean exit.")` -> `return 0`. `organism.py:67-76`: `_ExclusiveHTTPServer` sets `allow_reuse_address = False` + `SO_EXCLUSIVEADDRUSE` on Windows.

---

### C23: wiring.py -> epistemics (command: epistemics_beat)

- **Source:** `wiring.py` L516-548 (`epistemics_beat`)
- **Target:** `epistemics/run_offloop.py` (`compute_all`)
- **Type:** command
- **Direction:** uni
- **Strength:** weak (advisory, non-enforcer)
- **Frequency:** every N beats (default `CHRONO_EPISTEMICS_EVERY_N_BEATS=720`, ~12h)
- **Fragility:** robust (fail-soft: exception caught, returns None)
- **Observability:** visible (EPISTEMICS advisory published to bus; metrics count in result)
- **Failure impact:** none (epistemics is advisory annotation only -- "non-enforcer, no-collision")

**Evidence:** `wiring.py:516-548`: `epistemics_beat()` calls `compute_all()`, publishes advisory per metric to bus. `organism.py:363-367`: called when `OCTOPUS_WIRE_EPISTEMICS=1`.

---

### C24: wiring.py -> evolution (command: _evolve_rfc)

- **Source:** `wiring.py:675-732` (via `doctor.py:541-542`)
- **Target:** `doctor/evolution.py` (`RFCArchive`, `measured_lift`, `tournament_rank`, `survivor`)
- **Type:** command
- **Direction:** uni
- **Strength:** weak (propose-only, behind `OCTOPUS_WIRE_EVOLUTION=1`)
- **Frequency:** daily (inside doctor.run_cycle)
- **Fragility:** robust (fail-soft: import failure returns error dict)
- **Observability:** visible (DOCTOR_EVOLUTION_WINNER note in ledger; archive_size, winner_lift in result)
- **Failure impact:** none (evolution is propose-only; doctor submits without it)

**Evidence:** `doctor.py:541-542`: `if os.environ.get("OCTOPUS_WIRE_EVOLUTION") == "1": evolution_report = self._evolve_rfc(rfc, bottleneck, trace)`.

---

### C25: wiring.py -> box-of-agents (command: _run_box_cycle)

- **Source:** `doctor.py:534-535` (via wiring.py -> doctor)
- **Target:** `doctor/box/box.py` (`Box`, `BoxConfig`)
- **Type:** command
- **Direction:** uni
- **Strength:** weak (propose-only, behind `OCTOPUS_WIRE_BOX=1`)
- **Frequency:** daily (inside doctor.run_cycle)
- **Fragility:** robust (fail-soft: import failure returns error dict; Box.run_tick has Warden 2% cap + STOP-obey)
- **Observability:** hidden (Box agent metrics are in-memory only in `Box` object; not persisted to state files)
- **Failure impact:** none (box is propose-only; insights go through b3_bridge to doctor.submit)

**Evidence:** `doctor.py:552-645`: `_run_box_cycle()` creates Box, calls `box.run_tick(trace=trace)`, `b3_bridge.box_to_doctor_pipeline()`, `b4_fusion.compute_phi_t()`.

---

### Summary Table

| # | Source | Target | Type | Direction | Strength | Frequency | Fragility | Observable | Impact |
|---|---|---|---|---|---|---|---|---|---|
| C1 | organism | wiring | command | uni | core | once | fragile | visible | degraded |
| C2 | organism | governor_epoch | command | uni | core | every tick | fragile | visible | degraded |
| C3 | organism | doctor | command | uni | supporting | daily | robust | visible | none |
| C4 | organism | telemetry | data | uni | core | every tick | robust | visible | critical |
| C5 | organism | fitness | command | uni | supporting | daily | robust | visible | none |
| C6 | organism | chrono | command | uni | supporting | once | robust | visible | none |
| C7 | wiring | ALL subsystems | command | uni | core | once | robust | visible | degraded |
| C8 | doctor | approval_channel | approval | uni | supporting | daily | fragile | visible | none |
| C9 | governor_epoch | budgets.yaml | data | uni | core | every tick | single-point | visible | critical |
| C10 | governor_epoch | fitness (internal) | data | uni | supporting | every tick | robust | visible | none |
| C11 | doctor | sandbox | command | uni | supporting | daily | robust | visible | none |
| C12 | neural_driver | nociceptor | data | uni | supporting | every tick | robust | visible | none |
| C13 | neural_driver | reflex | data | uni | supporting | every tick | robust | visible | degraded |
| C14 | unified_bus | ledger | memory | uni | core | event-driven | fragile | visible | degraded |
| C15 | live_loop | unified_bus | event | bi | supporting | once | robust | hidden | none |
| C16 | cardiac | organism | data | uni | weak | every tick | robust | visible | none |
| C17 | germline | organism | data | uni | supporting | every tick | robust | visible | none |
| C18 | watchdog | organism | monitoring | uni | weak | periodic | robust | visible | none |
| C19 | telegram -> approval -> doctor | approval | bi | core | event-driven | fragile | visible | critical |
| C20 | capability_gate -> money_gate -> organ_gate | safety | uni | core | event-driven | robust | visible | critical |
| C21 | organism | opslib | data | bi | core | every tick | single-point | visible | critical |
| C22 | organism | port 8771 | monitoring | uni | core | once | single-point | visible | critical |
| C23 | wiring | epistemics | command | uni | weak | every 12h | robust | visible | none |
| C24 | wiring -> doctor | evolution | command | uni | weak | daily | robust | visible | none |
| C25 | wiring -> doctor | box-of-agents | command | uni | weak | daily | robust | hidden | none |

---

## 2. CRITICAL_PATHS

### 2.1 Boot Path

```
organism.py::main()
  |-- _serve(port)                          # bind exclusive 127.0.0.1:8771
  |     FAIL: OSError -> clean exit (C22)
  |-- import opslib                         # shared library (C21)
  |     FAIL: ImportError -> process won't exist
  |-- import wiring as _w                   # (C1)
  |     |-- _w.apply_profile()              # set flags from OCTOPUS_PROFILE
  |     |-- _w.wire_summary()               # read all flag states
  |     |-- _w.make_telegram_channel()      # auto-on if TELEGRAM_BOT_TOKEN
  |     |-- _w.make_doctor()                # OCTOPUS_WIRE_DOCTOR
  |     |-- _w.make_unified_bus()            # OCTOPUS_WIRE_UNIFIED
  |     |-- _w.make_lead_leg()              # OCTOPUS_WIRE_LEAD
  |     |-- _w.make_neural_stack()          # OCTOPUS_WIRE_NEURAL
  |     |-- _w.make_rhythm()                # OCTOPUS_WIRE_NEURAL
  |     |-- _w.make_circadian()             # OCTOPUS_WIRE_NEURAL
  |     |-- _w.make_sprint_runner()         # OCTOPUS_WIRE_NEURAL
  |     |-- _w.make_school_bridge()         # OCTOPUS_WIRE_CONSOLIDATION
  |     |-- _w.make_sensory_bus()            # OCTOPUS_WIRE_SCHOOL
  |     |-- _w.make_idea_graph()            # OCTOPUS_WIRE_IDEAS
  |     |-- _w.make_live_loop()             # always (if LiveLoop importable)
  |     FAIL (any): non-fatal -> None, organism runs bare
  |-- chrono.start_pacemaker_thread()       # (C6)
  |     FAIL: non-fatal -> chrono=None, no heartbeat
  `-- Enter main loop
```

**Single points in boot:** port 8771 bind (C22), opslib import (C21). Everything else is fail-soft.

### 2.2 Tick Path

```
organism.py main loop (every ~5 min, or cardiac-adjusted)
  |-- STOP check (STOP_ORGANISM / halted)  # kill-switch first
  |-- telemetry.snapshot()                  # (C4) READ genome ledger + core.db
  |-- telemetry.reconcile(snap)             # (C4) FREEZE if divergence > 20%
  |-- chrono.status()                        # (C6) beat count
  |-- wiring.enrich_state_with_germline()   # (C17) backup lag check (always on)
  |-- Rhythm beat                            # (neural) mode_color GREEN/AMBER/RED
  |-- Circadian readiness                    # (neural) hour-of-day awareness
  |-- neural_beat()                          # (C12, C13) nociceptor + reflex
  |     |-- NeuralDriver.evaluate()
  |     |     |-- Nociceptor.measure()       # pain signal
  |     |     |-- ReflexArc.evaluate()       # protective reflexes
  |     |     `-- SignalHub.collect()        # internal signal aggregation
  |     `-- protective_override()            # pain>0.7 -> halt; critical reflex -> throttle
  |-- IF NOT protective_skip:
  |     |-- governor_epoch.run_epoch()        # (C2) allostatic epoch
  |     |     |-- pressure_state(snap)       # velocity, deadline, anomaly
  |     |     |-- allocate_dry(snap)         # (C9) reads budgets.yaml
  |     |     |-- allocate_llm(snap, alloc)  # dual-gate: ACTIVATION + organ_gate
  |     |     `-- write epoch JSON + ledger NOTE
  |     |-- IF daily:
  |     |     |-- fitness.compute()           # (C5) fitness-latest.json
  |     |     |-- replication.evaluate()      # sigma calculation
  |     |     `-- ledger NOTE ORGANISM_DAILY
  |     |-- doctor_beat()                    # (C3) every N beats
  |     |     `-- doctor.run_cycle()
  |     |           |-- mine() -> propose_rfc() -> run_sandbox() -> submit_for_approval()
  |     |           |-- [box cycle] (if WIRE_BOX)
  |     |           `-- [evolution] (if WIRE_EVOLUTION)
  |     |-- consolidation_beat()             # every N beats
  |     |-- afferent_beat()                  # every N beats
  |     |-- publish_tick_signals()           # (C15) advisory to bus
  |     |-- leg_beat()                       # LeadLeg HLC + ack
  |     |-- idea_beat()                      # every N beats
  |     `-- epistemics_beat()                # every N beats
  |-- _write_state()                         # ORGANISM-STATE.json
  |-- cardiac.effective_period()             # (C16) dynamic sleep duration
  `-- time.sleep(_sleep_s)
```

**Observation:** The tick path has a single outer try/except (L383-388) that catches ALL exceptions, logs to governor-alerts.md, and continues. This is intentional (charter S4: "silent crash is the worst bug"), but it means any silent failure in the inner blocks is invisible unless it produces an alert.

### 2.3 Approval Path

```
Human clicks Telegram button
  |-- Telegram API -> getUpdates (long-poll)
  |-- approval_channel.poll_once()
  |     |-- callback_query detected
  |     |-- dispatch_callback("app:approve:<effect_id>:<token>")
  |     |     |-- verify effect_id in _pending
  |     |     |-- verify token (SHA256 match, anti-forgery)
  |     |     `-- _do_approve(effect_id, meta)
  |     |           |-- _on_human_judgment() -> chrono.on_human_judgment()
  |     |           |     `-- ledger.append(is_human=True)  # age_tick+1
  |     |           |-- _settle_effect() -> gate.settle(effect_id)
  |     |           `-- _record_approval() -> self._approvals[action_id]
  |     `-- answerCallbackQuery("confirmed")
  `-- approval_channel.approval_for() returns valid Approval
        |-- money_gate.check() -> allow (C20)
        `-- effect executes
```

**Current state:** PATH IS DEAD. Telegram is `live: false, mode: stub(no-creds)` per `channel-status.json`. The NotWiredStub returns None for all approvals. All money gates are closed. This is the intended fail-closed state for the paper phase.

### 2.4 Safety Path (Triple-Lock)

```
Any money effect request
  `-- capability_gate.require(action_id, amount_aud, channel)  # (C20)
        |-- is_open()
        |     |-- capability_ok()       # CAPABILITY-OK.flag fingerprint matches source
        |     |-- live_enabled()        # LIVE-ENABLED.flag exists (human-created only)
        |     `-- channel.approval_for() # per-action human approval match
        `-- money_gate.check(amount_aud, action_id, channel)
              |-- amount <= human_gate_aud (AU$20)  -> allow
              `-- amount > human_gate_aud -> require channel.approval_for()
```

**Three independent AND conditions:**
1. **Capability gate:** Source fingerprint of money code must match last green test run
2. **Live enabled:** Human must create LIVE-ENABLED.flag (never by code)
3. **Per-action approval:** Human must click approve in Telegram for this specific action
4. **Money gate:** Under AU$20 auto-allow; over AU$20 requires same approval

**Current state:** ALL FOUR CONDITIONS FAIL. CAPABILITY-OK.flag likely absent (no green test run documented). LIVE-ENABLED.flag does not exist. Telegram is dead (NotWiredStub). This is maximum safety.

---

## 3. SINGLE_POINTS_OF_FAILURE

### SPOF-1: organism.py (single process)

- **Nature:** Single Python process running the main loop
- **Evidence:** `organism.py::main()` L141-403 is the only entry point. No process supervisor, no fork, no worker pool.
- **Failure mode:** Unhandled KeyboardInterrupt (L383) or process kill = all organs dead immediately
- **Mitigation:** watchdog.py (`should_revive()`) can restart the process from outside, but only if STOP flags are clear and state file exists. Watchdog is external (Scheduled Task), not part of organism.
- **Severity:** critical -- but by design. The organism is a single-threaded event loop. Complexity of multi-process coordination is intentionally avoided.
- **Monitoring:** watchdog.py checks port 8771 liveness; HEARTBEAT.md written hourly; ORGANISM-STATE.json written every tick

### SPOF-2: opslib.py (shared library)

- **Nature:** Imported at module level by organism.py (L38) without try/except
- **Evidence:** `organism.py:38`: `import opslib` is unconditional. If opslib.py has a syntax error, import error, or missing dependency (e.g., PyYAML), the organism process cannot start at all.
- **Failure mode:** ImportError on startup = cascading failure of ALL modules that depend on opslib (telemetry, governor, fitness, wiring, doctor, etc.)
- **Mitigation:** None. opslib is the foundation layer. A syntax error or broken import in opslib kills everything.
- **Severity:** critical -- but low probability in steady state (opslib is stable, stdlib-only except PyYAML)
- **Counter-evidence:** Most other imports in organism.py ARE guarded (chrono L46-49, wiring L166-203, cardiac L59-64). But opslib itself cannot be guarded because it provides the guard functions (alert, heartbeat, etc.).

### SPOF-3: budgets.yaml (single source of truth)

- **Nature:** Single YAML file read by opslib.load_budgets() with caching
- **Evidence:** `opslib.py:117-127`: `load_budgets()` reads `BUDGETS_YAML` (budget/budgets.yaml), raises RuntimeError if missing global/projects. Used by: governor_epoch.allocate_dry() (C9), organ_gate.reserve() (C20), fitness.compute() (C5), money_gate.human_gate_aud() (C20), telemetry (organ mapping).
- **Failure mode:** Corrupt YAML = RuntimeError -> FREEZE in organ_gate (L72-75) -> organism halt. Missing file = same.
- **Mitigation:** File is in git (version controlled). But no backup copy or fallback. The cache (`_budgets_cache`) means a successful read at boot persists for the process lifetime.
- **Severity:** critical for all budget-dependent paths
- **Observation:** budgets.yaml is also the ONLY place where organ definitions (projects section), caps, floors, weights, and routing are defined. I6 (invariant): no edits to budgets.yaml from code -- only human diffs.

### SPOF-4: port 8771 (single-instance lock)

- **Nature:** Exclusive socket bind on 127.0.0.1:8771 serves as both HTTP status server and single-instance lock
- **Evidence:** `organism.py:51`: `PORT = 8771`. `organism.py:67-76`: `_ExclusiveHTTPServer` with `allow_reuse_address = False` + `SO_EXCLUSIVEADDRUSE` on Windows. `organism.py:144-148`: OSError on bind = clean exit.
- **Failure mode:** Port conflict (another process or zombie) = organism refuses to start. No retry, no fallback port.
- **Mitigation:** Only one instance can run (by design). Port conflict means another instance IS running (which is the correct behavior). Zombie port (process died without releasing) requires manual cleanup or OS timeout.
- **Severity:** critical for startup only (not for running organism)

### SPOF-5: genome ledger (append-only hash chain)

- **Nature:** Single file `ledger.jsonl` in genome-system directory
- **Evidence:** `opslib.py` -> `genome_ledger()` returns Ledger instance writing to GENOME_DIR/ledger/ledger.jsonl. Used by unified_bus.publish() (C14), doctor._note() (C8), governor_epoch (C2), organism ledger_note() (C5).
- **Failure mode:** Disk full or permission error on ledger write = events lost (but organism continues -- ledger failure is non-fatal in most paths)
- **Severity:** degraded (data loss, not process death). Ledger is append-only so corruption risk is low (atomic writes via tmp+replace pattern in LockedJson).

---

## 4. UNOBSERVED_CONNECTIONS

### UC-1: LiveLoop advisory signals (in-memory only)

- **Source:** `live_loop.py` L56: `self._advisory_signals: list[dict] = []`
- **Nature:** Advisory signals (RHYTHM, SPECTRAL, AFFERENT, DOCTOR) received via bus.subscribe() are stored only in the `_advisory_signals` list attribute of the LiveLoop object.
- **Evidence:** `live_loop.py:59-62`: subscribes to event types; `live_loop.py:_on_advisory()` appends to `self._advisory_signals`. No persistence to disk, no write to state files, no ledger entry.
- **Impact:** On organism restart, all advisory signal history is lost. No way to reconstruct what rhythm/spectral/afferent/doctor signals were published in previous ticks.
- **Severity:** none (advisory signals are non-enforcer by design), but this makes debugging and post-mortem analysis impossible for these signals.

### UC-2: Box-of-Agents agent metrics (in-memory only)

- **Source:** `doctor.py` L589: `snap = self._box.run_tick(trace=trace)`
- **Nature:** The Box micro-world maintains agent states (cognitive hidden states, stress, coherence, flagged agents) entirely in memory. The `Box` object is stored as `self._box` on the Doctor instance, which is itself in-memory (`_doctor_inst` in organism.py).
- **Evidence:** `doctor.py:574-583`: `self._box = Box(BoxConfig(seed=42))` created lazily in memory. No persistence method exists. `doctor.py:609`: `agent_states = [a.cognitive.hidden_state[0] ...]` reads directly from in-memory agent objects.
- **Impact:** On restart, entire Box evolutionary history is lost. Agent populations, phi_t measurements, novelty signals, Warden budget tracking -- all reset to initial state.
- **Severity:** low (box is propose-only, behind flag, non-enforcer), but makes Box experiments non-reproducible across restarts.

### UC-3: Neural SignalHub internal state (not persisted)

- **Source:** `neural_driver.py` L20-25: `self.hub = SignalHub()`
- **Nature:** NeuralDriver contains a SignalHub instance that aggregates signals (pain, rhythm, sensory, spectral, budget) per beat. The hub's internal state (signal history, correlations, Hebbian associations) is not persisted.
- **Evidence:** `neural_driver.py:20-25`: `self.hub = SignalHub(); self.reflex = ReflexArc(); self.nociceptor = Nociceptor()`. `wiring.py:590-595`: `neural_stack["hebbian"].observe(signals)` -- Hebbian associations are in-memory. `wiring.py:596-602`: consolidation runs every 10 beats but results are not persisted.
- **Impact:** Neural learning (Hebbian associations, consolidation insights) is lost on restart. The system cannot build long-term neural patterns.
- **Severity:** low (neural stack is advisory, behind flag), but means "neural memory" is a misnomer -- there is no actual memory across restarts.

### UC-4: Telegram quarantine log (in-memory only)

- **Source:** `approval_channel.py` L156: `self._quarantine: list[dict] = []`
- **Nature:** All incoming Telegram messages are quarantined in memory. On restart, quarantine is cleared.
- **Evidence:** `approval_channel.py:248-254`: `self._quarantine.append({"update_id": uid, "chat_id": chat_id, "from_id": from_id, "text": ...})`. No persistence. Offset IS persisted (`telegram_offset.json` L824-854), but quarantine content is not.
- **Impact:** On restart, message history is lost. Only offset is preserved, so old messages are skipped.
- **Severity:** none (messages are DATA not commands per T-8; no action taken on content)

### UC-5: Epoch history (file-per-epoch, not aggregated)

- **Source:** `governor_epoch.py:329-331`
- **Nature:** Each epoch writes a separate JSON file `budget/epochs/epoch-<timestamp>.json`. There is no aggregated epoch history or trend analysis. Files accumulate indefinitely.
- **Evidence:** `governor_epoch.py:329-331`: `fname = EPOCH_DIR / ("epoch-" + dt.datetime.now().strftime("%Y%m%dT%H%M%S%f") + ".json")`. No cleanup, no aggregation, no max retention.
- **Impact:** Disk usage grows linearly with epochs. No built-in way to query historical epoch trends without reading all files.
- **Severity:** low (disk space issue, not functional)

---

## 5. MISLEADING_CONNECTIONS

### MC-1: Telegram channel appears connected but is dead

- **Appearance:** `channel-status.json` lists telegram as a channel with fields: `channel: "telegram"`, `live: false`, `mode: "stub(no-creds)"`, `required_env: ["TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID"]`.
- **Reality:** The TelegramApprovalChannel code path is fully implemented (T-1 through T-8), but no credentials are provisioned. The `wiring.py:make_telegram_channel()` function (L121-142) returns `None` when `TELEGRAM_BOT_TOKEN` env var is absent. Even when the channel object is created, `approval_channel.py:160-162`: `wired` property returns False if token or owner is missing. All `approval_for()` calls return None. All `send_text()` calls return False silently.
- **Misleading signal:** `channel-status.json` exists and has a telegram section, suggesting the channel is configured. But `live: false, mode: "stub(no-creds)"` explicitly documents it is dead.
- **Impact on audit:** Any analysis of the approval path (C19) must note that the entire Telegram -> human approval flow is non-functional. The safety gates (C20) are all closed, which is correct for paper phase, but means the approval path cannot be tested end-to-end.

### MC-2: Epistemics appears as a connected subsystem but produces nothing authoritative

- **Appearance:** `wiring.py:516-548` has full `epistemics_beat()` wiring. `wiring.py:320` tracks `wire_epistemics` in `wire_summary()`. `organism.py:363-367` calls epistemics_beat every N beats.
- **Reality:** The epistemics module (`epistemics/run_offloop.py`) is behind `OCTOPUS_WIRE_EPISTEMICS` flag (default off). Even when enabled, the output is explicitly advisory-only: `wiring.py:519`: "advisory only -- non-enforcer. no-collision: only annotate, not fork." The code computes five metrics and publishes them to the bus, but no consumer acts on them.
- **Misleading signal:** The wiring infrastructure suggests epistemics is an active organ producing actionable intelligence. In reality, it is a passive measurement module with no enforcement power and no consumers.
- **Impact on audit:** Epistemics should be classified as diagnostic/observability, not as a functional organ.

### MC-3: Fitness appears to compute but is non-authoritative

- **Appearance:** `fitness-latest.json` exists with a full structure: `authoritative: false`, `cells: {}`, `weights: {...}`, `experience_span_days: 0`. `fitness.compute()` runs daily in organism.py (C5).
- **Reality:** `fitness.py:19-22`: "fitness numeric until ~4 weeks of data is only shadow." `fitness-latest.json:3-4`: `"authoritative": false, "experience_span_days": 0`. The `cells` dict is empty. No consumer is allowed to make live decisions based on fitness scores until `authoritative` becomes true (after 28 days of EXPERIENCE events in ledger).
- **Misleading signal:** The fitness computation runs and produces output files, suggesting it is actively governing resource allocation. In reality, governor_epoch uses its own internal `_fitness_dry()` with hardcoded neutral values (`value=0.5, efficiency=0.5`), completely independent of `fitness.py`.
- **Evidence:** `governor_epoch.py:86-95` comment: "EFFICIENCY is still neutral -- ~4 weeks of data needed; verdict session 16: fitness numeric until then only shadow."

### MC-4: Doctor appears to evolve the codebase but is propose-only

- **Appearance:** `doctor.py` has a full pipeline: mine -> propose_rfc -> run_sandbox -> critic_review -> submit_for_approval -> apply_merge. It writes RFC files to `knowledge/internal/`.
- **Reality:** `doctor.py:9`: "No automatic merge without human-append (TINV-7)." `doctor.py:439-455`: `apply_merge()` only runs after human Telegram approval. Since Telegram is dead (MC-1), `apply_merge` can never execute. All RFCs accumulate in `submitted-no-channel` status. The sandbox tests run but results are never acted upon.
- **Misleading signal:** Doctor produces RFC markdown files, sandbox test results, and ledger entries, suggesting active code evolution. In reality, no code has ever been modified by the doctor (no merged RFC exists).
- **Impact on audit:** Doctor's evolution pipeline is correctly designed as propose-only, but its apparent activity (files, ledger entries) should not be interpreted as actual system modification.

### MC-5: UnifiedBus appears to be a central nervous system but most modules bypass it

- **Appearance:** `unified_bus.py` is described as "convergence bridge" (L1-2) with `publish()` going to both genome ledger and chrono checkpoint. `live_loop.py` subscribes to bus events.
- **Reality:** Most modules do NOT use UnifiedBus for their primary data flow. `telemetry.py` reads directly from ledger.jsonl and core.db. `governor_epoch.py` reads directly from budgets.yaml and calls telemetry directly. `doctor.py` reads state files directly and writes to ledger directly via `opslib.ledger_note()`. Only advisory signals (RHYTHM, SPECTRAL, AFFERENT, DOCTOR) flow through the bus. The bus is behind `OCTOPUS_WIRE_UNIFIED` flag (default off in bare profile).
- **Misleading signal:** The name "UnifiedBus" and the documentation suggest all inter-module communication goes through it. In reality, it is an optional advisory signal bus, not a central data bus.
- **Evidence:** `wiring.py:146-155`: `make_unified_bus()` returns None when flag is off. Even when created, `live_loop.py:44`: `self.bus = bus or _InMemoryBus()` -- creates an in-memory fallback if no real bus is provided. Most data flows through direct function calls, not the bus.

---

## 6. CROSS-CUTTING OBSERVATIONS

### 6.1 Flag-Proliferation Pattern

The system has 20+ env-flags controlling wiring (OCTOPUS_WIRE_DOCTOR, OCTOPUS_WIRE_NEURAL, OCTOPUS_WIRE_UNIFIED, OCTOPUS_WIRE_LEAD, OCTOPUS_WIRE_SCHOOL, OCTOPUS_WIRE_CONSOLIDATION, OCTOPUS_WIRE_EVOLUTION, OCTOPUS_WIRE_BOX, OCTOPUS_WIRE_LEAD_TICK, OCTOPUS_WIRE_IDEAS, OCTOPUS_WIRE_SPECTRAL, OCTOPUS_WIRE_BARBELL, OCTOPUS_WIRE_DEBATE, OCTOPUS_WIRE_SCHEDULER, OCTOPUS_WIRE_RECONCILE, OCTOPUS_WIRE_FITNESS, OCTOPUS_WIRE_EPISTEMICS, OCTOPUS_WIRE_BIO, plus ACTIVATION flags and TELEGRAM_BOT_TOKEN). The `apply_profile()` function (P-W3) sets them in bulk via `OCTOPUS_PROFILE`, but the sheer number creates a large configuration surface.

### 6.2 Exception Swallowing Pattern

Nearly every connection has a `try/except Exception` with `opslib.alert()`. This is by design (charter S4: "no silent crash"), but creates a risk: exceptions are logged to `governor-alerts.md` which is a flat file, not a structured alerting system. If the alert path itself fails (disk full, permission error), exceptions are truly silent.

### 6.3 All Paths Lead to budgets.yaml

budgets.yaml is read by: governor_epoch (caps, weights, organ definitions), organ_gate (organ existence, monthly cap), money_gate (human_gate_aud), fitness (weights), telemetry (organ mapping via ORGAN_MAP -- though hardcoded, not from YAML), opslib (organ_table, fx rate), cardiac (mass estimation), and the HTTP status server (indirectly via state). It is the true single source of truth for the organism's economic anatomy.

### 6.4 No Circular Dependencies (Verified)

The codebase deliberately avoids circular imports. `approval_channel.py` uses lazy imports for chrono (L907-919). `wiring.py` adds paths dynamically. `doctor.py` adds budget/ paths at module level but does not import organism. The dependency graph is a clean DAG: organism -> wiring -> subsystems -> opslib -> budgets.yaml.

---

## 7. RISK MATRIX

| Risk | Probability | Impact | Mitigation Status |
|---|---|---|---|
| organism.py crash (no watchdog running) | Low | Critical (all organs dead) | Partial: watchdog.py exists but is external Scheduled Task, not guaranteed to run |
| opslib.py import failure | Very Low | Critical (cannot start) | None -- no fallback for foundation layer |
| budgets.yaml corruption | Low | Critical (all budget logic fails) | Partial: git version controlled; no runtime backup |
| Port 8771 zombie | Low | High (cannot start) | Manual cleanup needed; SO_EXCLUSIVEADDRUSE prevents accidental reuse |
| Telegram credentials leaked | Low | High (approval path compromised) | Secret-guard: token only from env, never hardcoded/logged (approval_channel.py L6-9) |
| Flag misconfiguration | Medium | Medium (wrong organs active) | PAPER-FULL profile defaults; override possible but logged in wire_summary |
| governor-alerts.md disk full | Low | High (silent exceptions) | No mitigation -- alert path itself can fail silently |
| Epoch file accumulation | Medium (over months) | Low (disk space) | No cleanup mechanism exists |
| LiveLoop advisory signal loss | Certain (every restart) | None (advisory only) | By design -- not worth persisting |

---

*End of Phase 5: Neural Connection Map. All entries evidence-backed with specific file:line references from the codebase dated 2026-07-08/09.*
