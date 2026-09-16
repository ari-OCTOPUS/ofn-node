---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: draft
tags: [research, track-b, track-c, validation]
created: 2026-07-04
updated: 2026-07-04
---

# گزارش تحقیق Desk — Track B & C — «Project-F»

> **نوع:** desk research یک‌پاسه (scheduled run، 2026-07-04) · **مصرف:** ~۱۴ web search + ۳ page fetch (داخل سقف ۲۰٪)
> **قیود رعایت‌شده:** هیچ اکشن خارجی انجام نشد؛ هیچ فایل موجودی ویرایش نشد؛ فقط عملیات legal (استرالیا/بازارهای قانونی)؛ بدون هیچ جزئیات شناسایی‌پذیر از پارتنر.
> **Tagging:** `[FACT]` تأییدشده از منبع · `[EST]` تخمین/تک‌منبع · `[OPINION]` قضاوت تحلیلی · `[SPEC]` گمانه · `[OPEN]` حل‌نشده.
> **Disclaimer:** این سند مشاوره حقوقی/مالیاتی نیست. آیتم‌های tax/legal فقط «flag برای مشاور licensed» هستند.

---

## ۱. خلاصه اجرایی

- `[FACT]` مسیر payout برای creator استرالیایی روی OnlyFans/Fansly **کار می‌کند و چند-گزینه‌ای است** (bank transfer + e-walletهای adult-friendly مثل Paxum). مشکل ساختاری «دریافت پول» نیست؛ **tail-risk سه‌لایه است:** (۱) freeze/ban در سطح اکانت، (۲) friction بانک شخصی با درآمد adult، (۳) فشار processorها (Visa/Mastercard) در سطح خودِ پلتفرم.
- `[FACT]` الگوی ban/freeze واقعی و مستند است (hold تا ~۹۰ روز، گاهی دائمی؛ نرخ موفقیت appeal پایین). ولی triggerها عمدتاً **رفتاری و قابل‌اجتناب‌اند**: chargebackها، پرداخت خارج از پلتفرم، automation غیرمجاز، نقض content policy.
- `[FACT]` ATO درآمد این vertical را business income می‌داند و از July 2024 پلتفرم‌ها مستقیم به ATO گزارش می‌دهند (Sharing Economy Reporting Regime) → مسیر «زیر رادار» وجود ندارد و نباید هم باشد؛ compliance کامل تنها مسیر سازگار با مرز سخت #۱ پروژه است.
- `[OPINION]` **Track B: Go مشروط.** blocker ساختاری پیدا نشد؛ به شرط معماری مالی جداگانه + قواعد رفتاری سخت + مشاور licensed.
- `[OPINION]` **Track C: Go محدود.** بخش automatable و ToS-safe واقعی است اما عمدتاً **خارج از پلتفرم** (content-ops pipeline، زمان‌بندی Reddit/X، analytics). automation داخل DMهای OnlyFans در فاز validation غیرضروری و پرریسک‌ترین بخش است. automation در این فاز «اهرم بهره‌وری» است، نه moat — همسو با ظنّ ریسک #۵.
- `[EST]` تقاضای feet niche واقعی و بازارش فعال است (marketplaceهای اختصاصی با گردش مالی چند-ده-میلیون‌دلاری self-reported)، ولی قیمت per-item پایین است ($5–15) → بقا وابسته به subscription/custom/volume است، نه تک‌فروشی. سیگنال نهایی تقاضا فقط از Track A درمی‌آید.

---

## ۲. Track B — پایداری Payment / Banking

### ۲.۱ گزینه‌های payout (creator استرالیایی)

| مورد | OnlyFans | Fansly | Fanvue |
|---|---|---|---|
| سهم creator | `[FACT]` 80% | `[FACT]` 80% (یک منبع 85% گفته — تناقض ثبت شد) | `[FACT]` 80% (پرومو 85/15 برای ۳ ماه اول) |
| حداقل payout | `[FACT]` $20 → `[EST]` از April 2026 به $10 کاهش (تک‌منبع) | `[FACT]` $100 (همه روش‌ها) | `[FACT]` ~£50 |
| روش‌ها | bank transfer, Paxum, Cosmo, Skrill | bank wire, Paxum, Skrill, **Bitcoin** | bank transfer, e-wallet محدود |
| تناوب | `[FACT]` manual یا خودکار daily/weekly/monthly | `[FACT]` پیش‌فرض ماهانه | ماهانه |
| Hold | `[FACT]` ۷ روز روی درآمد جدید (ضد-chargeback) | ~۷ روز | متغیر |
| ارز | USD | USD | GBP |
| نکته خاص | `[EST]` rollout روش‌های پرداخت local برای APAC از May 2026 — داشبورد چک شود | `[FACT]` fee عدم‌فعالیت $5/ماه بعد از ۱۲ ماه بی‌لاگین | پلتفرم UK |

- `[FACT]` واریز OnlyFans با نام **«Fenix International»** روی statement بانکی می‌نشیند — همین، trigger شایع flag شدن در بانک‌هاست.
- `[FACT]` Paxum e-wallet تخصصی صنعت adult است (۱۹۰+ کشور): ریسک flag تقریباً صفر، ولی جریان دومرحله‌ای (پلتفرم → Paxum → بانک) و کارمزد برداشت دارد (~$2.99 داخلی تا $50 حواله بین‌المللی).
- `[OPINION]` حداقل payout بالای Fansly ($100) برای برند صفر-صفر یعنی پول ماه‌ها روی پلتفرم می‌خوابد = افزایش balance-at-risk در سناریوی freeze. در فاز اول OnlyFans primary منطقی‌تر است، Fansly به‌عنوان redundancy.

### ۲.۲ الگوی ban/freeze در این vertical

- `[FACT]` triggerهای اصلی suspension/ban: نقض content policy، **chargebackهای مکرر** (مبلغ از balance کم می‌شود و تکرارش به ban می‌رسد)، فعالیت fraud-مانند، **دعوت به پرداخت خارج از پلتفرم** (CashApp/PayPal/crypto در DM یا bio — enforcement تهاجمی، تا حد forfeiture موجودی)، و automation/bot غیرمجاز.
- `[FACT]` در investigation، درآمد pending می‌تواند تا **~۹۰ روز** hold شود؛ در پرونده‌های fraud/chargeback گاهی دائمی.
- `[FACT]` appealها به‌ندرت موفق‌اند؛ وقتی flag از جنس chargeback pattern یا نگرانی banking partner باشد نرخ برگشت نزدیک صفر گزارش شده.
- `[FACT]` ریسک platform-level هم زنده است: گزارش‌های 2026 از سخت‌گیری بیشتر Visa روی استانداردهای fraud/chargeback پلتفرم‌های adult، کارمزد پردازش ۵–۱۰٪ برای این دسته، و اکراه برخی نهادهای مالی حتی در معامله سرمایه‌گذاری OnlyFans. سابقه‌ی ۲۰۲۱ (اعلام ban محتوای explicit زیر فشار payment و عقب‌نشینی بعدی) precedent این tail-risk است.
- `[OPINION]` نتیجه عملی: ریسک #۴ **حذف‌شدنی نیست، مدیریت‌شدنی است** — با انضباط رفتاری (صفر پرداخت خارج پلتفرم، صفر bot غیرمجاز)، برداشت با تناوب بالا (weekly/daily auto-payout برای حداقل‌کردن balance روی پلتفرم)، presence روی ۲ پلتفرم، و فرض برنامه‌ای «سناریوی ۹۰ روز بدون دسترسی به درآمد».

### ۲.۳ Friction بانکی در استرالیا

- `[FACT]` debanking صنعت adult در استرالیا مستند است (نمونه: بستن حساب صاحبِ licensed brothel به‌همراه خانواده‌اش با ban مادام‌العمر). الگوی جهانی: در نظرسنجی 2023 Free Speech Coalition، ~۶۳٪ از پاسخ‌دهندگان صنعت adult حساب بانکی/payment provider از دست داده بودند.
- `[FACT]` mitigationهای رایج: حساب بانکی **جدا** فقط برای درآمد creator؛ e-wallet واسط (Paxum) به‌جای واریز مستقیم؛ انتقال به حساب شخصی به‌شکل lump-sum transfer؛ بانک‌های digital-friendly. یک منبع Wise را برای conversion پیشنهاد می‌کند — `[OPEN]` ToS خود Wise درباره درآمد adult باید جداگانه چک شود، ادعای منبع را verify نکردم.
- `[SPEC]` بانک‌های Big-4 استرالیا policy یکسان و علنی درباره درآمد creator ندارند؛ رفتار case-by-case است. انتخاب بانک = یک آزمایش کوچک عملی در فاز setup (خارج از scope این desk research).

### ۲.۴ پرچم‌ها برای مشاور licensed (نه توصیه؛ فقط flag)

- `[FACT]` ATO این درآمد را business income می‌داند — از دلار اول declarable، مستقل از محل ثبت پلتفرم.
- `[FACT]` **ABN** برای فعالیت business لازم است؛ بدون آن ریسک withholding تا ۴۷٪ و ناتوانی در ثبت GST.
- `[FACT]` آستانه **GST**: گردش $75k در هر بازه ۱۲ماهه (جمعِ همه پلتفرم‌ها) → BAS فصلی.
- `[FACT]` از 1 July 2024 پلتفرم‌ها تحت **Sharing Economy Reporting Regime** داده درآمد را مستقیم به ATO می‌دهند.
- `[EST]` قاعده سرانگشتی رایج: کنار گذاشتن ۲۵–۳۰٪ درآمد برای tax.
- `[OPEN]` ساختار ۵۰/۵۰ (partnership vs. سایر ساختارها)، مالکیت IP، exit mechanics، و اثر مالیاتی تقسیم درآمد — دقیقاً همان آیتم blind-spot #۵ master-reference؛ فقط با مشاور licensed استرالیایی بسته شود.

---

## ۳. Track C — Automation-Fit

### ۳.۱ تفکیک taskهای روزمره creator فیسلس و قابلیت automation

| Task | Automatable؟ | ریسک ToS | ابزار/روش |
|---|---|---|---|
| Production (شوت، grooming، props، نور) | ❌ انسانی | — | batching (در production plan موجود) |
| Post-production hygiene: **EXIF strip، watermark، rename، vault** | ✅ کامل، local | صفر (off-platform) | ExifTool + اسکریپت — دقیقاً در حوزه مهارت اپراتور |
| زمان‌بندی/post به Reddit و X | ✅ بالا | پایین اگر ToS-safe باشد | Postpone (حالت notification-based برای Reddit) |
| پست/زمان‌بندی داخل OnlyFans | ✅ (native) | صفر با ابزار خود پلتفرم | scheduled posts + watermark + geoblocking داخلی OF |
| DM / chat / upsell در OF | ⚠️ جزئی | **بالاترین** | AI-چت‌ابزارها (Supercreator/Infloww/CreatorHero) — ناحیه خاکستری |
| Analytics / CRM / fan segmentation | ✅ | پایین (داده خودمان) | داشبورد ابزارها یا export + اسکریپت |
| Caption/idea generation، repurposing | ✅ نیمه | صفر | LLM + کتابخانه content |
| کشف leak / reverse-image self-test | ✅ دوره‌ای | صفر | Google Images / TinEye / Yandex |

### ۳.۲ مرز ToS در automation

- `[FACT]` ToS خود OnlyFans استفاده از «bots, crawlers, scrapers یا هر automated means» برای دسترسی/تعامل را ممنوع می‌کند؛ bulk-messaging و رفتار bot-مانند صریحاً ریسک ban دائمی دارد.
- `[FACT]` از 2026، OnlyFans برای پاسخ AI به fanها **الزام disclosure/labelling** گذاشته؛ ابزارهای تجاری بزرگ (Supercreator، Infloww و…) ادعای کار داخل همین چارچوب را دارند و بازارشان علنی است.
- `[OPINION]` جمع این دو یعنی: DM-automation در عمل tolerated-but-gray است — اتکای استراتژیک به آن برای یک برند نوپا عاقلانه نیست. در فاز validation حجم DM آن‌قدر کم است که انسان کافی است؛ این تصمیم را می‌شود به بعدِ traction موکول کرد (defer, not reject).
- `[FACT]` سمت Reddit: ابزار scheduling مثل Postpone عمداً از حالت notification-based استفاده می‌کند تا spam-detection تحریک نشود؛ خودِ Reddit با spam (تکرار همان پست در subهای زیاد) برخورد می‌کند نه با scheduling.
- `[FACT]` سمت X: محتوای adult فقط داخل چارچوب برنامه **ACC (Adult Content Creator)** مجاز است — ثبت‌نام با ID، برچسب سه‌سطحی (Sensitive/Adult/Explicit)، الزام label برای محتوای AI-generated، و **عدم monetization محتوای adult در creator program** → X فقط top-of-funnel است، پول همیشه روی OF/Fansly بسته می‌شود.

### ۳.۳ جمع‌بندی fit (نگاه به ریسک #۵)

- `[OPINION]` گلوگاه واقعی فاز فعلی **distribution + consistency** است (audience صفر)، نه پاسخ‌گویی به DM. پس بیشترین ROI اتومیشن الان: (۱) pipeline محافظت/آماده‌سازی content (EXIF/watermark/naming — که همزمان opsec است)، (۲) موتور زمان‌بندی چند-subreddit با رعایت سقف پست، (۳) لوپ analytics هفتگی. این‌ها ToS-safe و ارزان‌اند و مستقیم به bottleneck وصل‌اند.
- `[OPINION]` «automation به‌عنوان moat» در این فاز تأیید نشد — همان‌طور که ریسک #۵ حدس می‌زد. بهتر است فعلاً به‌عنوان **کاهنده هزینه عملیاتی زوج دونفره** قاب شود؛ سؤال moat بعد از Track A دوباره ارزیابی شود.

---

## ۴. Best Practices — Faceless / Feet Niche

### ۴.۱ سیگنال تقاضا و قیمت

- `[EST]` ادعای اندازه بازار «feet imagery» ~$2.1B (2024) با رشد ~۱۲–۱۵٪ سالانه — منبع کیفیت پایینی دارد و تعریف بازارش گشاد است (شامل عکاسی تجاری کفش و stock)؛ فقط به‌عنوان جهت‌نما، نه عدد قابل‌استناد.
- `[EST]` FeetFinder (بزرگ‌ترین marketplace اختصاصی، self-reported): $100M+ گردش خرید تجمعی، 12.5M عکس فروخته، 8M کاربر — ارقام پلتفرم خودش است؛ ولی وجود چند marketplace فعال با مدل اشتراک فروشنده، خودش سیگنال تقاضای واقعی است.
- `[EST]` قیمت‌های رایج: عکس تکی $5–15 (بازه کلی $5–100)، bundle و custom بالاتر؛ فروشنده casual ~$200–600/ماه و فعال ~$600–1500/ماه؛ top creatorها $2k–10k+/ماه. ⚠️ `[OPINION]` این ارقام از محتوای affiliate-آلود می‌آیند و survivorship bias دارند؛ به‌عنوان سقف خوش‌بینانه بخوان، نه انتظار پایه.
- `[FACT]` مدل fee پلتفرم‌های اختصاصی: FeetFinder اشتراک فروشنده ($4.99 یا $14.99/ماه) + کمیسیون (منابع بین ۱۰٪ و ۲۰٪ تناقض دارند `[OPEN]`)؛ FunwithFeet اشتراک ~$14.99/۶ماه + ~۱۵٪.
- `[OPINION]` دلالت برای Project-F: قیمت per-item پایین یعنی مدل درآمد پایدار = **subscription + custom + retention**، نه تک‌فروشی. این با فرض ریسک #۳ («قیمت قابل‌بقا») سازگار است ولی اثباتش فقط empirical است.

### ۴.۲ رشد organic — Reddit / X (اکانت فیسلس)

- `[FACT]` Reddit hub اصلی discovery این niche است؛ subredditهای پرتکرار: r/feetpics، r/prettyfeet، r/soles، r/higharches، r/VerifiedFeet، r/SexSells و… . قواعد کلیدی: **verification** در subهای معتبر (پست‌های verified تا ۲–۵ برابر بهتر عمل می‌کنند)، label کردن NSFW، سقف ~۳ پست/روز در برخی subها، و پرهیز از spray-and-pray (۳–۷ sub در روز، نه ۲۰+).
- `[EST]` انتظار زمانی رایج: اولین conversionها بعد از ۲–۴ هفته پست منظم — با time-box چهارهفته‌ای Track A هم‌خوان است.
- `[FACT]` مدل funnel استاندارد: Reddit/X فقط ترافیک می‌سازد؛ تراکنش روی paid platform بسته می‌شود (همسو با funnel بخش ۷ master-reference).
- `[FACT]` X: بدون عضویت ACC (با ID و certification) محتوای adult مجاز نیست و در هر حال monetize نمی‌شود؛ برخی subredditها هم فقط از فروشنده verified پست می‌پذیرند → **KYC پلتفرمی اجتناب‌ناپذیر است؛ ناشناسی فقط رو به عموم است، نه رو به پلتفرم/دولت** — این expectation باید از روز اول با پارتنر شفاف باشد.
- `[OPINION]` نکته مثبت برای این پروژه: نیاز به verification و سن اکانت یعنی برتری با اکانت‌های صبور و consistent است، نه spammy — دقیقاً جایی که discipline دونفره + scheduling pipeline مزیت می‌شود.

### ۴.۳ Opsec ناشناس‌ماندن (فشرده عملیاتی)

- `[FACT]` لایه‌های استاندارد (از راهنماهای 2026): ایمیل جدای creator (Proton و مشابه) · stage name بدون هیچ ربط به هویت واقعی · شماره تلفن جدا · حساب بانکی جدا · آدرس غیرخانگی برای مدارک · VPN همیشگی هنگام کار روی اکانت‌های creator · مرورگر/profile کاملاً جدا (صفر overlap با اکانت شخصی).
- `[FACT]` **Metadata:** حذف EXIF (GPS، مدل دستگاه، timestamp) از هر فایل قبل از آپلود — ExifTool/ImageOptim/Metapho؛ غیرقابل‌مذاکره. در pipeline اتومیشن بخش ۳ بگنجد.
- `[FACT]` **Content audit پیش از هر پست:** خال/tattoo/جواهرات متمایز، پس‌زمینه (نامه، مدرک، دکور خاص)، **بازتاب‌ها** (آینه/شیشه/صفحه گوشی)، آیتم‌های location-narrowing.
- `[FACT]` **Reverse-image self-test دوره‌ای** با Google Images / TinEye / Yandex روی محتوای promotional؛ هر match به هویت واقعی = توقف و اصلاح فوری.
- `[FACT]` **Geo-blocking در OF:** در سطح کشور (و برای برخی مناطق state-level) کار می‌کند، بر پایه IP؛ با VPN دورزدنی است → یک لایه است، نه راه‌حل کامل. برای Project-F: بلاک ایران (مرز قفل‌شده پروژه) + تصمیم درباره بلاک استرالیا/state محل زندگی یک trade-off درآمد-حریم است `[OPEN]`.
- `[FACT]` انضباط persona: backstory مبهم-ولی-ثابت، شهر واقعی هرگز، صفر تعامل با شبکه شخصی از اکانت‌های creator، و **response plan از قبل** برای سناریوی شناسایی (deny / deflect / own).
- `[FACT]` watermark با stage name: جلوی leak را نمی‌گیرد ولی هویتِ چرخنده در وب را به برند گره می‌زند نه به شخص.

---

## ۵. نگاشت به رجیستر ریسک (بخش ۵ master-reference)

| ریسک | یافته این تحقیق | اثر بر ارزیابی |
|---|---|---|
| **#۳ — تقاضای پرداخت‌کننده در قیمت قابل‌بقا** | `[EST]` بازار فعال و marketplaceها زنده‌اند؛ اما قیمت per-item پایین و ارقام درآمدی آلوده به survivorship bias. مدل بقا = subscription/custom/retention. | جهت مثبت، ولی desk research این ریسک را **نمی‌بندد** — همچنان فقط Track A (teaser واقعی، ۲–۴ هفته) سیگنال قطعی می‌دهد. Prob بدون تغییر. |
| **#۴ — پایداری ساختاری payment/banking** | `[FACT]` مسیر payout چند-گزینه‌ای موجود؛ triggerهای ban/freeze شناخته و عمدتاً رفتاری؛ debanking در AU مستند ولی mitigation-pattern جاافتاده (حساب جدا، Paxum، برداشت پرتناوب، دو-پلتفرمی). tail-risk سطح processor باقی است. | Impact همان ۵ می‌ماند (سناریوی freeze ویرانگر است) اما Prob با انضباط + معماری پیشنهادی **قابل‌کاهش** ارزیابی می‌شود `[OPINION]`. ریسک از «ناشناخته» به «مدیریت‌پذیر با playbook» جابه‌جا شد. |
| **#۵ — اتصال مهارت automation به bottleneck واقعی** | `[FACT+OPINION]` بخش ToS-safe اتومیشن عمدتاً off-platform است (content-ops، scheduling، analytics) و اتفاقاً به bottleneck فعلی (distribution/consistency/opsec) مستقیم وصل می‌شود؛ DM-automation داخل OF خاکستری و در این فاز غیرضروری. | فرض «automation = moat» تأیید نشد؛ فرض «automation = اهرم بهره‌وری متصل به bottleneck» تأیید شد. Score عملاً کمی پایین‌تر از ۱۲ `[OPINION]`. |

- ارتباط با blind-spotها: یافته‌های ۲.۴ دقیقاً blind-spot #۵ (نیاز به مشاور licensed) را فعال می‌کند؛ یافته‌های ۲.۲ blind-spot #۴ (tail-risk پلتفرم) را کمّی‌تر کرد.

---

## ۶. توصیه مقدماتی Go / No-Go `[OPINION]`

### Track B — **GO مشروط**
هیچ blocker ساختاری برای creator استرالیاییِ fully-compliant پیدا نشد. شرط‌های Go:
1. معماری مالی جدا قبل از اولین دلار: حساب بانکی مجزا (+ گزینه Paxum به‌عنوان لایه واسط)، auto-payout پرتناوب برای حداقل‌سازی balance روی پلتفرم.
2. قواعد رفتاری سخت و مکتوب: صفر پرداخت/دعوت خارج از پلتفرم، صفر bot غیرمجاز، انضباط content policy — چون اکثر banها رفتاری‌اند.
3. presence دو-پلتفرمی (OF primary، Fansly secondary) به‌عنوان redundancy، با علم به min-payout $100 در Fansly.
4. جلسه با مشاور مالیاتی licensed استرالیایی قبل از scale (ABN، GST، ساختار ۵۰/۵۰، SERR) — پیش از آن درآمد آزمایشی فقط declare-ready نگه داشته شود.
5. پذیرش صریح سناریوی «۹۰ روز freeze» در برنامه مالی (runway مستقل از این درآمد — که با سقف $200/ماه فعلی سازگار است).

### Track C — **GO محدود (scoped)**
سرمایه‌گذاری اتومیشن فقط روی سه چیز در فاز validation: (۱) pipeline محلی content-hygiene (EXIF/watermark/rename/vault — همزمان opsec)، (۲) scheduling چند-subreddit ToS-safe (الگوی notification-based)، (۳) لوپ analytics هفتگی. **No-Go فعلی** روی DM-automation داخل OF؛ بازبینی بعد از traction واقعی. قاب‌بندی: بهره‌وری، نه moat.

### پیش‌نیاز هر دو
این توصیه‌ها «مقدماتی از desk research» هستند؛ گیت نهایی هر build واقعی همچنان Track A + verdict انسانی + بازشدن Security Gate است (مطابق PROJECT.md — این run هیچ اکشنی در آن جهت انجام نداده).

---

## ۷. محدودیت‌های این تحقیق

- `[FACT]` یک پاس با سقف ~۱۵ جستجو؛ بخش قابل‌توجهی از منابع، بلاگ‌های agency/ابزارها هستند (تضاد منافع ذاتی) — اعداد fee/قیمت هرجا تناقض داشت `[OPEN]` علامت خورد.
- ToSهای رسمی پلتفرم‌ها مستقیم fetch نشدند (بودجه)؛ ادعاهای ToS از منابع ثانویه 2026 است — قبل از launch، متن رسمی OF/Fansly/X یک‌بار مستقیم خوانده شود.
- هیچ داده primary (قیمت رقبا به‌تفکیک، engagement واقعی) جمع نشد — آن بخش، کار Track A است.

## ۸. منابع

**Track B — payout / ban / banking / tax**
1. OGM — Payout Methods Compared (OF/Fansly/Fanvue, 2026): https://onlygemsmanagement.com/blog/payout-methods-every-platform-compared-2026/
2. The Creator Report — OnlyFans Payout Changes 2026: https://thecreatorreport.co/article/onlyfans-payout-changes-2026
3. Infloww — OnlyFans payout methods: https://infloww.com/blog/onlyfans-payout-method
4. RM11 — OnlyFans Ban: Why Most Appeals Fail: https://blog.rm11.com/onlyfans-account-banned-how-to-recover-or-migrate/
5. Chargeblast — OnlyFans Suspended for Chargeback: https://www.chargeblast.com/blog/onlyfans-account-suspended-for-chargeback
6. Lawyer Monthly (May 2026) — Why Banks Still Treat OnlyFans as High Risk: https://www.lawyer-monthly.com/2026/05/onlyfans-struggles-with-banks-and-payment-providers/
7. Policy Options — Financial discrimination against sex workers (شامل کیس استرالیا): https://policyoptions.irpp.org/magazines/may-2024/sex-work-financial-discrimination
8. MoneyMagpie — OnlyFans creators refused by banks: https://www.moneymagpie.com/make-money/onlyfans-creators-being-refused-by-banks
9. Dolman Bateman — OnlyFans Tax Australia: https://www.dolmanbateman.com.au/blog/onlyfans-tax-australia
10. National Accounts — OnlyFans Tax Guide (ABN/GST/SERR): https://www.nationalaccounts.com.au/influencer-services/onlyfans-tax-guide/

**Track C — automation / ToS**
11. Substy — Does OnlyFans Allow Chatbots (2026): https://substy.ai/blog/does-onlyfans-allow-chatbots
12. Supercreator — OnlyFans Bots: Do's and Don'ts: https://www.supercreator.app/guides/onlyfans-bots-dos-and-donts
13. Fanport — OnlyFans Management Tools 2026 (risk-safe scaling): https://fanport.co/blog/en/onlyfans-management-tools
14. Inrō — Best OnlyFans CRM & Automation Tools 2026: https://www.inro.social/blog/best-automation-tools-for-onlyfans-creators-in-2025
15. Postpone — Reddit/X scheduling (notification-based): https://www.postpone.app/ · https://www.postpone.app/platforms/reddit-post-scheduler

**Best practices — niche / growth / opsec**
16. Ecommerce Fastlane — Feet Pics Statistics 2026: https://ecommercefastlane.com/feet-pics-statistics/
17. Social Rise — How Much Do Feet Pics Sell For: https://social-rise.com/blog/how-much-do-feet-pics-sell-for
18. Footly — Selling Feet Pics on Reddit (2026): https://www.tryfootly.com/blog/selling-feet-pics-on-reddit-2026
19. Footly — Where to Sell Feet Pics 2026 (fees/safety): https://www.tryfootly.com/blog/where-to-sell-feet-pics-best-platforms-2026
20. Aruna Talent — The 20-Step OnlyFans Privacy Checklist (2026): https://arunatalent.com/blog/onlyfans-privacy-checklist/
21. Aruna Talent — OnlyFans Geoblocking Guide 2026: https://arunatalent.com/blog/onlyfans-geoblocking-guide/
22. SirenCY — OnlyFans Anonymous: Privacy & Identity Protection 2026: https://www.sirency.com/blog/onlyfans-anonymous-creator-privacy-protection-2026
23. AuditSocials — X Adult Content Policy 2026 (ACC rules): https://www.auditsocials.com/blog/x-twitter-adult-content-policy-2026-rules-guide
24. Aruna Talent — X Adult Content & Creator Program 2026: https://arunatalent.com/blog/x-adult-content-creator-program-2026/
