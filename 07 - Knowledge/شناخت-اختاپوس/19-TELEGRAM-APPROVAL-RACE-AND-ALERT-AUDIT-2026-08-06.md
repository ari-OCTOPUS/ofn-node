---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, telegram, concurrency, alerts]
created: 2026-08-06
updated: 2026-08-06
created_by: agent
sources:
  - "3 parallel workflows, 2026-08-06 night: debate-vote-bug debugging, alert-pattern audit, wiring-completeness audit"
---

# رأیِ مالک نمی‌گیرد + آلارمِ گمراه‌کننده — سه ریشه، یک شب — ۲۰۲۶-۰۸-۰۶

مالک گزارش داد: «۱۴ ایده که باید تأیید کنم، چرا دکمهٔ تأیید ثبت نمی‌شود؟».
سه چیزِ **مستقلِ** واقعی پیدا و رفع شد — نه یک باگ، سه تا که هم‌زمان اثر
داشتند.

## ریشهٔ ۱ — کارتی که مالک می‌دید اصلاً دکمهٔ رأی نداشت

`wiring.py::brain_digest_beat` هر بار یک کارت پوش می‌کند که
`organ_dialogue.debate_survivor_card` را embed می‌کند — و آن تابع **عمداً**
`kb=[]` برمی‌گرداند (کامنتِ خودش). کارتِ واقعیِ تعاملی
(`mn:ap → render_debate_survivors`) کاملاً سالم بود — صفر رأیِ `dbt-*` در
audit.log ثابت کرد مالک هرگز آن صفحه را باز نکرده. کامیت `fe8eff0`.

## ریشهٔ ۲ — فیکسِ ریشهٔ ۱ خودش دکمهٔ مرده ساخت

فیکسِ اول یک دکمهٔ `mn:ap` به همان کارت اضافه کرد — ولی آن کارت از باتِ
**دیگری** می‌رود (`approval_channel` روی `@Robo2725_bot`)، نه باتی که
verb ِ `mn:ap` را می‌شناسد (`center.py` روی `@intergrade2725_Bot`) —
«تلهٔ دو-باتی»ِ مستندشده، این‌بار روی یک ماژولِ سوم که اسکنرِ
emitter-parity اصلاً نمی‌بیند. دکمهٔ cross-bot حذف شد؛ راهنمایی به متنِ
کارت منتقل شد. کامیت `b1a943a`.

## ریشهٔ ۳ (احتمالاً اصلی‌ترین) — رِیسِ دو-پروسه روی approval_store

`approval_store.py`'s قفلِ `threading.RLock` فقط **درون‌پروسه‌ای** بود.
با هر دو `OCTOPUS_WIRE_MISSION_CARD`/`OCTOPUS_WIRE_MISSION_APPROVAL` مسلح،
`goal_action_bridge.emit_mission_cards()` هر epoch tick داخلِ پروسهٔ
`organism.py` روی همان `approvals.json` می‌نویسد که `center.py` هم
approve/reject رویش می‌زند. بازتولیدشده مستقیم: organism در T0 یک
snapshot می‌خواند، center در T0.5 approve را ذخیره می‌کند (مالک تیکِ
موفقیت می‌بیند)، سیوِ organism در T1 کلِ فایل را با snapshot ِ T0
بازنویسی می‌کند — تأیید بی‌صدا به pending برمی‌گردد، **بدونِ هیچ خطا**.

فیکس: `opslib.LockedJson` (قفلِ فایلی، نه RLock) روی بخشِ بحرانی —
همان الگویی که `legs/raw_store.py`/`legs/ledger_core.py` از قبل دارند.
کامیت `2f8e795`. `organism.py` + `center.py` هر دو ری‌استارت شدند.

## بدهیِ تستِ نگهبان

خودِ نامِ تست (`t_o_single_consumer_process_invariant`) فقط رشتهٔ import
را چک می‌کرد، نه کانالِ واقعیِ نقض — یعنی این رِیس ماه‌ها سبز می‌ماند
بدونِ اینکه گاردش واقعاً چیزی بگیرد.

---

# آلارمِ «مغزِ پولی خراب شد» — سه نمونهٔ فیکس‌شده، یکی legs-locked

همان کلاسِ باگی که امشب زودتر در `model_router.py` (سقفِ روزانهٔ فوگو →
«broken») پیدا شد، در اسکنِ سراسری **دو بار دیگر** پیدا شد:

| فایل | وضعیت | کامیت |
|---|---|---|
| `_ops/cortex/model_router.py` | فیکس شد | `ea03a75` |
| `_ops/deep_think.py` | فیکس شد | `72fcd2a` |
| `_ops/self_patch.py` | فیکس شد | `39f9e29` |
| `_ops/legs/outbound_worker.py` | **فیکس نشد — `_ops/legs/**` قفل است** | — |

`outbound_worker.py:send_one()` روی هر کانالِ transport ِ **همیشه**
NOT_ARMED (طبقِ طراحی — «بقیه stubِ NOT_ARMED همیشگی است») یک آلارمِ
مالک‌محور می‌زند با متنی که شبیهِ خرابی است. §۰.۲ این جلسه صریح است:
هیچ‌کدِ زیرِ `_ops/legs/**` بدونِ تأییدِ مالک دست نمی‌خورد. **این ردیف
منتظرِ رأیِ مالک است**، فیکسِ آماده در ادامه.

**پیشنهادِ فیکس (اگر مالک تأیید کند):** قبل از آلارم چک شود
`out.get('status')=='NOT_ARMED'`؛ اگر بله، یا آلارم زده نشود یا با متنِ
اطلاعاتیِ متفاوت (مثلِ فیکس‌های بالا).

## دو موردِ دیگر — ریسکِ محتمل، نه باگِ تأییدشده

این دو مسیرِ **جایگزینِ** model_router را دور می‌زنند (پس فیکسِ امشب
رویشان اثر ندارد) و آلارمِ ژنریک روی هر Exception می‌زنند:

- `_ops/heart/doctor_setpoint.py::llm_refine()` — وقتی
  `OCTOPUS_HEART_DOCTOR_USE_ROUTER` خاموش است (پیش‌فرض)، مستقیم
  `DeepSeekClient(role='econ').complete()` صدا می‌زند.
- `_ops/budget/governor_epoch.py::allocate_llm()` — همان الگو با
  `OCTOPUS_GOVERNOR_USE_ROUTER`.

هر دو الان **زنده**اند (`ACTIVATION-HEART-DOCTOR.flag`/
`ACTIVATION-GOVERNOR-LLM.flag` مسلح). تصمیمِ درست معماری است نه فیکسِ
نقطه‌ای: یا این دو مسیر هم از model_router عبور کنند (و فیکسِ fugu_quota
را رایگان بگیرند)، یا خودشان جداگانه همان تشخیص را بگیرند. **نیازِ
تصمیمِ مالک.**

---

# نقشهٔ ریسکِ ری‌استارت (برای فیکسِ بعدی، سریع‌تر)

اسکنِ AST ِ import روی ۵ پروسهٔ اصلی نشان داد کدام ماژول‌ها چند پروسه را
لمس می‌کنند (یعنی فیکسِ آینده‌شان چند ری‌استارت لازم دارد):

- **هر ۵ پروسه:** `_ops/budget/opslib.py` — بالاترین ریسک، هر تغییری
  همه را می‌خواهد.
- **۴ از ۵ پروسه** (همه جز `miniapp_gateway.py`): `model_router.py` +
  خواهرانش (`fugu_quota.py`, `context_fence.py`, `local_llm.py`,
  `route_scorer.py`, ...) + `budget/circuit_breaker.py`,
  `organ_gate.py`, `flag_drift.py`, `events.py`, `heart/fuel_meter.py`.
- **۲ از ۵** (`organism.py` مستقیم، `center.py` غیرمستقیم):
  `wiring.py` — کمتر از حدسِ اولیه.

میتودولوژی: استاتیک (AST)، نه ردیابیِ زمانِ اجرا — importِ پشتِ فلگ ممکن
است هرگز واقعاً load نشود؛ لیست را سقفِ بالا بخوان نه تضمینِ قطعی.

---

# یافته‌های جانبیِ سیم‌کشی (کم‌خطر، برای بک‌لاگ)

- `OCTOPUS_WIRE_RUNNER_APPLY=1` مسلح ولی **صفر خواننده** در کلِ کد —
  no-op محض.
- `_ops/token_meter.py` (ساخته‌شده ۰۸-۰۴، تست دارد) **صفر صداکنندهٔ
  تولیدی** — نه در organism، نه cortex، نه telegram_center.
- `OCTOPUS_WIRE_MINING_OS=1` مسلح (پاسِ گروهیِ ۰۸-۰۵) با وجودِ کامنتِ
  عمدیِ ۰۸-۰۲ «MINING_OS خاموش می‌ماند (بدونِ نودِ زنده، اسکلتِ صادقانه)»
  — دو تصمیم هرگز با هم چک نشدند.
- `question_budget.answer_callback_data()` قراردادِ `qb:ans:<id>`
  مستند می‌کند که هیچ کدِ تولیدی نمی‌سازد — کدِ مرده، نه دکمهٔ مرده.
- سیستمی (نه باگ): بعد از مسلح‌شدنِ `OCTOPUS_WIRE_CB_TOKEN` (۰۸-۰۳)، هر
  کارتِ قدیمی‌ترِ بدونِ توکن که هنوز روی صفحهٔ تلگرامِ مالک باز مانده
  برای همیشه «توکنِ نامعتبر» می‌دهد.
- `flag_drift.is_secret_name()` رشتهٔ «TOKEN» را substring می‌گیرد، پس
  `OCTOPUS_WIRE_CB_TOKEN` (یک فلگِ boolean، نه secret) از مقایسهٔ drift
  کور می‌ماند — severity کم چون مسیرِ توکن جداگانه تأیید شد.
- `approval_store` دو نقصِ کوچکِ دیگر (severity: low): خواندن‌ها
  (`get`/`load_pending`/`summary`) هرگز قفل نمی‌گیرند (نه read-consistency
  حتی درون‌پروسه)؛ گاردِ id-تکراری فقط سطلِ pending را می‌بیند، نه
  approved/rejected/done.

مرتبط: [[07 - Knowledge/شناخت-اختاپوس/18-STALE-TEST-BACKLOG-2026-08-06|18-STALE-TEST-BACKLOG]]
(همان شب، بدهیِ تستِ کهنه — موضوعِ جدا).
