# COCKPIT_V2_M1_LIVE_RESULT

**STATUS: PASS**

Board: 138 DietPi 192.168.0.138 user ari
Lane: Cockpit V2 M1 15-minute soak (close only; M2 not started; mesh not sent)
Measured: 2026-08-27 11:48:54 AEST via `ssh -o BatchMode=yes ari@192.168.0.138`
ofn.service ActiveEnterTimestamp: Thu 2026-08-27 11:33:40 AEST
Soak elapsed: 15 min 14 sec (11:33:40 -> 11:48:54 AEST)

## Gate

| Check | Expected | Observed |
| --- | --- | --- |
| ofn.service | active | active |
| MainPID | 1351408 unchanged | 1351408 |
| NRestarts | 0 | 0 |
| HEAD | 6070f519b94de93b6cc94671d7fbfb7f0c8f2333 | 6070f519b94de93b6cc94671d7fbfb7f0c8f2333 |
| branch | ofn/cockpit-v2-20260827 | ofn/cockpit-v2-20260827 |
| listeners | 127.0.0.1:8791-8794 legs, :8796 bridge, :8895 hypno, :20241, 0.0.0.0:22; no new LAN | unchanged, no new LAN TCP |
| GET 127.0.0.1:8794/ | 200 | 200 |
| GET 127.0.0.1:8794/cockpit-v2/ | 200 | 200 (Cockpit V2 M1 HTML) |
| GET /api/v2/owner/status Host panel.master-painting.com | 401 | 401 `{"error": "unauthorised"}` |

## systemctl show ofn.service

```
MainPID=1351408
NRestarts=0
ActiveEnterTimestamp=Thu 2026-08-27 11:33:40 AEST
```

## TCP listeners (ss -lntup) — no drift

- 127.0.0.1:8791 python3 pid=1351408 (leg)
- 127.0.0.1:8792 python3 pid=1351408 (leg)
- 127.0.0.1:8793 python3 pid=1351408 (leg)
- 127.0.0.1:8794 python3 pid=1351408 (leg)
- 127.0.0.1:8796 python3 pid=589802 (bridge)
- 127.0.0.1:8895 python3 pid=672 (hypno)
- 127.0.0.1:20241
- 0.0.0.0:22 and [::]:22

No new 0.0.0.0 / LAN TCP listeners. Also present (unchanged class, not LAN service): UDP 0.0.0.0:68 DHCP client; UDP UNCONN ephemeral * high ports.

## HTTP

- `/` -> 200 (legacy owner panel HTML)
- `/cockpit-v2/` -> 200 title مرکز فرمان OFN, eyebrow `OFN · Cockpit V2 · M1`
- Host `panel.master-painting.com` `/api/v2/owner/status` -> 401 `{"error": "unauthorised"}`

## Untouched this close

No restart. No mesh send. M2 not started. ofn-backup / Telegram / Shopify / 180 not touched.

