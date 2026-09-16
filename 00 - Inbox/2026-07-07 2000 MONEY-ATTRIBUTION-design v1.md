---
type: design
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, organism, attribution, fitness]
created: 2026-07-07
updated: 2026-07-07
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-07 1935 OCTOPUS-STAGE0-REPORT]]"
  - "[[_ops/ORGANISM-SPEC]]"
---

# MONEY-ATTRIBUTION v1 — منطق «کدام cell اعتبارِ دلار را می‌گیرد» (تصمیم‌ها قفل شد)

> نسخهٔ فشردهٔ طرحِ کاملِ چت (جلسه ۲۶-قبل)؛ سه تصمیمِ باز آن با **پاسخ‌های STAGE-0 آری (2026-07-07)** قفل شد → status: ready برای ساخت در **P2** (پس از merge + اولین tick). سازگار با ناوردی‌ها: تک-enforcer، fail-closed، پذیرش فقط انسانی+reconcile، append-only.

## سه تصمیمِ قفل‌شده (verdict آری 2026-07-07)

1. **feedِ مستقلِ reconcile: بله** — بانک/Stripe/فاکتور = ground-truth؛ fitness فقط روی پولِ reconcile‌شده با این feed؛ **هرگز self-report**.
2. **carrier ‏Lead-نقاشی:** شماره‌فاکتور وجود ندارد → **سیستم id یکتا mint می‌کند** (`lead/invoice id`) و attribution روی همان کلید می‌خورد.
3. **پنجرهٔ attribution: ۷ روز** (Lead→پرداخت تا ۷ روز منتسب می‌ماند؛ decision_epoch روی id ذخیره، اعتبار به cellِ زمانِ تصمیم).

## هسته (بدون تغییر از طرح اصلی)

- **چرخهٔ حیات:** `PROPOSAL` (mint id + expected [EST]؛ هرگز fitness نمی‌شود) → `CLAIMED` (گزارش انسان {ref, amount}؛ لازم ولی بی‌ارزش تا تطبیق) → `CONFIRMED` (فقط reconcile.py با feed مستقل؛ mismatch → [CONFLICT] freeze) → `ATTRIBUTED` (fitness می‌خواند).
- **قانون طلایی:** fitness هرگز چیزی زیر CONFIRMED نمی‌خواند. ایجنت‌ها فقط PROPOSAL/EXPERIENCE می‌نویسند؛ CONFIRMED را فقط job ‏reconcile می‌نویسد.
- **مدل انتساب:** single-touch روی attribution_id (Shapley/multi-touch عمداً حذف)؛ تقسیم درون‌زنجیره با وزنِ ثابتِ انسان‌تعیین — cellها هرگز وزن خودشان را ست نمی‌کنند.
- **پاهای بی‌درآمد** (Accounting/Mining/هیپنوتیزم): organ روی floor، **خارج از لوپ داروینی** — attribution فقط پاهای درآمدزا را حکومت می‌کند. Project-F 🔒 مستثنای مطلق.
- **دفاع‌های ضدگیم:** تطبیق فقط با feedِ read-only · dedup روی money-event id · CONFIRMED فقط از job · وزن‌ها ثابت · mismatch=freeze · waste خودپرداخت. گاردِ پایه از امروز test-backed است (چک «APPROVAL جعلی → acceptance بی‌حرکت»).
- **متریک سلامت:** `attribution_coverage` (چند٪ دلارها ref ‏match‌شونده دارند) = vital درجه‌یک کنار σ/drawdown؛ اگر پایین بود fitness نویز است — اول carrier را درست کن.
- **رویدادها:** طبق verdict ‏V2 (2026-07-07) = **type جدید در EVENT_TYPES** ژنوم (مثل `MONEY_ATTRIBUTION`) — پیاده‌سازی P1 با تست زنجیره.

## carrierهای per-pa (به‌روزشده با verdict)

| پا | carrier | منبع تطبیق | کیفیت |
|---|---|---|---|
| Lead-نقاشی | **id ‏mint‌شدهٔ سیستم** (lead/invoice id) — روی کوت/فاکتور/رسید تکرار شود | feed بانک/حسابداری | تمیز |
| Crypto-eToro | position_id | صورت بستهٔ eToro (P&L محقق) | تمیز |
| Ziman/marketing | UTM/کد تخفیف redeem‌شده | فروش منتسب | فازی — low-confidence، هرگز مبنای تنهای spawn |

## bootstrap (فاز A ‏shadow، ~۳۰ روز)

اپراتور دستی outcome+ref گزارش می‌دهد؛ reconcile روی export دستی feed؛ fitness محاسبه ولی هیچ‌چیز نمی‌راند؛ سنجش attribution_coverage. فاز B: fitness به پیشنهادها اطلاع می‌دهد (spawn همچنان human-gated). فاز C: پشت activation flag.

## چک‌لیست ساخت (P2)

- [ ] type جدید ledger (پیش‌نیاز، P1 — verdict V2)
- [ ] `_ops/budget/attribution.py` (mint/lifecycle/split) + `reconcile.py` (تطبیق، ترفیع CONFIRMED)
- [ ] اتصال fitness.py (فقط CONFIRMED/ATTRIBUTED؛ پنجرهٔ ۷روزه + grace)
- [ ] تست‌ها: جعل ref → CONFLICT نه CONFIRMED · double-claim یک دلار → dedup · coverage در گزارش
