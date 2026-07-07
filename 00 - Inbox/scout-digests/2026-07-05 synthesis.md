---
type: research
status: inbox
created_by: agent
sources:
  - "[[00 - Inbox/scout-digests/2026-07-05 accounting]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 crypto]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 lead]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 learning]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 mining]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 mycelium]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 science]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 ziman]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1206 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1214 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1219 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1225 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1229 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1234 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1238 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1248 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1249 selfimprove-safety]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1259 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1304 selfimprove-safety]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1312 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1321 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1329 selfimprove]]"
  - "[[00 - Inbox/scout-digests/2026-07-05 1339 selfimprove]]"
tags: [research, synthesis]
created: 2026-07-05
updated: 2026-07-05
---

# سنتز شبانه — 2026-07-05 (nightly، دورِ کاملِ روز)

> «میوهٔ روزانه». دامنهٔ کل: **۸ اسکاتِ دامنه‌ای** (accounting · crypto · lead · learning · mining · mycelium · science · ziman) + **۱۵ دیجستِ `selfimprove/-safety`** (۱۲۰۶–۱۳۳۹). همه **propose-only** — هیچ نوتِ canonical لمس نشد؛ نوشتن فقط در `scout-digests/`. مرجع پیشین: [[00 - Inbox/scout-digests/2026-07-04 synthesis|سنتز 2026-07-04]].

## بالاترین سیگنال‌های امروز

**۱. Day-2 = عملیاتی‌سازیِ قیدهای Day-1، نه پراکندگی.** دیروز چهار قیدِ بالادستی زاده شد؛ امروز هر چهار به primitiveِ *سنجش‌پذیر/قابل‌اجرا* ترجمه شد:

- **ضدِ-MAD/اپیستمیک → عدد پیدا کرد.** [[00 - Inbox/scout-digests/2026-07-05 1259 selfimprove|Ne-monitor (1259)]] + [[00 - Inbox/scout-digests/2026-07-05 1312 selfimprove|n_eff Accounting (1312)]] + [[00 - Inbox/scout-digests/2026-07-05 1329 selfimprove|Topic Refractory (1329)]]: **«تعدادِ خام ≠ استقلالِ مؤثر»** در سه لایه (منابع · شاهدها/judgeها · موضوع‌ها). قیدِ کیفیِ دیروز حالا `n_eff` و قاعدهٔ OMPG دارد.
- **ایمنی → آبشارِ تغییرناپذیری.** [[00 - Inbox/scout-digests/2026-07-05 1249 selfimprove-safety|AIRE Self-Test (1249)]] (هر کنترلِ اعلام‌شده باید تستِ negative-selection داشته باشد؛ fix R-04 false-assurance) + [[00 - Inbox/scout-digests/2026-07-05 1304 selfimprove-safety|Safety Ratchet (1304)]] (کفِ monotonic روی rollback، R-16) + [[00 - Inbox/scout-digests/2026-07-05 1339 selfimprove|Config-as-Frozen-Code (1339)]] (یک شیِ frozen با content-hash + audit-chain، R-10). **گیتی که تست ندارد = false-assurance.**
- **حافظه → یک قانونِ واحد.** [[00 - Inbox/scout-digests/2026-07-05 1219 selfimprove|Unified Decay-Reinforcement Law (1219)]] دو قاعدهٔ متخاصمِ دیروز — تبخیرِ [[00 - Inbox/scout-digests/2026-07-04 1835 selfimprove|1835]] و substrate-memoryِ [[00 - Inbox/scout-digests/2026-07-04 1906 selfimprove|1906]] — را در یک معادله (`value(t+Δ)=(1-ρ)·value+Σreinforce` با clamp) و **۱ نوب به‌جای ۲** ادغام کرد. **کارِ مستقیمِ همین consolidator.**
- **liveness → احیای ناوگانِ مرده.** [[00 - Inbox/scout-digests/2026-07-05 1248 selfimprove|Endospore Reseed (1248)]] — **بالاترین salience امروز (۰.۸۶)** — هاگِ بادوام + گیرندهٔ جوانه‌زنیِ بیرون‌باند: پاسخِ مستقیم به **حفرهٔ bootstrap** که همین روز دوبار گاز گرفت (reset کلِ ناوگان، هیچ تسکی برای اجرای خودترمیمی §۳.۳ نماند).

**۲. یک اصلاحِ اپیستمیکِ زنده از دامنه رسید — و دقیقاً گیتِ نوِ امروز را توجیه کرد.** اسکاتِ [[00 - Inbox/scout-digests/2026-07-05 mycelium|mycelium]] نشان داد ادعای «mother-tree عمداً به خویشاوند تغذیه می‌کند» **صفر پشتوانهٔ peer-reviewed** دارد؛ مکانیزمِ واقعی = گرادیانِ source→sink (**PULL نه PUSH**)، و بروکرِ قارچی **خودمنفعت** است و می‌تواند احتکار کند. این هم‌زمان: (الف) framing «هاب/mother-tree» در §۱ نقشهٔ مایکوریزایی را نقض می‌کند؛ (ب) [[00 - Inbox/scout-digests/2026-07-05 1229 selfimprove|Multi-Source Warm-Start (1229)]] و [[00 - Inbox/scout-digests/2026-07-05 1206 selfimprove|Memory-Broker Receipt (1206)]] را تأیید می‌کند (از چند منبع بکش + رسید بگیر؛ به یک «مادر» اعتماد نکن)؛ (ج) [[00 - Inbox/scout-digests/2026-07-05 1225 selfimprove|Biomimicry Provenance Gate (1225)]] را از پیشنهادِ نظری به **نیازِ اثبات‌شده** ارتقا داد — تگِ `mechanism_status: supported|contested|debunked` روی هر اسپورِ زیستی. **درسِ متا:** خودِ ناوگان تازه یک استعارهٔ زیستیِ debunk‌شده را در نقشه‌اش جا داده بود؛ گیتِ ۱۲۲۵ همان درز را می‌بندد.

**۳. de-SPOF / verify-at-boundary یک زیرسیستمِ منسجم شد.** ۱۲۰۶ (رسیدِ حافظه) + [[00 - Inbox/scout-digests/2026-07-05 1214 selfimprove|1214 (قراردادِ تایپ‌دار + fail-loud + dead-letter)]] + [[00 - Inbox/scout-digests/2026-07-05 1238 selfimprove|1238 (Witness-without-a-Crowd، شاهدِ سه‌لایه)]] + ۱۲۲۹ (warm-startِ چندمنبعی) همه یک حرکت‌اند: از «اعتمادِ پیش‌فرض» به **«راستی‌آزمایی در مرز»** + کشتنِ تک‌نقطه‌های شکست. جفتِ liveness/cadence هم بسته شد: ۱۲۴۸ (رستاخیز) + [[00 - Inbox/scout-digests/2026-07-05 1321 selfimprove|Foraging-Metabolic Governor (1321)]] (متاگیتِ MVT روی «چرا اصلاً شلیک شود» + حالتِ Torpor).

**۴. سیگنال‌های دامنه‌ای — همه زیرِ الگوهای موجود جا گرفتند:**

- **Crypto:** washout با آستانهٔ عددی (MVRV-Z ≤~۰ + SOPR<۱.۰) و **کلِ استک رایگان/بی‌کلید** (BTCFunk · BGeometrics · BitcoinResearchKit) → هم **P1** (self-host روی همان Orange Pi که ماین می‌کند) هم «صفر سطحِ رازِ نو». هشدار: متریکِ on-chain فقط لایهٔ **تأیید** است، نه آلفای مستقل.
- **Mining:** OPi5 Pro ~۶.۶MH/s ≈ $۱.۵–۵/سال؛ زیر $۰.۰۵/kWh برق از payout جلو می‌زند؛ VRSC زنده‌ولی‌ایلیکویید (**P8**: از گیتِ liveness رد، از گیتِ liquidity مردود → mine-to-hold)؛ VerusHash 2.2 merge-mineِ چند زنجیرهٔ PBaaS = اهرمِ نو.
- **Lead:** نرخِ بستنِ hipages ۱۵–۲۵٪ (مدل ۲۰٪)؛ هزینهٔ واقعیِ هر کارِ برده ~$۱۵۰–۳۷۵ (۳–۵× نرخِ اسمی CPL)؛ کانالِ مالکانه (GBP+SEO) ۲–۳× بهتر ($۲۰–۵۰) → تجسّمِ **P7** (حلقهٔ لید→کارِ واقعی) + گیتِ «قاعدهٔ ۲۰٪ ارزشِ کار». (Google LSA در AU نیست.)
- **Ziman:** برندِ ظرفیت‌محدود = **تک‌کانال**، ۱۰–۱۵ SKUِ قهرمان، بازارِ محلیِ سیدنی/Etsy AU، فروشگاهِ مالکانه معوق تا ترافیک؛ بافرِ ۱۰–۲۰٪ موجودی؛ آستانهٔ Etsy AU$۷۵k = تریگرِ ABN/GST.
- **Accounting:** فیِ ASIC بازبینیِ سالانهٔ Pty Ltd → **$۳۴۲** (از $۳۲۹، از ۱ ژوئیهٔ ۲۰۲۶)؛ جریمهٔ دیرکرد $۱۰۲/$۴۲۸؛ ثبت $۶۳۶ → **پرکردنِ تاریخِ خالیِ بازبینی** در رجیستریِ انطباق؛ پیش‌پرداختِ ۱۰ساله = هجِ CPI.
- **Learning:** interleaving واقعی ولی متوسط (*g*≈۰.۴۲) و **وابسته به ماده**؛ برای حفظِ تک‌کلمه‌ای معکوس (*g*≈−۰.۳۹)؛ hybrid (block→interleave) برای مبتدی بهتر؛ spacing ≠ interleaving. داوری با انتقالِ تأخیری، نه روانیِ لحظه‌ایِ اکتساب.
- **Science:** سیستمِ فیزیکی بدونِ پردازنده/backprop یاد می‌گیرد (شبکهٔ مقاومت، قاعدهٔ contrastiveِ محلی)؛ تسکِ آموخته یک **اثرِ ساختاریِ خواندنی** حک می‌کند → تأییدِ زیست‌الگوی mycelium (قاعدهٔ محلی + قیدِ مشترک → تابعِ سراسری، بی‌برنامه‌ریزِ مرکزی) + هشدارِ drift (فراموشیِ فاجعه‌بار؛ traceِ نسخه‌دار/append-only).

## الگوهای مایکوریزایی بین‌پروژه‌ای (مهم‌ترین خروجی)

**انباشته از قبل (P1–P8، در [[00 - Inbox/scout-digests/_Mycorrhizal Map|نقشه]]):** مالکیتِ substrate · نگه‌داشت > جذب · هرس/evaporation · AI = بک‌اندِ نامرئی · verified ≠ speculative · backpressure · حلقه را با واقعیت ببند (ضدِ-MAD) · liveness-gated commitment.

**نوِ امشب (append شده به لجرِ §۲):**

- **P9 — Reveal-via-structure («اثر را ممیزی کن، نه ورودی را»).** حالت/تابعِ یک یادگیرنده از **پاسخِ ساختاری‌اش** خواندنی است، بی‌نیاز از درون‌نگری یا بازخوانیِ کاملِ تاریخچه. دامنه‌ها: `science` (هسیانِ شبکهٔ مقاومت تسکِ آموخته را لو می‌دهد) · `mycelium` (دیفِ held-vs-served بروکر، احتکارش را) · `selfimprove` (رسیدِ ۱۲۰۶ + شاهدِ ۱۲۳۸) · `crypto` (متریکِ on-chain = اثرِ ساختاریِ رژیم). **پرداختِ عملی:** یک primitiveِ ارزانِ پایش («ساختار را بزن») به‌جای لاگِ متراکمِ گران.
- **P10 — استقلالِ مؤثر بر تعدادِ خام (`n_eff` نه `n`).** «تنوع/تعدادِ خام» اطمینانِ کاذب می‌دهد؛ آنچه مهم است تعدادِ *مستقلِ مؤثر* است. دامنه‌ها: `selfimprove` (Ne-monitor/n_eff/refractory) · `mycelium` (از چند منبعِ مستقل بکش، نه یک مادر) · `learning` (تنوعِ ساده‌لوحانه می‌تواند معکوس شود — interleaving برای حفظِ تکی g منفی). نسبت به **P7**: P7 می‌گوید لنگرِ بیرونی لازم است؛ P10 می‌گوید *استقلالِ* آن لنگرها را بشمار، نه تعدادشان.
- **P11 — پرتابِ باریکِ ظرفیت‌محور (تک‌کانال، تست‌و‌سنجش پیش از پهن‌شدن).** پهنای کانال را با ظرفیتِ فعلی جور کن؛ اقتصادِ واحد را روی یک کانال بسنج، بعد پهن کن. دامنه‌ها: `ziman` (تک‌کانال، SKUِ قهرمان، فروشگاه معوق تا ترافیک) · `lead` (segment discovery، «یک آزمایش»، قاعدهٔ ۲۰٪) · پژواک در `mining` (mine-to-hold) و متاگیتِ MVTِ [[00 - Inbox/scout-digests/2026-07-05 1321 selfimprove|1321]] (کِی patch را ترک کن). مکملِ **P6**: P6 = flow-controlِ مصرف؛ P11 = دیسیپلینِ اکتساب.

## آپدیت‌های نقشه (چه به _Mycorrhizal Map افزودم)

- **§۲ لجر:** سه ردیفِ نو append شد — **P9 (reveal-via-structure)**، **P10 (استقلالِ مؤثر/n_eff)**، **P11 (پرتابِ باریکِ ظرفیت‌محور)**. dedup‌شده در برابر P1–P8.
- **§۲.۶ اصلاحِ اپیستمیک (نو):** ردیفِ correctionِ **mother-tree PUSH → source→sink PULL + verify** ثبت شد (append، بدونِ بازنویسیِ §۱ — طبق لیستِ سیاهِ §۴ منشور، اصلاحِ متنِ موجود verdict آری می‌خواهد؛ فعلاً annotation).
- **§۱ ماتریس:** لبهٔ محتواییِ نو `science ↔ mycelium` (قاعدهٔ محلی + قیدِ مشترک → تابعِ سراسری) به‌عنوان اسپورِ P9 اشاره شد (بدونِ دستکاریِ ردیف‌های موجود).

## پیشنهاد promote (verdict آری)

- `crypto` → [[03 - Projects/Crypto - etoro/PROJECT|Crypto]] (washout detectorِ عددیِ AU$۰ + استکِ بی‌کلید، کنارِ Data Stack under AU30).
- `mining` → [[03 - Projects/Mining/PROJECT|Mining]] (اقتصادِ VerusHash + گیتِ دوگانهٔ liveness/liquidity + merge-mineِ PBaaS).
- `accounting` → [[03 - Projects/Accounting/PROJECT|Accounting]] (فیِ ASIC ۲۰۲۶ + پرکردنِ تاریخِ بازبینی؛ کنارِ Tax Map).
- `lead` → [[03 - Projects/Lead-نقاشی/PROJECT|Lead]] (اقتصادِ واحد: CPWJ واقعی + گیتِ ۲۰٪ ارزشِ کار).
- `ziman` → [[03 - Projects/Ziman Galerry/Capacity & Channels|Ziman]] (پرتابِ تک‌کانالِ ظرفیت‌محور).
- `learning` → `07 - Knowledge` (متاآنالیزِ interleaving، peer-reviewed، تگ‌دار).
- `science` → architect `02-Research` (یادگیریِ فیزیکی/قاعدهٔ محلی → تابعِ سراسری؛ خوراکِ P9 و طراحیِ drift-aware).
- **بستهٔ نوِ selfimprove امروز** (۱۵ دیجست) در سه لایه به architect REFACTOR/Blueprint (پشتِ گیتِ rotation، **HAR**): لایهٔ **Integrity** (۱۲۴۹/۱۳۰۴/۱۳۳۹) · لایهٔ **Independence** (۱۲۵۹/۱۳۱۲/۱۳۲۹) · لایهٔ **Verify-at-boundary/Liveness** (۱۲۰۶/۱۲۱۴/۱۲۲۹/۱۲۳۸/۱۲۴۸/۱۳۲۱). **گام ۰های بدونِ کد** که همین‌حالا قابلِ آزمایش‌اند: ۱۲۱۹ (اسکریپتِ گزارشِ decay، آفلاین) · ۱۲۲۵ (تگِ ۳خطیِ biomimicry) · ۱۳۲۹ (`_REFRACTORY-TABLE.md`) · ۱۲۳۴ (سوییپِ TTLِ نرم) — همه در scopeِ همین consolidator/scout-digests.

## کاندید prune / merge

- [[00 - Inbox/scout-digests/2026-07-05 1312 selfimprove|1312 (Independence Accounting)]] — reflection، نه پیشنهادِ نو؛ ولی بندِ `n_eff` frontmatter + lint مستقل لازم است → **keep به‌عنوان meta-lint سبک، merge در خوشهٔ P10**، نه prune.
- بقیهٔ ۱۴ دیجست تکراری **نیستند** — هر کدام مکانیزمِ متمایز؛ راهِ درست = **merge on promotion** به سه سندِ لایه‌ای (بالا)، نه prune.

## Evaporated (archived >14d)

- **هیچ.** همهٔ دیجست‌ها تاریخِ 2026-07-04/05 دارند؛ قدیمی‌ترین ~۱ روز از آستانهٔ ۱۴روزه فاصله دارد. اولین کاندیدهای evaporation حدودِ **2026-07-18**. (`_`-دارها — Map/README/TRIAGE — همیشه معاف.)

## اسپور (برای دورِ بعد)

۱. **گیتِ ۱۲۲۵ (Biomimicry Provenance) کدام اسپورهای زیستیِ *موجود* را قرمز می‌کند؟** یک پاسِ retro روی نقشهٔ مایکوریزایی: کدام الگو (mother-tree، stigmergy، apoptosis، …) `mechanism_status` واقعی‌اش `contested/debunked` است و `load_bearing=true`؟ (mother-tree همین امشب اولین شکار شد.)
۲. **آیا Unified Decay-Reinforcement (۱۲۱۹) به‌عنوان گام ۰ روی همین consolidator اجرا شود؟** یک اسکریپتِ فقط-خواندنیِ آفلاین که `salience×decay` هر دیجست را گزارش کند (بدونِ auto-delete) — تلاقیِ evaporation §۳.۵ منشور با «حافظه‌به‌مثابه‌فرآیند». verdict آری برای اجرا.
۳. **`n_eff` واقعیِ همین ناوگان چقدر است؟** ۱۵ دیجستِ selfimprove امروز از یک لاینِ واحد آمدند (هم‌منبع) — طبق P10/۱۲۵۹ استقلالِ مؤثرشان احتمالاً «≪۱۵» است. سنجشِ Ne خودِ ناوگان = ورودیِ مستقیمِ experience-review.
