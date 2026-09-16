---
project: octopus/ofn
leg: studio
title: اتوماسیون بازاریابی «اونلی فنز» — پلن اولیه v0.1
owner: آری
partner: سبا
date: 2026-08-05
status: پیش‌نویس اولیه — منتظر بازخورد آری و ایجنت‌های موازی
prerequisite_gates: secret_rotation 🔒 · partner_precondition 🔒 · (باید باز شوند)
tags: [ofn, studio, marketing, automation, plan]
---

# پلن اتوماسیون بازاریابی «اونلی فنز» — v0.1

> **این سند یک نقشهٔ اولیه است.** هر بخش نیاز به ایجنت تخصصی دارد.
> آری با چند ایجنت موازی روی آن کار می‌کند و پلن نهایی را برمی‌گرداند تا کدنویسی شود.

---

## ۰) خلاصهٔ اجرایی — آنچه قرار است ساخته شود

یک سیستم بازاریابی خودکار برای leg استودیو (سبا) که:

```
هر هفته یک سبک بازاریابی متفاوت را از بین ۱۰ سبک انتخاب می‌کند
       ↓
با تحقیق زندهٔ اینترنت + ترندها، موضوع آن هفته را پیدا می‌کند
       ↓
به سبا (از طریق مینی‌اپ تلگرام) پیشنهاد و سؤال می‌دهد
       ↓
محتوای درخواستی را از سبا می‌گیرد (عکس + حس + برچسب سبکی)
       ↓
نسخهٔ هر پلتفرم را تولید می‌کند (کپشن/هشتگ/فرمت مخصوص آن پلتفرم)
       ↓
هر چیزی که general است را در پلتفرم‌ها منتشر می‌کند، restricted هرگز بیرون نمی‌رود
       ↓
عدد پلتفرم را جمع می‌کند → با حس سبا و ترند مقایسه می‌کند → هفتهٔ بعد را شکل می‌دهد
```

**محتوای سبا:** faceless Persian beauty/feet content — انعطاف‌پذیر، بدون چهره، بدون nudity کامل،
در دو رده: `general` (قابل انتشار) و `restricted` (هرگز از دستگاه خارج نمی‌شود).

---

## ۱) 🔴 تصمیمات مالک که این پلن روی آن‌ها سوار شده (تثبیت‌شده)

| تصمیم | مقدار | پیامد ساختاری |
|---|---|---|
| محتوا | faceless Persian beauty/feet، بدون nudity کامل، انعطاف‌پذیر | دو ردهٔ `general` و `restricted` از `advisor_gate` |
| سطح اتوماسیون | **کاملاً خودکار حتی انتشار** (با تمام ریسک) | نیاز به «کلید رهایی صریح مالک» + guardrails سخت |
| مغز تحقیق | خودم تصمیم بگیرم (fugu سریع‌تر، fugu-ultra بهتر) | هر دو با fallback هوشمند (پایین → بالا) |
| پلتفرم‌ها | **۱۰ کانال از اول** | حتی آنهایی که API رسمی ندارند → دو لایهٔ API و manual-queue |

### ۱-۱) کلید رهایی صریح مالک (Owner Release Switch)

چون انتشار خودکار با قانون پیش‌فرض CLAUDE.md در تضاد است، این مکانیزم لازم است:

```python
# ofn/kernel/release_switch.py  (جدید)
# این تنها چیزی است که WIRE_PUBLISH را واقعاً روشن می‌کند.
# نه با env var، نه با config، نه با مدل — فقط با یک تصمیم دو مرحله‌ای آری.

class OwnerRelease:
    """
    انتشار خودکار فقط وقتی فعال که هر سه شرط باشد:
      1. آری صریحاً با تأیید دو مرحله‌ای (در پنل) فعال کرده باشد
      2. gateهای secret_rotation و partner_precondition باز باشند
      3. kill-switch روشن نباشد
    """
```

**Guardrails که حتی با کلید روشن هم اعمال می‌شوند:**
- فقط محتوای `sensitivity=general` (محرک: `advisor_gate.may_send_image`)
- فقط محتوای با رضایت معتبر (`consent.may_publish` قبل از هر انتشار)
- rate limit per platform (per hour / per day)
- idempotency key روی هر پست (retry دو بار پست نمی‌کند)
- kill-switch: یک endpoint `/api/v1/owner/kill` که با یک درخواست همه را متوقف می‌کند
- log کامل هر انتشار در ledger (tamper-evident)

### ۱-۲) مغز تحقیق — استراتژی دو پله‌ای هوشمند

```
سؤال تحقیق هفتگی:
   ۱. اول fugu (عمق استاندارد) — سریع، ارزان
   ۲. اگر fugu گفت "insufficient" (سیگنال صریح) → ارتقا به fugu-ultra
   ۳. هرگز ارتقا بدون سیگنال insufficient — سکوت یعنی نه
```

این هم سرعت fugu را می‌گیرد و هم عمق fugu-ultra را وقتی لازم است.
هزینهٔ متوسط کمتر از فقط-fugu-ultra، کیفیت بالاتر از فقط-fugu.

---

## ۲) معماری — روی معماری موجود سوار می‌شود، نه کنارش

### ۲-۱) آنچه از قبل هست و استفاده می‌شود

| موجود | نقش در پلن |
|---|---|
| `kernel/scout.py` | **الگوی تحقیق ترند هفتگی** — با حافظهٔ جغجغه‌ای، screen سخت، brief. فقط برای ماینینگ نوشته شده، analog برای استودیو ساخته می‌شود. |
| `kernel/consent.py` | دروازهٔ رضایت — هر انتشار قبل از رفتن چک می‌شود |
| `kernel/advisor_gate.py` | `sensitivity=restricted` هرگز از دستگاه خارج نمی‌شود (ساختاری) |
| `adapters/outbox.py` | تنها درِ خروج — هر انتشار از اینجا می‌رود، idempotent |
| `adapters/ledger.py` | هر انتشار tamper-evident ثبت می‌شود |
| `kernel/scrub.py` | PII قبل از هر تماس بیرونی پاک می‌شود |
| `kernel/routing.py` | چهار پله مغز + latency policy |
| `ofn/kernel/risk.py` | ارزیابی ریسک — انتشار همیشه RED می‌ماند |

### ۲-۲) آنچه جدید ساخته می‌شود (جدید)

```
ofn/kernel/
   scout.py           ← الگوی موجود (ماینینگ) — analog تولید می‌شود
   marketing_scout.py ← جدید: analog scout برای محتوا/ترند
   release_switch.py  ← کلید رهایی مالک (بالا)
   platform_matrix.py ← جدید: کدام پلتفرم چه محتوایی را می‌پذیرد (سختی‌ها)

ofn/adapters/
   trend_sources.py   ← جدید: Google Trends API + TikTok Creative Center + Exploding Topics
   content_router.py  ← جدید: یک محتوا → نسخهٔ هر پلتفرم (کپشن/هشتگ/فرمت)
   platforms/         ← جدید: یک آداپتور per پلتفرم
      telegram_channel.py
      bluesky.py
      email.py
      instagram.py
      tiktok.py
      youtube.py
      twitter_x.py
      facebook.py
      threads.py
      pinterest.py
      reddit.py
   metrics_puller.py  ← جدید: عدد پلتفرم را جمع می‌کند (API analytics)

ofn/adapters/studio_store.py  ← توسعه: posts و metrics سری زمانی (طرح در brief §۶ ذکر شده)

web/studio.html      ← توسعه: ویوی «مارکتینگ هفته» برای سؤال/پاسخ سبا

packs/studio.yaml    ← توسعه: ۱۰ سبک بازاریابی + content_styles
```

### ۲-۳) نمودار جریان هفتگی

```
┌─────────────────────────────────────────────────────────────────┐
│  دوشنبه ۰۳:۱۷ (بعد از backup) — چرخهٔ تحقیق ترند               │
│                                                                  │
│  trend_sources.py ──→ Google Trends + TikTok CC + Exploding Topics
│         ↓                                                        │
│  marketing_scout.research_focus()  ← شکاف‌های اندازه‌گیری‌شده     │
│         ↓                                                        │
│  فاوگ (با fallback فاوگ-اولترا)                                 │
│         ↓                                                        │
│  marketing_scout.screen() — سخت‌گیرانه، حافظه رد‌کرده‌ها          │
│         ↓                                                        │
│  Candidate trend (با تاریخ مشاهده + تعداد، نه پیش‌بینی)          │
│         ↓                                                        │
│  انتخاب سبک بازاریابی هفته (rotation یا best-fit با ترند)       │
│         ↓                                                        │
│  → پیام به مینی‌اپ سبا: «این هفته سبک X، ترند Y. این ۳ ایده…»   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  هر زمان سبا باز می‌کند — چرخهٔ تولید محتوا                     │
│                                                                  │
│  سبا عکس آپلود می‌کند + برچسب سبکی + حس (felt_right)            │
│         ↓                                                        │
│  consent check (subjects/releases)                              │
│         ↓                                                        │
│  content_router: یک محتوا → ۱۰ نسخهٔ پلتفرم                    │
│         ↓                                                        │
│  هر نسخه با سختیِ پلتفرم تطبیق (general-safe caption/hashtag)  │
│         ↓                                                        │
│  به outbox می‌رود (هر پلتفرم یک ردیف، idempotent)               │
│         ↓                                                        │
│  اگر OwnerRelease فعال → انتشار خودکار با rate limit            │
│  اگر نه → منتظر تأیید آری در پنل                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  جمع‌بندی هفتگی — چرخهٔ یادگیری                                  │
│                                                                  │
│  metrics_puller: عدد هر پلتفرم را می‌گیرد                       │
│         ↓                                                        │
│  مقایسه: حس سبا × عدد پلتفرم × ترند هفته                        │
│         ↓                                                        │
│  «حس بالا · عدد پایین → زمان انتشار؟»                          │
│  «حس پایین · عدد بالا → بیشتر بسازی؟»                           │
│         ↓                                                        │
│  خوراک research_focus هفتهٔ بعد (شکاف‌ها)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ۳) ده سبک بازاریابی (rotation هفتگی)

این فهرست از تحقیق ۲۰۲۶ است. هر هفته یکی برجسته می‌شود (rotation یا best-fit با ترند آن هفته).

| # | سبک | فرضهٔ عملی برای سبا | سختی پلتفرمی |
|---|---|---|---|
| ۱ | **Teaser/Promo** | glimpse از شوت جدید → لینک در bio به پلتفرم پولی | نیاز به funnel غیرمستقیم (بدون لینک مستقیم OnlyFans در IG/TikTok) |
| ۲ | **آموزشی/How-to** | «پدیکرور خانگی»، «یوگای پای» | همه پلتفرم‌ها OK — این ایمن‌ترین فریمینگ |
| ۳ | **Behind-the-Scenes** | setup نور، انتخاب لنز، ویرایش | همه OK |
| ۴ | **UGC/Repost** | feedback مشتری (با اجازه) | نیاز به رضایت مشتری هم |
| ۵ | **Email Newsletter** | خبرنامه هفتگی + محتوای انحصاری | کامل آزاد، حیاتی برای فرار از shadowban |
| ۶ | **Paid Ads** | amplification | 🔴 تقریباً همه رد می‌کنند feet/adult → فقط affiliate/neutral |
| ۷ | **SEO/Blog** | «best foot care routine 2026» | دیرپا، رتبه چندساله |
| ۸ | **Affiliate** | لینک referral به FeetFinder/FunWithFeet | خارج از پلتفرم‌های اصلی |
| ۹ | **Collaboration/Duo** | cross-post با pedicure artist | نیاز به پارتنر |
| ۱۰ | **Community-Building** | Telegram channel برای fans | کامل آزاد، monetization بالا |

---

## ۴) ده کانال پلتفرم + یک کانال مالکیت‌شده (ایمیل)

جدول کامل از تحقیق. **دو لایه:** API-ready (خودکار) و manual-queue (صف، آری/سبا دستی منتشر می‌کند).

| پلتفرم | API خودکار | محدودیت/روز | محتوای feet | لایه |
|---|---|---|---|---|
| **Telegram Channel** | ✅ رایگان | ~uncapped | آزاد | API |
| **Bluesky** | ✅ رایگان | ~۱۶۶۶/h | آزاد | API |
| **Email (SES)** | ✅ | reputation | آزاد | API |
| **X/Twitter** | ✅ pay-per-use | ~$0.015/post | تا حدی آزاد | API (با بودجه) |
| **YouTube Shorts** | ✅ | ~۶/روز (quota) | آموزشی OK | API |
| **Threads** | ✅ | ~۲۵۰/روز | خاکستری | API |
| **Pinterest** | ✅ (review) | متوسط | beauty OK | API (با review) |
| **Reddit** | ✅ محدود | sub-specific | sub-specific | API (محتاط) |
| **Instagram Reels** | ✅ (app review) | ~۱۰۰/۲۴h | خاکستری — fetish framing banned | API (با review + re-framing) |
| **TikTok** | ✅ (audit) | ۲۵/روز | خاکستری — ineligible for FYP | API (با audit + re-framing) |
| **Facebook** | ✅ | ~۲۵/روز | خاکستری | API (با review) |
| **LinkedIn** | ❌ | — | ❌ نامناسب | حذف |

**استراتژی re-framing برای محتوا خاکستری:** همهٔ captionها در فریم «wellness/beauty/educational» می‌مانند. هیچ لینک مستقیم به پلتفرم پولی. funnel از طریق link-in-bio جداگانه.

---

## ۵) منابع دادهٔ ترند (pipeline تحقیق)

از تحقیق ۲۰۲۶. هر هفته موازی کوئری می‌شوند:

| منبع | نقش | هزینه |
|---|---|---|
| **Google Trends API (alpha)** | حجم جستجو زمانی | رایگان (alpha) |
| **TikTok Creative Center** | trending hashtags/sounds | رایگان |
| **Exploding Topics** | ترند قبل از mainstream | ~پولی |
| **YouTube/X Trending** | native | رایگان |
| **Reddit (subs مرتبط)** | پالس جامعه‌ای | رایگان (API) |

**قاعدهٔ سخت (از STUDIO-ANSWERS §۴):** هر یافتهٔ ترند باید **تاریخ مشاهده + تعداد مشاهده** حمل کند. نه پیش‌بینی قطعی.

---

## ۶) فازبندی — ترتیب کار (پیشنهاد برای ایجنت‌ها)

> ⚠️ ترتیب مهم است. هر فاز به قبلی وابسته است.

### فاز M۰ — پیش‌نیازها (بدون این، هیچ‌چیز کار نمی‌کند)
- [ ] باز کردن gate `secret_rotation` (چرخش ۴ راز CRITICAL)
- [ ] ساخت ۴ بات تلگرام + تنظیم Menu Button
- [ ] ثبت `OFN_OWNER_USER_IDS` و allowlistها
- [ ] اجرای `brain-probe.py` + calibration latency واقعی
- [ ] فعال‌سازی NTP
- [ ] حل معمای `app.master-painting.com` (بیرون ۴۰۴)
- [ ] **ثبت پیش‌شرط انتشار** (`partner_precondition`) — باید صریح تعریف شود

### فاز M۱ — ستون فشرده (هستهٔ سخت، بدون پلتفرم)
این فاز بدون سبا هم قابل ساخت است:
- [ ] `marketing_scout.py` — analog `scout.py` (Candidate = trend، Constraints = platform matrix، Memory = رد‌کردها)
- [ ] `trend_sources.py` — آداپتور Google Trends + TikTok CC + Exploding Topics
- [ ] `platform_matrix.py` — کدام پلتفرم چه محتوایی را می‌پذیرد (به‌عنوان dataclass نه پرامپت)
- [ ] `content_router.py` — یک محتوا → نسخهٔ هر پلتفرم
- [ ] `release_switch.py` — کلید رهایی مالک
- [ ] توسعهٔ `studio_store.py`: جدول `posts` و `metrics` (سری زمانی) — طرح در brief §۶
- [ ] تست‌های ساختاری: kernel purity، tenancy isolation، risk one-way

### فاز M۲ — آداپتورهای پلتفرم (سه لایه از آزاد به سخت)
- [ ] **لایهٔ A (آزاد، رایگان):** Telegram channel، Bluesky، Email → اول این‌ها
- [ ] **لایهٔ B (با review):** YouTube، X، Threads → بعد از A
- [ ] **لایهٔ C (با re-framing + review):** Instagram، TikTok، Facebook، Pinterest، Reddit → آخر
- [ ] هر آداپتور: OAuth، rate limit، idempotency، logging در ledger

### فاز M۳ — رابط سبا + چرخهٔ هفتگی
- [ ] ویوی «مارکتینگ هفته» در `studio.html`
- [ ] سؤال از سبا: «این هفته سبک X، ترند Y. کدام ایده؟»
- [ ] جمع‌آوری felt_right قبل از دیدن عدد (STUDIO-ANSWERS §۳)
- [ ] cron هفتگی دوشنبه ۰۳:۱۷ (بعد از backup)

### فاز M۴ — چرخهٔ یادگیری
- [ ] `metrics_puller.py` — API analytics هر پلتفرم
- [ ] مقایسهٔ حس × عدد × ترند
- [ ] خوراک research_focus هفتهٔ بعد
- [ ] داشبورد در panel.html

### فاز M۵ — اتوماسیون کامل (آخر، با کلید مالک)
- [ ] فعال‌سازی release_switch (با تأیید دو مرحله‌ای آری)
- [ ] انتشار خودکار با guardrails
- [ ] kill-switch و monitoring
- [ ] تست قطع برق با انتشار در صف

---

## ۷) ریسک‌ها و آنچه باید بدانیم

### ۷-۱) ریسک‌های پلتفرمی
- **Shadowban/ban:** Instagram و TikTok حساب‌های feet را بدون هشدار بسته‌اند. mitigation: framing wellness، حساب‌های business جداگانه، backup حساب.
- **API revoke:** app review ممکن است رد شود (به‌ویژه برای feet). mitigation: شروع از لایهٔ A آزاد.
- **سن قانونی استرالیا:** Online Safety Amendment (Minimum Age 16) و Phase 2 Codes 202۶. سن فالوور قابل اثبات نیست → ریسک قانونی.

### ۷-۲) ریسک‌های سیستم
- **انتشار خودکار = ریسک واقعی.** یک باگ در content_router یعنی caption نامناسب در ۱۰ پلتفرم هم‌زمان. mitigation: هر نسخه با platform_matrix screen می‌شود قبل از outbox.
- **هزینه مغز:** بدون brain-probe، اعداد تخمینی. fugu-ultra هفتگی می‌تواند گران باشد.
- **نشست تلگرام بدون کلید رهایی:** اگر OwnerRelease خاموش باشد، همه چیز در outbox انباشته می‌شود.

### ۷-۳) ریسک‌های انسانی
- **سبا منبع محدود است.** اگر بار اول تجربهٔ بد ببیند، باز نخواهد گشت. (از ARI-STUDIO-STEPS گام ۷)
- **حس سبا مهم‌تر از عدد است.** اگر بعد از عدد پرسیده شود، دیگر حس او نیست.

---

## ۸) سؤالات باز برای ایجنت‌های موازی

این‌ها را ایجنت‌های تخصصی باید حل کنند. هر کدام یک scope مجزاست:

1. **ایجنت معماری:** نگاشت دقیق `scout.py` → `marketing_scout.py`. کدام فیلدها باید عوض شوند؟ (hardware_classes → content_styles، age_weeks → trend_recency و غیره). تمام پیاده‌سازی.

2. **ایجنت پلتفرم:** مشخصات فنی دقیق OAuth و endpoint هر پلتفرم در لایهٔ A (Telegram/Bluesky/Email). نمونهٔ کد هر آداپتور.

3. **ایجنت ترند:** یکپارچه‌سازی Google Trends alpha + TikTok CC + Exploding Topics. قواعد screen سخت (چه چیزی رد می‌شود).

4. **ایجنت رابط:** طراحی ویوی «مارکتینگ هفته» در studio.html — چه سؤالی از سبا، چه تصمیمی، چطور felt_right را قبل از عدد بگیرد.

5. **ایجنت ریسک:** guardrails انتشار خودکار. چه‌چیز اگر content_router باگ داشته باشد؟ اگر consent data خراب باشد؟

6. **ایجنت قانون:** مسائل Online Safety Amendment استرالیا + سیاست هر پلتفرم برای feet content. آیا نیاز به age-gating است؟

---

## ۹) آنچه این پلن **نمی‌کند** (مرزها)

- محتوای `restricted` هرگز خودکار نمی‌رود (ساختاری از `advisor_gate`)
- هیچ پیش‌بینی قطعی ترند (فقط مشاهده‌شده با تاریخ/تعداد)
- بدون رضایت معتبر، هیچ انتشار
- بدون باز بود gateهای پیش‌نیاز، فعال‌سازی release_switch ممکن نیست
- LinkedIn حذف شد (نامناسب)
- محتوای nudity کامل (بیرون از scope — تو گفتی نیست)

---

## ۱۰) تعریف «آماده برای کدنویسی»

این پلن وقتی آمادهٔ کدنویسی است که:
1. آری تصمیمات فاز M۰ را تأیید کند (به‌ویژه تعریف partner_precondition)
2. هر کدام از ۶ سؤال باز فاز ۸ توسط ایجنت تخصصی پاسخ داده شود
3. بودجهٔ مغز (پس از brain-probe) مشخص شود
4. ترتیب فازها تأیید شود

آن‌وقت کدنویسی فاز به فاز، با تست‌های ساختاری (kernel purity، tenancy، risk one-way، consent)، شروع می‌شود.

---

> **پایان v0.1.** منتظر بازخورد آری و خروجی ۶ ایجنت موازی.
