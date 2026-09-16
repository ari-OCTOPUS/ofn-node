---
type: research-report
prompt: P9
project: Project-F
created: 2026-07-04
status: draft-for-human-review
tags: [project-f, research, research-grounded]
up: "[[PROJECT]]"
---

# P9 — پایپ‌لاین بازتولید و زمان‌بندی محتوا (یک شوت در هفته → ده‌ها خروجی)

**خلاصه:** برای تیم دونفره Project-F با سقف بودجه AUD 200/ماه، امن‌ترین و ارزان‌ترین ستون فقرات اتوماسیون، **n8n به‌صورت self-hosted** است (بدون محدودیت محتوایی، چون روی سرور خودتان اجرا می‌شود)، به‌علاوه **Postpone** به‌عنوان scheduler سازگار با محتوای بزرگسال برای Reddit/X. کل هزینه ماهانه استک پیشنهادی ≈ **AUD 25–55** — بسیار زیر سقف بودجه. [OPINION بر پایه FACTهای زیر]

نرخ تبدیل استفاده‌شده: 1 USD ≈ 1.44 AUD [FACT — exchangerates.org.uk، 2026-07-03].

---

## ۱) معماری پایپ‌لاین (Shoot → Process → Distribute → Track)

```
[SHOOT — انسانی، هفته‌ای یک بار]
  دوربین/گوشیِ اختصاصی برند (نه دستگاه شخصی)
        │  انتقال به پوشه محلی /01_RAW/YYYY-WW/
        ▼
[PROCESS — تقریباً ۱۰۰٪ خودکار | اسکریپت یا n8n watch-folder]
  1. Rename طبق قرارداد نام‌گذاری خنثی (بدون نام واقعی/مکان)
  2. EXIF/metadata strip:  exiftool -all=  (عکس)  |  ffmpeg -map_metadata -1 (ویدئو)
  3. برش/رزایز به واریانت‌ها: X (16:9/1:1) ، Reddit (پرتره) ، teaser ده‌ثانیه‌ای، ست PPV
  4. Watermark خودکار (ImageMagick / ffmpeg overlay) — واریانت جدا برای هر پلتفرم
  5. انتقال به /02_READY/{platform}/  +  ثبت ردیف در Sheet/DB (asset ID، وضعیت)
        ▼
[DISTRIBUTE — نیمه‌خودکار]
  • OnlyFans: آپلود دستی به Vault + زمان‌بندی با scheduler داخلی خود پلتفرم (کم‌ریسک‌ترین راه)
  • Reddit + X: صف‌بندی در Postpone (کپشن/عنوان را انسان تأیید می‌کند — قوانین هر subreddit فرق دارد)
  • PPV: چیدمان ست‌ها از Vault — قیمت‌گذاری و ارسال = تصمیم انسانی
        ▼
[TRACK — خودکار]
  n8n هفتگی: جمع‌آوری آمار پست‌ها/کلیک‌ها → Google Sheet داشبورد → گزارش به Telegram/ایمیل تیم
```

قید همیشگی: **Geo-block ایران در سطح پلتفرم مقصد** (OnlyFans → Settings → Privacy & Safety → «Block by country») باید قبل از اولین انتشار فعال شود؛ این قابلیت رسمی OnlyFans در سطح کشور/ایالت/IP است [FACT — pippinclub.com و arunatalent.com، راهنمای 2026]. محدودیت: بلاک IP-محور است و مطلقاً ضدنفوذ نیست؛ صرفاً در حد ابزار رسمی پلتفرم از آن استفاده می‌کنیم. اتوماسیون هیچ نقشی در دور زدن این قید ندارد و نباید داشته باشد.

---

## ۲) انتخاب پلتفرم اتوماسیون: n8n vs Make vs Zapier

| پلتفرم | سیاست محتوای بزرگسال | قیمت (USD / ≈AUD) | ریسک برای Project-F |
|---|---|---|---|
| **n8n (self-hosted)** | لایسنس Sustainable Use هیچ بند محتوایی ندارد؛ استفاده داخلی تجاری آزاد است. چون روی سرور خودتان است، هیچ moderation بیرونی روی فایل‌ها اعمال نمی‌شود [FACT — docs.n8n.io/sustainable-use-license، دسترسی 2026-07-04] | نرم‌افزار: رایگان. VPS: Hetzner CAX11 ‏€3.29/ماه (≈USD 3.9 / AUD 5.6) یا CX22 ‏≈USD 4.5 (AUD 6.5)؛ حداقل کل ≈USD 5.5/ماه با دامنه [FACT — openhosst.com و dev.to، 2026] | **کم‌ترین ریسک** — داده و محتوا از سرور شما خارج نمی‌شود |
| n8n Cloud | ToS ابری بررسی دقیق نشد — قبل از استفاده نیاز به بازبینی دستی دارد [EST] | Starter €24/ماه (2,500 execution)، Pro €60/ماه؛ از آوریل 2026 محدودیت workflow فعال حذف شد [FACT — n8n.io/pricing و connectsafely.ai، 2026] | متوسط؛ برای این بودجه غیرضروری |
| **Make** | در T&C عمومی و MSA بند صریح ضد-adult پیدا نشد، اما ممنوعیت «محتوای غیرقانونی» و سیاست subprocessorها منطقه خاکستری می‌سازد — **needs manual verification** [EST — make.com/en/terms-and-conditions، دسترسی 2026-07-04] | Free: ~1,000 credit/ماه [EST]؛ Core ≈USD 9–12/ماه برای 10,000 credit (سالانه ارزان‌تر) [FACT — trackstack.tech و usecarly.com، 2026] | متوسط — احتمال تعلیق حساب در بازبینی دستی وجود دارد |
| **Zapier** | **صراحتاً ممنوع:** AUP (نسخه 2025-10-15) تولید «sexually explicit content» را در فهرست تخلفات آورده و اجرای آن case-by-case با امکان تعلیق حساب است [FACT — zapier.com/legal/acceptable-use-policy، دسترسی 2026-07-04] | Free ~100 task؛ Professional ‏USD 29.99/ماه (سالانه 19.99) برای 750 task ‏(≈AUD 43/29) [FACT — automationatlas.io و zapier.com/pricing، 2026] | **بالا — توصیه نمی‌شود.** عبور فایل‌های بزرگسال از زیرساخت Zapier نقض AUP بالقوه است |

**تصمیم:** n8n self-hosted روی VPS اروپایی (Hetzner). ارزان‌تر از هر دو رقیب، بدون بند محتوایی، و مدل اجرای per-execution آن (هر اجرای workflow = یک execution، فارغ از تعداد گام‌ها) برای پردازش دسته‌ای رسانه بسیار به‌صرفه‌تر از مدل per-task زپیر است [FACT — مقایسه openhosst/nocode.mba، 2026]. [OPINION]

---

## ۳) Schedulerها: کدام adult-friendly است؟

| ابزار | سیاست adult | قیمت | نکته |
|---|---|---|---|
| **Postpone** | صریحاً برای کریتورهای NSFW ساخته شده؛ Reddit/X/Instagram و ۱۲+ پلتفرم [FACT — postpone.app و postiz.com/blog، 2026] | Free: ‏5 پست/ماه، ۲ اکانت؛ پولی از ‏≈USD 9–16/ماه، استفاده واقعی Reddit ‏≈USD 20–25 (AUD 29–36) [EST — منابع 2026 متناقض‌اند؛ needs manual verification] | انتخاب اصلی برای Reddit (از API رسمی استفاده می‌کند → ToS-compliant) |
| **Postiz (open-source)** | self-hosted و بدون moderation بیرونی؛ ۱۷+ پلتفرم شامل Reddit و X؛ لایسنس AGPL-3.0 [FACT — github.com/gitroomhq/postiz-app، دسترسی 2026-07-04] | self-hosted رایگان (روی همان VPS) | گزینه «build» در build-vs-buy؛ سیاست نسخه ابری‌اش نامشخص [EST] |
| Scheduler داخلی OnlyFans | بومی خود پلتفرم؛ صف Scheduled Content و batch ۳۰+ پست [FACT — sozee.ai و supercreator.app، راهنمای 2026] | رایگان | امن‌ترین راه برای خود OF؛ از ابزار شخص ثالث برای پست خودکار داخل OF پرهیز کنید — ریسک اکانت [OPINION] |
| Buffer | ToS محتوای pornographic را ممنوع کرده [FACT — buffer.com/legal/terms-of-use/year/2023] | — | استفاده نکنید |
| Hootsuite / Later | جریان اصلی؛ عملاً برای این عمود ناامن [EST — بند صریح ۲۰۲۶ آن‌ها بازبینی نشد] | — | استفاده نکنید |

**زمینه پلتفرمی X (2026):** طبق گزارش AuditSocials (منتشر 2026-03-24، به‌روز 2026-05-09) X محتوای بزرگسال را مجاز نگه داشته اما با ساختار سفت‌تر: ثبت‌نام Adult Content Creator با احراز هویت، برچسب سه‌سطحی Sensitive/Adult/Explicit، حذف کامل از For You، و سیستم ۴-strike که «under-labeling» را جریمه می‌کند [FACT در حد گزارش ثانویه؛ خود X برنامه ACC را رسماً با این نام تأیید نکرده → جزئیات needs manual verification]. پیامد عملی برای پایپ‌لاین: هر پست خودکار باید flag رسانه حساس/برچسب درست را داشته باشد، وگرنه strike می‌خورید — این یک نقطه «تأیید انسانی» اجباری است. نکته حریم خصوصی: احراز هویت ACC یعنی KYC نزد پلتفرم (مثل خود OnlyFans)؛ ناشناسی عمومی حفظ می‌شود اما هویت نزد پلتفرم ثبت است [FACT/EST].

**Reddit:** زمان‌بندی با Postpone مجاز است، اما قواعد نانوشته را اتوماسیون نمی‌فهمد: نسبت مشارکت به تبلیغ ~3:1، حساب‌های زیر ۷–۳۰ روز در بسیاری از subredditها محدودند، و بیش از ~۴ پست تبلیغی در هفته بدون engagement معمولاً ظرف ~۱۰ روز به shadowban می‌رسد [EST — desirely.co و social-rise.com، راهنماهای 2026]. پس «ارسال» خودکار می‌شود ولی «انتخاب subreddit + عنوان + ریتم» انسانی می‌ماند.

---

## ۴) Watermark و بهداشت ناشناسی داخل پایپ‌لاین

**Watermark خودکار** (روی VPS یا لپ‌تاپ، داخل n8n با نود Execute Command):
- عکس: `magick composite -gravity SouthEast -dissolve 35 wm.png in.jpg out.jpg` — batch با یک حلقه ساده [FACT — xoogu.com و the-art-of-web.com]
- ویدئو: `ffmpeg -i in.mp4 -i wm.png -filter_complex "overlay=W-w-20:H-h-20" out.mp4` [FACT — gist bennylope و renderio.dev]
- تاکتیک: برای هر پلتفرم واریانت watermark متفاوت (جای/متن کمی متفاوت) بسازید تا منبعِ leak قابل ردیابی باشد؛ جای‌گذاری نیمه‌تصادفی، برش watermark را سخت‌تر می‌کند. [OPINION]

**EXIF/metadata stripping — گام غیرقابل‌حذف قبل از هر آپلود:**
- `exiftool -all= -overwrite_original -r ./02_READY/` — حذف GPS، سریال دوربین، تاریخچه XMP [FACT — exiftool.org forum و renamer.io]
- ویدئو: `ffmpeg -i in.mp4 -map_metadata -1 -c copy out.mp4` [FACT]
- ابزار لوکال است؛ هرگز از سرویس‌های آنلاین حذف EXIF استفاده نکنید (آپلود فایل خصوصی به سرور غریبه). [OPINION]

**مقاومت در برابر reverse-image-search:** موتورهایی مثل PimEyes چهره‌محورند (ایندکس ~۳.۵ میلیارد تصویر) [FACT — pimeyes.com، 2026]؛ محتوای feet-only ذاتاً در برابر جستجوی چهره مقاوم است، اما Google Lens/Yandex صحنه و اشیا را هم تطبیق می‌دهند. قواعد: هیچ عکسی که قبلاً در حساب شخصی منتشر شده هرگز وارد پایپ‌لاین برند نشود؛ پس‌زمینه/ملافه/فرش قابل‌شناسایی (منظره پنجره، مدارک، تتو/خال منحصربه‌فرد) حذف یا crop شود؛ دستگاه و اکانت‌های ابری اختصاصی برند جدا از زندگی شخصی. [OPINION/EST]

**انضباط نام‌گذاری:** الگوی `PF-YYYYWW-SET##-A##-{platform}.ext` — بدون نام واقعی، مکان، یا نام دستگاه. نام پوشه‌ها هم خنثی. متادیتای «نام سازنده» ویندوز/آفیس هم پاک شود (همان exiftool). [OPINION]

**سازمان‌دهی Vault/آرشیو:** ساختار سه‌لایه `01_RAW / 02_READY / 03_POSTED` + یک Sheet ردیاب (asset ID، پلتفرم، تاریخ پست، نوع: free-teaser/wall/PPV). داخل خود OnlyFans، Vault را با پوشه بر اساس ست و سطح (teaser/feed/PPV) مرتب کنید — مدیریت نشدنِ vault در مقیاس، منبع اصلی دوباره‌فروشی اشتباه و فرصت‌های سوخته است [FACT/EST — ofauditor.app، 2026]. بکاپ رمزگذاری‌شده (مثلاً Cryptomator + فضای ابری، ≈USD 5/ماه) [EST].

---

## ۵) Build vs Buy + برآورد زحمت و هزینه

**توصیه: hybrid — هسته را بساز، توزیع را بخر.** [OPINION]
- **Build (n8n + اسکریپت‌ها):** پردازش رسانه (rename/EXIF/watermark/رزایز) منطق ساده و پایداری دارد؛ ساختنش یک‌بار برای همیشه است و داده حساس را در خانه نگه می‌دارد.
- **Buy (Postpone):** اتصال پایدار به API های Reddit/X و مدیریت flairها/زمان بهینه ارزش خرید دارد؛ نگهداری اتصال‌های OAuth شکننده به پلتفرم‌های متخاصم را نخرید-نسازید، اجاره کنید.
- ساختن scheduler اختصاصی با Postiz فقط اگر Postpone گران/ناکافی شد (ماه ۳+).

| قلم | برآورد ساخت (اپراتور فنی) | هزینه ماهانه |
|---|---|---|
| اسکریپت‌های EXIF+watermark+rename | ۴–۶ ساعت [EST] | ۰ |
| VPS + نصب n8n (Docker+SSL) | ۱–۲ ساعت [EST — expresstech.io: ۳۰–۶۰ دقیقه فقط نصب] | ≈AUD 6–10 |
| Workflowهای n8n (watch-folder، ردیاب Sheet، گزارش هفتگی) | ۱۰–۱۶ ساعت [EST] | — |
| Postpone (صف Reddit/X) | ۲–۳ ساعت راه‌اندازی [EST] | ≈AUD 13–36 |
| بکاپ رمزگذاری‌شده | ۱–۲ ساعت [EST] | ≈AUD 7 [EST] |
| **جمع** | **~۲۰–۳۰ ساعت تا پایان ماه ۱؛ ~۴۰–۶۰ ساعت تجمعی تا ماه ۳** [EST] | **≈AUD 25–55 ≪ سقف 200** |

---

## ۶) نسخه هفته ۱ (حداقلی) در برابر ماه ۳ (کامل)

| لایه | هفته ۱ | ماه ۳ |
|---|---|---|
| پردازش | یک اسکریپت bash/PowerShell: rename → exiftool → watermark ثابت | n8n watch-folder؛ واریانت‌سازی خودکار per-platform؛ watermark متغیر |
| توزیع | OnlyFans scheduler داخلی + Postpone Free (۵ پست) یا Starter | Postpone پولی با صف ۲–۴ هفته‌ای Reddit/X؛ قالب عنوان per-subreddit |
| ردیابی | یک Google Sheet دستی | جمع‌آوری خودکار آمار + گزارش هفتگی Telegram |
| زحمت | ~۶–۱۰ ساعت [EST] | ~۴۰–۶۰ ساعت تجمعی [EST] |
| هزینه | ‏AUD 0–15 | ‏AUD 25–55 |

---

## ۷) چه چیزی واقعاً خودکارشدنی است — و گلوگاه واقعی کجاست

**خودکار end-to-end (بی‌خطر):** stripping متادیتا، watermark، رزایز/واریانت، نام‌گذاری، آرشیو/بکاپ، ارسال زمان‌بندی‌شده پس از تأیید، جمع‌آوری آمار.

**نیازمند قضاوت انسانی (خودکار کردنش = ریسک ban):** انتخاب بهترین شات‌ها، کپشن/عنوان مطابق قواعد هر subreddit، برچسب‌گذاری درست سطح حساسیت در X، engagement و پاسخ به کامنت‌ها، DM و قیمت‌گذاری PPV، و هر سیگنال «dog-whistle» فرهنگی (ظرافت زبانی که مدل/قالب خراب می‌کند). ارسال انبوه DM یا engagement مصنوعی مطلقاً ممنوع — هم نقض ToS و هم مسیر مستقیم shadowban [FACT — قواعد پلتفرم‌ها].

**گلوگاه واقعی:** با مخاطب صفر، گلوگاه «حجم تولید» نیست — **توزیع و اعتمادسازی در Reddit/X است** که ذاتاً انسانی و کند است (نسبت 3:1، سن اکانت، سقف ریتم). نقش درست اتوماسیون این است که ~۵–۸ ساعت پردازش هفتگی را به ~۱ ساعت برساند تا آن ساعت‌ها صرف engagement واقعی شود؛ اتوماسیونی که خودِ engagement را تقلید کند دقیقاً همان چیزی است که حساب را می‌سوزاند. [OPINION]

---

## Blind spots / نقاط کور

1. **قیمت‌های Postpone متناقض گزارش شده‌اند** ($9 تا $25) — قبل از خرید، صفحه plans رسمی چک شود. [needs manual verification]
2. **بند adult در MSA مِیک (PDF) کامل خوانده نشد**؛ نتیجه «منطقه خاکستری» از منابع ثانویه است. [needs manual verification]
3. **جزئیات برنامه ACC ایکس فقط از یک منبع ثانویه** (AuditSocials) است و خود X آن را با این نام تأیید نکرده؛ سازوکار برچسب‌گذاری از داخل ابزارهای شخص ثالث (Postpone) باید عملاً آزمایش شود.
4. **ToS خود OnlyFans درباره ابزارهای شخص ثالث** (به‌ویژه هر چیزی که به حساب OF لاگین می‌کند) اینجا عمیق بررسی نشد — پیش از اتصال هر ابزار به OF بازبینی شود.
5. Geo-block ایران IP-محور است و نشت از طریق VPN بیننده یا ایندکس موتورهای جستجو ممکن است؛ ریسک باقی‌مانده باید در سند ریسک پروژه ثبت شود (نه برای «حل» با ترفند).
6. مقاومت واقعی feet-only در برابر تطبیق تصویری غیرچهره‌ای (الگوی خال/تتو، فرش/کاشی خانه) آزمون عملی نشده — قبل از انتشار، ست اول را خودتان با Lens/Yandex تست کنید.
7. برآورد ساعت‌های ساخت [EST] برای یک اپراتور آشنا به Docker/CLI است؛ بدون آن سابقه، اعداد را ~۲ برابر کنید.
8. نرخ ارز و قیمت‌ها snapshot ژوئیه 2026 هستند و باید فصلی بازبینی شوند.

### منابع اصلی (دسترسی 2026-07-04)
- Zapier AUP: zapier.com/legal/acceptable-use-policy (نسخه 2025-10-15)
- n8n license/pricing: docs.n8n.io/sustainable-use-license · n8n.io/pricing · openhosst.com/blog/n8n-self-hosted-pricing · dev.to (cheapest self-host 2026)
- Make: make.com/en/terms-and-conditions · trackstack.tech/en/make-com-pricing-2026
- X policy: auditsocials.com/blog/x-twitter-adult-content-policy-2026-rules-guide (2026-05-09) · help.x.com/en/rules-and-policies/adult-content
- Schedulers: postpone.app · github.com/gitroomhq/postiz-app · buffer.com/legal/terms-of-use/year/2023 · sozee.ai (OF scheduler 2026)
- Reddit playbooks: desirely.co · social-rise.com (2026)
- Geo-block: pippinclub.com · arunatalent.com (2026)
- ابزارها: exiftool.org · gist.github.com/bennylope (ffmpeg watermark) · xoogu.com (ImageMagick) · pimeyes.com
- نرخ ارز: exchangerates.org.uk (USD/AUD ≈ 1.44، 2026-07-03)
