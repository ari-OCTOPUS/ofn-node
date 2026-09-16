---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [github-audit, security, org, ari-OCTOPUS]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
language: fa
---

# GITHUB AUDIT — حساب ari-OCTOPUS (2026-08-30، فقط-خواندنی)

```text
ACCOUNT=ari-OCTOPUS (Organization) · عضو: ari322
REPOS=3 (همه Private): ofn-node (Python) · langar (Python) · Armin (HTML)
PERSONAL_OWNED=0
METHOD=gh CLI 2.98.0 (device-flow auth، با اجازهٔ مالک) · همهٔ فراخوانی‌ها read-only
```

## ۱. جدول خلاصه

| repo | وضعیت | زبان | آخرین push | سلامت | نکتهٔ کلیدی |
|---|---|---|---|---|---|
| ofn-node | 🟢 فعال | Python | 2026-08-30 (امروز) | **8/10** | کانونیکال ناوگان؛ ۲۱۳۶ تست سبز؛ بدون CI/releases |
| langar | 🟢 فعال | Python | 2026-08-27 | **6/10** | ⚠️ فایل env با api_key واقعی کامیت شده |
| Armin | 🟡 نیمه‌فعال | HTML | 2026-08-27 | **3/10** | ۶ فایل idea-only؛ خودِ PR ممیزی‌اش می‌گوید «leg واقعی در ofn-node است» |

## ۲. گزارش تفصیلی

### ari-OCTOPUS/ofn-node — 8/10
مخزن کانونیکال ناوگان: کد OFN + vault + ۲۱ شاخه (شامل ۵ شاخهٔ حفاظتی `backup/*` و `archive/*` همین هفته). ‏HEAD main = `c1969bc` (بازگردانی ممیزی‌شدهٔ برد ۱۳۸). ‏**۵٬۴۹۴ فایل**، ‏README ✓، ‏بدون LICENSE، **بدون workflow CI**، ‏releases=0، ‏issues باز=0، ‏**۲ PR باز** (هر دو audit پری‌restore). اسکن امنیتی: صفر secret واقعی (تنها hit الگوی PRIVATE KEY یک **تستِ ضدنشت** است — ‏`assertNotIn`). ‏`SECRET-ROTATION.md` پاک است. ‏Dependabot خاموش. Debt: ‏۲ stale PR، ‏۲۱ شاخه (بعضی ۰۸-۱۶)، ‏mix محتوای شخصی vault با کد در یک repo.

### ari-OCTOPUS/langar — 6/10
اپ واقعی: بات تلگرام/چت (`langar/`) + بک‌اند FastAPI (`langar-pro/` با Dockerfile، postgres+pgvector، redis، requirements.txt). ‏README ✓ فارسی، ‏docker-compose unified + deploy.sh. **⚠️ HIGH: فایل `langar/env` کامیت شده با `api_key` واقعی (۷۵ کاراکتر) و ‏`BOT_TOKEN` (۲۸ کاراکتر)** — ظاهراً dump اشکال‌زدایی بوده. همچنین `POSTGRES_PASSWORD` با پیش‌فرض ۹-کاراکتری در compose. ‏۲ PR باز (audit‌های ۰۸-۲۸ که خودشان test-gap/dead-code گزارش کرده‌اند). بدون CI، بدون LICENSE، بدون release. Secret scanning + Dependabot خاموش.

### ari-OCTOPUS/Armin — 3/10
۶ فایل: یک HTML (heart-awareness-map) + یک پرامپت فارسی. عنوان PR ممیزی خودش: «idea-only repo، leg واقعی نقاشی در ofn-node است». بدون README، بدون LICENSE، بدون CI، ۲ PR باز (audit). کاندیدای آرشیو.

## ۳. اقدامات فوری (اولویت‌بندی)

| # | اولویت | اقدام |
|---|---|---|
| 1 | 🔴 HIGH | **چرخش کلید**: ‏`api_key` در `langar/env` لو رفته به تاریخچه repo (خصوصی، فقط شما دسترسی دارید — ولی hygiene حکم می‌کند rotate شود در کنسول سرویس‌دهنده) + ‏`git rm --cached langar/env` روی شاخهٔ chore (فایل روی دیسک بماند) + ‏`.gitignore` |
| 2 | 🟠 MED | فعال‌سازی **Secret Scanning + Push Protection + Dependabot** روی هر سه repo (Settings → Code security — یا با مجوز API با من) |
| 3 | 🟠 MED | حذف پسورد پیش‌فرض ۹-کاراکتری `POSTGRES_PASSWORD` از compose langar → env اجباری |
| 4 | 🟡 | قواعد/ruleset روی main (همان ۶ قاعدهٔ معلق) + ‏CI سادهٔ pytest برای ofn-node (۲۱۳۶ جمع) |
| 5 | 🟡 | تکلیف ۵ PR باز audit (۲ در langar، ‏۲ در Armin، ‏۲ در ofn-node — بستن بدون merge پیشنهاد می‌شود؛ شاخه‌ها می‌مانند) |
| 6 | ⚪ | ‏Armin → archive؛ ‏LICENSE برای langar/ofn در صورت intention عمومی؛ ‏README برای Armin |

## ۴. پیشنهاد آرشیو/ادغام/حذف

- **حذف: هیچ.** ‏**ادغام: Armin → اسنادش به ofn-node/docs منتقل و repo آرشیو شود.** ‏**آرشیو: langar اگر بات متوقف شد** (فعلاً فعال است — نگه داشتن).
- مخازن vault شخصی (Life OS) طبق حکم قبلی شما به گیت‌هاب نیامده‌اند — درست است؛ در bundleهای محلی + برد ۱۳۸ امن‌اند.

source: gh api read-only · raw: 06-EVIDENCE/GITHUB-AUDIT-20260830/raw/ · truth: MEASURED
