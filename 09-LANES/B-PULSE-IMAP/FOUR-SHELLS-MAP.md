---
type: map
lane: B-PULSE-IMAP
as_of: 2026-09-03T10:22:37Z
NOTHING_STARTED: yes
ssh_this_session: none
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
scope: this_host_only
accounting: not_done
---

# چهار اتاق، یک راهرو — پلاک‌ها بدون باز کردن در

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: runtime
  evidence: 09-LANES/B-PULSE-IMAP/receipts/shells-listen-this-host-20260903T102237Z.txt
```

این بدن لپ‌تاپ است، نه برد ۱۸۰. Wi-Fi = `192.168.0.191` (`hostname` + probe). ادعای «board 180» برای این سشن متوقف است.

کتاب‌ها ناقص‌اند — این برگه حساب نیست.

`ofn.run` اجرا نشد. bind نشد. به ۱۳۸ وصل نشدیم. SSH جدید نبود؛ ستون ۱۳۸ فقط از رسید قبلی لین B است.

## 1. پلاک روی در (کد؛ اجرا نشد)

Source: `F:\ofn-node\ofn\run.py` + `F:\ofn-node\ofn\config.py` + `F:\ofn-node\ofn\adapters\http_api.py` — read-only، این سشن.

یک فرایند، چهار سوکت loopback. ماژول‌داک `run.py` خطوط 3–5: «One process, four sockets on loopback; the tunnel maps a hostname to each.»

| port | intended name | intended bind | HTML / extra | functions |
|---|---|---|---|---|
| 8791 | ziman | `127.0.0.1` | `ziman.html` | `config.load()` `ports["ziman"]=8791` (`config.py:283`); `load_web()` (`run.py:184–198`); `main()` serve loop (`run.py:593–600`); `serve()` default `host="127.0.0.1"` (`http_api.py:1863–1866`) |
| 8792 | lead | `127.0.0.1` | `lead.html` | same four functions; `ports["lead"]=8792` |
| 8793 | studio | `127.0.0.1` | `studio.html` + `/sabaapp` aliases (`run.py:203`) | same; `ports["studio"]=8793` |
| 8794 | owner | `127.0.0.1` | `panel.html` + `load_cockpit_v2()` merged on owner port (`run.py:591`) | same; `ports["owner"]=8794` |

`main()` `serve(api, port, static=...)` را بدون override هاست صدا می‌زند → bind قصدی همان پیش‌فرض loopback است. `config.load()` این چهار پورت را ثابت می‌گذارد؛ override محیطی `OFN_PORT*` در `config.py` دیده نشد (`Select-String` این سشن).

`print` بوت: `listening on 127.0.0.1: {sorted(set(cfg.ports.values()))}` — `run.py:600`.

## 2. چهار اتاق

Missing LAN listen on `.191` ≠ loopback absent on 138. ستون ۱۳۸ این سشن **runtime نیست**.

| port | intended (code) | this-host live 2026-09-03T10:22:37Z | 138 prior FILE_VERIFIED | claim_type |
|---|---|---|---|---|
| 8791 | ziman · `127.0.0.1` · `ofn.run` | **LISTEN** `127.0.0.1` pid **2324** `tools/buynsw-harvester/ingest_server.py --port 8791 --allow-no-auth` — **نه** `ofn.run`. LAN `.191:8791` absent | LISTEN `127.0.0.1` pid **2574033** `/usr/bin/python3 -m ofn.run` | this-host=`runtime`; 138=`FILE_VERIFIED` |
| 8792 | lead · `127.0.0.1` · `ofn.run` | absent (loopback + LAN) | same pid 2574033 `ofn.run` | this-host=`runtime`; 138=`FILE_VERIFIED` |
| 8793 | studio · `127.0.0.1` · `ofn.run` | absent (loopback + LAN) | same pid 2574033 `ofn.run` | this-host=`runtime`; 138=`FILE_VERIFIED` |
| 8794 | owner · `127.0.0.1` · `ofn.run` | absent (loopback + LAN) | same pid 2574033 `ofn.run` | this-host=`runtime`; 138=`FILE_VERIFIED` |

Sources:

| column | source |
|---|---|
| intended | §1 file reads |
| this-host | `receipts/shells-listen-this-host-20260903T102237Z.txt` (probe stdout) |
| 138 | `09-LANES/B-PULSE-IMAP/SSH-RO-RECEIPT.md` + `receipts/listen-138-20260903T0932Z.csv` as_of `2026-09-03T09:32:05Z` — **not re-SSH** |

`scope` همین سشن = `this_host_only`. دو `node_id` در *این* سشن اندازه‌گیری نشد → هیچ ادعای `system_wide` نیست.

## 3. پلاک یکسان، مستأجر فرق

| host | who holds 8791 | source | status |
|---|---|---|---|
| this house `.191` | harvester `ingest_server.py --allow-no-auth` pid 2324 | probe `2026-09-03T10:22:37Z` | runtime |
| 138 | `python3 -m ofn.run` (پلاک ziman) pid 2574033 | B SSH-RO `2026-09-03T09:32:05Z` | FILE_VERIFIED |
| `F:\ofn-node` tree | `ingest_server.py` absent | D `OFN-LOCAL-ARCHITECTURE.md` §3 `Test-Path` | FILE_VERIFIED (other lane) |

ادغام نشوند. همان شماره اتاق، دو بدن.

صبح همین لین (`receipts/listen-this-host-20260903T0929Z.csv`) هم 8791 را pid 2324 نشان داد — همان مستأجر هنوز اینجاست.

## 4. همسایه‌ها (ارزان؛ همین پروب)

| port | this-host 10:22:37Z | morning 09:29Z (`listen-this-host-20260903T0929Z.csv`) | 138 FILE_VERIFIED 09:32Z |
|---|---|---|---|
| 8795 | absent | absent | absent |
| 8796 | absent | absent | `127.0.0.1` pid 589802 `octopus_bridge.run` |
| 8771 | `127.0.0.1` pid 22936 `organism.py` | same pid 22936 | absent |
| 8772 | pid 22584 `cortex\cortex.py` | same | absent |
| 8773 | pid 11992 `live\server.py` | same | absent |
| 8774 | pid 19176 `miniapp_gateway.py` | same | absent |
| 8775 | absent | absent | absent |
| 8776 | pid **14092** `telegram_center\center.py` | pid **6912** same cmdline | absent |
| 8777 | pid 22936 `organism.py` | same | absent |
| 8895 | absent | absent | `127.0.0.1` pid 672 `hypno.run` |
| 143 / 993 | absent | absent | absent |

8776: دو pid، یک cmdline. `resolution: null` · `status: open` — ادغام به «همان فرایند» نشد.

## 5. تأیید منفی

| action | this session |
|---|---|
| `python -m ofn.run` / `ofn.run` start | not run |
| bind 8791–8794 / `0.0.0.0` | not done |
| SSH to 138 | not done (prior receipt reused) |
| client socket to 138 or to these ports | not done |
| flag / merge / send / fetch | not done |
| commit | not done |

## 6. تناقض باز

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| 8791 body | harvester pid 2324 | this-host probe | `ofn.run` pid 2574033 | B SSH-RO 138 | null — دو میزبان | open |
| 8792–8794 on this house | absent | this-host probe | intended + live on 138 | code + prior SSH | null — غیبت اینجا ≠ غیبت ۱۳۸ | open |
| lane id in matrix | B folder + `SCOPE.md` owns `09-LANES/B-PULSE-IMAP/` | this tree | `09-LANES/LANE-MATRIX.csv` is L0–L9 only | same csv | null | open |
| 8776 pid | 6912 | morning csv | 14092 | this probe | null | open |

## 7. Evidence / rollback

- probe: `09-LANES/B-PULSE-IMAP/shells_listen_probe.py`
- stdout: `09-LANES/B-PULSE-IMAP/receipts/shells-listen-this-host-20260903T102237Z.txt`
- 138 prior: `09-LANES/B-PULSE-IMAP/SSH-RO-RECEIPT.md`

Rollback: این سه را نادیده بگیرید یا به `99-ARCHIVE/archive_B-PULSE-IMAP-FOUR-SHELLS-20260903/` ببرید. نه `rm -rf`. سرویسی روشن نشد — undo ریموت لازم نیست.
