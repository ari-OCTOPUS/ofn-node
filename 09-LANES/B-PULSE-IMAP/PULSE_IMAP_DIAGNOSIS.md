---
type: lane-output
lane: B
as_of: 2026-09-03T09:32:05Z
vantage: two_hosts_compared
this_host_ip: 192.168.0.191
remote_ip: 192.168.0.138
claim_type: runtime
NOTHING_RESTARTED: yes
ssh_login: authenticated_readonly
---

# PULSE_IMAP_DIAGNOSIS — this host + SSH-RO 138

```
MISSING_PROCESSES (this host) = no process matching imap|mail_listener|dovecot
IMAP_STATUS (this host) = absent — no 143/993; no IMAP task
IMAP_STATUS (138 live SSH) = oneshot last-success 2026-09-03T09:30:34Z + timer active; 143/993 absent; no dovecot
IMAP_STATUS (138 prior file) = RECOVERED — FILE_VERIFIED only from 06-EVIDENCE/.../LANE-B-PULSE-IMAP-DIAGNOSIS-2026-09-03.md
HEARTBEAT_STATUS (138 live SSH) = octopus-heartbeat oneshot last-success 09:00:10Z + ofn-heartbeat.service active; --failed empty
HEARTBEAT_STATUS (files) = failed-until-#106 (prior Lane B) AND blocked pending #106 (CURRENT-TRUTH:171) AND self-healed after #106 (SEASON-LOG) — resolution: null, status: open
PORT_LISTENERS (this host) = 127.0.0.1:8771-8774,8776,8777,8791,20241
PORT_LISTENERS (138 live) = 127.0.0.1:8791-8794 (ofn.run), 8796 (octopus_bridge.run), 8895 (hypno.run), 20241; 0.0.0.0:22; 877x/143/993/8795 absent
TCP22_138 = True (reachability) then SSH authenticated
ROOT_CAUSE_RANKED = 1) two bodies: 191 organism 877x vs 138 ofn 879x  2) 8791 number collision (harvester vs ofn.run)  3) IMAP oneshot ≠ IMAP daemon
REMEDIATION_OPTIONS_AWAITING_OWNER = (a) keep maps split by node  (b) journal read for ari if logs wanted  (c) CURRENT-TRUTH heartbeat line vs live — owner_decision  (d) do not merge/restart from this lane
NOTHING_RESTARTED = yes
```

## مقایسه (ادغام نشود)

| claim | this host 191 | 138 live SSH | prior Lane B file | status |
|---|---|---|---|---|
| 8771-8776 | listening (8775 absent) | absent | connection-refused | open — two hosts |
| 8791 | harvester `--allow-no-auth` | `python3 -m ofn.run` | فارسی web | open |
| 8792-8796 | absent | 8792-8794+8796 present; 8795 absent | present 8791-8794,8796 | not evidence of 138 down |
| IMAP | no process | oneshot success; no 143/993 | RECOVERED | open — definition |
| heartbeat | body_not_on_this_host | oneshot success + ofn-heartbeat running | failed-until-#106 | open vs CURRENT-TRUTH |

Missing LAN ports on 191 are not evidence that 138 loopback APIs are absent. Disk absence of 138 units on this Windows vault = `body_not_on_this_host`.
