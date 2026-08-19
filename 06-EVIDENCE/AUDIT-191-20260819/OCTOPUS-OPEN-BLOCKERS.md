# OCTOPUS-OPEN-BLOCKERS — only BLOCKED / UNKNOWN / STALE / VOID items

Audit close: 2026-08-19T02:07Z. Source: OCTOPUS-FULL-AUDIT.md (same directory). Ordered by impact on the learning goal.

## BLOCKED

| # | Item | Evidence | Unblock condition |
|---|---|---|---|
| 1 | **Live-4 primary scoring** — `LIVE4_SCORING=BLOCKED_JUDGE_UNREADABLE_1_OF_4`. Six E2E runs; best 3/4; 1 judge output stays UNREADABLE even with V2 JSON + re-ask | labels.json:376-383; live4-pairs.jsonl (batch 9, 24 rows) | One clean 4/4 foreground E2E run (judge_unreadable=0, baseline_failure=0) |
| 2 | **Contradiction radar not wired** — code exists, no production writer sets `contradiction_checker`; NOW.md still claims ACTIVE/VERIFIED | gate.py:188-198; zero grep hits wiring it | Wire radar into MemoryGate writers, or downgrade label to CLAIMED |
| 3 | **Two-phase Admission class not wired** — imported only by a test; production uses single-phase MemoryGate.submit | admission.py vs wiring.py:3169 | Wire Admission (PENDING→ADMITTED) into production writers |
| 4 | **COST_UNOBSERVABLE fail-closed not wired in general path** — `paid_blocked` set but never read outside Live-4 driver | cost_receipt.py:80-81; model_router.py:313 | Router must consult paid_blocked / scan receipts before next paid call |
| 5 | **`LIVE4_PROTOCOL_VERSION=PENDING_V2_FREEZE`** — protocol not formally frozen/hash-pinned before primary sample | labels.json:421 (null evidence_hash) | Owner ratifies + hash-pins V2 freeze before batch 1 primary starts |

## STALE (time-critical)

| # | Item | Deadline (UTC) | Consequence if missed |
|---|---|---|---|
| 6 | **FX_PIN expires 2026-08-19T06:00:00Z** (~3h53m at close; hash valid, RBA 2026-08-18, rate 1.4082523588) | 06:00Z | `validate_fx` returns paid_fallback=BLOCKED → all Live-4 paid evaluation stops |
| 7 | **PROVIDER_CAPACITY label expires 04:00Z** (~1h53m) | 04:00Z | Label auto-downgrades; capacity must be re-probed before scoring session |
| 8 | **docs/NOW.md stale vs labels.json** (01:04:06Z vs 01:22:49Z; 6 labels missing incl. VALID_PAIRS 3→0 supersession) | — | Sole-truth page misleads; regenerate |
| 9 | **DAEMON_4D / DAEMON_PID labels expire 12:30Z** | 12:30Z | Re-observe daemon liveness (trivial, daemon healthy) |

## UNKNOWN

| # | Item | Missing evidence |
|---|---|---|
| 10 | **Live daemon's actual `OCTOPUS_TCB_MANIFEST_ENFORCE` env** — flag set in OCTOPUS-flags.cmd:1500 but daemon launched without the documented wrapper | Live process env inspection, or relaunch via wrapper |
| 11 | **confidence_source / confidence_method on SYSTEM_DETERMINISTIC_RULE rows** — 0 such rows exist; gate populates only if a writer provides | A deterministic writer cycle post-patch |
| 12 | **Holdout membership hash** — no separate hash pins which members are holdout | Sidecar hash file like the taxonomy/baselines have |
| 13 | **ESP32 physical inventory (~140 boards claim)** — no count/inventory doc anywhere in vault | Physical inventory scheme (K4 also VOID) |
| 14 | **Kimi/GLM discovery runbooks** — referenced in workflow lore, absent from vault | Authoring the two runbooks |
| 15 | **"Daily loop is owner-invoked" + "automatic FX fetching forbidden"** — no explicit decision text | One-line owner decision additions |

## VOID (mechanism absent — claim cannot hold as stated)

| # | Item | Detail |
|---|---|---|
| 16 | **label-history hash-linking** | No prev_hash/entry_hash fields exist; append-only+parseable only |
| 17 | **D-A failure categorization taxonomy** | No rate-limit/route-denied/timeout/parse/receipt classification anywhere |
| 18 | **"Do not modify primary threshold from confirmatory results" warning** | Batches 3-4 labelled confirmatory in code, but no freeze-protection text exists |
| 19 | **K4–K8 hardware artifacts** | No inventory scheme, ESP32 pilot contract, MQTT-vs-NATS decision, purchase list, or pilot scope doc |
| 20 | **QUOTA-RESET-OBSERVATION.json** | Never written; override activation bypassed observation; reset only inferable from fugu-quota day rollover |

## OPEN defects (CLAIMED status, tracked but unfixed)

| # | Item | Note |
|---|---|---|
| 21 | **F3_METADATA_ENTRY** — MemoryStore.insert still accepts incomplete metadata | Next best auto-debug candidate (bounded, non-TCB) |
| 22 | **D3_GIT_HISTORY_RISK** — `_ops/legs/mail_credentials.py` old versions remain in git history | Rewrite forbidden without owner decision |
| 23 | **budget_before_aud bug** — model_router.py:319 passes cost_usd as budget_before → all 82 receipts show negative budget_after | Cosmetic to enforcement, real to audit trail |
| 24 | **FX expiry unchecked in general paid path** (F18) and **local-fallback leg unreceipted** (F15) | Wiring gaps; Live-4 path is covered |
| 25 | **reservation start_override resets all counters** (G11) and timeout leaves no receipt (G10) | All-or-nothing restart; add receipt artifact |
| 26 | **incidents LIVE4-DEFECT-CLOSURE-AND-E2E-01 / CONTINUE-LIVE4-DA-DB-CLOSURE-02 have no decision files** | IDs referenced in label-history only |
| 27 | **E2E fixture lacks judge_unreadable=0 / baseline_failure=0 assertions** (E14) — gate exists only as a live manual run | Add to test_e2e_fixture.py |
| 28 | **judge_independence hardcoded True; duplicate rationale_hash across E2E pairs** (same rationale text reused) | Measure independence or disclose limitation in every report |
| 29 | **REFERENCE_DIR misconfigured** (`./` → C-013 fallback to nonexistent `4D/`) | Soft warning; fix .env value |
| 30 | **Daemon records 0 predictions/0 proposals this run** — learning loop not closing from daemon side | Wire prediction recording or document why not |
