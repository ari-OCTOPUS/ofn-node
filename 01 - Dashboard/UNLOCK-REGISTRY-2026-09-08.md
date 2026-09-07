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
| L05 | `partner_precondition` | ✅ رأی R2-3 «yes to all»: سطر از gates.json برد ۱۳۸ حذف شد (پری‌ایمیج + رسید ROUND2-MOOT-GATES-PRODUCTION) | `EXECUTED` |
| L06 | `wire_publish` | ✅ رأی R2-3: حذف شد — صفر خواننده در کد زندهٔ ofn (grep تأیید) | `EXECUTED` |
| L07 | `owner_release` | نگه دار — دومرحله‌ای درست است | `PROPOSED`=KEEP |
| L08 | `kill_switch` | نگه دار — فوریت است | KEEP |

## C — گیت‌های AGENTS.md / guard_flags

| ID | گیت | پیشنهاد | وضعیت |
|---|---|---|---|
| L09 | `D1` | ✅ رأی R2-3: تعریفی بازیابی‌نشده → از لیست ممنوع AGENTS.md حذف و به‌عنوان «بدون تعریف» مستند شد | `EXECUTED` |
| L10 | `D7` | ✅ رأی R2-3: مثل L09 | `EXECUTED` |
| L11 | `OWNER_KEY` | کلید از قبل ساخته و live است (09-06) → گیت را به «استفادهٔ درست» تغییر بده نه «ساخت» | `PROPOSED` |
| L12 | `miner_isolation` | ✅ رأی R2-3: از AGENTS.md حذف؛ arming در config.py عمداً ماند (بی‌خطر، هیچ pack معدن ندارد) | `EXECUTED` |
| L13 | `OCTOPUS_WIRE_*` ممنوع | ✅ رأی R2-4 گزینه A: دامنهٔ قاعده در AGENTS.md §4 مستند شد — فقط ایجنت‌های ویرایشگر؛ فلگ‌های runtime خود ارگانیسم‌اند؛ بدون تغییر فلگ | `EXECUTED` |
| L14 | `OFN_WIRE_*` | ✅ مثل L13 (همان بند AGENTS.md §4) | `EXECUTED` |
| L15 | `OBSERVATORY` | ✅ رأی R2-3: retired/بدون مصرف‌کننده مستند شد؛ do-not-enable ماند | `EXECUTED` |
| L16 | `CORTEX_HYPOTHESIS` | ✅ مثل L15 | `EXECUTED` |
| L17 | `auto_email` | ✅ رأی R2-3: بند AGENTS.md بازنویسی شد — کانال ایمیل retired؛ خروجی فقط مسیر تلگرامِ حاکم GOV-V7/V8 با رسید | `EXECUTED` |
| L18 | `PRODUCTION` | ✅ رأی R2-2: telegram_production→true در RUNTIME_MODE.json برد ۱۳۸ (پری‌ایمیج؛ هیچ مصرف‌کننده‌ای نبود = تراز مستندات) | `EXECUTED` |

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
| L45 | `OCTOPUS_WIRE_MINING_OS` | wire معدن | ✅ رأی R2-3: moot مستند؛ فلگ runtime دست‌نخورده (R2-4: بدون تغییر فلگ) | `EXECUTED` |
| L46 | `OCTOPUS_WIRE_POCKETSMITH` | wire حسابداری | ✅ رأی R2-3: بدون مصرف‌کننده در کد (فقط مانیفست‌های audit)؛ مستند شد | `EXECUTED` |
| L47 | `OCTOPUS_WIRE_PS_WRITEBACK` | نوشتن به PocketSmith | خطرناک → بسته بماند تا درخواست صریح | KEEP |
| L48 | `IMPROVE_REFRACTORY_H` | فاصلهٔ بهبود | بازبینی بعد از ثبات wedge | `PROPOSED` |
| L49 | `OCTOPUS_IMPROVE_REFRACTORY_H` | همان | مثل L48 | `PROPOSED` |

## I — عملیاتی (باگ — ایجنت تعمیر می‌کند، ثبت با رسید)

| ID | مشکل | پیشنهاد | وضعیت |
|---|---|---|---|
| L50 | checkout1_poll مسیر لینوکس | پورت به ویندوز | `PROPOSED` |
| L51 | حسگر پول miswired | repoint به زیمان | `PROPOSED` |
| L52 | METABOLIC-OBS | ✅ رأی R2-1 (تله‌متری حقیقت): وایر از قبل بود (e2a317c)؛ اجرای زندهٔ ۰۹-۰۸: تلمتری==billed==AU$0.150135، conflicts=[] — رسید ROUND2-METABOLIC-VERIFIED | `VERIFIED` |

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
- 2026-09-08T23:4xZ (مرحله ۱ تکمیل، جلسهٔ ZCode پس از قطع Codex):
  - **D0 دامنهٔ اصلی زیمان**: مالک تصویر خرید را داد → نام‌ها: **ziman-gift.com.au** + **ziman-gift.shop** → رأی: «ziman-gift.com.au اصلی شود — جای صفحهٔ معرفی فعلی» → **EXECUTED + VERIFIED**: اتصال DNS (اتوریتات ns73.domaincontrol.com → 23.227.38.32) · TLS لبهٔ Shopify (Let's Encrypt، اولین 200 در 23:40:59Z) · **Primary badge روی ziman-gift.com.au در admin** · صفحهٔ محصول 200 بدون ریدایرکت به .com مرده (۰ رخداد لینک .com در HTML) · رسید: `09-LANES/UNLOCK-REVIEW-20260908/DOMAIN-EXECUTION-STEP3-FINAL.json` + STEP1/STEP2/PARTIAL · محدودهٔ رأی رعایت شد: ziman-gift.shop دست‌نخورده، بدون تغییر ایمیل/مینی‌اپ/خرید
  - قفل‌های حلقه: D0_domain ✅ · DOM2_names ✅ (هر دو نام ثبت شد) · L56 مسیر مینی‌اپ عمومی باز (HTTPS دامنهٔ زیمان موجود شد — نصب مینی‌اپ همچنان رأی جدا می‌خواهد)
- 2026-09-08T23:5xZ (مرحلهٔ ۲ کامل، رأی «yes to all» در جلسهٔ ZCode، ثبت در OWNER-APPROVALS دور چهارم):
  - **R2-1 METABOLIC-OBS (L52) → VERIFIED بدون تغییر کد**: وایر organ_gate→telemetry از قبل موجود بود (کامیت e2a317c)؛ اجرای زندهٔ همین لحظه: تلمتری==billed==AU$0.150135، conflicts=[]. عدد 1.07 زمان بالوت بازتولید نشد (هر دو ثبت). رسید: lane/ROUND2-METABOLIC-VERIFIED-20260908.json
  - **R2-2 PRODUCTION (L18) → EXECUTED**: telegram_production false→true در board138:~/octopus-mesh/state/RUNTIME_MODE.json؛ پری‌ایمیج + رسید در ~/octopus-mesh/receipts/ROUND2-MOOT-GATES-PRODUCTION-20260908.json؛ هیچ مصرف‌کنندهٔ کدی یافت نشد (تراز مستندات، بدون اثر اجرایی)
  - **R2-3 moot×۸+D1/D7 → EXECUTED**: gates.json برد: حذف partner_precondition+wire_publish (پری‌ایمیج؛ صفر خواننده در ofn/ofn زنده) · AGENTS.md §4: blocked-list به secret_rotation+OWNER_KEY کاهش یافت؛ auto_email→کانال retired؛ OBSERVATORY/CORTEX_HYPOTHESIS→retired مستند؛ config.py miner_isolation arming و guard_flags.py عمداً دست‌نخورده
  - **R2-4 wire scope (L13/L14) → EXECUTED**: دامنهٔ قاعده در AGENTS.md §4 مستند شد (ایجنت‌های ویرایشگر؛ فلگ‌های runtime خود ارگانیسم؛ تغییر فقط با رأی مالک)؛ صفر تغییر فلگ
  - سه قفل مطلق GOV-V8 (L01-L03) و چهار حفاظ GOV-V7 دست‌نخورده‌اند.

## 🔁 وصل به حلقه‌های دوپامین/ترس (فرمان مالک 2026-09-07)

> «همه چیزو به حلقه‌های دوپامین و ترس وصل کن، ارگانیسم خودش ادامه بدهد، بعد باز شدن هر قفل»

اجرا: `_ops/drive_loops.py` (ساختهٔ ایجنت موازی + به‌روزرسانی این جلسه):
- **ترس** = قفل‌های بستهٔ واقعی: دامنهٔ مرده (0.95) · پول صفر (0.85) · دو دامنهٔ نامعلوم (0.8) · انقضای GO (خودکار با آینهٔ `go-expiry.json`، الان ۱۰-۰۷) · فشار رجیستری (هر قفل PROPOSED +0.01)
- **دوپامین** = فقط بردِ رسیددار: رأی مالک ثبت‌شده · قفل بازشده (weight 0.5) · مأموریت سه‌نقشی · فراخوانی paid سالم
- **ادامهٔ خودکار** = هر قفل که باز شود → `task.resume` + قدم بعدی در `drive-queue.jsonl` → مدیر سه‌نقشی در context می‌بیند → مأموریت → ارزیاب → رسید → دوپامین بعدی. tick در organism.py هر beat (fail-soft).
- قفل‌های این حلقه الان: D0_domain 🔒 · AUTO1_sender 🔒 · MSG38 ✅(NOT_PAID رأی مالک) · L23_hold_external ✅ · L24_go ✅ · DOM2_names 🔒 · REGISTRY_round2 🔒 · CASH_first_order 🔒
- selftest سبز ۲ بار؛ سه قفل امروز باز شد و در صف ادامه ثبت شد (13:37:57Z)
