# 180 inbox leftover relocate 2026-08-27 ~12:31 AEST

PC GO bounded: relocate ONLY confirmed already_processed leftovers. No delete. No drain. No 180 DM. No second canary.

## Confirm
- Worker already_processed(mid, idem) = processed_index reply_acked or outbox.reply_acked
- FIRST_CLAIMABLE before: 2884079c-3b87-4648-b063-e1e4ee60622f task env=valid ap=True
- processed_index 2884079c: reply_acked=True ts=2026-08-27T01:52:17Z artifact_sha256=de1b6625...
- be612088 was NOT already_processed and stayed in inbox

## Move (1 file, not deleted)
- src inbox: 2026-08-27T01-51-27.727996Z__2884079c-3b87-4648-b063-e1e4ee60622f.json
- dest: /root/octopus-mesh/processed/archive-already-processed-20260827T0231Z/2026-08-27T01-51-27.727996Z__2884079c-3b87-4648-b063-e1e4ee60622f.json
- bytes: 1167

## After
- FIRST_CLAIMABLE: be612088-7154-45ea-a96b-0d777c7689ff run_id=fresh-e2e-canary-20260827B ap=False env=valid
- inbox left: 199 (was 200)
- 2884079c gone from inbox
- no other AP file was first; did not drain expired pings
- B OPEN. No PERSISTENT_GREEN. MANUAL_SESSIONS=0.