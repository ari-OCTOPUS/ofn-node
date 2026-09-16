# OWNER_REVIEW_PACKAGE

`ready_for_owner_decision`: **false**  
`authority_changed`: **false**  
`executed_actions`: **0**  
`decision`: **KEEP_WAVE0_LOCKED**

این بسته بر اساس EVIDENCE است نه امید. T7 اجرا نشده و نباید اجرا شود.

## baseline

نگاه کنید به [[CURRENT_STATE]] / `CURRENT_STATE.md` و `T0_FREEZE.json`.

## seven-day telemetry summary

**UNKNOWN**. uptime این boot حدود `03:49:19 up  2:33,  0 users,  load average: 1.09, 1.00, 0.97`. مجموعهٔ هفت‌روزهٔ پایدار برای آرمینگ موجود نیست.

## prediction/outcome statistics

- predictions: 56
- outcomes: 55
- usable_pairs: 53 (نیاز T1: 50)
- pending: 1
- orphan_outcomes: 0
- duplicate_predictions: 0
- ledger_verify: True (seq=111)

## skill estimate and lower bound

- samples: 53
- score: 0.0 — **model_is_the_baseline**؛ شاهد کیفیت مدل نیست؛ `candidate_loss=null`؛ T4 اجرا نشده
- lower_bound: 0.0
- eligible: False
- reason: not_better_than_baseline
- calibration_error: None → **UNKNOWN**

## missing-data report

homeostasis `unknown`: `['prediction_calibration']`.  
sensor_coverage live `0.5` status critical.  
missing با صفر پر نشده است.

## ledger verification

world_model / metacontrol / reflex: chained JSONL. جهان‌مدل `seq=111`.

## signed checkpoint verification

unsigned digest `sha256:3b60751b3759698b4982ccda035a008539cc0014cb086d96f516fc274142c150` seq `266`. امضا نیست. GAP-002 باز است.

## Doctor report

`doctor-report.json` (پس از اجرای read-only). repairs_attempted باید 0 باشد.

## GAP-001 evidence

`gap_001=OPEN`, `gap_001_last_result=TESTED_FAIL`, `gap_001_cryptographically_verified=false`. ادعای مگاپرامپت `PASSED` باطل است. فایل زنده مرجع است. evidence: `evidence/gap001-boot_report.json`.

## GAP-002 closure evidence

نیست. فقط unsigned export.

## registry signature verification

live v5، فایل‌های `.sig` موجود، digest `sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5`. v6 unsigned pack در TO-LAPTOP است؛ signed_present=false.

## planner invocation proof

ledger planner_invocations=0. اسکریپت‌های زنده planner را import نمی‌کنند.

## executable action proof

executable_actions=0. metacontrol.executable=False.

## rollback plan

`rollback-plan.md` — dry-run only.

## exact diff

`PROPOSED_DIFFS.md` — اعمال نشده.

## exact target scope (اگر روزی OA-T7 صادر شود)

فقط A0 advisory روی `octopus-sensorium` و `octopus-stability`. GPIO/PWM/MQTT/leg/reboot/restart/registry_write/drop_caches/cpufreq ممنوع.

## expiration / max actions

در قالب OA همه خالی/صفر → DENY. مالک باید issued_at، expires_at، max_duration_s، max_actions، rollback_digest و owner_signature را پر کند.

## T4 / T5

- T4: `NOT_EXECUTED_NO_CANDIDATE`. persistence-v1 هم مدل زنده است هم baseline؛ SS=0 تحلیلی است.
- T5: خروجی live = DENY با executable=false. رشتهٔ `PLAN_ALLOWED_ADVISORY` در live emit نمی‌شود. حتی اگر advisory، planner فراخوانی نمی‌شود.

## T8 stub

`T8_FUTURE_ACTUATOR_STUB.json` — اجرا نشده.

## قالب OA موردنیاز

`OA-T7-TEMPLATE.json` و `owner-authorization.schema.json`. امضا خالی = DENY.


## اعتبار بسته

`MANIFEST.json.sha256` digest است، نه امضا و نه provenance. روی لپ‌تاپ `python3 verify_owner_review_pack.py .` را اجرا کنید.

عبارت دقیق checkpoint: `octopus-audit-ledger checkpoint anchored at seq=266`  
hash کامل seq 266: `sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2`
