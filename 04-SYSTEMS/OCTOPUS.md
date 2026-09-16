---
type: system-note
system: octopus
created: 2026-08-15
sources:
  - "README.md ریشه (2026-08-10) — نقشهٔ ۶ پا + ۲ مغز"
  - "OCTOPUS/CURRENT-TRUTH.md (زنده، auto 2026-08-15T04:10Z)"
  - "اجراهای راستی‌آزمایی همین جلسه"
status: mixed — هر عدد برچسب خودش
---

# OCTOPUS — معماری کلی: ۶ پا + ۲ مغز + سیستم عصبی

> این یادداشت آینهٔ راستی‌آزمایی‌شده است؛ منبع اصلی [[../README.md|README.md]] و [[../OCTOPUS/CURRENT-TRUTH.md|CURRENT-TRUTH]].

## ساختار (طبق README ریشه)

```
مغز مادر: langar / 04-Architect System / _ops → F:\backup (کانونیکال)
۶ پا: 03 - Projects/{Accounting, Lead-نقاشی, Mining, Crypto-eToro, Ziman, Project-F}
۲ مغز مستقل: 4d_system (پژوهش) · NBB-CP (حاکم — B6)
۱ ابزار: نقشهٔ اختاپوس (تشخیص)
سیستم عصبی: nervous-system/
```

## وضعیت زندهٔ ارگانیسم (CURRENT-TRUTH 2026-08-15)

| مؤلفه | وضعیت | منبع |
|-------|-------|------|
| سه قلب + arbiter | LIVE · hybrid production wire **CLOSED** | CURRENT-TRUTH بخش Hearts/Brains |
| دو مغز زنده | cortex + business_brain · innervation 100% | همان |
| `4d_system` / Super-Governor | **وصل نیست** | همان |
| brain_core | SHADOW matched=0 → promote نشود | همان |
| پاها (legs) | ۵ پا fed در legs-feed 2026-08-12 · starved/stale=[] | CURRENT-TRUTH |
| halted | False · beat 36563 · coherence 0.95 | بلوک auto (verified) |

## جدول پاها (از README — تعداد تست‌ها فقط ادعای README)

| پا | شریک/نقش | وضعیت کد (ادعای README) | تست | وضعیت |
|----|-----------|--------------------------|------|-------|
| Accounting | قلب مالی | manifest کامل، اجرا صفر، کد در `_code/` | — | unverified |
| Lead-نقاشی | عباس · درآمد اصلی | Brushline 8/9، کاریابی | ۳۳ (کاریابی) | unverified |
| Mining | پژوهش/ناوگان | پژوهش کامل، اجرا صفر | — | unverified |
| Crypto-eToro | حسگر بازار | معماری کامل، NO_ACTION | — | unverified |
| Ziman | ملیحه · گالری/هدیه | control-brain | ۲۱ | unverified |
| Project-F | سبا · creator | brain+langar+studio | ۲۹ | unverified |

> ⚠️ README ریشه **stale** است: به `app/NBB-CP` حذف‌شده (2026-08-03) اشاره می‌کند → [[../01-TRUTH/CONTRADICTIONS.md|C-004]]

## پل ارشد↔برد

اتصال Windows (ارشد) ↔ Orange Pi (برد) — [[OFN-NODE]] · بستهٔ کد: `octopus-bridge/octopus_bridge/`
