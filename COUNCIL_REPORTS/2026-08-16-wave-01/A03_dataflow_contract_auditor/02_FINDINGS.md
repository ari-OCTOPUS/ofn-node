# 02_FINDINGS — A03 (2026-08-16)

Format: ID · claim · status · tier · source · lines · command · observed · confidence · severity · contradiction · next action.
Timestamps: all observations 2026-08-16 (UTC-local session). Tier per contract: T0 live runtime / T1 tests / T2 code+git / T3 manifests+ledgers / T4 ADRs / T5 old docs / T6 memory.

---

## F-01 · The consequential-execution core is a fail-closed contract pipeline
- **Claim:** action_bridge enforces versioned contracts (action-request/plan/receipt.v1) with fail-closed validation (13 required fields; bad shape ⇒ invalid; no exceptions thrown).
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/contracts.py` lines 26-165 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.97 · **Severity:** INFO (positive control) · **Contradiction:** none · **Next:** keep as reference for other lanes.

## F-02 · Classifier: unknown=A6, text only escalates (prompt-injection containment)
- **Claim:** `classify()` maps action_type→base class; unknown type ⇒ A6 REJECT; `intent`/`expected_effect` free text can only raise the class; fabrication-regex and scope-escape-regex force A6.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/classifier.py` 29-189 (rules 1-3 documented 5-18) · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** INFO · **Contradiction:** none · **Next:** adversarial fuzz of text-escalation regexes (Persian/English mixes).

## F-03 · Executor implements only A0/A1; A2+ structurally path-less
- **Claim:** `EXECUTABLE = frozenset({"A0","A1"})`; decision≠ALLOW ⇒ BLOCKED/REJECTED receipt; exception ⇒ FAILED never EXECUTED; dry_run=True default.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/executor.py` 35-99 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.97 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-04 · A2 is BLOCK, not "bounded automatic"
- **Claim (project):** A2 actions are bounded automatic actions. **Observed:** `DECISION_BY_CLASS["A2"]="BLOCK"` with comment "A2 عمداً BLOCK است چون governance هنوز اجازه نداده (VQ-SELFGOAL-002)".
- **Status:** CONTRADICTED (implementation is *stricter* than the claim) · **Tier:** T2 · **Source:** `_ops/action_bridge/classifier.py` 172-184; `_ops/action_bridge/integration.py` 41-43 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** MEDIUM (doc/reality drift) · **Contradiction:** contradicts "A2 automatic" claim; consistent with safety posture · **Next:** owner decision recorded (VQ-SELFGOAL-002 preconditions) — see 08.

## F-05 · action_bridge is armed and produced runtime records today
- **Claim:** bridge live. **Observed:** flag `OCTOPUS_WIRE_ACTION_BRIDGE=1` in `state/flags-loaded-cortex.json`, `audit/organism-manifest.json:385`, `OCTOPUS-flags.cmd:827`; component registry marks MS1 🟢 LIVE; `state/test_cycle/missions.jsonl` has 2026-08-16 rows (mission mis:f635d468…, needs_approval→running, owner-card + approval-job staged); journal cycle 2026-08-16#1 with `action_memories_used:3`.
- **Status:** VERIFIED_LIVE (state-at-rest; no process observed) · **Tier:** T3+T2 · **Source:** as listed · **Command:** tail/grep · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** INFO · **Contradiction:** none · **Next:** runtime agent (A02) to confirm process liveness.

## F-06 · Owner approvals are hash-bound, expiring, single-use
- **Claim:** owner_gate approvals bind `action_id`+`payload_hash`+`scope`, expire (24h), burn a nonce; no signing key ⇒ fail-closed; card ≠ authorization.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/owner_gate.py` 39-163 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** INFO · **Contradiction:** none · **Next:** verify nonces persisted (used-nonces.json exists per integration.py durability note).

## F-07 · Receipt discipline: no receipt ⇒ no success claim
- **Claim:** `finalize()` downgrades EXECUTED→FAILED if receipt write or ledger append fails; blocked/rejected kept honest.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/receipt.py` 59-87 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-08 · Idempotency separates DUPLICATE from CONFLICT; persisted across restart
- **Claim:** key=`action_id:payload_hash`; same id+different payload ⇒ CONFLICT; no ledger ⇒ CONFLICT; ledger/nonces persisted (integration.py: 2026-07-31 note).
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/idempotency.py` 24-58; `integration.py` 39-40 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.93 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-09 · Memory can veto missions, never authorize
- **Claim:** retrieval_router (flag on) returns veto; mission blocked + ledgered on veto; router error ⇒ fail-soft continue; plan byte-identical with/without advisory recall.
- **Status:** VERIFIED_LIVE (missions.jsonl input_refs carry `memory:` ids today) · **Tier:** T2+T3 · **Source:** `_ops/goal_action_bridge.py` 262-276, 395-399, 432-445 · **Command:** file read + tail · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-10 · "Sensorium" does not exist; afferent path is a stub fed by internal aggregates
- **Claim (project):** Sensorium is active. **Observed:** zero hits for "sensorium" in any file; `_observations_from_snapshot` derives synthetic labels (organ counts, spend aggregates) — "این منبعِ آورانِ زندهٔ ارگانیسم است … نه دادهٔ مشتری"; classifier is rule-based stub ("برای معمار: classifier واقعی … فعلاً rule-based").
- **Status:** NOT_FOUND (Sensorium) / VERIFIED_CODE_ONLY (afferent stub) · **Tier:** T2 · **Source:** `_ops/wiring.py` 2663-2747; `_ops/afferent/sensory_bus.py` 32-81 · **Command:** grep -ril sensorium (0 hits); file read · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** MEDIUM (claim drift) · **Contradiction:** contradicts "Sensorium active" · **Next:** rename docs to "afferent stub" or implement.

## F-11 · Owner channel: fail-closed allowlist; LLM display-only; approvals token-bound
- **Claim:** owner commands travel command-allowlist → intent classification → action cards; high-risk double-confirm; HMAC callback tokens; ask_brain replies never execute.
- **Status:** VERIFIED_CODE_ONLY (subagent-audited, spot-checked) · **Tier:** T2 · **Source:** `_ops/telegram_center/center.py` 2657-2674, 3024-3231, 4748-4847; `callback_token.py` 60-69; `ask_brain.py` 236-246,479; `actions.py` 101-117 · **Command:** subagent read + spot-check · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** INFO · **Contradiction:** none · **Next:** line-audit center.py in a later wave.

## F-12 · `/sh` owner shell console bypasses all gates
- **Claim:** authenticated owner can run arbitrary shell with one message; no double-confirm/receipt.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/telegram_center/center.py` ~3213 · **Command:** subagent read · **Observed:** 2026-08-16 · **Confidence:** 0.8 · **Severity:** MEDIUM · **Contradiction:** tension with "no consequential execution without policy receipt" · **Next:** wrap in double-confirm + action-audit row.

## F-13 · Lead email lane: real external sends outside action_bridge
- **Claim:** outbound_worker+transport send email (armed by owner vote 2026-07-31, vote 17); gates = per-effect owner authorization allowlist (default empty), consent_gate may_draft/may_release, daily cap 10 (env override, ≤0=uncapped per owner 2026-08-12), staleness gate 24h/72h ceiling, GAP-2 recorded-price-only, NOT_ARMED honest failures.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/legs/outbound_worker.py` 1-80,223+; `lead_effect_gate.py` 15,95,131-192,277+; `effector_gate_bridge.py` 20-30 · **Command:** file read/grep · **Observed:** 2026-08-16 · **Confidence:** 0.88 · **Severity:** MEDIUM (real A4-class lane parallel to action_bridge; cap now removable by env) · **Contradiction:** "actions are propose-only" holds only inside action_bridge · **Next:** document lane equivalence; consider porting to action_bridge A4 when its executor exists.

## F-14 · Genome ledger: live, hash-chained, append-only — single timestamp
- **Claim (project):** ledger is live and bitemporal. **Observed:** fields `id,ts,type,actor,payload,meta,prev,age_tick,is_human,age_rule,beat,hash`; append with fsync; `ts`=now at append; no occurred/recorded split.
- **Status:** VERIFIED_LIVE (as append-only chained) / DOCUMENTED_NOT_IMPLEMENTED (bitemporal) · **Tier:** T3+T2 · **Source:** `07 - Knowledge/genome-system/ledger/ledger.jsonl` (tail); `ledger/ledger.py` 226,233-236 · **Command:** tail; file read · **Observed:** 2026-08-16 · **Confidence:** 0.92 · **Severity:** MEDIUM (overstated claim) · **Contradiction:** bitemporal claim · **Next:** either add occurred_at or fix docs.

## F-15 · Four SQLite stores have occurred_at/recorded_at — always equal in practice
- **Claim:** bitemporal infrastructure exists. **Observed:** spine/outcomes/funnel/consent stores define both columns; publish defaults missing occurred_at to now ⇒ both equal; no caller passes a backdated occurred_at.
- **Status:** VERIFIED_CODE_ONLY (schema) / DOCUMENTED_NOT_IMPLEMENTED (semantics unused) · **Tier:** T2 · **Source:** `_ops/spine/event_spine.py` 31,95,118,155; `outcomes/outcome_store.py` 33,98; `funnel_store.py` 154,176; `legs/consent_store.py` 107-108,174 · **Command:** subagent grep + read · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** LOW-MEDIUM · **Contradiction:** none (supports future fix) · **Next:** have one producer emit true event-time.

## F-16 · MemoryStore implements real valid-time (TTL/supersede)
- **Claim:** memory records carry valid_from/valid_to; supersede sets valid_to=now, admission RETRACTED, no physical deletes; search filters ADMITTED+valid_to.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/memory/memory_store.py` 31,132,140-170,199; `_ops/memory/gate.py` `_TTL_DAYS` · **Command:** subagent read · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-17 · MemoryGate: model output can never commit owner/procedural; self_knowledge advisory
- **Claim:** FSM classify→scrub→dedupe→grade→TTL→commit; secrets/PII regex-rejected; behind flag (loaded value 1).
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/memory/gate.py` 1-50,167 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.92 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-18 · 4d memory store is ungated; raw LLM hypotheses persist
- **Claim:** `generate_hypothesis` saves LLM reply verbatim; no admission gate; hypotheses re-enter prompts.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `4d_system/brain/tools.py` 118-156 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** MEDIUM (poisoning vector, contained to research prompts) · **Contradiction:** violates "model output is untrusted input" at persistence layer · **Next:** route through a MemoryGate-equivalent or mark provenance=llm and downgrade trust.

## F-19 · 4d control_plane ladder is observe-only and unwired to execution
- **Claim:** Policy Gate runtime-enforced. **Observed:** policy.py self-documents "در v1 هیچ‌چیز را enforce نمی‌کند"; callers of evaluate() are only control_plane-internal + tests; live flags default-off.
- **Status:** VERIFIED_CODE_ONLY (as observe-only) — enforcement claim SPLIT (true for action_bridge ladder) · **Tier:** T2 · **Source:** `4d_system/control_plane/policy.py` 14-16; grep of callers · **Command:** grep -rn "from control_plane" · **Observed:** 2026-08-16 · **Confidence:** 0.93 · **Severity:** LOW-MEDIUM (two policy vocabularies confuse audits) · **Contradiction:** "Policy Gate runtime-enforced" without qualifier · **Next:** docs must name which ladder.

## F-20 · Viability loop is live and reports honest failures
- **Claim:** prereg→metric→verdict cycle runs. **Observed:** verdicts.jsonl today: two FAIL/no-movement verdicts on `attribution.claimed` (baseline 0.0, value_now 0.0); prereg rows carry forbidden_actions incl. external-send/spend.
- **Status:** VERIFIED_LIVE · **Tier:** T3 · **Source:** `_ops/state/test_cycle/verdicts.jsonl` (tail 2), `prereg.jsonl` (tail 1) · **Command:** tail · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-21 · identity_health computed live from state files
- **Claim:** live metric. **Observed:** `_identity_health()` = mean of 5 identity values; each a weighted equation over measurements.jsonl, ORGANISM-STATE.json, spectral-latest, hypothesis-queue, attribution, env honest-flags; consumers: organism snapshot, improve, spine, alert rules.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/math_control/spine.py` 157+; `_ops/identity_equations.py` 371+ · **Command:** subagent read · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** INFO · **Contradiction:** none · **Next:** A02 confirm it appears in live snapshots.

## F-22 · Dual-brain mutual veto exists; 4d side not connected
- **Claim:** governance is mutual veto. **Observed:** `control_plane/dual_brain.py` implements D1-D3 behind OCTOPUS_WIRE_DUAL_VETO; mission bridge passes NBB=APPROVED (planner itself), 4d=PENDING with comment "4d هنوز وصل نیست (W2+)" ⇒ non-APPROVED final → DUAL_VETO_HOLD when enabled.
- **Status:** VERIFIED_CODE_ONLY (partial wiring) · **Tier:** T2 · **Source:** `_ops/control_plane/dual_brain.py` 1-60; `_ops/goal_action_bridge.py` 478-495 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** LOW-MEDIUM · **Contradiction:** "mutual veto" as *operating* between two live brains is not yet true (one side pending) · **Next:** wire 4d side (W2+) or mark one-brain governance in docs.

## F-23 · Scope guard learns from a real past bypass (resolve, not substring)
- **Claim:** containment is component-wise after resolve; forbidden-marker denylist on resolved path; absolute/drive/UNC/NUL rejected.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `_ops/action_bridge/scope_guard.py` 27-154 (lesson: `code_autonomy.allowed_target` `..` bypass 2026-07-30) · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.95 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-24 · 4d guardrails: allow-list writes, TCB, Ed25519 trust boundary
- **Claim:** autonomous writes confined to outputs/ and never *.py; TCB files+dirs untouchable; trust-boundary manifest with sha256 digests + owner Ed25519 signature; enforcement env-flag OCTOPUS_TCB_MANIFEST_ENFORCE (default shadow).
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `4d_system/brain/guardrails.py` 69-99,109-218,274-351,367-406 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.93 · **Severity:** INFO (enforce flag state needs A02) · **Contradiction:** none · **Next:** confirm env flag in runtime bundle.

## F-25 · self_code apply re-runs full gate stack at approve time
- **Claim:** code proposals apply only after: enabled flag, pending status, TCB allowlist, stale check, static rescan, sandbox execution with tamper detection, backup.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `4d_system/brain/self_code.py` 403-443 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-26 · state_guard can rewrite "append-only" state files (quarantine)
- **Claim:** JSONL state ledgers (reach, action-audit, events, intervention) are repair-rewritten; sidecar quarantine exists (reach ledger, 2026-08-08, removed_null:1). Hash-chained ledgers not affected.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2+T3 · **Source:** `_ops/state_guard.py` ~65,297; `state/reach/ledger.jsonl.quarantined.20260808T165341` · **Command:** subagent read/ls · **Observed:** 2026-08-16 · **Confidence:** 0.8 · **Severity:** LOW-MEDIUM · **Contradiction:** "append-only" naming overstates for REPAIR_TARGETS · **Next:** chain or checkpoint these files.

## F-27 · Layers L0–L8 not found as code structure
- **Claim (project):** OCTOPUS has layers L0-L8. **Observed:** no L0..L8 layering in code; organization is organs/legs/components with registries (OCTOPUS-COMPONENT-REGISTRY.md, organism-manifest.json) and an architecture doc that itself reconciles organism-layer vs topology (OCTOPUS/ORGANISM-LAYER-RECONCILIATION-2026-08-12.md).
- **Status:** NOT_FOUND (as implementation) / DOCUMENTED (as model) · **Tier:** T2 survey + T5 · **Source:** repo survey; OCTOPUS/ARCHITECTURE-BIBLE.md (not line-audited) · **Command:** find/grep survey · **Observed:** 2026-08-16 · **Confidence:** 0.7 · **Severity:** LOW · **Contradiction:** layer numbering is a documentation model, not a code boundary · **Next:** A01/A15 to reconcile.

## F-28 · Verdict consolidation into memory is idempotent and outcome-bound
- **Claim:** fresh verdicts → MemoryGate episodic rows `source=deterministic`; flag-off skips without burning marker; dedupe counted as success.
- **Status:** VERIFIED_CODE_ONLY (+state marker present) · **Tier:** T2+T3 · **Source:** `_ops/goal_action_bridge.py` 565-637; `state/test_cycle/memory-consolidated.json` exists · **Command:** file read + ls · **Observed:** 2026-08-16 · **Confidence:** 0.88 · **Severity:** INFO · **Contradiction:** none · **Next:** none.

## F-29 · Temporal hygiene gaps: naive local timestamps in receipts/events
- **Claim:** receipts use local `strftime` without timezone (goal_action_bridge.py:532); 4d events naive `datetime.now()`; epoch floats elsewhere; one ledger (c6 research-ledger) has no timestamp at all.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** as listed (see TEMPORAL_SEMANTICS_AUDIT) · **Command:** file read/subagent · **Observed:** 2026-08-16 · **Confidence:** 0.85 · **Severity:** MEDIUM (cross-ledger correlation ambiguity) · **Contradiction:** none · **Next:** standardize UTC ISO-8601 with offset.

## F-30 · 4d telegram approve callback lacks double-confirm (deprecated lane)
- **Claim:** single button applies code; doctrine elsewhere requires double-confirm; module deprecated behind opt-in + 409-guard.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Source:** `4d_system/brain/telegram_bot.py` 358-367, 40-89 · **Command:** file read · **Observed:** 2026-08-16 · **Confidence:** 0.9 · **Severity:** LOW (dormant) · **Contradiction:** minor doctrinal inconsistency · **Next:** keep dormant or add confirm step on revival.
