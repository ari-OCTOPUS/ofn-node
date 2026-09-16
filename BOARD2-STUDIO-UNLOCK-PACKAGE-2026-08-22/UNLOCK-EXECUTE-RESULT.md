# Board2 Studio unlock EXECUTE — RESULT (2026-08-22)

**Result: FAIL** (gates unlocked + dry_run PASS; **one-item NOT queued**)

## What passed
- Step0: owner GO via ari ACK (partner_precondition=Saba/studio; secret_rotation risk accepted)
- Step1: `OFN_WIRE_OUTBOUND=1`; removed only `wire_outbound` from EXTRA; `OFN_KEEP_GATES_OPEN=1`
- Backup kept: `/home/ari/.config/ofn/node.env.bak-studio-unlock-20260822T123514Z`
- Step2: `ofn` active; legs `:8791-8794` healthz 200; wire_outbound open
- Step3 dry_run_diff: PASS — tenant=`studio`, platform=`telegram_channel`, media=`studio/shot-0001/0-1600.jpg`, draft=`unlock-shot-0001`, caption from existing media note `تست` (no invent)

## What failed
- Step3 enqueue: **queued=0**
- Exact rule: `consent:no_release` (subject=`self` declared on draft; **no** release document for `telegram_channel`)
- Outbox studio rows: none
- **Did not forge** a consent release

## Step4 schedule note (no fan-out)
Remaining `shot-0002`… library stays unqueued until owner records a real consent release covering `telegram_channel` for subject `self` (or equivalent), then re-ACK one-item enqueue.

## Rollback (ready)
1. Restore `/home/ari/.config/ofn/node.env` from `.bak-studio-unlock-20260822T123514Z`
2. `sudo systemctl restart ofn.service`
3. Prove wire_outbound closed again

## Machine JSON
See `UNLOCK-EXECUTE-RESULT.json` beside this note.