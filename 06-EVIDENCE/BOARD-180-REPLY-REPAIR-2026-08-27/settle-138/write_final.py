import os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"

watch = """# FRESH-E2E-WATCH be612088
run_id: fresh-e2e-canary-20260827B
watcher: 138 M4 Legs (readonly hop)
MANUAL_SESSIONS: 0
B: scored PASS
as_of_utc: 2026-08-27T02:46:35Z
as_of_aest: 2026-08-27 12:46:35 AEST

## Message IDs
- task (138->180): be612088-7154-45ea-a96b-0d777c7689ff
- 180 reply: 7ae7326a-d875-55ba-9287-300f6626ff69
- 138 ACK of 180 reply: 7ae7326a claim completed_no_reply (claimed_at 2026-08-27T02:32:19.808116Z)
- 138 auto-verify to 182: 04af67d5-d6c2-45ca-8826-bc11197021bb
- 182 reply: 577b0e22-0904-4ef7-b98b-72b491cb132f
- 138 ACK/settle of 182: 577b0e22 claim completed_no_reply (claimed_at 2026-08-27T02:45:41.363266Z); router_pass handler=cycle_settler seq 3708

## Timeline UTC / AEST (UTC+10)
- 2026-08-27T02:27:28Z (12:27:28 AEST): 138 sent task be612088 to 180
- 2026-08-27T02:27:27Z (12:27:27 AEST): 180 inbox accepted
- 2026-08-27T02:31:26Z (12:31:26 AEST): 180 froze prediction sha 0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829; created reply 7ae7326a
- first transmit failed injected_send_failure_once; retry_count=1; same frozen bytes
- 2026-08-27T02:32:16Z (12:32:16 AEST): 180 handed retry; 138 accepted reply
- 2026-08-27T02:32:19Z (12:32:19 AEST): 138 claimed+processed 180 result; cycle_settler seq 3407
- 2026-08-27T02:32:28Z (12:32:28 AEST): 138 auto-verify dispatched 04af67d5 to 182
- 2026-08-27T02:32:27Z (12:32:27 AEST): 182 accepted 04af67d5; later oneshots skipped_cap (max_n=1) while older valid verifies claimed 1/45s
- 2026-08-27T02:45:34Z (12:45:34 AEST): 182 AUTOCLAIM 04af67d5; reply 577b0e22 acked
- 2026-08-27T02:45:35Z (12:45:35 AEST): 138 accepted 182 witness_response
- 2026-08-27T02:45:41Z (12:45:41 AEST): 138 claimed+processed 577b0e22; cycle_settler seq 3708

## 180 inject / frozen bytes
- live outbox.py sha: 0e6dccfb6824e0da41c0a99014ee7b3709df9d9da29047e5387be183b12208ff
- inject_send_failure_once: true
- inject_send_failure_consumed: true
- last_error: injected_send_failure_once
- retry_count: 1
- frozen_prediction_sha256: 0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829 (prediction + meta + acked identical)
- response_sha256: 5ba5584916c96c2947532cf8a5eba278d5069adbc3a219c1633b0c95422f78bd
- MODEL_RERUNS=0: single prediction artifact 2026-08-27T02:31:26Z; no second model run during retry
- evidence 180: /root/octopus-mesh/state/replies/meta/be612088-7154-45ea-a96b-0d777c7689ff.json
- evidence 180: /root/octopus-mesh/state/replies/acked/efab5a3d773b93df01ca18329327b387f750b34ecd3cc0dbe90f0034f5e32deb.json
- evidence 180: /root/octopus-mesh/state/cognition/prediction-be612088-7154-45ea-a96b-0d777c7689ff.sha256
- evidence 180: /root/octopus-mesh/bin/octopus_reply_outbox.py

## 182
- witness timer stayed active; max_n=1; no extra units started; leftover relocate not done
- claim receipt: /root/octopus-mesh/receipts/04af67d5-d6c2-45ca-8826-bc11197021bb.claim.json status=completed reply_message_id=577b0e22-0904-4ef7-b98b-72b491cb132f
- outbox: /root/octopus-mesh/outbox/witness_response_04af67d5.json verdict=unresolved
- processed: /root/octopus-mesh/processed/04af67d5-d6c2-45ca-8826-bc11197021bb.json
- audit reply_acked 2026-08-27T02:45:34.610066Z

## 138
- processed task / 180 result / verify dispatch / 182 witness_response
- receipts: 7ae7326a.claim.json completed_no_reply; 577b0e22.claim.json completed_no_reply
- verify_dispatch_state be612088: verify_sent true origin 7ae7326a
- cycle_settler on both inbound results (seq 3407 result, seq 3708 witness_response)

## Constraints
- MANUAL_SESSIONS=0
- no second canary
- no unit start
- no inbox drain / no leftover relocate
- no PERSISTENT_GREEN
- no business / telegram / shopify / OF
- DUPLICATE_EFFECTS=0 (one 180 reply, one verify, one 182 reply)
- EXTERNAL_ACTIONS=0
"""

pt = """# FRESH-E2E-12POINT be612088
run_id: fresh-e2e-canary-20260827B
as_of_utc: 2026-08-27T02:46:35Z
as_of_aest: 2026-08-27 12:46:35 AEST
verdict: PASS

AUTOCLAIM_180: yes
AUTOREPLY_180: yes
AUTO_VERIFY_DISPATCH_138: yes
AUTOCLAIM_182: yes
AUTOREPLY_182: yes
AUTOSETTLE_138: yes
INJECT_SEND_FAILURE: yes
MODEL_RERUNS=0: yes
MANUAL_SESSIONS=0: yes
DUPLICATE_EFFECTS=0: yes
EXTERNAL_ACTIONS=0: yes
FROZEN_BYTES_MATCH: yes

## IDs
- task: be612088-7154-45ea-a96b-0d777c7689ff
- 180 reply: 7ae7326a-d875-55ba-9287-300f6626ff69
- 138 ACK (180): 7ae7326a claim completed_no_reply
- 182 verify: 04af67d5-d6c2-45ca-8826-bc11197021bb
- 182 reply: 577b0e22-0904-4ef7-b98b-72b491cb132f
- 138 ACK/settle (182): 577b0e22 claim completed_no_reply + cycle_settler seq 3708

## Why PASS
- 180 claimed be612088, froze bytes, first transmit failed injected_send_failure_once, retried same frozen_prediction_sha256 0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829 (retry_count=1, inject_send_failure_consumed=true, last_error=injected_send_failure_once). Single prediction file; MODEL_RERUNS=0.
- 180 reply 7ae7326a acked by 138; cycle_settler seq 3407.
- 138 auto-verify dispatched 04af67d5 (run verify-be612088-715).
- 182 auto-claimed 04af67d5 at 2026-08-27T02:45:34.181557Z after max_n=1 queue; replied 577b0e22; 138 accepted/claimed/processed and dispatched cycle_settler seq 3708.
- MANUAL_SESSIONS=0. No second canary. No unit start. No inbox drain. No PERSISTENT_GREEN. No external/business actions. One effect each hop.

## Evidence
- F:\\backup\\06-EVIDENCE\\BOARD-180-REPLY-REPAIR-2026-08-27\\settle-138\\FRESH-E2E-WATCH-be612088.md
- F:\\backup\\06-EVIDENCE\\BOARD-180-REPLY-REPAIR-2026-08-27\\settle-138\\FRESH-E2E-12POINT-be612088.md
- 180 meta: /root/octopus-mesh/state/replies/meta/be612088-7154-45ea-a96b-0d777c7689ff.json
- 180 acked: /root/octopus-mesh/state/replies/acked/efab5a3d773b93df01ca18329327b387f750b34ecd3cc0dbe90f0034f5e32deb.json
- 180 prediction sha: /root/octopus-mesh/state/cognition/prediction-be612088-7154-45ea-a96b-0d777c7689ff.sha256
- 180 outbox.py sha 0e6dccfb6824e0da41c0a99014ee7b3709df9d9da29047e5387be183b12208ff
- 182 claim: /root/octopus-mesh/receipts/04af67d5-d6c2-45ca-8826-bc11197021bb.claim.json
- 182 outbox: /root/octopus-mesh/outbox/witness_response_04af67d5.json
- 138 receipts: /home/ari/octopus-mesh/receipts/7ae7326a-d875-55ba-9287-300f6626ff69.claim.json
- 138 receipts: /home/ari/octopus-mesh/receipts/577b0e22-0904-4ef7-b98b-72b491cb132f.claim.json
- 138 processed: /home/ari/octopus-mesh/processed/577b0e22-0904-4ef7-b98b-72b491cb132f.json
- 138 audit seq 3407 cycle_settler (180 result) and seq 3708 cycle_settler (182 witness_response)
"""

for name, body in [
    ("FRESH-E2E-WATCH-be612088.md", watch),
    ("FRESH-E2E-12POINT-be612088.md", pt),
]:
    path = os.path.join(base, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print("wrote", path, os.path.getsize(path))