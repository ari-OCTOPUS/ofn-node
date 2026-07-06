# الگوهای معماری قوی و قابل‌استفاده مجدد — مغز دوم v2

## ۱) خلاصه اجرایی

آری از معماری سیستم‌های غیرمتمرکز و خودترمیم‌شونده الهام‌گرفته از زیست‌شناسی (Armillaria ostoyae) بود. ۱۲ الگوی بنیادی شناسایی شد که بین اسناد MYCELIAL-MASTER-SPEC، RATIFIED-TASKS، TWO-BRAIN-CONTROL-BLUEPRINT و AUTONOMY-LADDER دیده می‌شوند. این الگوها برای مغز دوم v2 (سیستم ۴ لایه‌ای) قابل‌استفاده‌اند به‌ویژه در فاز ۳ (آداپترها) و فاز ۴ (تکامل خودمختار).

---

## ۲) جدول الگوها (۱۲ الگو)

| # | نام الگو (فارسی) | اسم انگلیسی | ۱ خط ماهیت | فایل اصلی |
|---|---|---|---|---|
| 1 | توپولوژی مایسیلیایی | Mycelial Topology | شبکهٔ leaderless، بی‌SPOF، رشتهٔ رهیزومورف ستون‌شکل | MYCELIAL-ARCHITECTURE-vfinal.md |
| 2 | نردبان استقلال L0-L3 | Autonomy Ladder | چهار پله: گزارش/پیشنهاد/bounded-auto/خودکار با گاردهای سختِ whitelist | Autonomy Ladder v1 |
| 3 | درب‌های کنترلی (EffectorGate) | EffectorGate Pattern | تنها نقطهٔ choke برای side-effect؛ permit→execute→log | MYCELIAL-MASTER-SPEC §۲ |
| 4 | دفتر تغییرناپذیر (Anchor Ledger) | Anchor Ledger | append-only سند حقیقت برای تصمیم‌ها و تأییدها | MYCELIAL-MASTER-SPEC §۶ |
| 5 | وظایفِ مصحح‌شده | RATIFIED-TASKS | متن کامل پرامپت و cron‌ها کنار یکدیگر برای bootstrap-watchdog | RATIFIED-TASKS.md |
| 6 | تبخیر و عمرِ محدود (TTL) | Evaporation Pattern | دیجست‌های >۱۴ روز auto-archive + فایل‌های «_» معاف | RATIFIED-TASKS::mycelial-consolidator |
| 7 | تجمع و انتخابِ ناوگان | Spawn & Select Fleet | مِش scout‌ها؛ تکاملِ افزایشی با self-selection | RATIFIED-TASKS::fleet-selection |
| 8 | دوبی حکمِ doctor | Dual-Score Doctor | سلامتِ قطعی (ستون ۱) + جهش (ستون ۲) + حلقهٔ فکر (ستون ۳) | Evolutionary Doctor §۲-۴ |
| 9 | کنترلِ دو مغز | Two-Brain Control | انسان (قاضی/برازندگی) + دکتر (ادراک/تشخیص/پیشنهاد) | TWO-BRAIN-CONTROL-BLUEPRINT |
| 10 | بازخورد شنیدار و ردیابی | HEARTBEAT Watchdog | beat دوطرفه هر تسک؛ سکوت >۲×دوره = regress | AUTONOMY-LADDER §۵ |
| 11 | Reflexion و خودبهبودی | Reflexion Cycle | Actor→Evaluator→Self-Reflect→درس در ledger→دفعهٔ بعد | MYCELIAL-MASTER-SPEC §۷ |
| 12 | صف تأیید و Approve-First | Approve-First Queue | L2 action فقط پس از verdict انسانی؛ timeout=رد | ARCHITECTURE v2 §۶ |

---

## ۳) شرح هر الگو و نگاشت به v2

### الگو ۱: توپولوژی مایسیلیایی (Mycelial Topology)

**ماهیت:** یک شبکهٔ بدون‌مرکز که از یک ستونِ backbone (rhizomorph) تشکیل می‌شود که priority-lanes (EffectorGate) را حمل می‌کند و بر روی مِشِ leafِ بدون‌مرکز (scout agents) حاکم می‌شود.

**مکانیزم:** ستون = MYCELIAL-MASTER-SPEC و RATIFIED-TASKS (مرجعِ حقیقت)؛ هر پروژه یک leaf است؛ اتصالات طبق CONNECTIONS-MAP. بدون ستون = مِش بهم می‌خورد.

**در v2 فاز ۳:** هر آداپتر بیزنس (زیمان/نقاشی/حسابداری) یک leaf; رکن A و B هر یک یک هایفِ است. ادمینِ کنترل = ستون. synchronization via core.db (جدول briefs/outbox/feedback) — معادلِ آناستوموز.

**فایل:** `_launchpad/second-brain-live/ARCHITECTURE.md` §۱

---

### الگو ۲: نردبان استقلال (Autonomy Ladder)

**ماهیت:** چهار سطحِ تصمیم‌گیری: L0 گزارش / L1 پیشنهاد / L2 bounded-auto (فقط whitelist) / L3 خودکار (مشتق idempotent).

**مکانیزم:** پلهٔ پایین‌تر برای هر action مبهم؛ whitelist L2/L3 صریح؛ kill-switch انسان در تمام سطوح.

**در v2 فاز ۴:** فاز ۳ تمام اقدامات L2 هستند (bounded-auto: رکن A بریف تولید می‌کند، لکن outbox draft می‌ماند تا ادمین تأیید کند). فاز ۴ = L3 ممکن برای مغز تکاملی پیشنهاد جهش (با version-control + branch).

**فایل:** `00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder).md`

---

### الگو ۳: درب‌های کنترلی — EffectorGate

**ماهیت:** تنها نقطهٔ دروازه‌گذار برای هر side-effect (delete/build/deploy/پول/پیام خارجی); permit الزامی قبل‌از اجرا.

**مکانیزم:** `fusion-mvp/igk/daemon.py` یا معادلِ core.db transaction؛ هر write = `log(who, what, permit_status)`.

**در v2 فاز ۲:** gateway.py یک EffectorGate است برای LLM/search/tg calls؛ هر رکن B پیام قبل‌از ارسال از `outbox` مستدی اجازه می‌گیرد (status: draft→pending→approved/rejected→sent).

**فایل:** `MYCELIAL-MASTER-SPEC.md` §۲

---

### الگو ۴: دفتر تغییرناپذیر — Anchor Ledger

**ماهیت:** append-only سندی که تمام تصمیم‌ها (verdict، approve، regress) را سابقه می‌سازد — source-of-truth برای audit.

**مکانیزم:** EXPERIENCE-LEDGER در vault + ledger_ref برای هر ردیف دیگر.

**در v2 فاز ۲:** جدول‌های sqlite (`briefs`, `feedback`, `outbox`) append-only خود هستند؛ هر feedback = خط ledger v2 → برای فاز ۴ جهشِ مشخص.

**فایل:** `_memory/EXPERIENCE-LEDGER.md` (vault-side) + v2 schema

---

### الگو ۵: وظایفِ مصحح‌شده — RATIFIED-TASKS

**ماهیت:** متنِ کامل پرامپت + cron زمان‌بند کنار یکدیگر در یک منبعِ حقیقت؛ اگر تسک حذف شود، خود watchdog آن را از متن بازسازی کند.

**مکانیزم:** جدول رجیستری + autonomy-protocol-block تزریق به هر پرامپت (§۳ RATIFIED-TASKS).

**در v2 فاز ۲:** هر بیزنس یک تسک scheduler دارد (مثل APScheduler نقاشی)؛ رکن A روزانه trigger می‌شود. جدول ratified در control-brain رجیستری = منبع حقیقت.

**فایل:** `05 - Agents/RATIFIED-TASKS.md`

---

### الگو ۶: تبخیر و عمرِ محدود — TTL/Evaporation

**ماهیت:** داده‌های خودترمیم‌شونده (scout-digests) >۱۴ روز برگشت‌پذیرانه archive می‌شوند برای کاهش clutter و زیرِ نظارت.

**مکانیزم:** in-place archive → `_Duplicates/scout-digests-archive/` (برگشت‌پذیر); فایل‌های «_» معاف (تابلو، dashboard).

**در v2 فاز ۲:** briefs/feedback >۷ روز می‌توانند archive شوند (یا به summary جمع‌شوند)؛ knowledge entries دارایِ خودکار‌باقی می‌مانند.

**فایل:** `RATIFIED-TASKS.md` :: mycelial-consolidator

---

### الگو ۷: تجمع و انتخابِ ناوگان — Spawn & Select Fleet

**ماهیت:** مِش scout‌ها به‌صورت افزایشی تکامل می‌یابند؛ تسک‌های جدید micro/معقول اول؛ بعد merge و promotion با signal.

**مکانیزم:** fleet-selection در رجیستری + proposal ساختاری برای spawn/retire.

**در v2 فاز ۳:** هر بیزنس یک «ناوگان» محدود تحقیق دارد (مثل ziman harvesters)؛ فاز ۴ می‌تواند scout‌های نوی فرضیهٔ جهش بسازد (خودِ تکامل).

**فایل:** `RATIFIED-TASKS.md` :: fleet-selection

---

### الگو ۸: دوبیِ حکمِ Doctor — Dual-Score Doctor

**ماهیت:** دکتر از سه ستون تشکیل می‌شود: نگهبانِ سلامت (قطعی)، کاشفِ جهش، حلقهٔ فکری.

**مکانیزم:**
- ستون ۱ = health checks قطعی (dashboard_doctor.py) صفر-LLM
- ستون ۲ = Mutation Ledger (جهش‌های غیرمنتظره)
- ستون ۳ = Fugu Ultra (فکریِ تکاملی) پشتِ budget-gate

**در v2 فاز ۳:** دکتر v1 موجود است (validator); فاز ۴ ستون ۲+۳ ساخته می‌شوند.

**فایل:** `00 - Inbox/Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05.md`

---

### الگو ۹: کنترلِ دو مغز — Two-Brain Control

**ماهیت:** انسان (مالک / قاضی / تعریفِ برازندگی) و دکتر (ادراک / تشخیص / پیشنهاد) در یک حلقهٔ بازخورد؛ هیچ‌کدام جای دیگری را نمی‌گیرد.

**مکانیزم:** artifact زنده (ارتیفکت fleet-live-dashboard) = تنها کابینِ مشترک؛ askClaude برای دکتر، sendPrompt برای انسان.

**در v2 فاز ۳:** ربات ادمین (انسان) ارزیابیِ approve/reject از briefs (دکتر) را می‌کند.

**فایل:** `_memory/TWO-BRAIN-CONTROL-BLUEPRINT.md`

---

### الگو ۱۰: بازخورد شنیدار و ردیابی — HEARTBEAT Watchdog

**ماهیت:** هر تسک در شروع و پایان خود را ثبت می‌کند (timestamp + نتیجه); سکوت >۲×دورهٔ انتظار = alert + regress ledger.

**مکانیزم:** jدول `_memory/HEARTBEAT.md` (overwrite-مجاز); هر تسک یک سطر؛ experience-review هفتگی آن را می‌سنجد.

**در v2 فاز ۲:** جدول sqlite `scheduler_heartbeat` می‌تواند ثبت کند (کدام رکن خشکیده است؟) و هشدار بدهد.

**فایل:** `AUTONOMY-LADDER` §۵

---

### الگو ۱۱: Reflexion و خودبهبودی — Reflexion Cycle

**ماهیت:** Actor تولید → Evaluator نمره → Self-Reflection درس → ledger → دفعهٔ بعد بهتر.

**مکانیزم:** پرامپت critic + optimizer + logger (§۷ MYCELIAL-MASTER-SPEC); هر ایجنت که سند را می‌خواند باید خود را بهتر کند.

**در v2 فاز ۳-۴:** feedback جدول (useful/not-useful) = دادهٔ training برای Reflexion loop مغز تکاملی.

**فایل:** `MYCELIAL-MASTER-SPEC.md` §۷

---

### الگو ۱۲: صفِ تأیید و Approve-First — Approve-First Queue

**ماهیت:** هیچ action L2 بدون verdict انسانی جاری نمی‌شود؛ timeout یا رد (fail-closed).

**مکانیزم:** draft/pending/approved/rejected/sent state در outbox; ربات ادمین inline دکمه‌های Approve/Edit/Reject نشان می‌دهد.

**در v2 فاز ۳:** رکن B (OwnerInteraction) پیام را به `outbox` کشیدن می‌کند با status=draft، ربات ادمین approve می‌کند، سپس به ربات خود بیزنس برای صاحب می‌رود.

**فایل:** `_launchpad/second-brain-live/ARCHITECTURE.md` §۲ و §۶

---

## ۴) سه توصیهٔ تیزِ برای فاز ۴ — مغز تکاملی

بر اساس دیزاین RATIFIED و DOCTOR و TWO-BRAIN:

### توصیهٔ ۱: شروعِ Reflexion با feedback جدول (نه Fugu پرتوکل)

**چرا:** جدول `feedback` (brief_id, useful:0/1, note) از فاز ۳ آباد است. بدلِ اینکه Fugu مستقیم تحقیق را بدہد، درس‌های قطعیِ human-vetted را از feedback استخراج کن (مثل: «این brief overdetailed بود»، «قالب action غیر کاربردی بود»). Reflexion cycle اول روی این feedback اجری کن، بعد ارتقا به فکری Fugu.

**دامنهٔ الگو:** Reflexion Cycle + HEARTBEAT Watchdog + Dual-Score (ستون ۱ = feedback قطعی، ستون ۲ = Fugu proposal).

---

### توصیهٔ ۲: دو جهت برای Evaporation و TTL در Mutation Ledger

**چرا:** مغز تکاملی جهش‌ها پیشنهاد می‌دهد؛ بعضی قابلِ خودکار promotion و بعضی منتظرِ verdict. برای جهش‌های quarantined >۳۰ روز بدون verdict: خودکار revert با ردیفِ ledger «TTL-expired». این ریسکِ فراموشیِ جهش را کاهش می‌دهد و drift را مهار می‌کند.

**دامنهٔ الگو:** Evaporation Pattern + Anchor Ledger + Autonomy Ladder (L2 bounded-auto با timeout).

---

### توصیهٔ ۳: دکمهٔ اضطراری تیز‌تری (Three-Level Kill)

**چرا:** منشور autonomy و TWO-BRAIN‌ فقط یک kill-switch توصیف می‌کنند. برای فاز ۴ که Fugu خودش تصمیم‌گیری می‌کند، سه سطح لازم است:
- سطح ۱: حلقهٔ فاز ۴ را فقط pause کن (resume می‌شود)
- سطح ۲: حلقه را کل kill کن (یافته‌های quarantined باقی می‌مانند)
- سطح ۳: آخرین N جهش را revert کن (git rollback)

**دامنهٔ الگو:** Two-Brain Control + EffectorGate (درب‌های سه‌سطحی) + Anchor Ledger (برای undo).

---

## ۵) ریسک‌هایی که الگوها هشدار می‌دهند

| ریسک | الگوی هشدار | کاهش |
|---|---|---|
| drift منبعِ حقیقت (vault doc ↔ runtime) | Anchor Ledger + Mycelial Topology | همه‌ی read از فایل‌سیستم + لایهٔ شناخت زمینه (SYSTEM-STATE) |
| خزشِ دامنهٔ self-verdict | Autonomy Ladder + Dual-Score Doctor | معیارِ چهارگانهٔ L2 + halt فوری برای نقض invariant |
| فراموشیِ جهش (Fugu proposal بدون دنبال) | Mutation Ledger + TTL + HEARTBEAT | expires 30d; timeout=revert + beat watchdog |
| secret در artifact/cache/log | EffectorGate + Approve-First | تمامِ ورودیِ external quarantine؛ secret هرگز echo |
| SPOF در ربات ادمین | Mycelial Topology + spawn & select | چند ربات ادمین ممکن است (polling)؛ وضعیت در core.db shared |
| تبخیرِ شواهد (برگشت‌ناپذیر) | Evaporation Pattern | in-place archive → `_Duplicates/` برگشت‌پذیر; هرگز hard-delete |

---

**پایان.** این ۱۲ الگو آرایهٔ DNA‌ی سیستم هستند؛ v2 فاز ۳-۴ با شناخت و ارتباط این‌ها قوی‌تر می‌شود.

---

> **🧬 Pass 2 (عمیق‌تر، به دستور آری):** ۱۱ الگوی جاافتاده + ۵ هایبرید کامپوزیت + ۲۹ قاعدهٔ DECISIONS → [[00 - Inbox/ARCHITECTURE-PATTERNS-DEEP-V2-2026-07-06|ARCHITECTURE-PATTERNS-DEEP-V2]] — ورودی رسمی فاز ۴.
