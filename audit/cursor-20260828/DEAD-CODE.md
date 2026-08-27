# DEAD-CODE

scan: 2026-08-27T23:03Z · not a deletion list · additive report only

## Confirmed unused or shadow (runtime)

| path | why dead | evidence |
|---|---|---|
| /opt/octopus/ofn-l4 | L4-GATE listen/run/systemd false, phase shadow_only | var/L4-GATE.json |
| /opt/octopus/lab/vault as git object | untracked generated notes | git status ?? vault/ |
| ari322/Armin | 2 files, no lead pipeline | git clone depth 1 file count=2 |
| ari322/langar | Python Telegram bot not a 180/138/182 unit | no langar.service on scanned nodes |
| painting_shadow_only path to customers | policy forbids treating as live | cognitive_policy.json |
| octopus-telegram-bridge.service | unit exists, ActiveState=inactive | systemctl show |
| 180 octopus-mesh as GitHub history | no .git | git rev-parse fails |
| F:\backup mirror | last_sync_result blocked | /opt/octopus/state/sync.json |

## Likely leftover (high confidence, not deleted)

- Multiple `octopus_cognitive_worker.py.bak-*` and reply_outbox bak on 180.
- 138 `octopus_scheduler.py.bak-*` and twophase copies beside live scheduler.
- MEGAPROMPT*.md ×15 plus .bak-vault/.bak-scan on README/HANDOFF/INDEX.
- 180 inbox ~1490 files, sample 385/400 ping — historical noise, not a second worker.
- 182 `*.CANDIDATE` next to witness/verifier/heartbeat.

## Do not call “dead” without two vantages

- 138 ofn packs lead/ziman/studio — **live files** in the running ofn.service tree; not proven unused.
- 182 sensorium stack — **running**; unused for *money*, not unused as process.
- hypno-fugu-mini — **running**; unused for OFN owner-approve, live for its own app.

No files deleted this audit.
