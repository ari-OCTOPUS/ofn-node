---
type: proposal
status: proposal            # propose-only — پرامپتِ ساخت. اجرای هر فاز فقط با verdict آری.
role: Researcher-Designer   # منشور §۱: طراحی/پیشنهاد؛ اعمال هرگز بدون verdict
created: 2026-07-06
verdict: pending-آری
scope: پرامپتِ پنج‌گانهٔ ساختِ دو ایجنتِ ژنوم‌نشین — «نگهبانِ همیشه‌روشن» + «جعبه‌سیاهِ خلاقیت»
depends_on: "[[2026-07-06 RESEARCH-GENOME-RECONCILIATION-proposal]] (قانونِ ژنوم: read-only، propose→approve، whitelist، ledger)"
tags: [penta-prompt, governor, muse, creativity-blackbox, evolutionary-doctor, propose-only]
---

# پرامپتِ پنج‌گانه — GOVERNOR + MUSE (جعبه‌سیاهِ خلاقیت)

> **این سند یک پرامپت است، نه اجرا.** پنج فاز = پنج بلوکِ کپی‌پیست‌شدنی برای ایجنتِ کدنویست (Codex / Claude Desktop). هر فاز propose-only است و فقط بعد از verdict آری روی فازِ قبلی اجرا می‌شود. هیچ فایلی این‌جا تغییر نکرد.

---

## ۰. طرزِ استفاده

1. فاز ۱ را به ایجنتِ کدنویس بده → خروجی = **دیفِ پیشنهادی** (نه اعمال). آری verdict می‌دهد.
2. بعد از verdict، فاز بعد. هیچ فاز میان‌بر ندارد (منشور §۱: propose→approve→apply، timeout=DENY).
3. هر فاز خروجی‌اش را با یک ردیفِ ledger (kind=propose) و نوت در `00 - Inbox/build-proposals/` ثبت می‌کند — بدون لمسِ ژنوم.

**سه فرضِ صریح (اگر غلط‌اند، همین‌جا رد کن):**
- **A1 — «داخل ژنوم» یعنی:** *منشورِ* این دو ایجنت ژنوم‌نشین و immutable-برای-ایجنت است، ولی *runtime*شان تحت قانونِ propose-only/read-only اجرا می‌شود. (نه اینکه بتوانند ژنوم را بنویسند.)
- **A2 — «دکتر تکاملی» یک لایهٔ ارزیابیِ جدا است**، نه همان `dashboard_doctor.py`. دکترِ قطعیِ zero-LLM (سلامتِ vault) دست‌نخورده می‌ماند؛ «دکتر تکاملی» ایده‌های MUSE را انتخاب می‌کند.
- **A3 — MUSE همیشه‌روشن نیست**؛ زمان‌بندی‌شده و نادر است (صرفهٔ هزینه + ایمنی). فقط GOVERNOR همیشه‌روشن است.

*(هر سه در §۶ «نقاطِ verdict» قابلِ تغییرند.)*

---

## ۰.۱ آناتومیِ زیستی (هم‌راستا با لنزِ ژنومیِ پروژه — anti-metaphor: هر نقش = یک مکانیزمِ واقعی)

| نقش سیستم | آنالوگِ زیستیِ واقعی | نگاشتِ مهندسی |
|---|---|---|
| **GOVERNOR** (همیشه‌روشن) | هومئوستازی + نظارتِ ایمنی (immune surveillance) | supervisor process (NSSM) · control-plane · invariant-monitor |
| **MUSE** (جعبه‌سیاه) | somatic hypermutation — تولیدِ عمدیِ تنوع در B-cell | generatorِ high-temperature · read-only · sandboxed |
| **دکتر تکاملی** | clonal / negative selection — حذفِ واریانتِ خطرناک/خودواکنش | fitness-filter + safety-gate (فقط forward، نه اجرا) |
| **Ledger** | وراثت / حافظهٔ ژنومی | append-only EXPERIENCE + MUTATION ledger + git |
| **آری (verdict)** | فشارِ انتخابِ نهایی | human-approval gate (منشور §۱) |

منطقِ کلان: **MUSE تنوع می‌سازد (جهش) → دکتر تکاملی انتخاب می‌کند (selection) → آری فشارِ نهایی → Ledger وراثت.** GOVERNOR کلِ ارگانیسم را زنده و در تعادل نگه می‌دارد. این دقیقاً حلقهٔ تکاملی است، با ایمنیِ propose-only.

---

## فاز ۱ — منشورِ دو ایجنت + مرزها (CHARTER & BOUNDARIES)

```text
# ROLE
تو معمارِ ژنومی. خروجی‌ات فقط یک «دیفِ پیشنهادی» به ARCHITECT_CHARTER است — هیچ اعمالی.
# CONTEXT (بخوان قبل از هر کار)
- ARCHITECT_CHARTER.md (منشور — immutable برای ایجنت‌ها)
- learning-engine/MUTATION-WHITELIST.md (مرزِ جهش؛ تک‌whitelistِ معتبر)
- learning-engine/LEARNING-CONTRACT.yaml (قرارداد وابستگی)
- 2026-07-06 RESEARCH-GENOME-RECONCILIATION-proposal.md (قانونِ ژنوم و دریفت‌ها)
# TASK
یک بلوکِ منشورِ جدید (proposal، status: proposal) برای دو ایجنت بنویس:
1) GOVERNOR — «معمارِ همیشه‌روشن / نگهبانِ ژنوم»
2) MUSE — «جعبه‌سیاهِ خلاقیت»
برای هرکدام دقیقاً تعریف کن: identity · allowed · forbidden · autonomy_level · مسیرهای خواندن · مسیرهای نوشتن · کانالِ خروجی.
# قواعدِ سختِ غیرقابل‌مذاکره (از منشورِ موجود ارث می‌برند)
- هر دو ایجنت: autonomy برای «تغییر» = propose-only. صدورِ verdict ممنوع (D-01).
- GOVERNOR: فقط عملیاتِ خواندنی/نظارتی مجاز (restart، heartbeat، احترام به STOP/halted). هیچ تغییرِ کد/قاعده/پروژه بدون verdict.
- MUSE: دسترسیِ read-only به «تمامِ پروژه‌ها»؛ صفر نوشتن؛ خروجی فقط به کانالِ قرنطینهٔ «دکتر تکاملی» — هرگز به پروژه‌ها، هرگز به اجرا.
- ضدِ دستکاریِ evaluator (DEEP-GAP شکاف ۸): هیچ‌کدام نمی‌تواند whitelist · charter · LEARNING-CONTRACT · STATEِ حاکمیتی · یا منشورِ ایجنتِ دیگر را جهش دهد.
- هر دو زیرِ §Security Gate + kill-switch (D-06) + §Budget (منشور §۵) هستند.
- لیستِ سیاهِ human-only دست‌نخورده: secret · پول · پیام خارجی · git · charter.
# OUTPUT (Markdown، propose-only)
1) بلوکِ منشورِ دو ایجنت (جدولِ نقش‌ها به‌سبکِ منشور §۱)
2) دو ردیفِ AGENT_REGISTRY (trigger، autonomy_level، مسیرها)
3) فهرستِ «چه چیزی این فاز تغییر می‌دهد» (باید صفر باشد جز افزودنِ متنِ proposal)
4) نقاطِ verdictِ باز برای آری
# CONSTRAINT
هیچ فایلِ ژنوم/کد را ویرایش نکن. اگر ابهام: حداکثر ۳ سوالِ هدف‌دار، بعد توقف.
```

---

## فاز ۲ — GOVERNOR: معمارِ ۲۴ساعته (CONTROL + UPTIME)

```text
# ROLE
تو معمارِ قابلیت‌اطمینان (reliability/SRE). GOVERNOR را طراحی کن: ایجنتِ همیشه‌روشنی که کلِ ناوگان را
آنلاین، سالم و در-تعادل نگه می‌دارد و فقط «پیشنهاد» می‌دهد — هرگز به‌جای انسان تصمیم نمی‌گیرد.
# CONTEXT
- LAPTOP-RUNTIME.md (NSSM/Task-Scheduler، boot sequence، fail-closed recovery)
- scripts/DOCTOR-BLUEPRINT-v1.md (دکترِ قطعیِ zero-LLM — GOVERNOR آن را صدا می‌زند، جایگزینش نمی‌کند)
- ARCHITECT_CHARTER §۱/§۴/§۵/§۷ (نقش‌ها، kill-switch، بودجه، ماتریسِ تشدید)
# TASK — پنج مسئولیتِ GOVERNOR را کامل اسپک کن
1) UPTIME: سرویسِ همیشه‌روشن با NSSM (Restart=always) + heartbeat؛ احترامِ fail-closed به STOP/halted (D-06).
2) INVARIANT-MONITOR: زمان‌بندیِ اجرای dashboard_doctor + «چکِ genome-diff» (D4 از سندِ تطبیق: هر تغییرِ charter/contract/whitelist بدونِ ردیفِ verdict = CRITICAL).
3) ORCHESTRATION: جمع‌آوریِ وضعیتِ cross-domain + تشدید به تلگرام (نقشِ Chief Orchestrator، منشور §۱). فقط گزارش/پیشنهاد.
4) INTELLIGENCE-TIERING: پیش‌فرض = قطعی/ارزان؛ فراخوانِ LLM فقط در نقاطِ تصمیم (الگوی RouteLLM). هر tier با سقفِ هزینه.
5) COST-CEILING: hard-stop منشور §۵ (AU$30/ماه) + STATE.budget_ceiling_daily ($2) + budget_per_call_ceiling ($0.5) + alertهای ۵۰٪/۸۰٪.
# SAFETY
fail-closed در ابهام · بدونِ صدورِ verdict · بدونِ تغییرِ کد/قاعده · هر اجرای خودکار = ردیفِ Anchor Ledger + نوتیفیکیشنِ تلگرام.
# OUTPUT (propose-only)
پرامپتِ عملیاتیِ GOVERNOR (بلوکِ آماده) · نقشهٔ سیم‌کشیِ runtime (کجای LAPTOP-RUNTIME می‌نشیند) ·
جدولِ intelligence-tier (کار → مدل → سقف) · متریک‌های سلامتِ خودش · نقاطِ verdict.
# CONSTRAINT
proven over novel · بازاستفاده از fusion-mvp/langar به‌جای بازنویسی · بدونِ اعمال · فرض‌ها صریح.
```

---

## فاز ۳ — MUSE: جعبه‌سیاهِ خلاقیت (VARIATION OPERATOR)

```text
# ROLE
تو معمارِ یک موتورِ واگرا (divergent). MUSE را طراحی کن: «جعبه‌سیاهی» که تجربه و خروجیِ ایجنت‌های دیگر را
ترکیب می‌کند و ایده‌هایی در مرزِ «دیوانگی↔نبوغ» می‌سازد — ولی هر ایده را «با ترسِ بی‌نهایت» و کاملاً
غیرِدستوری بیان می‌کند و فقط به دکترِ تکاملی می‌فرستد. MUSE به هیچ‌چیز دست نمی‌زند.
# CONTEXT
- _memory/EXPERIENCE-LEDGER.md + MUTATION-LEDGER.md (مادهٔ خامِ ترکیب)
- خروجیِ ایجنت‌های دیگر (Governor، Researcher، scoutها) = ورودیِ الهام
- منشورِ فاز ۱ (مرزِ read-only و کانالِ قرنطینه)
# TASK — پنج ویژگیِ MUSE را کامل اسپک کن
1) READ-ONLY-ALL: mountِ فقط‌خواندنی به «تمامِ پروژه‌ها» (enforceِ فنی — گِرهِ D4). صفر نوشتن. sandbox = جعبه‌سیاهِ واقعی، بی side-effect.
2) SYNTHESIS: هم‌آمیزیِ cross-domain میانِ ledgerِ تجربه + خروجیِ ایجنت‌ها («ترکیب تجربه و ایجنت‌های دیگر»).
3) DIVERGENCE-DIAL: کاوشِ عمدیِ مرزِ دیوانگی↔نبوغ — دمای بالا، جهش‌های قیاسی (analogical)، انتقالِ بین‌دامنه‌ای. یک «شمارهٔ جسارت» ۱–۱۰ روی هر ایده.
4) FEAR-WRAPPER (اجباری — «با ترسِ بی‌نهایت»): هر ایده باید حمل کند:
   { confidence (پیش‌فرض ~۰) · blast-radius اگر اجرا شود · «چرا ممکن است دیوانگیِ محض باشد» ·
     سلبِ‌مسئولیتِ صریحِ NON-DIRECTIVE · معیارِ کُشتنِ ایده (kill-criteria) }.
5) QUARANTINE-OUT: خروجی فقط در `MUSE-QUARANTINE-LEDGER` (append-only) → مسیردهی به دکترِ تکاملی.
   هرگز به پروژه‌ها، هرگز به اجرا، هرگز verdict. نرخ‌محدود + بودجه‌محدود (نادر؛ مدلِ گران مجاز چون گیت‌شده).
# SAFETY
read-only فنی‌اجباری · صفر side-effect · هر خروجی «speculative» برچسب‌خورده · اگر MUSE چیزی خارج از قرنطینه بنویسد = نقضِ contract → halt.
# OUTPUT (propose-only)
پرامپتِ MUSE (بلوکِ آماده) · schemaی MUSE-QUARANTINE-LEDGER · نمونهٔ یک ایدهٔ کامل با fear-wrapper · نقاطِ verdict.
# CONSTRAINT
جعبه‌سیاه یعنی ایزوله: هیچ مسیرِ نوشتنی جز قرنطینه. اگر ابهام: ۳ سوال، بعد توقف.
```

---

## فاز ۴ — حافظه + هوشمندی + دکترِ تکاملی (MEMORY · INTELLIGENCE · SELECTION)

```text
# ROLE
تو معمارِ حافظه و ارزیابی. سه چیز را به‌هم سیم‌کشی کن: حافظهٔ مشترک، استراتژیِ هوشمندی/مدل، و دکترِ تکاملی.
# TASK
1) MEMORY (append-only، بدونِ overkill):
   - EXPERIENCE-LEDGER + MUTATION-LEDGER + LEARNING-STATE + vault + MUSE-QUARANTINE-LEDGER (جدید).
   - provenance روی هر ردیف (origin + external_data)؛ retention؛ بدونِ vector-DB سروری/Kafka (Q6 تطبیق: overkill).
2) INTELLIGENCE / MODEL-STRATEGY (tierهای صریح + برآوردِ هزینه):
   - دکترِ سلامتِ قطعی = رایگان (zero-LLM) · GOVERNOR = ارزان‌tier · دکترِ تکاملی = میان‌tier · MUSE = high-temp گران ولی نادر.
   - قواعدِ routing (کِی کدام مدل) + سقفِ per-tier + برآوردِ $ ماهانه.
3) EVOLUTIONARY-DOCTOR (لایهٔ انتخاب — جدا از dashboard_doctorِ قطعی):
   - ایده‌های قرنطینهٔ MUSE را نمره می‌دهد: { هم‌راستایی-با-charter · شواهد/امکان‌پذیری · blast-radius · ROI · برگشت‌پذیری }.
   - فقط «بازمانده‌ها» را به‌صورت propose-only به آری forward می‌کند. خودش هرگز اجرا نمی‌کند.
   - رابطه‌اش با dashboard_doctor را صریح کن: آن = سلامتِ ساختار (قطعی)؛ این = انتخابِ ایده (ارزیابی).
4) EVALUATION-FRAMEWORK: متریک‌ها (نرخِ بقای ایده، false-positive خلاقیت، هزینه/ایدهٔ پذیرفته، زمانِ قرنطینه→verdict).
# OUTPUT (propose-only)
schemaی حافظه · جدولِ model-tier + هزینه · rubricِ نمره‌دهیِ دکترِ تکاملی · فهرستِ متریک‌ها · نقاطِ verdict.
# CONSTRAINT
دکتر فقط forward می‌کند، اجرا نه. حافظه append-only. هزینه‌ها «برآورد» برچسب بخورند، نه قطعی.
```

---

## فاز ۵ — بک‌اپ + بازیابیِ فاجعه + بقایِ همیشه‌روشن (BACKUP · DR · INTERLOCKS)

```text
# ROLE
تو معمارِ بقا/DR. کاری کن «تمامِ حافظه و هوشمندی و بک‌اپ» لحاظ شده باشد و حلقهٔ همیشه‌روشن + خلاقیت هرگز از کنترل خارج نشود.
# CONTEXT
- LAPTOP-RUNTIME §۶/§۸ (کلاس‌های شکست؛ بک‌اپِ off-box = بزرگ‌ترین حفره، BACKLOG-10)
- ARCHITECT_CHARTER §۴/§۵ (kill-switch، بودجه، خط فاجعهٔ $500)
# TASK
1) OFF-BOX BACKUP (پرکردنِ حفره): rclone به off-box · رمزنگاری‌شده · زمان‌بندی‌شده · + «تمرینِ restore» (بک‌اپِ تست‌نشده = بک‌اپِ نداشته).
2) STATE-DURABILITY: SQLite WAL + pickle + ledger + git؛ recovery = چکِ fail-closedِ kill-switch در boot (LAPTOP-RUNTIME §۴).
3) ALWAYS-ON: GOVERNOR با NSSM Restart=always؛ MUSE فقط on-demand/نادر (نه always-on — صرفه + ایمنی).
4) RUNAWAY-INTERLOCKS: hard-stop AU$30/ماه + خط فاجعهٔ $500 (منشور §۵) · فایلِ STOP · propose→approve · ۱ جهش/روز · rollback بعدِ ۲ خطا.
   ثابت کن حلقهٔ [MUSE→دکتر→آری] و GOVERNOR نمی‌توانند self-amplify کنند (هر مسیرِ تقویتِ خودکار را نام ببر و ببند).
5) DR-RUNBOOK: مراحلِ بازیابی بعدِ کرش/از-دست‌رفتنِ دیسک/کلیدِ لو-رفته.
# OUTPUT (propose-only)
طراحیِ backup/DR · چک‌لیستِ interlockها · نقشهٔ «هر کلاسِ شکست → مکانیزم» · نقاطِ verdict.
# CONSTRAINT
همه‌چیز fail-closed. قبل از اعتماد به بک‌اپ، restore را تست کن. بدونِ اعمال.
```

---

## ۶. نقاطِ verdict (فقط آری تصمیم می‌گیرد)

1. **A1 «داخل ژنوم»:** منشورِ دو ایجنت genome-resident و immutable، ولی runtime تحت propose-only/read-only؟ *(توصیه: بله.)*
2. **A2 «دکتر تکاملی»:** یک لایهٔ ارزیابیِ LLMِ جدا (dashboard_doctorِ قطعی دست‌نخورده)؟ یا نقشِ انتخاب را همان `learning-engine-loop` بازی کند؟ *(توصیه: لایهٔ جدا.)*
3. **A3 MUSE:** نادر/زمان‌بندی‌شده (نه always-on)؟ *(توصیه: بله — فقط GOVERNOR همیشه‌روشن.)*
4. **مدل‌ها و بودجه:** هر tier کدام مدل (Haiku/Sonnet/Opus) + سقفِ $ هر کدام؟
5. **پیش‌بردن:** فازها را من به‌صورت پیشنهادِ فایل‌به‌فایل جلو ببرم، یا فعلاً فقط همین پرامپت‌ها را می‌خواستی؟

## ۷. ردیف‌های ledger پیشنهادی (اگر verdict داده شد — kind=propose)

| تاریخ | kind | مبنا | تغییرِ پیشنهادی | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | این سند فاز ۱ | منشورِ GOVERNOR + MUSE (proposal به ARCHITECT_CHARTER) | pending-verdict |
| 2026-07-06 | propose | فاز ۲ | اسپکِ GOVERNORِ همیشه‌روشن + سیم‌کشیِ NSSM | pending-verdict |
| 2026-07-06 | propose | فاز ۳ | اسپکِ MUSE + MUSE-QUARANTINE-LEDGER (read-only enforce) | pending-verdict |
| 2026-07-06 | propose | فاز ۴ | schemaی حافظه + دکترِ تکاملی + model-tiering | pending-verdict |
| 2026-07-06 | propose | فاز ۵ | backup off-box + DR + interlockهای ضدِ runaway | pending-verdict |

---

*این سند فقط پرامپت/پیشنهاد است. هیچ ژنوم/کدی تغییر نکرد. اجرای هر فاز = verdict صریح آری (منشور §۱/§۷).*
