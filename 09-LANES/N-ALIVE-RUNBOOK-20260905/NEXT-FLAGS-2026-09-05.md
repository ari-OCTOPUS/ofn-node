---
type: owner-decision
status: decided
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# فلگ‌های بعدی — پیدا شد، هنوز باز نشده

مالک: «انجام بده بپرس و فلگ‌های بعدی هم پیدا کن باز کنیم»

## جواب‌ها و اجرا

| سؤال | جواب | اجرا |
|---|---|---|
| ری‌لود | `organism_306` | **مسدود** — `ORGANISM-306-BLOCKED.md` · STOP نوشته نشد |
| صفر فایل | `FUGU_VIA_CENTRAL_GATE=1` | شد · رسید ۲ |
| ۱۳۸ | `memory_138` | فقط حکم · SSH نه |

ریستارت این نوبت **انجام نشد**. اسکریپت رسمی و `opslib.py` روی دیسک نیست. PID را نکشتم.

## سه پروسس زنده (همین جلسه)

| پروسس | PID | پروفایل در RAM | کسری بار | معنی |
|---|---|---|---|---|
| organism | 18452 | `bare` | ۳۰۶ از ۳۳۸، alarm | فایل می‌گوید live؛ RAM تقریباً خاموش است |
| center | 18320 | `live` | ۰ | فلگ فایل را دارد؛ `STUDIO_LLM_CLOUD_VIA_ROUTER` در RAM **ABSENT** (بوت ۱۷:۴۷+۱۰، فلیپ ۲۰:۱۶+۱۰) |
| live | 11992 | `live` | ۰ | بوت ۲ سپتامبر — کهنه |

منبع: `_ops/state/flags-loaded-organism.json` · `flags-loaded-center.json` · `Get-Process` همین جلسه.

## فلگ بعدی واقعی شماره ۱ — بار کردن، نه خط تازه

روی فایل لپ‌تاپ تقریباً همه `=1` است. گیت بستهٔ بزرگ = **organism هنوز bare است**.

در RAM ارگانیسم همین حالا `=0` است، در فایل `=1`:

`OCTOPUS_WIRE_EMAIL` · `OCTOPUS_WIRE_LEAD` · `OCTOPUS_WIRE_LEAD_OUTBOUND` · `OCTOPUS_WIRE_HARVEST` · `OCTOPUS_WIRE_ZIMAN` · `OCTOPUS_WIRE_DOCTOR` · و ۱۹ تای دیگر در همان اسنپ‌شات.

ریستارت organism = روشن کردن آن ۳۰۶ کلید در پروسس زنده. این همان «باز کردن فلگ بعدی» است، نه یک خط تازه.

ریستارت center = فقط می‌نشاند `STUDIO_LLM_CLOUD_VIA_ROUTER=1` در RAM. Center از قبل `LEAD_OUTBOUND=1` و `EMAIL=1` و `TG_DURABLE_OUTBOX=1` دارد.

## فلگ بعدی واقعی شماره ۲ — هنوز صفر روی فایل

| کلید | الان | اثر |
|---|---|---|
| `FUGU_VIA_CENTRAL_GATE` | ۰ | خواهر Studio LLM؛ دفعهٔ پیش انتخاب نشد |
| `OCTOPUS_WHISPER_ALLOW_DOWNLOAD` | ۰ | دانلود وزن از شبکه |
| `EXTERNAL_ACTIONS` | ۰ | شمارنده؛ گیت نیست |

## فلگ بعدی واقعی شماره ۳ — ۱۳۸ / OFN / Season-5

| گیت | وضعیت | از این لپ‌تاپ |
|---|---|---|
| `AUTOSENDER_ARMED` | UNKNOWN | SSH نمی‌نویسم؛ فقط رسید مالک |
| دیمن حافظه (D3 YES) | روی فایل لپ‌تاپ ۱؛ روی ۱۳۸ unverified | همان |
| `HOLD_EXTERNAL` در Season-5 md | هنوز true | فایل `01-TRUTH` را بازنویسی نمی‌کنم |
| `OFN_ONLYFANS_HTTP_ARM` / `OFN_ONLYFANS_LIVE` | بسته | REJECT؛ حتی با بله باز نمی‌شود |
| `OFN_KEEP_GATES_OPEN` | بسته | قانون جلسه |
| `OFN_PUBLIC_CATALOG` / `OFN_COMMERCE_ROUTES` | پیش‌فرض off در `ofn/config.py:304` | بدن روی ۱۳۸ |

## قفل‌هایی که نمی‌پرسم

secret · بازنویسی رسید · PASS بی‌رسید · کوکی OF · `OFN_KEEP_GATES_OPEN` · bind `0.0.0.0` · ارسال از این چت
