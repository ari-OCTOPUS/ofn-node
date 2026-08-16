# AGENT-EXECUTION-PLAN — Worker Agent 2026-08-16

> مبنای نرم: `OCTOPUS Implementation Directive` (مالک: Armin · مدل دستور: DeepSeek V4 Flash)
> مبنای سخت: واقعیتِ اندازه‌گیری‌شده در [[AGENT-INVENTORY-2026-08-16]] — جایی که طرح با واقعیت تفاوت دارد، واقعیت برنده است (R7) و تفاوت ثبت می‌شود.
> قواعد: TCB ممنوع (R1) · fail-closed (R2) · بدون delete/overwrite مخرب (R4) · ارگانیسم بدون restart (R5) · commit مرحله‌ای با stage صریح (R6) · trace_id همه‌جا (R8) · تک‌نویسنده (R10).

## ترتیب فازها

| # | فاز | خروجی | وضعیت |
|---|---|---|---|
| ۰ | inventory + plan | AGENT-INVENTORY + همین فایل + commit | ✅ انجام شد |
| ۱ | decisions registry | `04-SYSTEMS/DECISIONS-REGISTRY.yaml` (۸ تصمیم) | بعدی |
| ۲ | event spine wired | تست تأیید `test_spine_wired.py` + رأی tracked — spine در تولید **از قبل زنده است** (۴۷۷۰ رویداد)؛ کد جدید: صفر | – |
| ۳ | HEARTSTATE audit fix + OFF heartbeat | patch در `flag_drift.py` (گزارش فایل‌مسلح در snapshot) + `module.heartbeat` در taxonomy `events.py` + `emit_off_heartbeat()` + فراخوان هر ۱۰ beat + `test_off_heartbeat.py` | – |
| ۴ | life currency | `_ops/heart/life_currency.py` + `_ops/heart/budget_transfer.py` + تخصیص در beat GREEN + `test_life_currency.py` | – |
| ۵ | provider router | `_ops/cortex/provider_adapter.py` (Fugu→DeepSeek→GLM→Ollama + downgrade پله‌ای A2→propose) + اتصال `model_router.py` (بدون تغییر مسیر paid زنده) + `test_provider_router.py` | – |
| ۶ | dual brain | `_ops/control_plane/dual_brain.py` (وتوی متقابل + consensus halt + دامنه‌ها) + اتصال supervisor/approvals + `dual_veto_recorded` در spine + `test_dual_brain.py` | – |
| ۷ | wire 4d_system W1 | دسترسی read-only داده به 4d_system + تست — فقط W1؛ W2–W5 منتظر رأی مالک | – |
| ۸a | intel spine | پرچم از قبل ON در env — کار: تأیید خروجی آداپتورها + تست، نه init جدید | – |
| ۸b | afferent | سیم‌کشی sensory_bus به beat (پشتِ پرچم verdict) + تست | – |
| ۸c | synapse | `SYNAPSE_ENABLED` از مسیر رأی + فراخوان sense_once در beat + تست | – |
| ۸d | chord | پرچم + فراخوان + تست | – |
| ۸e | action bridge | runtime caller (پرچم از قبل ON ولی مسیر مرده) + A2=auto/A4=owner + downgrade fallback + تست | – |

## قواعد اجرایی من

1. **stage صریح** در هر commit — درخت dirty مالک دست نمی‌خورد.
2. ویرایش فایل‌های داغ (wiring.py / organism.py / events.py) فقط **additive**؛ پروسه‌های در حال اجرا تا restart بعدی تغییری نمی‌بینند — همهٔ اثرهای جدید پشتِ پرچمِ پیش‌فرض-خاموش یا additive-safe.
3. فلگ‌های جدید از `owner-verdicts.yaml` (tracked) — نه `.env` (ممنوع با `.agentignore`).
4. هر فاز: اول تست (سبک tmp_path/monkeypatch موجود)، بعد commit `agent-checkpoint: phase N — …`.
5. اگر ابهام ایمنی/حاکمیت: توقف + سؤال در `AGENT-REPORT.md` (§۵ دستورالعمل).
6. گزارش هر فاز در `04-SYSTEMS/AGENT-REPORT.md` (قرارداد خروجی §۵ دستورالعمل).

## ریسک‌های شناخته‌شده

- **هم‌نویسی با پروسه‌های زنده:** فقط فایل‌های جدید یا بخش‌های additive؛ هرگز state زنده را بازنویسی نمی‌کنم.
- **دو heartbeat-سنج:** beat_scheduler (۴۱۲۵) vs organism (۳۸۴۱۰) — تخصیص بودجه فاز ۴ به شمارندهٔ organism loop می‌چسبد (نه shadow scheduler) تا با cardiac-budget.json سازگار بماند.
- **فاز ۸ و پایش:** فعال‌سازی هر ماژول خفته نیازمند پایش ۱ هفته‌ای مالک است؛ من سیم‌کشی + تست را می‌سازم، روشن‌کردن دائمی با مالک.
