---
type: strategy
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[MASTER-BUILD-2026-07-04]]"
  - "[[Feet-Content-Business-Master-Playbook]]"
  - "[[THREAD-CLOSURE-D-2026-07-10]]"
  - "[[DECISION-MATRIX-M2-2026-07-10]]"
  - "[[STATE-REPORT-2026-07-05]]"
  - "[[00 - Control/SOURCE-OF-TRUTH-MATRIX]]"
  - "[[OpenQuestions]]"
  - "[[CLAUDE]]"
tags: [project-f, strategy, reconcile, source-of-truth, conflict-map]
aliases: ["Strategy Reconcile", "Master Reconcile 2026-07-12", "دو-master reconcile"]
---

# STRATEGY-RECONCILE — دو سند master متعارض (Project-F · 2026-07-12)

> **این نوت فقط نقشه است، نه verdict.** برای هر تعارض، هر دو موضع را با منبع/خط نشان می‌دهد و فقط **مسیرِ حل** پیشنهاد می‌کند؛ برندهٔ نهایی را مالک انتخاب می‌کند. مطابق [[00 - Control/SOURCE-OF-TRUTH-MATRIX]] §۴ (خط ۷۲): تا verdict، **هیچ سندی سند دیگر را overwrite نکند**.
> نام‌ها: **A = اپراتور** (ops/tech/marketing/finance) · **C = کریتور/پارتنر** (تولید محتوا). هیچ نام واقعی، handle، یا شهر به‌عنوان fact در این نوت echo نمی‌شود؛ توکن‌های «Sydney»/«Persian» فقط جایی نقل می‌شوند که موضوعِ خودِ تعارض‌اند (قاعدهٔ #۶).

---

## §۰ — چرا این نوت لازم است

دو فایل هم‌زمان خود را «master» می‌دانند و تاریخشان یکی است (2026-07-04):

- `MASTER-BUILD-2026-07-04.md` — سند اجرایِ ۲۰-بخشی، «کالیبراسیون واقع‌بینانه»، ستون‌فقراتِ اعداد محافظه‌کارانه.
- `Feet-Content-Business-Master-Playbook.md` — «Master Playbook»، ۲۰ بخش موازی، بانک تاکتیک/کپی/تقویم.

`STATE-REPORT-2026-07-05.md §۶` (خطوط ۱۲۳–۱۳۴) این را ۹ تعارضِ نسخه‌ای فهرست کرده و `CLAUDE.md §۶` (خط ۹۳) و `SOURCE-OF-TRUTH-MATRIX §۴` (خط ۷۲) همان مجموعه را «تصمیم مالک، نه فایل» تگ زده‌اند. `[FACT — اسناد]` این نوت آن‌ها را به شش سطرِ تصمیم‌پذیر جمع می‌کند و برای هرکدام یک **PATH** می‌دهد.

**قاعدهٔ حاکم بر خودِ این reconcile** (از `CLAUDE.md §۵` خط ۸۷ و قانون اساسی بند ۳): قواعد قفل‌شده با هیچ سند بیرونی/masterای overwrite نمی‌شوند؛ تعارض فقط flag می‌شود.

---

## §۱ — ماتریس تعارض‌ها (هستهٔ نوت)

> هر سطر: موضوع | موضع MASTER-BUILD (منبع) | موضع Playbook/دیگر (منبع) | متمایلِ THREAD-CLOSURE/DECISION-MATRIX | PATHِ پیشنهادی (نه verdict).
> تگ‌ها: مواضع = `[FACT — سند]`؛ «متمایل» = `[proposal]`؛ PATH = `[SPEC]/[OPINION]` (پیشنهاد ایجنت).

| # | موضوع | موضع MASTER-BUILD (منبع/خط) | موضع Playbook / سند دیگر (منبع/خط) | متمایلِ THREAD-CLOSURE / DECISION-MATRIX | PATHِ پیشنهادی (تصمیم با مالک) |
|---|---|---|---|---|---|
| R0 | **precedence بین دو master** | خود را «۲۰-بخشی واقع‌بینانه» می‌داند؛ `MONETIZATION-EXPANSION` فیلد `extends:` را به MASTER-BUILD اشاره داده نه Playbook → در گراف وابستگی، spine (STATE-REPORT §۶ خط ۱۳۴) | Playbook هم عنوان «Master» دارد و ۲۰ بخشِ موازیِ کامل (تقویم/۱۰۰ ایده/۵۰ کپشن/DM) — از نظر پوششِ تاکتیکی غنی‌تر | SOURCE-OF-TRUTH §۴ (خط ۷۲): هر دو نسخهٔ root کانونی‌اند در برابر آینه‌های `docs/`؛ اما تعارضِ محتوایی «owner decision». STATE-REPORT §۶ خط ۱۳۴ به‌سمت MASTER-BUILD (extends-pointer) | یکی را «canonical master (spine)» اعلام کن، دیگری را به **supplement/appendix** تنزل بده (انتقال، نه حذف — قانون اساسی). چون سه سند پایین‌دست (MONETIZATION-EXPANSION، architecture-blueprint، ACQUISITION-ENGINE) به MASTER-BUILD و اعداد محافظه‌کارانه‌اش گره خورده‌اند، مسیرِ کم‌اصطکاک: **MASTER-BUILD = spine، Playbook = بانک تاکتیک/کپی**؛ سطرهای R1–R4 پایین ابتدا حل شوند تا merge بی‌تناقض شود `[SPEC]` |
| R1 | **نردبان قیمت (۳ نسخه)** | First Steps **$6–8** · Themed **$10–15** · Sensory clip **$12–18** · Vault bundle **$29–39** · Custom photo از **$30** (+$5/عکس) · Custom video **$10/دقیقه، min $30** · **Monthly VIP $35/mo** (خطوط ۱۰۳–۱۱۲؛ VIP خط ۱۰۹) | **Playbook §۴.۱** (خطوط ۱۹۴–۲۰۰): Starter **$6** · Themed **$12** · Premium Bundle **$30** · Custom photo **$20–40** · Custom video **$50–100** · **VIP $20/mo**. — **نسخهٔ سوم = EXT-04** (`external-research-2026-07-05/04-onlyfans-funnel.md §۵/§۹۴`): ورودی **$3–5 / $8–15 / $15–30**، custom **$25+**، **بدون VIP در ۹۰ روز اول**، ماه اول بدون promo | **EXT-04**. THREAD-CLOSURE V4 (خط ۴۵) + DECISION-MATRIX E1 (خط ۲۶) و §۶ changelog (خط ۱۱۷): «تصویب EXT-04؛ VIP **منجمد نه حذف** تا G2»؛ round2: «فقط free-page می‌تواند timeline را price-lock کند» → OpenQuestions #۱۰ (خط ۲۳) آمادهٔ بستن | **قبل از seed کردن Fable5 DB4 (Offers & Pricing) یک نردبان واحد قفل شود.** مسیر: EXT-04 به‌عنوان baseline + VIP منجمد تا G2 + شرط شکستِ ثبت‌شده (اگر unlock<۵٪ پایدار → تست paid $4.99). قیمت hard-gated است (RISK-LADDER: «پیشنهاد قیمت» = 🟠 ORANGE) → **verdict A**. draft اجرایی: [[drafts-awaiting-gate/ppv-ladder]] `[SPEC]` |
| R2 | **نام برند (کاندید Anar Soles)** | شورت‌لیست §۳: **Anar Soles (#۱)** · The House Red · Yalda Arch (خطوط ۶۶–۷۷)؛ خط ۴۳۵: «برند پیشنهادی: Anar Soles (رزرو: The House Red)» | **Playbook §۳.۳**: **Arch & Amber** «پیشنهاد اصلی» (خط ۱۵۲) + Sunlit Soles / Harbour Soles / **Softly Sydney** (خطوط ۱۴۱/۱۴۸) — چند نامِ **شهر-محور** | **Anar Soles**. THREAD-CLOSURE §۷ (خط ۹۵) + DECISION-MATRIX + 12-prelaunch: Anar Soles **صفر collision**، Yalda Arch آزاد (رزرو)، Arch & Amber همسایهٔ `amberarch.com`. OpenQuestions #۶ (خط ۱۹): Anar Soles پیشنهاد، «تصمیم دونفره» | **تصمیم دونفرهٔ C+A** (برند = هویت مشترک) + چک نهاییِ handle در لحظهٔ ساخت اکانت (اکشن 🔴 RED، پشت GATE 0) + جستجوی دستی IP Australia. ⚠️ نام‌های شهر-محورِ Playbook (Softly Sydney/Harbour Soles) تا حل #۹ **کاندید نیستند** (به R3 ارجاع) `[SPEC]` |
| R3 | **«Persian/Sydney» در کپی عمومی — تعارض داخلیِ Playbook vs قاعدهٔ قفل‌شدهٔ #۶** | **منطبق با #۶.** هدر MASTER-BUILD صراحتاً «override معمارانه» ثبت کرده: «اشاره ملایم به Sydney» → «**Aussie** سطح کشور»، دلیل: «هیچ فکت جغرافیایی شهری» (خطوط ۱۱–۱۴)؛ USP «sunlit **Australia**» (خط ۶۱) | **متعارض با #۶.** Playbook توکنِ شهری را در سراسر کپی دارد: «لوکیشن برند: Sydney, NSW» (خط ۱۴)، bioها «natural **Sydney** light» / «sunny **Sydney** home» (خطوط ۱۷۷–۱۷۹، ۲۶۷). تحقیق بیرونی (13-external-integration) هم Persian/Sydney را توصیه می‌کند ولی خودش ریسک شناسایی را flag کرده | THREAD-CLOSURE این را **reconcile نکرد** (خارج از سه‌گانهٔ T7). DECISION-MATRIX P11 «افشای شهر / هدف‌گیری ایران» را prohibited و BanRisk=۱۰ می‌داند (خط ۸۲) اما توکن «Sydney» در کپیِ برند سیگنالِ نرم‌تری است. OpenQuestions #۹ (خط ۲۲): **[OPEN — P0-opsec]** | **این سطر متقارن نیست.** قاعدهٔ قفل‌شدهٔ #۶ (`CLAUDE.md` خط ۳۱: توکن‌های «Persian»/«Sydney» ممنوع، فرهنگ فارسی فقط بصری) تا **verdict انسانیِ صریح روی #۹** حاکم است. پس default اجرایی = نسخهٔ منطبقِ MASTER-BUILD («Aussie»)؛ همهٔ رشته‌های «Sydney» در کپیِ Playbook قبل از هر استفاده به «Aussie» نرمالایز شوند. مالک فقط با تصمیم روی #۹ می‌تواند #۶ را تعدیل کند — که آن‌گاه = تغییر قاعدهٔ قفل‌شده = 🔴 RED (RISK-LADDER) `[SPEC]` |
| R4 | **نقش Fansly (mirror vs هم‌وزن)** | «Fansly **موازی از روز اول**» `[High]` (خط ۴۱، ذیل کاهش ریسک تلاطم سیاست OF) — عملاً نزدیک به parallel/equal | **Playbook §۸.۳** (خطوط ۳۴۸/۳۶۲): **mirror** محتوای OF (۸۰/۲۰)، «اولویت پایین‌تر تا validate». ↔ **MONETIZATION-EXPANSION M1** (خط ۵۲): «**هم‌وزن OF از روز ۱**» + multi-tier Fansly (§۱۱۱) | «**mirror با تنظیم discovery-first**». THREAD-CLOSURE §۷ (خط ۹۷): تولید یک‌بار (هزینهٔ mirror) اما زمان‌بندی Fansly مستقل و native-first برای FYP؛ بازوزن‌دهی با دادهٔ G1. fresh-scan: «Fansly پلتفرم دوم قطعی». OpenQuestions #۸ (خط ۲۱): verdict معلق | **verdict A روی سه‌گانه:** (الف) mirror خالص [Playbook] · (ب) هم‌وزن روز-۱ [MONETIZATION] · (ج) میانهٔ THREAD-CLOSURE. مسیر پیشنهادی: **(ج)** به‌عنوان default کم‌هزینه، با نقطهٔ بازبینی در **G1** (اگر Fansly-native discovery سهم معنادار داد → ارتقا به هم‌وزن)؛ تصمیم multi-tier Fansly به Experiment Log ماه ۲ موکول (MONETIZATION §۲۵۵) `[SPEC]` |
| R5 | **ساعت هفتگیِ پارتنر (۳۰h vs ~۳h) — عملاً بسته** | C «**۳–۵ ساعت/هفته**» `[ASSUMED]` (خط ۱۳)؛ architecture-blueprint همین رقمِ محافظه‌کارانه | **project-master-reference.md** خط ۳۴: «**~۳۰ ساعت/هفته**» برچسبِ `[FACT]` (تک‌منبعِ single-source-of-truthِ قدیمی). Playbook رقم مستقیمِ پارتنر ندارد اما routine روزانه ۴۵–۶۰د (خط ۵۴۰) + «فروشندهٔ فعال ۱۰–۱۵h/هفته» (خط ۵۱) بارِ سنگین‌تری فرض می‌کند | **~۳h/هفته ADOPTED.** THREAD-CLOSURE §۰.۹ (خط ۲۳) + §۷ (خط ۹۸): با ورودی صریح انسانیِ A در ۲۰۲۶-۰۷-۱۰؛ OpenQuestions #۴ (خط ۱۷) **CLOSED**؛ M3 با اصلاحیهٔ **M3-a** (شکستن شوت ۴–۶h به دو جلسهٔ ≤۲.۵h) سازگار شد | **تنها تعارضی که ورودی انسانی از قبل بسته.** مسیر: هر پلن پایین‌دست که هنوز ۳۰h را فرض می‌کند (batch-plan سنگینِ MASTER-BUILD خط ۴۲۹، cadence روزانهٔ Playbook) به سقف **~۳h/هفتهٔ C** کالیبره شود؛ Effortِ ردیف‌های B3/E2 در DECISION-MATRIX به این حساس است (§۵ خط ۱۱۱). `project-master-reference.md` که ۳۰h را `[FACT]` زده در merge اصلاح شود (single-source-of-truthِ stale). عملاً: **closed pending owner ratification در DecisionLog** `[SPEC]` |

---

## §۲ — نکتهٔ عرضی: چرا R3 با بقیه فرق دارد

پنج سطرِ R0/R1/R2/R4/R5 تعارض‌های **متقارن** بین اسنادِ هم‌رتبه‌اند؛ مالک آزادانه انتخاب می‌کند. اما R3 (Persian/Sydney) **نامتقارن** است: یک طرفِ آن قاعدهٔ قفل‌شدهٔ #۶ است. طبق قانون اساسیِ vault و `CLAUDE.md §۱`، قاعدهٔ قفل‌شده با هیچ سندِ دیگری (حتی master یا تحقیق بیرونی) قابل overwrite نیست. بنابراین در R3، «موضع Playbook» یک **نقصِ انطباق برای flag‌کردن** است، نه یک موضعِ رقیبِ مشروع. تا verdictِ #۹، نسخهٔ منطبقِ MASTER-BUILD («Aussie») default است و باید هر استفادهٔ زندهٔ توکنِ شهری مسدود بماند. `[FACT — CLAUDE.md خط ۳۱ + قانون اساسی بند ۱–۲]`

---

## §۳ — پیشنهادِ precedence (هرمِ حل تعارض)

مبنا: `CLAUDE.md §۳` خط ۶۲ («قواعد قفل‌شده > ACQUISITION-ENGINE (برای جذب) > بقیه») + `SOURCE-OF-TRUTH §۴`. این هرم را به‌عنوان قاعدهٔ رسمیِ حلِ تعارض پیشنهاد می‌کنم — خودش هم `[proposal]` و نیازمند تأیید مالک:

1. **قواعد قفل‌شده** (`CLAUDE.md §۱`، هشت‌گانه) — بالاترین اقتدار. هیچ سندی overwrite نمی‌کند؛ تغییرشان = 🔴 RED + verdict انسانیِ صریح. → حاکم بر R3، و بر هر سطری که به opsec/privacy/ToS برخورد کند.
2. **ACQUISITION-ENGINE-2026-07-05.md** (نسخهٔ root، canonical per SOURCE-OF-TRUTH §۱) — **فقط در حوزهٔ جذب/acquisition**. وقتی master و ACQUISITION-ENGINE دربارهٔ تاکتیکِ جذب اختلاف دارند، ACQUISITION-ENGINE برنده است (تازه‌تر + هم‌راستا با سبد Do-Now در DECISION-MATRIX §۲).
3. **reconciled master** (پس از verdictِ R0) — برای بقیهٔ حوزه‌ها: offer/pricing (R1)، brand (R2)، Fansly (R4)، cadence/hours (R5)، تقویم، roadmap.

> پانوشت الزام‌آور تا reconcile: هیچ‌کدام از دو master دیگری را overwrite نکند (`SOURCE-OF-TRUTH §۴` خط ۷۲). این نوت **map** است، نه verdict؛ PLAN ≠ APPROVAL ≠ EXECUTION.

---

## §۴ — نگاشتِ «چه چیزی از مالک لازم است» (handoff)

| سطر | تصمیمِ لازم | صفِ متناظر | وضعیت فعلی |
|---|---|---|---|
| R0 | کدام master = spine؟ (پیشنهاد: MASTER-BUILD؛ Playbook → appendix) | THREAD-CLOSURE §۹ (کلانِ reconcile) | open |
| R1 | قفلِ نردبان واحد (پیشنهاد: EXT-04 + VIP منجمد تا G2) | THREAD-CLOSURE §۹ بند ۵ · [[drafts-awaiting-gate/ppv-ladder]] | open (قیمت = 🟠) |
| R2 | نام برند (پیشنهاد: Anar Soles + رزرو Yalda Arch) | THREAD-CLOSURE §۹ بند ۶ · OpenQuestions #۶ | open (دونفره) |
| R3 | حل #۹ (Persian/Sydney) — تا آن، #۶ حاکم | OpenQuestions #۹ [P0-opsec] | open (default = «Aussie») |
| R4 | نقش Fansly (پیشنهاد: mirror-but-discovery-first) | THREAD-CLOSURE §۹ بند ۷ · OpenQuestions #۸ | open |
| R5 | تصدیقِ رسمیِ ~۳h در DecisionLog + کالیبره‌کردن پلن‌های پایین‌دست | OpenQuestions #۴ | closed (ورودی انسانی) — منتظر ratify |

**Cross-links:** [[00 - Control/SOURCE-OF-TRUTH-MATRIX]] (کدام فایل کانونی) · [[OpenQuestions]] (#۴/#۶/#۸/#۹/#۱۰) · [[THREAD-CLOSURE-D-2026-07-10]] §۷/§۹ (صفِ verdict) · [[DECISION-MATRIX-M2-2026-07-10]] (E1/§۶ changelog) · [[VERDICT_QUEUE]] (PF-V*).

---

## §۵ — Sources (فایل/خطِ استنادشده)

- `MASTER-BUILD-2026-07-04.md` — brand §۳ (خطوط ۶۶–۷۷، ۴۳۵) · pricing §۴ (خطوط ۱۰۰–۱۱۲؛ VIP خط ۱۰۹) · hours (خط ۱۳) · Fansly parallel (خط ۴۱) · opsec override هدر (خطوط ۱۱–۱۴) · USP (خط ۶۱).
- `Feet-Content-Business-Master-Playbook.md` — brand §۳.۳ (خطوط ۱۴۰/۱۴۸/۱۵۲) · pricing §۴.۱ (خطوط ۱۹۴–۲۰۰) · Fansly §۸.۳ (خطوط ۳۴۸/۳۶۲) · Sydney bios (خطوط ۱۴، ۱۷۷–۱۷۹، ۲۶۷) · routine/hours (خطوط ۵۱، ۵۴۰).
- `THREAD-CLOSURE-D-2026-07-10.md` — §۰.۹ (خط ۲۳) · §۲/V4 (خط ۴۵) · §۷ (خطوط ۹۲–۹۸) · §۹ (خطوط ۱۰۴–۱۱۴).
- `DECISION-MATRIX-M2-2026-07-10.md` — E1 (خط ۲۶) · §۵ (خط ۱۱۱) · §۶ changelog (خطوط ۱۱۶–۱۱۷) · P11 (خط ۸۲).
- `STATE-REPORT-2026-07-05.md` §۶ — جدول ۹-تعارض (خطوط ۱۲۳–۱۳۴؛ hours خط ۱۲۶، brand خط ۱۲۷، pricing خط ۱۲۸، Fansly خط ۱۲۹، extends-pointer خط ۱۳۴).
- `project-master-reference.md` خط ۳۴ (~۳۰h `[FACT]`) · `MONETIZATION-EXPANSION-2026-07-04.md` خط ۵۲ (Fansly هم‌وزن) + §۱۱۱/§۲۵۵ (multi-tier).
- `external-research-2026-07-05/04-onlyfans-funnel.md` §۵/§۹۴ (EXT-04 ladder، بدون VIP ۹۰ روز).
- `CLAUDE.md` §۱ قاعدهٔ #۶ (خط ۳۱) · §۳ precedence (خط ۶۲) · §۶ (خط ۹۳).
- `00 - Control/SOURCE-OF-TRUTH-MATRIX.md` §۱/§۴ (خطوط ۳۲، ۷۲) · `00 - Control/RISK-LADDER.md` (سطوح ORANGE/RED) · `OpenQuestions.md` (#۴/#۶/#۸/#۹/#۱۰).

---

*Verification: هر موضع مقابل فایل منبع و شمارهٔ خط cross-check شد. هیچ قاعدهٔ قفل‌شده لمس/تعدیل نشد؛ هیچ hard-gated adopted نشد؛ هیچ برنده‌ای انتخاب نشد جز آنچه ورودیِ انسانیِ قبلی (R5) بسته بود. این سند proposal است (status: idea) و پشت GATE 0 + صفِ verdict می‌ایستد.*
