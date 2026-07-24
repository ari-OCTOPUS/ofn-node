---
type: proposal
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: draft
tags: [monetization, revenue-diversification, expansion, offer-ladder, track-a]
created: 2026-07-04
updated: 2026-07-04
extends: "[[MASTER-BUILD-2026-07-04]]"
---

# MONETIZATION EXPANSION — تعمیق و تنوع درآمد (Revenue Diversification)

> **مبنا:** درخواست ari «تنوع بیشتر و عمیق‌تر در راه‌های پول درآوردن» + MASTER BUILD §۴/§۸/§۱۲/§۱۷ + وریفای وب ‏2026-07. **کالیبراسیون: واقع‌بینانه** (همان انتخاب پروژه). سطح اطمینان: **High** = چندمنبعه/تأییدشده · **Medium** = تک‌منبع · **Low** = فرضیه/تجربه صنعت/منبع vendor.
> **این ماژول جایگزین §۴ نیست؛ آن را عمیق و پهن می‌کند.** نردبان فعلی (Free page + PPV + Custom + Tips + VIP) هسته می‌ماند؛ اینجا ۷ لایهٔ درآمدی جدید + عمقِ قیمت‌گذاری اضافه می‌شود.
> **قواعد قفل‌شده (بدون استثنا در همهٔ استریم‌ها):** فقط پا · بدون چهره/بدن · geo-block ایران · **پرداخت فقط داخل پلتفرم** (تعریف دقیق در M1) · بدون فکت جغرافیایی شهری · opsec/ناشناسی اولویت اول · 18+ · هیچ نقض ToS.
> **هشدار کالیبراسیون درآمد:** ارقام $500–3000/ماه در بلاگ‌های vendor/SEO ‏(Footly, EcommerceFastlane و…) **survivorship-biased و اغراق‌شده‌اند** [Low]. مبنای واقع‌بینانهٔ ما همان Floor سند اصلی می‌ماند (ماه اول $0–80، افق $1k در ماه ۳–۶). تنوع، **کفِ ریسک را بالا و سقفِ LTV را بلند می‌کند** — نه اینکه ماه اول را منفجر کند.

---

## M0 — اصل حاکم: Atomization (یک شوت → چند محصول)

**عمیق‌ترین اهرم درآمد، «کانال جدید» نیست؛ استخراج چند محصول از همان تولید است.** تیم دونفره با سقف ساعت، نمی‌تواند بی‌نهایت شوت کند — پس هر جلسهٔ ۲–۳ ساعتهٔ §۱۹ باید به‌جای ۱ خروجی، **۸ خروجیِ قابل‌فروش** بدهد. این «عمقِ» درخواست‌شده است: همان زحمت، چند برابر درآمد.

**مثال واقعی — یک شوت «Fresh Pedi» (§۷ ایدهٔ ۱):**

| # | خروجی از همان ۶۰ فایل | کجا فروش می‌رود | مدل درآمد |
|---|---|---|---|
| 1 | ۳ عکس teaser | X + Reddit + فید free OF/Fansly | قیف (رایگان) |
| 2 | ست ۱۰‌عکسی کامل | PPV در OF/Fansly | $10–15 |
| 3 | کلیپ ۳۰ث برس‌زدن لاک | **Clip store** (ManyVids/C4S) | $6–12 a-la-carte |
| 4 | کلیپ ASMR صدای remover | Clip store + PPV | $8–15 |
| 5 | فایل صوتی ۲دقیقه‌ای (sound-only) | Audio pack (M2) | $5–8 |
| 6 | یک frame در bundle فصلی | Vault/Bundle (§۴) | تجمیع در $29–39 |
| 7 | ۱ عکس منتخب برای email drop | لیست ایمیل (M6) | early-access/retention |
| 8 | نسخهٔ چاپی هنری (SFW crop) | Print-on-Demand (M2/M5) | $15–40 passive |

**قاعده:** هیچ شوتی «تک‌مصرف» نیست. در Content Assets (§۱۵) یک فیلد `monetization_paths (multi)` اضافه کن؛ تا وقتی هر asset به ≥۳ مسیر درآمد وصل نشده، «تمام» حساب نمی‌شود. **ROI هر ساعت شوت = درآمد تجمعی همهٔ مسیرها ÷ ساعت** — نه فروش تک‌ست.

---

## M1 — تنوع پلتفرمی (Platform Diversification)

**تعریف دقیق «پرداخت فقط داخل پلتفرم» (رفع سوءتفاهم):** قاعده یعنی **هرگز با یک خریدارِ منفرد پرداخت P2P بیرونی مذاکره نکن** (PayPal/crypto/بانک شخصی = بردار scam + ban + doxx). این قاعده **مانع استفاده از چند پلتفرم قانونی نیست** — هر پلتفرم زیر، payment را داخل خودش پردازش و به حساب برند واریز می‌کند. تنوع پلتفرم ✅ ، پرداخت بیرونیِ فرد ❌.

**سه لایهٔ پلتفرمی (نقش‌ها متفاوت‌اند، نه تکرار هم):**

### الف) Subscription / Fan-platform (رابطه + تکرار)

| پلتفرم | سهم creator | کشف داخلی؟ | قابلیت‌های کلیدی | نکتهٔ opsec / lock-in | نقش در stack |
|---|---|---|---|---|---|
| **OnlyFans** | ~80% | ❌ ندارد | استاندارد بازار، اعتماد خریدار | مالکیت جدید = ریسک سیاست [High] | هستهٔ فعلی |
| **Fansly** | ~80% | ✅ **search/tag** | multi-tier sub، live، paid-DM، custom، payout ۱–۲ روزه | AI-friendly = به‌نفع نیچ | **هم‌وزن OF از روز ۱** (§۸) |
| **Fanvue** | ~85% | ✅ | AI-moderation، engagement بالا | نوظهور، ترافیک کمتر · **قاعده سخت (legal رسمی، 07-05): موجودی بی‌حرکت بعد ۱۲ ماه Dormant/waived → برداشت حداقل سالانه اجباری** | لایهٔ ۳ (ماه ۲+) تست |
| **LoyalFans** | ~80% | ✅ | **live per-minute**، video-call، stories، tips uncapped، wishlist | wishlist را **خاموش کن** (بردار doxx) | برای live/tip اختصاصی |
| **Passes** | ~90% | نیمه | فیچرمحور، فی پایین | mainstream-leaning | اختیاری، ماه ۳+ |

**Patreon حذف:** سیاست ضدمحتوای بزرگسال سخت‌گیر شده؛ ریسک ban دارایی. ❌

### ب) Clip Store — بزرگ‌ترین شکافِ پلنِ فعلی [High]

پلنِ فعلی subscription/PPV-محور است. اما **بخش بزرگی از خریداران feet هرگز subscribe نمی‌کنند — a-la-carte می‌خرند**، و clip storeها **ترافیک fetish موجود** دارند (تو نمی‌سازی، برداشت می‌کنی). این یک موتور کشف + فروش مستقل است:

| پلتفرم | سهم creator | ویژگی | چرا مهم |
|---|---|---|---|
| **ManyVids** | ~80% (کمیسیون ۲۰٪) | clip + cam + fan-club + tips + merch + **contests** | contest = ترافیک رایگان + رتبه؛ اکوسیستم کامل |
| **Clips4Sale** | ~60–80% (۴۰٪ روی tube-traffic / ۲۰٪ روی direct) | قدیمی‌ترین، دستهٔ foot عظیم | intent خالص؛ خریدار آمادهٔ خرید |
| **iWantClips** | tiered (~۶۰–۸۰٪) | فرهنگ fetish/custom/femdom | **custom-heavy** = حاشیهٔ بالا |

**نکتهٔ کلیدی:** clip store **بدون subscription** پول می‌دهد و همان فایل‌های atomized (M0) را می‌فروشد. Time-to-first-$ اغلب کوتاه‌تر از OF است چون buyer-intent بالاست.

### ج) Feet Marketplace (ویترین intent، نه موتور)

| پلتفرم | هزینه/سهم | نکته |
|---|---|---|
| **FeetFinder** | ۱۰–۱۵٪ فی + sub فروشنده ($4.99–14.99/ماه) | ترافیک خریدار بیشتر؛ verification پامحور |
| **Feetify** | **۰٪ کمیسیون** با عضویت ($49/سال) | نگه‌داشتن ۱۰۰٪؛ مکمل خوب |
| **FunWithFeet** | ۰٪ کمیسیون، sub-based | ترافیک کمتر؛ فقط cross-list |
| **Footly** | ۵–۱۵٪ (keep 85–95%) | فید عمودی TikTok-style؛ کشف نوظهور |

**قاعدهٔ صنعت [High]:** هیچ creator موفقی تک‌پلتفرمی نیست؛ top earnerها خروجی را روی ۳–۴ کانال پخش می‌کنند (نمونهٔ رایج: ~۵۰٪ sub-site / ۳۰٪ marketplace / ۱۵٪ clip-store / ۵٪ آرشیو). **این دقیقاً ضدِ ban هم هست** (§۱۸ diversification).

**stack پیشنهادی (به‌ترتیب افزودن، ضدِ overload تیم):** OF + Fansly (روز ۱، §۸) → **ManyVids** (هفتهٔ ۴–۶؛ کم‌زحمت، فقط atomize کلیپ‌های موجود) → FeetFinder یا Feetify (ماه ۲) → Clips4Sale + LoyalFans-live (ماه ۲–۳) → بقیه فقط اگر آستانهٔ ساعت اجازه داد.

---

## M2 — تنوع نوعِ محصول (Product-Type Diversification)

فراتر از «عکس‌ست و ویدئو». هر نوع محصول یک بازار و یک بازهٔ قیمتِ متفاوت باز می‌کند و از همان آرشیو تغذیه می‌شود:

| محصول جدید | چیست | پلتفرم | قیمت | زحمت | حاشیه | نکتهٔ opsec/کلید |
|---|---|---|---|---|---|---|
| **Audio pack (ASMR sound-only)** | فایل صوتی خالص (لوسیون/جوراب/خلخال) | PPV + Gumroad (نسخهٔ SFW) | $5–8 | کم | **بسیار بالا** | تصویر ندارد = صفر ریسک قاب؛ فقط صدای محیط ساکت |
| **Video compilation / Megacut** | تجمیع کلیپ‌های ماه در یک ویدئوی بلند | OF/Fansly/ManyVids | $15–25 | صفر (بازبسته‌بندی) | بالا | passive از آرشیو |
| **Numbered Collector Set** | ست‌های شماره‌دار تم‌دار (نه NFT) | فید + bundle | $10–35 | کم | بالا | برای پرسونا Quiet Collector؛ روی پلتفرم، **بدون crypto** |
| **Wallpaper / lockscreen pack** | ۵–۱۰ فریم زیبایی‌شناسانه موبایل | Gumroad/OF | $4–7 | کم | بالا | crop امن؛ watermark سبک |
| **Foot-art Calendar (سالانه)** | تقویم ۱۲‌ماهه هنری | PDF دیجیتال + POD | $12–25 | متوسط (۱‌بار/سال) | بالا | محصول سالانهٔ برند؛ زاویهٔ «artistry» |
| **Fine-art Print (POD)** | چاپ هنری SFW از فریم قوی | Redbubble/Society6/Etsy | $15–40 | کم (POD می‌چاپد/می‌فرستد) | متوسط | **creator هرگز نمی‌فرستد**؛ ملاحظهٔ هویت Etsy → M5 |
| **Live stream (tips/goals)** | پخش زندهٔ feet-only با تیپ/هدف | Fansly/LoyalFans/ManyVids | tip + per-minute | متوسط | بالا | نیاز به **صبا حاضر** + opsec پس‌زمینه/صدا؛ ابزار lead-gen |
| **Timed DM session** | چت زمان‌دار محدود و قیمت‌دار | OF/Fansly paid-DM | $/بازهٔ ۱۵د | زمان‌بر | بالا | سقف تعداد؛ فقط ساعات فعال |

**دو بردهٔ سریع [High]:** (۱) **Audio pack** — از هر شوت ASMR که همین حالا در §۷ داری، یک محصول صوتی جدا بساز؛ تولید تقریباً صفر، حاشیه نزدیک ۱۰۰٪. (۲) **Megacut ماهانه** — کلیپ‌های موجود را یک‌بار به هم بچسبان؛ محصول premium بدون شوت جدید.

**Live = تغییردهندهٔ بازی، اما شرطی:** live بالاترین tip-per-minute را دارد و رابطه می‌سازد (§۲ پرسونا Ritual/Commissioner)، ولی **real-time است و قاب کنترل‌ناپذیرتر** — چک‌لیست ۵موردی §۱۷ (آینه/پنجره/سند/تتو/پس‌زمینه) + قطع هر صدای محیطی geo-tell قبل از هر پخش. استراتژی درست (§منبع صنعت): live = lead-gen، نه درآمد اصلی؛ بینندهٔ live را به sub/custom قیف کن.

---

## M3 — عمقِ قیمت‌گذاری و بسته‌بندی (Pricing Depth)

نردبان §۴ خطی است؛ این‌ها **مکانیزم‌های استخراج ارزش** روی همان نردبان‌اند:

1. **Multi-tier subscription (به‌جای فقط free+VIP):** روی Fansly سه tier: `Free (قیف)` · `$9.99 Core (فید کامل + ۱ PPV/هفته)` · `$24.99 Premium (همه + custom priority + رأی)`. free-page را برای کشف نگه‌دار، ولی tierِ میانی، خریدارِ «ماهی کمی می‌دهم ولی منظم» را می‌گیرد که PPV تکی از دستش می‌رود. **[Medium — تست A/B لازم]**
2. **Anchor & Decoy:** همیشه یک آیتم گران‌تر کنار پیشنهاد اصلی بگذار تا وسط ارزان‌تر جلوه کند (Vault $39 کنار ست $12 → ست ارزان به‌نظر می‌رسد).
3. **Auction برای اسلات نادر:** ۱ اسلات custom «امضا» در ماه را روی iWantClips/ManyVids **به مزایده** بگذار (highest bidder). کمیابی واقعی → کشف سقف قیمت. **[Low]**
4. **Crowd-goal / unlock-at-$X:** روی Fansly/LoyalFans هدف تیپ بگذار: «تا $X جمع شد، ست Y آزاد می‌شود». درآمد جمعی + هیجان گروهی. **[Medium]**
5. **Loyalty / streak & leaderboard:** جدول top-tipper ماه + پاداش (frame اختصاصی). رقابت مثبت، LTV↑. **[Low]**
6. **Founding-member (تزریق نقدینگی اولیه):** ۲۰ عضو «بنیان‌گذار» با نرخ lifetime پایین‌تر و badge → پول نقد زودهنگام + هستهٔ وفادار. **[Low]**
7. **Grandfather window (ضدِ ریزش هنگام گران‌کردن):** همان §۴ — «نرخ فعلی تا جمعه برای شما قفل است».
8. **Bundle laddering:** Sampler $29 → Season Vault $59 → Year Vault $99 (§M7). هر پله، سبد را بزرگ‌تر می‌کند.

---

## M4 — عمقِ Custom و سرویس (بالاترین حاشیه، داخل مرزها)

Custom پرحاشیه‌ترین درآمد است (§۴). **بدون شکستن هیچ مرز** (فقط پا، بدون چهره/بدن، بدون ملاقات، روی پلتفرم) می‌توان آن را عمیق‌تر پول‌ساز کرد:

| لایهٔ custom | چیست | قیمت | چرا |
|---|---|---|---|
| **Tiered packages** | Bronze (۵ عکس) / Silver (۱۰ عکس+کلیپ) / Gold (ست+ویدئو+priority) | $30 / $60 / $120 | خریدار خودش سطح را انتخاب می‌کند = up-sell خودکار |
| **Personalized ASMR audio** | فایل صوتی سفارشی (نام مستعار فن در ابتدای صدا) | $20–40 | تولید ارزان، حس شخصی بالا، بدون ریسک تصویری |
| **Rent-a-ritual (recurring custom)** | اشتراک: هر هفته ۱ frame شخصی‌سازی‌شده | $25–40/ماه | custom را به **درآمد تکرارشونده** تبدیل می‌کند |
| **Monthly limited menu** | منوی custom با ۳ اسلات/ماه، تم اعلام‌شده | scarcity pricing | کمیابی واقعی → قدرت قیمت |
| **Dedication product line** | ارتقای tip §۴ به محصول: ست کوچک با پیام (اسم مستعار) | $15–30 | خط محصول مستقل از دلِ یک tip |
| **Rush / priority fee** | تحویل سریع‌تر | +۳۰–۵۰٪ | حاشیهٔ خالص روی زمان |

**قاعدهٔ ثابت (§۱۰.۵ + §۱۷):** فرم intake ۵سؤالی، ۵۰٪ پیش‌پرداخت داخل پلتفرم، اسکریپت رد محترمانه برای هر درخواست خارج‌مرز، veto صبا. هیچ‌کدام از این لایه‌ها مرز را جابه‌جا نمی‌کند — فقط **بسته‌بندی و قیمت** را عمیق‌تر می‌کند.

---

## M5 — B2B / Licensing / Affiliate (پول بدون فنِ مستقیم)

لایهٔ درآمدی که به تعداد فن گره نخورده — بلکه به **دارایی محتوا و برند**:

| استریم | مدل | درآمد | ریسک/شرط |
|---|---|---|---|
| **Affiliate (props)** | لینک محصولات لاک/foot-care/جوراب/صندل در سمت SFW (IG/TikTok §۸ فاز۲) + email | کمیسیون ۳–۱۰٪ | فقط سمت SFW برند؛ Amazon Associates یا برنامهٔ برند |
| **Print-on-Demand (fine-art)** | فروش چاپ هنری SFW (M2) | $15–40 passive | نیاز به هویت فروش در Etsy → **به G3/ABN موکول کن** |
| **Sponsored (nail/foot-care brands)** | پست پولی SFW برای برند foot-care/لاک | flat fee | فقط SFW-aesthetic؛ برند بزرگسال‌محور را رد کن |
| **Digital template/preset** | فروش preset ادیت یا «guide نور» (know-how) | $8–20 | محصول know-how، صفر ریسک تصویری |

**قاعدهٔ opsec برای این لایه:** هرچیز SFW باید زیر **همان برند faceless** بماند (نه هویت شخصی)، fulfillment دیجیتال/POD (creator هرگز نمی‌فرستد)، و **پل‌نزدن هویت adult↔mainstream**. اگر Etsy/POD نیاز به نام حقوقی دارد، تا وجود ABN/شخصیت حقوقی (§۱۲ G3) **صبر کن** — این هم‌راستا با roadmap فعلی است، نه override.

**استریم‌های ردشده در این لایه (صادقانه):** licensing دیتاست/AI (از دست‌رفتن کنترل تصویر + بردار deepfake) و stock-licensing عمومی (opsec) → **رد/تعویق**. جزئیات در M10.

---

## M6 — عمقِ Community و درآمد تکرارشونده (LTV)

هدف: بالا بردن **LTV** (ارزش طول‌عمر هر فن) به‌جای صرفاً جذب فن جدید — چون هزینهٔ نگه‌داشتن << جذب.

- **Email list (§۱۲ ماه ۲ — عمیق‌تر):** SendX از فالوورهای گرم. درآمدِ ایمیل: drop اختصاصیِ فقط-ایمیل، early-access ۲۴ساعته به ست جدید، کمپین win-back (§۱۰.۶). ایمیل **دارایی مالکیتی ضدِ ban** است (§۱۸) — اگر فردا اکانتی سوخت، مخاطب می‌ماند.
- **Cross-platform funnel:** خریدارِ clip-store → دعوت به sub (رابطه) → عضو email. هر پلتفرم یک درِ ورود، همه به سمت رابطهٔ عمیق‌تر.
- **VIP tier + gamification (§۴ عمیق‌تر):** badge، leaderboard تیپ، «perk ماهانه» (نام مستعار روی شیشهٔ لاک §۹.۴۸). حس تعلق = retention.
- **Referral fan-to-fan:** «فنی که فن بیاورد، ۱ ست هدیه». رشد ارگانیک صفرهزینه.
- **ManyVids contests:** شرکت در contest = ترافیک رایگان + جایزهٔ نقدی + رتبهٔ کشف. عملاً marketing پولی‌شده بدون هزینه.

**KPI جدید برای §۱۴:** `Repeat rate`، `LTV per fan`، `Email→purchase %`. تنوع فقط وقتی «عمیق» است که این‌ها رشد کنند، نه صرفاً تعداد کانال.

---

## M7 — Back-Catalog و درآمد Passive (دارایی انباشته)

**محتوا دارایی مستهلک‌نشدنی است اگر کاتالوگ شود.** بعد از ماه ۱، آرشیو خودش می‌فروشد:

- **Repackage:** ست‌های قدیمی را در bundleهای جدید تم‌دار بازچینش کن («۱۲ هفته، ۱۲ رنگ» §۷.۱۵ → Vault). همان فایل، محصول نو.
- **Evergreen clip-store:** کلیپ‌های قدیمی در ManyVids/C4S **بدون کار جدید** سال‌ها می‌فروشند — فروشگاه دائمی.
- **Automated welcome-PPV:** ست First Steps ($6–8) در welcome خودکار به **هر فالوور جدید** — فروش روی autopilot (§۴/§۱۰.۱).
- **Annual Vault mega-product:** سالگرد برند (§۷.۸۰) → «Year One Vault» $99. محصول سالانهٔ high-ticket از آرشیو موجود.
- **Seasonal re-release:** محتوای فصلی AU (§۷ F) هر سال دوباره منتشر/فروخته می‌شود (فصل معکوس نیم‌کره = زاویهٔ یکتا §۱).

**اصل:** تا ماه ۳، بخشی از درآمد باید **بدونِ تولیدِ آن ماه** بیاید. این سقفِ ساعت تیم را از سقفِ درآمد جدا می‌کند — یعنی مقیاس بدون burnout (§۱۸).

---

## M8 — نقشهٔ توالی (Sequencing — ضدِ overload تیم دونفره)

هم‌راستا با roadmap §۱۲. قاعده: **حداکثر ۱ استریم جدید هر ۲–۳ هفته**، و هر استریم جدید باید یا atomization باشد (زحمت≈۰) یا آستانهٔ ساعت اجازه دهد.

| فاز | ماه | اضافه‌شونده (روی پلنِ فعلی) | چرا اینجا | زحمت افزوده |
|---|---|---|---|---|
| **Validate** | ۱ | پلن فعلی + (اواخر ماه) **ManyVids** + **Audio pack** | هر دو از فایل‌های همین‌الان‌شوت‌شده؛ atomization خالص | تقریباً صفر |
| **Systemize** | ۲ | **FeetFinder یا Feetify** · شروع **Email (SendX)** · تست **multi-tier Fansly** · اولین **live** (LoyalFans) · **منوی custom tiered** | data کافی جمع شده؛ رابطه شکل گرفته | متوسط |
| **Scale-or-Kill** | ۳+ | **Clips4Sale** · **rent-a-ritual + custom auction** · **VIP gamification** · **contests** · **Year/Season Vault** · **founding-member** | فقط روی برنده‌ها؛ back-catalog حالا وجود دارد | متوسط، هدف‌مند |
| **معوق تا G3/ABN** | — | **POD fine-art** · **Affiliate SFW** · **Sponsored** | نیاز به هویت حقوقی/ABN؛ منتظر gate | — |

**gate عبور هر فاز = همان G1/G2/G3 §۱۲.** استریم جدید اضافه نمی‌شود مگر KPIهای فاز قبل سبز باشند و ساعت صبا زیر سقف بماند (§۱۶).

---

## M9 — نقشهٔ Portfolio (امتیازدهی ROI ‏1–10)

امتیاز بالاتر = بهتر در آن ستون (Opsec: ۱۰=امن‌ترین · کم‌زحمتی: ۱۰=کم‌زحمت‌ترین).

| استریم | درآمد‌بالقوه | حاشیه | سرعت به اولین $ | مقیاس‌پذیری | امنیت opsec | کم‌زحمتی | اولویت |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **ManyVids (clip)** | 8 | 8 | 8 | 9 | 8 | 8 | **۱** |
| **Audio pack** | 5 | 10 | 7 | 8 | 10 | 9 | **۱** |
| **Custom depth (tiered/rent-a-ritual)** | 9 | 10 | 6 | 5 | 8 | 5 | **۱** |
| **Multi-tier subscription** | 7 | 9 | 6 | 8 | 9 | 8 | ۲ |
| **Back-catalog / Megacut (passive)** | 6 | 9 | 5 | 9 | 9 | 9 | ۲ |
| **Email list (deepened)** | 6 | 9 | 4 | 8 | 8 | 7 | ۲ |
| **Clips4Sale** | 7 | 7 | 7 | 8 | 8 | 8 | ۲ |
| **VIP + gamification** | 6 | 9 | 5 | 7 | 9 | 7 | ۲ |
| **FeetFinder / Feetify** | 5 | 7 | 6 | 6 | 8 | 7 | ۳ |
| **Live streaming** | 8 | 7 | 6 | 5 | **5** | 4 | ۳ |
| **POD fine-art** | 4 | 6 | 3 | 8 | 6 | 7 | ۴ (G3) |
| **Affiliate SFW** | 3 | 9 | 3 | 7 | 6 | 6 | ۴ (G3) |

**۵ افزودهٔ با بالاترین ROI (به‌ترتیب اجرا):**
1. **ManyVids** — درآمد + کشفِ مستقل، از فایل‌های موجود؛ کم‌ریسک‌ترین «کانال جدید».
2. **Audio pack** — حاشیهٔ نزدیک ۱۰۰٪، صفر ریسک تصویری؛ بردِ رایگان.
3. **Custom depth (tiered + rent-a-ritual)** — پرحاشیه‌ترین دلار + تبدیل custom به تکرارشونده.
4. **Multi-tier subscription (Fansly)** — گرفتنِ خریدارِ «ماهی کم ولی منظم» که الان از دست می‌رود.
5. **Email deepening** — LTV↑ + دارایی ضدِ ban (بیمهٔ کل کسب‌وکار).

---

## M10 — استریم‌های ردشده / محتاط (صداقت، نه سانسور)

هر استریمی که با قواعد قفل‌شده تعارض دارد — صریح رد یا محتاط شد:

| استریم | حکم | دلیل |
|---|---|---|
| **آیتم فیزیکی پوشیده (جوراب/جوراب‌شلواری)** | ❌ **رد** | آدرس ارسال/بسته‌بندی/KYC = شکستن ناشناسی؛ بردار stalking/doxx. حتی با fulfillment واسطه، سطح ریسک با opsec پروژه ناسازگار است |
| **Wishlist عمومی (Amazon/…)** | ❌ **رد** | لوکیشن/آدرس را لو می‌دهد؛ بردار doxx مستقیم. (Throne masked هم بردار کالای فیزیکی می‌ماند) |
| **تیپ crypto / پرداخت بیرونی فرد** | ❌ **رد** | نقض «پرداخت داخل پلتفرم» §۱۷؛ scam + ban + ردگیری‌ناپذیری |
| **NFT / collectible بلاکچینی** | ❌ **رد** | بازار عملاً مرده ۲۰۲۶ + قاعدهٔ no-crypto. جایگزین: Numbered Collector Set روی پلتفرم (M2) |
| **AI-chatbot برای DM** | ⚠️ **محتاط** | با مدلِ «۱:۱ انسانی + دستیارِ افشاشده» (§۱۰) تعارض دارد مگر **صریحاً افشا شود**. اگر استفاده شد، باید در welcome گفته شود — وگرنه صداقتِ برند (دارایی اصلی، §۱۳ تست ۱۰) می‌شکند |
| **licensing دیتاست/AI** | ❌ **رد/تعویق** | از دست‌رفتن کنترل تصویر + بردار deepfake؛ ضدِ opsec |
| **Patreon** | ❌ **رد** | سیاست ضدِ بزرگسال؛ ریسک ban دارایی |
| **Meetup / off-platform / city-geo** | ❌ **رد** (قفل پروژه) | خط قرمز ثابت §۱۷ |

---

## M11 — خلاصه و اقدام

**Revenue mix هدف (ماه ۳+، تصویری/Low):** Subscription+PPV ~۴۵٪ · Custom ~۲۵٪ · Clip stores ~۱۵٪ · Tips+Live ~۱۰٪ · Passive (audio/back-catalog/POD) ~۵٪. هیچ استریمی >۵۰٪ نباشد (ضدِ ban + ضدِ نوسان).

**چرا این «عمیق‌تر» است، نه فقط «بیشتر»:** درآمد از **۳ محور هم‌زمان** بزرگ می‌شود — (۱) عرض: چند پلتفرم/محصول؛ (۲) عمق: چند مسیرِ درآمد از هر شوت (M0) و چند مکانیزم قیمت روی هر فن (M3)؛ (۳) زمان: back-catalog که سقفِ ساعت را از سقفِ درآمد جدا می‌کند (M7). نتیجه: **LTV↑، ریسک ban↓، وابستگی به «تعداد فن جدید»↓.**

**۵ اقدام همین این هفته (صفرهزینه، صفرِ نقضِ قاعده):**
1. در Content Assets §۱۵ فیلد `monetization_paths (multi)` اضافه کن؛ قاعدهٔ «هر asset ≥۳ مسیر» را قفل کن (M0).
2. اکانت **ManyVids** بساز (geo-block IR)، ۳–۵ کلیپِ همین‌حالا‌موجود را a-la-carte بگذار.
3. از شوت‌های ASMR §۷، اولین **Audio pack** ($5–8) را بساز — تولید تقریباً صفر.
4. منوی **Custom tiered** (Bronze/Silver/Gold) و ایدهٔ **rent-a-ritual** را در §۴ ثبت کن.
5. تصمیم **multi-tier Fansly** را برای تست ماه ۲ در Experiment Log §۱۵ به‌عنوان فرضیهٔ جدید بنویس.

**سازگاری با اسناد قفل‌شده:** هیچ تعارضی — فقط پا، geo-block ایران، پرداخت داخل پلتفرم، بدون شهر، مدل افشاشده، و opsec در **همهٔ** استریم‌های جدید اعمال و هر استریمِ ناسازگار در M10 رد شد. **آماده برای verdict انسانی.**

---

## Sources (وریفای پلتفرم/فی — ۲۰۲۶-۰۷)

- OnlyFans alternatives & payout %: [Only Gems — Payout Methods Compared 2026](https://onlygemsmanagement.com/blog/payout-methods-every-platform-compared-2026/) · [Supercreator — OF Alternatives 2026](https://www.supercreator.app/guides/onlyfans-alternatives) · [Sozee — Top OF Alternatives 2026](https://sozee.ai/resources/top-onlyfans-alternatives-2026/)
- Clip stores (commission): [Medium — ManyVids vs Clips4Sale](https://medium.com/@Betterfans/manyvids-vs-clips4sale-what-is-the-difference-between-the-two-15e4b5d87255) · [Clips4Sale Creator Payouts](https://clips4salecreator.freshdesk.com/en/support/solutions/folders/151000545431) · [Postunreel — Clips4Sale Guide 2025](https://postunreel.com/blog/clips4sale-creator-monetization-guide)
- Live/tips features: [Only Gems — Multi-Platform 2026](https://onlygemsmanagement.com/blog/loyalfans-mym-manyvids-beyond-onlyfans-multi-platform-guide-2026/) · [premium.chat — LoyalFans guide](https://premium.chat/blog/everything-adult-content-creators-need-to-know-about-loyalfans/)
- Feet marketplaces & fees: [Footly — Feet Pics Platform Fees 2026](https://www.tryfootly.com/blog/feet-pics-platform-fees-comparison-2026) · [Footly — FeetFinder vs FunWithFeet 2026](https://www.tryfootly.com/blog/feetfinder-vs-funwithfeet-2026) · [EcommerceFastlane — FeetFinder vs Feetify](https://ecommercefastlane.com/feetfinder-vs-feetify/)
- Market size & earnings (⚠️ vendor/SEO — survivorship-biased, treated as [Low]): [Footly — How Much 2026](https://www.tryfootly.com/blog/how-much-can-you-make-selling-feet-pics-2026) · [EcommerceFastlane — Feet Pics Statistics 2026](https://ecommercefastlane.com/feet-pics-statistics/)
