---
type: pair-note
lane: B-PULSE-IMAP
as_of: 2026-09-03T10:39:49Z
NOTHING_STARTED: yes
NOTHING_SENT: yes
ssh_this_session: none
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
scope: this_host_only
accounting: not_done
---

# نامهٔ بی‌تمبر و پستچی ۱۳۸

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: runtime
  evidence: 09-LANES/B-PULSE-IMAP/receipts/imap-pair-probe-20260903T103949Z.txt
```

این بدن لپ‌تاپ است، نه برد ۱۸۰. Wi-Fi = `192.168.0.191` (`hostname` + probe). ادعای «board 180» برای این سشن متوقف است. ۱۹۱ ≠ ۱۸۰.

کتاب‌ها ناقص‌اند — این برگه حساب نیست.

`imap_listener` اجرا نشد. IMAP وصل نشد. ایمیلی نرفت. فلگی روشن نشد. SSH تازه نبود؛ ستون ۱۳۸ فقط از رسید قبلی لین B است.

## 1. نامه روی میز (کد؛ اجرا نشد)

Source: static AST of `F:\ofn-node\ofn\agents\imap_listener.py` — probe `2026-09-03T10:39:49Z`. Did not `import` the module. Did not call `cycle()`.

| field | value | source |
|---|---|---|
| path | `F:\ofn-node\ofn\agents\imap_listener.py` | probe |
| bytes | 15875 | probe `listener_bytes` |
| git | **still `??` / untracked** | `git status --porcelain` + `git ls-files --error-unmatch` this session (`pathspec did not match`) |
| `cycle()` | present, line 281 | AST |
| `if __name__ == "__main__"` | present, line 345 — prints `cycle(dry=...)` once then exits | AST |
| host:port | `imap.gmail.com` **993** via `IMAP4_SSL` | AST one call, line 297 in source |
| bind/listen in file | **0** | AST |
| mailbox | `INBOX` | `select("INBOX")` + `_load_state` default `{"mailbox":"INBOX",...}` |

**mailbox یعنی چه:** نام پوشه روی سرور Gmail، نه صندوق محلی، نه bind روی این میزبان. `select("INBOX")` پوشه را باز می‌کند؛ `last_uid.json` همان نام را به‌عنوان مکان‌نما نگه می‌دارد.

ورودها (نقشه؛ اجرا نشد):

| symbol | role |
|---|---|
| `cycle(dry=False, limit=60)` | یک پولِ کلاینت IMAP، بعد `logout` |
| `__main__` | یک بار `cycle()`، JSON روی stdout، خروج |
| host:port | کلاینت به `imap.gmail.com:993` — نه گوش محلی ۱۴۳/۹۹۳ |

دستور پخت هم‌خانواده، هنوز بی‌تمبر:

| field | value | source |
|---|---|---|
| path | `F:\ofn-node\tools\install_systemd.sh` | probe |
| bytes | 1817 | probe |
| git | **`??` / untracked** | same git porcelain |
| unit type | `Type=oneshot` | file text |
| Exec | `mk_svc imap "python3 $AGENTS/imap_listener.py"` | file text |
| timer | `mk_timer imap "*:0/15"` | file text |
| env **name** | `OCTOPUS_WIRE_LEAD_OUTBOUND` present in template | name only; not enabled this session |

`ofn` HEAD این درخت: branch `fix/demand-harvest` · `34e63a04c5df4a948361f48b306e2a3f5188d42f` (probe). `[behind 2]` روی remote-tracking از قبل هست؛ این سشن fetch نکرد.

## 2. پستچی ۱۳۸ (رسید قبلی؛ SSH تازه نه)

Source: `SSH-RO-RECEIPT.md` as_of `2026-09-03T09:32:05Z` + `receipts/listen-138-20260903T0932Z.csv`. **FILE_VERIFIED** only.

| claim | value | claim_type |
|---|---|---|
| `octopus-imap.service` | inactive/dead **oneshot**; last `code=exited, status=0/SUCCESS` at `2026-09-03 09:30:34 UTC`; `Result=success` | FILE_VERIFIED (prior SSH) |
| `octopus-imap.timer` | active; last trigger `09:30:01 UTC`; next was `09:45:00 UTC` at that measurement | FILE_VERIFIED |
| 138 listen 143/993 | absent | FILE_VERIFIED (`ss -lnt`) |
| 138 dovecot/imap daemon | none in `ps` | FILE_VERIFIED |
| journal `-u octopus-imap` | unverified | prior: permission denied as `ari` |

فایل قدیمی‌تر لین B (`06-EVIDENCE/.../LANE-B-PULSE-IMAP-DIAGNOSIS-2026-09-03.md`): `IMAP_STATUS = RECOVERED`. با تعریف زنده‌ی SSH (oneshot + no 143/993) یکی نیست.

## 3. این میزبان — ۱۴۳/۹۹۳ و فرایند

Source: probe `2026-09-03T10:39:49Z` (`Get-NetTCPConnection -State Listen` ports 143,993 only).

| claim | value | claim_type |
|---|---|---|
| listen 143 | absent | runtime |
| listen 993 | absent | runtime |
| process matching `imap_listener.py` / `dovecot` / `imapd` | 0 | runtime |

رسید اول (`receipts/imap-pair-probe-20260903T103901Z.txt`) فیلتر گشاد داشت و PowerShell خودِ پروب را گرفت. فیلتر تنگ شد. عدد فرایند = رسید دوم.

غیبت LAN اینجا ≠ API روی loopback ۱۳۸ غایب است. دیسکِ یونیت ۱۳۸ روی ویندوز = `body_not_on_this_host`.

## 4. یک گونه یا دو جانور

**گونهٔ شغل یکسان است:** کلاینت Gmail، یک پول، خروج. نامه (`cycle()` + `__main__`) همان کاری را می‌کند که دستور پخت `Type=oneshot` و تایمر `*:0/15` برای پستچی می‌نویسد. پستچی ۱۳۸ همان کلاس است: oneshot last-success + timer، نه daemon روی ۱۴۳/۹۹۳.

**ادارهٔ پست نیست:** هیچ‌کدام سرور IMAP محلی نیستند. فایل نامه `bind`/`listen` ندارد (AST = 0). این میزبان ۱۴۳/۹۹۳ ندارد. ۱۳۸ هم در رسید قبلی ۱۴۳/۹۹۳ ندارد.

**بدن‌ها یکی نیستند:** نامه روی لپ‌تاپ هنوز `??` است و اینجا نصب نشده. پستچی روی ۱۳۸ مسلح است (FILE_VERIFIED). اینکه یونیت ۱۳۸ دقیقاً همین ۱۵۸۷۵ بایت را اجرا می‌کند = `unverified` (این سشن SSH نکرد، fetch نکرد).

۸⁷⁷x روی ۱۹۱ را با ۸⁷9x روی ۱۳۸ قاطی نکن.

## 5. تناقض‌های باز (`resolution: null`, `status: open`)

| موضوع | value_a | source_a | value_b | source_b | status |
|---|---|---|---|---|---|
| نام «IMAP listener» | «گوش» / هر ۱۵ دقیقه / DISCOVERY «Real and verified» | `imap_listener.py` docstring; `F:\ofn-node\docs\DISCOVERY.md` (also `??`) | کلاینت oneshot؛ `__main__` یک cycle بعد خروج؛ ۱۳۸ بدون ۱۴۳/۹۹۳ | AST probe; `SSH-RO-RECEIPT.md` | open |
| IMAP_STATUS | RECOVERED | `06-EVIDENCE/.../LANE-B-PULSE-IMAP-DIAGNOSIS-2026-09-03.md` | oneshot last-success; no daemon | prior B SSH | open |
| فایل دقیق روی ۱۳۸ | recipe points at `/home/ari/ofn/ofn/agents/imap_listener.py` | untracked `install_systemd.sh` | this exact 15875 B file | unverified | open |
| lane matrix | folder `09-LANES/B-PULSE-IMAP/` exists | this tree | `LANE-MATRIX.csv` still L0–L9 only | FILE_VERIFIED | open |

D `OFN-LOCAL-ARCHITECTURE.md` §2 همان جفت را خوانده (کلاینت ۹۹۳، نه سرور محلی). این لین آن را تکرار می‌کند با پروب و رسید تازه؛ فایل D دست نخورده.

## 6. انجام‌نشده (عمدی)

- No `imap_listener` start, no `--dry` run of the letter.
- No IMAP connect, no FETCH, no flags.
- No email / `auto_email`.
- No new SSH, no `systemctl`, no merge, no commit.
- No flag enable (`OCTOPUS_WIRE_*` name seen in recipe only).
- No accounting.

## Rollback

نادیده گرفتن یا انتقال `IMAP-UNTRACKED-VS-138.md`، `imap_pair_probe.py`، و `receipts/imap-pair-probe-20260903T1039*.txt` به `99-ARCHIVE/archive_B-PULSE-IMAP-IMAP-PAIR-20260903/`. نه `rm -rf`. سرویسی استارت نشد؛ روی ۱۳۸ چیزی نوشته نشد.
