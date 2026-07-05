---
type: research-report
prompt: P2
project: Project-F
created: 2026-07-04
status: draft-for-human-review
---

# P2 — موتور رشد X/Twitter برای Project-F (پلی‌بوک ۲۰۲۶)

**روش تحقیق:** desk research خالص (۱۵+ جستجوی وب + مطالعه مستقیم صفحات رسمی X Help Center و docs.x.com در تاریخ 2026-07-04). هیچ اکانتی ساخته نشده و هیچ اقدام خارجی انجام نشده است. هر ادعا با [FACT]/[EST]/[OPINION] برچسب خورده است.

---

## ۱. سیاست محتوای بزرگسال X در ۲۰۲۶ — چه چیزی واقعاً معتبر است

- [FACT] طبق صفحه رسمی «Adult Content Policy» (تاریخ سند: May 2024؛ نسخه زنده در 2026-07-04 خوانده شد): انتشار محتوای بزرگسالِ «consensually produced» مجاز است **به شرط برچسب‌گذاری صحیح** و عدم نمایش در جاهای پرنمایش. منبع: https://help.x.com/en/rules-and-policies/adult-content (بازدید 2026-07-04).
- [FACT] محتوای بزرگسال **ممنوع است در:** عکس پروفایل، هدر/بنر، live video، بنر List و کاور X Communities. تخلف تکراری → حالت read-only یا تعلیق. (همان منبع)
- [FACT] مکانیزم برچسب‌گذاری: فعال کردن گزینه «Mark media you post as containing material that may be sensitive» در Settings → Privacy and safety → Your posts؛ به‌علاوه امکان فلگ‌کردن تکی هر عکس/ویدیو (برچسب‌های Nudity / Violence / Sensitive). منبع: https://help.x.com/en/rules-and-policies/media-settings (بازدید 2026-07-04).
- [FACT] اگر مرتب برچسب نزنید، X خودش اکانت را به‌صورت **دائمی** به حالت sensitive تغییر می‌دهد و روی اکانت label می‌گذارد؛ تشخیص خودکار (automated detection) هم دارد. (همان منبع)
- [FACT] کاربران زیر ۱۸ سال **و کاربرانی که تاریخ تولد در پروفایل ندارند** اصلاً نمی‌توانند محتوای برچسب‌خورده را باز کنند → سقف ساختاری reach. (Adult Content Policy، بازدید 2026-07-04)
- [FACT] Monetization داخلی X (ads revenue share / Subscriptions): محتوای «Adult or Sexual» در دستهٔ **Restricted Content** است و با محدودیت درآمدزایی روبه‌روست؛ درخواست پول در ازای خدمات جنسی صراحتاً ممنوع است. یعنی X برای Project-F فقط **کانال ترافیک** است، نه منبع درآمد. منبع: https://help.x.com/en/rules-and-policies/content-monetization-standards (بازدید 2026-07-04).

### ⚠️ هشدار اطلاعات جعلی (مهم)
- [EST/نیازمند تأیید دستی] چند وب‌سایت سئویی (auditsocials.com، arunatalent.com) از یک «Adult Content Creator (ACC) program با ID verification از ژانویه ۲۰۲۶» و «سیستم برچسب سه‌سطحی Sensitive/Adult/Explicit» و «سیستم ۴ اخطاره» می‌نویسند. **هیچ‌کدام از این‌ها در Help Center رسمی X (خوانده‌شده در 2026-07-04) وجود ندارد** و هیچ رسانه معتبری آن را پوشش نداده. احتمال بالا: محتوای content-farm ساختگی. فقط پس از بررسی داخل اپ/تنظیمات اکانت به آن اتکا کنید. (مقایسه: help.x.com/en/rules-and-policies/adult-content در برابر auditsocials.com، هر دو 2026-07-04)
- [FACT] چیزی که واقعی است: صفحه رسمی می‌گوید «content warning»های جدید مخصوص Adult Content (به‌جای برچسب عمومی sensitive) به‌تدریج در حال ارائه است — یعنی برچسب‌گذاری دقیق‌تر در راه است، اما نه «برنامه ثبت‌نام ACC».

### تغییرات محیطی ۲۰۲۵–۲۰۲۶ که reach را کم می‌کند
- [FACT] بریتانیا: از 25 July 2025 طبق Online Safety Act، دسترسی به پورن مستلزم age check قوی است؛ X سیستم age verification معرفی کرده و Ofcom در ژانویه ۲۰۲۶ تحقیقاتی علیه X (پرونده Grok) باز کرد → مخاطب UK فقط بزرگسالانِ تأییدشده. منابع: ofcom.org.uk (2025)، natlawreview.com (2025)، sumsub.com (2026).
- [FACT] استرالیا: از 10 December 2025 قانون منع زیر ۱۶ سال شامل X است (جریمه تا AUD 49.5M). برای نیش بزرگسال اثر مستقیم کم است (مخاطب هدف ۱۸+ است) اما فضای age-assurance سخت‌گیرانه‌تر شده. منبع: esafety.gov.au؛ npr.org (2025-12-10).

---

## ۲. الگوریتم با اکانت NSFW چه می‌کند

- [FACT] عنوان رسمی بخش سیاست، «Restricted Reach» است: محتوای برچسب‌خورده پشت content warning می‌رود و برای کاربران opt-out/زیر ۱۸/بدون تاریخ تولد نمایش داده نمی‌شود. (help.x.com، 2026-07-04)
- [EST] محتوای sensitive عملاً از پیشنهادهای For You برای غیرفالوورها و از بخش‌های Explore/Trends حذف یا به‌شدت تضعیف می‌شود؛ جزئیات دقیق منتشر نشده (کد الگوریتمِ open-source مال ۲۰۲۳ است). منابع ثانویه: posteverywhere.ai (2026)، whisper.fans (2025) — نیازمند رصد عملی.
- [EST] «cluster suppression»: اکانت‌هایی که فقط با خوشه ادالت‌کریتورها (RT-groupها) تعامل دارند شناسایی و reach آن‌ها سرکوب می‌شود؛ راه‌حل: تعامل واقعی با اکانت‌های SFW مجاور نیش. منبع: whisper.fans blog (2025).
- [EST] پست‌های حاوی لینک خارجی در timeline ارگانیک deprioritize می‌شوند (ادعای رایج صنعت؛ سیگنال هم‌راستا: API برای «Post با URL» ۱۳ برابر گران‌تر حساب می‌کند — $0.20 در برابر $0.015). راهکار: «link in bio»، نه لینک در متن پست. [منبع قیمت: docs.x.com، 2026-07-04]
- [FACT] اشتراک X Premium ranking پاسخ‌ها (replies) را بالا می‌برد و آنالیتیکس می‌دهد — برای استراتژی reply مفید است. منبع: help.x.com/en/using-x/x-premium (2026).

---

## ۳. تاکتیک‌های رشد ارگانیک اثبات‌شده (با فلگ ریسک)

| تاکتیک | جزئیات | ریسک ban/shadowban |
|---|---|---|
| پروفایل درست از روز اول | sensitive setting روشن؛ آواتار/بنر بدون برهنگی [FACT]؛ bio انگلیسی + CTA؛ pinned teaser؛ link hub (Linktree/Beacons) با مخلوطی از لینک‌های SFW [EST: لینک‌هاب تمام‌ادالت reach را می‌کُشد — social-rise.com, 2025-04-30] | کم |
| میکس محتوا | [EST] فرمول رایج: 40% teaser / 20% شخصیت و لایف‌استایل / 15% engagement (نظرسنجی، سؤال) / 15% RT و همکاری / 10% thread؛ ۳–۵ پست در روز. منبع: onlymonster.ai (2026) | کم |
| استراتژی Reply (موتور اصلی رشد از صفر) | reply دستی، بامزه/باارزش، زودهنگام روی پست‌های در حال وایرال شدن؛ تمرکز روی اکانت‌های میان‌اندازه 10k–50k؛ تعامل با اکانت‌های SFW مجاور (foot care، nail art، sneaker/hosiery، fashion) نه فقط ادالت. منبع: social-rise.com (2025-04-30) | کم (دستی)؛ اگر spammy/لینک‌دار شود: بالا |
| Quote post | نقل‌قول پست‌های بزرگ‌تر با ارزش افزوده (شوخی/دیدگاه)؛ بهتر از RT خالی [OPINION] | کم |
| X Communities | [FACT] هر Community قواعد خودش را روی X Rules اضافه می‌کند و مودها حذف/اخراج می‌کنند (help.x.com/en/using-x/communities-moderator-playbook). فقط به کامیونیتی‌هایی بپیوندید که صراحتاً NSFW را مجاز کرده‌اند؛ کاور Community هرگز نباید ادالت باشد [FACT] | متوسط (اخراج از کامیونیتی/ریپورت) |
| Promo threads و engagement (RT) groups | رایج در اکوسیستم OF؛ [EST] X این خوشه‌ها را شناسایی و reach را سرکوب می‌کند؛ حداکثر به‌عنوان جرقه اولیه، محدود و همراه تعامل ارگانیک. منابع: social-rise.com (2025)، whisper.fans (2025) | متوسط تا بالا (shadowban) |
| SFS (shoutout for shoutout) | با کریتورهای هم‌سایز/هم‌نیش (feet)؛ مذاکره دستی در DM با لحن انسانی | کم تا متوسط |
| هشتگ‌ها | ۱–۳ هشتگ نیشِ سالم (#lingerie #altmodel #FootModel [EST])؛ هشتگ‌های spam‌زده مثل #porn و #OnlyFans عملاً shadowban شده‌اند — استفاده نکنید. حتی واژه «OnlyFans» در متن پست trigger فیلتر است؛ جایگزین: ایموجی + «link in bio». منبع: social-rise.com (2025-04-30) [EST] | استفاده غلط: متوسط |
| پنجره‌های زمانی | [EST] پیک تعامل ادالت: ~19:30–23:30 به وقت مخاطب؛ برای بازار US یعنی حدود 10:00–15:30 AEST روز بعد برای تیم استرالیایی؛ آخر هفته‌ها دیروقت. منبع: social-rise.com (2025) + تجربه صنعت | — |
| Watermark و منع دانلود ویدیو | ضد سرقت محتوا و branding | صفر |

**بنچمارک‌های نیش feet (همه [EST] — منابع سئویی/وابسته، خطای زیاد):**
- 0→1,000 فالوور: واقع‌بینانه **~۹۰ روز** با ۳–۵ پست روزانه + reply روزانه (founderbrands.io، medium.com/@collin_2548، 2026).
- درآمد نیش feet: ماه اول $100–$400؛ ماه سوم $300–$900؛ کریتورهای تثبیت‌شده $500–$5,000/ماه (ecommercefastlane.com، 2026 — کیفیت منبع پایین).
- تبدیل: از ~500–1,000 فالوور فعال، اولین subscriberها می‌آیند (arunatalent.com، 2026 [EST]).
- ادعای conversion 12–18% از X به اشتراک برای کریتورهای ۱۲+ ماه [EST — مشکوک، احتمالاً خوش‌بینانه].
- [OPINION] برای feet-only بدون چهره، انتظار رشد را ۲۰–۴۰٪ کندتر از میانگین ادالت بگذارید (فقدان «شخصیت با چهره»)؛ جبران با کیفیت بصری بالا و صدای برند قوی.

---

## ۴. Shadowban و تعلیق: علل، تشخیص، درمان

**انواع [FACT — اصطلاحات تثبیت‌شده جامعه]:** Search Suggestion Ban → Search Ban → Ghost Ban (پاسخ‌ها ناپدید) → Reply Deboosting (پاسخ‌ها پشت «Show more»).

**علل اصلی [EST جمع‌بندی از social-rise.com 2025، whisper.fans 2025، unfollr.com 2026]:**
1) رسانه حساسِ بدون برچسب (X خودش اکانت را فلگ می‌کند [FACT])؛ 2) هشتگ‌های بلک‌لیست؛ 3) متن/پست تکراری و duplicate؛ 4) لینک خارجی در هر پست؛ 5) follow/unfollow تهاجمی؛ 6) تعامل فقط درون خوشه ادالت؛ 7) اکانت نو + شتاب غیرانسانی اکشن‌ها؛ 8) خرید فالوور/engagement؛ 9) mass DM.

**تشخیص (ابزارهای رایگان ۲۰۲۶) [FACT — وجود ابزارها]:** opentweet.io/tools/shadowban-check ، banchecker.org/twitter-ban-checker ، api.sorsa.io/playground/shadowban-check ، shadowban.yuzurisa.com. روتین: تست هفتگی + جستجوی دستی `from:handle` در حالت logged-out.

**درمان [EST]:** ۴۸–۷۲ ساعت توقف کامل پست/تعامل → حذف پست‌های پرریسک/هشتگ‌ها → بازگشت آرام با محتوای SFW-lean؛ اکثر shadowbanها ظرف ۱–۴ هفته برطرف می‌شوند اگر رفتار اصلاح شود.

---

## ۵. لایه اتوماسیون — چه چیزی مجاز است (قواعد رسمی، به‌روزرسانی April 2026)

منبع همه موارد این بخش: https://help.x.com/en/rules-and-policies/x-automation (نسخه «Updated April 2026»، خوانده‌شده 2026-07-04) — همگی [FACT]:

**مجاز:** زمان‌بندی/انتشار خودکار پست‌های خودت (via API)؛ auto-Repost/Quote برای مقاصد informational/novelty؛ auto-reply فقط به کاربرانی که **قبلاً opt-in داده‌اند**؛ auto-DM فقط پس از درخواست/اعلام قصد روشن کاربر + راه opt-out.

**ممنوع:** لایک خودکار؛ follow/unfollow انبوه یا خودکار؛ reply/mention خودکار بر اساس keyword search به افراد ناخواسته؛ DM انبوه/سرد؛ پست تکراری روی یک یا چند اکانت؛ دستکاری/پست خودکار روی trending topics؛ **هر اتوماسیون غیر-API (اسکریپت کردن سایت) → ریسک تعلیق دائم**؛ ابزارهای «فالوور بیشتر». نکته حیاتی برای ادالت: «Don't DM, mention, or reply to users with potentially sensitive content unless they've clearly indicated an intent to receive it» — یعنی هر reply-automation با محتوای حساس عملاً ممنوع است. AI reply botها هم به **تأیید کتبی قبلی X** نیاز دارند.

### X API — قیمت ۲۰۲۶
- [FACT] از 6 February 2026 مدل پیش‌فرض برای توسعه‌دهندگان جدید **pay-per-use** است؛ tier رایگان و ثبت‌نام جدید Basic/Pro حذف شده. منابع: docs.x.com/x-api/getting-started/pricing (2026-07-04)؛ اطلاعیه رسمی devcommunity.x.com (Feb 2026)؛ gigazine.net (2026-02-09).
- [FACT] نرخ‌های کلیدی (USD): ساخت پست $0.015؛ **پست حاوی URL $0.200**؛ خواندن پست $0.005/resource؛ «Owned Reads» (داده‌های خود اکانت: پست‌ها/فالوورها/منشن‌ها) فقط $0.001/resource؛ ساخت DM $0.015؛ media metadata $0.005. Deduplication در پنجره ۲۴ ساعته. تا 20% اعتبار برگشتی xAI. (docs.x.com، 2026-07-04)
- [FACT] پلن‌های قدیمی فقط برای مشترکان قبلی: Basic $200/mo، Pro $5,000/mo؛ [EST] مهاجرت Basicها به pay-per-use بعد از June 1, 2026 (منابع ثانویه: postproxy.dev، xpoz.ai، 2026).
- [EST] هزینه عملی Project-F با DIY: ۱۵۰ پست بدون لینک در ماه ≈ **$2.25** + آنالیتیکس با Owned Reads < $1 → ارزان‌ترین گزینه، ولی نیازمند زمان توسعه. لینک را هرگز via API پست نکنید ($0.20/پست) — لینک در bio بماند.

### جدول ابزارها (سیاست ادالت + قیمت)

| ابزار | سیاست محتوای بزرگسال | قیمت (USD) | ≈AUD* | نتیجه برای Project-F |
|---|---|---|---|---|
| **X native scheduler** (وب) | [FACT] همان قواعد X؛ کاملاً سازگار | رایگان | ۰ | ✅ پایه اصلی |
| **X Premium** (برای آنالیتیکس + reply boost) | [FACT] اکانت NSFW می‌تواند مشترک شود؛ ولی درآمدزایی ادالت محدود است | Basic $3/mo، Premium $8/mo، Premium+ $40/mo (وب، US) [FACT: help.x.com؛ قیمت AUD متغیر — تأیید دستی] | ~5 / ~12 / ~61 [EST] | ✅ Premium ($8) توصیه می‌شود |
| **Postpone** | [FACT] صراحتاً برای کریتورهای OnlyFans بازاریابی می‌کند (postpone.app/use-cases/onlyfans، 2026-07-04) → NSFW-friendly | Free (5 post/mo)؛ Starter $25/mo (۲۵۰ پست، ۳ اکانت)؛ Creator $45/mo [FACT: capterra/saasworthy 2025 — سقف tweet هر پلن را دستی چک کنید] | ~38 / ~68 | ✅ گزینه اول SaaS |
| **Social Rise** | [FACT] ابزار تخصصی پروموی OnlyFans (X + Reddit)؛ NSFW-native | Free 5 post/mo؛ ~$29.99/mo برای ۱,۰۰۰ پست (سالانه ~$144) [FACT: social-rise.com/pricing، 2026-07-04] | ~46 | ✅ جایگزین؛ ⚠️ فیچر «Autoresponder» (پیام خودکار به هر تعامل‌کننده) با قواعد opt-in X مرزی است — خاموش بماند |
| **Hypefury** | [FACT] ToS محتوای «obscene, lewd, lascivious» را ممنوع کرده (hypefury.com/terms-of-service) | از ~$19/mo | ~29 | ❌ استفاده نشود |
| **Buffer** | [FACT] ToS توزیع محتوای پورنوگرافیک را ممنوع می‌کند (buffer.com/legal؛ سیاست از 2017) | از $6/channel/mo | ~9 | ❌ استفاده نشود |
| **Typefully / سایر عمومی‌ها** | [EST] سیاست ادالت شفاف نیست — تأیید دستی لازم | — | — | ⚠️ فعلاً نه |

\* نرخ تبدیل فرضی USD→AUD ≈ 1.52 [EST، جولای ۲۰۲۶ — هنگام خرید چک شود].

**تقسیم کار خودکار/دستی [OPINION، منطبق بر قواعد رسمی]:**
- خودکار (کم‌ریسک): زمان‌بندی پست‌ها، صف محتوا، آنالیتیکس، گزارش هفتگی، watermark/رندر batch.
- دستی (اجباری): replyها، DMها، شرکت در Communities، مذاکره SFS، لایک‌ها، follow کردن.

---

## ۶. Deliverable 1 — پلی‌بوک ۳۰ روزه از صفر

**پیش‌فرض‌ها:** اکانت نو، برند انگلیسی، تنظیم sensitive از روز اول روشن [FACT: الزام سیاست]، لینک فقط در bio (link hub با چند لینک SFW)، همه مدیا watermark‌دار، هیچ چهره/هویتی در هیچ فریم.

| هفته | تمرکز | اقدامات روزانه | KPI پایان هفته [EST] |
|---|---|---|---|
| **آماده‌سازی (روز ۰–۲)** | زیرساخت | ساخت پروفایل (آواتار/بنر SFW-تیز اما بدون برهنگی [FACT])؛ bio + link hub؛ pinned post تیزر؛ 2FA؛ تقویم محتوا ۳۰ روزه؛ آماده‌سازی ۶۰+ فایل مدیا | پروفایل کامل |
| **هفته ۱ (روز ۱–۷)** | پایه + یادگیری الگوریتم | ۲–۳ پست/روز (تیزر + شخصیت برند)؛ ۱۰–۲۰ reply دستی باکیفیت به اکانت‌های 10k–50k (feet/lingerie/nail-art/fashion)؛ follow حداکثر ۱۰–۲۰ اکانت مرتبط در روز؛ عضویت در ۲–۳ Community مجاز NSFW؛ **هیچ لینکی در متن پست‌ها** | 30–80 فالوور |
| **هفته ۲ (روز ۸–۱۴)** | شتاب + شبکه | ۳–۴ پست/روز؛ A/B کپشن‌ها؛ ۱–۲ promo thread در روز (سقف‌دار — ریسک متوسط)؛ اولین SFS با کریتور هم‌سایز؛ شروع لاگ آنالیتیکس؛ تست shadowban هفتگی | 80–180 فالوور |
| **هفته ۳ (روز ۱۵–۲۱)** | فرمت‌های عمقی | ۴–۵ پست/روز؛ ۱ thread هفتگی (مثلاً «پشت‌صحنه ست‌آپ نور»)؛ نظرسنجی («کدام: ساتن یا توری؟»)؛ quote post روی کریتورهای بزرگ‌تر؛ تثبیت پنجره‌های زمانی برنده از دیتا؛ تست محتاطانه یک cue فرهنگی فارسی (موتیف بصری، کپشن انگلیسی — بدون هشتگ فارسی) | 150–300 فالوور |
| **هفته ۴ (روز ۲۲–۳۰)** | تثبیت + اتوماسیون | دو برابر کردن ۲۰٪ فرمت برتر؛ ۲–۳ SFS جدید؛ فعال‌سازی Postpone/Social Rise و پر کردن صف ۲ هفته؛ خرید X Premium؛ ممیزی پایان ماه: فالوور، ER، کلیک link hub، تست‌های shadowban، مرور انطباق با قواعد | 200–500 فالوور، ۳–۵ subscriber اولیه [EST] |

**ریتم هفتگی ثابت از ماه دوم:** دوشنبه برنامه‌ریزی/زمان‌بندی → سه‌شنبه تا شنبه اجرای reply روزانه (۳۰–۴۵ دقیقه) → یکشنبه آنالیز + تست shadowban.

---

## ۷. Deliverable 2 — استک اتوماسیون سازگار (بودجه AUD 200/ماه)

| جزء | ابزار | نقش | هزینه ماهانه |
|---|---|---|---|
| زمان‌بندی پایه | X native scheduler | پست‌های روزمره | AUD 0 |
| زمان‌بندی حرفه‌ای + صف NSFW | Postpone Starter (یا Social Rise) | صف ۲ هفته‌ای، bulk upload، بهترین ساعات | ~AUD 38 (~AUD 46) |
| آنالیتیکس + اعتبار اکانت | X Premium ($8) | آمار، reply ranking، ویدیو بلندتر | ~AUD 12–14 [EST — قیمت AU تأیید شود] |
| پایش سلامت | opentweet.io / banchecker.org / sorsa.io | تست هفتگی shadowban | AUD 0 |
| (اختیاری، فاز ۲) | X API pay-per-use | اسکریپت پست/آنالیتیکس اختصاصی | ~AUD 4–8 |
| **جمع** | | | **≈ AUD 50–70/ماه** ✅ زیر سقف |

قاعده طلایی: **اتوماسیون فقط برای publish و analytics؛ هر تعامل انسانی (reply/DM/like/follow) دستی می‌ماند** — این دقیقاً مرز رسمی X است [FACT: x-automation، April 2026].

---

## ۸. Deliverable 3 — لیست «هرگز انجام نده» (رتبه‌بندی بر اساس شدت مجازات)

**سطح ۱ — تعلیق دائم / غیرقابل‌بازگشت [FACT: سیاست‌های رسمی]:**
1. هر محتوای غیرقانونی/غیرتوافقی یا مرتبط با زیر ۱۸ (نابودکننده کسب‌وکار + پیگرد قانونی).
2. خرید فالوور/لایک/RT یا هر engagement مصنوعی (platform manipulation — help.x.com/en/rules-and-policies/authenticity).
3. Mass cold DM یا DM خودکار بدون opt-in.
4. اتوماسیون غیر-API (اسکریپت کردن سایت/مرورگر) — صراحتاً «permanent suspension» [FACT].
5. اکانت‌های تکراری/موازی با محتوای مشابه؛ ban evasion با اکانت جدید.
6. درخواست پول در ازای خدمات جنسی در پست/پروفایل (ممنوعیت solicitation) [FACT].

**سطح ۲ — تعلیق موقت / قفل اکانت [FACT]:**
7. برهنگی در آواتار/بنر/live/کاور Community.
8. تکرار آپلود مدیای حساسِ بدون برچسب (اول فلگ خودکار، بعد اقدامات شدیدتر).
9. auto-reply/mention مبتنی بر keyword به افراد ناخواسته؛ لایک خودکار.
10. follow/unfollow تهاجمی (follow-churn).
11. پست‌های duplicate/انبوه؛ هایجک trending topics برای پروموشن.

**سطح ۳ — shadowban / مرگ خاموش reach [EST]:**
12. هشتگ‌های بلک‌لیست (#porn، #OnlyFans و مشابه) و hashtag stuffing.
13. لینک OnlyFans خام در متنِ هر پست؛ link hub تمام‌ادالت.
14. تعامل انحصاری درون RT-groupهای ادالت.
15. واژه‌های trigger («OnlyFans»، عبارات صریح) در هر کپشن؛ متن یکسان تکراری.
16. رگبار پست در بازه کوتاه (رفتار بات‌نما) از اکانت نو.

**سطح ۴ — فرسایش برند (بدون مجازات پلتفرمی) [OPINION]:**
17. فید ۱۰۰٪ صریح (ارزش محتوای پولی را می‌کشد و بات‌نما به نظر می‌رسد).
18. بی‌پاسخ گذاشتن fanهای واقعی؛ ناپیوستگی چندروزه در ماه اول.

---

## ۹. ملاحظات ویژه Project-F

- **حذف کامل ایران:** [FACT — بر اساس بررسی مستندات؛ نیازمند تأیید دستی] X هیچ قابلیت رسمی برای geo-block کردن پست‌های ارگانیک توسط خود کاربر ارائه نمی‌دهد (محدودسازی کشوری فقط از سمت X و به دلایل حقوقی انجام می‌شود). بنابراین ایران‌-exclusion باید در لایه مقصد اجرا شود: geo-block در پلتفرم فروش + geo-fence روی landing page، و در لایه سیگنال: هیچ هشتگ/کپشن فارسی، هیچ تعامل با اکانت‌های داخل ایران، هیچ اشاره‌ای که مخاطب داخل ایران را دعوت کند.
- **Dog-whistle فارسی (دیاسپورا):** [OPINION] فقط نشانه‌های بصری/فرهنگی ظریف (موتیف، رنگ، اشاره شاعرانه ترجمه‌شده به انگلیسی) در ≤10٪ محتوا؛ برند English-first بماند. اندازه‌گیری اثر از طریق reply/DMهای ورودی، نه targeting.
- **ناشناسی:** [FACT] برای صرفِ پست کردن محتوای بزرگسال، X در حال حاضر ID نمی‌خواهد؛ اما Monetization رسمی X مستلزم identity verification + Stripe است → **هرگز** وارد برنامه‌های درآمدی X نشوید؛ X فقط قیف ترافیک بماند. (content-monetization-standards، 2026-07-04) توجه: age-verification در UK و الزامات AU ممکن است در آینده به کاربران عادی هم برسد — ریسک ناشناسی را در P-anonymity پایش کنید.

---

## Blind spots / نقاط کور

1. **UI واقعی برچسب‌گذاری ۲۰۲۶ دیده نشده** — desk research بدون اکانت؛ وضعیت رول‌اوت «content warningهای جدید Adult Content» و هر جریان ثبت‌نامی داخل اپ باید دستی چک شود.
2. **شایعه «ACC program / برچسب سه‌سطحی / ۴ strike»** فقط در content-farmها — تا تأیید داخل اپ، نه رد قطعی و نه پذیرش.
3. **جزئیات الگوریتم NSFW** (سهم For You، شعاع پیشنهاد) غیرشفاف است؛ اعداد reach همگی استنباطی‌اند.
4. **بنچمارک‌های نیش feet** از منابع سئویی/affiliate با انگیزه فروش‌اند؛ بازه خطا بزرگ است — KPIهای خودتان را از هفته ۲ مبنا قرار دهید.
5. **قیمت‌ها فرّار:** پلن‌های Postpone (سقف tweet هر پلن)، قیمت AUD ‌های X Premium، نرخ USD→AUD و نرخ‌های API — همه هنگام خرید دوباره چک شوند؛ X صراحتاً می‌گوید «Prices are subject to change».
6. **سیاست ادالت Typefully/Fedica/OnlySocial و Zapier/Make** بررسی نشد — پیش از استفاده تأیید شود.
7. **مهاجرت legacy Basic API بعد از June 2026** فقط از منابع ثانویه — اگر DIY API مدنظر است، اعلان‌های رسمی devcommunity را دنبال کنید.
8. **اثربخشی cue فارسی برای دیاسپورا** هیچ داده عمومی ندارد؛ صرفاً باید A/B تست شود (خارج از ایران، بدون targeting).
9. **ریسک باقیمانده ایران:** کاربران داخل ایران با VPN از نظر فنی می‌توانند محتوای عمومی X را ببینند؛ حذف ۱۰۰٪ در لایه X ناممکن است — کنترل در لایه فروش/پرداخت انجام می‌شود (ارجاع به گزارش حقوقی).
10. **X Communities مخصوص نیش feet** فهرست نشد (نیازمند جستجوی داخل اپ)؛ قواعد هر کامیونیتی قبل از پست باید خوانده شود.

---

### منابع کلیدی (همه بازدید 2026-07-04 مگر ذکر تاریخ)
help.x.com/en/rules-and-policies/adult-content (سند May 2024) · help.x.com/en/rules-and-policies/media-settings · help.x.com/en/rules-and-policies/x-automation (Updated April 2026) · help.x.com/en/rules-and-policies/content-monetization-standards · docs.x.com/x-api/getting-started/pricing · devcommunity.x.com/t/announcing-the-launch-of-x-api-pay-per-use-pricing/256476 (Feb 2026) · postpone.app/use-cases/onlyfans و /plans · social-rise.com/pricing و /blog/how-to-promote-onlyfans-on-twitter (2025-04-30) · hypefury.com/terms-of-service · buffer.com/legal · ofcom.org.uk (age checks، 2025) · esafety.gov.au (social media age restrictions، 2025-12) · npr.org (2025-12-10) · whisper.fans blog (2025) · onlymonster.ai (2026) · founderbrands.io (2026) · ecommercefastlane.com/feet-pics-statistics (2026) · opentweet.io · banchecker.org · api.sorsa.io
