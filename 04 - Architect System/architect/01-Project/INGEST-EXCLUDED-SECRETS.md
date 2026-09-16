---
type: report
status: active
created: 2026-07-03
updated: 2026-07-03
tags: [security, ingest, stage-0]
---

# INGEST-EXCLUDED-SECRETS — گیت امنیتی Stage 0

> اسکن سورس‌های ingest (فقط مسیرها؛ **هیچ فایلی باز یا خوانده نشد** — تشخیص با الگوی نام فایل و `rg -l`).
> این فایل‌ها از ingest حذف شدند و تا پایان rotation نباید وارد vault شوند.

SOURCE_DIRS اسکن‌شده:
`C:\Users\Armin\Desktop\AI-armin` · `C:\Users\Armin\Desktop\AI-sume` · `C:\Users\Armin\Desktop\Mining` · `C:\Users\Armin\Desktop\ENV.rar` (فایل منفرد) · `backup\مغز دوم`

## A) فایل‌های credential-دار — SECRET-EXCLUDED

| مسیر (نسبت به Desktop) | وضعیت در ROTATION_CHECKLIST |
|---|---|
| `ENV.rar` | **ردیف جدید 20** — محتوای ناشناخته |
| `AI-armin/AGI-Personal/AIFarm-book/fusion-mvp/.env` | ردیف 4 (نسخه دوم) |
| `AI-armin/AGI-Personal/AIFarm-book/fusion-mvp/logs/igk_state/.kernel_key` | ردیف 17 (نسخه دوم) |
| `AI-sume/AGI-Personal/AIFarm-book/fusion-mvp/.env` | ردیف 4 (نسخه سوم) |
| `AI-sume/AGI-Personal/AIFarm-book/fusion-mvp/logs/igk_state/.kernel_key` | ردیف 17 (نسخه سوم) |
| `AI-sume/AGI-Personal/AIFarm-book/langar/.env` و `langar/env` | ردیف‌های 5–6 |
| `AI-sume/AGI-Personal/AIFarm-book/langar-pro/.env` | ردیف‌های 5، 9، 16 |
| `AI-sume/AGI-Personal/AiFarm-Lead/…/brushline/60_code/.env` | ردیف‌های 4، 6، 10 |
| `Mining/Robo-data/.env` | ردیف‌های 4، 7، 14، 15 |
| `Mining/Mining-1/Hcash/config.env` | ردیف 18 |
| `Mining/Mining-1/Mining Q/monero wallet.txt` | ردیف 1 (نسخه دسکتاپ) |
| `Mining/Mining-1/Hcash/info.rar` | **ردیف جدید 21** — آرشیو ناشناخته کنار کیف پول |
| `AI-sume/AGI-Personal/AIFarm-book/New Text Document.txt` | **ردیف جدید 22** — الگوی secret در محتوا |
| `AI-sume/AGI-Personal/AiFarm-Lead/infra-control/docker-compose.yml` | **ردیف جدید 23** — احتمال env مقداردار |

## B) نوت‌های دانشی با الگوی secret در محتوا — تا پاکسازی EXCLUDED

- `AI-sume/فیوژن هیپنوتیزم/PROJECT_EXPORT_COMPLETE.md` (ردیف 6 — توکن ربات؛ نسخه vault هم موجود است)
- `AI-sume/فیوژن هیپنوتیزم/00_Knowledge_Base/TODO.md` · `OpenQuestions.md` (ردیف 6)
- `AI-armin/AGI-Personal/AIFarm-book/personal Research/PROJECT_EXPORT_COMPLETE.md` (ردیف 6)

## C) کد با احتمال secret هاردکد — کلاً POINTER-class (کد وارد vault نمی‌شود)

- `Mining/Robo-data/scout_all_in_one.py` · `scout.py` (ردیف 4 — sk-ant هاردکد)
- `AI-sume/…/brushline/60_code/tests/test_phase2_leadpath.py` · `test_phase2_reviewslice.py` · `test_phase3_approval_queue.py` (احتمالاً کلید تستی — بازبینی در rotation ردیف 4)
- `Mining/Robo-data/robots/sentinel/wallet_tracker.py` (کد ردیاب است، credential نیست — LOW)

## D) قالب‌های بدون مقدار — LOW، صرفاً ثبت

`.env.example` در: Mining ریشه · Robo-data · sentinel · fusion-mvp (×2) · AIFarm-book · langar · langar-pro · brushline/60_code · infra-control

## نتیجه

- «مغز دوم» (داخل vault): هیچ hit ای نداشت.
- هیچ‌کدام از مسیرهای بالا در Stageهای بعدی خوانده یا ingest نمی‌شوند؛ برداشتن این محدودیت فقط بعد از ROTATED شدن ردیف مربوط.
