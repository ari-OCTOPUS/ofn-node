---
created: 2026-07-06
updated: 2026-07-06
status: integrated-proposal (هیچ قاعدهٔ قفل‌شده‌ای overwrite نشده)
type: research-integration
round: 1
tags: [project-f, research, delta-map]
---

# RESEARCH-INTEGRATION — Round 1 (2026-07-06)

> **ورودی:** ۵ بلوک تحقیق خارجی paste شده توسط آری (چت 2026-07-06): (الف) Blueprint چت-Revenue-Ops آژانسی، (ب) تحلیل سگمنت مخاطب + ۳ پرامپت تحقیق، (ج) نقشه کانال/پلتفرم و B2B، (د) KYC/مالیات AU + سیاست AI + مدل مالی ۹۰روزه، (هـ) بنچمارک قیمت + آرکتایپ رقبا + گپ «Persian/Sydney». منبع‌گذاری داخلی این بلوک‌ها عمدتاً vendor/affiliate است (Footly, Ecommerce Fastlane, Substy, Maho, Aruna, Zori و…) → **پیش‌فرض همهٔ اعدادشان [EST] با سوگیری خوش‌بینانه**؛ ارجاع در این سند: `[EXT-R1/نام‌منبع]`.
> **روش:** delta-map چهار محور طبق CLAUDE.md §۵ — تأیید / تعارض (تگ دو طرف) / افزوده. قواعد قفل‌شده دست‌نخورده؛ تعارض‌ها فقط flag.

---

## ۰. قضاوت کلی

دیتای Round 1 در ~۸۰٪ موارد **مسیر فعلی corpus را مستقلاً تأیید می‌کند** (faceless + authenticity، AI-draft/human-send، سوشال=قیف، median پایین درآمد، dual-platform، مالیات AU). ارزش اصلی‌اش سه چیز است: (۱) لایهٔ **اثبات اصالت / C2PA** به‌عنوان خندق قیمت‌گذاری، (۲) چارچوب KPI و pipeline کاستوم دقیق‌تر، (۳) نقشهٔ آرکتایپ رقبا + پروتکل آدیت قابل‌اجرا. خطر اصلی‌اش: چهار پیشنهادش با قواعد قفل‌شده یا verdictهای قبلی ما تصادم دارد (§۵) و کل بخش AU آن به GATE 0 (هنوز باز) مشروط است.

---

## ۱. محور ایده (Concept)

**تأیید:**
- «انسان واقعیِ verified در عصر اشباع AI = premium» `[EST — EXT-R1/EF+Footly]` ↔ همان positioning فعلی ما (faceless + real، وعدهٔ zero-filter) `[ACQUISITION-ENGINE §۲، Content-Topics-Trends-2027]`.
- میانهٔ درآمد پایین: OF median $150–180/ماه `[EST — EXT-R1/EF]` ↔ کالیبراسیون بلوپرینت ($180 median؛ Floor/Base/Upside) `[architecture-blueprint]` — همگرایی کامل؛ اهداف فعلی واقع‌بینانه‌اند.
- Customs = مارجین اصلی (۲–۴× قیمت عادی؛ ۴۰–۶۰٪ درآمدِ تثبیت‌شده‌ها) `[EST — EXT-R1/Footly]` ↔ منوی کاستوم + ۳ اسلات/هفته `[ACQUISITION §۵، MONETIZATION-EXPANSION]`.

**تعارض:**
- «positioning اصالت ایرانی/Persian متنی» `[OPINION — EXT-R1]` ↔ قاعدهٔ قفل‌شده #۶ (سیگنال فرهنگی فقط بصری؛ «Persian/Sydney» ممنوع) `[CLAUDE.md §۱.۶، OpenQuestions #۹]` → فقط flag؛ ورودی جدید به سؤال ۹، نه تغییر قاعده.
- نقد دیتا به پرتفوی: «عکس‌های استایل‌شده ظاهر AI-enhanced دارند» `[OPINION — EXT-R1]` — با وعدهٔ برند ما هم‌جهت است اما یعنی اسِت‌های test/ فعلی شاید برای positioning اصالت مناسب نباشند → چک در Shoot #1.

**افزوده:**
- **C2PA / Human-Authorship به‌عنوان خندق:** الزام EU AI Act Art.50 از 2026-08-02 (در corpus بود `[research-track-BC]`) + برچسب‌گذاری خودکار Meta/X + false-positive روی رتوش Adobe `[EST — EXT-R1/RightsDocket+IMH]` → استدلال استراتژیک جدید به نفع «zero filter» و نگهداری RAWها؛ سؤال دیوایس C2PA-دار (Pixel 10 / S25) → OpenQuestions #۱۵ جدید.
- **تفکیک ۳ بازار:** fan-based نیش / **B2B (استاک Adobe-Foap + parts modeling، AUD 350–600/نیم‌روز `[EST]`)** / پارااجتماعی — مسیر B2B در corpus غایب بود → کاندید الحاق به MONETIZATION-EXPANSION (verdict انسانی). ⚠️ tension: قرارداد B2B = هویت واقعی/invoice/ABN ↔ ناشناسی برند — `[OPEN]` #۱۶.

---

## ۲. محور ساختار (Structure)

**تأیید:**
- **الگوی DM:** «AI درفت می‌زند، انسان هر پیام را تأیید/ارسال می‌کند» و رد کامل Autopilot `[EXT-R1 + FACT — Reuters]` ↔ دقیقاً تصمیم موجود ما `[P7، research-track-BC (Track C: No-Go)، ACQUISITION §۵، CLAUDE.md §۸]`. دیتای جدید اضافه می‌کند: در نیچ فتیش chatter انسانی حتی پرفروش‌تر است `[EST — vendor]` → تقویت.
- n8n self-hosted فقط برای بک‌آفیس، بدون اتصال به OF (API رسمی ندارد) ↔ `[P9]` — سازگار.
- سوشال = قیف کشف، فروش/پرداخت فقط داخل پلتفرم ↔ `[P1، P5، قاعده #۳]`.
- Fansly واریز مستقیم بانک AU، ۸۰/۲۰ ↔ `[12-prelaunch]`.

**تعارض:**
1. **کنسول چت متصل به OF (Supercreator/Infloww/…):** پیشنهاد EXT-R1 = Supercreator حالت Assist به‌عنوان کنسول. اما (الف) ToS رسمی OF: *«You cannot use an AI chatbot to write chats or direct messages»* `[FACT — Reuters، راستی‌آزمایی وب 2026-07-06]`؛ ادعای «Co-pilot مجاز است» فقط از vendorهای همین ابزارها است (Substy/Maho/Desirely — تضاد منافع) `[EST/COI]`. (ب) خود EXT-R1 اذعان می‌کند «همهٔ این ابزارها دسترسی غیررسمی به OF دارند» ↔ قاعدهٔ #۴ (صفر نقض ToS) + الگوی ACQUISITION §۵ («کنسول جدا، نه بات متصل»). → **وضع محافظه‌کار فعلی حفظ: درفت در کنسول کاملاً جدا + paste دستی؛ هیچ ابزار third-party متصل به اکانت OF بدون verdict.** (Supercreator در tools list حافظه هست اما به‌عنوان CRM، نه sender متصل — مرزش باید در verdict مکتوب شود.)
2. **FeetFinder/FunWithFeet به‌عنوان نقطهٔ شروع:** EXT-R1 آن‌ها را برای cold-start قوی می‌داند `[EST — EF affiliate + BBB-F و payout-hold خودش flag کرده]` ↔ P1: «marketplaces موتور رشد نیستند» (دو case study با $0) `[P1-channel-map]` + فی دقیق‌تر ما (۱۵٪ Basic/۱۰٪ Premium، نه ۲۰٪) `[12-prelaunch]` → تصمیم قبلی می‌ماند؛ حداکثر: کانال مکمل passive برای بازبینی بعد از G2.
3. **مقیاس آژانسی (multi-creator، شیفت chatter، QA/Scorecard):** برای تیم ۲نفرهٔ فاز validation over-engineering است ↔ `[project-master-reference]` → آرشیو الگو برای بعد از G3.

**افزوده:**
- **لایهٔ CRM فن:** سگمنت Whale/Regular/New/Silent + تگ ترجیحات ساختاریافته (موتور Customs) → پیشنهاد: ۳–۴ فیلد به DB فن‌های Fable5 (بعد از reconcile) `[Fable5-Build-Spec]`.
- **Voice dataset + سند Boundaries per-creator** (لحن + کارهایی که صبا نمی‌کند + منوی قیمت) به‌عنوان ورودی درفت‌های Claude → هم‌افزا با پرسشنامهٔ صبا؛ ساخت آن draft-safe است (داخل پوشه).
- معیار انتخاب هر ابزار آینده: **Export دیتا (ضد lock-in) + عدم نمایش credential خام به اپراتور دوم**.
- Uniquize کردن هر asset per-platform (تشخیص fingerprint تکراری = عامل shadowban) `[EST — EXT-R1/360uniquizer]` → افزودن گام به پایپ‌لاین ACQUISITION §۲.
- Paxum = single-point-of-failure payout → قانون «۲ مسیر payout مستقل از ماه ۲» (dual-platform فعلی ما همین را می‌دهد؛ صریح ثبت شد).

---

## ۳. محور اهداف (Objectives)

**تأیید:**
- منطق kill/scale با آستانهٔ مکتوب ↔ گیت‌های G1/G2 و «قاعدهٔ سه» `[architecture-blueprint، P10]`.
- پنجرهٔ شب AU (۷–۱۱ شب سیدنی برای فن AU/NZ) ↔ همان «پست دوم اختیاری ۹–۱۰ شب» ACQUISITION §۳.۱ — سازگار (پنجرهٔ اصلی ۹–۱۲ صبح برای پرایم US سرجایش).
- مالیات AU: SERR (گزارش خودکار پلتفرم به ATO)، GST از $75k ↔ `[11-fresh-scan، research-track-BC]`؛ set-aside ما ۳۰–۳۵٪ می‌ماند (EXT می‌گوید ۲۵–۳۰٪).

**تعارض:**
- **مدل مالی ماه ۳:** EXT-R1: خالصِ پایه AUD 280–615 / خوش‌بینانه AUD 1,560–3,285 `[EST — vendor-chain]` ↔ بلوپرینت: Floor $0–80 / Base $150–500 / Upside $500–1500 `[architecture-blueprint]` → نسخهٔ EXT در سناریوی بالا ~۲× خوش‌بینانه‌تر؛ **مبنای برنامه‌ریزی = بلوپرینت** (محافظه‌کار)، دلتا ثبت شد.
- «ABN از اولین دلار + کسر ۴۷٪ بدون ABN» `[EXT-R1/NationalAccounts]` — نادقیق: کسر ۴۷٪ مال پرداخت B2B داخل استرالیاست، نه payout پلتفرم خارجی؛ ولی جهتش ورودی سؤال باز #۱۱ (زمان ABN) است — سمت «زودتر» را تقویت می‌کند، تصمیم با مشاور Track B.
- نردبان قیمت EXT (عکس $5–15، باندل، charm pricing $14/$24/$39، custom 2–4×) `[EST]` — عملاً **نسخهٔ چهارمِ** نردبان نیست؛ به نسخهٔ EXT-04/ACQUISITION §۴ نزدیک است → ورودی تازه به سؤال باز #۱۰، هنوز سه‌نسخه‌ای و منتظر قفل.

**افزوده (KPI):**
- متریک‌های جدید برای شیت هفتگی/Fable5: **PPV unlock-rate** (سنجهٔ ارزانی/گرانی — در ACQUISITION بود، حالا صریح KPI شود)، **$/script-start**، **چرخهٔ تحویل Custom (روز)**، **Revenue/Fan/Month**، **$/ساعت DM** (نسخهٔ ۲نفرهٔ «درآمد per chatter-hour»). → پیشنهاد الحاق به لایهٔ KPI ‏ACQUISITION §۸ و Fable5.
- هدف mix بعد از validation: سهم Customs → ۴۰٪+ `[EST]` — هدف فاز G2+، نه الان.

---

## ۴. محور شناخت رقابتی (Competitive)

**تأیید:**
- Verified بودن ≈ ۲× تبدیل + گرم‌کردن اکانت ≥۲ هفته قبل از verify `[EST — EXT-R1/Aruna]` ↔ کیت verification و فاز کارمای ما `[P3، ACQUISITION §۳.۱]`.
- دیسیپلین Reddit: revenue-per-sub (نه upvote)، تفکیک ساب‌های Reach/Conversion ↔ نقشهٔ tracking-link per-sub ما `[ACQUISITION §۴، P10]`.
- «۲۰٪ برتر = فروش فعال + منوی کاستوم شفاف» ↔ لایهٔ ۴ ACQUISITION.

**افزوده:**
- **نقشهٔ ۴ آرکتایپ رقیب** (اتنیک فیس‌اوت / اتنیک فیس‌لس بدون اثبات → «مظنون Catfish» / مارکت‌پلیس-اسپشیالیست / جنرالیست حجمی) + **نردبان ۴سطحی اثبات اصالت**: KYC → verification ردیتی → آیین محتوایی (عکس تاریخ‌دار/BTS/لایو) → اثبات زبانی-فرهنگی. سطوح ۱–۳ کاملاً داخل قواعد ما اجراشدنی است؛ **سطح ۴ (دست‌خط/صدای فارسی) پشت سؤال ۹ قفل است**.
- **White-space ادعایی:** «Persian faceless + آیین اثبات + پنجرهٔ AU + قیمت AUD» — جذاب ولی دو قید: قاعدهٔ #۶ + هشدار خود EXT-R1 که positioning اتنیک ریسک شناسایی در کامیونیتی را بالا می‌برد (هم‌جهت با opsec ما).
- **۳ فرضیهٔ آزمون‌پذیر → Experiment Registry:** H1 (آیین اثبات دوزبانه در Reddit، +۲۵٪ Click→Sub) و H2 (کاستوم با voice-note فارسی، +۱۵٪ نرخ Custom) = **گِیت‌شده به سؤال ۹**؛ **H3 (پنجرهٔ شب AU + منوی AUD؛ سهم فن AU ≥۳۰٪ با ARPPU ≥ کنترل) = بدون تصادم با قواعد، اجراپذیر بعد از GATE 0/لانچ**.
- **پروتکل آدیت ۸–۱۰ کریتور واقعی** (فیلدها: هندل/پلتفرم/قیمت‌ها/کادنس/ساب‌ها/مکانیزم اثبات/شدت اتنیک ۱–۵) + متریک «تراکم دسته per کلیدواژه» برای کمّی‌کردن ادعای قفسهٔ خالی Persian → قابل‌اجرا read-only (داخل اختیارات فعلی؛ خروجی xlsx در دور بعد در صورت تأیید).

---

## ۵. تصادم با قواعد قفل‌شده / verdictهای قبلی — فقط FLAG

| # | پیشنهاد EXT-R1 | قاعده/verdict ما | وضعیت |
|---|---|---|---|
| 1 | فروش مستقیم «تلگرام + کریپتو» در محدودیت پرداخت | قاعدهٔ #۳: پرداخت فقط داخل پلتفرم | **REJECT** — حتی به‌عنوان گزینه ثبت نمی‌شود |
| 2 | «Verified real Persian, Sydney-based» متنی + voice-note فارسی | قاعدهٔ #۶ + OpenQuestions #۹ (P0-opsec) | FLAG → verdict انسانی سؤال ۹؛ تا آن موقع فقط سطوح اثبات ۱–۳ |
| 3 | ابزار چت متصل به OF (دسترسی غیررسمی) حتی در حالت Assist | قاعدهٔ #۴ + Track C No-Go + ToS letter `[FACT-Reuters]` | FLAG → پیش‌فرض: کنسول جدا + paste دستی؛ هر اتصال = verdict |
| 4 | کل بستهٔ AU (ABN/GST/Paxum/KYC خریدار AU) با فرض «creator مقیم سیدنی» | GATE 0 هنوز باز؛ KYC پلتفرم را **صبا** می‌دهد نه آری | مشروط به Branch A — EXT-R1 خودش هم KYC را «قید بحرانی» نامیده (تأیید مستقل GATE 0) |
| 5 | استک $15–100/اکانت + VPS | سقف ابزار AUD 100/ماه | فقط تیر پایین می‌گنجد؛ Nimbusreach($99+5%) خارج از بودجه |
| 6 | Chatter به‌جای کریتور (ریسک impersonation رسانه‌ای‌شده) | privacy دوطرفه + صداقت (هرگز ادعای انسانی‌بودن AI) | سؤال جدید #۱۴: سیاست شفافیت DM در قرارداد دونفره |

---

## ۶. نتیجهٔ راستی‌آزمایی (2026-07-06)

- `[FACT]` متن ToS ‏OF (به نقل Reuters، بازتاب Fast Company/wkzo): *AI chatbot برای نوشتن چت/DM ممنوع*. OF به سؤالات Reuters پاسخ نداد؛ نقض گسترده توسط آژانس‌ها مستند است (FlirtFlow/NEO).
- `[EST/COI]` روایت «Co-pilot با تأیید انسانی مجاز/پذیرفته است» **فقط** در بلاگ فروشندگان همین ابزارهاست؛ هیچ منبع رسمی OF آن را تأیید نکرده. → قرائت محافظه‌کار (الگوی فعلی ما) تنها قرائت defensible است.
- ارقام بازار ($2.1B→$2.78B، فی‌ها، ۴۷٪ فتیش‌ها) = منابع ثانویه/vendor → همه [EST]؛ هیچ‌کدام مبنای تصمیم مالی نشود بدون تأیید اولیه.

## ۷. پیشنهادهای ثبت (proposal — اجرا فقط موارد draft-safe)

1. OpenQuestions: افزودن #۱۴ (سیاست شفافیت DM)، #۱۵ (دیوایس C2PA)، #۱۶ (لایهٔ B2B و tension ناشناسی) + annotate ‏#۹/#۱۰/#۱۱ با ورودی round-1. ✅ اعمال شد
2. DecisionLog: ثبت ingestion این دور + REJECT تلگرام/کریپتو + ابقای الگوی DM محافظه‌کار. ✅ اعمال شد
3. PROJECT.md: یک خط در Active Context. ✅ اعمال شد
4. آیندهٔ نزدیک (منتظر دستور): قالب xlsx آدیت رقبا + شیت Experiment Registry (H1–H3، دو تای اول گِیت‌شده) · فیلدهای CRM به Fable5-Build-Spec · گام uniquize به پایپ‌لاین.

## Sources
- داخلی: `CLAUDE.md` · `_memory/onlyfans-project-memory-2026-07-05.md` · `STATE-REPORT-2026-07-05.md` §۶ · `PROJECT.md` · `OpenQuestions.md` · `DecisionLog.md` · `ACQUISITION-ENGINE-2026-07-05.md` §۱–۵ · ارجاعات P1/P3/P5/P7/P9/P10، `research-track-BC`، `12-prelaunch-verification`، `13-external-integration`
- بیرونی (راستی‌آزمایی 2026-07-06): [wkzo/Reuters — AI bots talk dirty so OnlyFans stars don't have to](https://wkzo.com/2024/07/30/ai-bots-talk-dirty-so-onlyfans-stars-dont-have-to/) · [Fast Company](https://www.fastcompany.com/91164902/onlyfans-stars-leave-sexting-ai) · vendor (COI): [Substy](https://substy.ai/blog/does-onlyfans-allow-chatbots) · [Maho](https://maho-management.com/en/blog-entry/does-onlyfans-allow-ai-content)
