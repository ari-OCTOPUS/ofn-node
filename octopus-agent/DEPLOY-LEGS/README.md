# DEPLOY-LEGS — revival + automation package for the OCTOPUS legs board (192.168.0.138)
Prepared by Sensorium agent 2026-08-17 (owner approved: watchdog + auto-ack rule +
three-node reporting). Deploy ONLY via owner-provided SSH. Nothing here touches
leg code (NBB-V5 authority stays on the board's own agent), TCB, or secrets.

## 1. Install watchdog (prevents another 13h silent window)
scp ofn-sync-watchdog.sh root@192.168.0.138:/usr/local/bin/
ssh root@192.168.0.138 "chmod +x /usr/local/bin/ofn-sync-watchdog.sh"
scp ofn-sync-watchdog.service ofn-sync-watchdog.timer root@192.168.0.138:/etc/systemd/system/
ssh root@192.168.0.138 "systemctl daemon-reload && systemctl enable --now ofn-sync-watchdog.timer && systemctl start ofn-sync-watchdog.service && tail -20 /var/log/ofn-sync-watchdog.log"
Expected first-run output: MOUNT GONE -> REMOUNTED ok (if mount was stale) and
ofn-heartbeat restarted. Heartbeat pushes resume within ~10 min to germline.

## 2. Catch-up ack (honest, one-time) for the 3 stuck commands
Per WIRE protocol outcomes must be honest. These were pulled by a manual test
(b003 note) before the bridge started, so the honest value is `unknown_outcome`.
Run ON THE BOARD (its agent or owner shell) using the board's own Bearer env:
  for id in 01a0096d-…aff0 01a009d1-… 01a00b85-…; do
    curl --cacert /etc/octopus-bridge/board-cp-ca.pem -X POST \
      https://192.168.0.191:8801/api/board-cp/ack \
      -H "Authorization: Bearer $(…from board's secure env…)" \
      -H 'Content-Type: application/json' \
      -d "{\"message_id\": \"$id\", \"outcome\": \"unknown_outcome\"}"
  done
(The board's agent knows its env layout — let IT run this; full message_ids in
FOR-BOARD-ACTION-NEEDED.md.)

## 3. Auto-ack RULE (recommendation for the board's own agent — code change is
its authority, propose-only for me): bridge must ack EVERY pulled command with
its honest outcome immediately after execution (succeeded/failed) or at pull
time (unknown_outcome) — never leave dispatches dangling. Add to bridge code
with a test; suggest mirror of this rule into ofn/wire as b005.

## 4. Wire reply b004 pending question (from FOR-BOARD-ACTION-NEEDED): answer
honestly per the board's reality — ack semantics = bridge's job (design intent),
execution outcomes = the 2h runs. The board's agent should append b004 to
ofn/wire via germline.

## Rollback
systemctl disable --now ofn-sync-watchdog.timer; rm /etc/systemd/system/ofn-sync-watchdog.{service,timer} /usr/local/bin/ofn-sync-watchdog.sh; umount not touched.

---
**WITHDRAWN 2026-08-18 — auto-ack rule proposal (P-ACK-1):**
The owner's verification doctrine (three-megaprompt design, 2026-08-18)
states: «هیچ فرمان dispatched را خودسرانه unknown_outcome نکن؛ فقط مالک
این وضعیت را می‌بندد» — no agent closes unknown_outcome; only the owner
does. The proposed auto-ack rule (>12h → unknown_outcome) contradicts this
and is WITHDRAWN. Replacement behavior: detection only — stale dispatched
commands are surfaced in reports for OWNER decision; nothing is closed
automatically. The 3 acks executed on 2026-08-17 were explicitly
owner-authorized and stand. `01a00d3d` remains owner-pending.
