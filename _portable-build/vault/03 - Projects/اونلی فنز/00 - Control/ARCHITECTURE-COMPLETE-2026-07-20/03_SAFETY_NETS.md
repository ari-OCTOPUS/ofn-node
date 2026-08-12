---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 03 · SAFETY NETS — جدول اثبات پس از فیکس (9/9 واقعی)

> قبل از این sprint: «۸/۹ واقعی؛ #۹ (compliance مسیر orchestrator) بای‌پس». حالا هر ۹ با شاهد کد + تست.

| # | تور | مکانیزم | شاهد (فایل/تابع) | تست |
|---|---|---|---|---|
| 1 | DM HITL بدون send | متد send/deliver ساختاراً وجود ندارد | `dm_pipeline.py` (کل ماژول؛ کامنت :12) | `test_dm_hitl` + `test_state_machines` |
| 2 | Warm-up Reddit | آیتم فروشی تا کارما<آستانه finalize نمی‌شود؛ state خراب = deny | `guards.py::WarmupGuard.link_allowed` | `test_warmup_guard` + `test_warmup_corrupt_file_still_denies_sales` |
| 3 | Warning-kill | ۱ هشدار=قفل کانال؛ ≥۲=full_stop کل قیف | `guards.py::ChannelLocks.report_warning` | `test_warning_kill` |
| 3b | **فیکس جدید:** locks-file خراب = fail-CLOSED (قبلاً fail-open بود) | `_load_json_failclosed` → ‏full_stop=True روی corrupt | `guards.py::ChannelLocks._state` | `test_channel_locks_corrupt_file_fails_closed` |
| 4 | OpsecGuard egress | deny-by-default: blocklist خالی/غایب = بلاک کامل send | `langar_bot.py::OpsecGuard.policy_ok/scrub` | `test_langar_failclosed` |
| 5 | KILL/HALT | فایل‌محور، restart-safe؛ boundary ‏C حرف آخر | `langar_bot.py::handle` ‏(KILL) · `creator_studio.py::halt/route` | `test_langar` + `test_creator_studio` |
| 6 | STOP-ORGANISM سراسری | walk-up تا `_ops`؛ لنگر فقط /status؛ استودیو halted | `langar_bot.py::_global_stop` · `creator_studio.py::_global_stop` | `test_global_stop_blocks_all_but_status` |
| 7 | CostMeter | fail-closed: state نامعتبر = مصرف ممنوع | `langar_bot.py::CostMeter.can_spend` | `test_langar` |
| 8 | Containment/rule#6 کپی | denylist روی هر ۳ فیلد + گاردِ دوباره در finalize/approve | `acquisition_pipeline.py::_all_clean/_finalize_gate` · `dm_pipeline.py::_dm_clean` | `test_acquisition_pipeline` |
| 9 | **Compliance tick (فیکس P0)** | چک‌ها از manifest؛ غایب/خراب/قانونِ بی‌لنگر → همه False → tick ‏`blocked_compliance` بدون هیچ advisory | `orchestrator.py::_load_compliance_checks/_RULE_ANCHORS` + گِیت در `tick()` (بندِ ۵) | `test_orchestrator_compliance` (۷ تست) |

مکمل‌ها (همین sprint): قفل RLock + atomic tmp+replace روی acq/dm ‏(`_save`) · dedup ‏idempotent · ‏`approvals.jsonl` ‏audit ‏HITL · ‏`/pf_dryrun` صفر-اثر · orchestrator بدون `_ops/neural` بوت می‌شود (fallback stdlib — `test_orchestrator_standalone`).

باقی‌ماندهٔ شناخته (عمداً باز): ‏`_global_stop` روی exception ‏fail-open است (return False) — ریسک پایین، در backlog ‏#R2.
