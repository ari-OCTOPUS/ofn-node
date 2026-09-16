---
type: research-integration
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: complete
round: 2
created: 2026-07-10
created_by: agent (Claude Fable 5 — propose-only)
relates_to: "[[RESEARCH-INTEGRATION-round1]] · [[ACQUISITION-ENGINE-2026-07-05]] · [[STATE-REPORT-2026-07-05]] · [[PROJECT-F-BRAIN-SPEC]] · CLAUDE.md"
tags: [project-f, research, round2, delta-map, methods-catalog, multi-agent, unit-economics]
aliases: ["Round 2", "تحقیق جامع", "WS-1..7"]
---

# RESEARCH-INTEGRATION — Round 2 (2026-07-10)

> اجرای پرامپت تحقیقاتی جامع ۷-محوره (WS-1 تا WS-7) با ۴ خط تحقیق موازی وب (پلتفرم / جذب / بازار / AI-stack). همهٔ URLها در تاریخ **2026-07-10** بازدید شده‌اند. تگ‌ها: `[FACT]` منبع‌دار · `[EST]` تخمین · `[OPINION]` قضاوت · `[SPEC]` فرضیه · `[OPEN]` سؤال باز · `[COI]` منبع vendor/affiliate (وزن پایین).
> **قواعد قفل‌شده حاکم‌اند؛ هیچ توصیهٔ این سند آن‌ها را override نمی‌کند. GATE 0 همچنان بلاکر هر اجراست.**

---

## §۰ — Research Plan (اجراشده)

چهار خط موازی: (الف) WS-1 پلتفرم‌ها — fee/payout/policy از منابع اولیه؛ (ب) WS-3 کانال‌های جذب — policy رسمی Reddit/X/TikTok/IG/ads/link-hub/email؛ (ج) WS-7+WS-2 — بنچمارک درآمد/churn با فیلتر ضد-bias؛ (د) WS-4 — قیمت API روزِ مدل‌ها + ToS ابزارهای اتوماسیون. سپس سنتز، delta-map مقابل corpus (round1، ACQUISITION-ENGINE، 12-prelaunch)، و verification pass. فرض‌های اعلام‌شده: Branch A/B هنوز باز → همه‌چیز در حالت planning؛ سقف ابزار AUD 100/ماه در مدل هزینه لحاظ شد؛ نرخ تبدیل فرضی AUD/USD ≈ ۰٫۶۵ `[EST]`.

---

## §۱ — Executive Summary (decision-ready)

۱. **مسیر فعلی corpus برای بار دوم به‌طور مستقل تأیید شد**: dual-platform (OF+Fansly)، Reddit=موتور رشد + X=هاب برند، قیف SFW→link-hub→OF، الگوی «AI درفت / انسان می‌فرستد»، و انتظارات درآمدی پایین. هیچ یافته‌ای تغییر استراتژیک بزرگ ایجاب نمی‌کند `[OPINION]`.
۲. اعداد پایهٔ پلتفرم سرجایشان‌اند: OF کمیسیون **۲۰٪** `[FACT — ToS رسمی]`، سقف sub ‏$4.99–49.99، payout min ~$20؛ Fansly ‏80/20 با min ‏$20 Paxum/$100 wire؛ Fanvue بند **مصادرهٔ موجودی ۱۲ماهه** از صفحهٔ legal رسمی تأیید شد.
۳. **ریسک پلتفرم بالاتر رفته است**: مالک OF (Radvinsky) در مارس ۲۰۲۶ فوت کرد؛ مذاکرهٔ فروش سهم اقلیتی با ارزش‌گذاری >۳ میلیارد دلار (سقوط از ۷–۸ میلیارد ۲۰۲۵) در جریان است `[FACT — Forbes]` → دورهٔ گذار مالکیتی = ریسک تغییر policy؛ قاعدهٔ «برداشت مکرر درآمد + ایمیل‌لیست» از توصیه به **الزام** ارتقا یابد `[OPINION]`.
۴. **موج جهانی age-verification فرصت/تهدید توأمان است**: ممنوعیت زیر-۱۶ استرالیا از دسامبر ۲۰۲۵ روی Reddit/X/IG/TikTok اجراست؛ UK OSA و verification اروپاییِ Reddit ریچ ارگانیک NSFW-tagged را ساختاری کم می‌کند `[FACT]` → مزیت نسبی برند ما: محتوای فقط-پای غیر-explicit روی X می‌تواند **unlabeled** بماند (معافیت صریح policy) و از افت ریچ فرار کند `[FACT — help.x.com]`.
۵. واقع‌بینی درآمد: میانگین payout هر اکانت creator در OF ‏≈$104/ماه `[FACT — محاسبه از صورت مالی FY2024]`، اما median بسیار پایین‌تر و **مُد = صفر** است (XSRUS). باند واقع‌بینانهٔ ماه‌های ۱–۳ برای صفحهٔ feet جدید: **$0–300/ماه با احتمال بالای نتیجهٔ نزدیک صفر** `[EST]` — سناریوهای موجود corpus (Floor/Base/Upside) معتبر، فقط وزن Floor را بالاتر ببینید.
۶. اقتصاد واحد: churn ماهانه ۳۰–۶۰٪ → عمر subscriber ‏۱٫۷–۳ ماه `[COI/EST]`؛ LTV مؤثر هر paid sub ≈ ‏$۱۵–۴۵ خالص `[EST]` → CAC باید نزدیک صفرِ پولی بماند (ارگانیک + زمان)؛ paid ads اصلاً گزینه نیست (همهٔ شبکه‌های اصلی adult-ads را ممنوع کرده‌اند `[FACT]`).
۷. مدل درآمد بهینه برای این نیش: **صفحهٔ free + قفل PPV روی تایم‌لاین + DM ladder** — چون صفحهٔ paid اجازهٔ price-lock پست تایم‌لاین ندارد `[FACT-secondary]`؛ این یافته نسخهٔ نردبان EXT-04/ACQUISITION را تقویت می‌کند (ورودی تازه برای سؤال باز #۱۰).
۸. اتوماسیون: ممنوعیت «AI chatbot برای چت/DM» در OF پابرجاست `[FACT — Reuters + گاید ۲۰۲۶]`؛ Fansly هم chatbot را ممنوع کرده (404 Media). الگوی محافظه‌کار ما (درفت در کنسول جدا + paste دستی) دوباره ابقا می‌شود. ⚠️ نکتهٔ جدید: ادعای «100% compliant» ‏Social Rise خوداظهاری است و هم‌زمان proxy چرخشی تبلیغ می‌کند → ریسک متوسط، فقط برای scheduling ساده استفاده شود، نه engagement `[OPINION]`.
۹. هزینهٔ مغز multi-agent عملاً بی‌اهمیت است: workload کامل پیشنهادی با routing ‏Haiku/Sonnet ‏≈ **AUD 8–12/ماه** (~۱۰٪ سقف) `[EST — محاسبه]`؛ ریسک هزینه از loopهای کنترل‌نشده است، نه قیمت واحد → cap و kill-switch مغز کافی است.
۱۰. دو ادعای پرتکرار فضای وب **رد شد**: «برنامه ACC ایکس» (تأیید سوم) و «بازار ۲.۱ میلیارد دلاری feet-pics به‌نقل از Statista» — منبع اولیه ندارد، احتمالاً جعلی `[UNVERIFIED — استفاده نشود]`.
۱۱. کانال جدید کاندید: **Bluesky** (adult-tolerant با labeling بومی) به‌عنوان کانال ارگانیک درجه‌۳ کم‌ریسک → سؤال باز جدید #۱۷.
۱۲. هیچ‌کدام از یافته‌ها GATE 0 را دور نمی‌زند؛ ترتیب اجرا همان بلوپرینت است: G0 → توافق‌نامه → reconcile تناقض‌ها → Day-Zero → warm-up → launch.

---

## §۲ — WS-1: چشم‌انداز پلتفرم و مدل کسب‌وکار

### ۲.۱ مکانیک OnlyFans (وضعیت 2026-07-10)
| آیتم | مقدار | تگ/منبع |
|---|---|---|
| کمیسیون | ۲۰٪ از هر پرداخت فن | `[FACT]` ToS رسمی onlyfans.com/terms |
| Payout min | ~US$20 (وجود حداقل در ToS، عدد از منابع ثانویه) | `[FACT-secondary]` — چک داشبورد در launch (سؤال بسته‌شدهٔ قبلی: $10=[SPEC]) |
| روش/چرخهٔ payout استرالیا | SWIFT ‏۲–۵ روز کاری؛ Paxum؛ دستی یا خودکار | `[EST]` صفحهٔ AU-specific رسمی پیدا نشد |
| ارز | همهٔ قیمت‌ها USD؛ conversion fee با پرداخت‌یار؛ مالیات تماماً گردن creator | `[FACT]` ToS |
| Subscription | $4.99–$49.99 یا free ($0) | `[FACT-secondary consensus]` |
| Tip | سقف $100 برای ~۴ ماه اول عضویت فن، بعد $200 | `[FACT-secondary/COI]` |
| PPV | سقف گزارش‌شده $50–$200 — منابع متناقض | `[UNVERIFIED]` → چک داشبورد (سؤال باز جدید #۱۸) |
| Bundles/Promo/Trial | باندل ۳/۶/۱۲ماهه، کمپین تخفیف، free-trial link، tracking link | `[FACT-secondary]` |
| Free vs Paid page | صفحهٔ paid **نمی‌تواند** پست تایم‌لاین را price-lock کند؛ صفحهٔ free می‌تواند. PPV در DM برای هر دو | `[FACT-secondary]` — پیامد مستقیم برای نردبان قیمت (§۳ و #۱۰) |
| Verification | 18+، ID دولتی + سلفی؛ **Release Form داخل داشبورد برای هر شرکت‌کنندهٔ اضافه** | `[FACT]` ToS + secondary |
| Geo-block | Settings → Privacy & Safety → Block by Country (کشور/ایالت/IP)؛ VPN دورزدنی است | `[FACT-secondary]` — مکانیزم اجرایی قاعدهٔ قفل‌شدهٔ #۲ (geo-block ایران) + دفاع privacy (بلاک AU برای آشنایان، تصمیم دونفره) |
| AI-content | محتوای AI باید برچسب #ai/#AIGenerated بگیرد | `[FACT]` ToS |
| AI-chat در DM | «You cannot use an AI chatbot to write chats or direct messages» | `[FACT — Reuters 2024-07؛ گاید 2026-04 می‌گوید پابرجاست]` — متن زندهٔ فعلی JS-gated، verify مرورگری pending |
| Suspension | تعلیق/حذف با اطلاع ۳۰روزه «به هر دلیل» یا فوری؛ توقیف earnings ممکن؛ dispute تا ۶ ماه | `[FACT]` ToS — استدلال دیگر برای برداشت مکرر |

### ۲.۲ Fansly و آلترناتیوها
- **Fansly:** ‏80/20 روی همه‌چیز `[FACT-secondary]`؛ payout min ‏$20 Paxum/crypto و $100 bank wire `[FACT-secondary — تأیید دوبارهٔ 12-prelaunch]`؛ **مزیت ساختاری: FYP/discovery الگوریتمی + suggestion** (OF معادل عمومی ندارد) `[FACT-secondary + Hollywood Reporter]` → برای برند faceless بدون شهرت شخصی ارزش واقعی دارد؛ subscription چند-tier با پرمیشن جدا؛ SFW مجاز؛ ممنوعیت chatbot از آپدیت ۲۰۲۴ `[FACT — 404 Media]`.
- **Fanvue:** ‏80/20؛ نرخ تبلیغی 85/15 دورهٔ intro (مدت متناقض ۳ vs ۱۲ ماه `[UNVERIFIED]`)؛ pending ‏۷–۲۸ روز؛ **بند مصادرهٔ موجودی خفتهٔ ۱۲ماهه (شامل استرالیا) از صفحهٔ legal رسمی** `[FACT]` — تأیید مجدد یافتهٔ 07-05؛ اگر به‌عنوان mirror دوم استفاده شود، قاعدهٔ برداشت دوره‌ای الزامی.
- **FeetFinder:** ‏fee ‏۱۵٪ Basic / ۱۰٪ Premium **+ اشتراک اجباری فروشنده** ($4.99–14.99/ماه)؛ payout min ~$30؛ Trustpilot ‏~۲٫۸/۵ با الگوی ۸۳٪ پنج‌ستارهٔ سازگار با review انگیزشی؛ شکایات BBB حول payout و تعلیق `[FACT]`؛ تقریباً کل محتوای «FeetFinder review» وب affiliate است `[COI]` → **تأیید سوم P1: مارکت‌پلیس‌ها موتور رشد نیستند**؛ حداکثر کانال فرعی، آن هم بعد از G2 `[OPINION]`.

### ۲.۳ Platform risk
- سابقه: اعلام ممنوعیت explicit در اوت ۲۰۲۱ زیر فشار بانک‌ها و بازگشت ۶روزه `[FACT — Time/BuzzFeed]` → کل مدل downstream شبکه‌های کارت است.
- **جدید ۲۰۲۶:** فوت Radvinsky (مارس ۲۰۲۶) + مذاکرهٔ فروش سهم ~۲۰٪ با ارزش‌گذاری >$3B در آوریل ۲۰۲۶ (در برابر گفت‌وگوهای $7–8B سال ۲۰۲۵) `[FACT — Forbes]` → گذار مالکیتی و افت ارزش‌گذاری = احتمال تغییر policy/فروش بالاتر از حد تاریخ اخیر `[EST]`.
- رگولاتوری: جریمهٔ £1.05M آفکام به Fenix بابت age-assurance ‏(مارس ۲۰۲۵) `[FACT — ofcom.org.uk]`؛ فشار OSA/Visa-Mastercard ادامه دارد.
- تاب‌آوری (لایهٔ validation): برداشت مکرر (بالانس روی پلتفرم نماند)، dual-platform از روز اول (مصوب قبلی)، ایمیل‌لیست از هفتهٔ اول، بکاپ محلی محتوا + consent/ID، مستندسازی compliance برای appeal `[OPINION]`.

**۳ نکتهٔ قابل‌اقدام WS-1:**
1. قاعدهٔ عملیاتی جدید پیشنهادی برای DecisionLog (بعد از verdict): «payout در آستانهٔ min برداشت شود؛ هرگز بالانس >$100 روی هیچ پلتفرمی نماند» — با توجه به گذار مالکیتی OF و بند Fanvue.
2. در Day-Zero چک‌لیست، سه چک داشبوردی ثبت شود: payout min واقعی، سقف PPV واقعی، متن زندهٔ بند AI-chat در Community Guidelines.
3. Release Form داخل OF برای صبا از روز اول تنظیم شود (حتی فقط-پا، شرکت‌کنندهٔ دوم = الزام ToS).

---

## §۳ — WS-2: معماری درآمد و درآمد نیمه‌خودکار (فقط مشروع)

### ۳.۱ لِوِرهای درآمد و ترتیب چیدن funnel
ترتیب بهینه بر اساس شواهد این راند (سازگار با ACQUISITION-ENGINE، با یک تصحیح):

```
کشف (Reddit/X/Fansly-FYP)
   → صفحهٔ OF از نوع FREE (سد ورود صفر)
      → قفل PPV روی پست‌های منتخب تایم‌لاین ($5–15 اولین خرید)
         → DM خوش‌آمد (انسان می‌فرستد) → PPV ladder در DM ($8–25)
            → Custom pipeline ($15–50 شروع؛ ۲–۴× پایه)
               → Tip menu + baseline
                  → (بعد از تثبیت) tier/VIP یا صفحهٔ paid دوم
```
- دلیل تصحیح: صفحهٔ paid نمی‌تواند پست تایم‌لاین را price-lock کند `[FACT-secondary]` → مدل «free + PPV» عملاً تنها راه اجرای نردبان کامل روی یک صفحه است؛ نسخهٔ EXT-04 (بدون VIP در ۹۰ روز اول) تقویت شد → ورودی تصمیم #۱۰.
- Retention/win-back مجاز: کمپین تخفیف بومی، باندل rebill، پیام win-back دستی، محتوای «renew-on» (پاداش تمدید) — همه featureهای بومی پلتفرم `[FACT-secondary]`.

### ۳.۲ «نیمه‌خودکار/passive» — مرز مجاز
| مجاز (back-office) | ممنوع/گِیت‌شده |
|---|---|
| Batching شوت (۱ شوت → ۳۰+ asset طبق 30-Clips) | هر پست/DM خودکار به‌نام creator |
| Scheduling با ابزار API-رسمی (Social Rise/Postpone برای Reddit؛ قابلیت queue بومی OF) | ابزار third-party متصل به اکانت OF (بدون verdict) |
| Evergreen funnel: welcome-flow دستی با template، tracking-linkهای دائمی | AI-chat خودکار (نقض ToS صریح OF/Fansly) |
| Pricing rule-based (منوی ثابت + قواعد تخفیف از پیش‌تأییدشده) | dynamic pricing خودکارِ بدون تأیید |
| Repurposing pipeline (P9) + WM/NOWM | mass-DM/spam به هر شکل |
| تنوع درآمد: استاک (Adobe royalty ‏۳۳٪، ‏Foap ‏$5/فروش `[FACT]`)، parts-modeling AU (~AU$180+/روز `[EST]`) | فروش خارج از پلتفرم (قاعدهٔ #۳) |

واقعیت را صریح بگوییم: شواهد مستقل (case مستند Salon: درآمد $0 بعد از هفته‌ها تلاش فعال؛ کیس £30k/ماه = کار تمام‌وقت بدون تعطیلی) نشان می‌دهد این کسب‌وکار **درآمد نیمه‌خودکار دارد، نه passive** — اتوماسیون فقط ساعت کار هر دلار را کم می‌کند، تولید و رابطه انسانی می‌ماند `[OPINION — مبتنی بر FACTهای §۵]`.

### ۳.۳ Unit economics (مدل ساده، سه سناریو)
فرض‌های پایه (همه `[EST]` مگر ذکر شود): sub قیمت free؛ PPV اول $8؛ unlock-rate ‏۱۵–۲۵٪ `[COI]`؛ conversion فالوئر free→خریدار ۵–۱۵٪ `[COI]`؛ churn ماهانه ۳۰–۶۰٪ → عمر مشتری ۱٫۷–۳ ماه؛ سهم پلتفرم ۲۰٪.

| متغیر | Conservative | Base | Optimistic |
|---|---|---|---|
| فالوئر free تجمعی تا پایان ماه ۳ | ۳۰ (حد G2) | ۱۰۰ | ۳۰۰ |
| نرخ خریدار از free | ۵٪ | ۱۰٪ | ۱۵٪ |
| خریدار فعال | ~۲ | ~۱۰ | ~۴۵ |
| ARPPU ماهانه (PPV+tip+custom) | $15 | $25 | $35 |
| **درآمد ناخالص ماه ۳** | **~$30** | **~$250** | **~$1,500** |
| خالص بعد از ۲۰٪ + هزینهٔ stack (A$45–105) | ~$0± | ~$130–170 | ~$1,100+ |
| LTV هر خریدار (عمر ×ARPPU×0.8) | $20–36 | $34–60 | $47–84 |

- سازگاری با corpus: باندهای Floor $0–80 / Base $150–500 / Upside $500–1500 **تأیید می‌شود**؛ فقط توزیع احتمال Floor را ≥۵۰٪ بگیرید (مُد صنعت = صفر است `[FACT — XSRUS]`) `[OPINION]`.
- CAC: پولی ≈ صفر (paid ads ممنوع/بی‌فایده)؛ CAC واقعی = زمان. با ۱۰ ساعت/هفتهٔ promo و سناریوی Base، هر خریدار ≈ ۱۲–۱۳ ساعت-کار جذب می‌خورد در ماه‌های اول `[EST]` → متریک $/ساعت-promo از هفتهٔ اول رصد شود (KPI کاندید round1).
- از دقت کاذب پرهیز: این جدول برای **تصمیم kill/continue در G1/G2** است، نه پیش‌بینی.

**۳ نکتهٔ قابل‌اقدام WS-2:**
1. تصمیم #۱۰ (نردبان قیمت) را با دادهٔ این راند ببندید: free page + PPV اول $8 (باند $5–15) + custom از $25؛ بدون VIP تا روز ۹۰ — نزدیک‌ترین نسخه: EXT-04.
2. سه متریک اقتصاد واحد از روز اول در Fable5: unlock-rate ‏PPV، ‏ARPPU، $/ساعت-promo (تعریف‌ها در §۶).
3. لایهٔ استاک/B2B (سؤال #۱۶) فعلاً «پارک»: تا حل tension ناشناسی، فقط RAWها آرشیو شوند؛ هزینهٔ فرصت ناچیز است (`[EST]` $0–100/ماه).

---

## §۴ — WS-3: کاتالوگ روش‌های جذب و درآمد (فقط compliant)

> ستون‌ها: وضعیت = C (compliant) / G (gray-area، شرط‌دار) / P (prohibited — فقط برای آگاهی، اجرا ممنوع). تلاش/هزینه: L/M/H. اطمینان: ★ (کم) تا ★★★ (بالا). اثر و time-to-result برای فاز validation تیم دونفره تخمین است `[EST]` مگر خلاف ذکر شود. **ردیف‌های P هرگز اجرا نمی‌شوند؛ جایگزین امن در ستون آخر.**

### الف) Reddit — موتور رشد #۱
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | Time-to-result | تناسب feet | ریسک اصلی | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | پست OC در subهای feet با verification | عکس WM-دار + عنوان hook؛ ورود از subهای کم‌سخت‌گیر | C | M | 0 | H | ۱–۳ هفته | عالی | حذف توسط mod؛ چک قوانین هر sub | ★★★ |
| A2 | Verification post استاندارد | کاغذ دست‌نویس (username+تاریخ+sub) — بدون چهره، فقط پا+کاغذ | C | L | 0 | پیش‌نیاز A1 | ۲۴–۷۲س approve | عالی | افشای دست‌خط → دست‌کش/چاپ | ★★★ |
| A3 | نردبان sub (کوچک→بزرگ) | شروع از subهای نیش کم‌رقابت، بعد subهای بزرگ با karma بالاتر | C | M | 0 | M-H | ماه ۱–۲ | عالی | شتاب زیاد = spam-filter | ★★★ |
| A4 | Cross-post حساب‌شده | همان asset در ۳–۵ sub مرتبط با فاصلهٔ زمانی | C | L | 0 | M | فوری | خوب | duplicate-detection؛ فاصله ≥چند ساعت | ★★ |
| A5 | Scheduling با Social Rise/Postpone | صف پست از طریق API؛ ارسال notification-based | C* | L | $9–30/ماه | M (بهره‌وری) | فوری | خوب | *compliance خوداظهاری+proxy ads → فقط schedule، نه engagement | ★★ |
| A6 | Comment engagement هدفمند | پاسخ به کامنت‌های پست خود؛ حضور در threadهای نیش | C | M | 0 | M | هفته‌ها | خوب | نه لینک در کامنت غریبه = spam | ★★★ |
| A7 | پروفایل Reddit به‌مثابه funnel | bio + pinned + لینک hub (نه OF مستقیم) | C | L | 0 | M | فوری | عالی | — | ★★★ |
| A8 | Sub اختصاصی برند (بعداً) | r/AnarSoles-type؛ آرشیو + جامعه | C | M | 0 | L→M | ماه ۳+ | خوب | نگه‌داری؛ فقط بعد از G2 | ★★ |
| A9 | Reddit Ads | — | **P** | — | — | — | — | — | ممنوع policy رسمی (adult) `[FACT]` → جایگزین: A1–A7 ارگانیک | ★★★ |
| A10 | AMA/تعاملی SFW در subهای عمومی‌تر | محتوای foot-care/lifestyle بدون فروش مستقیم | G | M | 0 | L | ماه‌ها | متوسط | خروج از نیش؛ برچسب self-promo | ★ |

### ب) X — هاب برند
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | پروفایل کامل + pinned funnel | bio بدون geo-fact شهری («Aussie» فقط) + لینک مستقیم مجاز به OF | C | L | 0 | H (تبدیل) | فوری | عالی | تفکیک x-bio/x-pin (مصوب) | ★★★ |
| B2 | ماندن unlabeled با محتوای غیر-explicit | معافیت صریح policy برای «partial/obscured» → ریچ کامل | C | L | 0 | H | فوری | **مزیت ویژهٔ نیش** | اگر محتوا مرزی شود force-label | ★★★ |
| B3 | کیدنس ۲–۴ پست/روز از بانک ۳۰-کلیپ | teaser عکس/کلیپ WM + کپشن hook (P4) | C | M | 0 | M-H | ۴–۸ هفته | عالی | سایه‌بان کیفیت < کمیت | ★★ |
| B4 | Reply-engagement نیش | تعامل واقعی با اکانت‌های هم‌نیش/فن‌ها | C | M | 0 | M | هفته‌ها | خوب | وقت‌خوار؛ اتومات ممنوع | ★★★ |
| B5 | S4S بعد از آستانهٔ ۱k فالوئر @ ≥۲٪ eng (مصوب) | تبادل shoutout با هم‌ترازها | C | L | 0 | M | ماه ۲+ | خوب | افت کیفیت فید؛ اسکم promo-seller | ★★ |
| B6 | X Communities نیش | پست در کامیونیتی‌های مرتبط | C | L | 0 | L-M | هفته‌ها | خوب | قوانین داخلی هر community | ★★ |
| B7 | X Ads | — | **P** | — | — | — | — | — | «adult products/services» ممنوع `[FACT]`؛ ACC هم جعلی → جایگزین B1–B5 | ★★★ |
| B8 | Thread روایی/آموزشی SFW | «پشت‌صحنهٔ برند faceless» بدون شناسه | G | M | 0 | L | ماه‌ها | متوسط | opsec — بازبینی انسانی هر thread | ★ |

### ج) قیف SFW — TikTok/IG/Shorts/Pinterest
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | TikTok کاملاً SFW (nail-art/ASMR/foot-care) | هرگز ذکر OF؛ CTA فقط «link in bio» → hub با گیت 18+ | G | H | 0 | H (حجم) | ۴–۱۲ هفته | خوب | **پرریسک‌ترین**: پاکسازی‌های مستند creatorها `[FACT — Rolling Stone]`؛ اکانت قربانی فرض شود | ★★ |
| C2 | IG Reels repurpose از TikTok | همان asset، متادیتا پاک (P9) | G | L | 0 | M | ۴–۱۲ هفته | خوب | shadowban؛ لینک OF مستقیم هرگز | ★★ |
| C3 | YouTube Shorts | repurpose سوم؛ کانال lifestyle | G | L | 0 | L-M | ماه‌ها | متوسط | strike اگر مرزی؛ عایدی جانبی ads بعید | ★★ |
| C4 | Pinterest بردهای aesthetic (کفش/جوراب/nail) | ترافیک SEO-مانند دیرپا به hub | G | M | 0 | L-M | ماه ۲+ | متوسط | policy ضد-adult پینترست؛ فقط تصویر کاملاً SFW | ★ |
| C5 | اشارهٔ مستقیم به OF در TikTok/IG | — | **P** | — | — | — | — | — | sexual-solicitation policy `[FACT]` → جایگزین: C1 bridge | ★★★ |

### د) زیرساخت funnel و owned audience
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | Link-hub با گیت 18+ و geo-filter | GAML ($9/ماه، geo-filter برای ایران+AU-optional) یا Beacons؛ AllMyLinks بکاپ | C | L | $0–9 | پیش‌نیاز همه | فوری | عالی | Linktree = ریسک تاریخی حذف SWها `[FACT — Vice]` | ★★★ |
| D2 | ایمیل‌لیست از هفتهٔ ۱ (SendX) | فرم در hub؛ هفته‌ای ۱ ایمیل evergreen | C | M | ~$10/ماه | H (تاب‌آوری) | ماه ۲+ | عالی | AU Spam Act: consent+sender-ID+unsubscribe ≤۵روز `[FACT — ACMA]`؛ تأیید کتبی SendX pending | ★★★ |
| D3 | Tracking link برای هر کانال | attribution بومی OF | C | L | 0 | M (داده) | فوری | عالی | — | ★★★ |
| D4 | کانال برودکست تلگرام SFW (بدون فروش/پرداخت) | teaser + لینک hub؛ صرفاً توزیع | G | L | 0 | L-M | ماه‌ها | متوسط | هر مذاکرهٔ پرداخت = نقض قاعدهٔ #۳؛ متن‌ها از قبل قالب‌بندی | ★★ |
| D5 | وب‌سایت/بلاگ کوچک SEO (foot-model aesthetic) | دامنهٔ برند + ۱۰–۲۰ مقالهٔ evergreen | C | H | ~$15/سال | L→M | ماه ۴+ | متوسط | ROI دیر؛ فقط post-G2 | ★★ |
| D6 | Bluesky (کانال نوظهور adult-tolerant) | labeling بومی؛ starter packs نیش | C | L | 0 | L-M | ماه‌ها | خوب (جدید) | آنالیتیکس ضعیف؛ جامعهٔ کوچک | ★★ |

### ه) Retention و monetization داخل پلتفرم
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | PPV ladder در DM (انسان می‌فرستد) | اولین PPV ارزان ($5–8) → پله‌پله بالا | C | M | 0 | H | هفتهٔ ۱ پس از launch | عالی | unlock<10٪ = گران؛ کالیبره کن | ★★★ |
| E2 | Custom pipeline با فرم استاندارد | منوی custom + قیمت ۲–۴× پایه + چرخهٔ تحویل معین | C | M | 0 | H (۴۰–۶۰٪ درآمد بالغ‌ها `[COI]`) | ماه ۱–۲ | عالی | scope-creep → فرم سفارش سفت | ★★★ |
| E3 | باندل ۳/۶ماهه ۱۰–۴۰٪ تخفیف | rebill قفل‌شده | C | L | 0 | M | ماه ۲+ | خوب | cash-flow جلو، LTV واقعی نامعلوم | ★★ |
| E4 | کمپین win-back بومی | تخفیف به expiredها، دستی | C | L | 0 | M | ماه ۲+ | خوب | تکرار زیاد = بی‌ارزش‌سازی | ★★ |
| E5 | Tip menu ثابت روی پروفایل | منوی شفاف (rating، نام‌بردن، ست عکس) | C | L | 0 | M | فوری | عالی | مرز explicit — کنترل Compliance-Guard | ★★★ |
| E6 | کمپین‌های فصلی از تقویم ۲۰۲۷ | یلدا/کریسمس/ولنتاین — سیگنال فرهنگی فقط بصری | C | M | 0 | M | مناسبتی | عالی | قاعدهٔ #۶ (هیچ متن Persian) | ★★★ |
| E7 | Renew-on پاداش | آیتم رایگان برای rebill-on | C | L | 0 | M | ماه ۲ | خوب | — | ★★ |
| E8 | صفحهٔ VIP دوم | بعد از تثبیت (روز ۹۰+) | C | M | 0 | L→M | ماه ۴+ | متوسط | تقسیم توجه؛ فقط با دادهٔ E1–E3 | ★★ |

### و) Cross-promo، همکاری، آژانس
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | S4S با هم‌ترازها (X/OF) | تبادل معرفی؛ مجاز در OF | C | L | 0 | M | ماه ۲+ | خوب | audience-mismatch؛ اسکمرها | ★★ |
| F2 | Collab محتوایی با creator دیگر | فقط با Release Form داخل OF + verified بودن طرف `[FACT-secondary]` | C | M | 0 | M | ماه ۳+ | سخت (faceless) | نقض consent = strike؛ verdict انسانی | ★★ |
| F3 | خرید promo از صفحه‌های بزرگ | خرید shoutout پولی از اکانت‌های نیش X | G | L | $20–100 | نامعلوم | فوری | متوسط | بازار اسکم‌خیز؛ فقط با track-link و مبلغ کوچک | ★ |
| F4 | آژانس/مدیریت | rev-share معمول ۲۰–۵۰٪ (سالم ۲۵–۳۵٪) `[EST/COI]` | **P (فعلاً)** | — | — | — | — | — | کنترل credential+هویت؛ مغایر privacy دوطرفه؛ مصوب round1: آرشیو تا G3+ → جایگزین: مغز خودمان | ★★ |
| F5 | Micro-collab غیرمستقیم SFW | تبادل با اکانت‌های aesthetic (nail-artist و…) در IG | G | M | 0 | L-M | ماه‌ها | خوب | افشای زنجیرهٔ هویت؛ بدون چهره | ★ |

### ز) مارکت‌پلیس و درآمد مجاور
| # | روش | مکانیزم | وضعیت | تلاش | هزینه | اثر | TTR | تناسب | ریسک | اطمینان |
|---|---|---|---|---|---|---|---|---|---|---|
| G1 | FeetFinder به‌عنوان کانال فرعی | لیستینگ passive؛ بدون promo فعال | G | L | $5–15/ماه | L (دو case صفر-درآمد + Salon $0) | نامعلوم | ضعیف به‌عنوان رشد | pay-before-earn؛ payout کند | ★★★ (که ضعیف است) |
| G2 | Fanvue mirror | آپلود دوره‌ای بهترین‌ها | G | L | 0 | L | ماه‌ها | متوسط | بند مصادرهٔ ۱۲ماهه → برداشت دوره‌ای الزامی | ★★ |
| G3 | استاک feet (Adobe/Foap) | عکس تجاری پا (skincare/podiatry) | C | M | 0 | L ($0–100/ماه `[EST]`) | ماه‌ها | خوب (SFW کامل) | tension با #۱۶ (هویت/invoice) | ★★ |
| G4 | Parts-modeling استرالیا | ~AU$180+/روز؛ گیگ پراکنده | C | M | 0 | L (نامنظم) | نامعلوم | متوسط | نیاز هویت واقعی → تعارض ناشناسی؛ پارک تا حل #۱۶ | ★ |

### ح) Prohibited — فهرست بسته (فقط آگاهی؛ اجرا ممنوع)
| # | تاکتیک رایج فضای adult-marketing | چرا ممنوع | جایگزین امن |
|---|---|---|---|
| P1 | Mass/cold DM (Reddit/X/IG) | spam policy همهٔ پلتفرم‌ها + قاعدهٔ #۷ | A6/B4 تعامل ارگانیک |
| P2 | بات auto-post/auto-reply/auto-DM | نقض ToS + قاعدهٔ قفل‌شده | صف پیش‌نویسِ انسان-تأیید |
| P3 | اکانت fake/sockpuppet برای upvote/hype | ban موج‌ی Reddit؛ کلاهبرداری از فن | رشد کند ارگانیک |
| P4 | خرید فالوئر/engagement pod | مرگ الگوریتمی اکانت + تقلب | S4S واقعی F1 |
| P5 | Scrape لیست کاربر + cold outreach | نقض API ToS + privacy | inbound funnel D1–D3 |
| P6 | هدایت پرداخت به PayPal/crypto/بانک | **قاعدهٔ قفل‌شدهٔ #۳** + ریسک ban دائم | همه‌چیز داخل پلتفرم |
| P7 | AI-chat خودکار با فن‌ها (حتی شفاف) | ToS صریح OF/Fansly `[FACT]` | درفت AI → ارسال دستی (سیاست #۱۴ pending) |
| P8 | Impersonation/جعل «صبا پشت چت است» به‌شکل فریبنده | ریسک اخلاقی/رسانه‌ای + سؤال #۱۴ | سیاست شفافیت مکتوب |
| P9 | Fake giveaway/قرعه‌کشی فریبنده | deceptive practice؛ AU Consumer Law | promo واقعی E4 |
| P10 | Review/upvote manipulation مارکت‌پلیس‌ها | fraud | کیفیت واقعی |
| P11 | هر هدف‌گیری کاربر ایران / افشای شهر | **قواعد #۲ و #۶** | geo-block + «Aussie» |
| P12 | دور زدن age-gate یا فروش به زیر-۱۸ | خط قرمز مطلق | گیت 18+ در D1 |

**۳ نکتهٔ قابل‌اقدام WS-3:**
1. هستهٔ ۸۰/۲۰ فاز validation: A1–A7 (Reddit) + B1–B4 (X) + D1–D3 (زیرساخت) — بقیه بعد از G1.
2. قبل از warm-up: چک in-app وضعیت r/VerifiedFeet + ۲۵ sub (سؤال #۷) و ثبت قوانین verification هر sub در Fable5.
3. Bluesky (D6) را با ۱۵ دقیقه/هفته تست کم‌هزینه کنید — تصمیم رسمی در #۱۷.

---

## §۵ — WS-4: سیستم Multi-Agent («اثر مولتی‌ایجنتی»)

> پایه: [[PROJECT-F-BRAIN-SPEC]] (control-plane + ۷ زیرعامل، propose-only، دو Guard، HITL tiered) **معتبر می‌ماند**. این بخش آن را با دادهٔ روز تکمیل می‌کند: routing مدل، هزینه، memory، eval. هیچ agentی اکشن بیرونی ندارد (قاعدهٔ #۷).

### ۵.۱ کجا multi-agent واقعاً ارزش دارد (نه hype)
ارزش واقعی `[OPINION]`: (۱) رصد رقبا/ترند (روزانه، خسته‌کننده برای انسان)؛ (۲) ideation و تطبیق با تقویم ۲۰۲۷؛ (۳) درفت کپشن/عنوان/DM-script برای صف تأیید؛ (۴) پایش KPI و هشدار انحراف؛ (۵) تحلیل نتیجهٔ آزمایش قیمت؛ (۶) compliance-check خودکار هر کپی قبل از صف انسانی. ارزش کاذب: «فن‌چت خودکار» (ممنوع)، «رشد خودکار» (وجود ندارد)، agent-swarm پیچیده برای تیم ۲ نفره (overhead > بهره) `[OPINION]`.

### ۵.۲ معماری + نگاشت مدل (routing)
```
                    ┌────────────── آری (Cockpit — verdict) ◄─── high-risk
صبا (Studio) ──► Control-Plane (مغز)
                    ├─ Compliance-Guard ── هر خروجی، بدون استثنا (rule-based + LLM ارزان)
                    ├─ Ethics-Guard ────── ضد-دستکاری، محدودهٔ صبا مقدم
                    ├─ Scout (رصد/ترند) ─── Haiku 4.5 + Batch API ── روزانه
                    ├─ Strategist ───────── Sonnet 5 ── هفتگی
                    ├─ Copywriter ───────── Sonnet 5 (درفت) → صف تأیید
                    ├─ Pricer (bandit) ──── محاسبات کلاسیک local + Sonnet برای توضیح ── approval-gated
                    ├─ Scheduler ────────── rule-based (بدون LLM) + تقویم
                    └─ Analyst (KPI) ────── Haiku روزانه / Sonnet هفتگی / Opus فصلی
```
| Agent | ورودی | خروجی | Gate انسانی | مدل/Tier | تناوب |
|---|---|---|---|---|---|
| Scout | فید عمومی Reddit/X (read-only)، بدون login | دایجست ترند/رقبا ۱۰-خطی | ندارد (read-only داخلی) | Haiku 4.5 + Batch | روزانه |
| Strategist | دایجست Scout + تقویم + KPI هفته | پیشنهاد تم هفته + نردبان | تأیید آری (استراتژی) | Sonnet 5 | هفتگی |
| Copywriter | brief صبا/Strategist | ۳ واریانت کپشن/DM-draft | **همیشه** — paste دستی | Sonnet 5 | on-demand |
| Pricer | لاگ فروش تأییدشده | پیشنهاد قیمت PPV بعدی | **همیشه** (پول) | local bandit + Sonnet | هفتگی |
| Scheduler | صف asset تأییدشده | جدول زمان پیشنهادی | تأیید در صف Social Rise | بدون LLM | هفتگی |
| Analyst | export دستی CSV از داشبوردها | KPI report + هشدار انحراف | ندارد (گزارش داخلی) | Haiku→Sonnet | روز/هفته |
| دو Guard | هر خروجی بالا | pass/drop + دلیل | drop نهایی است | rule-based + Haiku | همیشه |

- **قاعدهٔ سخت داده:** هیچ PII فن، هیچ media، هیچ credential وارد هیچ agentی نمی‌شود؛ فقط متادیتا/تجمیعی (مطابق BRAIN-SPEC §۵).
- **ضد-الگو:** هیچ agentی به اکانت OF/Fansly/X متصل نیست؛ Analyst از export دستی می‌خواند، نه API پلتفرم (نقض ToS scraping `[FACT-secondary]`).

### ۵.۳ Memory strategy
- **کوتاه‌مدت:** context هر run؛ dropped بعد از اتمام.
- **بلندمدت:** همین پوشه = source of truth (markdown + Fable5)؛ آرشیو «چه چیزی کار کرد» (BRAIN-SPEC) فقط از نتایج تأییدشده.
- **RAG:** ایندکس محلی روی corpus پروژه (embed محلی یا batch ارزان)؛ retrieval فقط متن خودی؛ هیچ سرویس ابری برای اسناد هویت‌دار `[OPINION — privacy]`.
- Persist نشود: DMهای خام فن‌ها، هر شناسه، media. Persist شود: KPI تجمیعی، قیمت‌ها، performance پست‌ها (بدون username فن).

### ۵.۴ هزینه (قیمت‌های رسمی 2026-07-10 `[FACT]`)
| مدل | ورودی/M | خروجی/M | نکته |
|---|---|---|---|
| Claude Haiku 4.5 | $1 | $5 | Batch ‏−۵۰٪، cache-read ‏$0.10 |
| Claude Sonnet 5 | $2/$10 تا 2026-08-31 → بعد $3/$15 | | پنجرهٔ intro در budgeting لحاظ شود |
| Claude Opus 4.8 | $5 | $25 | فقط تحلیل فصلی |
| GPT-5.4-nano / Gemini 3.1 Flash-Lite | $0.20/$1.25 · $0.25/$1.50 | | گزینهٔ ارزان‌تر Scout |
- ⚠️ tokenizer جدید Sonnet 5/Opus 4.8: ~۳۰٪ توکن بیشتر برای متن یکسان `[FACT — صفحهٔ pricing]`.
- Workload کامل §۵.۲ ≈ ۲٫۱M in / ۰٫۲۸M out در ماه → **Haiku-only ≈ US$3.5 · routing مختلط ≈ US$5–8 (≈AUD 8–12) · همه-Sonnet ≈ US$10.5** `[EST — محاسبه]`. + وب‌سرچ ($10/1k سرچ) ≈ $3–9/ماه اگر Scout روزی ۱۰–۳۰ سرچ بزند.
- نتیجه: **~۱۰–۲۰٪ سقف AUD 100** → ریسک بودجه از قیمت نیست؛ از loop است → hard-cap توکن per-run + kill-switch (موجود در BRAIN-SPEC) کفایت می‌کند. ۲٪-cap فعلی BRAIN-SPEC نسبت به درآمد صفرِ فعلی یعنی بودجهٔ صفر — تا اولین درآمد، سقف مطلق AUD 15/ماه پیشنهاد می‌شود `[OPINION]` → verdict.

### ۵.۵ Monitoring & Eval
- **آفلاین (پیش از استقرار):** promptfoo (رایگان، local) — suite تست برای Copywriter/Guards: ۲۰ کیس طلایی + ۱۰ کیس نقض عمدی (باید drop شود: چهره، explicit، شهر، پرداخت بیرونی، فارسی متنی، زیر-۱۸) `[FACT — ابزار]`؛ اجرای suite قبل از هر تغییر prompt = جلوگیری از regression.
- **آنلاین:** Langfuse (self-host MIT یا cloud free-tier ‏50k unit/ماه) برای trace/هزینه `[FACT — pricing رسمی]`؛ برای یک اپراتور، cloud free کافی است ولی فقط متادیتا (بدون متن حساس) لاگ شود `[OPINION]`.
- **متریک‌های کیفیت agent:** نرخ پذیرش درفت توسط آری/صبا (هدف >۵۰٪)، نرخ drop توسط Guardها (هشدار اگر >۲۰٪ = drift)، دقت هشدارهای Analyst (false-alarm <۳۰٪)، هزینه/هفته.
- **Kill-switch:** هر اخطار پلتفرم = توقف اتوماسیون مرتبط (منشور §۲) + هر عبور از cap = fail-closed.

**۳ نکتهٔ قابل‌اقدام WS-4:**
1. BRAIN-SPEC را با جدول routing §۵.۲ و سقف مطلق AUD 15/ماه (تا اولین درآمد) الحاق کنید — verdict آری.
2. suite ‏promptfoo با ۳۰ کیس بالا ساخته شود **قبل از** اتصال مغز به استودیو؛ معیار قبولی: ۱۰۰٪ dropهای اجباری.
3. پنجرهٔ intro قیمت Sonnet 5 تا 2026-08-31 است؛ بعد از آن هزینه ~۵۰٪ بالا می‌رود — در بودجهٔ سه‌ماهه لحاظ شود.

---

## §۶ — WS-5: Analytics، KPI و Experimentation

### ۶.۱ KPI Tree فاز validation
```
North-star فاز: «درآمد تأییدشدهٔ اولین ۹۰ روز» (G2)
├─ جذب: impressions (هر کانال) → CTR به hub → click به OF (tracking-link)
│    KPIها: پست/هفته، median upvotes، CTR hub→OF (هدف G1: ≥200 کلیک، ≥10٪ click→follow)
├─ فعال‌سازی: free-subs تجمعی (G2: ≥30) → نرخ خریدارشدن (هدف ≥5٪)
│    KPIها: free-subs/هفته، first-purchase-rate، **PPV unlock-rate** (باند سالم ۱۵–۲۵٪ `[COI]`)
├─ درآمد: ARPPU، سهم PPV/custom/tip، **$/script-start**، **چرخهٔ custom (روز)**
├─ نگهداشت: rebill-rate (بنچمارک ۲۰–۳۰٪ ماه۱ `[COI]`)، churn ماهانه، win-back rate
└─ بهره‌وری: **$/ساعت-promo**، **$/ساعت-DM**، delivery-rate صبا (G1: ≥80٪)
```

### ۶.۲ آزمایش‌ها در مقیاس کوچک (بدون over-fitting)
- واقعیت: با <۱۰۰ فالوئر، A/B آماری کلاسیک بی‌معناست. قواعد جایگزین `[OPINION — روش‌شناسی استاندارد small-sample]`:
 ۱. **یک متغیر در هر بازه؛ بازهٔ حداقل ۲ هفته** (بافر نوسان روز-هفته).
 ۲. آستانهٔ تصمیم از پیش ثبت‌شده در Fable5 (مثال: «PPV ‏$8→$12 فقط اگر unlock-rate <۱۰٪ نیفتد»)، نه p-value.
 ۳. شمارش‌ها به‌صورت Beta-Binomial ذهنی: ۳ خرید از ۲۰ ≠ سیگنال؛ حداقل ۳۰–۵۰ مشاهده برای هر نرخ.
 ۴. sequential: توقف زودهنگام فقط برای ضرر فاحش (unlock صفر از ۳۰ ارسال)، نه برد زودهنگام.
 ۵. لاگ هر آزمایش: فرضیه/متغیر/بازه/نتیجه/تصمیم — Pricer فقط از این لاگ یاد می‌گیرد (approval-gated).
- صف آزمایش‌های پیشنهادی ۹۰ روز: (۱) قیمت PPV اول $5 vs $8؛ (۲) عنوان Reddit: توصیفی vs روایی (P4)؛ (۳) ساعت پست X: شب AU vs صبح US؛ (۴) welcome-DM: کوتاه vs منو-دار. — هر کدام ۲ هفته، یکی‌یکی.

### ۶.۳ Dashboard قابل‌نگه‌داری برای تیم ۲ نفره
- منبع: export دستی هفتگی (OF stats + Fansly + Social Rise + GAML) → یک sheet در Fable5؛ ~۳۰ دقیقه/هفته، جمعه‌ها (حلقهٔ KPI منشور).
- ستون‌ها: هفته | پست‌ها (R/X) | upvote-med | کلیک hub | کلیک OF | free-subs | خریدار جدید | unlock٪ | درآمد PPV/custom/tip | rebill٪ | ساعت promo | ساعت DM | $/h | هزینهٔ stack | یادداشت آزمایش.
- سه نمودار کافی: funnel هفتگی (کلیک→sub→خریدار)، درآمد تجمعی vs گیت G2، unlock-rate روند. بیشترش = زینت `[OPINION]`.

**۳ نکتهٔ قابل‌اقدام WS-5:**
1. چهار KPI کاندید round1 (unlock-rate، $/script-start، چرخهٔ custom، $/DM-hour) رسماً وارد قالب داشبورد شوند — همین سند مرجع تعریف.
2. قالب «Experiment Log» ۶-ستونه در Fable5 ساخته شود؛ قانون: هیچ تغییر قیمتی بدون ردیف لاگ.
3. آستانه‌های kill/continue گیت‌های G1/G2 روی داشبورد hard-code شوند تا تصمیم احساسی نشود.

---

## §۷ — WS-6: ریسک، Compliance، Privacy، حقوقی

### ۷.۱ Risk Register (به‌روزشده — تکمیل ۵ ریسک master-reference)
| # | ریسک | احتمال | اثر | امتیاز | Mitigation | Trigger پایش |
|---|---|---|---|---|---|---|
| R1 | consistency پارتنر زیر friction (ریسک #۱ موجود) | H (تست‌نشده) | H | 20/25 | Trial sprint با متریک delivery؛ گزارش مالی زودهنگام | G1 delivery <80٪ |
| R2 | GATE 0 → Branch B (اقامت ایران) | ? | بحرانی | — | هیچ اجرا قبل از ثبت؛ مشاور licensed اگر B | پاسخ صبا |
| R3 | Deplatforming/تعلیق OF | L-M | H | 12 | dual-platform، برداشت مکرر، ایمیل‌لیست، مستندسازی compliance، appeal ≤۶ماه `[FACT — ToS]` | هر اخطار = kill-switch |
| R4 | تغییر policy/مالکیت OF (فوت Radvinsky، فروش سهم `[FACT]`) | M | M-H | 12 | همان R3 + رصد فصلی اخبار Fenix توسط Scout | اخبار فروش/تغییر ToS |
| R5 | فشار پردازندهٔ پرداخت (سابقهٔ ۲۰۲۱ `[FACT]`) | L | H | 8 | تنوع پلتفرم؛ محتوای ما غیر-explicit = کم‌خطرتر `[EST]` | اخبار Visa/MC |
| R6 | لیک محتوا / بازنشر | M-H | M | 12 | WM/NOWM (مصوب)، DMCA takedown (سرویس ~$30–100/ماه بعد از درآمد)، پلن پاسخ لیک (مصوب 07-05) | reverse-search ماهانه |
| R7 | Doxxing/شناسایی صبا یا آری | L-M | بحرانی | 15 | faceless سخت، صفر metadata (EXIF strip در P9)، بدون شهر، بدون دست‌خط باز (A2 با چاپ)، تست cross-contamination ماهانه (مصوب) | هر سؤال هویتی در DM |
| R8 | Age-verification regs (AU under-16 live، UK OSA، EU) `[FACT]` | اجراشده | L-M مستقیم | 6 | مخاطب ما 18+؛ ریسک = misclassification و friction اکانت‌ها؛ گیت 18+ در hub | اخطار سنی پلتفرم |
| R9 | نقض ناخواستهٔ ToS با ابزار (Social Rise proxy-caution جدید) | M | M | 9 | فقط schedule؛ صفر third-party متصل به OF؛ بازبینی فصلی ToS ابزارها | هر اخطار API |
| R10 | مالیات/ساختار AU | M | M | 9 | set-aside ۳۰–۳۵٪ (مصوب)؛ سؤالات مشاور §۷.۲ | اولین payout |
| R11 | مصادرهٔ موجودی Fanvue ‏۱۲ماهه `[FACT — legal رسمی]` | L | L | 4 | یادآور برداشت فصلی در Fable5 | بالانس >0 و >۹۰ روز |
| R12 | هزینه/loop مغز AI | L | L | 4 | cap مطلق AUD 15/ماه تا درآمد؛ fail-closed | گزارش هزینهٔ هفتگی Langfuse |

### ۷.۲ فهرست سؤالات مشاور licensed استرالیا (بدون مشاورهٔ قطعی از سوی ما)
مالیاتی: (۱) زمان بهینهٔ ABN — روز صفر یا G3؟ (تصحیح round1: کسر ۴۷٪ بدون ABN فقط برای پرداخت B2B داخلی است، نه payout پلتفرم خارجی)؛ (۲) GST — آیا درآمد پلتفرم خارجی «GST-free export» است و آستانهٔ ۷۵k چطور شمرده می‌شود؛ (۳) طبقه‌بندی hobby vs business و پیامد استهلاک تجهیزات؛ (۴) ساختار: sole trader آری vs partnership ۵۰/۵۰ vs company — پیامد پرداخت سهم صبا در خارج (Branch-A-dependent)؛ (۵) گزارش‌دهی ارزی USD→AUD و timing؛ (۶) بیمه/superannuation برای self-employed. حقوقی: (۷) قرارداد دونفرهٔ cross-border و enforceability؛ (۸) الزامات نگهداری سوابق consent/سن (AU + الزامات OF)؛ (۹) پیامد حقوقی ارسال درآمد به شخص مقیم ایران در صورت Branch B — **سؤال تعیین‌کننده**؛ (۱۰) IP و برند (ثبت Anar Soles لازم است؟).

### ۷.۳ OpSec عملی (تکمیلی این راند)
- geo-block: ایران (قاعده) + تصمیم دونفره دربارهٔ بلاک AU (پنهان‌ماندن از آشنایان vs از دست دادن بازار محلی) — geo-filter ‏GAML لایهٔ دوم `[FACT-secondary]`؛ VPN-bypass یعنی geo-block کاهش ریسک است نه تضمین → faceless بودن دفاع اصلی می‌ماند.
- verification پابلیک (A2): دست‌خط = biometric ضعیف؛ متن چاپی یا دست‌کش `[OPINION]`.
- سؤال #۱۵ (C2PA) باز می‌ماند؛ RAWها آرشیو شوند (مصوب round1).

**۳ نکتهٔ قابل‌اقدام WS-6:**
1. R4 (گذار مالکیتی OF) به risk register رسمی اضافه شود؛ قاعدهٔ «بالانس >$100 نماند» به verdict برود.
2. لیست ۱۰-سؤالی §۷.۲ متن آمادهٔ جلسهٔ مشاور Track B است — قبل از اولین payout استفاده شود.
3. چک‌لیست AU Spam Act (consent + sender-ID + unsubscribe ≤۵ روز کاری `[FACT — ACMA]`) در قالب ایمیل SendX ثبت شود.

---

## §۸ — WS-7: تحقیق رقابتی و بازار

### ۸.۱ توزیع درآمد (لنگر واقع‌بینی)
- صورت‌های مالی Fenix ‏FY2024: gross ‏$7.22B، payout ‏$5.80B، ‏4.63M اکانت creator، ‏377.5M اکانت فن `[FACT — Companies House via Variety]` → میانگین ≈ **$104/ماه به‌ازای هر اکانت** (شامل خفته‌ها؛ میانگین ≠ میانه).
- XSRUS ‏(۲۰۲۰، تنها تحلیل توزیعی مستقل): median ‏~$180/ماه ناخالص، **مُد = $0**، top-1٪ = ۳۳٪ کل پول، top-10٪ = ۷۳٪، Gini ‏≈0.83 `[FACT — xsrus.com]`. ادعاهای median ‏۲۰۲۴–۲۶ همه بازیافت همین منبع‌اند → «median ‏$100–250/ماه» فقط `[EST]`.
- ⚠️ عدد «بازار $2.1B ‏feet-pics (Statista)» که در وب می‌چرخد به هیچ منبع اولیه نمی‌رسد → **استفاده نشود** `[UNVERIFIED — احتمالاً جعلی]`.

### ۸.۲ نیش feet — قیمت و رفتار موفق‌ها
- قیمت‌های رایج (خوشهٔ vendor، سازگار ولی همگی `[COI]`): sub ‏$5–15؛ عکس تکی $5–10؛ باندل ۱۰تایی $10–30؛ custom عکس $15–50 (نوپا) / $50–150 (جاافتاده)؛ ویدیو ‏~$20–25/دقیقه؛ customs ‏۴۰–۶۰٪ درآمد فروشنده‌های بالغ.
- الگوی creatorهای موفق faceless-feet ‏`[EST — سنتز]`: (۱) positioning حسی/aesthetic نه بدن‌محور؛ (۲) کیدنس روزانهٔ کانال کشف + هفتگی صفحهٔ پولی؛ (۳) درآمد اصلی از DM/custom نه sub؛ (۴) رابطهٔ پایدار با ۱۰–۳۰ خریدار تکراری به‌جای شکار دائمی؛ (۵) کار واقعی: کیس £30k/ماه = ۶:۳۰ تا ۲۱ بدون تعطیلی `[FACT — گزارش، اعداد خوداظهار]`.
- کیس‌های مستند: Salon (اوت ۲۰۲۵) — faceless روی FeetFinder، هفته‌ها تلاش فعال، **درآمد $0 و خالص −$5.54** `[FACT]`؛ «SeducingSole ‏$200k/2023» = ادعای بازاریابی خود پلتفرم `[COI — unaudited]`؛ Coppage ‏$1M = outlier رسانه‌ای face-out و explicit — بی‌ربط به بنچمارک ما `[FACT — گزارش]`.

### ۸.۳ Retention benchmarks (همگی vendor — directional)
churn ماهانه ۳۰–۶۰٪ (خوب: ۳۰–۴۰٪، عالی <۲۰٪)؛ rebill بعد ماه ۱: ‏۲۰–۳۰٪ معمول، ۴۰–۵۰٪ قوی؛ free→paying ‏۵–۱۵٪؛ unlock بهینه ۱۵–۲۵٪ `[COI]`. هیچ دادهٔ مستقل post-2020 وجود ندارد — شکاف دانشی واقعی؛ اعداد خودمان از ماه ۱ ارزشمندتر از هر بنچمارک است `[OPINION]`.

### ۸.۴ Delta-map این راند مقابل corpus
| نوع | یافته |
|---|---|
| **تأیید** | dual-platform؛ Reddit-engine؛ مارکت‌پلیس≠رشد (بار سوم)؛ X ACC جعلی (بار سوم)؛ Fansly ‏80/20+minها؛ GAML $9؛ Social Rise ‏$29.99؛ ممنوعیت AI-DM؛ median پایین؛ سناریوهای Floor/Base/Upside؛ بند Fanvue |
| **تعارض** | (۱) سقف PPV: $50 vs $100 vs $200 بین منابع `[UNVERIFIED]` → چک داشبورد؛ (۲) «median ‏$180» در یک منبع per-year و در XSRUS per-month — مرجع ما XSRUS ماهانه با تگ `[EST]`؛ (۳) ادعای compliance کامل Social Rise vs تبلیغ proxy همان vendor → tension ثبت شد |
| **افزوده** | فوت Radvinsky + فروش سهم $3B (R4)؛ AU under-16 live + UK OSA + EU-Reddit (R8)؛ مزیت unlabeled-X برای نیش؛ free-page-only بودن price-lock تایم‌لاین (ورودی #۱۰)؛ سقف tip ‏$100/۴ماه اول؛ Fanvue ‏85/15 intro؛ Bluesky (#۱۷)؛ رد «$2.1B»؛ کیس Salon ‏$0؛ پنجرهٔ قیمت Sonnet 5؛ tokenizer +۳۰٪؛ Ofcom fine؛ appeal ‏۶ماهه OF |

**۳ نکتهٔ قابل‌اقدام WS-7:**
1. در همهٔ اسناد، هر benchmark درآمدی بدون منبع اولیه با `[COI]` بازتگ شود؛ «$2.1B» اگر جایی از corpus آمده حذف شود.
2. انتظارات صبا با «مُد=صفر + کیس Salon» کالیبره شود — بخشی از پیام GATE 0/توافق‌نامه (شرط تعهد: دیدن مسیر پول).
3. از هفتهٔ ۴، بنچمارک شخصی جایگزین بنچمارک وب شود (داشبورد §۶.۳).

---

## §۹ — Validation-Phase Roadmap (۳۰/۶۰/۹۰ — همه پشت GATE 0)

### روز ۰–۳۰ (پیش‌اجرا + warm-up مشروط)
| گام | معیار موفقیت |
|---|---|
| ارسال پیام G0 + بازپرسیدن سؤال آخر → ثبت Branch A/B | ثبت در PROJECT/DecisionLog |
| اگر A: امضای توافق دونفره (+ بند شفافیت DM ‏#۱۴) | سند امضاشده |
| Reconcile چهارگانه: ساعت صبا، برند (پیشنهاد: Anar Soles)، نردبان قیمت (پیشنهاد: EXT-04 با دادهٔ §۳)، وزن Fansly | ۴ ردیف DecisionLog |
| Day-Zero ‏(۱۴ آیتم، ~A$13) + ۳ چک داشبوردی §۲ | چک‌لیست سبز |
| Fable5 حداقلی (۴ DB) + قالب داشبورد و Experiment Log | ثبت اولین ردیف |
| suite ‏promptfoo ‏۳۰-کیسه → اتصال مغز (propose-only) | ۱۰۰٪ drop اجباری‌ها |
| Shoot #1 → بانک ≥۳۰ asset با بافر ≥۷ روز (مصوب) | ۳۰ asset تگ‌خورده |
| Warm-up: اکانت X + Reddit، verificationها، GAML | بدون هیچ اخطار |

### روز ۳۰–۶۰ (launch + G1)
Launch OF free + Fansly (روز ~۲۱–۳۰ طبق بلوپرینت) · کیدنس A1–A7/B1–B4 · welcome-flow دستی · اولین آزمایش قیمت (§۶.۲) · ایمیل‌لیست فعال. **گیت G1 (هفتهٔ ۶):** ≥۲۰۰ کلیک، ≥۱۰٪ click→follow، ≥۸۰٪ delivery صبا → عبور یا kill/pivot طبق ACQUISITION-ENGINE.

### روز ۶۰–۹۰ (بهینه‌سازی + G2)
دو آزمایش بعدی صف §۶.۲ · win-back اولین expiredها · تصمیم Bluesky ‏(#۱۷) · جلسهٔ مشاور با §۷.۲ قبل از اولین payout. **گیت G2 (هفتهٔ ۱۲):** ≥۳۰ free-sub، ≥۵٪ free→paid، اولین AUD 100 → ادامه به فاز بعد یا توقف مستند.

### §۹.۵ — Devil's Advocate (رد محتمل توصیه‌های کلیدی + شرط شکست)
| توصیه | ردِ محتمل | شرط شکست (kill-condition) |
|---|---|---|
| free-page + PPV به‌جای paid-page | free-page فیلتر کیفیت ندارد؛ ممکن است ۳۰ فالوئر رایگان جمع شود ولی unlock نزدیک صفر بماند و زمان DM بسوزد | اگر تا هفتهٔ ۸: unlock <۵٪ و درآمد PPV <A$50 → تست صفحهٔ paid ‏$4.99 |
| Reddit به‌عنوان موتور #۱ | موج age-verification (UK live، EU از ژوئن ۲۰۲۶) ریچ NSFW را ساختاری کم می‌کند؛ اگر AU هم verification سخت بگذارد، قیف اصلی نصف می‌شود | افت >۵۰٪ در median upvotes دو هفتهٔ متوالی → وزن به X/Bluesky |
| ادامهٔ کار روی OF در دورهٔ گذار مالکیتی | مالک جدید می‌تواند policy نیش/payout را عوض کند؛ سابقهٔ ۲۰۲۱ نشان داد ۶ روز کافی است | هر تغییر ToS مالی/محتوایی → فعال‌سازی پلن Fansly-primary |
| ساخت مغز multi-agent در فاز validation | برای تیم ۲ نفره با صفر درآمد، حتی ۱۰ ساعت ساخت/نگه‌داری ممکن است ROI منفی داشته باشد؛ خطر «ابزارسازی به‌جای اجرا» (الگوی فعلی corpus: اسناد زیاد، اجرا صفر) | اگر تا G1 مغز ≥۵ ساعت/هفته بخورد یا نرخ پذیرش درفت <۳۰٪ → freeze مغز، اجرای دستی |
| کالیبرهٔ پایین انتظارات (مُد=صفر) | ممکن است انگیزهٔ صبا (فاکتور بقای پروژه، ~۶٫۵/۱۰) را بشکند؛ واقع‌بینی افراطی هم ریسک است | اگر پیام کالیبره → عقب‌نشینی صبا: بازطراحی سهم/انتظارات به‌جای وارونه‌گویی |

---

## §۱۰ — Sources & Confidence

**اولیه/رسمی (اعتماد بالا):** onlyfans.com/terms · legal.fanvue.com/creator-earnings-payouts · help.x.com (adult-content, media-settings, monetization-standards) · business.x.com (ads policy) · business.reddithelp.com (ads/prohibited) · support.reddithelp.com · tiktok.com/community-guidelines · transparency.meta.com (ad standards) · support.google.com/adspolicy · linktr.ee/s/about/community-standards · mailchimp.com/legal/acceptable_use · acma.gov.au (Spam Act) · esafety.gov.au (under-16) · ofcom.org.uk (جریمهٔ Fenix) · docs.n8n.io/sustainable-use-license · zapier.com/legal/acceptable-use-policy · platform.claude.com/docs pricing · developers.openai.com/api/docs/pricing · ai.google.dev/gemini-api/docs/pricing · langfuse.com/pricing · social-rise.com/pricing · helpx.adobe.com (royalty).
**ژورنالیسم معتبر (بالا-متوسط):** Variety (صورت‌های Fenix ‏FY23/24) · Forbes (Radvinsky، فروش سهم ۲۰۲۵/۲۰۲۶) · Reuters via wire ‏(AI-chat ban، ژوئیهٔ ۲۰۲۴) · 404 Media (Fansly) · Rolling Stone (پاکسازی TikTok) · Time/BuzzFeed (۲۰۲۱) · Salon (کیس $0، اوت ۲۰۲۵) · Hollywood Reporter (Fansly discovery) · EFF/CNBC (age-verification) · Vice (Linktree).
**تحلیلی مستقل:** xsrus.com (توزیع ۲۰۲۰ — کهنه ولی یگانه).
**Vendor/affiliate ‏`[COI]` (وزن پایین؛ فقط قیمت/مکانیک consensus):** social-rise blog، supercreator، postpone، pseudoface، tryfootly، infloww، arunatalent، divafluence، pippinclub، enforcity، creatorgrowlabs، fanspicy، maho-management، substy، sirency و مشابه.
**سطح اطمینان کلی سند:** ساختار پلتفرم/policy = بالا؛ بنچمارک‌های نیش/retention = پایین-متوسط (سلطهٔ `[COI]`)؛ اقتصاد واحد = مدل تصمیم، نه پیش‌بینی.

---

## §۱۱ — Open Questions (برای انسان/دادهٔ تکمیلی)

**جدید این راند:**
- **#۱۷ — Bluesky:** کانال درجه‌۳ اضافه شود؟ (کم‌ریسک، جامعهٔ کوچک، آنالیتیکس ضعیف) — پیشنهاد: تست ۱۵دقیقه/هفته بعد از G1 `[OPEN — P2]`.
- **#۱۸ — سقف واقعی PPV و tip در داشبورد OF:** منابع متناقض ($50/$100/$200) — چک روز اول `[OPEN — P1، بدون هزینه]`.
- **#۱۹ — بلاک جغرافیایی استرالیا (privacy) یا باز نگه داشتن (بازار):** تصمیم دونفره قبل از launch `[OPEN — P1]`.
- **#۲۰ — سقف مطلق هزینهٔ مغز (AUD 15/ماه تا اولین درآمد):** جایگزین موقت ۲٪-cap — verdict آری `[OPEN — P2]`.
**به‌روزرسانی قبلی‌ها:** #۱۰ (نردبان قیمت): دادهٔ این راند (free-page price-lock + قیمت‌های نیش) نسخهٔ EXT-04 را تقویت می‌کند → آمادهٔ بستن. · #۷ (r/VerifiedFeet): این راند هم quarantine را نه تأیید و نه رد کرد — چک in-app می‌ماند. · #۱۲ (وزن‌های Phoenix): این راند بررسی نکرد — باز. · #۱۴/#۱۵/#۱۶: بدون تغییر، ورودی جدید ندارند جز tension بیشتر #۱۶ با دادهٔ parts-modeling (نیاز هویت واقعی).
**شکاف‌های دانشی:** دادهٔ مستقل retention (وجود ندارد — با دادهٔ خودمان پر می‌شود)؛ صورت مالی FY2025 ‏Fenix (~سپتامبر ۲۰۲۶)؛ متن زندهٔ بند AI-chat (verify مرورگری)؛ policy کامل promo در Fansly (تحقیق نشد).

---
*پایان Round 2 — propose-only؛ هیچ قاعدهٔ قفل‌شده‌ای تغییر نکرد؛ همهٔ اکشن‌ها پشت GATE 0 و verdict انسانی.*



