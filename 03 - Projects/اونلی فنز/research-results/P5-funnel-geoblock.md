---
type: research-report
prompt: P5
project: Project-F
created: 2026-07-04
status: draft-for-human-review
tags: [project-f, research, research-grounded]
up: "[[PROJECT]]"
---

# P5 — فانل SFW→NSFW، ابزارهای link-in-bio و گیت‌های سن و جغرافیا (age-gate / geo-block)

**دامنه گزارش:** طراحی مسیر کلیک از اولین تماس تا اشتراک پولی برای Project-F (برند feet-only، بدون چهره، تیم دونفره در استرالیا، سقف بودجه AUD 200/ماه)، به‌علاوه زیرساخت gating. ایران در تمام لایه‌ها کاملاً مسدود می‌شود (اقدام حفاظتی/انطباقی). همه ادعاها با [FACT]/[EST]/[OPINION] برچسب خورده‌اند. نرخ تبدیل ارز: ‏1 USD ≈ 1.5 AUD [EST — نرخ روز را دستی چک کنید].

---

## ۱) معماری پیشنهادی فانل (Deliverable 1)

[OPINION] بهترین معماری برای برند بدون مخاطب و anonymity-first، فانل چهارلایه با «لایه ضربه‌گیر» (buffer) روی دامنه اختصاصی است:

```
[لایه 0 — کشف / SFW]
  TikTok · Instagram · X · Reddit (محتوای SFW یا platform-appropriate؛
  در X و Reddit محتوای بزرگسال مجاز است، در IG/TikTok مطلقاً SFW)
        │  (در IG/TikTok: لینک فقط در bio؛ هرگز لینک مستقیم OnlyFans)
        ▼
[لایه 1 — link-in-bio روی custom domain]
  GetAllMyLinks (پلن Creator) با Geo Filter فعال → BLOCK: Iran
  ظاهر صفحه: SFW و discreet + برچسب 18+
        │
        ▼
[لایه 2 — (اختیاری) landing page روی دامنه خودی پشت Cloudflare]
  Cloudflare WAF rule: ip.src.country eq "IR" → Block
  + RTA meta-tag + age-gate + صفحه فرود بدون محتوای explicit
        │
        ▼
[لایه 3 — صفحه رایگان/تریال پلتفرم]
  OnlyFans Free page یا free-trial link (قلاب lead)
  Geoblocking داخلی پلتفرم: Iran مسدود
        │  (تبدیل داخل پلتفرم: پیام خوش‌آمد + پیشنهاد)
        ▼
[لایه 4 — پول]
  صفحه پولی / PPV / تیپ  ← فانل free→paid داخل پلتفرم
```

[OPINION] لایه 2 برای شروع اجباری نیست؛ با بودجه فعلی می‌توان مستقیم از لایه 1 به لایه 3 رفت و لایه 2 را بعداً برای SEO و مالکیت ترافیک اضافه کرد. نکته کلیدی: هرچه صفحه‌های میانی SFW بمانند، هم ریسک link-block پلتفرم‌ها کمتر است و هم بار قانونی age-verification (بخش ۴) سبک‌تر می‌شود.

---

## ۲) استک ابزار + قیمت (Deliverable 2)

| ابزار | نقش | سیاست محتوای بزرگسال | قیمت (USD / ≈AUD) | ریسک/نکته |
|---|---|---|---|---|
| **AllMyLinks** | link-in-bio ساده | [FACT] صراحتاً adult-friendly؛ سابقه بن کردن کریتورهای بزرگسال ندارد (exclu.at، sirency.com، 2026) | رایگان [FACT] | [EST] ادعای blocklist شدن دامنه‌اش در Instagram از مقاله Help رقیب (GetAllMyLinks) است — تضاد منافع دارد؛ دستی تست کنید |
| **GetAllMyLinks** ⭐ پیشنهاد اصلی | link-in-bio + custom domain + **Geo Filter** | [FACT] adult-friendly؛ برای کریتورهای بزرگسال ساخته شده (try.getallmylinks.com/pricing، بازدید 2026-07-04) | Free $0؛ Creator **$9/مـاه ≈ AUD 13.5**؛ Agency $29 | Geo Filter فقط در پلن پولی؛ block/redirect بر اساس کشور/شهر [FACT] |
| **OOPSIE (oopsie.bio)** | link-in-bio مخفی‌کار با geo-block و decoy-routing | [FACT] مخصوص کریتورهای بزرگسال (oopsie.bio، 2026) | Free تا 5 لینک با همه امکانات؛ پلن‌های بالاتر توافقی | [FACT] پرداخت فقط کریپتو (NOWPayments) — [OPINION] ریسک اعتماد/حسابداری؛ برای Project-F گزینه دوم |
| **Linktree** | جریان اصلی (mainstream) | [FACT] لینک به محتوای بزرگسالِ قانونی مجاز است اگر sensitive علامت بخورد؛ فروش/پرداخت محتوای بزرگسال داخل Linktree ممنوع (linktr.ee/s/about/community-standards) | Free؛ پولی از ~$5/ماه [EST] | [FACT] سابقه حذف دسته‌جمعی سکس‌ورکرها (Vice، 2021)؛ [EST] ریسک flag شدن — توصیه نمی‌شود |
| **Beacons** | link-in-bio همه‌کاره | [FACT] فقط «لینک دادن به بیرون» با sensitive-content notice مجاز؛ خود صفحه باید all-ages باشد؛ فروش adult ممنوع (beacons.ai/i/community-standards) | Free؛ Pro $10/ماه ≈ AUD 15 | [OPINION] قابل‌قبول ولی مزیتی بر GAML ندارد |
| **Carrd** | landing page ارزان | [FACT] پورنوگرافی ممنوع؛ فقط استثنای «آثار هنری بزرگسال متعلق به خود سازنده» (carrd.co/docs/general/content-policy) | ~US$19/سال [EST] | [OPINION] برای برند بزرگسال ریسک ToS دارد — استفاده نشود |
| **Cloudflare Free** | geo-block لایه دامنه خودی | بی‌طرف نسبت به محتوا (میزبان نیست، proxy است) [FACT] | **$0** [FACT] | WAF Custom Rules روی پلن رایگان country-block می‌کند [FACT] (developers.cloudflare.com) |
| **OnlyFans Tracking Links** | attribution داخلی | داخل خود پلتفرم | $0 [FACT] | Settings → Tracking Links (supercreator.app، pippinclub.com، 2025–2026) |

[EST] جمع هزینه استک پیشنهادی: GAML Creator ‏$9/ماه + دامنه ~US$12/سال + Cloudflare $0 ≈ **AUD 15–16/ماه** — بسیار زیر سقف AUD 200.

**کدام لینک‌ها توسط پلتفرم‌های mainstream بلاک می‌شوند؟** [FACT] Instagram دامنه‌های شناخته‌شده adult و لینک مستقیم OnlyFans را flag می‌کند؛ [EST] راه‌حل استاندارد 2026: link-in-bio روی **custom domain بدون سابقه adult** (منابع: inro.social/blog/avoid-instagram-bans-onlyfans؛ help.getallmylinks.com «Why Your Bio Link Gets Flagged»، 2026). [OPINION] ریسک shadowban هرگز صفر نمی‌شود؛ اکانت‌های SFW باید مستقل از لینک هم ارزش داشته باشند.

---

## ۳) Best practiceهای صفحه فرود و نردبان free→paid

- [FACT] صفحات کوتاه با یک CTA واحد (تکرارشده در بالا/وسط/پایین) برای پیشنهادهای کم‌تعهد مثل تریال بهترین عملکرد را دارند (cxl.com؛ unbounce.com، 2026).
- [FACT] ‏social proof (تعداد فن، ستاره، نقل‌قول) تصمیم ~90٪ خریداران را تحت‌تأثیر قرار می‌دهد (mailerlite.com؛ userevidence.com). [OPINION] برای برند ناشناس، social proof عددی (تعداد لایک/فن) امن‌تر از testimonial با هویت است.
- **نردبان پیشنهادی [OPINION]:** صفحه فرود SFW → صفحه Free/Trial پلتفرم → پیشنهاد paid با تخفیف ماه اول → PPV. [FACT] تریال ۷روزه بیشترین ورودی را می‌آورد اما کمترین retention را دارد؛ تبدیل free→paid معمولاً 5–15٪ است (arunatalent.com/blog/onlyfans-free-vs-paid-page؛ 2026).
- [FACT] اولین خرید PPV اهرمی‌ترین لحظه چرخه عمر فن است؛ عملیات‌های حرفه‌ای 30–60٪ از سابسکرایبرهای جدید را در ۷ روز اول به اولین PPV می‌رسانند (tdmmanagement.com؛ everything-pr.com، 2025–2026).

---

## ۴) الزامات age-gate (بریتانیا/استرالیا/اتحادیه اروپا 2025–2026)

- **بریتانیا [FACT]:** از 25 جولای 2025، سایت‌های پورنوگرافیک در دسترس کاربران UK باید «highly effective age assurance» (تخمین سن چهره، اپراتور موبایل، کارت اعتباری، digital ID و…) داشته باشند؛ self-declaration کافی نیست؛ جریمه تا £18m یا 10٪ گردش مالی؛ تا فوریه 2026 بیش از ۹۰ پرونده و چند جریمه (ofcom.org.uk؛ natlawreview.com).
- **استرالیا [FACT]:** از 10 دسامبر 2025 ممنوعیت زیر ۱۶ سال در سوشال‌مدیا اجرا شد؛ کدهای Phase 2 (تا مارس 2026) برای سایت‌های adult در دسترس استرالیایی‌ها age assurance سخت‌گیرانه الزام می‌کند (esafety.gov.au؛ theconversation.com). [OPINION] چون تیم در استرالیاست، اگر لایه 2 (سایت خودی) محتوای explicit داشته باشد مستقیماً در دامنه این کدها می‌افتد — پس صفحه فرود را SFW نگه دارید و بار age-verification را به OnlyFans منتقل کنید که خودش مسئول انطباق است. ⚠️ نیاز به تأیید حقوقی دستی.
- **اتحادیه اروپا [FACT]:** بلوپرینت age-verification کمیسیون از 14 جولای 2025 منتشر و نسخه دوم از 15 آوریل 2026 «feature-ready» شد؛ هدف دسترسی همه شهروندان به age-verification حافظ حریم خصوصی تا 31 دسامبر 2026 (digital-strategy.ec.europa.eu).
- **پیاده‌سازی عملی برای لایه‌های خودی [OPINION]:** تا وقتی صفحات لایه 1–2 غیر-explicit هستند: (الف) age-gate کلیکی «18+» به‌عنوان حسن‌نیت، (ب) برچسب RTA در header:‏ `<meta name="RATING" content="RTA-5042-1996-1400-1577-RTA" />` — رایگان و داوطلبانه [FACT] (davidwalsh.name/rta-label؛ rtalabel.org)، (ج) اگر روزی محتوای explicit روی دامنه خودی رفت، 2257 statement و age-verification شخص ثالث الزامی می‌شود [FACT] (automatehorizon.com؛ firstamendment.com).

---

## ۵) چک‌لیست geo-block لایه‌به‌لایه — هدف: مسدودسازی کامل ایران (Deliverable 3)

**زمینه [FACT]:** خود OnlyFans در ایران توسط حاکمیت ایران از 2020 فیلتر است و پرداخت از ایران عملاً ممکن نیست (pleazeme.com؛ social-rise.com؛ ofac.treasury.gov) — اما Project-F مستقلاً در همه لایه‌ها block می‌کند.

| لایه | ابزار | مراحل | اتکاپذیری |
|---|---|---|---|
| 0 — سوشال | IG/TikTok/X | [FACT] کنترل کشوری creator-side قابل‌اتکایی برای اکانت‌های عادی ندارند → کنترل نرم: محتوا فقط انگلیسی، بدون هشتگ/نشانه هدف‌گیری ایران؛ نشانه‌های فرهنگی فقط برای دیاسپورای خارج از ایران | پایین [EST] |
| 1 — link-in-bio | GetAllMyLinks | ‏Dashboard → Geo Filter → Add rule → Country = Iran → **Block** (نه redirect) → Save (help.getallmylinks.com/articles/10191584) | متوسط–بالا (IP-based) |
| 2 — دامنه خودی | Cloudflare Free | ۱) دامنه را Proxied (ابر نارنجی) کنید ۲) Security → WAF → Custom rules → Create ۳) Expression: ‏`(ip.src.country eq "IR")` ۴) Action: **Block** → Deploy (developers.cloudflare.com/waf/custom-rules/use-cases/block-traffic-from-specific-countries) — اجرای رول در edge و روی پلن رایگان [FACT] | بالا (edge-level) |
| 3 — پلتفرم اصلی | OnlyFans | ‏Settings → Privacy and Safety → Geoblocking → جستجوی Iran → تیک → Save؛ اثر فوری؛ پروفایل از سرچ حذف و لینک مستقیم صفحه خطا می‌دهد [FACT] (arunatalent.com/blog/onlyfans-geoblocking-guide، 2026-02-19) | متوسط–بالا |
| 3ب — پلتفرم‌های جایگزین | Fansly | ‏Settings → Privacy → Location blocking؛ کشور/ایالت/شهر [FACT] (توییت رسمی Fansly، 2021-03-19؛ vocal.media) | متوسط–بالا |
| | Fanvue | ‏Settings → Privacy and safety → Block by country → Iran → Save؛ بازدیدکننده «This page does not exist» می‌بیند، حتی بدون اکانت؛ فعلاً فقط سطح کشور [FACT] (help.fanvue.com/articles/7860534، به‌روزرسانی ~2025) | متوسط–بالا |
| | LoyalFans | ‏Settings → Privacy & Safety → Blocked Regions → Iran؛ حتی granularتر از کشور [FACT] (loyalfans.zendesk.com) | متوسط–بالا |
| 4 — پرداخت | — | [FACT] کارت‌های بانکی ایران در شبکه بین‌المللی کار نمی‌کنند و OnlyFans در ایران در دسترس نیست → سد پرداخت، آخرین لایه طبیعی | بالا |

**محدودیت صادقانه [FACT]:** همه این بلاک‌ها IP-based هستند؛ کاربر VPN‌دار از هر کشوری می‌تواند از سد IP عبور کند (این گزارش هیچ روش دور زدنی را بررسی یا توصیه نمی‌کند — صرفاً ریسک باقیمانده ثبت می‌شود). [OPINION] چیدن block در ۵ لایه + سد پرداخت، exposure عملی به ایران را به حداقلِ قابل‌دفاع می‌رساند و حسن‌نیت انطباقی Project-F را مستند می‌کند. برخی ابزارها (SLT.bio) ادعای بستن VPN/datacenter-range هم دارند [EST — تأییدنشده].

---

## ۶) ردیابی (Tracking / UTM) سازگار با محتوای بزرگسال

- [FACT] ‏**OnlyFans Tracking Links** (Settings → Tracking Links): برای هر کانال یک لینک؛ کلیک، فن جدید و نرخ تبدیل هر کمپین را نشان می‌دهد — ستون فقرات attribution، رایگان (supercreator.app/guides/onlyfans-tracking-links).
- [FACT] ‏**Bitly** مقصدهای دسته‌بندی‌شده adult را block می‌کند → برای این فانل استفاده نشود (quora.com گزارش‌ها + policy Bitly).
- [OPINION] الگوی امن: ‏UTM فقط روی دامنه خودی (لایه 1–2) + آنالیتیکس داخلی GAML/OOPSIE + لینک نهایی به OnlyFans همیشه از نوع Tracking Link. برای وب‌آنالیتیکس دامنه خودی، ابزار self-hosted (مثل Umami) هیچ ToS محتوایی ندارد چون روی سرور خودتان است [FACT-by-design]؛ سرویس‌های ابری مثل Plausible باید جداگانه policy-check شوند [EST].
- [EST] تفاوت LTV بین کانال‌ها می‌تواند شدید باشد (مثال گزارش‌شده: فن Reddit با LTV ~$8 در برابر فن shoutout با ~$45 — ofmanager.com) → تصمیم‌گیری فقط بر اساس کلیک ممنوع.

---

## ۷) بنچمارک‌های تبدیل هر پله فانل — همه [EST] (Deliverable 4)

| پله فانل | بنچمارک [EST] | منبع (تاریخ) |
|---|---|---|
| بازدید پروفایل IG → کلیک bio-link | 0.1–0.5٪ | inro.social benchmarks (2026-05-05) |
| ‏DM گرم (open rate) | 80–90٪ | inro.social (2026-05-05) |
| ‏CTR لینک داخل DM | ~28٪ | inro.social (2026-05-05) |
| کلیک سرد → سابسکرایبر پولی | <0.5٪ | inro.social (2026-05-05) |
| کلیک گرم (DM) → سابسکرایبر پولی | 5–8٪ | inro.social (2026-05-05) |
| کلیک Reddit → سابسکرایب | میانگین 2–5٪؛ برترین‌ها 8–12٪ | sirency.com؛ desirely.co (2026) |
| فالوئر IG → ساب پولی جدید در ماه | 0.01–0.05٪ (passive) / 0.05–0.08٪ (DM funnel) | inro.social (2026-05-05) |
| ‏free page/trial → paid | 5–15٪ | arunatalent.com (2026) |
| ساب جدید → اولین PPV در ۷ روز | 30–60٪ (عملیات حرفه‌ای) | tdmmanagement.com (2025) |

[OPINION] برای Project-F با مخاطب صفر و نیش feet: شش ماه اول این اعداد را به‌عنوان سقف ببینید نه میانگین؛ اعداد فوق عمدتاً از کریتورهای عمومی با مخاطب بزرگ آمده‌اند و attribution فروشندگان ابزار (Inrō) upward bias دارد.

---

## Blind spots / نقاط کور

1. **تست عملی نشده:** هیچ ابزاری hands-on تست نشده (قاعده desk-research). ادعای Geo Filter در GAML و geo-block در OOPSIE باید قبل از launch با VPN تستِ«block شدن IR» شود — [INCOMPLETE تا تست دستی].
2. **تضاد منافع منابع:** بخش بزرگی از بنچمارک‌ها و مقایسه‌های link-in-bio از وبلاگ فروشندگان/آژانس‌ها (Inrō، Exclu، GAML، آژانس‌های OFM) است؛ اعداد را محافظه‌کارانه تعدیل کنید.
3. **وضعیت حقوقی سایت خودی در استرالیا:** مرز دقیق «سایت adult» در کدهای Phase 2 استرالیا برای یک landing page غیر-explicit اما مرتبط با برند بزرگسال، نیازمند مشاوره حقوقی است — پیش از ساخت لایه 2 بررسی شود.
4. **بلاک‌لیست دامنه‌ها در IG/TikTok پویاست:** دامنه‌ای که امروز پاک است ممکن است فردا flag شود؛ مانیتورینگ ماهانه لینک bio لازم است.
5. **VPN و residual risk ایران:** بلاک IP هرگز مطلق نیست؛ سیاست داخلی باید این ریسک باقیمانده را بپذیرد و مستند کند (بدون هیچ اقدام دیگری).
6. **قیمت‌ها فرّار:** قیمت GAML/Beacons/Inrō و نرخ USD→AUD از صفحات 2026 برداشت شده؛ پیش از خرید دوباره چک شود.
7. **پوشش‌نیافته:** سیاست adult سرویس‌های آنالیتیکس ابری (Plausible/Fathom) و جزئیات پلن‌های سفارشی OOPSIE راستی‌آزمایی نشد.

**منابع کلیدی (بازدید 2026-07-04):** exclu.at/blog/best-link-in-bio-for-onlyfans · try.getallmylinks.com/pricing · help.getallmylinks.com/articles/10191584 · oopsie.bio · linktr.ee/s/about/community-standards · beacons.ai/i/community-standards · carrd.co/docs/general/content-policy · arunatalent.com/blog/onlyfans-geoblocking-guide (2026-02-19) · help.fanvue.com/articles/7860534 · x.com/fansly/status/1373010914807574535 · loyalfans.zendesk.com · developers.cloudflare.com/waf/custom-rules · ofcom.org.uk (age checks) · esafety.gov.au (social media age restrictions) · digital-strategy.ec.europa.eu (EU age-verification blueprint) · davidwalsh.name/rta-label · inro.social/blog/instagram-to-onlyfans-conversion-benchmarks (2026-05-05) · sirency.com · tdmmanagement.com · pleazeme.com/onlyfans-banned-countries
