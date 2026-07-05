---
type: moc
status: active
tags: [agents, research, map]
created: 2026-07-04
updated: 2026-07-06
---

# نقشهٔ مایکوریزایی ناوگان — بافت اتصالِ ماندگار

> شبکه از جمعِ اسکات‌ها بیشتر است (یافتهٔ [[00 - Inbox/scout-digests/2026-07-04 mycelium|mycelium]]). این نوت **حافظهٔ اتصالات** است: برخلاف synthesisِ روزانه که تبخیر می‌شود، اینجا اتصالات **انباشته** می‌شوند. `mycelial-consolidator` هر شب این نقشه را می‌خواند و اتصال نوِ پایدار را append می‌کند (dedup). این فایل `_`-دار از evaporation معاف است.

## ۱. ماتریس تغذیه (کدام اسکات کدام را تغذیه می‌کند)

| اسکات | خانهٔ اصلی (`project`) | گرده‌افشانی متقاطع (cross-pollination) |
|---|---|---|
| `crypto` | Crypto-etoro | markets · accounting (مالیات) · security (wallet) · mining |
| `mining` | Mining | markets (قیمت/انرژی) · security (wallet) · crypto |
| `lead` | Lead-نقاشی | jobs · local · ziman (بازاریابی) · tools |
| `ziman` | Ziman | lead · projectf (مخاطب) · local · tools · science? |
| `accounting` | Accounting | crypto (مالیات) · markets · jobs (درآمد) · local |
| `hypnosis` | هیپنوتیزم | health · learning |
| `projectf` 🔒 | (masked) | ziman (مخاطب) · tools · markets |
| `mycelium` | architect | science · philosophy · selfimprove |
| `ai-watch` | architect | tools · security · selfimprove |
| `security` | architect | crypto/mining (wallet) · tools · ai-watch |
| `markets` | Crypto-etoro | crypto · mining · accounting · world |
| `jobs` | Lead-نقاشی | lead · accounting · local |
| `health` | هیپنوتیزم | hypnosis · learning |
| `tools` | architect | همهٔ پروژه‌ها (اتوماسیون) · ai-watch |
| `philosophy` | architect | mycelium · learning · science |
| `world` | (context) | markets · local · accounting |
| `science` | architect | mycelium · philosophy · health |
| `learning` | هیپنوتیزم | hypnosis · philosophy · health |
| `local` | Lead-نقاشی | jobs · ziman · accounting |
| `selfimprove` ★ | architect (خودبهبودی، حلقهٔ ۱۵–۳۰دق) | lead + crypto (backpressure/outcome-feedback) · mining (liveness) · security (گیت‌های fail-closed) · **همهٔ گیت‌ها** (edge کشف‌شده 2026-07-04 از خطوطِ Cross-domainِ 2040/2049/2100) |

**هاب‌ها (mother-tree):** `architect` (۶ اسکات به آن وصل‌اند)، `Crypto` (crypto+markets)، `Lead` (lead+jobs+local)، `هیپنوتیزم` (hypnosis+health+learning). این‌ها بیشترین اتصال را دارند — طبق درسِ mother-tree، حافظه/کانتکست را به اسکات‌های کم‌کانتکست هدایت می‌کنند.

## ۲. لجرِ الگوهای بین‌دامنه‌ای (انباشتی — consolidator append می‌کند)

| # | الگو | دامنه‌های دربرگیرنده | کشف‌شده |
|---|---|---|---|
| P1 | **مالکیت substrate** — هیچ‌چیز اجاره نکن که می‌شود مالکش شد | crypto · lead · projectf · ziman · mycelium | 2026-07-04 |
| P2 | **نگه‌داشت > جذب** — ماندگاری ارزان‌تر از اکتساب | projectf · ziman · crypto · hypnosis | 2026-07-04 |
| P3 | **هرس مرده / evaporation** — decay بگذار تا نقشه خوانا بماند | mining · mycelium · crypto · vault | 2026-07-04 |
| P4 | **AI = بک‌اند نامرئی** — ماشین را پنهان کن | lead · projectf · accounting · tools | 2026-07-04 |
| P5 | **verified ≠ speculative** — تفکیک اپیستمیک | selfimprove · hypnosis · crypto · accounting | 2026-07-04 |
| P6 | **Backpressure (تولید > ظرفیتِ مصرف)** — وقتی نرخِ تولید از ظرفیتِ داوری/پیگیری جلو زد، flow-control لازم است (admission-control + WIP-cap + سیگنالِ congestion)، نه صرفِ dedup | selfimprove · lead (لید > ظرفیتِ پیگیری) · crypto (داده > ظرفیتِ تصمیم) | 2026-07-04 |
| P7 | **حلقه را با واقعیتِ بیرون ببند** — خودبهبودی بدونِ لنگرِ برون‌زا فرومی‌پاشد (model-collapse/MAD): هم ورودیِ خارجیِ غیرِخودی لازم است، هم بازخوردِ پیامدِ *واقعی* (credit-assignment)، نه خودارزیابیِ باطنی | selfimprove · philosophy · lead (تبدیلِ واقعیِ لید→کار) · crypto (P&Lِ تحقق‌یافته) | 2026-07-04 |
| P8 | **liveness-gated commitment / death-watch** — قبل از خرجِ منابع، زنده/متصل‌بودنِ هدف را چک کن؛ روی جدایی fail-closed شو (نه waitِ کور روی مُرده/گیرکرده) | mining (۵۳٪ کوینِ مرده→chain-liveness) · selfimprove/safety (Anoikis/Apoptosis/Stall-watchdog) · orchestration | 2026-07-04 |
| P9 | **reveal-via-structure** — حالت/تابعِ یک یادگیرنده از پاسخِ ساختاری‌اش خواندنی است، بی‌نیاز از درون‌نگری یا بازخوانیِ کاملِ تاریخچه؛ «اثر را ممیزی کن، نه ورودی را» (primitiveِ ارزانِ پایش) | science (هسیانِ شبکهٔ مقاومت) · mycelium (دیفِ held-vs-served بروکر) · selfimprove (رسیدِ 1206 · شاهدِ 1238) · crypto (متریکِ on-chain = اثرِ رژیم) | 2026-07-05 |
| P10 | **استقلالِ مؤثر بر تعدادِ خام (`n_eff` نه `n`)** — تنوع/تعدادِ خام اطمینانِ کاذب می‌دهد؛ تعدادِ مستقلِ مؤثر را بشمار. مکملِ P7 (P7=لنگرِ بیرونی لازم است · P10=استقلالِ لنگرها را بسنج) | selfimprove (Ne-monitor/n_eff/refractory 1259/1312/1329) · mycelium (چند منبعِ مستقل، نه یک مادر) · learning (تنوعِ ساده‌لوحانه معکوس می‌شود؛ interleaving برای حفظِ تکی g منفی) | 2026-07-05 |
| P11 | **پرتابِ باریکِ ظرفیت‌محور** — پهنای کانال را با ظرفیتِ فعلی جور کن؛ اقتصادِ واحد را روی یک کانال بسنج، بعد پهن کن. مکملِ P6 (P6=flow-controlِ مصرف · P11=دیسیپلینِ اکتساب) | ziman (تک‌کانال/SKUِ قهرمان/فروشگاه معوق) · lead (segment discovery/قاعدهٔ ۲۰٪) · mining (mine-to-hold) · selfimprove (متاگیتِ MVTِ 1321) | 2026-07-05 |
| P12 | **ریسکِ زنجیرهٔ‌تأمینِ MCP بزرگ‌تر از کیفیتِ تک‌سرور است** — تعدادِ کانکتورِ متصل خودش ریسک را ضرب می‌کند (Unit42: ۵ سرور → ۷۸٪ نرخِ موفقیتِ حمله با یکی آلوده)؛ گاردِ نرمِ پرامپتی («فقط بنویس در X») باید به‌سمتِ enforcement فنی (allowlist در کد، hash-pin تعریفِ tool) میل کند. سه منبعِ مستقل هم‌زمان به این رسیدند (security/tools/ai-watch) — n_eff بالا برای این الگو | security · tools · ai-watch · architect (کلِ زیرساختِ MCP همین vault) | 2026-07-06 |
| P13 | **کالیبراسیونِ عددی به‌جایِ سطلِ اطمینان** — احتمالِ دقیق در [0,1] + امتیازِ Brier (نمرهٔ کاملاً proper) بهتر از برچسبِ «بالا/متوسط/پایین» می‌سنجد؛ حجمِ تکرار (نه فقط تصمیم‌های نادرِ پرمخاطره) کالیبراسیون می‌سازد. بسطِ مستقیمِ P5 (verified≠speculative) به بتِ واقعی، نه فقط ادعای دیجست | crypto (خروج) · mining (انتخابِ کوین) · selfimprove/fleet-selection (نمرهٔ عینیِ یافتهٔ promote-شده) · philosophy | 2026-07-06 |

## ۲.۵ کانکشن‌های محتوایی گراندد (از خواندن عمیقِ تمام نالج + پروژه‌ها، 2026-07-04)

> نقشهٔ canonical انسانی: [[04 - Architect System/architect/02-Research/Report - Vault Relationship Map 2026-07-04 v3|Vault Relationship Map v3]]. این بخش لایهٔ محتوایی است (نه حدسی — با استناد نوت).

| # | کانکشن واقعی | مدرک (نوت) | چرا مهم |
|---|---|---|---|
| C1 | **ستون فقرات مشترک: Anchor Ledger/langar** — «سه ناوردا» (تأیید انسانی + سقف‌خرج/kill-switch + آدیت hash-chain) در Crypto، Lead/Brushline، Ziman control-brain و architect **یکسان** پیاده شده | `CRYPTO_ARCHITECTURE_v1` · Brushline `ARCHITECTURE_MASTER §1` · Ziman `safety.py` · `ARCHITECT_CHARTER` | کل vault یک سیستم است، نه ۸ جزیره |
| C2 | **گلوگاه SPOF#1: چرخش کلیدها** — تا ۴ ردیف CRITICAL باز است، autonomy همهٔ ایجنت‌ها read-only (charter §2). یک اقدام آری → کل اکوسیستم باز | `ROTATION_CHECKLIST` (in-degree ۲۶) · هر PROJECT.md §Security Gate | بالاترین‌اهرم کل سیستم |
| C3 | **هیپنوتیزم → دیسیپلین ترید Crypto** — `spacing_x_expectancy_protocol` صریحاً روی node‌های P2/P3/P5 (expectancy/trait) ساخته؛ HRV self-regulation ↔ ترید از طریق 00-Orchestrator | `Crypto/spacing_x_expectancy_protocol` (⚠️ misfiled) · `Neuro-HRV/01-master-prompt` | دانش شخصی مستقیماً به درآمد وصل است |
| C4 | **Mining + Crypto = یک ناوگان فیزیکی واحد** — نوت‌های L7/L3 کریپتو مستقیماً کد بات Mining را ویرایش می‌کنند؛ همان ۱۶× OPi5 Pro هم ماین (energy edge) هم اسکات (crypto signal) | `Crypto/L7_FLEET_DESIGN` + `L3_patches/APPLY_L3_PATCHES` → `Mining/02-Code/Ai bots/` | دو پروژه، یک سخت‌افزار |
| C5 | **Accounting = هابِ درآمد** — همهٔ پروژه‌ها مالیاتشان به اینجا می‌ریزد (Crypto CGT، Mining business-income، Lead GST، Ziman COGS، Project-F creator-income؛ ترتیب D-26) | `Accounting/Ecosystem-Rollout-Plan §2` · `Tax Map FY2025-26` | گره اتصال همهٔ درآمدها |
| C6 | **بودجهٔ AU$30 (D-25) یک قیدِ مشترک** — data-stack کریپتو، هزینهٔ Accounting، همهٔ بات‌ها زیر یک سقف | `Report Data Stack under AU30` · `AGENT_REGISTRY:29` · `ARCHITECT_CHARTER` | یک تصمیم، سقفِ همه |
| C7 | **متدِ مشترک: آزمایشِ پیش‌ثبت زیر قید** — Ziman D4 (سقف ظرفیت) · Lead «یک آزمایش، segment=[To measure]» · Project-F گیت‌های عددی G0–G5 | `Ziman capacity.py` · `Lead Pipeline & Experiments` · `Project-F architecture-blueprint` | همان دیسیپلین علمی در ۳ پروژه |
| C8 | **New Thought/Cardew (نالج) → برندسازی** — پژوهش «expectancy/belief-framing» تاریخیِ سیدنی، ریشهٔ اهرمِ بازاریابیِ Ziman/Lead/Project-F | `Report - Cardew` · P2b (`nodes/`) | دانش تاریخی → کپی مارکتینگ |
| C9 | **گپ: Projects→Knowledge ≈ ۰** — درس‌های پروژه‌ها هرگز به دانش ماندگار تبدیل نمی‌شوند (جریان یک‌طرفه) | Vault Map v3 §flow asymmetry | فرصت: حلقهٔ بازخورد دانش |
| C10 | **SPOF#2: صف verdict آری** — ۳ فایل proposal + ۶ دلتای adversarial + ~۱۶ آیتم Inbox، همه سریالی روی یک انسان | Vault Map v3 M17 | دومین گلوگاه انسانی |

**یافته‌های اقدام‌پذیر (proposal، verdict آری):** (الف) `spacing_x_expectancy_protocol` محتوایش هیپنوتیزم است ولی در پوشهٔ Crypto و از PROJECT.md کریپتو لینک شده → انتقال به `07 - Knowledge`. (ب) عدد ظرفیت Ziman در کد=۳۰ ولی PROJECT.md «ثبت‌نشده» می‌گوید — تناقض. (ج) نشت نام پارتنر خارج از Project-F در ۴ فایل (نقض charter §6). (د) `.env` داخل vault در `کاریابی/bot/`. → همه در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] برای آری.

## ۲.۶ اصلاحاتِ اپیستمیک (append-only — متنِ §۱ بازنویسی نمی‌شود، verdict آری می‌خواهد)

> این بخش الگو/استعارهٔ زیستیِ **قبلاً ثبت‌شده** را که بعداً debunk/contested شد، بدونِ حذفِ متنِ اصلی *پرچم* می‌کند (طبق لیستِ سیاهِ §۴ منشور: اصلاحِ نوتِ canonical = verdict آری). ورودیِ گیتِ [[00 - Inbox/scout-digests/2026-07-05 1225 selfimprove|Biomimicry Provenance Gate 1225]].

| # | ادعای اصلی (کجا) | وضعیتِ واقعیِ مکانیزم | تصحیح | مدرک |
|---|---|---|---|---|
| E1 | «mother-tree عمداً به خویشاوند تغذیه می‌کند» (§۱ هاب‌ها، «طبق درسِ mother-tree حافظه/کانتکست را هدایت می‌کنند» — PUSH) | **debunked** — صفر پشتوانهٔ peer-reviewed برای provisioningِ عمدیِ خویشاوند؛ بروکرِ قارچی خودمنفعت (می‌تواند احتکار کند) | 