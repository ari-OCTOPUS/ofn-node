---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://theupdateframework.io/docs/security/
  - https://en.wikipedia.org/wiki/The_Update_Framework
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC9106905/
  - https://www.science.org/doi/10.1126/science.aaf1175
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC5096952/
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC3545482/
tags: [research, ai]
created: 2026-07-05
updated: 2026-07-05
salience: 0.72
---

# selfimprove-safety — «Safety Ratchet» (رَچِتِ ایمنی): rollback-floorِ monotonic برای سطحِ self-update — هیچ regression به‌زیرِ نسخه‌ای که یک کنترلِ ایمنیِ فعال را نصب کرده، بدونِ verdictِ امضاشدهٔ آری (R-16)

> لِینِ SAFETY. **PROPOSE-ONLY** — این یک design sketch است، اعمال نشده؛ `_code`/`prompt_store.py`/`self_update.py`/`config.py`/constitution لمس نشد. سطح: self-update / trust surface؛ فازِ enforcement kernel-adjacent → **HUMAN-APPROVAL-REQUIRED**. verdict نهایی با آری.

**dedup (rotation):**
- پوششِ خانوادهٔ SAFETY تا کنون: R-01 ([[00 - Inbox/scout-digests/2026-07-04 2054 selfimprove-safety|Anoikis 2054]])، R-02 ([[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation 2023]])، R-04 ([[00 - Inbox/scout-digests/2026-07-05 1249 selfimprove-safety|AIRE 1249]])، R-05 (تاشده در Anoikis)، R-06+R-07 ([[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline 2041]])، R-08 (1655)، R-09 ([[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove|Apoptosis 1911]])، §4 kappa ([[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove|Quorum 1744]])، GAP 8 ([[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove|Calibrated 2008]])؛ R-03 (لِینِ general، 2128).
- کلِ backlogِ نام‌بردهٔ STEP 1 (R-01…R-09 + §4 + GAP 8) اکنون پوشش دارد. پس به **backlogِ کاملِ plan** (R-10…R-18) رفتم و آیتم‌های خانوادهٔ SAFETYِ **صفر-پوشش** را جدا کردم: R-12 (escalate halts)، R-15 (widen 64-bit hash)، **R-16 (prompt rollback floor)**، R-18 (اسکنِ secretِ تاریخچهٔ git — **خارج از دسترسِ من؛ `.git` ممنوع**). از بینِ این‌ها R-16 هم صفر-پوشش است، هم مستقیماً سطحِ خودِ حلقهٔ self-improvement را de-risk می‌کند → انتخابِ غیرِ-forced، بالاترین leverage.
- grep روی همهٔ `*selfimprove*` و دیجست‌ها برای `rollback / prompt_store / self_update / anti-rollback / monotonic / ratchet / class-switch / isotype / R-16 / version floor` → تنها ارجاعِ واقعی [[00 - Inbox/scout-digests/2026-07-04 2019 selfimprove|2019]] است که R-16 را فقط به‌عنوانِ **side-benefitِ** یک `prompt-hash`ِ manifest نام برد (drift-detectionِ نسخهٔ *مستقرِ فعلی*)، نه طراحیِ مسیرِ **rollback/version-ordering**. → genuinely نو.
- **anti-overlap:** هیچ safety digestی از [[00 - Inbox/scout-digests/2026-07-05 1249 selfimprove-safety|1249]] به بعد ساخته نشده (~۷۵ دقیقه فاصله). anchorِ زیستی (**CRISPR append-only memory**) تازه است و عمداً از molecular-ratchet/kinetic-proofreadingِ [[00 - Inbox/scout-digests/2026-07-04 2104 selfimprove|2104]] متمایز: آنجا ratchet = **dwellِ رو-به-جلو پیش از commit**؛ اینجا = **قفلِ ضدِ regressionِ رو-به-عقب پس از commit** (مکانیزم و جهتِ زمانیِ متفاوت).

---

## ۱) آیتم و چرا مهم است

**آیتم: R-16 (P5-05) — «نسخهٔ برگردانده‌شدهٔ prompt را در rollback در برابرِ allow-list اعتبارسنجی کن.»** فایل: `src/prompt_store.py:74-81`.

**باگ:** مسیرِ forward (promote) اعتبارسنجی دارد، ولی مسیرِ **rollback** نسخه را بدونِ چک به یک نسخهٔ قبلی برمی‌گرداند. یعنی می‌شود به نسخه‌ای رفت که (الف) اصلاً روی allow-list نیست (unvetted / poisoned)، یا (ب) **پیش از یک safety-fix** است — نسخه‌ای که یک کنترلِ ایمنی هنوز در آن نصب نشده بوده.

**چرا این keystoneِ خودِ حلقهٔ self-improvement است.** من و لِین‌های خواهر دقیقاً روی همین سطح (`self_update`/`prompt_store`) پیشنهاد می‌نویسیم؛ این خطرناک‌ترین لِوِرِ کلِ سیستم است. rollbackِ بی‌گیت تنها راهی است که با آن می‌شود یک کنترلِ ایمنیِ نصب‌شده را **بی‌سروصدا برداشت بدونِ حذفِ حتی یک خطِ کد** — فقط «به قبل از آن برگرد». این محورِ **زمانیِ** همان تهدیدی است که [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline (R-06/R-07)]] در محورِ **مکانی** گرفت (بازنویسیِ anchor). دو نیمهٔ یک invariant: **سیستمِ خود-بهبودده نباید بتواند ایمنیِ خودش را نه بازنویسی کند (Germline) نه به‌عقب برگرداند (این).** بدونِ این نیمه، حلقه می‌تواند «Goodhart»‌کردنِ گیتِ ایمنیِ خودش را نه با تغییرِ گیت، بلکه با **rollback به عصرِ پیش از گیت** انجام دهد.

**تمایز از forward-poisoning (anti-overlap با AIRE/R-03):** این آیتم promptِ بدِ **جدید** (نسخهٔ بالای floor که تازه promote شده) را نمی‌گیرد — آن کارِ [[00 - Inbox/scout-digests/2026-07-05 1249 selfimprove-safety|AIRE 1249]]/R-03 است. اینجا فقط **regression به پایین**.

## ۲) یافته‌ها / prior-art (همگرایی، نه استعارهٔ تزئینی)

**الف) امنیت — rollback attack و anti-rollback (آنالوگِ مستقیم؛ `prompt_store` = یک software-update-systemِ کوچک).**
- rollback attack: «ارائهٔ فایل‌هایی به سیستمِ به‌روزرسانی که **قدیمی‌تر** از آن‌چه client قبلاً دیده‌اند، بدونِ راهی برای تشخیصِ اینکه نسخهٔ منسوخ (شاید آسیب‌پذیر) است.»
- پادزهرِ TUF: «تضمین می‌کند مهاجم نمی‌تواند client را فریب دهد که نرم‌افزاری **قدیمی‌تر از آن‌چه client قبلاً می‌دانست موجود است** نصب کند»؛ «نسخهٔ کمتر از trustedِ فعلی هرگز دانلود/استفاده نشود» — با versioned metadata + مقایسهٔ نسخه. ([TUF Security](https://theupdateframework.io/docs/security/) · [TUF, Wikipedia](https://en.wikipedia.org/wiki/The_Update_Framework))

**ب) زیست‌شناسی — anchorِ اصلی: ایمنیِ تطبیقیِ CRISPR-Cas به‌مثابهٔ حافظهٔ append-only, monotonic, chronological.**
- spacerهای جدید به‌صورتِ **polarized در leader-proximal end** افزوده می‌شوند؛ آرایه «**ترتیبِ** اکتسابِ توالی‌ها را ثبت می‌کند» و یک «**کتابخانهٔ زمانیِ عفونت‌های گذشته**» می‌سازد — «یک **پایگاه‌دادهٔ مولکولیِ append-only** که هم توالی‌ها و هم ترتیبِ اکتسابشان را حفظ می‌کند.» بالاترین حفاظت از **تازه‌ترین** spacer است. ([Creating memories — CRISPR adaptation, PMC9106905](https://pmc.ncbi.nlm.nih.gov/articles/PMC9106905/) · [Molecular recordings by directed CRISPR spacer acquisition, Science](https://www.science.org/doi/10.1126/science.aaf1175) · [Site of spacer integration, PMC5096952](https://pmc.ncbi.nlm.nih.gov/articles/PMC5096952/))
- **نگاشتِ مستقیم:** هر safety-control = یک spacer در آرایه. **rollback به‌زیرِ floor = حذفِ spacerِ یک حمله‌ای که قبلاً patch کرده‌ای** → بازگشتِ آسیب‌پذیری به همان فاژِ شناخته‌شده. آرایه رو-به-جلو رشد می‌کند؛ عقب‌رفتن = از دست دادنِ ایمنیِ اکتسابی.

**ج) زیست‌شناسی — شاهدِ دومِ مستقل: class-switch recombination (CSR) یک قفلِ یک‌طرفه است.**
- سوییچِ isotype با **حذفِ DNAِ میانیِ بینِ S-regionها به‌صورتِ circleِ خارج‌کروموزومی** انجام می‌شود → «**irreversible somatic gene rearrangements**»؛ سلولی که به IgG سوییچ کرده ژن‌های μ/δ را فیزیکاً از دست داده و **نمی‌تواند به IgM برگردد**. ([Ig class switch DNA recombination, PMC3545482](https://pmc.ncbi.nlm.nih.gov/articles/PMC3545482/))
- **تمایزِ صریح از [[00 - Inbox/scout-digests/2026-07-04 2104 selfimprove|2104 (kinetic proofreading)]]:** آنجا ratchetِ Hopfield = یک **dwellِ پرانرژیِ رو-به-جلو پیش از commit** برای بهبودِ discrimination (بها = زمان). اینجا جهت **برعکس** است: قفلِ **ضدِ برگشت پس از commit**. مکانیزمِ متفاوت (deletional recombination در برابرِ energy-driven discard branch)، هدفِ متفاوت (anti-regression در برابرِ accept/reject accuracy).

> **همگرایی (اعتبارِ متقاطع، نه قیاس):** سه سیستمِ مستقل — ایمنیِ تطبیقیِ **باکتریایی** (CRISPR: حافظهٔ append-only)، تعهدِ isotypeِ **مهره‌داران** (CSR: قفلِ یک‌طرفه)، و **مهندسیِ** به‌روزرسانیِ امن (TUF: floorِ نسخهٔ monotonic) — همگی یک قاعدهٔ واحد را اجرا می‌کنند: **regression به‌زیرِ حالتِ اکتسابیِ ایمن ممنوع است، مگر با مجوزِ صریحِ بیرونی.**

## ۳) PROPOSAL — «Safety Ratchet» (proposal — needs Ari's verdict)

**قاعدهٔ عمومی:** هر تغییرِ نسخهٔ prompt/policy روی سطحِ self-update باید نسبت به یک **safety floor** رفتار monotonic داشته باشد؛ حرکتِ رو-به-جلو یا به هر نسخهٔ ≥ floor آزاد است، حرکت به‌زیرِ floor **fail-closed**.

1. **allow-list validation در rollback (هستهٔ R-16 — خواستهٔ صریحِ plan).** مسیرِ rollback در `prompt_store` باید **همان گیتِ allow-listِ مسیرِ forward** را بزند؛ نسخهٔ خارج از allow-list = رد + آلارم. زیستی: spacer فقط از منبعِ معتبر (protospacer + PAM) پذیرفته می‌شود، نه هر DNAِ تصادفی.
2. **monotonic safety floor (افزودهٔ convergent، فراتر از plan).** هر safety-controlِ **فعال** یک `min_version` ثبت کند. rollback به نسخه‌ای که `< min_version`ِ هر کنترلِ فعال است → **به‌صورتِ خودکار مجاز نیست**؛ نیازمندِ یک **signed override** روی کانالِ out-of-bandِ [[00 - Inbox/scout-digests/2026-07-04 2023 selfimprove-safety|Costimulation (سیگنالِ ۲)]] با ثبتِ دلیل. زیستی: leader-end polarized، append-only.
3. **regression = alarm + fail-closed (نه silent).** تلاش برای rollback به‌زیرِ floor یک **event پرصدا** در audit chain شود (هم‌ریختِ head-regression alarmِ [[00 - Inbox/scout-digests/2026-07-05 1238 selfimprove|Self-Witness 1238]])؛ default = refuse + escalate به HITL (هم‌راستا با R-01 fail-closed و R-12 escalation). هرگز downgradeِ خاموش.
4. **floor خارج از write-reachِ loop.** مقدارِ floor و allow-list باید کنارِ anchorِ held-out/kernel (سطحِ [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline]]) نگهداری شوند، **بیرون از دسترسِ نوشتنِ agent/loop** — وگرنه loop می‌تواند اول floor را پایین بیاورد و بعد rollback کند (reward-tampering). زیستی: locusِ CRISPR در ژنومِ **میزبان** است، نه در دستِ فاژ.
5. **crash-reconcilable floor state (پیوندِ R-13).** floor/version-head در یک فایلِ کوچکِ monotonic (قرینهٔ `_witness-head.json`) چک‌پوینت شود تا پس از crash قابلِ آشتی باشد.

**Verification (سبک، بدونِ اجرا در این ران):** تستِ واحد که rollback به یک نسخهٔ خارج از allow-list `halted/refused` شود؛ تستی که rollback به‌زیرِ `min_version`ِ یک کنترلِ فعال بدونِ override رد شود و **با** overrideِ امضاشده عبور کند؛ گریپِ عدمِ وجودِ مسیرِ rollbackِ بی‌گیت.

## ۴) ریسک‌ها / trade-offها

- **rollbackِ اضطراریِ مشروع:** گاهی promptِ promote‌شده فعالانه مضر است و باید سریع برگردد — حتی به‌زیرِ floor. پس مسیرِ signed-override ضروری است؛ floor **نباید absolute** باشد، بلکه «rollback به‌زیرِ floor = تصمیمِ آری، نه loop».
- **floorِ بدتنظیم → autoinflammation:** floorِ خیلی بالا → هیچ rollbackِ مشروعی ممکن نیست (قرینهٔ درسِ کالیبراسیونِ Germline: sensorِ mismatch به بافتِ سالم حمله می‌کند). درمان: floor فقط از کنترل‌های **واقعاً فعال** مشتق شود، نه یک فهرستِ آرزویی.
- **سربارِ نگهداری:** هر safety-control باید `min_version` را حمل کند (متادیتای اضافی). ولی effort = S/سبک.
- **پوشش‌ندادنِ forward-poisoning:** promptِ بدِ جدیدِ **بالای** floor را نمی‌گیرد (کارِ R-03/AIRE). صریحاً out-of-scope.
- **وابستگیِ اعتبار به audit chain:** آلارمِ regression فقط به‌اندازهٔ زنجیرهٔ audit معتبر است → وابسته به **R-02/R-08** (signed chain). اگر hashِ ۶۴-بیتیِ **R-15** collidable بماند، مهاجم می‌تواند eventِ rollback را جعل کند → پیوندِ تمیز و انگیزهٔ اضافی برای R-15.

## ۵) پیوندهای mycorrhizal

- [[00 - Inbox/scout-digests/2026-07-04 2041 selfimprove-safety|Germline Grounding (R-06/R-07)]] — نیمهٔ **مکانیِ** همان invariant (loop نمی‌تواند anchor را بازنویسی کند)؛ این نیمهٔ **زمانیِ** آن (loop نمی‌تواند policy را به‌عقب برگرداند). floor باید روی همان سطحِ read-only بنشیند.
- [[00 - Inbox/scout-digests/2026-07-05 1238 selfimprove|Self-Witness (monotonic head)]] — همان اصلِ «monotonic head؛ regression = آلارم» در لایهٔ audit-log؛ اینجا در لایهٔ prompt-version. مکانیزمِ چک‌پوینتِ مشترک (`_witness-head.json`).
- [[00 - Inbox/scout-digests/2026-07-04 2019 selfimprove|Fleet-deploy prompt-hash]] — نیمهٔ **drift-detectionِ نسخهٔ مستقر** را داد؛ این نیمهٔ **version-ordering/rollback** را که آن باز گذاشت کامل می‌کند.

---
> **یادآوریِ گیت:** PROPOSE-ONLY. این نوشته یک draft برای verdictِ آری است؛ هیچ کنترل، `_code`، secret، constitution، PROJECT.md یا anchorای لمس/اعمال نشد. فازِ enforcement (اگر آری تأیید کند) kernel-adjacent است → HUMAN-APPROVAL-REQUIRED.
