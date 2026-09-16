# 182 independent test oracle — evidence plan
Stamp: 2026-08-27 AEST
Writer: 182 only. Path: this folder. MUTATIONS on 180/138 = 0.

## Until a repair candidate exists
- Do not claim production task `30f60773` or probe `16fc28ed`.
- Do not write outcomes onto 180/138 production.
- Oracle + fixtures live only here. Verdict stays `unresolved`.

## Contract under test (from PC_WAVE0_PLAN)
PROCESS ONCE → FREEZE RESPONSE → DURABLE REPLY_PENDING → IDEMPOTENT TRANSMIT → ACK → INPUT_PROCESSED

States: CLAIMED → PROCESSING → RESPONSE_FROZEN → REPLY_PENDING → TRANSMITTING → REPLY_ACKED → INPUT_PROCESSED

Illegal: INPUT_PROCESSED before REPLY_ACKED. Model rerun after RESPONSE_FROZEN. New bytes on retry.

## Falsification cases (independent fixtures)
1. frozen_immutability — retry must emit same bytes/hash/idempotency key
2. ack_before_processed — processed flag cannot precede ACK
3. send_failure — after freeze, retry transmits frozen bytes
4. ack_lost — retransmit same key; no second process
5. sigkill_before_send — recover from REPLY_PENDING, no model rerun
6. sigkill_after_send — orphan scanner; ACK or retransmit, never reprocess
7. no_model_rerun_on_retry — model_calls stays 1
8. duplicate_receiver — second ACK/receive is no-op (no second effect)
9. orphan_recovery — processed-without-ACK is recovered, not re-modelled
10. start_limit_no_flap — crash loop must not flap unit (Restart/StartLimit)
11. no_listener_no_external — oracle opens no LAN socket, no HTTP, no TG

## After a candidate arrives
Run `oracle.py` against the candidate (diff/worktree or documented behavior).
Do not apply the candidate on 180. Verdict: confirmed | disputed | unresolved.

## Isolation
Write: this dir only.
Forbidden write: WAVE0/, pc-worker/, settle-138/, 180 disk, 138 disk, systemd.
