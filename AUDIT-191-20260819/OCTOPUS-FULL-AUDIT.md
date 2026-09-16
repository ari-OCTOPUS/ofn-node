# OCTOPUS-FULL-AUDIT — Full State, Learning, Safety, Runtime and Hardware Audit

- **Auditor**: ZCode OCTOPUS Evidence Auditor (read-only; no repair, no deletion)
- **Audit window**: 2026-08-19T01:04Z → 2026-08-19T02:07Z (11:04–12:07 AUSEST)
- **Method**: direct process/DB/JSONL inspection + code reading + hash recomputation. Nothing was modified. Note: the registry, the Live-4 E2E loop and paid-calls.jsonl were **mutating live during the audit**; all counts carry their observation timestamp.
- **Key hashes**: `labels.json` sha256 `b575053d72ed7e72e36fc47b4c034e8c65f2243829a6afbef79891d5eb896347` (47-label state, 01:08:35Z) → `043719430bc3972f551fd85f62130c5eded06e998ea06acad4851275bea9e136` (50-label state, 01:22:49Z). `live4-pairs.jsonl` sha256 prefix `b0a0c4dc830f4304` (54 lines, 02:07Z).
- **Statuses used**: VERIFIED | OBSERVED | CLAIMED | BLOCKED | VOID | UNKNOWN | STALE.

## TL;DR (برای مالک)

سیستم سالم و ایمن است ولی **هنوز واقعاً یاد نگرفته**: `MEMORY_LIVE_LEARNING_UNVERIFIED`، زوج‌های معتبرِ_primary = **۰ از ۳۰**، و تنها مسدودکنندهٔ امتیازدهی، **۱ مورد از ۴ خروجی غیرقابل‌خواندن داور (D-B)** در گیتِ E2E است — شش تلاش اجرا شد و بهترین نتیجه ۳/۴ بود. دیمن زنده و لوکال است (صفر فراخوانی پرداختی). هزینهٔ امروز ≈ **$0.017 AUD**. پین FX ساعت **06:00Z امروز** می‌گذرد و اگر تازه نشود مسیر پرداختی Live-4 قفل می‌شود. باگ کوچک ولی واقعی در رسیدها (`budget_after` منفی) و سه شکاف سیم‌کشی (radar، paid_blocked، FX-expiry) ثبت شد. پروتکل Live-4 هنوز **PENDING_V2_FREEZE** است — پیش از شروع نمونهٔ primary باید توسط مالک فریز شود.

---

## A. Sole Truth, Registry, Documentation

**A1 — labels.json existence/validation**
ANSWER: Exists at `_ops/state/labels.json`, valid JSON, schema id `octopus-labels/1`, 47 labels at 01:08:35Z growing to 50 by 01:22:49Z (live-updating registry). No external JSON-Schema file exists to machine-validate against; validation is structural only.
STATUS: VERIFIED (existence/parse) · UNKNOWN (external schema validation)
EVIDENCE: `_ops/state/labels.json`; hashes above. TRACE: `python json.load` + sha256. TS: 2026-08-19T02:07:13Z.

**A2 — active label count by group**
ANSWER: 50 total. By NOW.md section mapping: SYSTEM 9, MEMORY 9, PROVIDER/BUDGET 11, LIVE-4 15 (incl. `LIVE4_PILOT_VALID_PAIRS`, `LIVE4_PRIMARY_VALID_PAIRS`, `LIVE4_PROTOCOL_VERSION`, `LIVE4_SCORING`, `D_A_BASELINE_ARM`, `D_B_JUDGE_CONTRACT`), INCIDENTS 6. Limitation: registry records carry no explicit group field; grouping inferred from the NOW.md renderer.
STATUS: OBSERVED. EVIDENCE: labels.json (50 labels, generated_at 2026-08-19T01:22:49Z).

**A3 — required fields per label**
ANSWER: value/status/evidence_path present on all 50. Update timestamp present as `updated_at_utc` (not `timestamp_utc`). `evidence_hash` is **null on 5 labels**: VALID_PAIRS, LIVE4_STATE, LIVE4_SCORING, D_A_BASELINE_ARM, D_B_JUDGE_CONTRACT. Hash length is inconsistent across labels (64-hex for some, 16-hex truncated for others, e.g. FX_PIN `9275047ac861592a`).
STATUS: OBSERVED (partial compliance). NEXT: populate evidence_hash on the 5 nulls; standardize hash width.

**A4 — label-history append-only/parseable/hash-linked**
ANSWER: 50→55 lines during audit, every line parses, chronologically append-only (INIT block at 01:04:06Z then TRANSITION entries). **Not hash-linked**: no `prev_hash`/`entry_hash` fields exist at all.
STATUS: VERIFIED (append-only, parseable) · VOID (hash-linking — mechanism absent).
EVIDENCE: `_ops/state/label-history.jsonl`.

**A5 — all status transitions represented in history**
ANSWER: Yes for everything since registry INIT (2026-08-19T01:04:06Z): 47 INIT + TRANSITIONs incl. `VALID_PAIRS 3→0` (owner_decision_id `LIVE4-DEFECT-CLOSURE-AND-E2E-01`), `D_A_BASELINE_ARM` supersedes chain, `LIVE4_PILOT_VALID_PAIRS=3`/`LIVE4_PRIMARY_VALID_PAIRS=0`. No history exists before INIT — pre-INIT transitions are unknowable.
STATUS: OBSERVED. EVIDENCE: label-history.jsonl lines 1–55.

**A6 — NOW.md generated, not hand-edited**
ANSWER: Header claims generation from labels.json and content is consistent with the 01:04:06Z label state, but **no generator script exists anywhere in the repo** (repo-wide grep). Generation is agent/session-invoked.
STATUS: CLAIMED. NEXT: check in a checked-in generator so regeneration is reproducible.

**A7 — NOW.md matches registry**
ANSWER: **No.** NOW.md generated 01:04:06Z vs labels.json 01:22:49Z. Missing: `D_A_BASELINE_ARM`, `D_B_JUDGE_CONTRACT`, `LIVE4_SCORING`, `LIVE4_PILOT/PRIMARY_VALID_PAIRS`, `LIVE4_PROTOCOL_VERSION`. Stale values: `VALID_PAIRS=3` (registry: 0), `LIVE4_STATE=ACTIVE_FG_PENDING_DEFECT_FIXES_DA_DB` (registry: `ACTIVE_DEBUG_NOT_SCORING`), `LIVE4_PROTOCOL=FROZEN` (registry: `PENDING_V2_FREEZE`).
STATUS: STALE. EVIDENCE: `docs/NOW.md:1` vs `_ops/state/labels.json`.

**A8 — Obsidian pages generated from same source**
ANSWER: No — `00-INDEX.md`, `01 - Dashboard/HANDOFF.md`, `06-RISKS/OPEN-GATES.md` are maintained by hand/agent sessions; only NOW.md claims label-derived generation. Multiple divergent current-state sources.
STATUS: OBSERVED.

**A9 — stale/expiring/blocked/void/unknown labels**
ANSWER (at 02:07Z): expiring — `FX_PIN` (expires 06:00Z, ~3h53m), `PROVIDER_CAPACITY` (expires 04:00Z, ~1h53m), `DAEMON_4D`/`DAEMON_PID` (expire 12:30Z). Blocked — `LIVE4_SCORING=BLOCKED_JUDGE_UNREADABLE_1_OF_4`. Open-claimed — `F3_METADATA_ENTRY=OPEN (CLAIMED)`, `D3_GIT_HISTORY_RISK=OPEN (CLAIMED)`. Void/unknown — none labelled as such.
STATUS: OBSERVED.

**A10 — VERIFIED without runtime evidence**
ANSWER: Two over-claims found: (1) `CONTRADICTION_RADAR=ACTIVE/VERIFIED` cites `gate.py`, but the radar is **not wired into any production writer** (see C4). (2) `LIVE4_PROTOCOL=FROZEN/VERIFIED` in NOW.md vs `LIVE4_PROTOCOL_VERSION=PENDING_V2_FREEZE` with null hash in registry. `D_A_BASELINE_ARM=FIXED_VERIFIED` is acceptable (8 consecutive clean baseline calls observed).
STATUS: flagged. NEXT: downgrade CONTRADICTION_RADAR to CLAIMED until wired; resolve protocol-freeze contradiction.

**A11 — owner decisions with ID/timestamp/evidence**
ANSWER: With records — CORE-LIVE-LEARNING-01, CARD-A-DISARM-2026-08-19, D3-PHASE2-UNTRACK-2026-08-19, A2-001, A2-SANDBOX-LAB-FIRST-TASK, F1-ACCEPTANCE (`02-DECISIONS/`); FX-PIN-20260819-01 (FX-RECORD.json), FREEZE-RELEASE-20260819-01 (receipt), LEARNING-FIRST-BUDGET-EXPANSION-01 (reservation state). **Missing decision files**: `LIVE4-DEFECT-CLOSURE-AND-E2E-01` and `CONTINUE-LIVE4-DA-DB-CLOSURE-02` — referenced as owner_decision_ids in label-history but no decision document exists.
STATUS: OBSERVED (gap on 2).

**A12 — single next unblock action**
ANSWER: Make the D-B judge contract produce **4/4 readable E2E cases** (currently 3/4 with 1 UNREADABLE), then release primary batch scoring (2×15). Everything else — daemon, provider, budget, freeze, memory gate — is green for this path.
STATUS: OBSERVED. EVIDENCE: `LIVE4-DA-DB-E2E-REPORT.md:19-20` ("۴case تازه؛ ۴/۴ ⇒ آزادسازی batch کامل").

---

## B. Core, Daemon and TCB Health

**B1 — daemon alive** VERIFIED. PID 18020, started 2026-08-18T13:08:39Z (23:08:39 AUSEST), cmdline `"C:\Program Files\Python313\python.exe" -X utf8 -m brain.daemon`, cwd `F:\backup\4d_system` (SYSTEM_ROOT resolution), ~500 MB RSS. No process-hash mechanism exists (UNKNOWN by design absence). TRACE: `Get-CimInstance Win32_Process -Filter "ProcessId=18020"`.

**B2 — protective HALT since restart** VERIFIED: zero. 0 HALT hits in `daemon-launch4b.err.log` and all sibling/watchdog logs since 08-18 23:08. Last HALT anywhere: `daemon-launch3.err.log:1371` (2026-08-16, root-caused in TCB-HALT-ROOT-CAUSE.md).

**B3 — most recent tick** OBSERVED: 2026-08-19T01:09:35Z+ (log appending in real time during audit; ~30 s cadence; 1352 ticks by 11:22 local per `daemon_state.json`).

**B4 — real activity vs looping** OBSERVED: 1356 task.started / 1162 completed / 0 failed / 194 blocked; 608 memory.read; 106 ideas generated, 358 deduped as repetitive; **0 hypotheses recorded, 0 predictions, 0 proposals** (self_code=False). The daemon reads memory and produces local compute, but the learning loop (predictions → outcomes) is not closing from the daemon side.

**B5 — provider-backed vs local** VERIFIED: daemon is **local-only** (`cloud_calls: 0` in daemon_state.json; Ollama not running). All 55 paid calls in the last 24 h are from the Live-4/non-daemon pipeline, 100% `deepseek/deepseek-v4-flash`.

**B6 — reachable shell/subprocess/scheduler/board/external paths** VERIFIED minimal: subprocess only in `git_watcher.py:101` and `self_code.py:347`, both gated behind `self_code_on=False`; no `shell=True`; zero ssh/board-IP/schtasks hits in the brain package; network only in budget-gated LLM clients.

**B7 — OCTOPUS_TCB_MANIFEST_ENFORCE in daemon env** UNKNOWN/AMBIGUOUS: set to `1` in `_ops/OCTOPUS-flags.cmd:1500`, but the daemon was **not launched via the documented wrapper** (`04-SYSTEMS/LAUNCHER-ENFORCE-INVARIANT-2026-08-16.md:54`). The pre-restart invariant (run with the flag set) showed `enforcement: true`; a check from the wrong cwd showed `false`. The live process's actual environment was not inspected. NEXT: relaunch via the wrapper or read the live env.

**B8 — live invariant checks** OBSERVED (preflight, 2026-08-18T23:07): `{"anchors_ok": true, "enforcement": true, "tampered": false, "mismatches": [], "signature": "valid"}` — `06-EVIDENCE/CL01-191-20260818-2233/preflight-invariant.txt`.

**B9 — cwd/REFERENCE_DIR** OBSERVED: cwd correct and reproducible. `REFERENCE_DIR='./'` in `4d_system/.env:22` trips the C-013 guard → fallback to nonexistent `SYSTEM_ROOT/'4D'` — permanent soft warning, degraded but non-fatal (`config/settings.py:33-46`).

**B10 — active TCB drift** VERIFIED: none. All 15 TCB digests in `4d_system/config/trust-boundary.json` match current files (recomputed during audit); `daemon_state.json: integrity_ok: true`.

**B11 — rollback/stop method** VERIFIED: `outputs/daemon.stop` file / SIGINT/SIGTERM / `daemon.pause` for the 4d daemon; STOP-ORGANISM / HALT-ALL for the organism; bounded `taskkill` as last resort (`04-SYSTEMS/HALT-DRILL-RUNBOOK-2026-08-16.md`). Rollback = `git checkout -- <touched-tcb-file>` + invariant re-check.

**B12 — stop preserves ledger/memory integrity** OBSERVED: graceful shutdown writes state atomically (`os.replace`, finally block, `daemon.py:294-299`); daemon stores are JSONL-append (no WAL). The organism's `chrono.db` has an active 4.2 MB WAL that needs a checkpoint for a clean organism stop — outside daemon scope.

---

## C. Memory, Admission, Retrieval, Learning

**C1 — canonical stores census** VERIFIED: (a) `_ops/state/memory/memory.db` — canonical graded SQLite, table `memory` (23 cols, FTS5), **508 rows**; writers: `gate.py:182` via MemoryGate (wiring.py, c6_trigger, verdict_recorder, receipt_critic, goal_action_bridge, self_loop_ingest, research_ingest); readers incl. retrieval_router, daily_loop (mode=ro), learning_evaluator (mode=ro). (b) `_ops/state/semantic_memory.jsonl` — raw reflection ingest, 253 rows, NOT canonical. (c) `_ops/state/chrono.db` — time-series (heartbeat 41,500; experience_meter 41,053 …).

**C2 — research vs canonical separation** VERIFIED: `4d_system/outputs/4d_experiments.db` (hypotheses 1,439; patterns 1,000 …) is separate; `write_gate_enforcer.py` exists precisely because the 4d brain's `save_hypothesis()` bypasses the graded gate — a known, bounded exception.

**C3 — MemoryGate on live path** OBSERVED/partial: MemoryGate wired (`wiring.py:3169`, `OCTOPUS_WIRE_MEMORY_GATE=1`) and is the only insert path; but the **two-phase `Admission` class is imported only by a test** — production writers use single-phase `MemoryGate.submit()`.

**C4 — contradiction radar before ADMITTED** BLOCKED: radar code exists (`admission.py:121-137`, `contradiction_radar.py`) and gate.py supports an optional `contradiction_checker`, but **no production writer sets it** (zero grep hits outside the modules themselves). The NOW.md label `CONTRADICTION_RADAR=ACTIVE/VERIFIED` is therefore an over-claim.

**C5 — bypass of MemoryGate** VERIFIED: none found. `store.insert()` is called at exactly one production location (`gate.py:182`); all write-capable MemoryStore instantiations are gate-wrapped.

**C6 — undocumented sqlite/open paths** VERIFIED: full census in C1/C5; only read-only `mode=ro` connects target memory.db outside the gate (`daily_loop.py:44`, `learning_evaluator.py:83`).

**C7 — enforced admission fields** VERIFIED (partial): 8 REQUIRED_META enforced (`admission.py:26-27`: trace_id, parent_id, timestamp, actor, source, schema_version, idempotency_key, confidence) + tenant/project/agent (`gate.py:138-139`); 16/23 columns NOT NULL. **evidence_ref is validated at admission but not stored as a column**.

**C8 — status counts** VERIFIED: ADMITTED=500, PENDING=1, RETRACTED=7, QUARANTINED=0 (total 508).

**C9 — metadata completeness** OBSERVED: of 500 ADMITTED — provenance_json/created_at/valid_to 100%; **confidence NULL 42 (91.6% complete)**; salience NULL 52; mkey NULL 45.

**C10 — excluded records** VERIFIED: the 42 confidence-missing historical records are excluded **at query time** (`live4_harness.py:133-140` REQUIRED_ROW; `live4_driver.py:105-107` WHERE clause) — never altered.

**C11 — deterministic confidence distinguishable** CLAIMED: mechanism coded (`live4_harness.py:142-144` excludes SYSTEM_DETERMINISTIC_RULE from LLM calibration) but **0 such rows currently exist**.

**C12 — confidence_source/method on deterministic rows** UNKNOWN: no records to inspect; `gate.py:167-168` populates the fields only if a writer provides them — none does today.

**C13 — raw vs canonical separation** VERIFIED: raw trails (`self-loop-ingest.jsonl` 1.09 MB, `research-ingest.jsonl`, `semantic_memory.jsonl`) are append-only and never ADMITTED by construction (`admission.py:15-16`).

**C14 — retrieval provenance** VERIFIED: `memories_used` carries memory_id, content_sha256, trust_grade (`memory_store.py:321-324`; `retrieval_router.py:110`).

**C15 — retrieved memory alters proposal** VERIFIED: direct causal trace in Live-4 — evidence rows fetched with mem_-ids injected into the conditioned prompt (`live4_driver.py:103-124`), recorded per pair (`evidence_ids`), wins attributed.

**C16 — paired baseline-vs-evidence record** VERIFIED: `live4-pairs.jsonl` (batch/pair/void/cond_won/cond_position/evidence_ids/baseline_sha/cond_sha/judge{verdict, rationale_hash, provider, model, trace_id}) + `API-RECEIPTS.jsonl`.

**C17 — honest learning verdict** VERIFIED: `MEMORY_LIVE_LEARNING_UNVERIFIED` — sole failing condition is ④ valid evidence-conditioned pairs (currently 0 primary) — `live3/LEARNING-VERDICT.md`.

**C18 — upgrade evidence** VERIFIED: `learning_evaluator.py:104-121` requires Brier delta > 0.0 AND provenance coverage ≥ 0.9, plus the owner's condition ④ (valid pairs per frozen Live-4 protocol: ≥30 valid, ≥20 conditioned wins).

---

## D. Prediction, Outcome, Evaluation, Calibration

**D1 append-only ledger** VERIFIED (INSERT-only code; schema `prediction-ledger.v1`). **D2 triggers** VERIFIED: four `RAISE(ABORT)` triggers block UPDATE/DELETE on predictions and outcomes (`prediction_ledger.py:68-80`, confirmed in sqlite_master). **D3 id uniqueness** VERIFIED: prediction_id TEXT PK; 109 IDs, 0 duplicates. **D4 temporal order** VERIFIED: 0 rows with outcome_at ≤ created_at. **D5 backdating/duplicate rejection** VERIFIED in code (ValueError on backdating and future-skew >300 s).

**D6 — counts** VERIFIED: predictions 109, outcomes 102 (6 predictions without outcome), hits 40, misses 17, voids 46; eligible 57.

**D7 — Brier per frozen run** VERIFIED: Live-1 = 0.0225 (n=1), Live-2 = 0.1195 (n=20, baseline), Live-3 = 0.026 (n=30). Live-4: no scored primary pairs yet.

**D8 — frozen+hashed artifacts** OBSERVED: TASK-CLASS-TAXONOMY.json sha256 `8d33263f…`, BASELINE-L3 `a4a97d17…`, BASELINE-L2 `f56f9ea5…` (sidecar .sha256 files). **Holdout membership has no separate hash** (UNKNOWN).

**D9 — group-B label** VERIFIED: `UNDERCONFIDENT_OR_INCONCLUSIVE` — not "perfect" (`live3/CORRECTION-CALIBRATION.md:3`).

**D10 — composition-shift caveat** VERIFIED documented (`CORRECTION-CALIBRATION.md:4`).

**D11 — provider failure vs decision error** OBSERVED: Live-3 provider failure 1/18 (5.6%); decision error 8/30 (26.7%). Historical Live-4 voids were mostly the freeze/tier defects, now fixed.

**D12 voids excluded** VERIFIED (`learning_evaluator.py:67-73`; void text matches no scoring pattern; driver routes voids to R["voids"]). **D13 no void-as-valid path** VERIFIED (driver/fg_runner/harness all VOID→continue; zero grep hits to the contrary).

**D14 — unit costs** VERIFIED (computed 01:30Z): Live-4 paid calls 132 totalling **$0.006473 AUD** → $0.000049/call; per valid pair (3 then) $0.002158; per evidence-conditioned win (2 then) $0.003236. (At close: 11 non-void rows / 4 wins incl. E2E — primary-scoring pairs still 0.)

**D15 — pilot/primary isolation** OBSERVED: separate labels (PILOT=3 / PRIMARY=0) but **one shared live4-pairs.jsonl** with no mechanical firewall — procedural, not structural.

---

## E. Live-4 Protocol and Defects

**E1** OBSERVED: `LIVE4_STATE=ACTIVE_DEBUG_NOT_SCORING` (labels.json:258, updated 01:12:07Z). NOW.md's `ACTIVE_FG_PENDING_DEFECT_FIXES_DA_DB` appears nowhere in evidence — stale.
**E2** OBSERVED: `LIVE4_PROTOCOL_VERSION=PENDING_V2_FREEZE` (labels.json:421, null evidence_hash). Taxonomy self-labels "frozen 2026-08-19" but no freeze-moment hash exists. **Protocol not formally frozen.**
**E3** OBSERVED: pilot valid 3 (`LIVE4_PILOT_VALID_PAIRS`), primary valid 0, confirmatory 0 (batches 3-4 never ran); batch 9 = E2E foreground gate (6 runs × 4 cases during audit).
**E4** VERIFIED final counts (02:07Z, 54 lines): voids — `exc:IntegrityError` 19, `judge` 13, `base=False/fugu cond=deepseek-v4-flash` 7, `exc:KeyError` 4 (total 43); non-void 11, cond_won 4.
**E5** VERIFIED: primary metric = VALID_PAIRED_CASES.
**E6** OBSERVED gap: PROVIDER_CAPACITY exists as a label but is **not shown beside valid_pairs** in any structured daily report (interim status is free-form narrative).
**E7** VERIFIED: criterion is exactly 2 batches × ≥15 pairs, ≥30 total valid, ≥10 wins/batch, ≥20 wins total (TASK-CLASS-TAXONOMY.json:4-6).
**E8** OBSERVED + VOID: batches 3-4 labelled confirmatory in code (`live4_driver.py:149-151`), but **no text forbids modifying the primary threshold from confirmatory results**.
**E9/E10** VERIFIED: deterministic seeded RNG decides A/B before the judge call; mapping recorded in the same record. No cryptographic sealing step exists (limitation).
**E11** OBSERVED: `judge_independence_limited` is **hardcoded True** (`live4_fg_runner.py:44` — same provider family as arms), not measured.
**E12** OBSERVED: **three parsers of varying strictness coexist** — `parse_judge` (lenient, still used by the original driver), `judge_contract` (plain-text), `judge_json` (strict JSON, fg_runner only). The strict contract is not the only acceptance path in code.
**E13** VERIFIED: in contract/json paths any malformed/prose/missing-field output → UNREADABLE → void=true (`live4_harness.py:82,89,115-116`).
**E14** VERIFIED absence: `test_e2e_fixture.py` (3 tests) asserts **no** `judge_unreadable==0` / `baseline_failure==0` gate.
**E15** VERIFIED: D-A root cause = `ask_fugu` called without tier → `TASK_TIERS.get(task,"local")` → baseline ran on local qwen2.5:1.5b while conditioned ran deepseek (asymmetric arms). Fix = explicit `tier="primary"` in both arms; reproduced from original traces (`live4-b1-base-*`).
**E16** OBSERVED reproduction exists; VOID: no formal failure-category taxonomy (rate-limit/route-denied/timeout/parse/receipt/other).
**E17** VERIFIED post-fix: both arms on `deepseek-v4-flash` primary — `FIXED_VERIFIED_0_FAILURES_IN_LAST_8` baseline calls. (Pre-fix voids `base=False/fugu` remain as history.)
**E18** VERIFIED: local/freeze fallback always `evaluation_eligible=false` (`TIER-ROUTING-CONTRACT.md:9`; `model_router.py:645`).
**E19** VERIFIED: D-B fixed by code (strict `judge_json`) **plus 8 tests** (`test_judge_json_v2.py`) — not prompt-only.
**E20** VERIFIED-NO: the composite 4/4 gate has **not passed**. Six live E2E runs during the audit: 3/4 (1 judge-void) → 4×KeyError → 4×IntegrityError → 4×judge-void → 2/4 → 3/4 (V2 JSON + re-ask). Best = 3/4; `judge_unreadable=1` persists.
**E21** OBSERVED: exact remaining blocker = **1-of-4 judge UNREADABLE**. Until a fresh 4-case run yields 4/4, primary scoring stays blocked per owner ruling.

---

## F. Provider, Routing, Cost, Budget

**F1** VERIFIED tier map: local=ollama/qwen2.5:1.5b; secondary=primary=DeepSeek `deepseek-v4-flash` (role=reason); fugu = explicit quota path (`model_router.py:116-138,515-518`).
**F2** VERIFIED: post-INC-2 the map matches the owner TIER-ROUTING-CONTRACT.
**F3** computed (last 200 paid-calls lines): 43 primary + 40 secondary ok calls (all deepseek-v4-flash, metered); 34 ok=false denials/errors.
**F4/F6** VERIFIED: 82/82 receipts carry provider + exact_model + all 12 core fields (100%); `cost_method=REPORTED`, `receipt_status=COMPLETE`. Gap: `fx_usd_to_aud`/`fx_pin_id` present on 0/82 (emitted only for DETERMINISTIC_ESTIMATE).
**F5** VERIFIED: COST-OBS-1 inline in `_ask_paid()` (`model_router.py:305-329`).
**F7** PARTIAL/BLOCKED-wiring: `COST_UNOBSERVABLE` sets `paid_blocked=True` (`cost_receipt.py:80-81`) but the **general paid path never reads it** — only the Live-4 driver scans receipts. The comment's fail-closed promise is not wired.
**F8** VERIFIED: free calls = `FREE_OR_UNBILLED`, cost None, budget unchanged, explicit "not claimed as 0 AUD" note.
**F9** computed: **today (AUSEST day) $0.011869 USD = $0.016714 AUD**; all-time $0.452982 USD = $0.637913 AUD; budget-state `spent_month_aud=0.753346` (includes historical Fugu subscription estimates — reconciles the delta).
**F10** VERIFIED effective caps: general path — 2 AUD/day + 30 AUD/month (budget_gate), cost_receipt defaults 0.50/call + 12 hard-stop; **Live-4 — 30/24/1 AUD enforced in driver** (`live4_driver.py:32,55-56`).
**F11** **BUG VERIFIED**: `model_router.py:319` passes `cost_usd` as `budget_before_aud` → **all 82 receipts show negative budget_after**. Real enforcement (organ_gate, file-locked) is unaffected — receipt fields are audit-cosmetic and currently wrong.
**F12** VERIFIED: file-lock atomicity (O_CREAT|O_EXCL + stale-steal); idempotency is in-process only (not cross-restart).
**F13** VERIFIED: 0 duplicate trace_ids across 82 receipts; double-charge not possible in practice.
**F14** VERIFIED: primary-failure + fallback-success both visible in paid-calls.jsonl; `fallback_of` field exists but router doesn't populate it.
**F15** GAP: the local fallback leg itself is **not receipted** through COST-OBS-1 (semi-silent; only `record_fallback()`).
**F16** VERIFIED: FX pin valid — hash **recomputed and matching** `839517e3…`; age 19h15m at check; **expires 2026-08-19T06:00Z** (~3h53m left at audit close).
**F17** VERIFIED: RBA record — source `RBA_EXCHANGE_RATES_DAILY_2026-08-18`, ts 06:00Z, AUD_USD 0.7101 → reciprocal 1.4082523588, pin `FX-PIN-20260819-01`, hash valid.
**F18** GAP: FX expiry blocks **Live-4 only** (`live4_harness.py:44`); the general paid path has **no expiry check** — stale-rate conversions possible after 06:00Z.
**F19** VERIFIED: provider quota (fugu-quota.json: day 2026-08-19, used 42) distinct from local budget (spent_today_usd 0.008694); DeepSeek separate $20 USD/week cap.
**F20** VERIFIED documented: `organ_gate.settle()` Errno 22 (Windows file-lock) → catch-all `opslib.freeze()` → 3-day freeze (2026-08-16T20:09Z → 2026-08-19T10:17Z local); silent-local-fallback transparency defect since patched (`PAID_PATH_BLOCKED_BY_FREEZE` annotation).
**F21** VERIFIED: foreground-only in practice; no scheduler integration anywhere.
**F22** computed: reservation caps 200 provider attempts / 60 pairs / 60 judge evals / 90-min window; used 76 attempts, 11 pairs; **124 attempts remaining**; window ~33 min elapsed at check. Activation was `start_override("LEARNING-FIRST-BUDGET-EXPANSION-01")`.

---

## G. Freeze, Reservation, Router Safety

**G1** VERIFIED: release receipt `_ops/budget/FREEZE-RELEASE-RECEIPT.json` (owner decision FREEZE-RELEASE-20260819-01, 2026-08-19T10:17:06 local); flag archived as `FREEZE.flag.released-…`, not deleted.
**G2/G3** VERIFIED: root cause + structured metadata (freeze_id FREEZE-LEGACY-2026-08-16, reason_code LEGACY_UNSTRUCTURED, scope all-organs/paid-grants, created 2026-08-16T20:09:05, release condition owner-manual).
**G4** VERIFIED: three blocking layers (organ_gate pre-check; router loop "skipped-frozen"; post-hoc annotation + paid-calls entry). 0 block entries since release.
**G5** VERIFIED post-patch: frozen paid request can no longer masquerade as a local success — explicit `fallback_reason`/`provider_actual`/`evaluation_eligible=false` injection.
**G6** VERIFIED (`model_router.py:645`).
**G7** VERIFIED: reservation active only inside the 90-min window, auto-stops (`live4_reservation.py:73-74`).
**G8** VERIFIED: deferral happens at the top of `ask()` **before** provider dispatch (`model_router.py:619-633`).
**G9** VERIFIED: exactly 1 `DEFERRED_FOR_LIVE4_RESERVATION` receipt (task=summarize, cost 0, provider none) at 11:17:36 local.
**G10** PARTIAL: auto-timeout yes; **no dedicated timeout receipt artifact** (state JSON only).
**G11** PARTIAL: `stop()` preserves counters; `start()`/**`start_override()` resets all counters to zero** — all-or-nothing, previous window state lost.
**G12/G13** GAP: `QUOTA-RESET-OBSERVATION.json` does not exist; the override activation bypassed quota-reset observation; reset only inferable from fugu-quota day rollover.
**G14** VERIFIED: zero scheduler/crontab/schtasks references in reservation/launcher code; SCHEDULER=UNCHANGED holds.

---

## H. Incidents, Self-Debugging, Patch Promotion

**H1** VERIFIED register: INC-CL1-001 FIXED_VERIFIED (real telemetry origin, H3) · INC-2 (tier map) FIXED_OR_MONITORED · FREEZE_ERRNO22 FIXED_VERIFIED · F3_METADATA_ENTRY OPEN (CLAIMED) · D3_GIT_HISTORY_RISK OPEN (CLAIMED) · CARD-A CLOSED_DISARMED. **D-A/D-B are labels, not formal incidents** — no standalone incident files; documented only inside E2E reports.
**H2** VERIFIED: both FIXED_VERIFIED incidents have reproduction, patch diff, test run (11/11 PASSED), rerun, rollback artifact and TEST-EVIDENCE-MANIFEST.sha256.
**H4** VERIFIED: 42 historical confidence-missing rows excluded, not altered.
**H5** OPEN: F3 unpatched (`MemoryStore.insert` still accepts incomplete metadata — "F3-full").
**H7** VERIFIED: Live-4 scoring blocked by D-B judge unreadability only; F3 blocks learning-promotion metadata eligibility, not scoring.
**H8** VERIFIED: CORE-AUTO-DEBUG scope limits explicit (small patches, reproducible bug + rollback, non-TCB; TCB = owner ceremony).
**H9** OBSERVED: no unattended TCB change detected; 20 commits since 08-12 touch governed dirs; 1:1 commit→decision mapping not fully traced (limitation).
**H10** VERIFIED for CL01 promotions (diff/rollback/test-hash/manifest); the older self-patch ledger (`sp-*.json`) lacks those link fields.
**H11** OBSERVED: highest regression risk = **INC-2 tier-map** — current fix is execution-only (driver forces tier), the router-level root cause (`_has` map) remains pending.
**H12** OBSERVED: next auto-debug candidate = **F3** (bounded, non-TCB, precisely specified).

---

## I. Safety, External Boundaries, Security

**I1** VERIFIED: `/sh` disarmed; fail-closed tested **without executing a shell command** (`_ops/tests/test_raw_shell_capability.py:129-136` asserts ok=False/ran=False while disarmed).
**I2** VERIFIED: activation flag archived (`_ops/ACTIVATION-RAW-SHELL.flag.disarmed-20260819-104530`) + owner decision CARD-A-DISARM.
**I3** VERIFIED: no scheduler/service/timer changes (F1-191 report; label UNCHANGED).
**I4** VERIFIED: no boards/SSH/discovery/tunnel actions in scope (R01 manifest; DENY list).
**I5** VERIFIED: external actions PROPOSE_ONLY; `executable=False` by default (`wiring.py:1969`).
**I6** VERIFIED: output guard blocks `os.system`/`subprocess.*`/dynamic import patterns (`output_guard.py:56`); deny-list prevents governance-file self-modification.
**I7** VERIFIED: admission.py is the sole canonical write path, fail-closed on missing metadata.
**I8** VERIFIED: no unredacted secrets found in receipts/logs/evidence (flags snapshots show `<redacted>`; the one `sk-…` string is a clearly-marked fake test fixture).
**I9** VERIFIED: D3 phase-2 complete — `git rm --cached` + .gitignore; `git ls-files` shows no credential files tracked.
**I10** VERIFIED: `.env` **never committed** (0 commits in history for .env/.env.bak). `_ops/legs/mail_credentials.py` old versions **do remain in git history**; risk explicitly OPEN; rewrite forbidden without owner.
**I11** VERIFIED: TCB manifest (15 files, sha256 digests, Ed25519 signature) enforced by `check_trust_boundary()` gating execution.
**I12** VERIFIED: all hard stops active — TCB mismatch, budget/cost-unknown, receipt-required, bypass fail-closed, metadata failure, forbidden-action list, plus HALT-ALL.

---

## J. Obsidian, NOW, Audit, Knowledge Continuity

**J1** OBSERVED: decisions/incidents/runs mostly recorded; **missing**: decision files for LIVE4-DEFECT-CLOSURE-AND-E2E-01 and CONTINUE-LIVE4-DA-DB-CLOSURE-02; D-A/D-B exist only under 06-EVIDENCE.
**J2** OBSERVED: additive/historical pattern held in sampled histories (archives, dated evidence dirs, immutable decisions).
**J3** VERIFIED: pages link evidence manifests + sha256 hashes (HANDOFF, promotion reports).
**J4** VERIFIED: NOW.md distinguishes all five (paid smoke / daemon running / Live-4 blocked / learning unverified / valid pairs) — but see J10 staleness.
**J5** VERIFIED: `06-RISKS/OPEN-GATES.md` lists F3, D3, FX_PIN, D-A/D-B.
**J6** UNKNOWN: no explicit "daily loop is owner-invoked, not scheduler" statement found (only implied by SCHEDULER=UNCHANGED).
**J7** UNKNOWN: no explicit "automatic FX fetching forbidden" decision (implicit via PROPOSE_ONLY/DENY external-send).
**J8** VERIFIED: budget caps + receipt policy documented in decision + NOW.md.
**J9** OBSERVED: 19/20 sampled links valid; 1 broken — HANDOFF links `FOURD-DAEMON-RESTART-…` but file is `4D-DAEMON-RESTART-2026-08-17.md`.
**J10** VERIFIED: operational facts missing from Obsidian — NOW.md lacks the 6 newest labels; the six batch-9 E2E attempts and VALID_PAIRS 3→0 supersession are not yet in any vault page.
**J11** OBSERVED over-claims: (1) 00-INDEX marks CURRENT-TRUTH "verified" though stale since 08-15; (2) GATES.md header `status: unverified` vs detailed verified body; (3) NOW.md `LIVE4_PROTOCOL=FROZEN` vs registry PENDING_V2_FREEZE.
**J12** Recommendation: read **`docs/NOW.md`** (after regeneration) → `06-RISKS/OPEN-GATES.md` → `02-DECISIONS/CORE-LIVE-LEARNING-01-2026-08-18.md`.

---

## K. Hardware, Sensorium, Future Cluster

**K1** PARTIAL: only **.191 (laptop DESKTOP-KA9RFN5)** live-verified (F1-191 process inventory). `.180` CLAIMED (continuity candidate, never started). `.182` OBSERVED-documented (SMB/NATS/sentinel docs; no live probe in scope). `.138` CLAIMED (watchdog services documented). **No verified RAM/storage/OS/health matrix for any Orange Pi.**
**K2** Covered by K1: verified = laptop only; the rest assumed/claimed.
**K3** UNKNOWN/CLAIMED: **no document in the vault evidences "~140 idle ESP32 boards"** — owner statement only; no count, no inventory file.
**K4–K8** VOID: no physical inventory scheme, no ESP32 pilot contract, no MQTT-vs-NATS decision, no purchase list, no pilot scope (sensor-only vs actuator) exists anywhere.
**K9** VERIFIED: board contact prohibited in active scope (BOARDS=NO_CONTACT; DENY list; R01).
**K10** VERIFIED: owner-gated hardware actions enumerated (any SSH, service install, network change, credential deployment, timer creation, activation beyond observe-only).
**K11** UNKNOWN: no Kimi/GLM discovery runbooks found in the vault.
**K12** VERIFIED: `.180` remains not started until owner approves role+gate.

---

## L. Owner Decisions Required

**L1 — blocked only on owner**: (a) FX re-pin before 06:00Z today (Live-4 paid path auto-blocks on >24 h pin); (b) ratify/freeze LIVE4_PROTOCOL_VERSION V2 **before** the primary sample; (c) D3 git-history purge (rewrite currently forbidden); (d) any hardware/board action; (e) judge-provider change if the next D-B iteration still fails; (f) re-arm reservation override if the 90-min window lapses before scoring.
**L2 — decision most increasing 30-valid-pair odds**: keep the Live-4 lane unblocked end-to-end — fresh FX pin + protocol freeze + reservation re-arm, so the moment D-B hits 4/4 the primary batches can run inside one window.
**L3 — highest irreversible risk**: git history rewrite (credential purge); second: any board/SSH contact.
**L4 — do NOT authorize yet**: board/SSH/ESP32 purchases or pilots, .180 activation, git rewrite, budget-cap raise beyond 30/24/1, TCB edits, automatic FX fetching.
**L5 — best next action after D-A/D-B fixed**: fresh 4-case foreground E2E; on 4/4 → release 2×15 primary batches with VOID accounting and side-by-side PROVIDER_CAPACITY reporting.
**L6 — evidence for LEARNING_VERIFIED**: Brier delta > 0 on frozen task classes, provenance coverage ≥ 0.9, ≥30 valid pairs with ≥20 conditioned wins under the frozen protocol, deterministic-rule rows separated, judge-independence limitation disclosed.
**L7 — falsifiers**: no Brier improvement on identical classes/eligibility; wins < 20/30; gains explainable by dataset-composition shift; coverage < 0.9; voids correlated with condition arm.
**L8 — one-line operational truth**: *Daemon healthy and local-only; learning UNVERIFIED with 0/30 primary valid pairs; scoring blocked solely by 1-of-4 judge-unreadable E2E cases; FX pin expires 06:00Z; spend trivial (~$0.017 AUD today); safety boundaries intact.*

---

*Generated read-only by the OCTOPUS Evidence Auditor, 2026-08-19T02:07Z. Companion files: OCTOPUS-OPEN-BLOCKERS.md, OCTOPUS-NEXT-24H-ACTIONS.md, OCTOPUS-CLAIMS-VS-EVIDENCE.md, OCTOPUS-OWNER-DECISIONS.md (same directory).*
