# 01-BOARD-PROBE-MATRIX — probe سه برد + لپ‌تاپ (همه فقط-خواندنی)

قاعدهٔ تفسیر: refused (curl exit 7 / TCP reset) = میزبان بالا، پورت بسته · timeout (exit 28) = فیلتر/فایروال — «مرده» نگو · ARP dynamic = دیده‌شده در L2.

## board-138 (192.168.0.138) — از داخل با ssh ari@192.168.0.138
| پورت | نتیجه | گوش‌دهنده |
|---|---|---|
| 8791 | 200 `{"ok": true}` | pid 2574033 `python3 -m ofn.run` — 127.0.0.1 |
| 8792 | 200 `{"ok": true}` | همان پروسه |
| 8793 | 200 `{"ok": true}` | همان پروسه |
| 8794 | 200 `{"ok": true}` | همان پروسه |
| **8796** | 200 `{"ok":true,"name":"octopus-bridge"}` | pid 589802 `python3 -m octopus_bridge.run` |
| 8801 | **refused** (exit 7) | هیچ |

**کشف ساختاری:** هر چهار «پا»ٔ 8791–8794 در واقع **یک پروسهٔ واحد `ofn.run`** روی چهار پورت loopback است — نه چهار سرویس مستقل. 8796 (پورت bridge) در هیچ سند قبلی ثبت نشده بود.

## board-180 (192.168.0.180) — از لپ‌تاپ (.191)
| Probe | خروجی | تفسیر |
|---|---|---|
| ping -n 2 | 0% loss، TTL=64، 43ms→1ms | UP |
| TCP-22 (Test-NetConnection) | **TcpTestSucceeded: True** | sshd فعال |
| curl :80 / :8791 / :8801 | exit 28 (timeout) | فیلتر — نه بسته، نه مرده |
| ssh با کلید octopus_mesh_ed25519 | `Permission denied (publickey,password)` | sshd جواب می‌دهد؛ احراز رد |
**وضعیت: UP_SSHD_AUTH_DENIED — داخل UNPROBED**

## board-182 (192.168.0.182) — از لپ‌تاپ (.191)
| Probe | خروجی | تفسیر |
|---|---|---|
| ping -n 2 | 0% loss، TTL=64، 2–13ms | UP |
| TCP-22 | **TcpTestSucceeded: True** | sshd فعال |
| curl :80 / :8791 / :8801 | exit 28 (timeout) | فیلتر |
| ssh با کلید mesh | `Permission denied (publickey)` | **password-auth هم بسته است** (سخت‌گیرانه‌تر از 180) |
**وضعیت: UP_SSHD_AUTH_DENIED — داخل UNPROBED**

## vantage دوم — از board-138
`ip neigh`: هر دو با MAC ثبت (STALE = اخیراً دیده‌شده). `~/.ssh/config` وجود ندارد؛ `/etc/hosts` بی‌ارجاع به بردها. `~/.ssh/`: authorized_keys، known_hosts، کلیدهای `octopus_138`، **`octopus_mesh_ed25519`**، `ofn_deploy` — کلید mesh هست ولی پذیرفته نشده روی 180/182.

## laptop (.191)
8801: هیچ گوش‌دهنده‌ای نیست — ادعای «CONTROL_URL:8801 روی لپ‌تاپ» از اسناد قدیمی **مرده** است.

اندازه‌گیری 2026-09-03 · FILES_I_MERGED=none
