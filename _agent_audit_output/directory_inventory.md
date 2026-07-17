# موجودیِ دایرکتوری F:\backup — ممیزیِ 2026-07-16

> منبع: ممیزی‌های چند-ایجنتیِ جلسات 07-15/16 (۸+۷+۶ ایجنتِ فقط‌خواندنی) — نه اسکنِ سطحی.

## نمای کلی
vaultِ ابسیدینِ agent-first یک اپراتور (فارسی، سیدنی) + **ارگانیسمِ نرم‌افزاریِ زنده** + دو اختاپوس (_ops و PF).

## درختِ سطحِ بالا (خلاصه)
```
F:\backup
├─ 00 - Inbox            ← ورودی + AGENT_QUESTIONS.md (کانالِ رأیِ مالک)
├─ 01 - Dashboard        ← HANDOFF.md (ایندکسِ جلسه‌به‌جلسه) + Home
├─ 02 - Life OS · 03 - Projects (Lead-نقاشی/Ziman/Mining/Crypto/Accounting/اونلی‌فنز)
├─ 04 - Architect System ← اسکریپت‌ها + validators + watchdog
├─ 05..10                ← Agents/Maps/Knowledge/Assets/People/Telegram
├─ _ops                  ← ارگانیسم: organism/wiring/heart/cortex/doctor/legs/budget/tests(۱۴۰+)
├─ 4d_system             ← ارگانیسمِ پژوهشیِ مهروموم (MAP-Elites، خودجهش، نسل ۹)
├─ public/octopus-patches-2026-07-15  ← ۱۵ پچ + نقشه‌ها/گزارش‌ها
├─ _Archive / _Duplicates ← فقط مقصدِ انتقال (باز نکن)
└─ .env (gitignored) · .agentignore (مرزهای ماشین‌خوان) · .claude/worktrees
```

## دسته‌بندیِ فایل‌ها
- **کد:** `_ops/**`, `4d_system/**`, `03 - Projects/اونلی فنز/{langar,studio,brain}`, `04 - Architect System/scripts`
- **پرامپت:** `04 - Architect System/prompts/`, PF `prompts/`
- **کانفیگ:** `_ops/budget/budgets.yaml`, `OCTOPUS-flags.cmd` (پرچم‌های غیرمحرمانه), `langar_config.json`
- **حافظه/دیتابیس:** `_ops/state/**` (JSONهای اتمیک), `genome-system/ledger` (append-only), `brain/core.db`
- **مستندات:** PROJECT.mdها، MOCها، `public/octopus-patches-*/…`
- **لاگ:** `_ops/state/watchdog.log`, `governor-alerts.md`, `langar_log.jsonl`
- **حساس (مقدار هرگز خوانده/چاپ نمی‌شود):** `.env` (کلیدها)، `08 - Partner (PII)`، مسیرهای `.agentignore` — «یافت شد؛ امن‌سازی: gitignore + گاردِ PHI فعال است»

## نسخه‌ها/بکاپ‌ها
- worktreeهای `.claude/worktrees/*` = شاخه‌های کاریِ ایجنت (بزرگ‌ترین مصرفِ دیسک)
- برنچِ فعالِ کار: `claude/three-heartbeat-systems-523a74` (کامیت‌های f1e062d→c3e903f)
- درختِ زنده جلوتر از master است (پچ‌های staged) — merge = رأیِ مالک

## فایل‌های کلیدی برای خواندنِ عمیق
| فایل | نقش |
|---|---|
| `_ops/organism.py` | حلقهٔ حیات (tick ۳۰۰s، قفلِ 8771) |
| `_ops/wiring.py` | سیم‌کشیِ همهٔ beatها/پرچم‌ها |
| `_ops/heart/control_law.py` | قانونِ ضربان + ترمزِ σ |
| `_ops/cortex/model_router.py` | مغزA — سه‌رده، محلی-اول |
| `_ops/doctor/doctor.py` | دکترِ تکاملی (RFC propose-only) |
| `_ops/budget/capability_gate.py` | گیتِ پولِ fail-closed |
| `public/…/NEXT-10-PROGRAMS-2026-07-16.md` | نقشهٔ V2 |
