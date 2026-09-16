---
type: research-report
prompt: executive-summary
project: Project-F
created: 2026-07-04
status: draft-for-human-review
tags: [project-f, research, research-grounded]
up: "[[PROJECT]]"
---

# خلاصه اجرایی — ۱۰ گزارش تحقیقاتی موتور لیدگیری (Project-F)

**روش:** هر ۱۰ پرامپت فایل `research-prompts-lead-generation.md` در تاریخ 2026-07-04 با desk research خالص اجرا شد (مجموعاً 150+ جستجو/fetch وب، عمدتاً منابع دست‌اول: Help Center و ToS و صفحات قیمت). هیچ اکشن خارجی انجام نشد؛ همه خروجی‌ها draft و نیازمند verdict انسانی‌اند. ترتیب اجرا طبق اولویت: P1، P2، P3، P10 (عمیق) → P5، P4، P9 → P6، P7، P8. **هیچ گزارشی [INCOMPLETE] نیست**؛ موارد نیازمند تأیید دستی در انتهای همین سند تجمیع شده‌اند.

## فهرست گزارش‌ها

| گزارش | موضوع | لینک |
|---|---|---|
| P1 | نقشه کانال و آناتومی رقبا | [P1-channel-map.md](P1-channel-map.md) |
| P2 | موتور رشد X + اتومیشن مجاز | [P2-x-growth-engine.md](P2-x-growth-engine.md) |
| P3 | موتور Reddit و حضور سالم | [P3-reddit-engine.md](P3-reddit-engine.md) |
| P4 | پرسونا/لور + آزمایشگاه هوک | [P4-persona-hooks.md](P4-persona-hooks.md) |
| P5 | فانل SFW→NSFW و geo-block | [P5-funnel-geoblock.md](P5-funnel-geoblock.md) |
| P6 | مخاطب مالکیتی (ایمیل/تلگرام) | [P6-owned-audience.md](P6-owned-audience.md) |
| P7 | اتوماسیون DM (ToS-safe) | [P7-dm-automation.md](P7-dm-automation.md) |
| P8 | شبکه S4S/شات‌اوت | [P8-s4s-network.md](P8-s4s-network.md) |
| P9 | پایپ‌لاین Repurposing | [P9-repurposing-pipeline.md](P9-repurposing-pipeline.md) |
| P10 | آنالیتیکس و حلقه آزمایش | [P10-analytics-experiment-loop.md](P10-analytics-experiment-loop.md) |

## یافته‌های برتر هر گزارش

### P1 — نقشه کانال
- Marketplaceهای feet (FeetFinder/FunWithFeet) موتور رشد نیستند: دو تجربه‌نگاری مستقل (Salon و Mamamia، ۲۰۲۵) با درآمد $0 تمام شدند؛ ادعاهای درآمدی رایج وب عمدتاً محتوای affiliate خود پلتفرم‌هاست [FACT/EST].
- ترکیب برنده: **Reddit (موتور رشد) + X (هاب برند؛ تنها پلتفرم بزرگ با لینک مستقیم به صفحه پولی) + صفحه پولی دوگانه OnlyFans+Fansly** (کشف رایگان FYP).
- بنچمارک‌ها همه [EST]: تبدیل فالوئر→مشترک ۰٫۵–۵٪؛ ۱۰۰ مشترک اول از صفر ~۳–۶ ماه؛ درآمد ماه اول نیچ feet معمولاً $0–80. faceless بودن در نیچ feet کمترین penalty را دارد.

### P2 — موتور X
- feet بدون برهنگی طبق تعریف رسمی X اصلاً "Adult Content" محسوب نمی‌شود [FACT]؛ اما محتوای برچسب‌خورده sensitive برای زیر-۱۸ها و اکانت‌های بدون تاریخ تولد نامرئی است (سقف ساختاری reach).
- قواعد اتوماسیون X (به‌روزرسانی April 2026): زمان‌بندی پست مجاز؛ auto-like، auto-reply، mass-follow و mass-DM ممنوع تا حد تعلیق دائم [FACT].
- API فقط pay-per-use است: پست $0.015، پست لینک‌دار $0.200 (۱۳ برابر — جریمه لینک) [FACT]. موتور رشد از صفر: reply دستی باکیفیت، نه هشتگ.
- استک سازگار: X native scheduler + Postpone + X Premium ≈ AUD 50–70/ماه.

### P3 — موتور Reddit
- فروش محتوای دیجیتال بزرگسال در Reddit مجاز است [FACT، Reddit Help، 2026-05-19] — پایه موتور محکم است.
- verification بدون چهره در subهای تخصصی feet استاندارد است (عکس پا + کاغذ دست‌نویس با username و تاریخ)؛ فقط خانواده GoneWild و برخی subهای فروش عمومی باید حذف شوند.
- warm-up میان‌بر ندارد: ۲–۴ هفته، ~۱۰۰ post karma و ~۵۰ comment karma، بدون لینک خارجی در ۷ روز اول؛ قاعده ۹:۱ (تعامل:پروموشن) [EST].
- تبدیل واقعی از کلیک روی username می‌آید نه لینک داخل پست؛ scheduler پیشنهادی: Postpone (NSFW-مجاز).

### P10 — اندازه‌گیری و حلقه آزمایش
- OnlyFans/Fansly/Fanvue هر سه tracking link بومی دارند [FACT]؛ ضعف مشترک: نشتی cross-device و نبود دید بالادستی قیف.
- Beacons، Short.io و Bitly برای adult ممنوع/پرریسک‌اند [FACT]؛ hub امن: AllMyLinks؛ گزینه بدون ریسک policy: YOURLS self-hosted.
- تصمیم‌گیری با نمونه کوچک: «قاعده سه» — صفر تبدیل در n کلیک یعنی نرخ واقعی احتمالاً زیر 3/n؛ قضاوت click→sub قبل از ~۵۰ کلیک ممنوع.
- داده Reddit Post Insights بعد از ۴۵ روز پاک می‌شود [FACT] → ثبت هفتگی در spreadsheet الزامی. استک: AUD 0–28/ماه.

### P5 — فانل و geo-block ایران
- geo-block بومی ایران در هر ۴ پلتفرم پولی تأیید شد (OnlyFans، Fansly، Fanvue، LoyalFans) [FACT] + لایه link-in-bio با GetAllMyLinks Geo Filter + دامنه شخصی پشت Cloudflare WAF رایگان (`ip.src.country eq "IR"`) — دفاع چندلایه با ~AUD 15–16/ماه.
- محدودیت باقی‌مانده همه لایه‌ها: VPN (فقط مستندسازی شد؛ حذف کامل ممکن نیست).
- موج age-verification (UK از جولای ۲۰۲۵، AU Phase 2 از مارس ۲۰۲۶، EU تا پایان ۲۰۲۶) [FACT] → لایه‌های میانی فانل SFW بمانند تا بار حقوقی age-check روی پلتفرم پولی بیفتد.

### P4 — پرسونا و هوک
- ناشناسیِ مدیریت‌شده خودِ محصول است (الگوی Daft Punk/Banksy): بی‌چهرگی باید در لور برند اعلام شود، نه پنهان. لور حداقلی = ۳–۵ فکت ثابت.
- ۳۰ قالب hook انگلیسی در ۱۰ خانواده تحویل شد؛ POV قوی‌ترین فرمت بی‌چهره است. X: هوک ≤۶۰ کاراکتر، CTA فقط ۱ از ۳–۴ پست؛ Reddit: تایتل = کل کپشن، فروش در تایتل ممنوع.
- سیگنال فرهنگی دیاسپورا فقط بصری/تقویمی (انار، چای، پست «longest night» حوالی یلدا، تم بهاری حوالی نوروز) — **هرگز متن یا هشتگ فارسی** (انکارپذیری + جلوگیری از جذب ترافیک ایران).

### P9 — پایپ‌لاین Repurposing
- Zapier صراحتاً ممنوع (AUP اکتبر ۲۰۲۵) [FACT]؛ Make خاکستری؛ **n8n self-hosted** امن، بدون بند محتوایی، ~AUD 6–10/ماه روی VPS [FACT].
- بهداشت ناشناسی کاملاً خودکارشدنی: `exiftool -all=`، `ffmpeg -map_metadata -1`، watermark با ImageMagick.
- گلوگاه واقعی تولید محتوا نیست؛ **engagement انسانی** است — اتوماسیون باید ساعت آزاد کند، نه تعامل را تقلید کند (مسیر مستقیم ban).
- ساخت هفته-۱: ~۶–۱۰ ساعت؛ استک کل: AUD 25–55/ماه.

### P6 — مخاطب مالکیتی (بیمه ضد-بن)
- تقریباً همه ESPهای مین‌استریم (Mailchimp، MailerLite، Brevo، Klaviyo، Flodesk، حتی Kit و EmailOctopus) adult را ممنوع کرده‌اند [FACT]؛ گزینه‌های سازگار: **SendX** ($9.99/mo، پیشنهادی)، YNOT Mail، Postr.
- تلگرام: کانال عمومی باید کاملاً SFW بماند؛ تلگرام geo-gating ندارد → لایه تلگرام انگلیسی‌only و بدون هیچ پروموی فارسی/ایرانی.
- تنش ناشناسی/الزام هویت فرستنده حل‌شدنی است: business name + ABN + PO Box (الزامات Spam Act استرالیا و CAN-SPAM بدون افشای نام شخصی).

### P7 — اتوماسیون DM
- OnlyFans دسترسی خودکار (bot/scraper) را ممنوع کرده؛ فرمول منطبق بازار: «AI پیش‌نویس می‌زند، انسان send می‌کند» [FACT].
- EU AI Act ماده ۵۰ (از 2026-08-02) افشای چت‌بات را الزامی می‌کند؛ در AU نیز عدم افشا پرریسک است → افشای ملایم «دستیار» عملاً اجباری و ضمناً دارایی برند [FACT].
- ابزار پیشنهادی: Supercreator CRM ~$15/mo (فقط draft و سگمنت)؛ Botly عملاً از دسترس خارج شده — شاهد ریسک churn ناگهانی ابزارهای این بازار.
- تقسیم: ماشین = زمان‌بندی/welcome/سگمنت/پیش‌نویس؛ انسان = هر گفتگوی ۱:۱، هر تصمیم پولی، و همیشه دکمه send.

### P8 — شبکه S4S
- بازار S4S پر از scam است (bot audience، screenshot جعلی، payment scam)؛ vetting: engagement-math روی ۱۰ پست آخر + screen recording + تست کوچک $10–15 با tracking link.
- engagement pods و follow trains در X مصداق platform manipulation است (موج ban مارس ۲۰۲۶) [FACT]؛ PayPal برای پرداخت adult ممنوع/در خطر فریز [FACT]؛ Fiverr ممنوع.
- **توصیه بودجه: AUD 0 تا رسیدن X به N=1,000 فالوور با engagement ≥۲٪**؛ سپس سقف آزمایشی AUD 75/ماه فقط با هزینه هر sub زیر USD 15.

## ۵ اینسایت اجرایی برای طراحی اسپرینت تیزر Track A

1. **معماری اسپرینت: Reddit موتور، X هاب، marketplace فقط ویترین ثانویه.** شواهد مستقل (نه affiliate) نشان می‌دهد marketplace بدون ترافیک بیرونی ~$0 می‌سازد. ساعت‌های محدود اسپرینت باید صرف Reddit + reply-engine دستی X شود؛ صفحه پولی دوگانه OF+Fansly برای کشف رایگان FYP.
2. **تقویم اسپرینت با warm-up شروع می‌شود، نه با پروموشن.** ۲–۴ هفته اول Reddit فقط karma و حضور واقعی (بدون لینک خارجی در ۷ روز اول، قاعده ۹:۱)؛ یعنی انتشار تیزرهای اصلی از هفته ۳–۴. اگر اسپرینت کوتاه‌تر طراحی شود، شکست از پیش تعیین‌شده است.
3. **روز صفر = زیرساخت گیت و اندازه‌گیری (نیم‌روز کار، تقریباً رایگان):** OnlyFans Block-by-country برای ایران + AllMyLinks/GAML با Geo Filter + دامنه شخصی پشت Cloudflare WAF + tracking link جدا به‌ازای هر کانال + Google Sheet هفتگی با kill criteria از پیش ثبت‌شده (قاعده 3/n). داده Reddit بعد از ۴۵ روز می‌پرد — ثبت هفتگی از هفته اول.
4. **لیست سیاه/سبز ابزارها از روز اول:** سیاه = Buffer، Hypefury، Bitly، Beacons، Linktree (پرریسک)، Zapier، ESPهای مین‌استریم، Fiverr، PayPal. سبز = Postpone، AllMyLinks/GAML، n8n self-hosted، SendX، Supercreator (فقط draft). کل استک اسپرینت ≈ **AUD 60–105/ماه، زیر نصف سقف** — باقی بودجه خرج نشود تا X به ~۱٬۰۰۰ فالوور برسد (آستانه ورود به S4S پولی).
5. **اتوماسیون فقط پشت صحنه؛ تعامل همیشه انسانی و افشاشده.** زمان‌بندی پست، EXIF-strip و watermark خودکار: آری. auto-reply/auto-like/mass-DM: هرگز (تعلیق دائم). در DM: «AI پیش‌نویس، انسان send» + افشای ملایم دستیار. گلوگاه واقعی اسپرینت ساعتِ انسانیِ تعامل است — برنامه هفتگی حول همین چیده شود.

## موارد نیازمند تأیید دستی پیش از اجرا (تجمیع)

- **مهم‌ترین ابهام: وضعیت برنامه «ACC / ID-verification» در X.** بین P2 (فقط در content-farmها دیده شد؛ احتمالاً جعلی) و P4/P8 (واقعی فرض شده) تناقض وجود دارد — فقط از داخل اپ/Help Center رسمی قابل حل است و روی تصمیم ناشناسی اثر مستقیم دارد.
- کارمزد و Seller Agreement روزِ FeetFinder/FunWithFeet (منابع متناقض).
- member count و قوانین لحظه‌ای سابردیت‌های هدف + وضعیت فعلی r/Sexsells.
- قیمت روز Postpone، X Premium، SendX (به AUD) پیش از خرید.
- تست عملی Geo Filter در GAML/OOPSIE و سیاست adult آنالیتیکس‌های ابری (Plausible/Fathom).
- متن دقیق ToS فعلی OnlyFans درباره اتوماسیون (آرشیو از داخل اکانت در روز launch).

## نقاط کور سطح مجموعه

- تقریباً همه بنچمارک‌های عددی از منابع ذی‌نفع (vendor/affiliate) می‌آیند — به‌عنوان **سقف خوش‌بینانه** رفتار شود و از هفته اول با داده واقعی جایگزین شوند.
- retention/rebill و pricing عمداً خارج از scope این مجموعه بود (post-lead؛ مجموعه بعدی).
- ریسک باقیمانده VPN در geo-block در همه لایه‌ها وجود دارد و مستند شد؛ حذف کامل ممکن نیست — دفاع چندلایه بهترین حالت عملی است.
