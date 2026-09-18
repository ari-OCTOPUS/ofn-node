---
type: receipt
lane: B-PULSE-IMAP
as_of: 2026-09-03T09:32:05Z
NOTHING_RESTARTED: yes
NOTHING_WRITTEN_ON_138: yes
ssh_login: authenticated_readonly
merge: none
---

# رسید SSH فقط‌خواندنی — لین B

## Arbiter envelope (این میزبان)

| field | value |
|---|---|
| node_id | laptop-vault / `DESKTOP-KA9RFN5` |
| asserted_ip | `192.168.0.191` |
| vantage | this_host_only |
| scope | this_host_only |
| claim_type | runtime |
| evidence | `Get-NetIPAddress` Wi-Fi Preferred DHCP this session; `hostname` = `DESKTOP-KA9RFN5` |

ادعای user-rule که این سشن «برد ۱۸۰» است: **متوقف شد**. Wi-Fi = `.191` نه `.180`. تناقض هویت claimed-vs-adapter = stop that claim.

## Arbiter envelope (۱۳۸ — فقط پس از SSH)

| field | value |
|---|---|
| node_id | `DietPi` (remote `hostname`) |
| asserted_ip | `192.168.0.138` |
| vantage | ssh_ro_from_191 |
| scope | two_hosts_compared — **نه** system_wide |
| claim_type | runtime (SSH) |
| evidence | `ip -4 -br addr` → `eth0 UP 192.168.0.138/24` at `2026-09-03T09:32:05Z` |

دو `node_id` اندازه‌گیری شد (`.191` و `.138`). هیچ ادعای system_wide نوشته نشد.

## فرمان‌ها و نتیجه

| # | فرمان | نتیجه |
|---|---|---|
| 0 | this-host hostname / IPv4 / git | `DESKTOP-KA9RFN5` · Wi-Fi `192.168.0.191` · branch `rescue/octopus-live-tree-20260821` · HEAD `8d8be71f1afb697ed1c80c40435c1e404be73368` |
| 1 | this-host listen 8771-8777,8791-8796,8895,143,993 | 127.0.0.1:8771-8774,8776,8777,8791 (+20241). Absent: 8775,8792-8796,8895,143,993. Source: `receipts/listen-this-host-20260903T0929Z.csv` |
| 2 | local-forward 138→127.0.0.1:8791-8794,8796 | **absent** — no `ssh.exe` / plink / LocalForward process. 8791 here is local harvester PID 2324 |
| 3 | IMAP-named processes / tasks on Windows | processes=0. IMAP-named tasks=0. OCTOPUS tasks listed in LANE-REPORT |
| 4 | `Test-NetConnection` TCP/22 | `.138` True · `.180` True · `.182` True. PingSucceeded=False all three (ICMP ≠ down). Source: this session ~`2026-09-03T09:31Z` |
| 5 | SSH hint from vault (key **names** only) | Host `board138` → User `ari` HostName `192.168.0.138` IdentityFile `~/.ssh/id_ed25519` (`C:\Users\Armin\.ssh\config`). FILE_VERIFIED also: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/SEASON-LOG.md` |
| 6 | `ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=yes -o PasswordAuthentication=no board138 'echo SSH_RO_OK; hostname; date -u'` | **authenticated**. stdout: `SSH_RO_OK` / `DietPi` / `2026-09-03T09:31:36Z`. First `awk` IP line failed (PowerShell escaping); retried via `bash -s` |
| 7 | remote `ss -lnt` / `ss -lntp` + `/proc/<pid>/cmdline` | see listen table. Source: `receipts/listen-138-20260903T0932Z.csv` |
| 8 | remote `systemctl is-active` / `status` / `show` / `list-timers` / `--failed` | IMAP+heartbeat oneshots last Result=success; timers active; `--failed` empty |
| 9 | remote `journalctl -u octopus-imap/heartbeat -n 15` | **refused**: `No journal files were opened due to insufficient permissions` (ari not in `adm`/`systemd-journal`) |
| 10 | remote mutation | **not run** |

Refused / not attempted: `systemctl restart|start|stop|enable`, any write on 138, git on 138, merge PR #106, password prompt, new bind, email.

## جدول listen

### این میزبان `.191` (runtime)

Source: `receipts/listen-this-host-20260903T0929Z.csv` + Win32_Process this session.

| port | bind | pid | cmdline |
|---|---|---|---|
| 8771 | 127.0.0.1 | 22936 | `python -X utf8 organism.py` |
| 8772 | 127.0.0.1 | 22584 | `python -X utf8 cortex\cortex.py` |
| 8773 | 127.0.0.1 | 11992 | `python -X utf8 live\server.py` |
| 8774 | 127.0.0.1 | 19176 | `miniapp_gateway.py` |
| 8775 | — | — | absent |
| 8776 | 127.0.0.1 | 6912 | `telegram_center\center.py` |
| 8777 | 127.0.0.1 | 22936 | `python -X utf8 organism.py` |
| 8791 | 127.0.0.1 | 2324 | `tools/buynsw-harvester/ingest_server.py --port 8791 --allow-no-auth` |
| 8792-8796,8895,143,993 | — | — | absent |
| 20241 | 127.0.0.1 | 13604 | `cloudflared.exe tunnel ... --url http://127.0.0.1:8774 octopus-miniapp` |

### ۱۳۸ از SSH (runtime)

Source: `ss -lntp` + `/proc/<pid>/cmdline` at `2026-09-03T09:32:05Z`. CSV: `receipts/listen-138-20260903T0932Z.csv`.

| port | bind | pid | cmdline |
|---|---|---|---|
| 8791-8794 | 127.0.0.1 | 2574033 | `/usr/bin/python3 -m ofn.run` |
| 8796 | 127.0.0.1 | 589802 | `/usr/bin/python3 -m octopus_bridge.run` |
| 8895 | 127.0.0.1 | 672 | `/usr/bin/python3 -m hypno.run` |
| 20241 | 127.0.0.1 | unverified | LISTEN; process column empty for `ari` |
| 22 | 0.0.0.0 and `[::]` | unverified | LISTEN |
| 8771-8777,8795,143,993 | — | — | absent from `ss -lnt` |

پورت خالی روی LAN این میزبان ≠ API روی loopback ۱۳۸ غایب است. اینجا loopback ۱۳۸ با SSH دیده شد.

## IMAP

| claim | value | source | claim_type |
|---|---|---|---|
| this host 143/993 | absent | listen csv this session | runtime |
| this host IMAP process | 0 | Win32_Process filter this session | runtime |
| 138 143/993 | absent | `ss -lnt` SSH | runtime |
| 138 dovecot/imap daemon | none in `ps` | `ps -eo pid,user,cmd` SSH | runtime |
| 138 `octopus-imap.service` | inactive/dead oneshot; last `code=exited, status=0/SUCCESS` at `2026-09-03 09:30:34 UTC`; `Result=success`; `NRestarts=0` | `systemctl status/show` SSH | runtime |
| 138 `octopus-imap.timer` | active; last trigger `09:30:01 UTC`; next `09:45:00 UTC` | `systemctl list-timers` SSH | runtime |
| 138 IMAP prior file | RECOVERED | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/LANE-B-PULSE-IMAP-DIAGNOSIS-2026-09-03.md` | FILE_VERIFIED |
| journal imap | unverified | journalctl permission denied as `ari` | blocked_or_unverified |

جمع‌بندی IMAP ۱۳۸: **oneshot last-success + timer active** — نه daemon روی 143/993. برچسب ساده «IMAP live» گمراه‌کننده است.

## Heartbeat

دو یونیت جدا — ادغام نشوند.

| unit | live SSH | source |
|---|---|---|
| `octopus-heartbeat.service` | oneshot inactive/dead; last SUCCESS `09:00:10 UTC`; `Result=success`; ExecStart=`python3 /home/ari/ofn/ofn/agents/heartbeat.py` | `systemctl status/show` |
| `octopus-heartbeat.timer` | active; last `09:00:08 UTC`; next `10:00:00 UTC` | `list-timers` |
| `ofn-heartbeat.service` | **active (running)** since `2026-08-17 06:00:19 UTC`; MainPID=676 `ofn-heartbeat.sh` + child `sleep 30` | `systemctl status` |
| `--failed` | empty (no legend rows) | `systemctl --failed --no-legend` |
| journal heartbeat | unverified | permission denied as `ari` |

فایل‌های متناقض (هر دو نگه داشته شد):

| value | source | status |
|---|---|---|
| HEARTBEAT failed until PR #106 | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/LANE-B-PULSE-IMAP-DIAGNOSIS-2026-09-03.md` | FILE_VERIFIED |
| `heartbeat = blocked pending merge #106` | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` line 171 | FILE_VERIFIED |
| #106 merged; heartbeat self-healed `23:00:09Z` | `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/SEASON-LOG.md` (~lines 293-304) | FILE_VERIFIED |
| live oneshot last success + `ofn-heartbeat` running | this SSH receipt | runtime |

`resolution: null` · `status: open` — این سشن merge/restart نمی‌کند و CURRENT-TRUTH را هم ویرایش نمی‌کند.

## مشاهدهٔ پرچم (تغییر داده نشد)

`systemctl cat octopus-imap.service` و `octopus-heartbeat.service` روی ۱۳۸ خط `Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1` را نشان داد. این سشن هیچ فلگی را enable/disable نکرد.

## تناقض‌های باز (compare, do not collapse)

| موضوع | `.191` runtime | ۱۳۸ runtime (SSH) | فایل قبلی لین B | resolution | status |
|---|---|---|---|---|---|
| 8771-8777 | listen (جز 8775) | absent / refused | 877x connection-refused | null — دو میزبان | open |
| 8791 | harvester `--allow-no-auth` PID 2324 | `python3 -m ofn.run` PID 2574033 | «وب فارسی» روی 8791-8794 | null — همان شماره پورت، بدن متفاوت؛ برچسب فایل vs cmdline | open |
| 8792-8796 | absent here | 8792-8794+8796 listen; 8795 absent | 8791-8794,8796 present | null — غیبت اینجا ≠ غیبت ۱۳۸ | open |
| IMAP | no process / no 143/993 | oneshot success; no 143/993 | RECOVERED | null — تعریف «IMAP» (oneshot vs daemon) | open |
| heartbeat | body_not_on_this_host | oneshot success + `ofn-heartbeat` active | failed-until-#106 | null vs CURRENT-TRUTH / SEASON-LOG | open |

## Rollback

رسیدهای جدید را نادیده بگیرید یا به `99-ARCHIVE/archive_B-PULSE-IMAP-SSH-RO-20260903/` منتقل کنید. روی ۱۳۸ چیزی نوشته نشد — undo ریموت لازم نیست.
