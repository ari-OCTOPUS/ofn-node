# 00-OWNER-ABSENCE-PLAN — the 24-hour test (blueprint §11 + PR #75)

scope_measured: scenario list mirrors tests/test_chaos_owner_absent.py
  (P1 merged #74/#75 @dd1d6cc; load-path + in-flight close on this follow-on);
  gate implementations referenced are merged-or-open code, not aspirations.
scope_not_measured: the 24-hour run itself has NOT happened yet — this document is the plan,
  the tests are the unit-level proof; the day-long exercise remains open work (P7).

## Premise

مالک ۲۴ ساعت در دسترس نیست. اگر تنها راه بازیابی، تماس با مالک بود، پروژه هنوز محصول نیست.
هر سناریوی زیر یک تستِ اجراشده دارد؛ «رفتار مورد انتظار» یعنی همان رفتاری که تست آن را قفل کرده.

## Seven scenarios → enforcing code → test

| تزریق آشوب | رفتار مورد انتظار | کد | تست |
|---|---|---|---|
| یک منبع می‌میرد | UNKNOWN، نه FALSE | `kernel/source_health.classify_fetch(None)→UNKNOWN` | Scenario1 |
| agent timeout | سایر بازوها ادامه می‌دهند | run store فقط رویدادهای واقعی را می‌پذیرد | Scenario2 |
| rate limit | bounded backoff سپس PARKED | `source_health.backoff_delays()`=(1,2,4) سرریزبه‌PARKED | Scenario3 |
| duplicate delivery | یک اثر | `run_store` ردِ (kind,ref) تکراری | Scenario4 |
| بودجهٔ یک بازو تمام | توقف همان بازو | `callbudget` per-rung (REMOTE=100) | Scenario5 |
| global HALT | هیچ run جدیدی؛ in-flight close مجاز | `halt_flag` + `run_gate.start_run` (STARTS only) | Scenario6 |
| recovery بدون مالک | بستن run معیوب و شروع دوباره | `run_store.close()` + start | Scenario7 |

## Escalation ladder (what genuinely needs the owner)

- هر ارسال بیرونی (quote_sent / transport binding) — Q-05، ساختاری مهرشده
- چرخش راز — Q-08
- HELD items on the outbox — تصمیم انسانی با context (claim refused, approve-from-HELD deliberately refused)
- هر policy relaxation یا gate removal — قانون آهنین

## Acceptance for the real Chaos Day (still to run)

۲۴ ساعت بدون مداخله: بدون جعل شاهد، بدون دوبار خرج‌کردن، بدون توقف سایر بازوها.
Evidence: `run_store` JSONL + outbox states + incidents log — همه append-only.
