# 182 WITNESS_REPLY_REPAIR_RESULT (candidate review)
**received:** 2026-08-27 11:31 AEST
**pc_disposition:** VERDICT=unresolved accepted. Checkpoint A OPEN.

```text
PATCH_REF=180:REPLY_RETRY_REPAIR_180_RESULT hash e41e03e7... + forensic 31012b88... + PC_worker 557b6b48
TEST_ORACLE_INDEPENDENT=yes pc-worker fixtures 11/11 (not their 24); 180 official tests not adopted
ACK_BEFORE_PROCESSED=pc-worker PASS; 180 local_ack NOT 138 ACK; 138 reports none
RETRY_SAME_BYTES=pc-worker PASS
MODEL_RERUNS=pc-worker 1 on retry PASS
DUPLICATE_EFFECTS=receiver PASS; kill-after-send retry re-sends 1->2 (NOT idempotent transmit)
CRASH_RECOVERY=pc-worker PASS
START_LIMIT=pc-worker PASS
VERDICT=unresolved
MUTATIONS=0
STATUS=UNRESOLVED_WAIT_138_ACK official_180_live_enable=NO b4893759_absent claimed_not_verified_e2e
frozen_sha256=fd198dcf13b81fbc5d34e527b19ae890c7b8c8e05fed6495624fa76ec0908c56
END_RESULT
```

Hole to carry: PC_worker kill-after-send is not idempotent. Do not deploy 557b6b4 as-is.
