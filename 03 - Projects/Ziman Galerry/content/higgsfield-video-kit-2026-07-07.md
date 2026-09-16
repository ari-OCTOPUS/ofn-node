---
type: content-pack
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: draft
created: 2026-07-07
updated: 2026-07-07
created_by: agent
note: "کیت paste-ready هیگزفیلد — draft. تولید در هیگزفیلد با خودِ آری؛ انتشار پشتِ verdict + سقف ظرفیت D4. عکس‌ها photo-agnostic؛ با رسیدن عکس‌های جدید تخصیص می‌شود."
sources:
  - "[[03 - Projects/Ziman Galerry/content/first-sale-pack]]"
  - "[[03 - Projects/Ziman Galerry/Business-Zeiman]]"
---

# 🎬 کیت ویدیوی هیگزفیلد — زیمان (۱۰ روش)

> **این چیست:** برای هر یک از ۱۰ روش، یک recipe آماده که در هیگزفیلد paste می‌کنی. پرامپت‌ها انگلیسی‌اند (بهترین خروجی)، کپشن‌ها انگلیسی (طبق استراتژی)، طولِ هدف ۳۰–۶۰ ثانیه.
> **ترکِ جدا:** ویدیو ترکِ پیش‌پرداخت‌شده است ($۷۰ AUD / کردیت موجود). **تولید آزاد است؛ انتشار/مقیاس پشتِ سقفِ ظرفیت (۳۰/هفته) و verdict می‌ماند** — تولید کن، ولی فقط به‌اندازه‌ای پست کن که مامان بتواند تحویل دهد.

## ۰. تصحیحِ مدلِ هزینه (مهم)

داکیومنتِ قبلی «۵ کردیت/ثانیه» فرض کرده بود — **`[FACT]` این غلط است**؛ هزینه به مدل بستگی دارد (منبع: Higgsfield pricing، مه ۲۰۲۶):

| مدل | کاربرد | هزینه | معادلِ ثانیه |
|---|---|---|---|
| Kling 3.0 @720p | b-roll بی‌صدا، حرکتِ محصول | ۷ کردیت / ۵ ثانیه | ~۱.۴ cr/s |
| Higgsfield Speak 2.0 | کلیپِ گفتار/voiceover | ۱۴ کردیت / ۵ ثانیه | ~۲.۸ cr/s |
| Seedance 2.0 | حرکتِ سینمایی‌تر | ۲۵ کردیت / ۵ ثانیه | ~۵ cr/s |
| Veo 3 (با صدا) | هیرو، کیفیت بالا | ۵۸ کردیت / ۸ ثانیه | ~۷.۲۵ cr/s |
| Nano Banana Pro | عکسِ محصولِ تمیزشده | ۲ کردیت / تصویر | — |
| Soul Inpaint / Product Placement | جاگذاریِ محصول | ۰.۲۵ کردیت | — |

**قاعدهٔ خرجِ کم:** ستونِ فقراتِ هر ویدیو Kling 3.0 (ارزان) باشد؛ Speak 2.0 فقط برای یکی‌دو کلیپِ گفتار؛ Veo 3 فقط برای **یک** ویدیوی هیرو. با این ترکیب، هر ویدیوی ۳۰–۶۰ ثانیه ≈ **۴۵ تا ۱۰۰ کردیت** → با ~۸۳۵ کردیت حدود **۸ تا ۱۵ ویدیو**. (نه ۴۷.)

## ۰.۱ لنگرِ طول (دیتای ۲۰۲۶)

`[EST — چند منبعِ ۲۰۲۶]` ۱۵–۳۰s = بیشترین reach · ۲۱–۳۴s = sweet-spot تکمیل · ۳۰–۶۰s = آموزشی/دمو · ۶۰–۹۰s **فقط** وقتی هر ثانیه ارزش اضافه کند. هوک در ثانیهٔ ۱–۱.۵ · **همیشه زیرنویسِ روی تصویر** (۸۵٪ بی‌صدا می‌بینند) · یک ایده در هر ویدیو · CTA یکی. → «تا حد امکان طولانی» را **۳۰–۶۰ ثانیه** تفسیر می‌کنیم؛ فقط روش‌های ۱ و ۷ اجازهٔ ۶۰–۹۰ دارند.

---

## ۱. نگاشتِ ۴ دستهٔ محصولِ واقعیِ زیمان

از `Business-Zeiman`. «۴۷ محصول» احتمالاً ۴۷ **طرح/SKU** داخلِ همین ۴ دسته است (تعارض با vault در OpenQuestions ثبت شد).

| کد | دسته | جایگاه | مناسبت‌های اصلی | قیدِ خاص |
|---|---|---|---|---|
| **C1** | گل‌آراییِ مصنوعیِ ماندگار | دکور/یادگاری (نه گلِ تازه) | خانهٔ نو، تشکر، «همین‌طوری» | تأکید بر «مصنوعی/ماندگار» |
| **C2** | سبدِ هدیه | هدیهٔ ترکیبی | تولد، تشکر، شرکتی | — |
| **C3** | شادوباکسِ گلِ قاب‌شده 🏆 | یادگاریِ شخصی‌سازی‌شده (عکس/نام/تاریخ) | نامزدی، سالگرد، نوزاد، یادبود | **هیرو دسته** — بیشترین مارجین/تمایز |
| **C4** | همپرِ شکلات | هدیهٔ خوراکی | سوپرایزِ نزدیک | **فقط تحویلِ حضوری** · بطری = آبِ تزئینی نه الکل |

**بینشِ رقابتی `[FACT — تحقیق زنده ۲۰۲۶]`:** رقبای سیدنی (A Pocketful of Roses، Always in Bloom) شادوباکسِ گلِ **واقعی** با ۸–۱۶ هفته انتظار و $۷۴۰–۱۱۵۰ می‌فروشند. تمایزِ زیمان: گلِ **مصنوعی** → بدونِ انتظار، ساختِ سریعِ سفارشی، قیمتِ خیلی پایین‌تر. باندِ قیمتِ واقع‌بینانه برای C3 با شخصی‌سازیِ عکس ≈ **$۹۰–۱۶۰ AUD** (مقایسه: Pip&Willow $۹۴.۹۵، Grand Bazaar $۱۵۳.۵۰). → پیام: «همان یادگاری، بدونِ انتظارِ ۴ ماهه، با عکسِ خودت.»

---

## ۲. ده روش (paste-ready)

> ساختارِ هر کلیپِ image-to-video: عکسِ محصول را آپلود کن، پرامپت را paste کن. `[PHOTO]` = جای عکسِ محصولِ تو.

### روش ۱ — برند-استوریِ چندصحنه‌ای · کارِ قیف: اعتماد · ۶۰–۹۰s (هیرو)
**بهترین دسته:** همه (چتر برند) · **مدل:** Veo 3 برای صحنهٔ اول، Kling 3.0 برای بقیه · **کردیت:** ~۱۲۰–۱۵۰
**کلیپ‌ها (استیچ):**
1. `Cinematic slow push-in on a handcrafted rose-gold floral keepsake on a warm-lit Sydney table, soft morning light, shallow depth of field, cozy artisan mood. [PHOTO]`
2. `Close-up hands arranging delicate artificial blooms into a frame, gentle motion, tactile detail, warm tones.`
3. `A finished framed flower shadow box held up to window light, rotating slowly to show depth. [PHOTO]`
**Voiceover (Speak 2.0, EN):** "Ziman. Handmade keepsakes, made in Sydney — by a mother and daughter. Our flowers are everlasting, so your memory is too. Made in small batches, just for you."
**On-screen hook (0–1.5s):** "Made by hand, in Sydney 🌸"
**Caption:** Every piece is handmade in Sydney by me and my mum. Everlasting florals = a keepsake that never wilts. Limited batches. 💌 DM to order · local delivery · PayID
**CTA:** "Follow for handmade keepsakes 🌸" · **متریک:** Reach · Follows

### روش ۲ — سفرِ آنباکسینگ · اشتیاق · ۳۰–۴۵s
**دسته:** C2, C3 · **مدل:** Kling 3.0 (صدا روشن برای ASMRِ کاغذ) · **کردیت:** ~۶۰–۸۰
**کلیپ‌ها:** `Top-down unboxing of an elegant gift box, hands lifting tissue paper to reveal a floral keepsake, satisfying reveal, natural light, audio on. [PHOTO]` → `Close-up of the keepsake settling in the box, ribbon detail, gentle motion.`
**On-screen:** "POV: your gift just arrived 🎁"
**Caption:** The moment they open it 🌸 Handmade, everlasting, and packed with care in Sydney. Which colour would you choose? 💌 DM to order.
**CTA:** "Save this for gift inspo 🎁" · **متریک:** Saves

### روش ۳ — ریویوِ صادقانه + b-roll · تبدیل · ۴۵–۶۰s
**دسته:** C3 (رفعِ objection) · **مدل:** Speak 2.0 + Kling 3.0 · **کردیت:** ~۹۰–۱۱۰
**پیامِ کلیدی (objection):** «مصنوعی یعنی همیشه تازه؛ هیچ‌وقت پژمرده نمی‌شود.»
**Voiceover (EN):** "People ask — are these real flowers? No. They're everlasting. That means no wilting, no water, no waiting eight weeks like preserved bouquets. Your photo, your colours, framed to last."
**b-roll:** `Slow pan across a framed floral shadow box on a shelf, dust-free, vivid colours after 'one year later' text overlay.`
**On-screen:** "'Won't they die?' → Nope. Here's why 👇"
**Caption:** Real talk: our flowers are everlasting, not fresh. So your keepsake looks this good in a year. Add your photo + names. 💌 DM "FRAME" to start.
**CTA:** Comment "FRAME" → DM · **متریک:** DM / سفارش

### روش ۴ — تیوتوریالِ «چطور سفارش بدم» · اکشن · ۳۰s
**دسته:** همه · **مدل:** Kling 3.0 + متنِ روی تصویر · **کردیت:** ~۴۵–۶۰
**۳ گام روی تصویر:** 1) "DM us your occasion" 2) "Pick colours + add a photo" 3) "Pay by PayID · pick up or local delivery"
**Voiceover (EN, optional):** "Ordering is easy. DM your occasion, choose your colours, send a photo to personalise, and pay by PayID. Sydney local delivery — hampers are pickup only."
**On-screen hook:** "How to order a Ziman keepsake in 30s ⏱️"
**Caption:** Ordering is this easy 👆 DM your occasion → pick colours → PayID → done. Local Sydney delivery. 💌
**CTA:** "DM to start your order" · **متریک:** DM / سفارش

### روش ۵ — مونتاژِ مناسبت‌ها · قصد · ۴۵s
**دسته:** C1–C4 (هر مناسبت یک دسته) · **مدل:** Kling 3.0 · **کردیت:** ~۷۰–۹۰
**کلیپ‌ها (هر مناسبت ۵–۸s):** anniversary shadow box → newborn keepsake (soft pastel) → housewarming arrangement → chocolate hamper (local). هر کدام `[PHOTO]`.
**On-screen:** "One keepsake for every moment 🌸"
**Caption:** Anniversary. New baby. New home. Just because. A handmade keepsake for every moment — made in Sydney. Which one's your occasion? 💌
**CTA:** "Tag someone with a moment coming up" · **متریک:** Send · DM

### روش ۶ — کامپایلِ تستیمونیال/استریت-اینترویو · اعتماد · ۳۰–۴۰s
**⚠️ گیت:** الان فروش = صفر، پس مشتریِ واقعی برای تستیمونیال نداریم. **این روش تا بعد از اولین ۳–۵ سفارش قفل است.** فعلاً جایگزین: reaction به پیامِ خودِ سفارش‌دهنده‌ها (با اجازه).
**بعداً — مدل:** UGC/Interview stitch · **کردیت:** ~۶۰

### روش ۷ — ASMRِ بلندِ ساخت · واچ‌تایم · ۶۰–۹۰s
**دسته:** C3 (ساختِ شادوباکس) · **مدل:** Kling 3.0 صدا-روشن · **کردیت:** ~۱۰۰–۱۳۰
**کلیپ‌ها:** ribbon pull · petal placement · glass frame closing · paper wrap — همه صدا روشن، بدون گفتار.
**On-screen:** "Making a keepsake, start to finish 🎧"
**Caption:** Sound on 🎧 Making a framed flower keepsake by hand. Everlasting florals, made in Sydney. Save this if it satisfied you 🌸
**CTA:** "Save + follow for more 🎧" · **متریک:** Watch-time · Save

### روش ۸ — کلونِ ادِ برنده · پرفورمنس · ۳۰s
**دسته:** C3/C2 · **مدل:** `ad_reference` → نیازمندِ **آپلودِ یک ویدیوی رفرنسِ گیفتینگ** (خودت انتخاب کن). · **کردیت:** ~۵۰
**نکته:** ساختارِ ادِ اثبات‌شده را بگیر، محصولِ زیمان را جاگذاری کن (Soul Inpaint/Product Placement ۰.۲۵ cr). **بلاکر:** تا رفرنس ندهی، این ساخته نمی‌شود.

### روش ۹ — نسخهٔ دوزبانه (فارسی) · دسترسی · هزینهٔ dub
**دسته:** همه · **مدل:** مسترِ انگلیسی → dubbing فارسی (لیپ‌سینک) · **کردیت:** هزینهٔ dub جدا
**کاربرد:** دسترسی به جامعهٔ ایرانیِ سیدنی (بازارِ گرمِ first-sale-pack). مستر را یک‌بار بساز، فقط dub کن.
**Caption (FA):** هدیه‌های دست‌سازِ ماندگار، ساختِ سیدنی 🌸 DM برای سفارش · تحویلِ محلی · PayID

### روش ۱۰ — میزبانِ ثابتِ برند · برند · زیرساخت
**دسته:** همه · **مدل:** train Soul/Element یک «میزبانِ زیمان» (~۱۰ دقیقه) → استفادهٔ مکرر · **کردیت:** هزینهٔ ترین یک‌بار
**چرا:** یک چهرهٔ ثابت = recognition. **قیدِ برند/اصالت:** اگر آواتارِ AI انسان‌نما استفاده شد، طبق قواعدِ افشای AI پلتفرم‌ها باید شفاف باشد؛ برای اعتمادِ عمیق، چهرهٔ واقعیِ خودت/مامان بهتر است. → این روش **اختیاری** و کم‌اولویت.

---

## ۳. اولویت‌بندیِ ROI با بودجهٔ ~۸۳۵ کردیت

| اولویت | روش | کردیت | چرا اول |
|---|---|---|---|
| ۱ | ۴ · تیوتوریالِ سفارش | ~۵۵ | نزدیک‌ترین به پول، اصطکاکِ سفارش را برمی‌دارد |
| ۲ | ۳ · ریویوِ صادقانه | ~۱۰۰ | objection «پژمرده می‌شه» را می‌بندد |
| ۳ | ۱ · برند-استوری (هیرو) | ~۱۳۵ | اعتمادِ بازارِ گرم + پستِ pin |
| ۴ | ۵ · مونتاژ مناسبت‌ها | ~۸۰ | قصدِ خرید در لحظهٔ مناسبت |
| ۵ | ۷ · ASMR ساخت | ~۱۱۵ | واچ‌تایم/Save، سوختِ الگوریتم |
| ۶ | ۲ · آنباکسینگ | ~۷۰ | Save، اشتیاق |
| **جمعِ فاز ۱** | **۶ ویدیو** | **~۵۵۵** | **~۲۸۰ کردیت ذخیره برای بازتولیدِ برنده‌ها** |

روش‌های ۶ (تستیمونیال)، ۸ (رفرنس لازم)، ۹ (dub)، ۱۰ (آواتار) = فاز ۲، پس از اولین سفارش‌ها یا فراهم‌شدنِ پیش‌نیاز.

## ۴. ریتمِ انتشار (زیرِ سقفِ D4)

۳–۴ ریلز در هفته `[EST ۲۰۲۶]`، بهترین ساعت ۷–۹ صبح و ۱۱–۱۳ به‌وقتِ سیدنی. اما **هر پستِ سفارش‌ساز فقط تا سقفِ ~۳۰ واحد/هفته**. اگر یک ویدیو viral شد و تقاضا از سقف زد → پست‌های بعدی را نگه‌دار (waitlist)، تولید را جلو نینداز. پستِ برند/ASMR (بدونِ CTAِ مستقیمِ خرید) سقف ندارد و می‌تواند مداوم برود.
