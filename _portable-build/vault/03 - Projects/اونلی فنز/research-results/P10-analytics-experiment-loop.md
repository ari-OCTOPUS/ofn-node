---
type: research-report
prompt: P10
project: Project-F
created: 2026-07-04
status: draft-for-human-review
tags: [project-f, research, research-grounded]
up: "[[PROJECT]]"
---

# P10 — لایه اندازه‌گیری، Attribution و حلقه آزمایش هفتگی برای Project-F

**هدف:** ساخت لایه اندازه‌گیری (measurement layer) برای فاز اعتبارسنجی (validation) با اعداد بسیار کوچک، بودجه سقف AUD 200/ماه و تیم دونفره. نرخ تبدیل ارز در این گزارش: ‏1 USD ≈ 1.45 AUD ‏[FACT] (منبع: exchangerates.org.uk، ۲۰۲۶-۰۷-۰۳).

**اصول حاکم:** فقط تاکتیک‌های سازگار با ToS؛ حذف کامل ایران (geo-block)؛ ناشناس‌ماندن سازنده؛ محرمانگی خریدار. هر ادعا با [FACT]/[EST]/[OPINION] برچسب خورده است.

---

## ۱. قابلیت‌های Tracking داخلی پلتفرم‌ها و محدودیت‌ها

### OnlyFans
- [FACT] OnlyFans قابلیت **Tracking Links** دارد: از مسیر Settings → Tracking Links ساخته می‌شود؛ برای هر لینک، **کلیک‌ها، فن‌های جدید (subscription) و conversion rate** و همچنین درآمد/خرج فن‌ها را نمایش می‌دهد. Attribution از نوع **last-click** است. (منبع: supercreator.app/guides/onlyfans-tracking-links، به‌روزرسانی ۲۰۲۶-۰۲-۱۸؛ onlymonster.ai docs)
- [FACT] محدودیت‌ها: کلیک‌هایی که کاربر ساعت‌ها بعد یا از دستگاه دیگر subscribe کند ممکن است ثبت نشوند (شکاف cross-device / delayed attribution). (همان منبع، ۲۰۲۶-۰۲-۱۸)
- [FACT] آمار بومی OnlyFans (بخش Stats) محدود است: درآمد تخمینی، تعداد subscriber، لایک و بازدید پست — اما **profile visit به‌صورت funnel کامل گزارش نمی‌شود**. (منبع: help.creatorhero.com «OnlyFans Statistics»؛ fanso.io/blog/onlyfans-metrics-to-track، بازیابی ۲۰۲۶-۰۷-۰۴)
- [FACT] Geo-blocking از مسیر Settings → Privacy & Safety → Geo Blocking انجام می‌شود؛ **ایران را باید همان روز اول مسدود کرد**. محدودیت شناخته‌شده: VPN می‌تواند آن را دور بزند (خارج از کنترل ما؛ هیچ راه‌حلی برای دور زدن پیشنهاد نمی‌شود). (منبع: pippinclub.com/blog/guide-to-onlyfans-geoblocking؛ arunatalent.com، بازیابی ۲۰۲۶-۰۷-۰۴)
- [EST] «Free trial links» به‌عنوان ابزار attribution ثانویه (لینک آزمایشی مجزا برای هر کانال) در راهنماهای متعدد ذکر شده، اما جزئیات فعلی باید هنگام راه‌اندازی داخل داشبورد به‌صورت دستی تأیید شود. ⚠️ نیاز به تأیید دستی.

### Fansly (پلتفرم جایگزین ۱)
- [FACT] Fansly از حدود مارس ۲۰۲۵ **tracking links** ارائه می‌دهد؛ برای هر کانال/کمپین لینک مجزا، با گزارش کلیک و conversion. (منبع: creatorsspicytea.co/tracking-links، انتشار ۲۰۲۵-۰۳-۱۱)
- [FACT] داشبورد Fansly تفکیک traffic source (FYP، Search، Suggestions) هم دارد — یعنی discovery داخلی پلتفرم از ترافیک بیرونی قابل تفکیک است. (منبع: infloww.com/blog/fansly-analytics-101، بازیابی ۲۰۲۶-۰۷-۰۴)
- [OPINION] کاربرد عملی: tracking link مجزا برای هر پلتفرم + مقایسه هفتگی؛ افت ناگهانی ترافیک یک کانال، سیگنال shadowban همان کانال است. (creatorsspicytea، ۲۰۲۵-۰۳-۱۱)

### Fanvue (پلتفرم جایگزین ۲)
- [FACT] Fanvue قابلیت Tracking Links با **تعداد نامحدود لینک** دارد (Creator Settings → Tracking Links). (منبع: help.fanvue.com مقاله 11363166، ۲۰۲۵-۰۵-۱۲)
- [FACT] «AI Analytics» فن‌وی شامل تفکیک درآمد (renewals، PPV، tips) و **موقعیت جغرافیایی فن‌ها** است — برای پایش رعایت حذف ایران مفید است. (منبع: help.fanvue.com مقاله 9539478، ۲۰۲۵-۰۶-۲۴)

**جمع‌بندی [OPINION]:** هر سه پلتفرم tracking link بومی دارند و برای فاز اعتبارسنجی «به‌ازای هر کانال یک لینک» کافی است. ضعف مشترک: attribution از نوع last-click، بدون دید بالادستی (impression تا کلیک) — این حفره را باید با آمار بومیِ شبکه‌های اجتماعی و یک spreadsheet پر کرد.

---

## ۲. ابزارهای Link Shortener / Link-in-Bio و سیاست محتوای بزرگسال

| ابزار | سیاست محتوای بزرگسال | قیمت | حکم برای Project-F |
|---|---|---|---|
| **AllMyLinks** | [FACT] پذیرای لینک‌های NSFW؛ الزام: بخش «+18» اجباری، ممنوعیت لینک escort و ممنوعیت فروش مستقیم محتوای بزرگسال روی خود صفحه (منبع: creator-hero.com؛ premium.chat؛ sirency.com، بازیابی ۲۰۲۶-۰۷-۰۴) | [FACT] پلن رایگان؛ پلن‌های پولی از ~USD 5/ماه؛ پلن Creator با آنالیتیکس و دامنه اختصاصی ~USD 9/ماه (≈ AUD 13) (منبع: creatoreconomytools.com، بازیابی ۲۰۲۶-۰۷-۰۴) | ✅ انتخاب اصلی (hub میانی + شمارش کلیک) |
| **Linktree** | [FACT] لینک به محتوای بزرگسالِ قانونی مجاز است اگر برچسب sensitive بخورد؛ آپلود رسانه بزرگسال و دریافت پول بابت محتوای بزرگسال روی خود Linktree ممنوع. [FACT] سابقه حذف گسترده حساب‌های sex worker (Vice، ۲۰۲۲) → ریسک enforcement ناگهانی | [FACT] Free / Starter USD 8 / Pro USD 15 / Premium USD 35 ماهانه (≈ AUD 0/12/22/51)؛ افزایش قیمت نوامبر ۲۰۲۵ (منابع: linktr.ee/s/about/community-standards؛ talkspresso.com، بازیابی ۲۰۲۶-۰۷-۰۴) | ⚠️ گزینه پشتیبان؛ ریسک متوسط بسته‌شدن صفحه |
| **Beacons.ai** | [FACT] ممنوعیت صریح NSFW/sexually explicit (شامل subscription سایت‌های بزرگسال) در Community Standards (منبع: beacons.ai/i/beacons-community-standards، بازیابی ۲۰۲۶-۰۷-۰۴) | Free / پولی | ❌ استفاده نشود — ریسک ban بالا |
| **Bitly** | [FACT] AUP محدودکننده؛ محتوای explicit غیرهم‌رضایتی صراحتاً ممنوع و اختیار گسترده برای حذف هر لینک «مضر»؛ در عمل برای لینک‌های adult قابل‌اتکا نیست (منبع: bitly.com/pages/acceptable-use، بازیابی ۲۰۲۶-۰۷-۰۴) | Free محدود / پولی | ❌ استفاده نشود |
| **Short.io** | [FACT] ToS صراحتاً redirect به محتوای «pornographic» را ممنوع کرده (بخش 10 Acceptable Use) (منبع: short.io/terms، نسخه ۲۰۲۳-۰۳-۳۱، بازیابی ۲۰۲۶-۰۷-۰۴) | Free / از USD 5 | ❌ استفاده نشود |
| **YOURLS (self-hosted)** | [FACT] متن‌باز (MIT)، روی دامنه و سرور خودمان؛ هیچ policy بیرونی روی محتوا اعمال نمی‌شود؛ آمار کلیک، referrer و geo دارد (منبع: yourls.org؛ github.com/YOURLS، بازیابی ۲۰۲۶-۰۷-۰۴) | [EST] دامنه ~USD 10/سال + VPS کوچک ~USD 4–6/ماه (≈ AUD 6–9/ماه) | ✅ گزینه حرفه‌ای‌تر برای UTM/کوتاه‌کننده بدون ریسک policy |
| **Google Analytics (GA4)** — برای landing page اختیاری | [FACT] ToS سایت‌ها را بر اساس موضوع رد نمی‌کند (adult ممنوع نیست)، اما اکوسیستم Ads برای adult بسته است؛ برای صرفاً آمار بازدید قابل استفاده (منبع: seroundtable.com/archives/013611.html؛ marketingplatform.google.com/about/analytics/terms، بازیابی ۲۰۲۶-۰۷-۰۴) | Free | ⚠️ فقط اگر landing page مستقل ساختیم؛ با ایمیل مستعار |
| **Plausible Analytics** | ⚠️ سیاست adult در جست‌وجو تأیید نشد — پیش از خرید باید ToS بررسی دستی شود | [FACT] از USD 9/ماه (≈ AUD 13) (منبع: omr.com/en/reviews، ژوئن ۲۰۲۶) | ⚠️ جایگزین حریم‌خصوصی‌محور GA؛ نیاز به تأیید دستی |

**نکته ناشناسی [OPINION]:** اگر دامنه اختصاصی می‌خرید (برای YOURLS یا AllMyLinks)، حتماً WHOIS privacy فعال و ثبت با ایمیل/نام مستعار برند انجام شود؛ هیچ ابزاری که ID واقعی بخواهد وارد stack نشود.

---

## ۳. Deliverable 1 — تعریف KPIها + آستانه‌های فاز اعتبارسنجی

قیف کامل: **Impression → Profile Visit → Link Click → Free Follow / Email → Paid Sub → Revenue per Fan**

| مرحله قیف | تعریف دقیق | منبع داده | Benchmark نزدیک‌ترین نیش [EST] | آستانه اعتبارسنجی Project-F [OPINION] |
|---|---|---|---|---|
| Impressions | تعداد نمایش پست در هر کانال | [FACT] Reddit Post Insights (views، upvote rate، share؛ داده بعد از ۴۵ روز پاک می‌شود — هفتگی یادداشت شود؛ منبع: support.reddithelp.com، بازیابی ۲۰۲۶-۰۷-۰۴)؛ X Analytics | — | ثبت هفتگی؛ هدف حجمی نه کیفی |
| Profile visit | بازدید پروفایل شبکه اجتماعی | آمار بومی X/IG | — | نسبت visit/impression >2% خوب [EST] |
| Link click | کلیک روی لینک hub یا tracking link | AllMyLinks + OF Tracking Link | [EST] X organic CTR ‏0.5–1.5% (webeyez.com، بازیابی ۲۰۲۶-۰۷-۰۴)؛ IG bio-link فقط 0.1–0.5% بازدیدکنندگان پروفایل (inro.social، به‌روزرسانی ۲۰۲۶-۰۵-۰۵ — داده vendor، سوگیری تبلیغاتی) | ≥50 کلیک/هفته تا پایان ماه ۲ |
| Free follow | subscriber صفحه رایگان OF | OF Tracking Links | [EST] Reddit click→sub ‏8–12% و profile-click→sub ‏5–10% (arunatalent.com؛ desirely.co، ۲۰۲۶ — بلاگ آژانسی، خوش‌بینانه) | ‏10–20% از کلیک‌ها |
| Email capture (اختیاری) | ایمیل از landing page | فرم/ESP | [EST] 2–5% بازدید→ایمیل (عمومی صنعت) | فاز ۲؛ در اعتبارسنجی اجباری نیست |
| Paid sub / خریدار PPV | فن پرداخت‌کننده | OF Stats + Tracking Link | [EST] free→paid ‏5–15%؛ ‏10%+ عملکرد خوب (arunatalent.com، بازیابی ۲۰۲۶-۰۷-۰۴) | ≥5% از free followها در ۳۰ روز |
| Revenue/fan (ARPF) | درآمد ماهانه ÷ کل فن‌ها | OF Stats | [EST] ARPS >USD 5/ماه برای صفحه رایگان «سالم» (arunatalent) ؛ درآمد نیش feet: مبتدی USD 150–500/ماه (tryfootly.com؛ ecommercefastlane.com، ۲۰۲۶) | >USD 3 در فاز اعتبارسنجی |

[OPINION] در فاز صفر-مخاطب، KPI اصلی هفته‌های ۱–۴ فقط **Link Click** و **Free Follow** است؛ paid sub قبل از ~۱۰۰ کلیک تجمعی سیگنال قابل‌اتکایی نیست (بخش ۷).

---

## ۴. Attribution وقتی آنالیتیکس پلتفرم ضعیف است

1. **یک tracking link بومی به‌ازای هر کانال** (OF/Fansly/Fanvue) — ستون فقرات attribution. [FACT] قابلیت موجود است (بخش ۱).
2. **لایه میانی hub:** همه کانال‌ها → AllMyLinks (شمارش کلیک ورودی) → دکمه‌های خروجی که هرکدام tracking link مجزای OF هستند. اختلاف «کلیک hub» و «کلیک OF» = نشتی مرحله میانی. [OPINION]
3. **پارامترهای UTM** روی هر لینکی که به landing page یا hub می‌رود (utm_source=reddit و…) — فقط جایی که آنالیتیکس خودمان (GA4/Plausible/YOURLS) داریم خوانده می‌شود. [FACT]
4. **نظرسنجی welcome message:** در پیام خوش‌آمد OF بپرسید «از کجا ما را پیدا کردی؟» — روش رایج و مجاز برای attribution نرم. (منبع: social-rise.com/blog/onlyfans-welcome-message؛ ofagency.co، بازیابی ۲۰۲۶-۰۷-۰۴) [FACT]
5. **همبستگی زمانی:** جهش subscriber در پنجره ۲۴ ساعته بعد از هر پست، به همان پست/کانال نسبت داده شود؛ برای پست‌های مهم، لینک تازه بسازید تا baseline تمیز باشد. (supercreator.app، ۲۰۲۶-۰۲-۱۸) [FACT/توصیه]
6. **کد/آفر متمایز به‌ازای کانال** (مثلاً trial link مجزا برای Reddit) — دقیق‌ترین روش برای کانال‌های پرترافیک. [OPINION]
7. ❗ **ممنوع:** هر نوع scraping داده شخصی کاربران یا fingerprinting خریداران — هم خلاف ToS و هم خلاف اصل محرمانگی خریدار.

---

## ۵. Deliverable 2 — راهنمای گام‌به‌گام راه‌اندازی Tracking (روز ۰ تا ۷)

1. **روز ۰ — پایه پلتفرم:** در OnlyFans، Geo Blocking را باز کنید و ایران را مسدود کنید [FACT: قابلیت موجود]؛ همین کار در پلتفرم دوم (در Fanvue از گزارش location برای پایش استفاده کنید).
2. tracking link بسازید: `reddit-main`، `x-main`، `ig-teaser`، `tiktok-sfw`، `hub-direct` (ترافیک مستقیم hub) + یک لینک `promo-paid` برای هر shoutout پولی. نام‌گذاری: `کانال-کمپین-ماه` (مثل `reddit-solesfriday-jul`).
3. **AllMyLinks:** حساب با ایمیل مستعار برند؛ بخش +18 طبق قوانین؛ هر دکمه = tracking link مربوط به همان کانال (نه URL خام پروفایل). پلن رایگان کافی است؛ ارتقا USD 9/ماه فقط اگر آنالیتیکس عمیق‌تر لازم شد.
4. **بیو هر شبکه اجتماعی → لینک hub** (نه لینک مستقیم OF) — هم برای تفکیک، هم برای کاهش ریسک لینک مستقیم adult در IG/TikTok. [OPINION]
5. **Welcome message** با پرسش «از کجا پیدام کردی؟» + گزینه‌های کوتاه (R/X/IG/دیگر) تنظیم شود. [FACT: تاکتیک رایج مجاز]
6. **Spreadsheet هفتگی** (بخش ۶) را بسازید؛ یادآور تقویمی یکشنبه‌ها ۳۰ دقیقه «جلسه داده».
7. (اختیاری، ماه ۲+) دامنه مستعار + YOURLS برای کوتاه‌کننده اختصاصی؛ WHOIS privacy الزامی.
8. **هفتگی:** اعداد Reddit Insights را قبل از انقضای ۴۵روزه در شیت ثبت کنید [FACT: انقضا ۴۵ روز، support.reddithelp.com].

**هزینه کل stack پیشنهادی: از USD 0 تا ~USD 19/ماه (≈ AUD 0–28) — بسیار زیر سقف AUD 200.** [FACT بر اساس قیمت‌های بخش ۲]

---

## ۶. داشبورد: Spreadsheet در برابر ابزار پولی

- **پیشنهاد اصلی [OPINION]: Google Sheets/Excel رایگان.** در مقیاس <۱۰۰۰ کلیک/ماه، هیچ ابزار پولی ارزش افزوده واقعی ندارد.
  - **Tab 1 — Weekly Funnel:** ردیف = هفته×کانال؛ ستون‌ها: Posts, Impressions, Profile Visits, Hub Clicks, OF Clicks, Free Subs, Paid Subs, Revenue, ساعت کار صرف‌شده.
  - **Tab 2 — Experiment Log:** جدول بخش ۷.
  - **Tab 3 — Attribution Soft:** پاسخ‌های welcome survey (شمارنده ساده، بدون ذخیره داده شخصی).
- **ابزارهای CRM مثل Infloww (از ~USD 40/creator/ماه ≈ AUD 58؛ منبع: ofm-tools.com/infloww-review، بازیابی ۲۰۲۶-۰۷-۰۴) یا Supercreator:** [OPINION] برای فاز اعتبارسنجی زائد؛ فقط پس از عبور از ~USD 1k درآمد ماهانه بازبینی شود. سیاست این ابزارها adult-friendly است (ابزار مدیریت OF هستند) [FACT].
- **Plausible (USD 9/ماه)** فقط در صورت راه‌اندازی landing page مستقل — و پس از تأیید دستی ToS درباره adult. ⚠️

---

## ۷. Deliverable 3 — حلقه آزمایش هفتگی + تصمیم‌گیری با نمونه‌های آماری کوچک

### چارچوب (برای تیم ۲ نفره، حداکثر ۲ آزمایش هم‌زمان [OPINION])
**Hypothesis → تغییر تک‌متغیره → آستانه تصمیم از پیش ثبت‌شده → اجرا ۱–۲ هفته → Decision (Kill / Iterate / Scale)**

### صداقت آماری با اعداد کوچک
- [FACT] **قاعده سه (Rule of Three):** اگر در n مشاهده هیچ رویدادی رخ ندهد، سقف ۹۵٪ نرخ واقعی ≈ 3/n است. مثال: ۱۰۰ کلیک و صفر sub یعنی نرخ واقعی به‌احتمال ۹۵٪ زیر ۳٪ است. (منبع: en.wikipedia.org/wiki/Rule_of_three_(statistics)؛ statology.org، بازیابی ۲۰۲۶-۰۷-۰۴)
- [FACT] آزمون significance کلاسیک با ترافیک کم عملاً ناممکن است؛ رویکرد درست: تفکر Bayesian/sequential — از benchmark به‌عنوان prior شروع کنید و با داده به‌روز کنید؛ توقف زودهنگام فقط با شواهد قوی. (منابع: craftuplearn.com sequential testing guide؛ statsig.com/glossary/bayesian-ab-test؛ convert.com، بازیابی ۲۰۲۶-۰۷-۰۴)
- [OPINION] قواعد عملی Project-F:
  1. مقایسه کانال‌ها روی **متریک پرحجم** (کلیک) انجام شود، نه رویداد نادر (paid sub).
  2. قضاوت درباره نرخ click→sub قبل از **~۵۰ کلیک** ممنوع؛ درباره free→paid قبل از **~۳۰ free sub** ممنوع.
  3. اختلاف کمتر از ۲ برابر بین دو کانال با این حجم‌ها «نویز» فرض شود؛ فقط اختلاف‌های ≥۲–۳ برابری actionable است.
  4. هر آزمایش با **آستانه عددی مطلق** (نه درصدی) از پیش ثبت شود.
  5. **حساب بهره‌وری:** clicks per hour of effort هم ثبت شود — در تیم ۲ نفره، زمان گران‌ترین منبع است.
  6. runway سه‌ماهه = ۱۲ چرخه هفتگی: هفته‌های ۱–۲ راه‌اندازی، ۳–۸ آزمایش کانال‌ها، ۹–۱۲ تمرکز روی ۱–۲ کانال برنده.

### قالب پرشدنی (Experiment Log)

| فیلد | توضیح | مثال پرشده |
|---|---|---|
| Week / ID | شماره هفته و آزمایش | W5-E1 |
| Hypothesis | یک جمله قابل‌ابطال | «عنوان‌های سؤالی در ساب‌ردیت‌های نیش، CTR را ≥۲× می‌کنند» |
| متغیر واحد | فقط یک چیز تغییر کند | فرمت عنوان پست (بقیه ثابت) |
| کانال / لینک | tracking link مربوط | reddit-titletest-aug |
| Primary metric | یک KPI | OF clicks per post |
| Baseline | میانگین ۲ هفته قبل | 6 کلیک/پست |
| آستانه تصمیم (از پیش) | Scale / Iterate / Kill | ‏≥12 → scale؛ ‏7–11 → iterate؛ ‏≤6 → kill |
| حجم حداقلی | قبل از قضاوت | ≥8 پست یا ≥300 impression |
| نتیجه | عدد واقعی | 13 کلیک/پست (9 پست) |
| Decision + آموخته | یک خط | Scale؛ سؤال+کنجکاوی برنده شد |

---

## ۸. Deliverable 4 — معیارهای Kill به‌تفکیک کانال [OPINION مبتنی بر benchmarkهای [EST] بخش ۳]

پیش‌فرض: اجرای منظم طبق برنامه محتوایی؛ همه اعداد تجمعی. «Kill» یعنی توقف سرمایه‌گذاری فعال، نه حذف حساب.

| کانال | شرط حداقل تلاش | سیگنال Iterate (تعمیر) | سیگنال Kill (توقف) | ریسک ToS/ban که باید جدا پایش شود |
|---|---|---|---|---|
| **Reddit** (نیش feet) | ۴ هفته، ≥۲۰ پست در ≥۵ ساب‌ردیت مرتبط | <100 کلیک تجمعی → خودِ محتوا/عنوان؛ کلیک خوب اما free-sub <10% کلیک‌ها → پروفایل/آفر | بعد از ۶ هفته و ≥200 کلیک: free subs <5% کلیک‌ها؛ یا 0 paid از ≥60 free sub (سقف ۹۵٪ = 5% — زیر کف benchmark) | حذف پست/ban ساب‌ردیت در صورت نقض قوانین هر subreddit؛ اسپم‌کردن = ریسک site-wide ban [FACT] |
| **X/Twitter** | ۴ هفته، ≥40 پست | <10k impression کل → hook/فرکانس؛ CTR <0.3% با ≥10k impression → کپشن/CTA | هفته ۶: کماکان <50 کلیک/هفته یا CTR <0.2% پایدار | [FACT] محتوای adult مجاز اما از monetization رسمی مستثناست؛ ریسک کاهش reach (بلاگ‌های ۲۰۲۶: arunatalent) — پایش هفتگی impression برای کشف shadow-throttle |
| **Instagram (اکانت SFW teaser)** | ۴ هفته، ≥12 پست/ریل | bio-click <0.2% بازدید پروفایل → بیو/CTA [EST: بازه نرمال 0.1–0.5%، inro.social ۲۰۲۶-۰۵-۰۵] | دومین restriction/حذف محتوا از سمت IG → کانال متوقف شود (ریسک > بازده) | [FACT] ریسک بالای ban برای اکانت‌های مرتبط با OF؛ هرگز لینک مستقیم OF در بیو نگذارید — فقط hub |
| **TikTok (SFW فقط)** | ۴ هفته، ≥12 ویدئو | views خوب اما کلیک hub ≈0 → مسیر بیو | اولین ban اکانت؛ یا ۶ هفته بدون ≥30 کلیک | [FACT] TikTok به‌شدت ضد محتوای adult-adjacent؛ بالاترین ریسک حذف — فقط محتوای کاملاً SFW |
| **Paid shoutout / promo خرید از کریتورها** | ۲ خرید آزمایشی کوچک | CPC > USD 0.5 → مذاکره/تعویض فروشنده | 0 free sub از ≥100 کلیکِ promo (سقف ۹۵٪ = 3%)؛ یا CPC > USD 1 | فقط از کریتورهای واقعی با tracking link اختصاصی؛ پرداخت بدون لینک رهگیری ممنوع [OPINION] |
| **Telegram (کانال دیاسپورا)** | — | — | ⚠️ توصیه به راه‌نینداختن در فاز اعتبارسنجی: Telegram ابزار geo-block در سطح کانال برای حذف ایران ندارد و ریسک نقض قید «حذف کامل ایران» بالاست [OPINION/FACT-mix؛ نیاز به بررسی حقوقی جدا] | — |

**قاعده کلان [OPINION]:** پایان هفته ۸، فقط ۱–۲ کانال با بهترین «free sub per hour of effort» نگه داشته شود؛ بقیه به حالت نگهداری حداقلی می‌روند.

---

## ۹. یادآوری‌های ریسک و انطباق

- [FACT] Beacons، Bitly و Short.io برای لینک adult ممنوع/پرریسک‌اند (بخش ۲) — استفاده = ریسک قطع ناگهانی قیف.
- [FACT] Linktree مجاز اما با سابقه enforcement سخت‌گیرانه علیه کریتورهای بزرگسال (Vice) — نسخه پشتیبان hub همیشه آماده باشد.
- [OPINION] هیچ‌کدام از تاکتیک‌های این گزارش (tracking link، UTM، نظرسنجی خوش‌آمد، spreadsheet) فی‌نفسه ریسک ban ندارند؛ ریسک‌ها در «کانال‌های توزیع» است که بالا پرچم‌گذاری شد.
- ناشناسی: همه حساب‌های ابزارها با ایمیل مستعار برند؛ دامنه با WHOIS privacy؛ در spreadsheet هیچ داده شناسایی‌پذیر خریداران ذخیره نشود (فقط شمارنده‌های تجمیعی).

---

## Blind spots / نقاط کور

1. **Benchmarkهای نیش feet مستقیماً وجود ندارند** — اعداد بخش ۳ از بلاگ‌های آژانسی/vendor (سوگیری خوش‌بینانه) و پلتفرم‌های عمومی OF گرفته شده؛ باید بعد از ~۴ هفته با داده واقعی خودمان جایگزین شوند.
2. **سیاست adult در Plausible و چند ابزار جانبی تأیید نشد** — پیش از پرداخت، بررسی دستی ToS لازم است.
3. **جزئیات فعلی Free Trial Links در OnlyFans** (تعداد مجاز، گزارش‌دهی) داخل داشبورد تأیید نشده است.
4. **دقت tracking link های OF** (نشتی cross-device) قابل اندازه‌گیری مستقل نیست؛ اعداد ما همیشه کمی کمتر از واقعیت خواهند بود — تصمیم‌ها باید به این خطا مقاوم باشند.
5. **راه‌حل measurement برای مخاطب دیاسپورای فارسی‌زبان** عمداً حداقلی ماند؛ سنجش cueهای فرهنگی بدون ریسک ایران نیاز به طراحی جدا دارد (پیشنهاد: صرفاً tracking link مجزا برای پست‌های دارای cue، روی همان کانال‌های انگلیسی).
6. قیمت‌ها و قابلیت‌ها (Linktree نوامبر ۲۰۲۵ گران شد؛ Fansly فیچرها سریع عوض می‌شوند) — **هر عدد قیمتی قبل از خرید دوباره چک شود**؛ تاریخ همه منابع ذکر شده است.
7. داده Reddit Insights بعد از ۴۵ روز پاک می‌شود — اگر ثبت هفتگی فراموش شود، تاریخچه بازیابی‌شدنی نیست.
