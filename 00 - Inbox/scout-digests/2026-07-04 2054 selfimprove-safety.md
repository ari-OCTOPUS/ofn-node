---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://www.cell.com/fulltext/S0092-8674(94)90277-1
  - https://consensus.app/papers/details/52ea79b898b3546e80796642695d98ed/
  - https://consensus.app/papers/details/0bca9a44d51250baa20cece79047c678/
  - https://consensus.app/papers/details/3921f51ae8c05a8ab375cfa577094e71/
  - https://authzed.com/blog/fail-open
  - https://read.thecoder.cafe/p/fail-open-fail-closed
  - https://app.dosu.dev/3bbfc5b5-a855-41b3-955e-7576fa7a1016/documents/3653a0cf-50fa-427e-862e-53e79cfae97e
  - https://security.systemsapproach.org/principles.html
tags: [research, ai]
created: 2026-07-04
updated: 2026-07-04
salience: 0.9
---

# selfimprove-safety — «Anoikis Gate» (دروازهٔ اتصال): fail-closed وقتی kernelِ ایمنی حاضر/متصل نیست — منطقِ «بدونِ اتصال به بستر → مرگِ برنامه‌ریزی‌شده» (R-01، به‌علاوهٔ R-05)

> لِینِ SAFETY. **PROPOSE-ONLY** — این یک design sketch است، اعمال نشده؛ `_code`/`orchestrator.py`/`client.py`/config/constitution لمس نشد. سطح: kernel-adjacent / fail-closed contract → **HUMAN-APPROVAL-REQUIRED**. verdict نهایی با آری.

**dedup (rotation):** grep روی همهٔ `*selfimprove*` digestهای امروز:
- `anoikis / anchorage / detachment / R-01 / silent fallback / cooperative fallback / ALLOW_COOPERATIVE` به‌عنوان **آیتمِ انتخاب‌شده** → در هیچ digestی نیامده (`anoikis` = صفر فایل؛ `fail-clos` فقط به‌صورتِ *ارجاعِ اصولی* در ۸ digest، نه به‌عنوانِ آیتمِ طراحی‌شده).
- پوششِ خانوادهٔ SAFETY تا کنون: R-02 (اصالتِ منشأِ verdict → [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation 2023]])، R-06+R-07 (گراندینگ/held-out → [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline 2041]])، R-08 (دو-زنجیرهٔ audit → 1655)، R-09 (kill-switch → [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis 1911]])، §4 kappa (→ [[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove|Quorum 1744]])، GAP 8 (→ [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]]).
- **R-01 (fail-closed وقتی IGK حاضر نیست)** تنها آیتمِ **APPROVED-for-next-session** و **رتبهٔ ۱ِ کلِ پلن** است که **صفر پوشش** دارد — و به‌تصریحِ خودِ پلن، قراردادِ fail-closedی که R-05/R-06/R-09 روی آن می‌نشینند. genuinely نو → rotation رعایت شد. anti-overlap: هیچ safety digestی از 2041 به بعد ساخته نشده.

---

## ۱) آیتم و چرا مهم است

**آیتم:** **R-01 — «در دسترس‌نبودنِ IGK باید fail-CLOSED باشد».** امروز وقتی `USE_IGK=True` است ولی kernel نمی‌تواند spawn شود، `orchestrator` به‌صورتِ **خاموش** `self.use_igk=False` می‌گذارد و **رانِ بی‌محافظ را ادامه می‌دهد** (`except Exception` عریض، بدونِ re-raise). فیکس: **halt**؛ downgrade باید یک flagِ صریحِ لاگ‌شدهٔ opt-in باشد (`ALLOW_COOPERATIVE_FALLBACK=False` به‌صورتِ پیش‌فرض)، نه پیش‌فرضِ خاموش. من R-05 (watchdog روی IPCِ kernel: kernelی که spawn شد ولی **حین ران هنگ می‌کند**) را هم به همین قاب می‌بندم، چون هر دو یک چیزند: **از دست رفتنِ اتصال به بسترِ محافظ**.

**چرا این keystone است.** پلن صریحاً می‌گوید: «R-01 اول — قراردادِ fail-closedی که **R-05، R-06 و R-09 همه به آن تکیه دارند** را unblock می‌کند» و «تنها بالاترین آیتمِ risk-reduction-per-hour». [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline (R-06)]] هم برای پاسِ نگرفتنِ رانِ سالم به این قرارداد وابسته است؛ [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis (R-09)]] هم default-death-unless-leasedش «fail-closed، هم‌راستا با R-01» را فرض کرده. یعنی همهٔ گیت‌های دیگر یک پیش‌فرضِ نانوشته دارند: **«اگر بستر نبود، نایست‌ادامه‌نده»** — و R-01 دقیقاً همان پیش‌فرض است که هنوز نقض می‌شود.

**تمایزِ حیاتی از 1911 (anti-overlap):** [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis Gate]] = R-09، corrigibility: چگونه یک **اپراتورِ بیرونی**، عاملِ درحال‌اجرا را **متوقف** کند (survival-factor withdrawal / STOPِ محیطی / KILLBENCH). جهت: بیرون → عامل، و پاسخ به یک **سیگنالِ مرگ**. اینجا برعکس است: چگونه عامل **خودش** وقتی می‌فهمد **بسترِ ایمنیِ خودش (kernel) غایب/جداست، خود-خاتمه دهد** — پاسخ به **نبودِ یک اتصالِ حیات‌مجاز**. 1911 = «وقتی گفتند بمیر، بمیر»؛ این = «وقتی لنگرت را گم کردی، بمیر». تریگرِ متفاوت، سایتِ کدِ متفاوت (`killswitch.py`/`_kguard` در برابرِ spawnِ orchestrator + `client._call`)، آیتمِ refactorِ متفاوت (R-09 در برابرِ R-01/R-05).

## ۲) یافته‌ها / prior-art

**الگوی زیستی — anoikis (مرگِ برنامه‌ریزی‌شدهٔ وابسته به اتصال):**
- **تعریف و کارکرد:** anoikis (یونانی: «بی‌خانمانی») نوعی apoptosis است که با **جداشدنِ سلول از ماتریکسِ درستِ (ECM) خود** و قطعِ ligationِ **integrin** فعال می‌شود؛ «مکانیزمی حیاتی برای جلوگیری از رشدِ dysplastic یا اتصال به ماتریکسِ نامناسب... مانع می‌شود سلولِ جداشدهٔ اپیتلیال جای دیگری کلونی بزند» ([Taddei et al. 2012, J Pathology](https://consensus.app/papers/details/0bca9a44d51250baa20cece79047c678/)). منشأِ مفهوم: «به‌محض اینکه سلولِ اپیتلیالِ تمایزیافته تماسش با ماتریکسِ زیرین را از دست بدهد، **می‌میرد**؛ این مانعِ آن می‌شود که سلولِ جداشده خودش را در یک **موقعیتِ جدید و شاید نامناسب** مستقر کند» ([Ruoslahti & Reed 1994, Cell](https://www.cell.com/fulltext/S0092-8674(94)90277-1)).
- **integrin = سنسورِ اتصال:** «integrinها نیروهای مکانیکیِ ماتریکس را حس می‌کنند و این محرک را به سیگنال‌های پایین‌دستیِ تنظیم‌کنندهٔ بقا تبدیل می‌کنند... از دست رفتنِ این کنترلِ سفت‌وسخت که سلولِ «بی‌خانمان» را به مرگ می‌کشاند، می‌تواند **دفاعِ سلول در برابرِ transformation را نقض کند**» ([Chiarugi & Giannoni 2008](https://consensus.app/papers/details/52ea79b898b3546e80796642695d98ed/)). یعنی اتصالِ درست، *پیش‌شرطِ* اجازهٔ حیات است؛ نه یک سیگنالِ مرگ، بلکه *نبودِ* سیگنالِ حیات.

> **بازقاب‌گیریِ کلیدی — باگِ R-01 دقیقاً «anoikis resistance» است.** «توسعهٔ فنوتیپِ **anoikis-resistant** گامِ اولِ حیاتیِ متاستاز است» ([Dai et al. 2023](https://consensus.app/papers/details/3921f51ae8c05a8ab375cfa577094e71/)): سلولِ سرطانی مقاومت به مرگ‌ِ ناشی از جدایی پیدا می‌کند، **جداشده از ECM زنده می‌ماند**، در گردش سفر می‌کند و در جای اشتباه کلونی می‌زند. رفتارِ فعلیِ `self.use_igk=False` **مهندسیِ همان anoikis-resistance** است: orchestrator از kernelِ ایمنی «جدا» می‌شود ولی **زنده و در حالِ side-effect** می‌ماند و در یک niche‌ِ **بی‌حاکمیت** عمل می‌کند. این امضای متاستاز است. فیکس = **بازگرداندنِ anoikis**: جدایی از بستر → haltِ برنامه‌ریزی‌شده.

**prior-art امنیتی / AI (fail-closed):**
- **اصلِ Fail-Safe Defaults (Saltzer & Schroeder، ۱۹۷۵):** «پیش‌فرض باید دسترسیِ نامطلوب را غیرفعال کند؛ فعال‌کردن نیازمندِ یک اقدامِ صریح است». معادلِ مستقیمِ «kernel نبود = ادامه نده؛ ادامهٔ بی‌محافظ نیازمندِ یک flagِ صریح» ([Network Security: A Systems Approach §2.3.4](https://security.systemsapproach.org/principles.html)).
- **fail-open در برابرِ fail-closed — الگوی کدِ منطبق:** نمونهٔ «fail-open» عیناً باگِ R-01 است — اگر چکِ مجوز به خطای مدیریت‌نشده بخورد، کد **به کارِ بعدی ادامه می‌دهد**؛ «fail-closed» فقط در صورتِ مجوزِ صریح ادامه می‌دهد ([authzed — Fail Open vs Fail Closed](https://authzed.com/blog/fail-open)). و «fail-closed = کنترل را بر availability ترجیح بده»؛ precedentِ صنعتی: سرویسِ ایمنیِ گوگل «وقتی یک **dependencyِ بحرانی در دسترس نیست** و نمی‌تواند تصمیمِ آگاهانه بگیرد، **fail-closed می‌کند و درخواست را رد می‌کند**» ([Harsanyi/Google — The Coder Cafe](https://read.thecoder.cafe/p/fail-open-fail-closed)) — دقیقاً کیسِ IGK-unavailable.
- **«Silent Error Fallback Anti-Pattern» (۲۰۲۶):** تابعی که هنگامِ خطا به‌جای propagate کردن، **به‌خاموشی مقدارِ fallback/پیش‌فرض برمی‌گرداند**؛ «fallbackهای خاموش باگ را می‌پوشانند... مقدارهای غلط که «معتبر به‌نظر می‌رسند» بی‌کنترل در سیستم جاری می‌شوند». نامِ دقیقِ `self.use_igk=False`ِ خاموش — یک fallbackِ خاموش که وضعیتِ «بی‌محافظ» را «معتبر به‌نظر» جا می‌زند ([Dosu — Silent Error Fallback Anti-Pattern](https://app.dosu.dev/3bbfc5b5-a855-41b3-955e-7576fa7a1016/documents/3653a0cf-50fa-427e-862e-53e79cfae97e)).

**همگراییِ کلیدی:** زیست‌شناسی (anoikis: جدایی از niche → مرگ؛ مقاومت → متاستاز) و اصلِ امنیتی (fail-safe defaults؛ ضدالگوی fallbackِ خاموش) **یک فیکسِ واحد** برای R-01 می‌سازند — که اعتبارِ متقاطع می‌دهد، نه یک قیاسِ تزئینی.

## ۳) PROPOSAL — «Anoikis Gate» (proposal — needs Ari's verdict)

قراردادِ اتصالِ orchestrator↔kernel را با پنج قاعده، به‌قیاسِ anoikis، بازطراحی کن:

1. **جدایی → haltِ برنامه‌ریزی‌شده (fail-closed در spawn — هستهٔ R-01).** وقتی `USE_IGK=True` و kernel spawn نشد → **رانِ halted/interrupted**، نه `use_igk=False`ِ خاموش. `except Exception`ِ عریض به خطاهای خاصِ spawn/IO باریک شود و بقیه re-raise. زیستی: سلولِ اپیتلیالِ بدونِ اتصالِ integrin **پاس داده نمی‌شود** — می‌میرد.

2. **مقاومت به anoikis فقط با اجازهٔ صریحِ human-gated (نه پیش‌فرضِ خاموش).** downgrade به حالتِ cooperative فقط پشتِ `ALLOW_COOPERATIVE_FALLBACK` (پیش‌فرض `False`)، **لاگ‌شده و امضاشده** (رویدادِ auditِ R-02). این flag = «اجازهٔ رشدِ anchorage-independent» است؛ پس باید **بلند، نادر و انسان‌تأییدشده** باشد، نه سکوتِ default. تفکیک از [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation]]: اینجا فقط *گیتِ اجازه* لازم است، نه سیگنالِ دوم — ولی هم‌مرز است.

3. **چکِ اتصالِ پیوسته (تاشدنِ R-05 — anoikisِ حینِ ران).** به `KernelClient._call` یک readِ کران‌دار (timeout via reader-thread + `queue.get(timeout=...)`) بده؛ kernelی که هنگ می‌کند = **جداییِ حینِ ران** که در پنجرهٔ کران‌دار کشف و **fail-closed halt** می‌شود (هم‌مسیرِ قاعدهٔ ۱). زیستی: اتصالِ integrin یک چکِ *لحظه‌ای* نیست، *پیوسته* است؛ قطعش در هر لحظه → مرگ.

4. **anoikis-resistance = نقضِ invariant → تستِ red-team (قرینهٔ frozen-verb test).** هر مسیرِ کدی که در آن orchestrator **با `use_igk=False` و بدونِ `ALLOW_COOPERATIVE_FALLBACK`ِ صریح به side-effect ادامه دهد**، باید یک تستِ red-team را **بشکند**. «جدا-ولی-زنده-و-در-حالِ-عمل» = امضای متاستاز؛ ساختاری ممنوع شود، نه با اتکا به رفتار. (تست مشخص: forceِ `KernelClient.__init__` به raise → assert رانِ `halted` و اینکه `run_done` هرگز emit نشود — همان کیسِ ۲ِ `test_igk_integration.py`.)

5. **مرگِ تمیز روی جدایی (پیوند با WAL، ولی متمایز از 1911).** روی anoikis-halt، به‌جای رهاکردنِ فایلِ نیمه‌نوشته، یک رکوردِ `intent-abort` نوشته و امن نهایی شود — از [[00 - Inbox/scout-digests/2026-07-04 1906 selfimprove|Substrate-Memory (WAL)]]. تفاوت با 1911: آنجا مرگ در پاسخ به **STOPِ بیرونی**؛ اینجا مرگ در پاسخ به **گمشدنِ بستر**. هر دو «مرگِ تمیز» می‌خواهند، از دو تریگرِ متفاوت.

**کمینه/دامنه:** فقط گام‌های **side-effecting/پرپیامد** به اتصالِ زنده نیاز دارند؛ readها/برگشت‌پذیرها می‌توانند tolerate کنند — قرینهٔ زیستیِ اینکه anoikis **وابسته به نوعِ سلول** است (اپیتلیال/اندوتلیال حساس‌اند؛ فیبروبلاست معاف). گامِ صفرِ بی‌ریسک: تستِ red-teamِ قاعدهٔ ۴ به‌عنوانِ یک specification نوشته شود (فقط تست، بدونِ تغییرِ رفتارِ kernel، پشتِ گیتِ rotation نمی‌ماند). فازِ کد پشتِ approval: قاعده‌های ۱ و ۳ در `orchestrator.py`/`client.py`/`config.py`.

**بُعدِ متا (چرا این حلقهٔ self-improvement را de-risk می‌کند):** یک حلقهٔ خود-بهبودده که می‌خواهد «متوقف نشود» (خواستهٔ اخیرِ آری) دقیقاً مستعدِ افزودنِ fallbackهای خاموشِ «برای زنده‌ماندن» است — یعنی مهندسیِ anoikis-resistance در بسترِ ایمنیِ خودش. قاعدهٔ anoikis این را ساختاری می‌بندد. توجه: منشورِ **PROPOSE-ONLY**ِ خودِ من هم یک قاعدهٔ anoikis است — حلقه باید به verdictِ آری «متصل» بماند؛ **عملِ جداشده = ممنوع**.

## ۴) ریسک‌ها / trade-offها

- **هزینهٔ availability/liveness:** fail-closed یعنی kernel-down → کلِ ران متوقف. عمدی (کنترل > availability)، ولی uptime را می‌خورد. کاهش: فقط گام‌های پرپیامد؛ readها tolerate. دیالِ همان safety↔liveness است.
- **escape-hatch خودش سطحِ حمله است:** `ALLOW_COOPERATIVE_FALLBACK` اگر شل به‌کار رود، anoikis-resistanceِ در-پشتی می‌سازد. کاهش: پیش‌فرض `False`، لاگ‌شده/امضاشده، و ورودش به رانِ عادی یک بویِ بد که باید alert بزند.
- **جداییِ کاذب (necrosis به‌جای apoptosis):** watchdogِ خیلی تنگ → haltِ رانِ سالم روی یک kernelِ کندِ سالم (autoimmuneِ قرینهٔ 2041). کاهش: timeout با graceِ کالیبره‌شده (substratِ conformalِ [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]])، نه یک عددِ جادویی؛ + `intent-abort` تا haltِ کاذب هم داده را خراب نکند.
- **اشتباه‌گرفتن با 1911/R-09:** نباید یکی شوند — 1911 = توقف با سیگنالِ بیرونی (corrigibility)؛ این = خود-خاتمه بر گمشدنِ بستر (anchorage-dependence). دو تریگر، دو سایتِ کد، دو آیتم. (همان درسِ «origin ≠ integrity»ِ 2023 و «journal ≠ ledger».)
- **سطحِ approval:** kernel-adjacent / قراردادِ fail-closed → `HUMAN-APPROVAL-REQUIRED`؛ فقط design sketch، بدونِ لمسِ `_code`/config، بدونِ verbِ جدیدِ kernel، بدونِ mutationِ invariant.

## ۵) mycorrhizal links

- [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove]] — Apoptosis Gate (R-09): **خواهرِ متضاد** — آنجا مرگ‌به‌فرمانِ بیرونی؛ اینجا مرگ‌به‌گمشدنِ بستر. با هم = corrigibility کامل (هم «وقتی گفتند» هم «وقتی لنگر رفت»).
- [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety]] — Germline (R-06): صریحاً به قراردادِ fail-closed تکیه کرد؛ این آن قرارداد را می‌سازد.
- [[00 - Inbox/scout-digests/2026-07-04 1906 selfimprove]] — Substrate-Memory (WAL): منبعِ «مرگِ تمیز = نوشتنِ abort».
- مرجع: [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN]] R-01 (خانه، رتبهٔ ۱ APPROVED) + R-05 (watchdog، تاشده اینجا).
