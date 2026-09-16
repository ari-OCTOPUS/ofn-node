---
type: read-and-plan
status: proposed-read-complete-implementation-blocked
tags: [telegram, c3, c4, polling, 409, 429, owner-order, wave1-locked, no-live-send, milestone-correction, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
audit_commit: d3013390d52aab2e61bd2578613aff7077f68742
inherited_code_commit: fa38d16cca944a80396ae1e1a16c547ab3122f78
branch_observed: equip/g10-cognition-20260816
head_observed: 53e527aef95c9bb30a3822e3ac278df59590e1d4
wave1_unlocked: false
live_send_authorized: false
webhook_authorized: false
restart_authorized: false
paid_calls_authorized: false
implementation_authorized_by_this_document: false
---

# OCTOPUS Milestone Correction — Telegram Read and Plan — 2026-08-21

## 0. Executive verdict

**No implementation, service restart, webhook mutation, manual `getUpdates`, or live Telegram output is authorized by this document.**

At archive commit `d301339`, C3 and C4 are **fixture-level scheduler components**, not a closed production path:

- C3 preserves a long `retry_after` for `sendMessage` only, and only when a queue is explicitly attached.
- C4 provides a durable metadata queue and a fake-transport `SenderBridge`, but the live Center imports neither.
- The queue stores hashes and timing metadata, not a recoverable Telegram request, so it cannot reconstruct a deferred delivery after restart.
- Most Bot API methods, including `editMessageText`, bypass C4 and call the transport directly.
- Polling converts successful-empty polls, 409, 429, malformed responses, and transport failures into the same observable return value, `[]`.
- The archive has a port mutex and a token-fingerprint file lock, but both contain fail-open paths. The file lock also mistakes a second process using the same constant `poller_id` for the existing holder.
- The Center can fall back to the same token used by `approval_channel`, while the startup lease is acquired only from `TG_CENTER_BOT_TOKEN`. In fallback mode the effective polling token is therefore not leased.
- The poll loop has no persistent error-specific scheduler. A 409 or a long poll-side 429 can immediately re-enter `getUpdates` and perpetuate the conflict/rate-limit loop.

**Required correction:** establish one fail-closed polling owner per token digest, one typed poll outcome, one durable offset owner, and one global Bot API admission/cooldown governor. Prove all behavior with fake transport and isolated state before any isolated Center restart is even proposed.

## 1. Authority and stop conditions

Authoritative owner record: [[02-DECISIONS/OWNER-ORDER-WAVE1-2026-08-21]].

The following constraints are treated as hard gates even where older or sidecar artifacts disagree:

1. Read → Plan → explicit gate/approval → atomic implementation commits.
2. `d301339` is the requested immutable audit object. It is not checked out or modified.
3. Wave 1 remains operationally locked for this work.
4. Live sender default is OFF; webhook default is OFF; paid calls are zero.
5. No live `sendMessage`, `editMessageText`, `answerCallbackQuery`, command/menu mutation, pin/delete, topic mutation, or other Bot API side effect.
6. No manual `getUpdates` probe. Read-only remote diagnosis, if separately authorized later, is limited to `getMe` and `getWebhookInfo`; this Plan performs neither.
7. `UNCERTAIN_SEND_OUTCOME` is never automatically resent.
8. Secrets are inventoried only by presence and one-way digest; token bytes never enter logs, evidence, queue rows, or this document.
9. Existing append-only evidence is not rewritten.
10. Any lease, state, queue, or offset ambiguity fails closed before network I/O.
11. This document does not authorize a Center restart. A future isolated restart requires its own gate after exact-head verification.

### Gate interpretation

`d301339` itself records:

- `confirmed=true`
- `verifier_independent=false`
- terminal state `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`

A later independent verdict exists at `bfbb03f`, but that later artifact does not change the bytes or gate state of `d301339`. Before implementation, the owner must ratify a new canonical target HEAD and state whether the later verifier applies to that exact target. Until then, **archive facts and later evidence remain separate layers**.

## 2. Evidence layers and reproducibility pins

### 2.1 Archive identity

- Audit commit: `d3013390d52aab2e61bd2578613aff7077f68742`
- Parent/inherited code commit: `fa38d16cca944a80396ae1e1a16c547ab3122f78`
- Commit subject explicitly scopes verification to `verifier_independent=false`.
- `d301339` changes evidence files only; the audited runtime blobs are inherited from `fa38d16`.

### 2.2 Byte pins for the audited blobs

| Archived object | Git blob | SHA-256 of file bytes |
|---|---|---|
| `_ops/telegram_center/center.py` | `4934be33371b3adfc86f1e86fbea31775ed6d913` | `07acf564baae4d58d9fcf96a1ddc6edc02798fcb9ad1b27c8dd7354352d71464` |
| `_ops/telegram_center/tg_api.py` | `4b766b4d7aeb0fa7fc7e4f4bffe9f8ff87d0e25b` | `9fb54883f42a173e4a9497e1f7ebb6aeab9d27c4102a174d88ea3e0c317382ea` |
| `_ops/telegram_center/tg_poller_lease.py` | `45b9d23e854ab3a3042e5dc5a7b9083ba0115029` | `d776683a65452775022843121b7370c59bbc43342fa00bed56340a76ffb13235` |
| `_ops/telegram_center/rate_limit_queue.py` | `10c2bb201b1dcab6ec6c3f4e2c218328f21c1eb3` | `2b706c0ecf9861d7de1c022c97eebf64deee1034119a1efb79258aab91bf71df` |
| `_ops/telegram_center/sender_bridge.py` | `3f03ca87123afb146be39777c4d2b696cd0b3fef` | `ad3c6ce0b41bf575561283f132593266f8a8ea5d589131e36a92025c9610bf6f` |
| `_ops/budget/approval_channel.py` | `6b62ab561e77f5d0148f0e118edbd4ee9c86b4f2` | `798789d2c8420774ead3a0b87602d26945135add959754975767db260f1aa67b` |
| `_ops/tests/test_security_c1_c4.py` | `9c21cf345acdd78baca74eb4c297b73130159aca` | `4e56d8c3ffce85477ca224252efe388d2700e2972886c58e73c7cd8fd9c79446` |
| `_ops/tests/test_tg_409_rival_poller.py` | `12683405216f91c942f46ec5379d7bcd35d165f0` | `2e7b6c80da8d36e3726e07ee751c3ec1d9dc122df15b6324a0e848f889cebb31` |

Reproduction form, without checkout:

```bash
git show d301339:<path>
git rev-parse d301339:<path>
```

### 2.3 Later observations: informative, not projected backward

Later evidence identifies bounded-file-read and DNS-resolution stalls:

- [[06-EVIDENCE/INCIDENT-CENTER-HANG-2026-08-21]]
- [[06-EVIDENCE/TELEGRAM-DEEP-DEBUG-2026-08-21/STATUS]]
- [[06-EVIDENCE/TELEGRAM-DEEP-DEBUG-2026-08-21/RESTART-CONTROLLED-2026-08-21]]

These support the proposed architecture, but are not claims about bytes already present at `d301339`.

A current-tree reproducibility defect must be resolved before selecting a target HEAD:

- `HEAD:_ops/telegram_center/tg_api.py` imports `poll_lease` in the poll-gate path (`tg_api.py:820-821`, `assert_poll_lease`) and again in the 409 circuit path (`tg_api.py:862`). The tracked runtime's conflict handling therefore depends on an untracked module.
- `HEAD:_ops/tests/test_poller_lease_20260821.py` imports `poll_lease`.
- `_ops/telegram_center/poll_lease.py` is absent from `HEAD` and exists only as an untracked working-tree file.
- `_ops/tests/test_poll_lease.py` is also untracked.
- Commit `2af9904` added only the lease test; it did not commit the implementation.
- Commit `ad42c43` added only Wave E tests; it did not attach C3/C4 to the Center.

Therefore no exact-HEAD stability claim may rely on those untracked bytes.

## 3. Archived topology at `d301339`

### 3.1 Polling paths

| Path | Token source | Calls `getUpdates` | Participates in shared lease | Archived risk |
|---|---|---:|---:|---|
| `telegram_center.TgClient` | prefers `TG_CENTER_BOT_TOKEN`, falls back to `TELEGRAM_BOT_TOKEN` | yes | only startup `tg_poller_lease`, and only when `TG_CENTER_BOT_TOKEN` exists | fallback can share approval token without lease |
| `budget.TelegramApprovalChannel` | `TELEGRAM_BOT_TOKEN` | yes | no | can conflict with Center fallback |
| legacy `4d_system/brain/telegram_bot.py` | shared env name | yes when opt-in enabled | no | latent second poller; guard must remain fail-closed |
| webhook delivery | remote Telegram configuration | mutually exclusive with polling | no local lease | Center does not fail closed on webhook presence |

### 3.2 Center loop

Archived flow:

```text
launcher loop
  -> localhost port mutex :8776
  -> Center/TgClient construction
  -> optional tg_poller_lease.acquire()
  -> run_forever()
       -> run_once()
            -> read center-config.json
            -> poll_updates(offset)
            -> dispatch each update
            -> write max(update_id)+1
       -> write pulse
       -> periodic beat
```

Relevant archived lines:

- `center.py:188-201` — direct config read; corruption/read failure becomes `{}`.
- `center.py:5880-5969` — poll/dispatch/offset flow.
- `center.py:6011-6017` — loop has no error-specific delay.
- `center.py:6065-6089` — localhost singleton socket.
- `center.py:6102-6129` — socket errors explicitly continue without the lock.
- `center.py:6148-6163` — poller lease acquisition is wrapped in broad fail-soft handling.
- `RUN-TG-CENTER.bat:12-19` — unconditional relaunch ten seconds after exit.

Port `8776` is a mutex port, **not a PID**. Process identity must use PID plus process-start/boot identity and code head.

## 4. C3/C4 implementation status

### 4.1 C3 — Telegram `retry_after`

| Capability | At `d301339` | Limit |
|---|---|---|
| Parse full positive `parameters.retry_after` | implemented | invalid/missing value becomes unknown |
| Short prohibition (`<=30s`) | synchronous sleep then one retry | blocks caller; not globally coordinated |
| Long prohibition (`>30s`) | offered to optional defer hook | `sendMessage` only |
| Durable queue adapter | `attach_defer_queue()` exists | Center never calls it |
| Poll-side long 429 | not durably scheduled | immediately returns `[]`; loop can re-poll immediately |
| Non-`sendMessage` Bot methods | no durable defer | edits, callbacks, pin/delete, topics, commands bypass queue |
| Cross-client/process cooldown | absent | approval client and other clients keep sending |

Archived citations: `tg_api.py:174-226`, `369-386`, `453-506`, `757-800`.

Specific defects:

1. `_defer_message_key()` hashes only method, chat ID, and text. It omits topic, keyboard, parse mode, stream, bot identity, and request version; distinct requests can collide.
2. `_default_defer()` stores a method-derived `chat_hash`, not the actual destination hash.
3. Its `payload_hash` hashes method plus retry duration, not the request payload.
4. A known 429 received inside `durable_loop.deliver()` becomes `None` at `_call_post()`, then becomes `UNCERTAIN_SEND_OUTCOME`; a known rejection is therefore misclassified as an uncertain transport result.
5. Poll 429 and delivery 429 do not share a persisted bot-level cooldown.
6. Failure streak and retry timing are per client instance and disappear on restart.

### 4.2 C4 — durable rate queue and sender bridge

Implemented in fixture/shadow form:

- SQLite WAL and `synchronous=FULL`.
- unique `message_key`.
- FIFO within priority.
- `retry_not_before` persistence.
- local policies: 1/s per chat, 20/min per group, 30/s nominal global.
- explicit `SENDING`, `CONFIRMED`, and `DLQ` states.
- uncertain post-attempt outcome can be quarantined.
- fake/injected `send_fn` bridge with one bounded pass.

Not implemented as a complete delivery system:

1. The module docstrings explicitly say no network capability and no live attachment.
2. Center has no `RateLimitQueue`, `SenderBridge`, or `attach_defer_queue` import/call.
3. The queue persists only `chat_hash` and `payload_hash`; no method, bot identity, destination, body, or reconstructable payload reference exists.
4. A deferred row therefore cannot be converted into a real request after restart.
5. `SENDING` rows are not automatically reconciled on startup; an explicit per-key call is required.
6. There is no atomic `claim_due` owner/generation lease. `due()` and `mark_delivery_attempt()` are separate operations.
7. The rate-event scope is only this queue, not all Bot API methods or clients.
8. `is_group` defaults false and cannot be recovered from a destination hash.
9. Wall-clock rollback is not handled.
10. Queue-full rejection has no global fail-closed transport guard; callers can still use direct transport paths.
11. `SenderBridge` counts a failed claim as `dlq` even though it does not transition the row to DLQ.
12. Jitter defaults to zero, and evidence does not prove deterministic backoff across restart.

Archived citations: `rate_limit_queue.py:25-53`, `58-102`, `104-181`, `183-215`; `sender_bridge.py:1-67`.

### 4.3 Existing fixture evidence and its boundary

`test_security_c1_c4.py` verifies:

- full long `retry_after` preservation;
- no early retry at `retry_after-1`;
- due at the boundary;
- duplicate-key behavior;
- queue depth/age bounds;
- local chat/group/global counters;
- fake bridge success/defer/uncertain behavior.

It does **not** prove:

- live Center attachment;
- request reconstruction after restart;
- one owner across processes/hosts;
- global admission for edits and maintenance methods;
- a typed poll error contract;
- fail-closed lease behavior;
- a real conflict-free soak;
- exact-HEAD reproducibility when runtime dependencies are untracked.

## 5. Diagnostic report — 409 Conflict

### 5.1 Root-cause classes

| ID | Trigger | Archived mechanism | Stability impact |
|---|---|---|---|
| `409-A` | Center fallback and approval poller use `TELEGRAM_BOT_TOKEN` | Center warns but still polls | two legitimate local consumers fight over one bot |
| `409-B` | fallback token is effective but startup lease reads only `TG_CENTER_BOT_TOKEN` | no token lease is acquired | conflict is not fenced before network |
| `409-C` | second process uses constant `poller_id="center-canonical"` | lease returns `already-holder` without comparing current PID | second process is admitted |
| `409-D` | simultaneous file-lock acquisition | losing `O_EXCL` raises; startup catches broadly | loser continues to poll without lease |
| `409-E` | socket bind/lease I/O error | explicit/broad fail-open branches | polling proceeds without ownership proof |
| `409-F` | PID reuse or stale identity | file record stores PID only; no boot ID, code head, generation, or TTL | stale/foreign owner can be mistaken for current owner |
| `409-G` | restart/watchdog overlap | launcher relaunches after 10s; no request drain contract | old and new long-polls may overlap |
| `409-H` | another checkout, state directory, device, or host | local socket/file locks are not global | external consumer is invisible locally |
| `409-I` | webhook configured | Center does not gate polling on read-only webhook status | polling cannot become healthy |
| `409-J` | manual diagnostic `getUpdates` | diagnostic itself becomes a second consumer | testing creates the incident |
| `409-K` | any observed 409 | client alerts hourly then immediately returns `[]` | same loop continues to contend |

### 5.2 Why process count plus a lease file is insufficient

- A process list is a snapshot, not token ownership proof.
- PID is reusable and does not identify a process incarnation.
- Port `8776` proves only that something owns a local port.
- A local file cannot fence a poller on another host.
- A TTL without a fencing generation cannot reject a stale owner after takeover.
- A fencing generation cannot cancel a request already inside DNS/HTTP; the transport must also be bounded and terminable.
- A lease checked only at process start cannot prevent later loss of ownership.

### 5.3 Required 409 behavior

1. Resolve the **effective** token first; never lease one token and poll another.
2. If dedicated Center token is absent, polling fails closed. No fallback polling.
3. Acquire/renew a per-token lease transactionally before every `getUpdates` attempt.
4. Lease/storage error means zero network.
5. One 409 is sufficient to open `DUPLICATE_CONSUMER`; do not wait for three conflicts.
6. Stop polling immediately, persist the circuit state, and use exponential cooldown with jitter.
7. Do not advance offset on 409.
8. Do not auto-delete a webhook. Record `WEBHOOK_PRESENT` and require owner action.
9. Do not issue manual `getUpdates` during diagnosis.
10. Reset the 409 streak only after a completed successful long-poll, including a valid empty result—not on lease refresh.

## 6. Diagnostic report — 429 Too Many Requests

### 6.1 Global logic gaps

| Gap | Archived behavior | Required behavior |
|---|---|---|
| no global choke point | every `_call_post` method can execute directly | every Bot API method passes one admission governor |
| `sendMessage`-only durable deferral | other methods are not queued/deferred | method-aware policies and shared bot cooldown |
| direct edit metabolism | `editMessageText` bypasses C4; source notes about 288 edits/day | count, coalesce, and defer edits globally |
| multiple clients | Center, approval channel, and other adapters own independent retry state | shared state keyed by token digest |
| synchronous retry | sleeps caller and retries once | persist `not_before`; scheduler owns retry |
| poll long 429 spin | no durable poll defer when `retry_after > 30` | poll scheduler honors full server prohibition |
| known rejection loses type | `_call_post` returns `None` | typed `RATE_LIMITED(retry_after)` result |
| no persistent streak/backoff | restart resets local state | persisted, reason-specific backoff |
| no recoverable deferred request | hashes only | sealed payload or deterministic payload reference |
| static nominal limits treated as truth | 30/s etc. local policy only | local safety margin; Telegram `retry_after` remains authoritative |

### 6.2 Required 429 behavior

- Persist the full server `retry_after`; never cap it.
- `not_before = max(existing_not_before, now + retry_after, computed_backoff)`.
- A valid 429 is a known rejection, so it may be safely deferred; it is not an uncertain send.
- A POST timeout/connection ambiguity after bytes may have left the host is `UNCERTAIN_SEND_OUTCOME` and is never auto-retried.
- Polling and all output methods share a bot-level cooldown, while per-chat/per-method windows remain separate.
- No direct fallback is permitted when the queue is full, locked, corrupt, or missing payload.
- Repeated identical edits for the same `(chat_id, message_id, payload_hash)` are TTL-suppressed; newer edits for the same target supersede older unattempted edits.
- `answerCallbackQuery` receives a high-priority lane but still obeys the server prohibition.

## 7. Target architecture

```text
Canonical launcher / one declared host
  -> EffectiveTokenResolver (dedicated token only; digest output only)
  -> PollOwnershipStore (SQLite transaction + TTL + boot identity + fencing generation)
  -> PollScheduler
       -> bounded/terminable Telegram transport
       -> typed PollOutcome
       -> OffsetStore (durable high-water after intent persistence)
       -> PollHealth

All Bot API calls
  -> TelegramTransportGovernor
       -> bot/method/chat TTL admission cache
       -> durable cooldown/backoff store
       -> durable delivery claim state
       -> injected fake transport in fixtures
       -> real transport unavailable unless a later owner gate enables it
```

### 7.1 Public typed outcomes

Preserve existing external methods initially, but add an internal result contract:

```python
PollOutcome(
    kind: Literal[
        "OK", "LEASE_DENIED", "CONFLICT", "RATE_LIMITED", "TIMEOUT",
        "DNS_ERROR", "HTTP_5XX", "HTTP_4XX", "MALFORMED", "STOPPED"
    ],
    updates: tuple[dict, ...] = (),
    retry_after_s: float | None = None,
    error_code: int | None = None,
    lease_generation: int | None = None,
    completed_at: float | None = None,
)
```

Compatibility rule: `TgClient.poll_updates()` may continue returning a list for old callers, but the canonical Center must use `poll_once_typed()` and must never infer health from `[]`.

### 7.2 Poll lease — byte/schema contract

Recommended SQLite row, keyed by the raw 32-byte SHA-256 token digest:

```sql
CREATE TABLE poll_lease (
  token_digest BLOB PRIMARY KEY CHECK(length(token_digest)=32),
  owner_instance BLOB NOT NULL CHECK(length(owner_instance)=16),
  owner_pid INTEGER NOT NULL,
  process_start_ns INTEGER NOT NULL,
  host_boot_digest BLOB NOT NULL CHECK(length(host_boot_digest)=32),
  code_head TEXT NOT NULL CHECK(length(code_head)=40),
  generation INTEGER NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('ACTIVE','DRAINING','OPEN','RELEASED')),
  acquired_wall_ms INTEGER NOT NULL,
  heartbeat_mono_ns INTEGER NOT NULL,
  lease_until_mono_ns INTEGER NOT NULL,
  request_deadline_mono_ns INTEGER NOT NULL DEFAULT 0,
  cooldown_until_wall_ms INTEGER NOT NULL DEFAULT 0,
  conflict_streak INTEGER NOT NULL DEFAULT 0,
  last_reason TEXT NOT NULL DEFAULT ''
);
```

Rules:

- `BEGIN IMMEDIATE` wraps acquire, renew, release, and takeover.
- New ownership increments `generation` atomically.
- Same-owner renewal requires exact `(owner_instance, PID, process_start, host_boot, generation)` match.
- A still-valid foreign owner returns `LEASE_DENIED` before URL construction/network.
- Database error or clock ambiguity returns `LEASE_DENIED`.
- Default lease TTL: 90 seconds for a 25-second poll plus hard transport margin.
- Renewal occurs immediately before request launch and after typed completion.
- Takeover is forbidden until both lease expiry and the prior `request_deadline` plus drain margin have passed.
- The bounded transport is terminated before release/takeover.
- The generation is checked again before committing an offset or health success.
- Wall time is for audit/cross-boot cooldown; same-boot TTL uses monotonic time plus host boot digest.

### 7.3 Global rate/cooldown cache

```sql
CREATE TABLE api_cooldown (
  token_digest BLOB NOT NULL CHECK(length(token_digest)=32),
  lane TEXT NOT NULL,
  scope_hash BLOB NOT NULL CHECK(length(scope_hash)=32),
  method TEXT NOT NULL,
  not_before_wall_ms INTEGER NOT NULL,
  not_before_mono_ns INTEGER NOT NULL,
  host_boot_digest BLOB NOT NULL CHECK(length(host_boot_digest)=32),
  failure_streak INTEGER NOT NULL DEFAULT 0,
  reason TEXT NOT NULL,
  updated_wall_ms INTEGER NOT NULL,
  PRIMARY KEY(token_digest,lane,scope_hash,method)
);
```

Admission must consult:

1. bot-global cooldown;
2. method/lane cooldown;
3. destination cooldown;
4. group window where applicable;
5. current queue depth and claim ownership.

All Bot API methods count, including edit, callback answer, pin/delete, topic/command maintenance, and `getFile`. Polling uses a receive lane but obeys bot-level 429 prohibition.

### 7.4 Delivery row and recoverability

```sql
CREATE TABLE delivery (
  message_key BLOB PRIMARY KEY CHECK(length(message_key)=32),
  token_digest BLOB NOT NULL CHECK(length(token_digest)=32),
  method TEXT NOT NULL,
  chat_hash BLOB NOT NULL CHECK(length(chat_hash)=32),
  payload_hash BLOB NOT NULL CHECK(length(payload_hash)=32),
  payload_version INTEGER NOT NULL,
  sealed_payload BLOB,
  payload_ref TEXT,
  priority INTEGER NOT NULL,
  state TEXT NOT NULL CHECK(state IN (
    'QUEUED','CLAIMED','ATTEMPTING','DEFERRED','CONFIRMED','UNCERTAIN','DLQ'
  )),
  business_attempts INTEGER NOT NULL DEFAULT 0,
  delivery_attempts INTEGER NOT NULL DEFAULT 0,
  created_wall_ms INTEGER NOT NULL,
  not_before_wall_ms INTEGER NOT NULL,
  claim_instance BLOB,
  claim_generation INTEGER,
  claim_until_mono_ns INTEGER,
  telegram_message_id INTEGER,
  error_code TEXT
);
```

A deferred request must be recoverable by exactly one of:

- a deterministic `payload_ref` to immutable render inputs; or
- a DPAPI/service-account-sealed request body with key ID/version outside Git.

Hashes alone are insufficient. If neither recovery method is available, transition to `DLQ/PAYLOAD_UNRECOVERABLE`; never call the transport with guessed content.

State taxonomy is explicit:

```text
AUTHORIZED -> CLAIMED -> ATTEMPTING -> DELIVERED(API-confirmed) -> OBSERVED(optional readback)
                                  \-> DEFERRED(known rejection)
                                  \-> UNCERTAIN(ambiguous attempt; no auto-resend)
                                  \-> DLQ(permanent/poison/unrecoverable)
```

### 7.5 Backoff contract

Inject clock and jitter in tests. Persist every deadline.

- 429: `delay >= retry_after`; use the maximum of the full server prohibition and local backoff.
- 409: first conflict opens circuit immediately. Equal-jitter exponential cooldown: base 5s, cap 300s.
- DNS/timeout/5xx/malformed poll response: decorrelated exponential backoff, base 1s, cap 60s.
- Permanent 4xx: no automatic retry unless explicitly classified idempotent/recoverable.
- Reset a lane’s failure streak only after a valid success in that same lane.
- Empty successful long-poll is success and resets poll failure streak.
- Lease refresh, process restart, and unrelated method success do not reset conflict/rate streaks.
- Clock rollback or corrupt deadline state fails closed.

## 8. Offset and ordering contract

The archive returns `{}` on config read failure and may restart from offset zero. The corrected design must not.

1. Store Telegram offset separately from presentation/config state.
2. Record schema, generation, checksum, `last_committed_update_id`, and `next_offset`.
3. On missing state at first installation, require an explicit bootstrap policy; do not silently infer zero in an established deployment.
4. On corrupt/unreadable state, use a verified last-known-good snapshot or stop polling.
5. Persist each accepted update’s durable intent or dead-letter record before advancing the high-water mark.
6. Advance monotonically to `max(update_id)+1` only after durable write/readback.
7. If offset write fails, stop before the next poll; deduplication remains a second defense, not the primary offset store.
8. A replayed `update_id` maps to the existing idempotency key and produces no second effect.
9. A poison update is durably dead-lettered so it cannot block later updates.
10. Lease generation must still be current when offset is committed.

## 9. Required edge/error behavior

| Condition | Required observable result |
|---|---|
| token absent | no lease row, no URL, no network, no output |
| dedicated Center token absent | poller refuses; no fallback to approval token |
| active foreign lease | `LEASE_DENIED`; zero network |
| lease DB locked/corrupt | fail closed; zero network |
| same PID reused after restart | boot/process-start mismatch denies stale identity |
| lease expires during request | terminate/drain transport; stale generation cannot commit offset |
| webhook URL present | `WEBHOOK_PRESENT`; no poll and no automatic delete |
| first 409 | circuit OPEN, offset unchanged, no immediate retry |
| valid empty poll | `OK`, progress timestamp advances, failure streak resets |
| short/long 429 | exact server delay persisted; no early retry |
| 429 without usable delay | exponential cooldown; no tight loop |
| 5xx/timeout on `getUpdates` | offset unchanged; bounded backoff |
| timeout/exception after write attempt | `UNCERTAIN`; never auto-resend |
| known 429 on write | `DEFERRED`, not `UNCERTAIN` |
| permanent 4xx | `DLQ` with bounded sanitized error |
| queue full | reject/alert; never bypass governor |
| duplicate message key | return existing state; one transport claim maximum |
| `SENDING/ATTEMPTING` found at boot | `UNCERTAIN`; no automatic due selection |
| payload unavailable after restart | `DLQ/PAYLOAD_UNRECOVERABLE` |
| repeated identical edit | TTL suppress/coalesce; no second call |
| newer unattempted edit to same target | supersede older edit deterministically |
| malformed offset/config | LKG or stop; never reset to zero silently |
| manual diagnostic asks for `getUpdates` | structural refusal |
| output mode is `BLOCK_ALL` | every side-effecting Bot API method is blocked and receipted locally |

## 10. Sequential implementation plan — no steps executed here

Every wave begins from a clean, declared target worktree; stages only its listed paths; and ends with a manifest, test receipt, no-secret scan, rollback command, and exact HEAD. Never use `git add -A`.

### G0 — Canonical release-candidate contract

**No code.** Owner/maintainer decision required.

- Choose one target HEAD derived from the audited archive and later accepted fixes.
- Amend stale `fa38d16/d301339` head references rather than silently replacing them.
- Require no untracked file in any runtime/import/test path.
- Generate `TEST-NODE-MAP.json` from actual registered node IDs; reconcile 151/163/202 counts.
- Record current Wave lock authority and later SIG-IV scope.
- Freeze source blob hashes and rollback base.

Exit: one canonical HEAD, clean execution paths, plan approved. Otherwise stop.

### W1 — Typed poll result and bounded transport

Candidate files:

- `_ops/telegram_center/tg_api.py`
- new `_ops/telegram_center/poll_outcome.py`
- bounded/terminable transport module selected from later candidate work
- focused tests only

Changes:

- add typed outcome without breaking legacy list-return API;
- distinguish empty success, 409, 429, DNS, timeout, 4xx/5xx, malformed;
- enforce hard request deadline and bounded worker/process count;
- remove sleeps from transport path; return scheduler instructions.

Fixture exit: zero network, 100 simulated DNS stalls, no unbounded thread/process growth, exact outcome assertions.

Rollback: revert W1 only; live Center remains untouched/default-off.

### W2 — Poll ownership TTL, boot identity, and fencing

Candidate files:

- tracked `_ops/telegram_center/poll_lease.py`
- `_ops/telegram_center/process_identity.py`
- `_ops/telegram_center/center.py` only through an approved WORKLOCK slice
- lease race tests

Changes:

- implement schema in §7.2;
- effective-token lease before every network attempt;
- fail closed on all lease errors;
- one 409 opens circuit;
- remove polling fallback to shared token;
- ensure release/drain and generation validation.

Fixture exit: 100 concurrent acquirers yield exactly one owner and zero network from losers; PID reuse, boot change, TTL boundary, clock rollback, DB lock, stale generation, and crash tests pass.

Rollback: revert W2; polling integration remains disabled.

### W3 — Durable offset/high-water owner

Candidate files:

- new `_ops/telegram_center/offset_store.py`
- minimal approved Center integration
- offset/replay/poison tests

Changes:

- separate offset from `center-config.json`;
- checksum/generation/LKG;
- durable-intent-before-offset ordering;
- fail closed on unreadable state or failed write;
- lease generation checked at commit.

Fixture exit: restart at every transition boundary produces no loss and no duplicate effect.

Rollback: revert W3 and restore pre-wave snapshot; no state migration deletion.

### W4 — Global Bot API governor and TTL cooldown cache

Candidate files:

- evolve `_ops/telegram_center/rate_limit_queue.py`
- new `_ops/telegram_center/transport_governor.py`
- `_ops/telegram_center/tg_api.py`
- approval/adapter seam only if canonical token policy requires it

Changes:

- implement cooldown/admission schema;
- route every Bot API method through one choke point;
- count and coalesce edits;
- persist full retry prohibition and exponential backoff;
- provide atomic claim operation;
- prohibit direct fallback on governor failure.

Fixture exit: mixed-method, multi-client, multi-process load never exceeds local policy; repeated 429 cannot spin; every method is visible in receipts.

Rollback: revert W4; transport remains `BLOCK_ALL`.

### W5 — C3/C4 delivery integration with recoverable payload

Candidate files:

- `_ops/telegram_center/rate_limit_queue.py`
- `_ops/telegram_center/sender_bridge.py`
- `_ops/telegram_center/durable_loop.py`
- payload protection/reference adapter
- no live Center attachment

Changes:

- unify durable-loop delivery truth with queue states;
- preserve known 429 as `DEFERRED`;
- atomically claim due work;
- add startup reconciliation of `ATTEMPTING` to `UNCERTAIN`;
- implement deterministic payload reference or sealed payload;
- preserve two historical uncertain rows without resend.

Fixture exit: restart at `retry_after-1` makes zero calls; at boundary makes one fake call; crash before attempt is recoverable; crash after attempt is uncertain and never resent; duplicate key produces one claim.

Rollback: revert W5; schema migrations must be forward-compatible and data-preserving.

### W6 — Eliminate rival poller and direct-call seams

Candidate scope:

- canonical launcher/task definitions;
- `approval_channel` startup policy;
- latent poller guards;
- static AST call-site test;
- read-only webhook preflight adapter.

Changes:

- one declared polling owner per token;
- approval path uses a distinct token or becomes a handler behind the canonical poller;
- legacy paths remain default-denied;
- static test rejects any new `getUpdates` or Bot API transport bypass;
- `getWebhookInfo` may report, never mutate.

Fixture/static exit: exactly one reachable poll entry point; no output side effect at import/boot.

Rollback: revert W6; no task/service restart performed.

### W7 — Full fixture battery and exact-head verifier kit

Required matrix:

- lease: first owner, N-way race, TTL−1/TTL, PID reuse, boot change, stale generation, DB lock/corruption;
- polling: empty success, update batch, 409, webhook present, 429 with/without delay, DNS stall, timeout, 5xx, malformed body;
- offset: missing bootstrap, corrupt state, failed write, replay, poison update, out-of-order IDs;
- governor: all methods, global/per-chat/group windows, edit coalescing, queue full, clock rollback;
- delivery: retry boundary, duplicate key, crash before/after attempt, missing payload, confirmed no-resend;
- invariants: token absent, `BLOCK_ALL`, zero live network, zero paid calls, isolated `OCTOPUS_STATE_DIR`;
- registration: registered = executed = passed; skipped/unexecuted reported separately.

Produce a manifest of exact source/test blobs. Builder terminal state remains `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`.

### G-SIG-IV — Independent exact-head verification

A separate identity/session reproduces W7 from a clean worktree with no untracked runtime dependencies. It must attest the exact candidate HEAD and side-effect hashes. Self-verification cannot open the next gate.

### G-RESTART-PRECHECK — separate owner decision

No restart request is valid unless all are true:

- canonical HEAD and source manifest match;
- exact-head independent verification passed;
- polling output mode is `BLOCK_ALL`;
- SenderBridge/live transport remains disabled;
- exactly one Center launcher and one intended Center process are inventoried;
- effective token has one lease owner/generation;
- no reachable rival poller shares the token;
- webhook status is known OFF without mutation;
- offset/LKG and queue snapshots verify;
- uncertain outcomes are quarantined and not due;
- kill switch and rollback snapshot are tested;
- no untracked runtime dependency;
- owner explicitly authorizes an **isolated Center restart**, not a system-wide restart.

### G-SOAK — polling-only stability proof after an authorized isolated restart

Initial acceptance window: 60 minutes, sample every 30 seconds.

Required SLO:

- one Center process and one launcher;
- one lease owner; generation stable except declared takeover;
- `poll_completed` age < 60 seconds;
- empty polls count as progress;
- 0 observed 409;
- 0 observed 429;
- 0 offset regression;
- 0 duplicate update effect;
- 0 live output methods, including edits and callback answers;
- 0 webhook mutation;
- 0 paid calls;
- 0 watchdog intervention;
- no worker/thread growth beyond declared bound;
- no config/offset fallback to zero;
- no unresolved lease or state error.

Any missing sample or ambiguous signal is failure, not success. Only an independent verifier may label `TELEGRAM_LOOP_BASELINE`; otherwise the status remains pending/failed-safe.

## 11. Acceptance semantics for “stable, conflict-free”

The phrase is reserved for evidence satisfying all of the following:

1. Ownership: one token digest, one current owner instance, one fencing generation.
2. Connectivity: completed long-polls continue even when there are no updates.
3. Conflict: no 409, no webhook, no rival entry point, no manual `getUpdates`.
4. Rate: all methods share admission; no 429; no early retry.
5. Durability: offset monotonic, queued prohibitions survive restart, uncertain sends remain quarantined.
6. Reproducibility: running bytes equal committed bytes; tests and manifests refer to the exact HEAD.
7. Safety: output is `BLOCK_ALL`, live sends/edits are zero, secrets are absent from artifacts.
8. Operations: bounded transport, bounded workers, tested drain/rollback, no restart storm.

A single process snapshot, a fresh pulse, a lease file, five green polls, or a passing fake-send test is insufficient on its own.

## 12. Explicit non-goals

- No live canary.
- No raw `sendMessage` test.
- No SenderBridge attachment to the live Center.
- No webhook activation, takeover, deletion, or migration.
- No system-wide daemon restart.
- No credential read, copy, rotation, or display.
- No paid/model call.
- No rewriting append-only evidence.
- No Wave 1 unlock/flip.
- No claim that later working-tree bytes were present at `d301339`.
- No claim that a local lease alone can fence an undeclared remote host; deployment authority must prohibit remote consumers, and any 409 fails closed.

## 13. Decisions required before implementation

1. Ratify the canonical implementation/evidence HEAD after `d301339`.
2. Decide the canonical polling owner and whether `approval_channel` uses a distinct bot or becomes handler-only.
3. Approve fail-closed removal of Center polling fallback to `TELEGRAM_BOT_TOKEN`.
4. Choose payload recovery: deterministic reference or DPAPI/service-account-sealed body.
5. Approve the exact local safety limits and priority classes; Telegram server prohibitions remain authoritative.
6. Confirm that output `BLOCK_ALL` includes edits, callback answers, command/menu setup, pin/delete, and topic mutation during the soak.
7. Resolve WORKLOCK ownership for `center.py` and `run_all.py` before touching either.
8. Decide whether a 60-minute clean soak is the promotion gate or only the first stage of a longer observation window.

## 14. Terminal state of this Read and Plan

```text
READ_COMPLETE
PLAN_WRITTEN
IMPLEMENTATION_NOT_STARTED
WAVE1_LOCKED
LIVE_OUTPUT_BLOCKED
WEBHOOK_BLOCKED
RESTART_BLOCKED
NEXT_GATE = OWNER_RATIFIES_CANONICAL_HEAD_AND_PLAN
```

This note is the only file created by this audit. It is a proposal and evidence map, not an activation artifact.
