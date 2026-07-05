---
tags: [backlog, architect]
updated: 2026-07-04
---

# BACKLOG — اقدام‌ها به ترتیب اولویت (impact × effort)

> خروجی اولین اجرای [[PROMPT-B-test-improve]]. **آیتم‌های ۱–۱۰ در یک هفته قابل اجرا هستند.** Impact و Effort از ۱۰ (Effort کمتر = بهتر). Priority = Impact × (11−Effort).

## 🔥 هفتهٔ اول (۱–۱۰)

| # | اقدام | Impact | Effort | منبع |
|---|-------|--------|--------|-------|
| 1 | **Rotate همهٔ کلیدها/توکن‌های نشت‌کرده** (bot token، API keys)؛ حذف `.env`ها، `langar.db`، `langar.db-wal` از repo؛ `.gitignore` کامل؛ کلید age → off-box (password manager/USB) | 10 | 1 | G-01، red-team ضعف #2 |
| 2 | رفع باگ‌های deploy: افزودن `anthropic`/`openai` به `langar-pro/requirements.txt`؛ یکسان‌سازی pg15؛ رفع clone در `one-liner-vps-setup.sh` | 9 | 1 | G-02 |
| 3 | یکسان‌سازی سقف‌های بودجه طبق §۵ v2 (Normal/Growth) + گسترش `BudgetManager` به **همهٔ** callهای LLM + alert پلکانی ۵۰٪/۸۰٪ + halt خودکار در سقف ماهانه | 9 | 2 | G-06، red-team ضعف #1 |
| 4 | Wire کردن `BrainRouter` به مسیر پیام + نگاشت tier→model + فعال‌سازی prompt caching | 8 | 2 | G-05 |
| 5 | افزودن `@trace` به چهار span (model_call، tool_call، reasoning، handoff) — sink از قبل wire شده در `main.py` | 7 | 1 | G-08 |
| 6 | Call-site برای `HybridRetriever` در `/research` و سؤال روزانه | 7 | 1 | G-03 |
| 7 | چک kill-switch در هر round حلقهٔ `self_update` + قبل از هر commit؛ + mirror فایل `STOP` در langar (منبع حقیقت: flag DB) | 8 | 1 | red-team محور ۵، D-06 |
| 8 | ساخت جدول `action_policy(tenant_id, domain, max_amount, requires_approval, hard_stop)` + enforcement در مسیر فرمان bot | 8 | 2 | §۶ v2 (کد ندارد) |
| 9 | Step-up passphrase برای فرمان‌های APPROVE_FIRST (`/deploy`، `/kill`، `/budget growth`) + intent-router rule-based متن آزاد→فرمان | 8 | 2 | red-team محور ۲، S1 |
| 10 | بکاپ ساعتی off-box جداول حیاتی (rclone) + runbook restore + **یک restore واقعی تستی** | 9 | 2 | red-team S3 |

## 📋 بعد از هفتهٔ اول (v1-فاز)

| # | اقدام | Impact | Effort | منبع |
|---|-------|--------|--------|-------|
| 11 | `held_out.json` واقعی (۲۰+ فکت) + جایگزینی `score_prompt` کیواژه‌ای با eval غیرخودارجاع + گیت allowlist ساختار به‌جای denylist | 9 | 4 | G-04، G-15 |
| 12 | Anchor set ۵۰ case دستی + baseline eval + MLflow حداقلی | 8 | 3 | §۸ v2 |
| 13 | Adapter اول (Accounting): creds read-only جدا + `status/logs/report/audit` + ثبت در `projects.yaml` | 8 | 3 | G-11 |
| 14 | استقرار VPS: unified compose + ufw + Uptime Kuma/Dozzle + گزارش هفتگی هزینه در تلگرام | 8 | 3 | §۷ v2 |
| 15 | Producer برای Outcome تا ACE loop داده بگیرد (یا تصمیم صریح به حذف ACE به‌نفع حلقهٔ fusion — ثبت در DECISIONS) | 6 | 2 | G-03 |
| 16 | برچسب `origin` در memory + `<external_data>` در بازیابی | 7 | 2 | FM-3 |
| 17 | Circuit-break روی retry با arguments همسان (max 3) + validation روی tool results | 6 | 2 | FM-2، [[08-research-tool-interoperability]] |
| 18 | تصحیح نام‌گذاری «وزن» در قانون ۱۲ constitution کد (→ `agent_weights`) | 3 | 1 | G-24 |
| 19 | Verify قیمت Haiku 4.5 از منبع رسمی و ثبت در DECISIONS | 4 | 1 | G-23 |
| 20 | حذف یا استفادهٔ redis در compose | 3 | 1 | G-17 |
| 21 | `model_registry` (config/DB) + فرمان `/brain check` + proposal card تلگرام با APPROVE_FIRST+passphrase + canary/rollback | 7 | 3 | D-28، [[BRAIN-UPGRADE-LOOP]] |
| 22 | Pipeline ارزیابی مدل کاندید: anchor set روی Batch API + مقایسهٔ per-task + Δهزینه از trace واقعی (پیش‌نیاز: #11، #12) | 7 | 2 | D-28، [[BRAIN-UPGRADE-LOOP]] |
| 23 | راه‌اندازی سینک گوشی↔لپ‌تاپ (Obsidian Sync + exclusions: `_code/`، DBهای زنده، workspace) + حذف `.obsidian` تودرتوی architect — **فقط بعد از #1** | 6 | 1 | D-29، [[OBSIDIAN-SYNC]] |
| 24 | repo خصوصی `agent-outbox` + تابع `write_note` در بات + pull ساعتی لپ‌تاپ به `05-Agent-Outbox/` (همراه استقرار VPS، #14) | 6 | 2 | D-29، [[OBSIDIAN-SYNC]] |

## 🔭 v2-فاز (ترتیب در §۹ blueprint)

- LIVE اول حلقهٔ خودبهبودی با گیت سه‌شرطی + judge بین‌خانواده (پیش‌نیاز: #11، #12، ≥۵۰ trajectory — G-20)
- `GROUNDING_REQUIRED=True` + ActuationGate روی مسیرهای واقعی + OS-user جدا برای kernel (G-10)
- مهاجرت Postgres+pgvector+Mem0؛ DBOS journaling؛ hash-chain مالی/deploy؛ MCP gateway با trigger D-05؛ tenantهای بعدی؛ EU AI Act ops (G-19)؛ راه‌حل E2E تلگرام (G-18)

## قانون نگهداری

هر اجرای PROMPT-B: آیتم‌های انجام‌شده را ✅ بزن (حذف نکن)، آیتم‌های جدید را با منبع اضافه کن، اولویت‌ها را بازمحاسبه کن.

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
