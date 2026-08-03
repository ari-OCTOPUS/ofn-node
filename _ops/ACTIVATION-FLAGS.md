# رجیستریِ `ACTIVATION-*.flag` — رأی‌های مسلح‌سازیِ مالک

**نسخه:** 2026-08-03 · **گامِ ۷ ِ [[UNIFICATION-DESIGN-2026-08-03]]** · **گاردِ اجرایی:** `_ops/tests/test_activation_flag_presence.py`

> این سند فهرستِ آرزو نیست؛ هر ردیفش با AST از `_ops/**/*.py` و با `stat()` از دیسک اندازه گرفته شده و
> یک تست همان سه مجموعه (منبع / دیسک / این جدول) را با هم برابر نگه می‌دارد. اگر ردیفی دروغ بگوید،
> `test_activation_flag_presence` قرمز می‌شود — نه اینکه در مرورِ کد کشف شود.

---

## چرا این فایل وجود دارد

سه واقعیتِ اندازه‌گیری‌شده که با هم یک تله می‌سازند:

1. **این فایل‌ها در گیت نیستند.** `.gitignore` خطِ `_ops/ACTIVATION-*.flag` را دارد
   (`git check-ignore -v` تأیید می‌کند). یعنی هیچ رأیِ مسلح‌سازیِ مالک **تاریخچه ندارد**؛
   حذف شود، برنمی‌گردد و هیچ diff ای نشانش نمی‌دهد. تنها ردِ tracked ِ این رأی‌ها همین سند است.
2. **دستِ‌کم یکی از آن‌ها هر ضربان می‌نویسد.** `_ops/state/pulse/heartstate-latest.json`
   (در همین جلسه `ts` اش از `2026-08-03T16:01:30` به `16:04:16` جلو رفت و `written: true` دارد)
   نویسنده‌اش `heart/heartstate.py::persist` است که پشتِ `heart/heartstate.py::enabled` قرار دارد.
3. **`enabled()` دو راهِ مسلح‌سازی دارد و ممیزیِ فلگ فقط یکی را می‌بیند.** (بخشِ بعد.)

نتیجه: یک ایجنتِ «پاکسازی» به فایلی می‌رسد که از `2026-07-23` دست‌نخورده است، «مرده» می‌خواندش،
منتقلش می‌کند — و یک نویسندهٔ هر-ضربان **بی‌صدا** می‌میرد. سنگ‌قبرِ نثری جلوی این را نمی‌گیرد؛ تست می‌گیرد.

---

## ⚠️ هشدارِ اصلی — `heartstate` با **فایل** مسلح است، نه با env

`heart/heartstate.py::enabled` این است (نامِ نماد، نه شمارهٔ خط):

- اول env ِ `HEARTSTATE_SHADOW` را با allowlist ِ truthy می‌خواند؛
- **وگرنه** `heart/heartstate.py::_FLAG_FILE` یعنی `_ops/ACTIVATION-HEARTSTATE.flag` را `exists()` می‌کند.

و اندازه‌گیری روی درختِ زنده:

- نامِ `HEARTSTATE_SHADOW` در **هیچ‌کدام** از ۴ فایلِ `_ops/state/flags-loaded-*.json` نیست.
- فایلِ `_ops/ACTIVATION-HEARTSTATE.flag` **هست** (۸۵ بایت، mtime = `2026-07-23`).
- پس مسیرِ زنده **شاخهٔ فایل** است.

پیامدهایی که باید نوشته شوند چون کسی دوباره روی‌شان می‌لغزد:

- **هر ممیزیِ مبتنی‌بر `flags-loaded-*.json` این قابلیت را «خاموش» گزارش می‌کند در حالی که می‌نویسد.**
  گزارشِ «خاموش» دربارهٔ env درست است و دربارهٔ رفتار غلط.
- **حتی docstring ِ صداکننده هم همین را اشتباه می‌گوید.** `_ops/wiring.py::heartstate_beat`
  می‌نویسد «پشتِ `HEARTSTATE_SHADOW` (پیش‌فرض خاموش)» — ولی خودش `_hs.enabled()` را صدا می‌زند
  که شاخهٔ فایل را هم دارد. سند از کدش عقب افتاده؛ رفتارِ زنده «روشن» است.
- **mtime ِ این فایل شاهدِ تازگی نیست.** فایلِ مسلح‌سازی یک‌بار ساخته می‌شود و دیگر لمس نمی‌شود؛
  کهنه‌بودنِ mtime دربارهٔ «آیا کسی می‌خواندش؟» هیچ نمی‌گوید. به زبانِ `_ops/provenance.py`:
  یک `Mtime` همیشه `Mode.UNKNOWN` با `reason="mtime-only"` می‌دهد — و همان تست این را قفل کرده
  تا کسی دوباره از mtime نتیجهٔ «مرده» نگیرد.

**قاعده:** هیچ `ACTIVATION-*.flag` ای بر اساسِ ظاهرِ کهنه‌اش منتقل/حذف نمی‌شود.
تنها تغییرِ مجاز = رأیِ صریحِ مالک، و همان لحظه یک ردیفِ این جدول عوض می‌شود.

---

## جدولِ رجیستری

ستونِ **حالت** واژگانِ کنترل‌شده دارد و تست می‌خواندش: `RAISED` = فایل روی دیسکِ زنده هست،
`CLOSED` = عمداً نیست (گیتِ بسته). ستونِ **نمادِ خواننده** باید در اسکنِ AST پیدا شود وگرنه تست قرمز است.

| فایل | چه چیزی را مسلح می‌کند | نمادِ خواننده | شکلِ گیت | حالت |
|---|---|---|---|---|
| `ACTIVATION-C6-RESEARCH.flag` | تریگرِ پژوهش/خودترمیمیِ C6 | `c6_trigger.py::ACT_FLAG` | تک‌قفله `exists()` | RAISED |
| `ACTIVATION-CODE-AUTONOMY.flag` | اکچوایتورِ سطح A (اعمالِ پچ به کد) | `cortex/code_autonomy.py::ACTIVATION` | تک‌قفله `exists()` + نبودِ `STOP-CODE-AUTONOMY`؛ `arm_gate.py::DANGEROUS` توکنِ دومِ تازه می‌خواهد | RAISED |
| `ACTIVATION-CORTEX-PAID.flag` | لِینِ LLM ِ پولیِ کورتکس | `cortex/model_router.py::ACT_CORTEX_PAID` | دوقفله `opslib.live_gate_open` | RAISED |
| `ACTIVATION-DEBATE.flag` | حلقهٔ مناظرهٔ زنده (نه stub ِ آفلاین) | `budget/opslib.py::ACT_DEBATE` | دوقفله `opslib.live_gate_open` | RAISED |
| `ACTIVATION-GO-LIVE.flag` | بایپسِ سراسریِ سپرِ تاریخِ فاز −۱ | `budget/opslib.py::GO_LIVE_FLAG` | تک‌قفله `exists()` درونِ `live_gate_open` | RAISED |
| `ACTIVATION-GOVERNOR-LLM.flag` | گاورنرِ LLM ِ اپاک بودجه | `budget/opslib.py::ACT_GOV_LLM` | دوقفله `opslib.live_gate_open` | RAISED |
| `ACTIVATION-HEART-DOCTOR.flag` | setpoint ِ دکترِ قلب | `heart/doctor_setpoint.py::ACT_HEART_DOCTOR` | دوقفله `opslib.live_gate_open` | RAISED |
| **`ACTIVATION-HEARTSTATE.flag`** | **نوشتنِ `_ops/state/pulse/heartstate-latest.json` هر ضربان** — ↑ هشدارِ بالا | `heart/heartstate.py::_FLAG_FILE` | تک‌قفله `exists()`، **بدونِ سپرِ تاریخ** | RAISED |
| `ACTIVATION-PULSE-ARBITER.flag` | persist ِ آربیترِ پالس (`arbiter-latest.json` / `arbiter-shadow.jsonl`) | `heart/pulse_arbiter.py::ACT_ARBITER` | دوقفله `opslib.live_gate_open` | CLOSED |
| `ACTIVATION-PULSE.flag` | سایهٔ قلب (`heart/shadow.py`) | `heart/shadow.py::ACT_PULSE` | دوقفله `opslib.live_gate_open` | RAISED |
| `ACTIVATION-REPLICATION.flag` | پیشنهاددهیِ زندهٔ replication | `budget/opslib.py::ACT_REPLICATION` | دوقفله `opslib.live_gate_open` | RAISED |
| `ACTIVATION-RESEARCH-EARLY.flag` | overrideِ زودهنگامِ سپرِ تاریخ برای مسیرِ پژوهشِ پولی | `cortex/model_router.py::ACT_RESEARCH_EARLY` | تک‌قفله `exists()` | RAISED |
| `ACTIVATION-SELF-IMPROVE-AUTO.flag` | خودبهبودیِ **خودکار** (بدونِ تپِ مالک) | `cortex/improve.py::ACT_AUTO` | تک‌قفله `exists()` | RAISED |
| `ACTIVATION-WORK-LLM.flag` | لِینِ LLM ِ پمپِ کار | `heart/work_pump.py::ACT_WORK_LLM` | دوقفله `opslib.live_gate_open` | RAISED |

`_ops/ACTIVATION-GOVERNOR-LLM.flag.off` عمداً در این جدول نیست: پسوندش `.flag` نیست، هیچ خواننده‌ای
ندارد و تنها فایلِ **tracked** ِ این خانواده است (یک یادگارِ خاموشِ ۲۰۲۶-۰۷-۱۰).

---

## گاردی که این سند را صادق نگه می‌دارد

`_ops/tests/test_activation_flag_presence.py::audit` سه مجموعه را می‌سازد و اختلافشان را گزارش می‌کند:

| یافته | یعنی |
|---|---|
| `MISSING-RAISED` | جدول می‌گوید RAISED ولی فایل روی دیسک نیست ← **کسی یک فایلِ باربر را کشت** |
| `WRONGLY-CLOSED` | جدول می‌گوید CLOSED ولی فایل هست ← رأیِ تازهٔ مالک ثبت نشده |
| `UNREGISTERED-REF` | کد فلگی را می‌خواند که ردیف ندارد ← اهرمِ تازه بدونِ سند |
| `UNDECLARED-ON-DISK` | فایلی مسلح است که هیچ ردیفی ندارد |
| `STALE-REGISTRY-ROW` | ردیفی که هیچ خواننده‌ای در `_ops` ندارد |
| `UNKNOWN-READER` | ستونِ نمادِ خواننده در اسکنِ AST پیدا نشد ← سند نامِ نمادِ مرده می‌برد |
| `UNPARSED-SOURCE` | فایلِ پایتونی که اسکنر نتوانست بخواند ← نقطهٔ کورِ اسکن |

اسکنِ منبع عمداً `_ops/tests/` و `_ops/patch_backups/` را رد می‌کند: اولی فلگ‌های خیالی
(`ACTIVATION-TEST.flag`، `ACTIVATION-X.flag`، `ACTIVATION-ABSENT.flag` در `tests/test_go_live.py`)
به‌عنوان فیکسچر می‌سازد و دومی رونوشتِ بایگانیِ کد است — هیچ‌کدام خوانندهٔ تولیدی نیستند.

**وقتی مالک رأیش را عوض کرد:** فایل را خودش بساز/بردار، بعد ستونِ «حالت» همان ردیف را
`RAISED`↔`CLOSED` کن. تست تا آن لحظه قرمز می‌ماند — همین عمدی است، چون این جدول تنها جایی است
که آن رأی tracked می‌شود.
