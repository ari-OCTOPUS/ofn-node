# برنامه کامل یکپارچه‌سازی Self → Compass → Heart → Mission → Action

> این سند برنامهٔ اجرا بعد از پایان ایجنت موازی است. هیچ رأی ضمنی برای arm/restart/send/spend نیست.

## وضعیت فعلی

- این پکیج: `IMPLEMENTED_NOT_INTEGRATED`
- Action Bridge: `IMPLEMENTED_NOT_INTEGRATED`
- World Discovery: `IMPLEMENTED_NOT_INTEGRATED`
- Goal Evaluation Loop: `LIVE`
- Self-model freshness: `BROKEN/STALE`
- Heart: `ADVISORY_SHADOW`
- Whole-body innervation: `PARTIAL`

## فاز ۰ — اتمام و freeze کار موازی

1. ایجنت تلگرام/registry کارش را commit و handoff کند.
2. GLM و boundary integration کامیت/تحویل تمیز داشته باشند.
3. status و foreign hunks دوباره map شوند.
4. `run_all.py` فقط بعد از مالکیت تمیز تغییر کند.

## فاز ۱ — تست این پکیج

پنج تست مستقل اجرا شوند. سپس mutationهای زیر:

- shadow heart → authoritative
- stale self-model → READY
- free text method → A0
- unknown candidate → owner_action
- guidance target override → accepted
- missing mission/action/memory → graph complete
- prereg A و B → یک action_id

همه باید قرمز شوند، سپس restore از git و پاک‌کردن pycache.

## فاز ۲ — رفع self/state freshness

مالکیت: ایجنت ارشد، نه این پکیج.

1. `VQ-OBS-REPLACE-001` را با تشخیص handle ویندوز ببند.
2. `LockedJson` را فقط پس از inventory همه callerها تغییر بده.
3. replace retry/backoff + alarm + حفظ نسخه قبلی.
4. self-model refresh واقعاً روی دیسک بنشیند.
5. `ORGANISM-STATE` تازه شود.
6. innervation باید spine/selfmodel را سبز ببیند.

شرط عبور: self-model در SLA، ORGANISM-STATE در SLA، coverage=100% یا استثنای مکتوب.

## فاز ۳ — authority ریتم قلب

تصمیم معماری لازم:

A) تا بازشدن production wire، Cortex از default استفاده کند.
B) قلب سایه cadence بدهد، ولی صریح `ADVISORY_SHADOW` ثبت شود. پیشنهاد فعلی: B برای آزمایش، A برای production سخت.

در هر حالت:

- `rhythm_policy.decide` یک نقطه حقیقت شود.
- shadow هرگز `AUTHORITATIVE` گزارش نشود.
- hash قانون کنترل با SIM-REPORT دوباره هماهنگ شود.
- Gate-0 و delta_self بررسی شود؛ برای بازکردن گیت عدد جعل نشود.

## فاز ۴ — اتصال exact prereg به Unified Control

بعد از `prereg.register` و قبل از اقدام:

```python
prepared = unified_control.pipeline.prepare_records(
    directions=goal_directed.load_goals(),
    prereg=p["row"],
    heart=explicit_heart_authority_record,
    cortex=current_cortex_summary,
    self_model_authority=current_self_model_authority,
    innervation=current_innervation,
    owner_guidance=current_bounded_guidance,
)
```

قانون: رکورد همان چرخه پاس داده شود؛ «آخرین ردیف» از دیسک حدس زده نشود.

## فاز ۵ — Canonical Mission Link

- Mission Genome و SGC را جایگزین نکن.
- mission envelope ساخته‌شده با همان `trace_id` ثبت شود.
- نگاشت statusها به قرارداد موجود مستند شود.
- `goal_key`, `prereg_id`, `mission_id`, `task_id`, `trace_id`, `action_id` در همه receipts بمانند.
- هر transition غیرقانونی fail-closed.

## فاز ۶ — Action Bridge

1. A0/A1 فقط sandbox.
2. A3 فقط کارت مالک.
3. A2 تا شروط L3 بسته است.
4. A4/A5 BLOCKED_BY_OWNER.
5. A6 REJECT.
6. used nonces و ledger پایدار شوند.
7. HMAC از env، بدون چاپ.
8. receipt-write failure موفقیت اعلام نشود.

برای goal فعلی claimed:

- no qualified lead ⇒ BLOCKED/no-qualified-lead-evidence
- qualified real lead ⇒ A3 owner card
- هیچ claim خودکار، lead جعلی یا metric write

## فاز ۷ — Verdict و حافظه

- evaluator فقط prereg + metric روی دیسک را بخواند.
- action receipt فقط شاهد است، نه رأی نهایی.
- PASS/PARTIAL/FAIL/BLOCKED به همان trace وصل شود.
- فقط outcome تأییدشده وارد Memory Gate شود.
- memory مجوز نیست.
- شکست باید pivot چرخه بعد را تغذیه کند.

## فاز ۸ — Owner Guidance

- focus/think cadence/pause می‌تواند همان لحظه اعمال شود.
- goal/metric/baseline/target فقط در چرخه بعد و با prereg تازه.
- guidance آزاد هرگز action authorization نیست.
- همه overrideهای ممنوع audit شوند.

## فاز ۹ — World Discovery

- artifact → boundary translator → action-request.
- E0→A0، E1→A1، E2→A3، E3→A4، E4→A5.
- `NO_VALID_DISCOVERY` → NO_ACTION.
- گزارش/گفت‌وگو فقط Outer DM.
- send هر بار رأی تازه.

## فاز ۱۰ — تلگرام

مطابق `_ops/telegram_contract`:

- Outer DM: همه قابلیت‌ها، هدف‌ها، مأموریت و کارت‌ها.
- Inner DM: سلامت/approval/receipt.
- Group: فقط پاها.
- callback handler روی emitter bot.
- capability manifest برای این پکیج بعد از تست اضافه شود.

## فاز ۱۱ — پذیرش end-to-end

یک مأموریت read-only:

```text
Direction → Goal → Prereg → Mission → A0 Action → Receipt → Metric → Verdict → Memory
```

یک مأموریت owner-gated:

```text
claimed goal → qualified lead check → A3 card → owner verdict → receipt → evaluator
```

شرط Done:

- یک trace مشترک
- self-model تازه
- heart authority صادق
- innervation کامل
- target immutable
- action receipt واقعی
- evaluator مستقل
- memory outcome-bound
- zero unauthorized send/spend/merge/restart/arm

وضعیت‌های مجاز:

- `READY_FOR_OWNER_GATE`
- `INTEGRATED_IN_SANDBOX`
- `IMPLEMENTED_NOT_LIVE`
- `UNIFIED_CONTROL_LIVE`

بدون شاهد کامل، آخری ممنوع است.
