---
type: report
status: done
tags: [memory, phase0, security, recon]
created: 2026-07-04
created_by: claude-cowork
---

# EXCLUDED — Phase 0 ignore-set + secret-scan (PATHS ONLY)

> هیچ محتوایی از این فایل‌ها خوانده/ذخیره نشده؛ فقط path. منبع قواعد: Phase 0a پرامپت + `.agentignore` + `.gitignore`.

## A) درخت‌های excluded (کل پوشه — فایل‌به‌فایل لیست نشده)

| مسیر | تعداد فایل | دلیل |
|---|---|---|
| `04 - Architect System/architect/_code/` | 4753 | `.agentignore: **/_code/` (شامل venv) |
| `_Duplicates/` | 303 | قرنطینهٔ dedup |
| `secrets-export/` | 14 | secret store — فقط برای password manager مالک |
| `.obsidian/` | 6 | تنظیمات اپ |
| `.claude/` | 4 | تنظیمات ایجنت |
| `.git/` | — | repo |
| `_Archive/` | **موجود نیست** ⚠️ | خلاف snapshot پاکسازی 2026-07-03 — ببین بخش Discrepancies در recon report |

## B) فایل‌های excluded با glob (case-insensitive)


### `glob:*key*` — 3 فایل

- `03 - Projects/Lead-نقاشی/کاریابی/MOVED - 05_راهنمای_API_keys.md`
- `03 - Projects/Lead-نقاشی/کاریابی/bot/harvesters/keywords.py`
- `03 - Projects/Mining/02 - Code/Ai bots/QuantumAlphaBot/check_keys.py`

### `glob:*secret*` — 5 فایل

- `03 - Projects/Ziman Galerry/control-brain/SECRETS.md`
- `03 - Projects/Ziman Galerry/control-brain/core/secrets.py`
- `03 - Projects/Ziman Galerry/control-brain/tests/test_secrets.py`
- `04 - Architect System/architect/01-Project/INGEST-EXCLUDED-SECRETS.md`
- `04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST.md`

### `glob:*wallet*` — 4 فایل

- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/wallet_tracker.py`
- `03 - Projects/Mining/02 - Code/Robo-data/robots/sentinel/wallet_tracker.py`
- `03 - Projects/Mining/03 - Rigs/Mining-1/Mining Q/MOVED - GUI Wallet.lnk.md`
- `03 - Projects/Mining/03 - Rigs/Mining-1/Mining Q/MOVED - monero wallet.txt.md`

### `glob:.env` — 2 فایل

- `03 - Projects/Lead-نقاشی/کاریابی/bot/.env`
- `03 - Projects/Ziman Galerry/control-brain/.env`

### `glob:.env.*` — 10 فایل

- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/60_code/.env.example`
- `03 - Projects/Lead-نقاشی/AiFarm-Lead/infra-control/.env.example`
- `03 - Projects/Lead-نقاشی/کاریابی/bot/.env.example`
- `03 - Projects/Mining/02 - Code/.env.example`
- `03 - Projects/Mining/02 - Code/Ai bots/QuantumAlphaBot/.env.example`
- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/.env.example`
- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/.env.template`
- `03 - Projects/Mining/02 - Code/Robo-data/.env.example`
- `03 - Projects/Mining/02 - Code/Robo-data/robots/sentinel/.env.example`
- `03 - Projects/Ziman Galerry/control-brain/.env.example`

### `glob:moved - *` — 6 فایل

- `03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/60_code/MOVED - .env.md`
- `03 - Projects/Mining/02 - Code/Ai bots/QuantumAlphaBot/MOVED - .env.md`
- `03 - Projects/Mining/02 - Code/Ai bots/sentinel/MOVED - .env.md`
- `03 - Projects/Mining/02 - Code/Robo-data/MOVED - .env.md`
- `03 - Projects/Mining/03 - Rigs/Mining-1/Hcash/MOVED - config.env.md`
- `04 - Architect System/architect/_meta/MOVED - pre-reorg-backup-2026-07-03.zip.md`


## C) Secret-scan hits (Phase 0b — الگوی regex، بدون خواندن کامل)

- `03 - Projects/Lead-نقاشی/Lead-نقاشی.md` — pattern: generic-assignment ⚠️ **یافتهٔ جدید — در ROTATION_CHECKLIST نیست؛ مالک بررسی کند**


## D) خارج از ingest scope (فقط شمارش — path-catalog در recon report)

فایل‌های غیر-Markdown طبق قاعدهٔ «ingest = فقط `*.md`» وارد حافظه نمی‌شوند:

- `.jpg`: 862
- `.py`: 175
- `.pdf`: 61
- `.txt`: 25
- `.json`: 21
- `.jpeg`: 20
- `.sh`: 16
- `(none)`: 15
- `.bat`: 15
- `.parquet`: 14
- `.js`: 11
- `.zip`: 10
- `.csv`: 10
- `.html`: 10
- `.yaml`: 8

_ابزار اسکن: python-regex (gitleaks در sandbox موجود نبود — توصیه: اجرای gitleaks از ویندوز قبل از Phase 1)._
