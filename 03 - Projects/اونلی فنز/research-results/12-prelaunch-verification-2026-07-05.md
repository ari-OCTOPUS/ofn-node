---
created: 2026-07-05
updated: 2026-07-05
status: draft-for-human-review
type: research
tags: [project-f, verification, prelaunch]
---

# 12 — Pre-Launch Live Verification Sprint (2026-07-05)

> اجرای Prompt 3 از PROMPTS-2026-07-05.md. هدف: بستن آیتم‌های «verify at execution time» از STATE-REPORT §6–§7 با چک زنده وب، قبل از Day-Zero.
> روش: فقط desk research — هیچ اکانتی ساخته نشد، هیچ پیامی ارسال نشد. هر ادعا: منبع + تاریخ fetch + تگ [FACT]/[EST]/[SPEC]/[BLOCKED].
> محدودیت محیط: reddit.com و برخی دامنه‌ها در fetch-blocklist این محیط هستند؛ آیتم‌های مربوطه صادقانه [BLOCKED — چک دستی] علامت خورده‌اند.

---

## ۱. جدول verdict — سیاست و قیمت پلتفرم‌ها (Block 3)

| # | آیتم | مقدار قبلی (fresh-scan 07-04) | مقدار زنده (07-05) | Verdict | منبع |
|---|---|---|---|---|---|
| 1 | **Social Rise** | $29.99 = ۱۰۰۰ پست، اکانت نامحدود، free=۵ | **عیناً همان**: $29.99/mo per 1000 posts · yearly $143.91 (−۲۵٪) · free ۵ پست/ماه · همه فیچرها در همه پلن‌ها · unlimited accounts · proxyهای rotating · autoresponder | ✅ CONFIRMED [FACT] | social-rise.com/pricing (صفحه رسمی، fetch 2026-07-05) |
| 2 | **Postpone** | گران شد: $25/$49/$99 | صفحه pricing با JS رندر می‌شود — fetch ناقص؛ منابع ثانویه همان tierها | ⚠️ INCONCLUSIVE [EST] — بی‌اثر (Social Rise انتخاب شده) | postpone.app/pricing (fetch 07-05، body خالی) |
| 3 | **OF حداقل payout** | $20 [FACT]؛ ادعای $10 فقط thecreatorreport.co → [SPEC] جعلی | ادعای «$10 از 2026-04-01» حالا در ۵+ بلاگ affiliate تکرار می‌شود (pleazeme، onlygems، luvi و…) اما **همچنان صفر منبع رسمی OF یا رسانه معتبر**؛ همه رد به همان thecreatorreport.co می‌رسند. جستجوی site:onlyfans.com هیچ تأییدی نداشت | 🔶 UNCHANGED [SPEC] — «echo spread» بیشتر شده ولی اثبات نه. حکم fresh-scan پابرجا: **چک داشبورد در launch** | WebSearch 07-05 |
| 4 | **Fansly** | ۲۰٪ ثابت + FYP؛ payout min $100 (Playbook) | ۸۰/۲۰ تأیید · حداقل payout: **$20 (Paxum/crypto) / $100 (bank transfer)** — عدد Playbook فقط برای bank درست است · pending ۷ روز، پرداخت ۱–۲ روز کاری · geo/location-blocking موجود | ✅ CONFIRMED + دقیق‌تر [EST — منابع ثانویه متعدد همسو] | fans-alternative.com، sozee.ai، onlygemsmanagement.com (07-05) |
| 5 | **GetAllMyLinks** | پلن Creator $9 + Geo Filter | Creator **$9/mo** (سالانه −۲۰٪) · **Geo Filter موجود و مستند**: block/redirect بر اساس کشور/شهر/region، فقط در پلن Creator/Agency · Agency $29 · هر دو ۱۴ روز trial | ✅ CONFIRMED [FACT] | help.getallmylinks.com «What is the Geo Filter»، try.getallmylinks.com/pricing (07-05) |
| 6 | **X — برنامه ACC** | جعلی؛ صفحه رسمی هنوز May 2024 | صفحه رسمی Adult Content Policy **هنوز «May 2024»** است (fetch مستقیم) — هیچ برنامه ID-verification برای creatorها اضافه نشده. تعریف Adult Content: برهنگی/رفتار جنسی → **پای بدون برهنگی مشمول تعریف نیست**؛ الزام: media settings → sensitive ON، نه در avatar/banner | ✅ CONFIRMED [FACT] | help.x.com/en/rules-and-policies/adult-content (fetch 2026-07-05) |
| 7 | **SendX — AUP** | سازگار؛ نیازمند تأیید کتبی | ToS رسمی (updated 2025-01): **هیچ بند منع adult ندارد**؛ الزامات: opt-in خالص، بدون لیست خریداری‌شده، CAN-SPAM، محتوای متعلق به خودت. منابع ثانویه (adent.io، founderbounty): «SendX adult را می‌پذیرد اگر legal و consensual» | ✅ سازگار [FACT برای ToS، EST برای تفسیر] — ایمیل تأیید کتبی هنوز لازم (draft در §۵) | sendx.io/terms-and-conditions (fetch 07-05) |
| 8 | **FeetFinder — فی** | متناقض: 10/15/20٪ | Seller Agreement فعلی: **۱۵٪ فی (پلن Basic) / ۱۰٪ (Premium)** + اشتراک فروشنده **$4.99/mo یا $14.99/yr (Basic)** · **$14.99/mo یا $49.99/yr (Premium)** · گزینه lifetime $40/$80. عدد ۲۰٪ متعلق به منابع قدیمی است | ✅ RESOLVED [EST — منبع رقیب tryfootly + ecommercefastlane همسو؛ تأیید نهایی at signup] | tryfootly.com fee-breakdown، rewarble.com (07-05) |
| 9 | **Fanvue — بند مصادره** | مصادره موجودی بی‌حرکت بعد ۱۲ ماه | تأیید از **صفحه legal رسمی**: بعد از ۱۲ ماه بدون payout → Dormant (۲ یادآوری ~ماه ۹ و ۱۱) → حق دریافت «irrevocably waived»؛ بازپرداخت late claim تا ۶ سال فقط discretionary | ✅ CONFIRMED و حتی سفت‌تر [FACT] | legal.fanvue.com/creator-earnings-payouts (07-05) |
| 10 | **AU compliance** | ARM codes از 2026-03-09 + ban زیر ۱۶ | تدقیق تقویم: SMMA (زیر ۱۶) اجرایی از **2025-12-10**؛ eSafety تا حالا ۲۳ notice به ۱۰ پلتفرم؛ جریمه تا $54.6M (سمت پلتفرم) · ARM codes ثبت‌شده؛ age assurance برای search engineها تا **2026-06-27** (گذشته) و app storeها تا **2026-09-09** | ✅ CONFIRMED — بار انطباق همچنان سمت پلتفرم؛ تکلیف ما همان برچسب‌گذاری + 18+ | esafety.gov.au (رسمی)، dlapiper، bakermckenzie (07-05) |

**جمع‌بندی Block 3:** هیچ عددی از بلوپرینت/Day-Zero باطل نشد. بودجه warm-up (GAML $9 ≈ AUD 13) و sprint (Social Rise $29.99) معتبر ماند.

---

## ۲. ماتریس تصمیم برند (Block 1)

روش: exact-phrase collision search در Google (07-05) + تلاش RDAP برای دامنه (این محیط body JSON را برنمی‌گرداند → [BLOCKED]). چک مستقیم handle در X/IG/TikTok از این محیط ممکن نیست (JS/login) → [DEFER-TO-SIGNUP]. Trademark: جستجوی IP Australia فقط دستی ممکن است → [DEFER].

| کاندید | Collision یافت‌شده | شدت | Discoverability | Verdict اولیه |
|---|---|---|---|---|
| **Anar Soles** | هیچ برند/creator فعالی نه؛ نزدیک‌ترین‌ها بی‌ربط (ابزار پدیکور «ANSR Sole»، عبارت کاتالان «a soles») | ندارد | بالا (عبارت یکتا) | 🟢 **CLEAR — قوی‌ترین گزینه** |
| **Yalda Arch** | هیچ entity؛ فقط اشخاص با نام Yalda + مدارک M.Arch | ندارد | بالا | 🟢 CLEAR |
| **Arch & Amber** | عکسِ نام: **Amber Arch** — شرکت بریتانیایی mystery-shopping از ۱۹۹۵ (amberarch.com، Trustpilot فعال) + دکور «Amber Arch» | کم (صنعت کاملاً متفاوت؛ ولی «Amber Arches Co.» واریانت Playbook خیلی نزدیک است) | متوسط | 🟡 RISKY-LOW |
| **The House Red** | برند مستقیمی نه، ولی «house red» عبارت generic شراب → SEO/جستجو همیشه wine برمی‌گرداند؛ trademark ضعیف | متوسط (نه حقوقی، بلکه یافت‌ناپذیری) | پایین | 🟡 RISKY (discoverability) |
| Saffron Steps (رزرو) | فقط محتوای آشپزی/کشت زعفران؛ برند نه | ندارد | متوسط (نویز generic) | 🟢 CLEAR-ish |

**پیشنهاد `[OPINION]`:** ‏**Anar Soles** #1 (صفر collision + یکتایی جستجو + لور آماده «anar means pomegranate — that's all you get») · رزرو: Yalda Arch. ‏«Arch & Amber» به‌دلیل همسایگی با amberarch.com و «The House Red» به‌دلیل genericness یک پله پایین. تصمیم نهایی = دونفره + چک handle در لحظه ساخت اکانت (Day-Zero ردیف ۷/۸) و جستجوی دستی IP Australia (~۵ دقیقه).

---

## ۳. وضعیت audit ردیت (Block 2) — [BLOCKED برای چک زنده]

- ‏reddit.com در fetch-blocklist این محیط است؛ ابزارهای ثانویه (subredditstats.com) بعد از API pricing ردیت **مرده/stale** هستند — پس audit زندهٔ ۲۵ sub از این محیط ممکن نیست.
- این دقیقاً همان چیزی است که P3 §Limitations خودش پیش‌بینی کرده بود: «قوانین دقیق subها فقط داخل اپ قابل‌راستی‌آزمایی است».
- **سیگنال جدید و مهم [EST — منبع stale]:** صفحه subredditstats برای r/VerifiedFeet برچسب «**This subreddit is quarantined**» دارد. اگر هنوز quarantined باشد، discovery ارگانیک آن به‌شدت محدود است → رتبه «هسته ۱» آن زیر سؤال می‌رود. **اولین چک in-app باید همین باشد.**
- راهنماهای ثانویه ۲۰۲۶ همچنان قاعده «۳–۷ sub در روز، نه بیشتر» P3 را تأیید می‌کنند (tryfootly 2026).
- **اقدام:** چک‌لیست دستی ۲۵ sub (قالب P3 §۳) در **هفته warm-up داخل اپ Reddit** انجام شود — ~۴۵ دقیقه؛ ستون‌ها: exists? / member count / verification؟ / لینک خارجی؟ / آخرین پست. تا آن موقع rank های P3 فقط [EST].

---

## ۴. Patch list — اصلاحات مشخص در اسناد

1. **STATE-REPORT §6، ردیف «OF minimum payout»:** بدون تغییر ($20 [FACT] / $10 [SPEC]) — فقط یادداشت «echo spread در بلاگ‌های affiliate؛ همچنان بدون منبع رسمی، 07-05» اضافه شود. ✔ همین سند مرجع است.
2. **STATE-REPORT §6، ردیف «FeetFinder fees»:** RESOLVED → «۱۵٪ Basic / ۱۰٪ Premium + sub $4.99–14.99/mo؛ عدد ۲۰٪ outdated». ✔
3. **Playbook §8.3:** ‏«Fansly payout min $100» → دقیق شود: «$20 Paxum/crypto، $100 bank».
4. **بلوپرینت §۵ (Day-Zero):** اعداد GAML ($9) و ترتیب بدون تغییر معتبر. ردیف ۸ (Reddit): یک ساب‌آیتم اضافه شود: «چک وضعیت quarantine ‏r/VerifiedFeet قبل از شروع warm-up».
5. **بلوپرینت §۲ دلتا #7:** تقویم AU تدقیق: SMMA از 2025-12-10 اجرایی؛ ARM codes ثبت؛ ددلاین‌های age-assurance: search 2026-06-27 / app store 2026-09-09. اثر بر ما: هیچ (بار سمت پلتفرم).
6. **MONETIZATION M-لایه Fanvue:** بند Dormant رسماً تأیید شد — قاعده «برداشت حداقل سالانه» از توصیه به **قاعده سخت** ارتقا یابد.

---

## ۵. Draft ایمیل تأیید SendX (ارسال نشده — فقط draft)

> Subject: Pre-sales question — content policy for 18+ creator newsletter
>
> Hi SendX team,
> I'm evaluating SendX for a small opt-in newsletter for an 18+ content-creator brand (legal, consensual, feet-focused content; no explicit imagery inside emails — text + links to age-gated platforms). All contacts are double-opt-in, CAN-SPAM/GDPR compliant, content fully owned by us.
> Before subscribing I'd like written confirmation: does your Acceptable Use Policy permit this use case? Is there anything specific (content, links, imagery) we should avoid to stay compliant?
> Thanks, [brand alias]

ارسال: فقط بعد از ساخت ایمیل برند (Day-Zero ردیف ۱) و از همان آدرس.

---

## ۶. Confidence & Coverage

1. **چک زنده موفق (رسمی):** social-rise.com، help.x.com، sendx.io، legal.fanvue.com (via search snippet)، esafety.gov.au (via search) — بالاترین اطمینان.
2. **منابع ثانویه همسو:** Fansly، FeetFinder، GAML — [EST]، تأیید نهایی at signup.
3. **BLOCKED:** reddit.com (blocklist محیط)، RDAP/domain (body خالی)، IP Australia (JS) → چک دستی ~۱۵ دقیقه با مرورگر خودت.
4. **مهم‌ترین یافته تغییردهنده:** سیگنال quarantine ‏r/VerifiedFeet (رتبه ۱ هستهٔ P3) — اگر تأیید شود، وزن sub های هسته باید بازچینی شود.
5. **مهم‌ترین عدم-تغییر:** کل اعداد بودجه Day-Zero/sprint معتبر ماندند؛ ادعای OF $10 همچنان [SPEC].
