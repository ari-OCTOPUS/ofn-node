# INVENTORY — Evidence-Control Plane (Stage 1 only)

- **Date:** 2026-08-11
- **Mode:** read-only inventory — **no code changes, no WORKLOCK registration**
- **Mission:** Senior Integration, Test & Safety Architect
- **Rule:** repository reality > prompt claims; discrepancies listed below

---

## 0. Claim verification (prompt vs disk)

| Claim | Verified? | Evidence |
|---|---|---|
| ADR-033 exists | YES | `03 - Projects/research-spec-compiler/adr/ADR-033-evidence-control-plane.md` |
| Talk Discovery / Collaborator live + model | YES (flags) | `OCTOPUS-flags.cmd:1350,1373` `WIRE_COLLAB=1`, `COLLAB_USE_MODEL=1` |
| Daily model cap = 20 | YES (flags) / NOTE | flags `1374` set `=20`; adapter default if unset is **30** (`collab_model_adapter.py:17-38`) |
| PolicyGate fail-safe (exception→DENY) | YES | `policy/policy_gate.py:84-91` |
| signals-registry + schema | YES | `architecture/signals-registry.yaml` + `.schema.json` (8 signals) |
| validator script | YES / PARTIAL | `_ops/scripts/validate_signals_registry.py` — **JSON Schema only**, no path/semantic/report JSON |
| shadow_channels BCM/Hebbian/Pain | YES | `_ops/signals/shadow_channels.py` |
| Kalman shadow pipeline | YES | `_ops/heart/kalman_shadow_pipeline.py` |
| SOG/DARE OTLP + Alloy sample | YES | `telemetry/sog_metrics_v2.py`, `alloy_sog.alloy.example` |
| AGENTS Test Intelligence | YES | `_ops/AGENTS-TEST-INTELLIGENCE.md` |
| New suites not in `run_all.py` | YES | see §6 — WORKLOCK still open |
| `_ops/control/` package | **NO** | directory does not exist; enforcement split across `policy/`, `runtime/`, `wiring.py`, `agi2027_control/` |

---

## 1. Capability truth table (runtime-verified)

| capability_id | path | entrypoint | flag | status واقعیت | tests | telemetry | external-effect path | risk |
|---|---|---|---|---|---|---|---|---|
| talk-discovery / collaborator | `_ops/owner_console/collaborator.py` | `handle` L99–234; `callback` L236 | `OCTOPUS_WIRE_COLLAB` (+ `COLLAB_USE_MODEL`, MEMORY, DIGEST) | **ARMED** draft-only; model path armed | `test_talk_discovery.py`, `test_cognitive_unify.py`, `test_api_collab.py` (in run_all); `test_adr033_*` **not** in run_all | event log via talk_gate; no OTLP required | **No send** by design (`external_effect=False`); model may call `model_router` | MEDIUM — live LLM path; outbound elsewhere still armed |
| talk PolicyGate (ADR-033) | `_ops/policy/policy_gate.py` | `PolicyGate.decide` L83–122 | none (library) | **TESTED** library | `test_adr033_control_plane.py` (not in run_all) | `evidence_plane` counters on deny/quarantine | none | LOW if wired; MEDIUM if bypassed |
| talk_gate bridge | `_ops/policy/talk_gate.py` | `guard_talk_discovery_draft` L101; kill via `OCTOPUS_KILL_SWITCH` L35–36 | `OCTOPUS_KILL_SWITCH` (default unset→off) | **TESTED** / wired into collaborator | adr033 / cognitive | JSONL events | none | LOW |
| legacy TalkDiscoveryPolicy | `_ops/collab/talk_discovery_policy.py` | `TalkDiscoveryPolicy.decide` L53 | none | **TESTED** (fallback if ADR-033 import fails) | `test_cognitive_unify.py` | none | none | LOW — dual policy surfaces |
| approval_sm | `_ops/collab/approval_sm.py` | `transition` L56; `begin_execute` L100 | none | **TESTED** library (in-process) | cognitive_unify | none | none | MEDIUM — not Redis-backed |
| approval_state | `_ops/collab/approval_state.py` | `can_approve` / `approve_or_block` L70–130 | none | **TESTED** library | `test_approval_state.py` (**not** in run_all) | none | none | MEDIUM — in-memory idempotency only |
| MiniApp gateway | `_ops/telegram_center/miniapp_gateway.py` | `handle` L457; routes ask L558 / mirror L627 / collab L752; inject L223–226 | `OCTOPUS_TG_MINIAPP`, collab inject from `WIRE_COLLAB` | **ARMED** | many `test_miniapp_*`, `test_api_collab` | hit log | ask/mirror/collab can reach LLMs; actions route separate | HIGH surface — auth/rate limits present |
| Ask mode | `ask_brain` via gateway L588–608 | `ask_brain.ask` | (ask path always available when miniapp on) | **ARMED** parallel persona | `test_tg_ask_vault.py` etc. | provider logs in router | paid/local LLM possible | MEDIUM — not Talk Discovery policy |
| Mirror mode | `mirror_room` via gateway L658–661 | `mirror_room.ask` | — | **ARMED** parallel | mirror tests | — | LLM possible | MEDIUM |
| model_router | `_ops/cortex/model_router.py` | `ask` L531; `_ask_impl` L379 | organ/paid gates internal | **ARMED** shared pool | TI router tests in run_all | paid usage logs | network to providers | HIGH — shared by Ask/Mirror/Collab |
| collab_model_adapter | `_ops/owner_console/collab_model_adapter.py` | `complete` (~L115+); `daily_cap` L36 | `OCTOPUS_COLLAB_USE_MODEL`, `OCTOPUS_COLLAB_MODEL_DAILY_CAP` | **ARMED** (cap 20 when flags loaded) | talk_discovery / collab_components | — | via router only | MEDIUM |
| discovery facade v2 | `_ops/discovery/discover_facade.py` + `sources.py`; adapter `owner_console/discovery_facade.py` | `discover_reply_text` | none (read-only) | **SHADOW/STRUCTURAL** read-only | cognitive_unify, approval_state facade tests | — | none | LOW |
| evidence-control-plane | `_ops/evidence_plane/*`, `_ops/runtime/*`, `_ops/capabilities/*` | event_log, registry, quarantine, seven_day, checkpoint/replay/rollback | none | **TESTED** library; not organism-wide choke point | `test_adr033_control_plane.py` not in run_all | JSONL under `state/adr-033/` | dry-run replay only | MEDIUM — not yet universal gate for all tools |
| capability registry (JSON) | `_ops/capabilities/*.json` + `evidence_plane/registry.py` | `CapabilityRegistry` | none | **TESTED** | adr033 | — | none | LOW |
| signals registry | `architecture/signals-registry.yaml` | N/A (data) | none | **TESTED** schema; incomplete vs mission fields | `test_signals_registry_schema.py` not in run_all | — | none | MEDIUM — missing name/family/inputs/outputs vs Stage-2 schema ask |
| schema validator | `_ops/scripts/validate_signals_registry.py` L15–32 | `main` | none | **STRUCTURAL/TESTED-partial** | schema test | print only | none | HIGH gap — no semantic path checks / machine report |
| BCM | `_ops/neural/bcm.py` | `BCMStabilizer.step` L137 | `OCTOPUS_WIRE_BCM`, `WIRE_BCM_FEED` | **ARMED** persist to JSON | `test_bcm_*` in run_all; shadow e2e not in run_all | phase metrics | **indirect:** `wiring.protective_override` if `NEURAL_LEARNED_APPLY=1` | **HIGH** — APPLY armed |
| Hebbian | `_ops/neural/hebbian.py` | `observe` L71; `decay` L85 | `WIRE_HEBBIAN_*` spectral/cardiac | **ARMED** persist | hebbian tests in run_all | — | wiring beats; not ADR-033 gated | MEDIUM |
| Nociceptor/Pain | `_ops/neural/nociceptor.py` | `Nociceptor.measure` L174 | threshold flags | **ARMED** pure compute | pain tests in run_all; chaos shadow not in run_all | effect-shadow jsonl | **YES via** `wiring.protective_override` → `protective_halt` L1812–1859 | **HIGH** — decision-changing when threshold crossed |
| neural APPLY path | `_ops/wiring.py` | `neural_beat` L1587; `protective_override` L1812 | `OCTOPUS_NEURAL_LEARNED_APPLY=1` (flags:1191), `NEURAL_EFFECT_SHADOW=1` | **ARMED control effect** | neural loop tests | governor alerts | pauses non-essential work | **CRITICAL discrepancy** vs «signals never gate» doctrine |
| spectral (legacy doctor) | `_ops/doctor/spectral.py` | `estimate_sigma` L96; `spectral_mine` L106 | used by organism/doctor | **ARMED/TESTED** historic | `test_spectral*.py` | — | advisory historically; pain census notes disconnect | MEDIUM |
| spectral_metrics + criticality_v2 | `doctor/spectral_metrics.py` L33; `criticality_v2.py` L70/`observe` | none / `OCTOPUS_WIRE_CRITICALITY_OTLP` **unset in flags** | **SHADOW** library | cognitive + adr033 (latter not in run_all) | JSONL + optional OTLP | **none** (explicit) | LOW if stays shadow |
| pulse arbiter | `_ops/heart/pulse_arbiter.py` | `arbitrate` L171; `wire_open` L478; `persist` L425 | `OCTOPUS_WIRE_PULSE_ARBITER=1` (flags:1045) | **ARMED** period control when wire open | heart tests | shadow sinks | **YES** — can change organism period | **HIGH** |
| pulse shadow compare | `_ops/heart/pulse_shadow_compare.py` | `shadow_compare` L46; `record_divergence` L70 | `OCTOPUS_WIRE_PULSE_ARBITER_SHADOW` **not in flags** | **TESTED** default off | cognitive_unify | JSONL if armed | none | LOW |
| Kalman shadow pipeline | `_ops/heart/kalman_shadow_pipeline.py` | `KalmanShadowPipeline.tick` | none | **TESTED** shadow observer | `test_kalman_shadow_pipeline.py` not in run_all | — | none by construction | LOW |
| SOG/DARE math | `_ops/heart/sog_math.py` | `p_closed` L46; `dare_crosscheck` L127; `mc_witness_core` L142; `run_lock` L401 | provenance via `SOG_4PY_PATH` | **LOCKED** math (MC gates) | `test_heart_math.py`, `test_sog_provenance.py` | sog_metrics_v2 optional | `run_lock` writes lock/ledger note | MEDIUM if run_lock misused |
| SOG OTLP | `_ops/telemetry/sog_metrics_v2.py` | `SOGTelemetry` / `snapshot_from_sog_math` | reuses `OCTOPUS_WIRE_CRITICALITY_OTLP` (off) | **SPEC_NOT_BUILT/STRUCTURAL** exporter off | schema test sog-snapshot | Alloy example only | none | LOW |
| control_law / living-beat | `_ops/heart/control_law.py` | `heart_step` L214 | bio/heart flags | **ARMED** in heart chain | heart tests | telemetry helper | feeds shadow/arbiter | HIGH coupled to pulse |
| heart shadow | `_ops/heart/shadow.py` | `shadow_step` | dedicated shadow sinks | **SHADOW path exists** | heart tests | shadow files | none if wire closed | MEDIUM |
| identity equations L/E/G/K/O | `_ops/identity_equations.py` | `evaluate` L371; `card` L461 | `OCTOPUS_WIRE_IDENTITY_EQ` | **ARMED read-only UI** if flag on | live_commands tests | TG cards | **none** (documented) | LOW overclaim risk if misread as auth |
| chrono rhythm CR-B0 | `_ops/chrono_rhythm/rhythm.py` | numeric core (module) | not in signals as implemented | Code exists; registry **SPEC_NOT_BUILT** | unknown/limited | — | module claims advisory-only | **DISCREPANCY** — code≠SPEC_NOT_BUILT label |
| agi2027 PolicyGate + idempotency | `_ops/agi2027_control/runtime.py` | `PolicyGate`, `IdempotencyStore` (~L87+) | ops paths | **ARMED** for ops-actions | agi2027 tests | sqlite | YES for allowed ops actions | HIGH — separate plane from ADR-033 |
| Redis | (various) | N/A | — | **Not required** for ADR-033 path (file/SQLite); Redis down simulated only in PainChaosRuntime mock | chaos shadow test | — | production Redis usage elsewhere possible | MEDIUM — fail-closed for Redis not universal |
| kill switch (ADR-033) | env `OCTOPUS_KILL_SWITCH` via talk_gate L35 | — | **not set in OCTOPUS-flags.cmd** | **STRUCTURAL** | unit tests set engange in chaos mock | trust_metrics counter | blocks talk_gate when env=1 | MEDIUM — not organism-global |
| outbound HTTPS / lead outbound | flags + integrations | — | `OCTOPUS_WIRE_OUTBOUND_HTTPS=1`, `LEAD_OUTBOUND=1` | **ARMED** (separate from Talk Discovery) | outbound tests | — | **YES real external effect** | **CRITICAL** for safety scope — out of Talk Discovery but live |
| Grafana Truth dashboard | — | — | — | **SPEC_NOT_BUILT** | — | — | — | — |
| octopus_test_pack layout (pytest unit/contract/…) | — | — | — | **SPEC_NOT_BUILT** (mission target; not present as package) | harness-style tests exist instead | — | — | — |

---

## 2. File:line evidence (selected choke points)

| Area | Location |
|---|---|
| Collaborator ADR-033 gate | `collaborator.py:121–173` quarantine + `guard_talk_discovery_draft` |
| Collaborator draft invariants | `collaborator.py:176–234` `external_effect=False`, `response_mode=draft` |
| PolicyGate exception→DENY | `policy_gate.py:84–91` |
| Hard-forbidden actions | `policy_gate.py:54–80`, `talk_discovery_policy.py:43–49`, `approval_state.py` FORBIDDEN set |
| MiniApp collab inject | `miniapp_gateway.py:223–226`, route `752+` |
| Ask / Mirror routes | `miniapp_gateway.py:558+`, `627+` |
| Daily cap | `collab_model_adapter.py:17–38,82+`; flags `1373–1374` |
| Pain→halt | `wiring.py:1812–1859` |
| LEARNED_APPLY armed | `OCTOPUS-flags.cmd:1191` vs comment in `wiring.py:1819–1820` claiming default-off / not in flags — **stale comment** |
| Pulse arbiter armed | `OCTOPUS-flags.cmd:1045`; `pulse_arbiter.py:54,478` |
| Criticality SHADOW | `criticality_v2.py` docstring + `evidence_level="SHADOW"` |
| Idempotency (ops) | `agi2027_control/runtime.py` IdempotencyStore; ADR-033 ledger `runtime/rollback.py:20,97–100` |
| Validator limits | `validate_signals_registry.py:15–32` schema-only |

---

## 3. Discrepancy list (docs / spec / runtime)

1. **Doctrine vs neural APPLY:** Mission forbids signal→authorization; live `OCTOPUS_NEURAL_LEARNED_APPLY=1` folds BCM-derived pressure into pain and can `protective_halt` (`wiring.py:1837–1859`). Registry lists BCM/pain as `may_gate=false` / `allowed_effect=none` — **understates live authority**.
2. **wiring comment stale:** Says LEARNED_APPLY «در OCTOPUS-flags.cmd نیست → default-off» but flags line 1191 sets `=1`.
3. **`_ops/control/` missing:** Enforcement is not a single package; ADR-033 PolicyGate is not the universal tool boundary.
4. **Dual PolicyGates:** ADR-033 `policy.PolicyGate` vs `agi2027_control.runtime.PolicyGate` — different planes; risk of assuming one covers all.
5. **chrono-rhythm-cr-b0:** Registry `SPEC_NOT_BUILT` + null path, but `_ops/chrono_rhythm/rhythm.py` exists (advisory numeric core). Truth should be at least STRUCTURAL after Stage 2.
6. **Validator gap:** Mission Stage 3 wants semantic/path/digest JSON report; current validator only jsonschema + print.
7. **Registry schema gap vs Stage 2 fields:** Missing required mission fields (`name`, `family`, `inputs`, `outputs`, `known_limits`, `promotion`) in YAML.
8. **Default CAP mismatch:** Adapter default 30 vs armed flag 20 — OK when flags load; tests that unset env may assume 30.
9. **Kill switch not global:** `OCTOPUS_KILL_SWITCH` only consulted in talk_gate; not in pulse arbiter / protective_override / miniapp actions.
10. **Outbound still ARMED:** `OUTBOUND_HTTPS` + `LEAD_OUTBOUND` live while Talk Discovery claims no external effect — true for collaborator path, false for organism overall.
11. **Pulse arbiter ARMED** while pulse_shadow_compare flag off — production period path exists without mandatory shadow divergence recording.
12. **Test pack layout:** Mission wants `tests/{unit,contract,e2e,redteam,chaos,evals,adr}/`; repo uses flat `_ops/tests/test_*.py` harness runner.
13. **WORKLOCK:** New suites exist on disk but absent from `run_all.py` (intentional per prior sessions).

---

## 4. Signals registry vs families to inventory later (Stage 2)

Present in registry (8): spectral-criticality-v2, spectral-metrics-sensor, bcm-stabilizer, hebbian-associator, nociceptor-pain, sog-dare-identity, kalman-shadow-period, chrono-rhythm-cr-b0.

**Not yet registered (code/docs exist):** identity L/E/G/K/O (`identity_equations.py`), legacy `doctor/spectral.py`, living-beat `control_law.py`, pulse arbiter, cardiac allometry (if present under heart), phi-accrual (chrono/doctor), Doctor Box dynamics, latent cosine retrieval, decay-reinforcement (BCM forgetting β), discovery facade.

---

## 5. External-effect map (organism-level)

| Path | Effect? | Notes |
|---|---|---|
| Collaborator / Talk Discovery | No | draft + content-free digest only |
| Ask / Mirror | LLM network | not ADR-033-gated the same way |
| protective_override | Yes (internal halt) | pain + optional learned_pressure |
| pulse_arbiter wire_open | Yes (period) | flag armed |
| LEAD_OUTBOUND / OUTBOUND_HTTPS | Yes (external) | armed; excluded from Talk Discovery vote but live |
| BCM/Hebbian persist | Disk write | local state files |
| ADR-033 replay | No if dry_run | enforced in `runtime/replay.py` |

---

## 6. Test runner / WORKLOCK status (no change this stage)

| Suite | Exists | In `run_all.py` |
|---|---|---|
| test_talk_discovery.py | yes | yes |
| test_cognitive_unify.py | yes | yes |
| test_approval_state.py | yes | **no** |
| test_adr033_control_plane.py | yes | **no** |
| test_signals_registry_schema.py | yes | **no** |
| test_kalman_shadow_pipeline.py | yes | **no** |
| test_bcm_hebbian_shadow_e2e.py | yes | **no** (flat path, not `tests/e2e/`) |
| test_nociceptor_chaos_shadow.py | yes | **no** (flat path, not `tests/chaos/`) |
| test_registry_semantic_validator.py | **no** | no |
| tests/adr/test_adr_033_invariants.py | **no** | no |

---

## 7. Items deliberately not changed (Stage 1)

- No edits to `run_all.py`, flags, PolicyGate, wiring, registries, dashboards, or production config.
- No feature flag arm/disarm.
- No attempted live side effects.
- No status promotions in registry.
- No creation of full pytest package layout yet.

---

## 8. Highest-priority risks for Stage 2+ (advisory only)

1. Reconcile **neural APPLY + protective_halt** with «signals never authorize» — either demote APPLY, or register as ARMED control effector with separate ADR (not a diagnostic signal).
2. Make ADR-033 PolicyGate the choke point for Talk Discovery **and** document that agi2027/ops-actions remain a second plane.
3. Upgrade registry validator to semantic + path existence + machine-readable report.
4. Align chrono-rhythm truth_status with existing `rhythm.py`.
5. Register identity / pulse arbiter / control_law honestly.
6. Only after Stages 2–9: propose WORKLOCK diff for `run_all.py`.

---

## 9. Owner gate

**Awaiting explicit owner approval before Stage 2 (Capability Truth / code changes / WORKLOCK).**

Suggested next owner choice:
- **A)** Proceed Stage 2–3 (registry+schema+validator only; no flag changes)
- **B)** First freeze/disarm `OCTOPUS_NEURAL_LEARNED_APPLY` pending ADR (policy decision)
- **C)** Stop after this inventory
