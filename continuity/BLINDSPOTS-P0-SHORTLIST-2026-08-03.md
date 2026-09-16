# OCTOPUS Blindspots — P0 SHORTLIST

> Generated: 2026-08-03
> Source: 6 blindspot files (items 1-565), excluding missing MASTER-BACKUP (328-463)
> Items triaged: ~433 present items
> Criteria: owner control / stop / kill seam / state corruption / data loss / safety bypass

---

## Summary Statistics

| Category | Count |
|---|---|
| **P0** | **38** |
| P1 | 42 |
| P2 | 66 |
| P3 | 73 |
| R | 60 |
| needs_review | 21 |
| duplicate | 18 |
| obsolete | 1 |

---

## P0 ITEMS — Fix Now

### Safety Bypass / Control Seam

| ID | Title | Evidence | Decision | Notes |
|---|---|---|---|---|
| 30 | arm_gate_enforcing:false, wire_actuator:false — EffectorGate pass-through | ORGANISM-STATE.json | fix_now | All actions pass through without enforcement. |
| 276 | (dup of 30) | ORGANISM-STATE.json | duplicate | Same root cause. |
| 302 | context_fence only alerts, never blocks | context_fence.py | fix_now | Safety mechanism is advisory-only. Should block. |
| 305 | Watchdog split-brain: two divergent organism-watchdog.ps1 | organism-watchdog.ps1 | fix_now | Two watchdogs with different logic. |
| 316 | Flag grammar 4 competing idioms — one flag can be on and off simultaneously | _ops/ | fix_now | Safety flags bypassed by different readers. |
| 74 | Stale-lock break at 30s steals lock from slow writer | opslib.py:241-255 | fix_now | Slow writer loses lock mid-write. Data corruption. |
| 145 | O_CREAT\|O_EXCL not truly atomic on Windows — stale-reclaim 30s | pending_card_recovery.py:180-220 | fix_now | Two processes can hold lock simultaneously. |

### Data Loss / State Corruption

| ID | Title | Evidence | Decision | Notes |
|---|---|---|---|---|
| 53 | latent_space silently wipes on corruption | latent_space.py:176 | fix_now | except:pass → start fresh = invisible data loss. |
| 54 | BCM forgetting is irreversible — keys below w_floor permanently deleted | bcm-weights.json | queue | No restore from consolidation log. |
| 71 | hebbian observe() not thread-safe | hebbian.py observe() | fix_now | Concurrent beat can drop co-occurrence increments. |
| 315 | Hebbian/BCM in-memory state from multiple threads without lock | hebbian.py, bcm.py | fix_now | Data corruption in neural state. |
| 271 | beat_seq silently restarts from 1 if chrono.db empty/corrupt | chrono.py | fix_now | Should fail-closed. |
| 314 | 595 except:pass silent, 56 in budget/neural, some in persist money verdict | _ops/ | fix_now | Silent exception swallowing in critical paths. |
| 38 | _close_intents loops on non-unique intent → contradictory closures | goal_directed.py:263-275 | fix_now | State corruption from infinite loop. |
| 148 | _load_store corrupted → {} silently — all pending money cards vanish | pending_card_recovery.py:139-147 | fix_now | Silent data loss of all pending money cards. |
| 197 | No signal handler — SIGTERM = hard kill, state lost | organism.py | fix_now | No graceful shutdown. |
| 205 | RESTART-REQUESTED without TTL — infinite restart-loop | organism.py | fix_now | Restart marker persists across reboots. |
| 509 | 111 modified + 277 untracked — 24K insertions uncommitted | git status | fix_now | Massive uncommitted changes at risk. |
| 490 | approval_store.py dual-write — phase-1 + phase-2, silent divergence | approval_store.py:85-111 | fix_now | Two approval stores can diverge silently. |

### Money / Credential Leakage

| ID | Title | Evidence | Decision | Notes |
|---|---|---|---|---|
| 131 | redact() fail-open — exception returns unredacted text to Telegram | approval_channel.py:2859 | fix_now | **CRITICAL PII leak.** |
| 132 | _redact_pii() second layer silently disabled on import error | approval_channel.py:2874 | fix_now | Second PII defense no-ops. |
| 133 | TOCTOU between on_human_judgment and status read — double-settle | approval_channel.py:1088-1091 | fix_now | Race condition in money approval. |
| 134 | APPROVING state sticks forever if crash between persist and settle | approval_channel.py:1069-1076 | fix_now | No timeout-reconciliation. Money card stuck. |
| 135 | Wall clock for expiry — backward jump re-validates expired tokens | pending_card_recovery.py:72 | fix_now | NTP jump = money token bypass. |
| 136 | State machine without transition whitelist — any transition allowed | pending_card_recovery.py:542 | fix_now | APPROVED→APPROVING, DENIED→APPROVED both allowed. |
| 137 | 409 continues consuming — throttled alert but no stop | approval_channel.py:419-423 | fix_now | Callbacks silently eaten by rival consumer. |
| 138 | autonomy_matrix.is_important() only checks top-level fields | autonomy_matrix.py:47-59 | fix_now | Nested amount_aud=5000 bypasses as 'free'. |
| 182 | ps_writeback.py can POST behind read-only flag | OCTOPUS_WIRE_POCKETSMITH | fix_now | Read-only contract violated. |
| 183 | Ledger hash-chain verify failure non-blocking — organism continues | brain_worker.py:251-256 | fix_now | Corrupt audit trail silently ignored. |
| 191 | _effectively_reversed without cycle detection — J1<->J2 mutual reverse | ledger_core.py:291-300 | fix_now | Both journals settle, neither reversible. |
| 496 | OWNER-PROFILE.json with PII tracked in git (commit 76f58ca) | _ops/state/OWNER-PROFILE.json | fix_now | **CRITICAL: PII in git history forever.** |
| 497 | OWNER-PROFILE-LOG.md also PII, also tracked | _ops/state/OWNER-PROFILE-LOG.md | fix_now | Same as 496. |

### Neural / AI Integrity

| ID | Title | Evidence | Decision | Notes |
|---|---|---|---|---|
| 310 | protective_override is sole neural efferent and hard-immunized from learning | neural_driver.evaluate | fix_now | **ROOT CAUSE: Neural structurally unplugged.** |
| 214 | BCM sync-delete wipes all weights when latent_space empty | bcm.py:153 | fix_now | ROOT CAUSE of empty BCM. One-line fix. |
| 215 | organism.py never passes acquisition_data/doctor_archive to consolidation | organism.py:749 | fix_now | BCM has no data to learn from. |
| 513 | Learning write-only — memory written but never read by any decision | outcomes/ + memory/ | fix_now | Confirms 310. Dead-end storage. |
| 515 | Ledger missing = held-out pass — empty ledger silently passes verify | held_out_evaluator.py | fix_now | Fail-open: missing ledger = all clear. |

### Systemic / Time Safety

| ID | Title | Evidence | Decision | Notes |
|---|---|---|---|---|
| 311 | Circuit-breaker cooldown uses wall-clock — NTP step re-opens hot breaker | circuit_breaker.py | fix_now | Broken safety re-opens on clock jump. |
| 313 | All expiries use wall-clock — 214 time.time() in security paths | _ops/ | fix_now | TINV-5 violated. NTP jump = token bypass. |
| 267 | HLC without max-drift bound — c grows unbounded after backward clock | chrono.py | fix_now | Breaks causal ordering. |
| 14 | Governor LLM router broken 24h+ | debate/client.py:42-48 | fix_now | 22 fails. Budget allocation blind. |
| 15 | extract_json crashes on unclosed brace | debate/client.py | fix_now | Causes governor failure cascade. |
| 16 | Governor falls to dry mode | governor_epoch.py | fix_now | Budget allocation blind. |
| 95 | Circuit-breaker thrash: 3 restart/300s throttled | lead-naghshi logs | fix_now | Self-heal restart-looping. |
| 96 | Heart slept 19h/day until cap raised 288 to 2000 | cardiac-budget | fix_now | Config bug made system comatose. |
| 101 | Two bots polling simultaneously — 409 Conflict risk | BOTS-REGISTRY.md:100-108 | fix_now | Shared token. 409 causes callback loss. |
| 105 | cockpit_readmodel::redact() fail-open PII leak | cockpit_readmodel.py | fix_now | PII leak to Telegram. |
| 108 | HMAC callback_token 64-byte cap — real card lost 24h | callback_token.py | fix_now | 75 bytes caused 400, exception swallowed. |
| 198 | HTTP handler reads ORGANISM-STATE.json without lock | organism.py | fix_now | Race with writer. |
| 250 | action_hash fail-soft to '' — bind content silently dropped | approval_channel.py | fix_now | Fail-soft on hash = security bypass. |
| 309 | 3 bots token-sharing 409 risk, no runtime guard | BOTS-REGISTRY.md | fix_now | Token conflict causes callback loss. |
| 73 | organ_gate reserve/settle not transactional | organ_gate.py | fix_now | Crash = leaked budget. |

---

## P0 CLUSTERS (Root Causes)

### Cluster 1: Wall-Clock in Security Paths (items 135, 311, 313, 267)
214 instances of `time.time()` in security-sensitive paths. NTP backward jump validates expired tokens, re-opens circuit breakers, breaks HLC ordering.
**Fix:** Systematic migration to `time.monotonic()` or HLC.

### Cluster 2: Silent Exception Swallowing (items 53, 148, 314)
595 `except:pass` blocks, 56 in budget/neural, several in money verdict persistence. Corrupted state silently replaced with empty defaults.
**Fix:** Lint rule: `except` in `_ops/budget/` must alert. Replace bare `except:pass` with logging + fail-closed defaults.

### Cluster 3: PII Leak Vector (items 131, 132, 138, 496, 497)
Redaction is fail-open. Second PII layer silently disabled. autonomy_matrix bypasses nested fields. OWNER-PROFILE with real PII tracked in git.
**Fix:** One-line fix for fail-open (131). gitignore + git rm --cached for PII files. Expand autonomy_matrix to flatten nested fields.

### Cluster 4: Neural Unplugged (items 310, 214, 215, 513, 54)
The single efferent path from neural layer reads only fixed thresholds, never learned weights. BCM sync-deletes itself empty every cycle. No data flows in. Memory is written but never read.
**Fix:** Three wiring changes: (1) `if known:` guard in bcm.py:153, (2) pass acquisition_data in organism.py:749, (3) read BCM weights in neural_driver.evaluate.

### Cluster 5: Money State Machine Gaps (items 134, 136, 137, 191, 73)
APPROVING state can stick forever. Any transition is allowed. 409 consumer keeps eating. Mutual reversal cycle detection missing. Reserve/settle not atomic.
**Fix:** Transition whitelist. Timeout-reconciliation. Cooldown on 409. Cycle detection in reversal. Transactional reserve/settle.

### Cluster 6: Concurrency on Windows (items 71, 145, 315, 74)
O_CREAT|O_EXCL not atomic. 30s stale-lock break steals from slow writers. Hebbian/BCM shared across threads without locks.
**Fix:** Add locks per module. Increase stale-lock timeout or use named mutex on Windows.

---

## Missing Items (328-463)

The file `OCTOPUS-BLINDSPOTS-MASTER-BACKUP.md` (items 328-463, 136 items) was not found on disk. These items could not be triaged. If recovered, add to the JSONL and re-run classification.

---

## Recommended Fix Order (Next 48 Hours)

1. **Item 131** — redact() fail-open (1 line)
2. **Item 214** — BCM sync-delete guard (1 line)
3. **Item 496/497** — PII gitignore + git rm --cached (1 command)
4. **Item 515** — held-out fail-closed on empty ledger (1 line)
5. **Item 148** — _load_store fail-closed instead of {} (1 line)
6. **Item 316** — unify flag grammar to single opslib.flag() (1 helper)
7. **Item 14/15** — governor router extract_json fence-stripping (few lines)
8. **Item 134** — APPROVING timeout-reconciliation
9. **Item 136** — money state-machine transition whitelist
10. **Item 310** — plug BCM weights into neural_driver.evaluate (1 import + 1 read)
