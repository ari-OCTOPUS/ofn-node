import json, os
base = r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\settle-138"
watch = """# FRESH-E2E-WATCH be612088
run_id: fresh-e2e-canary-20260827B
message_id_task: be612088-7154-45ea-a96b-0d777c7689ff
watcher: 138 M4 Legs (readonly hop)
MANUAL_SESSIONS: 0
B: OPEN
poll_note: auto path only; no DM 180/182; no unit start; no inbox drain; no second canary; leftover relocate blocked

## Message IDs
- task (138->180): be612088-7154-45ea-a96b-0d777c7689ff
- 180 reply: 7ae7326a-d875-55ba-9287-300f6626ff69
- 138 ACK of 180 reply: lease/claim 7ae7326a (receipt completed_no_reply) + audit terminal_consumed_no_reply
- 138 auto-verify to 182: 04af67d5-d6c2-45ca-8826-bc11197021bb
- 182 reply: NOT YET
- 138 ACK of 182 / settle: NOT YET

## Timeline (UTC / AEST UTC+10)
- 2026-08-27T02:27:28Z (12:27:28 AEST): 138 sent task be612088 to 180; audit ack_received/sent
- 2026-08-27T02:27:27Z (12:27:27 AEST): 180 inbox accepted be612088
- 2026-08-27T02:31:26Z (12:31:26 AEST): 180 froze prediction sha 0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829; created reply 7ae7326a
- first transmit injected_send_failure_once; retry_count=1; same frozen sha
- 2026-08-27T02:32:16Z (12:32:16 AEST): 180 handed retry; 138 accepted reply
- 2026-08-27T02:32:19Z (12:32:19 AEST): 138 claimed+processed 180 result (completed_no_reply)
- 2026-08-27T02:32:28Z (12:32:28 AEST): 138 auto-verify dispatched 04af67d5 to 182; 182 accepted
- 2026-08-27T02:34:41Z (12:34:41 AEST): 182 oneshot claimed=1 max_n=1; 04af67d5 action=skipped_cap
- 2026-08-27T02:36:16Z (12:36:16 AEST): 04af67d5 still inbox pos 248/257; 12 valid verification_tasks ahead (parent); leftover relocate BLOCKED

## 180 inject / frozen bytes
- outbox.py sha: 0e6dccfb6824e0da41c0a99014ee7b3709df9d9da29047e5387be183b12208ff (live match)
- inject_send_failure_once: true
- inject_send_failure_consumed: true
- last_error: injected_send_failure_once
- retry_count: 1
- frozen_prediction_sha256: 0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829 (prediction file + meta + acked)
- response_sha256: 5ba5584916c96c2947532cf8a5eba278d5069adbc3a219c1633b0c95422f78bd (same on wire)
- model_rerun: not present as a second prediction; single prediction artifact at 02:31:26Z; MODEL_RERUNS=0
- evidence: /root/octopus-mesh/state/replies/meta/be612088-7154-45ea-a96b-0d777c7689ff.json
- evidence: /root/octopus-mesh/state/replies/acked/efab5a3d773b93df01ca18329327b387f750b34ecd3cc0dbe90f0034f5e32deb.json
- evidence: /root/octopus-mesh/state/cognition/prediction-be612088-7154-45ea-a96b-0d777c7689ff.sha256

## 182 watch
- witness timer active; WITNESS_ONCE_MAX default 1; do not raise max_n
- 04af67d5 still unclaimed in inbox
- leftover c3f085a8 still present (prior run); ignored
- do not drain inbox; do not relocate leftovers (blocked)

## Constraints observed
- MANUAL_SESSIONS=0 (no Grok DM / SendToAgent 180 or 182)
- no second canary
- no unit start
- no PERSISTENT_GREEN
- no business / telegram / shopify / OF
"""
p = os.path.join(base, "FRESH-E2E-WATCH-be612088.md")
with open(p, "w", encoding="utf-8", newline="\n") as f:
    f.write(watch)
print("wrote", p, os.path.getsize(p))

pt = """# FRESH-E2E-12POINT be612088
run_id: fresh-e2e-canary-20260827B
as_of_utc: 2026-08-27T02:36:16Z
as_of_aest: 2026-08-27 12:36:16 AEST
verdict: OPEN (waiting AUTOCLAIM_182 / AUTOREPLY_182 / AUTOSETTLE_138)

AUTOCLAIM_180: yes
AUTOREPLY_180: yes
AUTO_VERIFY_DISPATCH_138: yes
AUTOCLAIM_182: no
AUTOREPLY_182: no
AUTOSETTLE_138: no
INJECT_SEND_FAILURE: yes
MODEL_RERUNS=0: yes
MANUAL_SESSIONS=0: yes
DUPLICATE_EFFECTS=0: yes
EXTERNAL_ACTIONS=0: yes
FROZEN_BYTES_MATCH: yes

## Why open
- 180 inject fail-then-retry observed: inject_send_failure_consumed=true, last_error=injected_send_failure_once, retry_count=1, frozen_prediction_sha256=0e2612128dc5b5ba93c235b954c9579b6e384ffa950c29b0d8a1c9817379a829 identical on prediction + reply meta + acked.
- 138 auto-verified: 04af67d5-d6c2-45ca-8826-bc11197021bb sent to 182 (verify-be612088-715).
- 182 timer claims max_n=1. Last oneshot skipped_cap on 04af67d5. 12 valid unprocessed verification_tasks sit ahead. Leftover relocate BLOCKED. Watching auto-claim only.

## IDs
- task: be612088-7154-45ea-a96b-0d777c7689ff
- 180 reply: 7ae7326a-d875-55ba-9287-300f6626ff69
- 138 ACK: 7ae7326a claim completed_no_reply
- 182 verify: 04af67d5-d6c2-45ca-8826-bc11197021bb
- 182 reply: pending
"""
p2 = os.path.join(base, "FRESH-E2E-12POINT-be612088.md")
with open(p2, "w", encoding="utf-8", newline="\n") as f:
    f.write(pt)
print("wrote", p2, os.path.getsize(p2))