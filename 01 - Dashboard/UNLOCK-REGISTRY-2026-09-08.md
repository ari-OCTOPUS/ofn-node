---
type: dashboard
status: active
tags: [octopus, locks, unlock, registry, owner-decisions]
created: 2026-09-08
updated: 2026-09-08
---

# 🔓 UNLOCK-REGISTRY — سرشماری قطعی همهٔ قفل‌ها + وضعیت هرکدام

> **پروتکل مالک (فرمان 2026-09-08):** ایجنت پیشنهاد می‌دهد → مالک تایید می‌کند → ایجنت ثبت می‌کند (همین فایل) → اجرا + تاییدعمل → همه می‌بینند.
> وضعیت‌ها: `PROPOSED` (پیشنهاد داده شد) → `APPROVED` (مالک تایید کرد) → `EXECUTED` (اجرا شد) → `VERIFIED` (کارش تایید شد) / `KEEP` (بسته می‌ماند) / `WAIVED` (مالک گذشت)

## شمارش صادقانه

مالک گفت «۹۱ قفل». سرشماری واقعی طبق منابع (نوت ۹۷ + flags.cmd + BUDGET.json + budgets.yaml + سیستم‌های default-OFF):

| طبقه | تعداد |
|---|---|
| A — سه قفل مطلق GOV-V8 | ۳ |
| B — gates.json برد ۱۳۸ | ۵ |
| C — گیت‌های AGENTS.md/guard_flags | ۱۰ |
| D — نردبان GOV-V8 | ۵ |
| E — قفل‌های زمانی | ۳ |
| F — فایل‌های switch | ۵ |
| G — سقف‌های بودجه | ۱۰ |
| H — فلگ‌های خاموش (=0) | ۹ |
| I — قفل‌های عملیاتی (باگ) | ۳ |
| J — زیرسیستم‌های default-OFF | ۱۰ |
| **جمع واقعی** | **۶۳** |

عدد ۹۱ با هیچ شمارش مستندی تایید نشد (status: unverified). اگر هر عضو خانوادهٔ `OCTOPUS_WIRE_*` جدا شمرده شود از ۹۱ بیشتر می‌شود؛ قفل‌شده‌های واقعی = ۶۳. هر دو عدد ثبت شد (resolution: مالک می‌تواند بگوید ۹۱ را از کجا دید).

---

## A — مطلق (هیچ‌کس باز نمی‌کند، حتی با رأی مالک)

| ID | قفل | وضعیت | یادداشت |
|---|---|---|---|
| L01 | چاپ/ارسال secret | `KEEP` ابدی | GOV-V8 قفل دائم |
| L02 | حذف/بازنویسی زنجیرهٔ رسید | `KEEP` ابدی | GOV-V8 قفل دائم |
| L03 | PASS بی‌رسید | `KEEP` ابدی | GOV-V8 قفل دائم |

## B — gates.json برد ۱۳۸ (مالک باز می‌کند)

| ID | گیت | پیشنهاد | وضعیت |
|---|---|---|---|
| L04 | `secret_rotation` | مالک چرخش را waive کرد (09-07) → گیت را بگذار باز تا کد stale نشود | `PROPOSED` |
| L05 | `partner_precondition` | moot — حذف یا تعریف کن «همکار یعنی چه» | `PROPOSED` |
| L06 | `wire_publish` | کد مصرف‌کننده ندارد → حذف از gates.json | `PROPOSED` |
| L07 | `owner_release` | نگه دار — دومرحله‌ای درست است | `PROPOSED`=KEEP |
| L08 | `kill_switch` | نگه دار — فوریت است | KEEP |

## C — گیت‌های AGENTS.md / guard_flags

| ID | گیت | پیشنهاد | وضعیت |
|---|---|---|---|
| L09 | `D1` | تعریف واقعی را پیدا/مستند کن؛ اگر «اجرا production» است و سیستم production است → بی‌اثر، مستندش کن | `PROPOSED` |
| L10 | `D7` | تعریف گم شده → یا مستند یا حذف | `PROPOSED` |
| L11 | `OWNER_KEY` | کلید از قبل ساخته و live است (09-06) → گیت را به «استفادهٔ درست» تغییر بده نه «ساخت» | `PROPOSED` |
| L12 | `miner_isolation` | moot (mining PARKED) → حذف | `PROPOSED` |
| L13 | `OCTOPUS_WIRE_*` ممنوع | تناقض: ۱۹۵ تا روشن است → یا قاعده را به «wire-write بیرونی» محدود کن یا همه را خاموش کن | `PROPOSED` |
| L14 | `OFN_WIRE_*` | مثل L13 | `PROPOSED` |
| L15 | `OBSERVATORY` | تعریف گم شده → مستند یا حذف | `PROPOSED` |
| L16 | `CORTEX_HYPOTHESIS` | تعریف گم شده → مستند یا حذف | `PROPOSED` |
| L17 | `auto_email` | moot (تلگرام جایگزین) → حذف از AGENTS.md با رأی مالک | `PROPOSED` |
| L18 | `PRODUCTION` | تناقض: سیستم production است ولی flag بسته → روشن کن با رأی مالک | `PROPOSED` |

## D — نردبان GOV-V8

| ID | قفل | پیشنهاد | وضعیت |
|---|---|---|---|
| L19 | L2 OWNER-CANCEL cash-gate | درست کار می‌کند → نگه دار تا VERIFIED_CASH واقعی | KEEP |
| L20 | L3 | با ۳ تراکنش واقعی باز می‌شود — هدف سیزن، نه دستی | AUTO |
| L21 | L4 | مستند نشده → مالک تعریف کند یا حذف | `PROPOSED` |
| L22 | `MAY_AUTHORIZE=false` | مطلق درست — هرگز باز نشود | KEEP |
| L23 | `hold_external=true` | ✅ رأی مالک ۰۹-۰۷: «باز کن با رسید» → **اجرا + تایید**: spec locks + ofn سه فایل + ۲ تست (۳۳/۳۳ سبز، کامیت 63938eb0 روی ۱۳۸) + scheduler تک‌منبعی (۱۱ جای هاردکد → `_spec_hold_external()`) + ofn.service ری‌استارت PID 3905410 + **تیک ۱۳:۳۰:۰۵Z سکدولر exit 0/SUCCESS** · سقف روز ۸/۸ پر بود ⇒ اولین پکت با hold_external=false روز ۰۹-۰۸ UTC mint می‌شود · رسید: `board138:~/octopus-mesh/receipts/GO-EXT2-HOLD-EXTERNAL-OPEN-20260907.json` | `VERIFIED` (پکت‌سطحی: اولین mint ۰۹-۰۸) |

## E — زمانی

| ID | قفل | پیشنهاد | وضعیت |
|---|---|---|---|
| L24 | standing GO (انقضا 09-14) | ✅ رأی مالک ۰۹-۰۷: «تا ۱۰-۰۷» → **اجرا شد**: spec `expires_at=2026-10-07` + ext:2 + رسید GO-EXT2 (قبلاً ۰۹-۲۱ با GO-EXT1 از بالوت موازی) | `EXECUTED` |
| L25 | msg38 (انقضا 09-08T12:10Z) | ✅ رأی مالک ۰۹-۰۷: «نمی‌خرم — NOT_PAID ثبت شود» → **اجرا شد** قبل از ددلاین: رسید `MSG38-RESOLVED-NOT-PAID-20260907.json`؛ جایگزین REPORTED_NOT_VERIFIED از بالوت شب (هر دو ثبت شدند، جدیدترین حاکم) | `EXECUTED` |
| L26 | L1 scoring (09-08) | خودکار — دست نزن | AUTO |

## F — فایل‌های switch

| ID | فایل | پیشنهاد | وضعیت |
|---|---|---|---|
| L27 | HALT-ALL | نگه دار (فوریت) | KEEP |
| L28 | STOP-ORGANISM | نگه دار | KEEP |
| L29 | STOP-CORTEX | نگه دار | KEEP |
| L30 | STOP-TG-CENTER | نگه دار | KEEP |
| L31 | WATCHDOG-STALL-REVIVE | روشن درست است | DONE |

## G — سقف‌های بودجه (تغییر = رأی مالک)

| ID | سقف | مقدار | پیشنهاد | وضعیت |
|---|---|---|---|---|
| L32 | cap_monthly | 45 AUD | نگه دار | KEEP |
| L33 | life_currency_daily_cap | 30 | نگه دار | KEEP |
| L34 | daily_message_cap | 25 | کافی است | KEEP |
| L35 | daily_spend_cap_aud | 50 | کافی است | KEEP |
| L36 | paid_ads | false/0 | تا اولین فروش نگه دار | KEEP |
| L37 | human_gate_aud | 20 | نگه دار | KEEP |
| L38 | explore_pct | 0.1 | نگه دار | KEEP |
| L39 | on_cap_reached | halt | نگه دار | KEEP |
| L40 | fugu/paid-calls quota | محدود | پایش کن | KEEP |

## H — فلگ‌های خاموش (۹)

| ID | فلگ | معنا | پیشنهاد | وضعیت |
|---|---|---|---|---|
| L41 | `EXTERNAL_ACTIONS=0` | شمارندهٔ اثر بیرونی خاموش | روشن کن با L23 | `PROPOSED` |
| L42 | `OCTOPUS_BRAIN_CALL_SHARE=0.6` | سهم مغز از beat | با ارتقای مغز بازبینی | `PROPOSED` |
| L43 | `OCTOPUS_TG_VOICE_KEEP_AUDIO` | صدای مالک ذخیره نشود | پیش‌فرض درست (حریم خصوصی) | KEEP |
| L44 | `OCTOPUS_WHISPER_ALLOW_DOWNLOAD` | دانلود صدا | با L23 بازبینی | `PROPOSED` |
| L45 | `OCTOPUS_WIRE_MINING_OS` | wire معدن | moot (PARKED) → حذف | `PROPOSED` |
| L46 | `OCTOPUS_WIRE_POCKETSMITH` | wire حسابداری | تعریف کن یا حذف | `PROPOSED` |
| L47 | `OCTOPUS_WIRE_PS_WRITEBACK` | نوشتن به PocketSmith | خطرناک → بسته بماند تا درخواست صریح | KEEP |
| L48 | `IMPROVE_REFRACTORY_H` | فاصلهٔ بهبود | بازبینی بعد از ثبات wedge | `PROPOSED` |
| L49 | `OCTOPUS_IMPROVE_REFRACTORY_H` | همان | مثل L48 | `PROPOSED` |

## I — عملیاتی (باگ — ایجنت تعمیر می‌کند، ثبت با رسید)

| ID | مشکل | پیشنهاد | وضعیت |
|---|---|---|---|
| L50 | checkout1_poll مسیر لینوکس | پورت به ویندوز | `PROPOSED` |
| L51 | حسگر پول miswired | repoint به زیمان | `PROPOSED` |
| L52 | METABOLIC-OBS | دو مسیر — مالک انتخاب کند | `PROPOSED` ← مرحله ۲ |

## J — زیرسیستم‌های default-OFF

| ID | سیستم | چرا خاموش | پیشنهاد | وضعیت |
|---|---|---|---|---|
| L53 | `OCTOPUS_UNIFIED_CHAT=0` | conv-hub فاز ۱ | روشن کن بعد تست | `PROPOSED` |
| L54 | epistemics default-OFF | ADR-039 wired نیست | C3 اول | `PROPOSED` |
| L55 | spine flag-off | تازه UNIFY شد | مصرف‌کنندهٔ اول را وصل کن | `PROPOSED` |
| L56 | مینی‌اپ public URL | HTTPS نداریم | با دامنهٔ زیمان حل می‌شود | `PROPOSED` ← وابسته به دامنه |
| L57 | brain_core shadow | matched=0 | promote نکن | KEEP |
| L58 | 4d_system | وصل نیست | owner تصمیم سال بعد | KEEP |
| L59 | TG listener (Q9) | منتظر GO | با L23 بررسی | `PROPOSED` |
| L60 | presence-bot | نقص مستند | بازنویسی | `PROPOSED` |
| L61 | hooks governance silent | بعد از flip خاموش | audit کن | `PROPOSED` |
| L62 | KILL_SEAM unarmed | اختیاری | مسلح کن | `PROPOSED` |

---

## خلاصهٔ رأی‌گیری‌ها

| مرحله | رأی‌ها | وضعیت |
|---|---|---|
| ۱ (الان) | L23 hold_external · L24 GO تمدید · L25 msg38 · دامنهٔ زیمان | در جریان |
| ۲ | مغز (L42) · L52 METABOLIC · L18 PRODUCTION · L13 wire تناقض | بعد از ۱ |
| ۳ | پاک‌سازی moot (L05 L06 L12 L15 L16 L17 L45 L46) | بعد از ۲ |
| ۴ | عملیاتی (L50 L51) — ایجنت اجرا می‌کند | همزمان |
| ۵ | default-OFF ها (L53-L56 L59-L62) | بعد از ثبات |

## تاریخچهٔ رأی‌ها (append-only)

- 2026-09-07T13:2xZ (مرحله ۱، سؤال ساختاریافته، جلسهٔ لپ‌تاپ UNLOCK-REGISTRY):
  - **L23 hold_external**: مالک → «باز کن با رسید (پیشنهاد)» → EXECUTED (رسید GO-EXT2-HOLD-EXTERNAL-OPEN-20260907.json روی ۱۳۸)
  - **L24 standing GO**: مالک → «تا ۱۰-۰۷» → EXECUTED (spec ext:2، قبلی ۰۹-۲۱ از GO-EXT1 بالوت موازی)
  - **L25 msg38**: مالک → «نمی‌خرم — NOT_PAID ثبت شود» → EXECUTED (MSG38-RESOLVED-NOT-PAID-20260907.json؛ supersedeٔ REPORTED_NOT_VERIFIED شب، هر دو حفظ شدند)
  - **دامنهٔ زیمان**: مالک → «جدید ثبت کردم دوتا خریدم بگرد پیدا کن موازی باهات یه ایجنت نوشته» → **جستجو انجام شد، پیدانشد**: vault (کامیت‌ها + diff‌های commitنشده + tg-inbox/outbox + doctor state) · برد ۱۳۸ (delivered packets + platform_matrix + data) · Shopify API (۴ دامنه: فقط قدیمی‌ها) → **منتظر نام دو دامنه از مالک** (status: unverified)
  - کشف همزمان: بالوت موازی شب قبل (a379298 + OWNER-APPROVALS-2026-09-07.md) D-1 مغز=API را بسته و FX-1 پین را اجرا کرده — فراخوانی paid موفق deepseek-v4-flash با رسید ($0.0000183) ⇒ فاز-۲ «مغز» عملاً حل است؛ دوباره نپرسید.
- 2026-09-08: رجیستری ساخته شد (کامیت این فایل). هیچ رأیی هنوز ثبت نشده.
