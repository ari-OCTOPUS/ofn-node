# LIVE CHECKPOINT — Fugu — 2026-07-25 (به‌روزرسانی چهارم: quick gate کامل سبز)

> هدف: اگر جلسه قطع شد، ایجنت بعدی دقیقاً از همین‌جا ادامه دهد. درخت زنده است؛ اعمال موازی ممنوع.

## وضعیت lane قبلی (C2/C3/Router) — بسته‌شده با شاهد

- سوئیت کامل: **۲۹۲ فایل، exit=0** (قبل از موج جدید).
- commitها هنوز ساخته نشده‌اند (Fugu shell/git ندارد) — دستورهای staging در EXECUTION-REPORT.

## موج جدید (megaprompt T1..T8) — اعمال‌شده، quick verify سبز

| کار | تغییر | تست |
|---|---|---|
| T1 int('متوسط') | `_ops/organ_dialogue.py` — نگاشت برچسب→عدد دو‌زبانه + fail-soft؛ ۳۴۸ کرش بسته می‌شود | `test_organ_dialogue_digest.py` |
| T3 self-heal کور | `_ops/chrono.py` — `_record_leg_failure` (phi-timeout → state/legs/<leg>-last-failure.json + غنی‌سازی selfheal-events/task.blocked) · `_ops/wiring.py` — `_record_leg_error` (استثنا → last-error.json) | `test_leg_failure_reason.py` |
| T4 سنجه‌های دروغ | `_ops/heart/producers.py` — گارد self_referential (metronome>0.9 → authoritative=false) + حذف clampِ Δ (منفی منتشر می‌شود) + gate0 با Δ≤0 بسته — همه پشتِ `OCTOPUS_HEART_HONEST_PULSE` (در flags.cmd **=1** شد، §۳) | `test_heart_honest_pulse.py` |
| T7 لوله‌های خاموش | `03 - Projects/Accounting/personal/categorize-config.json` — اسکلت معتبرِ خالی ساخته شد · `_ops/legs/journal_bridge.py` — هشدار فقط برای غایب/ناخوانا (نه خالیِ معتبر) | تست journal_bridge موجود در سوئیت |
| T8 صفِ RFC | `_ops/doctor/doctor.py` — dedupe روی متنِ گلوگاه + `_reconcile_input_validity` (σ/FREEZE مرده → stale-input) + submit idempotent | `test_doctor_rfc_stale_dedup.py` |

**مهم:** T1/T3/T4/T8 در کدِ دیسک اعمال شده‌اند ولی پروسه‌های زنده هنوز کدِ قدیمی را اجرا می‌کنند — اثر واقعی = **پس از restart** (فقط بعد از سبزشدنِ سوئیت، با RESTART-ORGANISM.bat).

## یافته‌های تشخیصی (بدونِ تغییرِ کد)

- **T5/KeyError: 'text'**: قبلاً در ۲۰۲۶-۰۷-۱۸ فیکس شده (defensive `.get()` در `debate_loop.py:~196-202`) — ۷۲ هشدار تاریخی است، نه زنده.
- **T5/price_in/price_out**: علتِ واقعیِ «governor llm failed» نبودِ کلید نیست — نبودِ قیمتِ قفل در budgets.yaml است → VERDICT_QUEUE.
- **T6 بودجهٔ ضربان**: تناقضی نیست — سه ساعتِ متفاوت: chrono beat (نخِ ۶۰s) · تیکِ ارگانیسم (~۴۲.۴s از bio_rhythm با mass=1) · arbiter (۹۰۰s پس از اتمامِ بودجه). cap=288 برای تیکِ ۵دقیقه‌ای طراحی شده ولی تیکِ واقعی ۴۲.۴s است → بودجه ~۳.۴h تمام می‌شود → بقیهٔ روز resting/900s. daily_cap عوض نشد (قفلِ megaprompt) → VERDICT_QUEUE.
- **T7/consolidation «neural_stack is None»**: تاریخی (۲۰۲۶-۰۷-۱۰، ۴ بار، متوقف‌شده) — اقدام لازم نیست.
- **T7/memory.db یک سطر**: reachability تأیید — نویسنده وصل است ولی فلگ‌های تولیدکننده (HARVEST/EMAIL) خاموش‌اند → صندوق خالی → تقاضا صفر. شاهد: ORGANISM-STATE.lead_discovery sensed=0 همیشه.

## T2 هم اعمال شد (سه لایه، پشتِ OCTOPUS_HONEST_OUTCOMES، پیش‌فرض خاموش)

- `_ops/cortex/goal_directed.py` — لایهٔ ۱ (نویسنده): `_dedupe_intents` (قدیمی‌ترین baseline برنده) · لایهٔ ۳ (معنا): `_vote_keys` (درون‌زاد=total_discoveries رأی نمی‌دهد ولی در endogenous_delta لاگ می‌شود).
- `_ops/cortex/improve.py` — لایهٔ ۲ (خواننده): مخرجِ improvement_rate = نیتِ متمایز با آخرین رأی per key.
- تست: `test_honest_outcomes.py` (dedupe، عدمِ تناقض، درون‌زاد=False، مخرجِ متمایز، None).
- **فلگ عمداً روشن نشد** — OCTOPUS_HONEST_OUTCOMES در فهرستِ §۳ نبود → VERDICT_QUEUE.

## شاهد quick gate مالک — کامل سبز

اجرای `VERIFY-QUICK-2026-07-25.ps1` پس از normalization بایتی CRLF:

- syntax: PASS
- C2 + C6 propose-only: PASS
- C3: ۵/۵ PASS
- Router dark config، شاملِ نبود lone-LF و CRCRLF: PASS
- T1: PASS
- T3: PASS
- T4: PASS (Δ منفی و gate0 بسته)
- T8: PASS
- T2: PASS
- خروجی نهایی: `ALL QUICK CHECKS PASSED`

## اقدام بعدی واحد

```powershell
python -X utf8 "F:\backup\_ops\tests\run_all.py"
```

انتظار شمار فعلی: baseline قبلی ۲۹۲ + پنج فایل تست ثبت‌شده = **۲۹۷ فایل**. فقط شمار صریح و exit code معتبر است. پس از suite کامل: اسناد VERDICT_QUEUE/ARCHITECTURE-SOT/گزارش نهایی به‌روز و lane تحویل می‌شود.

## خطرِ شناخته‌شده

- flags.cmd یک‌بار LF شد و مالک آن را با normalization بایتیِ idempotent به CRLF برگرداند. تست dark-config اکنون CRLF، lone-LF و CRCRLF را هر سه می‌سنجد و PASS شده است.

## قفل‌ها (دست‌نخورده)

- `OCTOPUS_CB_SECRET` و `_ops/ACTIVATION-C6-RESEARCH.flag` — فقط دستِ مالک.
- فلگ‌های router گاورنر/قلب/selfknow همچنان **=0** (فعال‌سازی = مرحلهٔ T5 با restart + مانیتورِ سهمیه).
- production_wire قلب باز نمی‌شود.
