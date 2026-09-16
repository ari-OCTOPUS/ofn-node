---
type: truth-note
section: ledger-vs-contradictions
created: 2026-08-20
updated: 2026-08-20
status: active
---

# لجر ژنوم ≠ دفتر تناقض‌ها

دو مسیر جدا. ثابت‌ماندن `ledger.jsonl.tip.json` شاهدِ «تناقض ثبت نشد» **نیست**.

| مسیر | فایل | چه کسی می‌نویسد | برای چه |
|---|---|---|---|
| دفتر تناقض | `01-TRUTH/CONTRADICTIONS.md` + نوت `06-EVIDENCE/C-0*.md` | ایجنت/مالک هنگام کشف | ادعای دو-مقداری، وضعیت OPEN/… |
| لجر ژنوم | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | `Ledger.append` از ارگانیسم/کد (`GENOME_CHANGE`, `HEARTBEAT`, …) | زنجیرهٔ رویدادهای ماشین |

ثبت C-043 / C-044 / C-045 / C-046 در دفتر تناقض **رخداد ژنوم نمی‌سازد**. هیچ hookای از `CONTRADICTIONS.md` به `ledger.append` در این درخت پیدا نشد (جستجوی 2026-08-20).

اگر مالک بخواهد این دو همگام شوند، آن یک تصمیم جدا است (رأی + کد). تا آن رأی، tip ثابت بعد از ثبت تناقض = رفتار مورد انتظار.

شاهد tip این جلسه: n=12765 · `3de325a6…` · ts 2026-08-20T01:49:44Z — پس از T1 (`B1_SIGNATURE_ATTACHED`) ارگانیسم heartbeat زد؛ ثبت تناقض‌های بعدی append نکرد.
