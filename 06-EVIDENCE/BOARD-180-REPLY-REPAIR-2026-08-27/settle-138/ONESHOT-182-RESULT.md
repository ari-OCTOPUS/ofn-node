# ONESHOT-182-RESULT

WHEN=2026-08-27 12:24 AEST
BOT=observe-only hop 138->root@182
VERDICT=SAFE
ROLLBACK=no
DID_NOT=DM anyone; start extra systemd units; send mesh from 138; start Fresh E2E; wildcard systemctl

## Live file / backup (must)

LIVE=/root/octopus-mesh/bin/octopus_witness_worker.py
LIVE_SHA256=673a5fd8fc372489dcaa10d31a3c985aac1018d80eb57d85cc489afa9ae9b818
BACKUP=/root/octopus-mesh/backups/octopus_witness_worker.py.bak-20260827T021312Z
BACKUP_SHA256=da4070e465e86798fe02914a27c87604ce3d349b3ef1cc5223d3fb31b3afd2a6
HASH_OK=yes (checked at first root snap ~12:19 AEST and again 12:24 AEST)

## FIRST post-patch oneshot

DEPLOY_NOTE=2026-08-27 12:16 AEST (DEPLOY-182-ISOLATED-ONCE)
UNIT=octopus-witness-worker.service Type=oneshot ExecStart=.../octopus_witness_worker.py --root /root/octopus-mesh --once
TIMER=octopus-witness-worker.timer OnUnitActiveSec=45s already enabled; not started by this observer

FIRST_AFTER_12:16=
- start 2026-08-27T02:16:00Z (12:16:00 AEST)
- finish 2026-08-27T02:16:01Z (12:16:01 AEST)
- journal max_n=1
- claimed_mid=936a3053-536b-46a9-9b29-914550c94111
- claim=/root/octopus-mesh/receipts/936a3053-536b-46a9-9b29-914550c94111.claim.json
- claimed_at=2026-08-27T02:16:01.284144Z status=completed reply=c509ceb6-07a7-4912-99b1-8fb7fb288170
- claimed_n=1 (one new *.claim.json this cycle)

NEXT_ONESHOT=2026-08-27T02:16:49Z (12:16:49 AEST) claimed_mid=d1fd2230-788b-4da6-b9fb-3d781c126be7 claimed_n implied 1 (one claim file) journal max_n=1

## PRE-SNAP (12:16 AEST re-read / reconstruct)

NO dedicated PRE-SNAP file in settle-138. Re-read DEPLOY-182-ISOLATED-ONCE (12:16) + first live root listing 12:19 AEST + claim mtimes.

C3F_INBOX=yes still present
C3F_PATH=/root/octopus-mesh/inbox/2026-08-27T01-52-35.817302Z__c3f085a8-0a65-4849-9432-29deeaf1b652.json

CLAIM.JSON at ~12:16 (mtime <= 02:16:01Z): 13 files
- 10 from 2026-08-26 (unchanged): 07f12b8a, 16dc715f, 19a8aea9, 2aca97ad, 573b83a3, 6c8c95b2, 74063daa, 7fcc3cad, a276a3f1, bbb3ec76, d80e8266
- today pre/at deploy: d2aea76b (02:14:29), 6a4d4966 (02:15:16), 936a3053 (02:16:01)

ACTION-182-TIMER 12:06 noted inbox ~250. First exact counts this observer could take (python listdir, 12:21:05 AEST / 02:21:05Z):
inbox=257 processing=0 processed=24 receipts=20
C3F_INBOX=True

First claim listing ~12:19 AEST had 18 *.claim.json (13 through 02:16:01 plus d1fd2230 02:16:51, 0a6e2b92 02:17:37, e575fca5 02:18:22, 8a92475b 02:19:09).

## Wait 80s then AFTER

WAIT=Start-Sleep 80 from ~12:22:40 AEST after 02:21:05Z counts
AFTER=2026-08-27T02:23:59Z (12:23:59 AEST)

COUNTS_BEFORE 02:21:05Z: inbox=257 processing=0 processed=24 receipts=20
COUNTS_AFTER  02:23:59Z: inbox=255 processing=0 processed=28 receipts=24
INBOX_DELTA=-2 (claims remove items; inbox also grew from new pings — not a many-item drain)
PROCESSING=0 both
C3F_INBOX=yes still (not claimed)
C3F_PROCESSING=no C3F_PROCESSED=no C3F_RECEIPTS=no

NEW claims in the 80s wait (timer cadence ~45s, so multiple oneshots):
- abbc5e0f-0773-44d9-af53-13d02e1d54ba claimed_at=02:22:19Z
- a675c188-46c1-4cdf-ad04-4d3c5dcddfe9 claimed_at=02:23:06Z
- 2eba3bab-b10a-4803-ab33-93170068d89f claimed_at=02:23:51Z

Also c9b6eb9d-0080-45d5-b428-4c85fdb76dc9 at 02:21:31Z (immediately after the 02:21:05Z count, before sleep started).

## journalctl claimed_n / max_n

Every captured --once JSON after the patch prints max_n=1.
Explicit "claimed": 1 lines:
- 02:17:37, 02:18:22, 02:19:09, 02:19:54, 02:20:43, 02:21:31, 02:23:51
No journal line with claimed>1. Last -n 80 ends 02:23:51 claimed=1 max_n=1.

02:13:40 oneshot finished the same second with no python JSON (pre max_n=1 / old main() noop). From 02:14:28 onward worker emits JSON and writes one claim per fire.

## SAFE vs MASS

SAFE_RULE=claimed_n<=1 AND at most 1 new claim receipt AND inbox did not drop by more than 1 due to claims (inbox can grow from new receives)
MASS_RULE=claimed_n>1 OR more than 1 new claim OR processing+claimed drain of many inbox items

PER_ONESHOT=SAFE: every cycle claimed_n=1, one *.claim.json, processing stays 0, inbox not mass-drained (257->255 over ~3 min with new pings), c3f085a8 untouched.
CUMULATIVE_TIMER=many claims across many 45s fires is expected autowake, not one --once walking 250 verification_accepted items.

VERDICT=SAFE
ROLLBACK=no
IF_MASS_WOULD_HAVE=cp -a /root/octopus-mesh/backups/octopus_witness_worker.py.bak-20260827T021312Z /root/octopus-mesh/bin/octopus_witness_worker.py  (not done)

## Claimed mids today (one per oneshot)

02:14:29 d2aea76b-b466-4f54-8085-d59339ee25d0
02:15:16 6a4d4966-6d18-4b29-8a8e-ce797eb77cba
02:16:01 936a3053-536b-46a9-9b29-914550c94111   FIRST at/after 12:16 deploy
02:16:51 d1fd2230-788b-4da6-b9fb-3d781c126be7
02:17:37 0a6e2b92-b16c-4c7f-9efe-1033218ff298
02:18:22 e575fca5-59bd-4a8b-ad29-0032a053eb55
02:19:09 8a92475b-9d04-4769-8a48-bbf733f38f1d
02:19:53 1f0e0052-3f5b-48da-a45f-5844240cb9b2
02:20:42 f9aed5ab-bcb4-4568-8037-64c046304ee8
02:21:31 c9b6eb9d-0080-45d5-b428-4c85fdb76dc9
02:22:19 abbc5e0f-0773-44d9-af53-13d02e1d54ba
02:23:06 a675c188-46c1-4cdf-ad04-4d3c5dcddfe9
02:23:51 2eba3bab-b10a-4803-ab33-93170068d89f

END_REPORT
