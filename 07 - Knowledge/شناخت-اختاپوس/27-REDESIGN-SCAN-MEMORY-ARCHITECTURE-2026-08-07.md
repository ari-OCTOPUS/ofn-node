---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, memory, redesign, fugu, architecture-scan]
created: 2026-08-07
updated: 2026-08-07
created_by: agent
sources:
  - "8-agent Workflow scan (7 phases + synthesis), 2026-08-07, F:/backup/_ops live tree, 548 tool calls, ~1.83M tokens"
  - "commit a7daa7b (5 fixes applied on master), 2026-08-07"
  - "Desktop\\OCTOPUS-REDESIGN-SCAN-2026-08-07\\ (فاز-۱..۷.md + REDESIGN-PROPOSAL.md)"
---

# اسکنِ بازطراحیِ حافظه‌محور — مگاپرامپت v2 — ۲۰۲۶-۰۸-۰۷

> مگاپرامپتِ مالک: کلِ اختاپوس را با تزِ «اهرمِ واقعی حافظه است، Fugu خودش
> ارکستراتور است، دورش ارکستراسیونِ اضافه نساز» بازممیزی/بازطراحی کن، ۸ ستونِ
> معماریِ حافظهٔ ۲۰۲۶ (CoALA، Zep/Graphiti، A-MEM، Generative-Agents، Letta،
> ACT-R forgetting، MemGuard، MemRL) را بسنج، ۷ فاز، هیچ فایلی جا نماند.

## نتیجهٔ کلی

تز **جزئاً تأیید شد**. هستهٔ پولی-معماری (model_router.py→organ_gate→money_gate→
circuit_breaker) دقیقاً یک درِ واحدِ منضبط است. حافظه — برخلافِ فرضِ بدبینانهٔ
اولیه — از سالم‌ترین بخش‌های ارگانیسم است: BCM/Hebbian-decay/consolidation-fold
هر سه زنده (ستون ۶، فراموشیِ کنترل‌شده)، retrieval_router واقعاً ۲۹ خاطره را
narrow می‌کند (نه صرفاً veto — تمایزِ مهم)، recall_trend یک سنجهٔ خودآگاهیِ نادر با
۱۰۳ نمونهٔ زنده دارد. اما دورِ همین هسته، الگویِ «ساختن دو بار» بارها دیده شد:
debate_loop.py (Thinker/Verifier محلی روی مدلِ ۱.۵B، دقیقاً کارِ Fugu)، governor.py
(tier-router موازیِ model_router، armed ولی صفر caller — کشفِ مستقلِ دو فاز)، دو
drawdown_guard هم‌نام، دو صفِ HITL، دو سیستمِ لاگِ رویداد ناسازگار.

## ۸ ستونِ حافظه — حکمِ نهایی

۱ CoALA: زنده (برچسب‌گذاریِ اسمی ناقص) · ۲ Zep/Graphiti: ناقص (زمان‌مندی هست، گراف نیست)
· ۳ A-MEM: ناقص (idea_graph + consolidation موازی، وصل‌نشده) · ۴ Retrieval+reflection:
زنده/ناقص (بازیابی زنده، reflection غایب) · ۵ Letta sleep-time: نیمه (چرخهٔ خواب
زنده، سطحِ نمایشی مرده) · ۶ ACT-R forgetting: **زنده — سالم‌ترین ستون** · ۷ MemGuard:
ناقص (گاورننسِ نوشتن قوی، مصرفِ خروجی صفر) · ۸ MemRL: ناقص (مشاهده‌پذیر، اثرگذاریِ
رفتاری اثبات‌نشده).

جزئیاتِ کامل + کوچک‌ترین diff برایِ هر ستون: `Desktop\OCTOPUS-REDESIGN-SCAN-2026-08-07\REDESIGN-PROPOSAL.md`.

## فیکس‌های اعمال‌شده (کامیت `a7daa7b`)

- `heart/pulse_arbiter.py::persist()` — written روی دیسک همیشه false بود (همان
  کلاسِ باگِ heartstate.py که قبلاً فیکس شده بود، به این خواهر سرایت نکرده بود).
- `dark_capabilities.py` — فیلترِ is_secret_name رویِ mentioned هم اعمال می‌شد،
  پس OCTOPUS_HTTP_AUTH/OCTOPUS_WIRE_CB_TOKEN (دو گیتِ امنیتیِ زنده) به‌غلط
  «مسلح ولی بی‌خواننده» گزارش می‌شدند.
- `wiring.py::apply_profile()` — یک `return profile` تکراری/مرده حذف شد.
- `durable_journal.py` + `agi2027_control/runtime.py` — دو کامنت/docstringِ کهنه
  که با کدِ زندهٔ امروز تناقض داشتند، به‌روز شدند.
- هر ۵ فیکس: تست + mutation-test (git-stash trick) + CRLF-check + رگرسیون.

## دو موردِ مهم که **عمداً فیکس نشد**

۱. **FUGU_DAILY_CALL_CAP=60** — امروز از ۰۹:۴۷ تا ۲۰:۳۰ (>۱۰ ساعت) هر تماس رد شد
   (هزینه=۰، subscription=max). ولی `OCTOPUS-flags.cmd:376` نشان داد این عمدی بود
   («از ۳۰۰ به ۶۰ سفت شد — ترمزِ عملیاتی نه پولی»)، نه فراموشی. **سؤالِ بازِ مالک:**
   آن ترمز هنوز با شاهدِ امروز توجیه دارد؟
۲. **ask_brain._context_for()** — پیشنهادِ اولیهٔ اسکن (continuity با recent_turns)
   مستقیماً ناقضِ مرزِ مستندِ خودِ فایل بود («هیچ متنِ مالک در context تکرار
   نمی‌شود جز خودِ سؤال»). رد شد؛ سؤالِ باز برایِ مالک در REDESIGN-PROPOSAL.md.

هر دو نمونهٔ خوبی از «اسکنِ اول شواهد پیدا کرد، بررسیِ فیکس زمینهٔ تصمیمِ عمدیِ
موجود را هم پیدا کرد» — درسِ آشنا: هم‌زمانیِ شواهد علیت نیست، و ماژولِ تست‌شده
می‌تواند صداکنندهٔ صفر داشته باشد بدونِ اینکه باگ باشد.

## پوشش

۲۳۳۵ فایلِ ردیابی‌شدهٔ `_ops` — ۷۴ در `legs/**` (فقط‌خواندنیِ سخت، دست‌نخورده) +
۱۲۶۱ زیرِ claim فازهای ۱-۶ + ۱۰۰۰ فازِ ۷ (residual، محاسبه‌شده نه حدس‌زده). جزئیاتِ
کامل + هر finding: `Desktop\OCTOPUS-REDESIGN-SCAN-2026-08-07\فاز-۱.md` تا `فاز-۷.md`.

مرتبط: [[17-RAG-MEMORY-DEEP-SCAN-2026-08-06]] · [[24-COGNITION-SYNC-AUDIT-2026-08-07]] ·
[[25-INTERACTION-SURFACE-AND-QUOTA-DEAD-END-2026-08-07]] · [[26-OPERATIONS-MONEY-SCAN-2026-08-07]]
