# FIXTURE-MANIFEST-DESIGN.md

> agent F-D (read-only recon). Writer must verify before acting.

## summary
Read the full data-layer of F:\octopus-phase0-isolated: chrono.py (ChronoDB DDL + EffectorGate + on_human_judgment), the genome ledger (07 - Knowledge/genome-system/ledger/ledger.py — JSONL SHA-256 hash-chain with age_tick arrow), opslib.py (paths/flags/genome bridge), attribution.py (MONEY_ATTRIBUTION lifecycle), outcome_store.py (outcomes.db), the four approval stores, money_gate/approval_channel, budgets.yaml (model providers), and tests/harness.py (the canonical sandbox builder). I designed 11 synthetic, deterministic, PII-free fixtures, each grounded in the exact schema in source. Two build hazards are load-bearing and must be respected in any sandbox: (1) opslib pins the genome ledger to a hardcoded canonical F:\backup path unless the GENOME_DIR env var is set BEFORE opslib import (opslib.py:43-44), so a naively-built fixture writes into the LIVE organism; (2) telegram_center/approval_store.py resolves its paths module-relative with NO env override (approval_store.py:47-56), so it cannot be redirected to a temp dir by env alone — it must be monkeypatched. harness.py is the correct pattern for env-first sandboxing and should be the base for every fixture. All schemas below are verbatim from source; no fixture contains real chat IDs, tokens, financial refs, or partner names.

## findings
- **[critical]** genome_ledger() writes to a hardcoded canonical F:\backup genome path unless GENOME_DIR is set before opslib import; a fixture that forgets this env var mutates the LIVE ledger (append does fsync).  
  evidence: `F:/octopus-phase0-isolated/_ops/budget/opslib.py:43`  
  fix: Every genome-ledger / attribution / chrono-human-append fixture MUST export GENOME_DIR=<sandbox>/genome-system BEFORE importing opslib (harness.py:112 does this). Verify opslib.GENOME_DIR resolves inside the temp root before any append.
- **[high]** telegram_center/approval_store.py computes _APPROVALS_JSON, _LEGACY_DIR, _AUDIT_PATH from module file location (parent.parent + '/_octopus/state'), with no env override, so it always writes inside the imported tree — not a temp sandbox.  
  evidence: `F:/octopus-phase0-isolated/_ops/telegram_center/approval_store.py:47`  
  fix: Fixture for the octopus approvals.json store must monkeypatch approval_store._APPROVALS_JSON / _LEGACY_DIR / _AUDIT_PATH to temp paths (env injection alone is insufficient). Document this as a store-specific seam.
- **[medium]** A valid genome-ledger fixture requires a correct SHA-256 hash chain: each record's body is canonicalized with json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False) and hashed; prev must equal the prior record's hash or verify() fails at that record.  
  evidence: `F:/octopus-phase0-isolated/07 - Knowledge/genome-system/ledger/ledger.py:64`  
  fix: Builder must replicate _canonical() exactly (stdlib only) and chain prev/hash; also honor the age_tick rule (advances +1 only when is_human==1 or beat==1 for age_rule='heart' records) or verify() reports age-reversal/non-advancing errors.
- **[info]** chrono.db baseline is fully specified by the _DDL literal (8 tables + PRAGMA user_version=1); gated_effect.status and leg_clock.state have CHECK constraints that reject out-of-enum fixture rows.  
  evidence: `F:/octopus-phase0-isolated/_ops/chrono.py:141`  
  fix: Build chrono.db by executescript of the verbatim _DDL (lines 141-228); gated_effect.status must be one of pending/releasable/settled/refused and leg_clock.state one of alive/suspected/failed.
- **[info]** ChronoDB default path is opslib.STATE_DIR/chrono.db (=OPS_DIR/state), and outcome_store default path honors OCTOPUS_STATE_DIR env; both are sandbox-friendly if the env is set or an explicit path is passed to the constructor.  
  evidence: `F:/octopus-phase0-isolated/_ops/chrono.py:233`  
  fix: Prefer passing explicit paths (ChronoDB(path=...), OutcomeStore(path=...)) in fixtures to avoid any dependence on env-resolved live dirs.
- **[medium]** MONEY_ATTRIBUTION accounting records live inside the genome ledger (not a separate DB); CONFIRMED/ATTRIBUTED may only carry actor='reconcile-job', and fitness reads only CONFIRMED/ATTRIBUTED — a fixture that mislabels actor breaks the anti-reward-hacking invariant being tested.  
  evidence: `F:/octopus-phase0-isolated/_ops/budget/attribution.py:25`  
  fix: Accounting fixture = MONEY_ATTRIBUTION events appended to the same genome ledger fixture with synthetic LEAD-YYYYMMDD-NNN ids; set actor='attribution' for PROPOSAL/CLAIMED and actor='reconcile-job' for CONFIRMED/ATTRIBUTED/CONFLICT.

## artifact
# FIXTURE-MANIFEST — Octopus Phase-0 (role F-D, Fixture Architect)

All shapes verbatim from `F:\octopus-phase0-isolated`. Fixtures are synthetic, deterministic, PII-free ($0/offline/stdlib). **Golden rule:** follow `_ops/tests/harness.py` — build a `tempfile.mkdtemp()` root and set env (`ORG_ROOT`, `OPS_DIR`, `GENOME_DIR`, `BRAIN_DIR`, `BUDGET_STATE`, `OCTOPUS_STATE_DIR`) **before** importing `opslib`/consumers. Never write under `F:\backup`.

## Sandbox skeleton (deterministic knobs)
- Freeze time: inject `clock=lambda: FIXED_MS` into `ChronoBus`/`Pacemaker` (chrono.py:289) — no wall-clock reads in legs (TINV-5).
- Freeze chrono cadence: `CHRONO_PERIOD_S`, `CHRONO_AGE_PER_N_BEATS=1` (fast age arrow for tests), `CHRONO_RETAIN_BEATS=0` (chrono.py:62-74).
- Freeze randomness: `gated_effect.effect_id` is `uuid4().hex[:16]` (chrono.py:383) — for determinism, pre-`INSERT` rows with fixed ids rather than calling `request()`.

---

## F1 — Genome Ledger (LANGAR) `ledger.jsonl`
- **Consumer:** `opslib.genome_ledger()` (opslib.py:371) → everything: `chrono.on_human_judgment`, `attribution.py`, `Pacemaker` age-tick (chrono.py:718).
- **Shape:** append-only JSONL; one record per line, body = `{id, ts, type, actor, payload, meta, prev, age_tick, is_human, age_rule, beat}` + `hash` (ledger.py:197-204). `type ∈ {OBSERVE,INDEX,METRIC,PROPOSAL,APPROVAL,APPLY,GENOME_CHANGE,HEARTBEAT,NOTE,MONEY_ATTRIBUTION}` (ledger.py:44). `prev` chains to prior `hash`; GENESIS = 64×"0".
- **Build (temp):** write lines directly with a stdlib helper mirroring `_canonical` (ledger.py:64): `hash = sha256(json.dumps(body, sort_keys=True, separators=(",",":"), ensure_ascii=False))`. Chain `prev`. Age rule: for `age_rule="heart"` records, `age_tick` = prev_age+1 iff `is_human==1 or beat==1`, else unchanged; never decreases (verify() at ledger.py:239). Provide 3 variants: **valid**, **torn-last-line** (scar path, ledger.py:280), **tampered** (bad hash → verify fail).
- **PII:** synthetic `actor` ("test-agent"/"human"/"pacemaker"), payloads are `{"subtype":"…"}` placeholders.

## F2 — chrono.db (schema baseline)
- **Consumer:** `ChronoDB`/`Pacemaker`/`EffectorGate` (chrono.py:231).
- **Shape:** SQLite/WAL, `PRAGMA user_version=1`, 8 tables = `heartbeat, leg_clock, experience_meter, duration_marker, anticipation_queue, checkpoint, gated_effect, metabolic_age` (verbatim `_DDL`, chrono.py:141-228). CHECK enums: `leg_clock.state ∈ {alive,suspected,failed}`, `gated_effect.status ∈ {pending,releasable,settled,refused}`.
- **Build:** `sqlite3.connect(tmp/'chrono.db')`; `executescript(_DDL)`. Baseline = empty. Populated variant: seed `heartbeat` (beat_seq 1..N, monotone), `leg_clock` rows per leg.
- **Pass explicit path** `ChronoDB(path=tmp/'chrono.db')` to avoid `STATE_DIR` resolution.

## F3 — gated_effect table (TINV-7 gate)
- **Consumer:** `EffectorGate.request/release_gated_effects/release_one/settle/sweep_stale_effects` (chrono.py:355-470).
- **Shape:** rows `{effect_id, kind, payload_ref, created_beat, created_ts, release_ref, status}`. Batch-releasable kinds = `{send,publish,sync,pay}` (chrono.py:346); per-effect kinds `{lead_outbound,customer_send}` need `release_one`.
- **Build:** pre-`INSERT` fixed-id rows to exercise each status transition. Fixtures: (a) `pending` money-kind (batch path), (b) `pending` customer-kind (must fail batch, need release_one), (c) `releasable` with `release_ref` (settle-ready), (d) stale `pending` `created_ts < now-72h` (sweep target), (e) `refused`.
- **PII:** `payload_ref` = opaque hash string, never real message text.

## F4 — Approvals (four distinct stores — keep all alive)
| Store | Path | Shape | Consumer |
|---|---|---|---|
| Telegram legacy verdicts | `_ops/state/telegram/approvals/<id>.json` + `approvals.jsonl` | `{id, verdict("ok"/…), ts, source}` | `approval_store.sync_to_octopus_state` (approval_store.py:232), `approval_queue_unified._reconcile_approvals_jsonl` (:341) |
| Octopus pending queue | `<root>/_octopus/state/approvals.json` | `{schema_version, pending[], approved[], rejected[], done[]}`; job = `{id,type,title,status,risk,created_at,expires_epoch,requires_confirmation,dry_run_report,source}` | `approval_store` (:80,131) — **monkeypatch paths (finding 2)** |
| Unified queue | `_ops/state/unified-approval-queue.json` | `{generated, items[], counts}`; item = `UnifiedQueueItem` dataclass (id,source,type,status,summary,amount_aud,priority,effect_id,risk_level,actions,gate_status) (approval_queue_unified.py:72) | `UnifiedApprovalQueue._load` (:142) |
| Approval-log (state machine) | `_ops/state/approval-log.jsonl` | `{ts, action_id, from_status, to_status, actor, action_type, rationale}`; statuses `suggested→queued→owner_approved→executed`(+rejected/expired/superseded/dry_run) (approval_state_machine.py:45) | `approval_state_machine` |
| ops snapshots (optional) | `…/approvals/pending_snapshot.json`, `rfc_snapshot.json` | dict `eid→{amount_aud,summary,guard,status,created_at}` | `UnifiedApprovalQueue._pull_ops` (:409) |
- **Build:** JSON/JSONL literals; sanitized ids (`[A-Za-z0-9_.\-]`, approval_store.py:58). All content-free. **PII:** synthetic 16-hex ids, no owner text.

## F5 — money_gate approval channel
- **Consumer:** `money_gate.check` (money_gate.py:34) via `ApprovalChannel`.
- **Shape:** `Approval(action_id, amount_aud, status, source)`; `valid` iff `status ∈ {approved,sent}` (approval_channel.py:28-41). Threshold `human_gate_aud ≤ AU$20` (fail-closed floor, money_gate.py:19).
- **Build:** use `MockApprovalChannel([Approval(...)])` (approval_channel.py:60) — no live core.db needed. Fixtures: below-threshold (auto-allow), above+valid mock approval (allow), above+`NotWiredStub` (deny).

## F6 — Proposal outcomes `outcomes.db`
- **Consumer:** `OutcomeStore.record/events/metrics` (outcome_store.py:65).
- **Shape:** SQLite/WAL, `SCHEMA_VERSION=1`, table `outcomes` cols per `_COLS` (event_id PK, idempotency_key UNIQUE, correlation_id, mission_id, proposal_id, leg_id, lead_id, event_type, verdict, value_aud_claimed, occurred_at, recorded_at, schema_version, payload_json). `event_type ∈ {delivered,deferred,accepted-measurement,rejected,failed}` (:27).
- **Build:** `OutcomeStore(path=tmp/'outcomes.db')`; `.record({...})` a deterministic set, or pre-INSERT rows. Set `occurred_at` to fixed ISO. `value_aud_claimed` is a CLAIM (confirmed_revenue always 0 here, :143).

## F7 — Telegram state
- **Consumer:** telegram center / `extract_telegram_*`.
- **Shape:** `center-config.json` = `{chat_id(int), display_names{}, topics{name→int}, commands_set, last_digest{}, seen[ids]}`; `telegram_offset.json`; approvals dir (F4).
- **Build:** literal JSON. **PII (critical):** live file has a real `chat_id: -1004475788460` and real topic map — fixture uses a synthetic negative id (e.g. `-1000000000001`) and dummy topic ints. No bot token anywhere (secret lives in env only, approval_channel.py:9).

## F8 — Accounting records (MONEY_ATTRIBUTION)
- **Consumer:** `attribution.fold/confirmed_revenue` (attribution.py:133), `fitness`.
- **Shape:** MONEY_ATTRIBUTION events **inside the F1 genome ledger** (no separate table). State machine `PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED` (+`CONFLICT`, sticky) (attribution.py:23). Payload keys: `attribution_id, state, cell, expected_aud, amount_aud, lead, decision_date, ref, matched, split, partners`. Invariant: CONFIRMED/ATTRIBUTED only with `actor="reconcile-job"` (:26); PROPOSAL/CLAIMED with `actor="attribution"`.
- **Build:** append MONEY_ATTRIBUTION lines into F1. ids `LEAD-20260101-001` (synthetic). partners = fake names ("PartnerA"/"PartnerB"), never real people. Also `core.db.usage`/`outbox` (harness.py:97-101) for cost/attribution consumers.

## F9 — Model providers (budgets.yaml)
- **Consumer:** `opslib.load_budgets/organ_table/fx_aud_per_usd` (opslib.py:199-230); `money_gate.human_gate_aud`.
- **Shape:** YAML with required top keys `global` + `projects` (else FREEZE, opslib.py:206). `routing.{econ,reason,glm,anthropic,orchestr,premium,local}` each `{provider,model,base_url,price_in,price_out,...}`; `global.human_gate_aud`, `cap_monthly`, `aud_per_usd`; `loop.DEBATE_LOOP`; `allocation.partners_default`.
- **Build:** reuse `harness.TEST_BUDGETS` (harness.py:29) as the canonical PII-free fixture (deepseek/sakana stub providers, no keys). Extend with `routing.local` ollama + a `human_gate_aud: 20` for money_gate tests. **PII:** `business:` block stays empty strings (ABN/bank blank), `base_url` uses `${ENV}` placeholders — no secrets.

## F10 — STOP / HALT / activation flags
- **Consumer:** `opslib.halted/master_halted/frozen/halt_reason` (opslib.py:284-329), `EffectorGate.force_closed` (chrono.py:369), `Pacemaker.run_forever` (chrono.py:757).
- **Shape:** presence-only flag files (first text line = reason). Severity order: `HALT-ALL` > `STOP(architect)`=`04 - Architect System/STOP` > `STOP-METABOLIC` > `STOP-DEBATE`; plus `STOP-ORGANISM`, `FREEZE.flag`, `ACTIVATION-*.flag`, `backup/GITWRITE-FAILED.flag`.
- **Build:** `touch` the file under the sandbox `OPS_DIR`/`ARCHITECT` to simulate kill; absence = running. Fixtures: none (nominal), `STOP-ORGANISM` (gate force-closed), `HALT-ALL` (master halt), `FREEZE.flag` (I3). Content = synthetic `"<iso> test-reason"`.

## F11 — checkpoint / metabolic_age / heartbeat (chrono sub-tables)
- **Consumer:** `Pacemaker.beat_once/status` (chrono.py:590,740).
- **Shape:** part of F2. `checkpoint{beat_id,logical_clock,ledger_hash,snapshot_ref,metrics}`, `metabolic_age{leg_id,wear,updated_beat}` (row `'_organism'` = whole-body), `heartbeat{beat_seq,wall_ts,hlc_phys,hlc_logical,present_legs,absent_legs,workspace_ref,ts}`.
- **Build:** seed monotone `beat_seq`; `metabolic_age` with `_organism` + one leg row. Deterministic via injected clock.

---
### Build-order recipe (per fixture set)
1. `root = mkdtemp()`; create `_ops/{budget,state,...}`, `genome-system/ledger`, `_octopus/state`, `brain/logs` (mirror harness.py:63-86).
2. Write `budgets.yaml` (F9), `core.db` (harness.py:96).
3. `export` env → import `opslib` (verify `opslib.GENOME_DIR` is inside `root` — finding 1).
4. Build F1 (+F8) hash-chain; F2/F3/F11 via `_DDL`; F6 via OutcomeStore; F4/F7 JSON; F10 flags.
5. For F4 octopus-approvals: monkeypatch module paths (finding 2).
