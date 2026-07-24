---
type: decision-matrix
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: proposal (awaiting human verdict)
created: 2026-07-10
created_by: agent (Claude Fable 5 — اجرای PROMPT A / M2)
input: "[[RESEARCH-INTEGRATION-round2-2026-07-10]] §۴ (کاتالوگ ۵۸-روشی) + §۲–۳"
tags: [project-f, decision-matrix, prioritization, m2]
aliases: ["Decision Matrix", "M2", "ماتریس تصمیم"]
---

# DECISION MATRIX — Project-F (M2 / 2026-07-10)

> فرمول: `Composite = Impact×0.25 + Speed×0.15 + Fit×0.20 + (10−Effort)×0.10 + (10−BanRisk)×0.30` — وزن سنگین ban-risk چون از دست رفتن اکانت اصلی در فاز validation فاجعه‌بار است.
> **Gate rule:** هر ردیف `prohibited` یا `BanRisk ≥ 8` → مستقیم به Avoid، فارغ از Composite.
> **راستی‌آزمایی compliance:** همهٔ ستون‌های compliance همین امروز (2026-07-10) در round2 با منابع اولیه (policy رسمی پلتفرم‌ها) verify شده‌اند — سرچ مجدد همان‌روز redundant بود؛ ارجاع هر قضاوت: [[RESEARCH-INTEGRATION-round2-2026-07-10|round2]] §۲/§۴/§۱۰. امتیازها `[EST — قضاوت ساختاریافته روی شواهد round2]` مگر خلاف ذکر شود.

## ۱. ماتریس کامل (مرتب بر Composite نزولی)

| Tactic | Cat | Impact | Speed | Fit | Effort | BanRisk | Conf | Compliance | **Composite** | توجیه یک‌خطی |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 لینک‌هاب 18+ با geo-filter (GAML) | Infra | 8 | 9 | 10 | 1 | 1 | H | compliant | **8.95** | پیش‌نیاز همهٔ قیف‌ها؛ صفر ریسک؛ راه‌اندازی یک‌ساعته |
| B1 پروفایل X کامل + pinned funnel | X | 7 | 9 | 9 | 1 | 1 | H | compliant | **8.50** | تنها پلتفرم بزرگ با لینک مستقیم مجاز به OF `[FACT]` |
| D3 tracking-link برای هر کانال | Infra | 6 | 9 | 10 | 1 | 1 | H | compliant | **8.45** | attribution بومی OF؛ بدون داده هیچ تصمیمی ممکن نیست |
| A7 پروفایل Reddit به‌مثابه funnel | Reddit | 6 | 9 | 9 | 1 | 1 | H | compliant | **8.25** | رایگان، دائمی، بدون ریسک sub-rule |
| E1 نردبان PPV در DM (ارسال دستی) | Monetize | 9 | 8 | 9 | 4 | 2 | H | compliant | **8.25** | موتور درآمد اصلی نیش؛ الگوی درفت-AI/ارسال-انسان |
| B2 برچسب‌گذاری محافظه‌کارانهٔ X ‏(re-scored ‏T6) | X | 7 | 8 | 10 | 1 | 4 | M | compliant | **7.65** | متن policy معافیت SFW را صریح دارد `[FACT — help.x.com، fetch ‏07-10]`، ولی ریسک re-classification/force-label واقعی است → حالت دو-وضعیتی: پستِ کاملاً SFW بدون label + هر رسانهٔ مرزی sensitive؛ تنظیم اکانت sensitive-media روشن (پیش‌فرض محافظه‌کار T3) |
| E2 خط تولید Custom با فرم سفارش | Monetize | 9 | 6 | 9 | 5 | 2 | H | compliant | **7.85** | ۴۰–۶۰٪ درآمد فروشنده‌های بالغ `[COI]`؛ حاشیهٔ بالاترین |
| E5 منوی Tip روی پروفایل | Monetize | 6 | 8 | 9 | 1 | 2 | H | compliant | **7.80** | صفر هزینه، شفاف، بدون ریسک |
| A1 پست OC در subهای feet (با WM) | Reddit | 8 | 7 | 9 | 5 | 3 | H | compliant | **7.45** | موتور رشد #۱ طبق ۳ راند تحقیق؛ ریسک فقط mod-level |
| A2 پست verification (چاپی، بدون دست‌خط) | Reddit | 5 | 8 | 9 | 2 | 2 | H | compliant | **7.45** | enabler ورود به subها؛ opsec: متن چاپی |
| D2 ایمیل‌لیست SendX + چک‌لیست Spam Act | Infra | 7 | 4 | 9 | 4 | 1 | H | compliant | **7.45** | تنها دارایی ضد-deplatforming؛ اثرش دیرمی‌رسد |
| A3 نردبان subها (کوچک→بزرگ) | Reddit | 7 | 6 | 9 | 4 | 3 | H | compliant | **7.15** | مسیر رشد پایدار karma/اعتبار |
| E3 باندل ۳/۶ماهه (۱۰–۴۰٪ تخفیف) | Monetize | 5 | 6 | 7 | 1 | 1 | M | compliant | **7.15** | feature بومی؛ cash جلو می‌کشد؛ LTV واقعی نامعلوم |
| B3 کیدنس X ‏۲–۴ پست/روز از بانک ۳۰-کلیپ | X | 7 | 5 | 9 | 6 | 2 | M | compliant | **7.10** | وابسته به delivery صبا (ریسک R1، نه ریسک ban) |
| E4 کمپین win-back بومی | Monetize | 5 | 6 | 7 | 2 | 1 | M | compliant | **7.05** | ارزان‌ترین درآمد برگشتی؛ از ماه ۲ معنا دارد |
| E7 پاداش renew-on | Monetize | 4 | 5 | 7 | 1 | 1 | M | compliant | **6.75** | خرد اما رایگان؛ اثر تجمعی روی rebill |
| A5 زمان‌بندی Reddit با Social Rise (فقط schedule) | Reddit | 5 | 8 | 8 | 2 | 4 | M | compliant* | **6.65** | بهره‌وری؛ *compliance خوداظهاری vendor + تبلیغ proxy → فقط صف پست، صفر engagement-automation |
| E6 کمپین‌های فصلی تقویم ۲۰۲۷ | Monetize | 5 | 4 | 9 | 4 | 2 | M | compliant | **6.65** | سیگنال فرهنگی فقط بصری (قاعدهٔ #۶) |
| A4 cross-post حساب‌شده (۳–۵ sub) | Reddit | 6 | 8 | 8 | 2 | 5 | M | compliant | **6.60** | ارزان و سریع؛ ریسک duplicate-filter با فاصله‌گذاری مهار می‌شود |
| B5 S4S بعد از 1k فالوئر @ ≥2٪ | X | 6 | 5 | 7 | 2 | 3 | M | compliant | **6.55** | مصوب قبلی؛ بازار اسکم‌خیز → فقط هم‌تراز verify‌شده |
| A6 comment-engagement هدفمند | Reddit | 5 | 5 | 7 | 5 | 2 | H | compliant | **6.30** | اعتبارساز؛ وقت‌خوار؛ اتومات‌ناپذیر (قاعده) |
| F1 S4S عمومی با هم‌ترازها | Promo | 5 | 5 | 7 | 2 | 3 | M | compliant | **6.30** | مثل B5 اما cross-platform؛ audience-mismatch رایج |
| D6 Bluesky (کانال نوظهور) | Infra | 4 | 4 | 7 | 2 | 2 | M | compliant | **6.20** | adult-tolerant بومی؛ جامعهٔ کوچک → بلیت ارزان تنوع |
| B4 reply-engagement نیش در X | X | 5 | 4 | 7 | 6 | 2 | H | compliant | **6.05** | رشد ارگانیک واقعی؛ گران از نظر وقت |
| F3 خرید shoutout پولی (مبلغ خرد + track-link) | Promo | 4 | 7 | 6 | 2 | 4 | L | gray | **5.85** | نتیجه نامعلوم، بازار اسکم؛ فقط تست ≤A$30 |
| B6 X Communities نیش | X | 4 | 5 | 6 | 3 | 3 | M | compliant | **5.75** | کم‌هزینه؛ قوانین داخلی هر community چک شود |
| G2 آینهٔ Fanvue (آپلود دوره‌ای) | Mkt | 3 | 4 | 6 | 2 | 2 | M | gray | **5.75** | ارزان اما بند مصادرهٔ ۱۲ماهه → برداشت فصلی الزامی `[FACT]` |
| G3 استاک feet ‏(Adobe/Foap) | Adjacent | 2 | 2 | 8 | 5 | 1 | M | compliant | **5.60** | SFW کامل؛ درآمد $0–100/ماه `[EST]`؛ گره #۱۶ هویت |
| C2 IG Reels ‏repurpose | SFW-funnel | 6 | 5 | 7 | 3 | 6 | M | gray | **5.55** | حجم بالا اما shadowban/ban واقعی؛ اکانت قربانی فرض شود |
| D4 کانال برودکست تلگرام SFW | Infra | 4 | 5 | 6 | 2 | 4 | M | gray | **5.55** | مجاورت خطرناک با قاعدهٔ #۳ → فقط توزیع teaser، صفر مذاکره |
| A8 ساب‌ردیت اختصاصی برند | Reddit | 4 | 2 | 7 | 6 | 2 | M | compliant | **5.50** | ارزشش بعد از G2؛ فعلاً هزینهٔ نگه‌داری > بهره |
| C1 TikTok کاملاً SFW (bridge) | SFW-funnel | 8 | 6 | 7 | 8 | 7 | M | gray | **5.40** | بزرگ‌ترین حجم بالقوه، بزرگ‌ترین ریسک پاکسازی `[FACT — Rolling Stone]` |
| E8 صفحهٔ VIP دوم | Monetize | 4 | 2 | 6 | 5 | 2 | M | compliant | **5.40** | فقط بعد از دادهٔ E1–E3 (روز ۹۰+) |
| D5 وب‌سایت/بلاگ SEO برند | Infra | 4 | 1 | 6 | 8 | 1 | M | compliant | **5.25** | ROI دیررس؛ post-G2؛ مالکیت کامل کانال |
| G4 ‏parts-modeling استرالیا | Adjacent | 3 | 2 | 5 | 6 | 1 | L | gray | **5.15** | نیاز هویت واقعی → tension حل‌نشدهٔ #۱۶؛ پارک |
| G1 ‏FeetFinder (لیستینگ passive) | Mkt | 2 | 4 | 5 | 3 | 3 | H | gray | **4.90** | سه شاهد صفر-درآمد؛ pay-before-earn؛ حداکثر آزمایش post-G2 |
| C3 YouTube Shorts | SFW-funnel | 4 | 3 | 6 | 3 | 5 | M | gray | **4.85** | repurpose سوم؛ strike-risk؛ اولویت پایین |
| A10 ‏AMA/محتوای SFW در subهای عمومی | Reddit | 3 | 3 | 5 | 5 | 4 | L | gray | **4.50** | خروج از نیش؛ برچسب self-promo |
| B8 ‏thread روایی «پشت‌صحنهٔ faceless» | X | 3 | 3 | 5 | 5 | 4 | L | gray | **4.50** | opsec-حساس؛ هر خط بازبینی انسانی |
| C4 ‏Pinterest بردهای aesthetic | SFW-funnel | 3 | 3 | 6 | 4 | 5 | L | gray | **4.50** | policy ضد-adult سختگیر؛ فقط تصویر ۱۰۰٪ SFW |
| F5 micro-collab غیرمستقیم SFW | Promo | 3 | 3 | 5 | 5 | 4 | L | gray | **4.50** | زنجیرهٔ افشای هویت؛ ارزش نامطمئن |
| F2 collab محتوایی (Release Form الزامی) | Promo | 5 | 3 | 4 | 6 | 5 | M | compliant-gated | **4.40** | برای برند faceless عملاً سخت؛ verdict انسانی + فرم OF `[FACT-secondary]` |

### ردیف‌های Gate-شده (حذف از Do فارغ از Composite)
| Tactic | Compliance | BanRisk | دلیل | جایگزین امن |
|---|---|---|---|---|
| A9 ‏Reddit Ads | prohibited | 10 | adult در policy تبلیغات ممنوع `[FACT — رسمی]` | A1–A7 ارگانیک |
| B7 ‏X Ads | prohibited | 10 | «adult products/services» ممنوع `[FACT]`؛ ادعای ACC جعلی | B1–B5 |
| C5 ذکر OF در TikTok/IG | prohibited | 10 | sexual-solicitation policy `[FACT]` | C1/C2 ‏bridge |
| F4 آژانس/مدیریت | prohibited (فعلاً) | 8 | کنترل credential + مغایر privacy دوطرفه؛ مصوب round1: آرشیو تا G3+ | مغز داخلی + این ماتریس |
| P1 ‏mass/cold-DM | prohibited | 10 | spam policy همه‌جا + قاعدهٔ #۷ | A6/B4 |
| P2 بات auto-post/reply/DM | prohibited | 10 | ToS + قاعدهٔ قفل‌شده | صف درفتِ انسان-تأیید |
| P3 ‏fake/sockpuppet | prohibited | 10 | ban-wave + فریب | رشد ارگانیک |
| P4 خرید فالوئر/pod | prohibited | 9 | مرگ الگوریتمی + تقلب | S4S واقعی |
| P5 ‏scrape + cold-outreach | prohibited | 10 | نقض API ToS + privacy | inbound قیف D1–D3 |
| P6 پرداخت خارج پلتفرم | prohibited | 10 | **قاعدهٔ #۳** + ban دائم | in-platform only |
| P7 ‏AI-chat خودکار | prohibited | 9 | ToS صریح OF/Fansly `[FACT]` | درفت AI → ارسال دستی |
| P8 ‏impersonation فریبنده | prohibited | 9 | اخلاق + ریسک رسانه‌ای (#۱۴) | سیاست شفافیت مکتوب |
| P9 ‏giveaway فریبنده | prohibited | 8 | deceptive practice + ACL استرالیا | promo واقعی E4 |
| P10 دستکاری review/upvote | prohibited | 9 | fraud | کیفیت واقعی |
| P11 هدف‌گیری ایران / افشای شهر | prohibited | 10 | **قواعد #۲ و #۶** | geo-block + «Aussie» |
| P12 دور زدن age-gate | prohibited | 10 | خط قرمز مطلق | گیت 18+ در D1 |

## ۲. سه سبد (Buckets)

**🟢 Do-Now (Composite ≥ 7.0، همه compliant):** D1 · B1 · D3 · A7 · B2 · E1 · E2 · E5 · A1 · A2 · D2 · A3 · E3 · B3 · E4 — این ۱۵ مورد = هستهٔ فاز validation؛ با ACQUISITION-ENGINE هم‌راستاست.
**🟡 Test-Carefully (5.5–7.0 یا gray با مهار):** E7 · A5(فقط schedule) · E6 · A4 · B5 · A6 · F1 · D6 · B4 · F3(≤A$30) · B6 · G2(با برداشت فصلی) · G3 · C2 · D4(صفر مذاکره) · A8(post-G2) · C1(اکانت قربانی) · E8(روز ۹۰+) · D5(post-G2) — هرکدام با شرط مهار مشخص در ماتریس.
**🔴 Avoid-or-Watch:** همهٔ جدول Gate-شده (A9, B7, C5, F4, P1–P12) + G1(سه شاهد صفر-درآمد → watch) + G4/F2/F5/C3/C4/A10/B8 (Composite <5.2 یا گره باز — فعلاً نگاه، نه اجرا).

## ۳. توجیه Top-5 + counter-argument

| رتبه | Tactic | چرا بالا | ردِ محتمل | شرط شکست |
|---|---|---|---|---|
| ۱ | D1 لینک‌هاب | تک‌نقطهٔ اتصال کل قیف؛ ریسک ~صفر؛ geo-filter = اجرای فنی قاعدهٔ #۲ | «هاب یک واسطهٔ اضافه است؛ هر کلیک واسطه ~۲۰–۳۰٪ افت `[EST]`» | اگر CTR ‏hub→OF <۵۰٪ شد → لینک مستقیم X را تست کن (در X مجاز است) |
| ۲ | B1 پروفایل X | تنها شاه‌راه لینک مستقیم؛ یک‌بار بساز، همیشه کار می‌کند | «پروفایل بدون محتوا و فالوئر خالی است — impact واقعی به B3/B4 وابسته است» | ۴ هفته کیدنس و <۱۰۰ فالوئر → hookهای P4 بازطراحی |
| ۳ | D3 tracking-link | بدون attribution، تخصیص وقت بین Reddit/X کور است | «در حجم کم (<۲۰۰ کلیک) نویز > سیگنال؛ ریسک تصمیم زودهنگام» | تا آستانهٔ G1 (۲۰۰ کلیک) فقط جمع کن، قضاوت نکن |
| ۴ | E1 نردبان PPV | مستقیم‌ترین مسیر اولین دلار؛ free-page+PPV تنها مدل full-ladder `[FACT-secondary]` | «DM-labor گلوگاه واقعی است؛ با ساعات محدود صبا/آری ‏scale نمی‌شود» | اگر $/ساعت-DM < حداقل دستمزد ذهنی شد → منوی ثابت‌تر، DM کمتر |
| ۵ | A7 پروفایل Reddit-funnel | رایگان و دائمی؛ سطح ریسک نزدیک صفر؛ مکمل مستقیم A1–A3 | «پروفایل بدون جریان پست منظم مرده است — ارزش مشتق از A1 است، نه مستقل» | اگر ترافیک profile-view→hub <۲٪ ماند → بازطراحی bio/pinned |

## ۴. Sensitivity note (وزن ban-risk ‏0.30 → 0.15)

با فرمول جایگزین `Impact×0.25 + Speed×0.15 + Fit×0.20 + (10−Effort)×0.10 + (10−BanRisk)×0.15` (جمع وزن‌ها 0.85؛ مقایسه فقط نسبی):
- **صدر جدول تغییر نمی‌کند** — D1/B1/D3/E1 هم impact بالا دارند هم ریسک پایین؛ رتبه‌شان robust است.
- **برنده‌های اصلی کاهش وزن ریسک:** C1 ‏TikTok ‏(5.40→4.95 در برابر D1 ‏8.95→7.60 — فاصله از 3.55 به 2.65 می‌بندد)، C2 ‏IG، A4 ‏cross-post، F3 ‏shoutout — یعنی سبد «حجم بالا/ریسک بالا» یک پله بالا می‌آید.
- **تفسیر:** اگر روزی تیم تحمل ریسک بیشتری داشته باشد (مثلاً بعد از تثبیت درآمد و اکانت‌های بکاپ)، اولین ارتقای منطقی C1/C2 است، نه تاکتیک جدید. در فاز validation وزن 0.30 درست است `[OPINION]` — یک ban زودهنگام کل آزمایش را بی‌اعتبار می‌کند.

## ۵. Open Questions / دادهٔ گم‌شده
- سقف واقعی PPV/tip (‏#۱۸) → روی قیمت‌گذاری E1 اثر مستقیم؛ چک روز اول.
- وضعیت r/VerifiedFeet ‏(#۷) → اگر quarantined باشد، ترتیب A3 عوض می‌شود.
- ساعت واقعی صبا (#۴) → امتیاز Effort ردیف‌های B3/E2 به آن حساس است؛ با ۳–۵h/هفته، B3 باید به ۱–۲ پست/روز کاهش یابد `[EST]`.
- بلاک AU ‏(#۱۹) → روی Fit چند تاکتیک X/Reddit اثر جزئی دارد.
- دادهٔ گم‌شده: هیچ بنچمارک مستقلی برای CTR ‏hub→OF در نیش feet وجود ندارد `[OPEN]` — با دادهٔ خودمان (D3) پر می‌شود.

## ۶. Changelog — T6 re-verify (2026-07-10، همان روز)
- **B2:** ‏«unlabeled در X» → «برچسب‌گذاری محافظه‌کارانهٔ دو-وضعیتی»؛ BanRisk ‏۲→۴، Composite ‏8.25→7.65، خروج از Top-5 (جایگزین: A7). دلیل: policy رسمی معافیت SFW را دارد `[FACT — help.x.com fetch ‏07-10]` اما ریسک force-label/re-classification و ابهام مرز، وزن محافظه‌کارانه می‌گیرد (هم‌راستا با بلوپرینت دلتا #۱: «برچسب‌گذاری محافظه‌کارانه»). ⚠️ تعارض ثبت‌شده: ادعاهای «ACC program / three-tier ‏۲۰۲۶» در سرچ امروز هم فقط از content-farmها (auditsocials) آمد و صفحهٔ رسمی همچنان May 2024 است → `[UNVERIFIED — استفاده نشود]` (سومین رد).
- **D3 tracking-link:** re-verify شد؛ امتیاز بدون تغییر (‏8.45) با سه قید طراحی الزامی: (۱) هیچ PII/شناسه در URL؛ (۲) هیچ cloaking/redirect برای پنهان‌کردن مقصد OF در پلتفرم‌هایی که لینک OF را ممنوع می‌کنند (TikTok/IG — حتی masked link مصداق ban است `[EST — گزارش‌های حذف]`)؛ (۳) لینک OF فقط جایی که صریحاً مجاز است (X، Reddit، hub). طراحی کامل: [[drafts-awaiting-gate/tracking-link-design]].

---
*Gate rule اعمال شد؛ هیچ تاکتیک prohibited توصیه نشد — فقط bucket و جایگزین. این سند proposal است؛ ترتیب اجرا پشت GATE 0 و verdict انسانی.*
