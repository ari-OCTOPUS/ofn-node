# LANE-REPORT — B / Pulse-IMAP

Lane: **B-PULSE-IMAP**
As of: `2026-09-03T10:39:49Z` (imap pair probe) / prior SSH `2026-09-03T09:32:05Z` (FILE_VERIFIED only)

## خلاصه برای مالک

- نامهٔ محلی (`imap_listener.py`) هنوز **`??`** است — بی‌تمبر. پستچی ۱۳۸ همان **گونهٔ شغل** است (کلاینت Gmail، oneshot + تایمر)، نه ادارهٔ پست (۱۴۳/۹۹۳). مسیر: `IMAP-UNTRACKED-VS-138.md`
- این خانه: ۱۴۳/۹۹۳ خاموش؛ فرایند `imap_listener.py` / dovecot = 0.
- چیزی فرستاده نشد. listener روشن نشد. SSH تازه نبود.

## 1. What was done

- Identity: `DESKTOP-KA9RFN5` · Wi-Fi `192.168.0.191`. Claim «board 180» stopped. 191 ≠ 180.
- Read-only `git status` / `ls-files` in `F:\ofn-node`: `ofn/agents/imap_listener.py` and `tools/install_systemd.sh` still untracked.
- Static AST map of entrypoints (`cycle` / `__main__` / `imap.gmail.com:993` / mailbox=`INBOX`). Did not import or run the listener.
- Paired with prior `SSH-RO-RECEIPT.md` (138 oneshot+timer). No second SSH.
- Cheap re-check listen 143/993 only + tightened process filter.
- Wrote `imap_pair_probe.py`, ran twice (second receipt canonical after self-hit on wide filter), wrote `IMAP-UNTRACKED-VS-138.md`.
- Did not edit A files or C packet. Did not commit.

## 2. What remains

- Whether 138's oneshot executes **this exact** 15875 B file: `unverified` (no SSH this session, no fetch).
- 138 listen / unit state not re-measured (FILE_VERIFIED only).
- Journal on 138 as `ari` still blocked (prior receipt).
- `LANE-MATRIX.csv` still L0–L9 only while this folder exists — `status: open`.
- Naming clash «IMAP listener» vs oneshot client — both values kept, `status: open`.

## 3. What failed

- First process filter matched the probe's own PowerShell (string `imap_listener` inside the query). Tightened. Canonical count = 0 from second receipt.
- Nothing required for this increment failed after that.
- No standing IMAP listener 143/993 (reconfirmed cheap).

## 4. Evidence paths

| Claim | Value | Source | Status |
|---|---|---|---|
| this host IP | 192.168.0.191 | probe stdout | verified |
| ofn-node HEAD | `34e63a04c5df4a948361f48b306e2a3f5188d42f` on `fix/demand-harvest` | `git rev-parse` in `F:\ofn-node` | verified |
| listener tracked | untracked `??` | `git status --porcelain` + `ls-files` miss | verified |
| recipe tracked | untracked `??` | same | verified |
| imap host:port | `imap.gmail.com` 993 | AST of listener | verified (code) |
| cycle / `__main__` | lines 281 / 345 | AST | verified (code) |
| mailbox | `INBOX` (remote folder name) | AST select + state default | verified (code) |
| this host 143/993 | absent | `receipts/imap-pair-probe-20260903T103949Z.txt` | verified |
| this host imap process | 0 (tight filter) | same | verified |
| 138 oneshot+timer | last success `2026-09-03T09:30:34Z`; timer active | `SSH-RO-RECEIPT.md` | FILE_VERIFIED |
| 138 143/993 | absent | `receipts/listen-138-20260903T0932Z.csv` | FILE_VERIFIED |
| servers started | 0 | this session | verified |
| mail sent | 0 | this session | verified |
| SSH this session | none | this session | verified |

## 5. Rollback

نادیده گرفتن یا انتقال `IMAP-UNTRACKED-VS-138.md`، `imap_pair_probe.py`، و `receipts/imap-pair-probe-20260903T1039*.txt` به `99-ARCHIVE/archive_B-PULSE-IMAP-IMAP-PAIR-20260903/`. نه `rm -rf`. سرویسی استارت نشد؛ روی ۱۳۸ چیزی نوشته نشد.
