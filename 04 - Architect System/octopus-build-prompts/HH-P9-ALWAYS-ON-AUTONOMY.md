---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, autonomy, boot, work-pump]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[01 - Dashboard/HANDOFF]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P9 — همیشه-روشنِ خودگردان: «لپ‌تاپ روشن شد → بتپد → کارِ واقعی → حافظه → ارتقا»

> vision مالک (2026-07-10): «لپ‌تاپ روشن شد خودش ضربانش را بر اساسِ همهٔ دیتاها نظم بدهد و شروع کند؛ طبقِ این ضربان سرچِ واقعی، APIِ واقعی، یادگیریِ واقعی و خاطرات — مثل معماری شرکت‌های بزرگ — یادش بماند و بر اساسِ نقشه‌ریزیِ درونی‌اش ارتقا بدهد.»

## نگاشتِ vision به معماری (چه ساخته شد، چه مانده)

| حلقه | قطعه | وضعیت |
|---|---|---|
| **بیدارشدن** | `RUN-ORGANISM.bat` (ضدِ دوبار-روشن) + `watchdog.py` (منطقِ احیا، STOP همیشه برنده) + **`organism-watchdog.ps1` (نو — runner)** | ✅ ساخته؛ ثبتِ ۲ Scheduled Task = **فقط مالک** (بند ۴) |
| **تپیدن** | قلبِ HH-P0..P7 (سایه؛ زنده پشتِ predicateِ ۸شرطی) | ✅ ساخته (جلسه ۴۶) |
| **کار طبقِ ضربان** | **`_ops/heart/work_pump.py` (نو)** — پنجره‌های کار = periodِ سایه؛ هر پنجره ≤۱ task از planِ درونی | ✅ ساخته؛ پشتِ `OCTOPUS_WIRE_HEART_WORK` (خاموش) |
| **کارِ $0 (الان)** | health-snapshot · gap-report از حافظهٔ مدرسه | ✅ زنده به‌محضِ رأی |
| **کارِ paid (سرچ/LLM)** | ردهٔ paid در همان پمپ — دوقفله: تاریخ ≥ 2026-07-21 + `ACTIVATION-WORK-LLM.flag` + عبورِ lazy از organ_gate (I2) | 🔒 ساختار آماده؛ provider = رأی مالک (بند ۳) |
| **حافظه (مثل شرکت‌ها)** | ledger hash-chained (رویداد) + consolidation/BCM/latent (تحکیم/فراموشی) + school (آگاهی) + germline (بک‌اپ) + work-log (نو: ممیزیِ هر کار) | ✅ موجود — پمپ به آن می‌نویسد نه جای آن |
| **ارتقا از نقشهٔ درونی** | `work-plan.json` (نو: نقشهٔ ماشین‌خوانِ کار) + Doctor RFC → human-append merge (موجود) | ✅ v1؛ گامِ ۵: Doctor برای plan تغییر propose کند |

## گام‌های اجرا (به ترتیب)

1. **[مالک — ۲ دقیقه، بعد از merge]** ثبتِ دو تسک (یک‌بار):
   - `schtasks /Create /TN "OCTOPUS-Organism" /SC ONLOGON /TR "F:\backup\_ops\RUN-ORGANISM.bat"`
   - `schtasks /Create /TN "OCTOPUS-Watchdog" /SC MINUTE /MO 5 /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\organism-watchdog.ps1"`
   - نتیجه: روشن‌شدنِ لپ‌تاپ = تولدِ خودکار؛ کرش = احیای ≤۵ دقیقه (STOP همیشه حاکم؛ first-birth طبقِ INC-1 قبلاً انجام شده).
2. **[مالک — رأی]** `OCTOPUS_WIRE_HEART=1` + `OCTOPUS_WIRE_HEART_WORK=1` + restart → ضربانِ سایه + پمپِ $0 شروع می‌کند (health/gap-report؛ log در `state/pulse/work-log.jsonl`).
3. **[مالک — تصمیمِ provider]** سرچِ واقعی: کدام provider؟ (پیشنهاد: یک SEARCH API ارزان با کلید در `.env`؛ ثبتِ ارگانِ `SEARCH_WEB` در budgets.yaml با floor کوچک — SoT human-gated). LLMِ یادگیری: همان DeepSeek econ موجود.
4. **[ایجنت — بعد از 2026-07-21 و پرچمِ مالک]** پیاده‌سازیِ دو executorِ paid در work_pump:
   - `search`: query از gap-report (کم‌آگاه‌ترین موضوع) → provider (کلید از env، هرگز echo) → نتیجه به `10 - Telegram processing/Raw`-سبک vault note یا مستقیم به afferent → school یاد می‌گیرد. هر call: `organ_gate.reserve/settle` روی ارگانِ SEARCH_WEB.
   - `llm_learn`: چکیده‌سازیِ یافته‌ها با client econ → append به نوتِ دانش (`07 - Knowledge`، created_by: agent + sources) + consolidation منبعِ نو. هر call گیت‌خورده.
   - تستِ هر دو با client تزریقی/fake (بدونِ شبکه) + سوییت سبز.
5. **[ایجنت — فازِ بعد]** ارتقای خودگردانِ نقشه: Doctor per-epoch بتواند برای `work-plan.json` تغییر propose کند (RFC → کارتِ تلگرام → human-append) — نرخِ تکامل = نرخِ حضورِ انسان، طبقِ قانون.

## ناوردی‌ها (بی‌تغییر)

kill-switch مطلق (STOP → پمپ ساکت) · FREEZE → هیچ کار · هر پنجره ≤۱ task (ضدِ طوفان) · paid فقط دوقفله + organ_gate (I2) · پمپ فقط `state/pulse/*` خودش را می‌نویسد؛ حافظهٔ واقعی از مسیرهای موجود (afferent/consolidation/ledger) پر می‌شود · تولد/احیا = ابزارِ مالک (LifeDoctrine §۴).
