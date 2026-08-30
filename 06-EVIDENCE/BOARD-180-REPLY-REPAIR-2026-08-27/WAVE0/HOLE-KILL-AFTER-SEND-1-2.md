# Hole: kill-after-send re-transmits (1->2)
**logged:** 2026-08-27 11:32 AEST
**status:** OPEN — blocks live enable and Checkpoint A

Confirmed by:
- 182 on PC_worker 557b6b4: kill-after-send retry re-sends 1->2
- 180 on canonical octopus_reply_outbox.py: after fn(wire) succeeds, kill before on_acked() leaves REPLY_TRANSMITTING/RETRY_WAIT; retry_pending_this_activation calls fn(wire) again. No TRANSMIT_HANDED latch.

PC orders:
- 180: isolated latch + retest, no live-enable, no re-claim
- PC_worker: same latch in reference worktree only
- 138: HOLD, no PASS, no deploy, no live canary of unlatched transmit
- 182: wait for latch candidate, then falsify 1->1

Still WAIT_138_ACK for the current official result; that ACK alone does not close Checkpoint A.
