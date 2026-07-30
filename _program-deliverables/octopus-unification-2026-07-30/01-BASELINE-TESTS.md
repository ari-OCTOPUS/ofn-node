# 01 — BASELINE TESTS (پیش از هر تغییر)

تاریخ: 2026-07-30 · برنچ: fix/tg-p2-2026-07-30 · HEAD: 8d76618

**جمع: 463/463 شمارش‌پذیر در 42 سوییت** · قرمز: ۰ · ۳ سوییتِ PASS-فرمت (بی‌شمارش، با شاهدِ tail) · run_all: BLOCKED (دلیل پایین)

| suite | pass/total | exit | s |
|---|---|---|---|
| action_bridge/test_classifier | 24/24 | 0 | 0.1 |
| action_bridge/test_scope_guard | 12/12 | 0 | 0.1 |
| action_bridge/test_flow | 25/25 | 0 | 0.2 |
| action_bridge/test_claimed_fixture | 5/5 | 0 | 0.1 |
| unified_control/test_snapshot_compass | None/None | 0 | 0.3 |
| unified_control/test_snapshot_staleness | 10/10 | 0 | 0.2 |
| unified_control/test_authority_policies | None/None | 0 | 0.1 |
| unified_control/test_pipeline | None/None | 0 | 0.1 |
| unified_control/test_runtime_seam | None/None | 0 | 0.1 |
| unified_control/test_translator_graph | None/None | 0 | 0.1 |
| wda/test_boundary | 43/43 | 0 | 0.2 |
| owner_console/test_catalog | None/None | 0 | 0.2 |
| owner_console/test_conversation | None/None | 0 | 12.1 |
| owner_console/test_acceptance_questions | None/None | 0 | 29.1 |
| owner_console/test_telegram_adapter | None/None | 0 | 2.5 |
| owner_console/test_mutation_gaps | 4/4 | 0 | 1.5 |
| sgc/test_test_cycle_beat | 14/14 | 0 | 0.5 |
| sgc/test_goal_generator | 10/10 | 0 | 0.2 |
| sgc/test_prereg_evaluator | 16/16 | 0 | 0.3 |
| sgc/test_target_guard | 14/14 | 0 | 0.2 |
| sgc/test_goal_max_circular | 14/14 | 0 | 0.3 |
| sgc/test_goal_directed | 6/6 | 0 | 0.3 |
| mission/test_tg_mission | 13/13 | 0 | 0.4 |
| mission/test_tg_mission_runner | 12/12 | 0 | 0.8 |
| memory/test_memory_gate | 10/10 | 0 | 0.3 |
| memory/test_honest_outcomes | None/None | 0 | 0.2 |
| memory/test_outcome_spine | 10/10 | 0 | 0.3 |
| memory/test_acct_memory | None/None | 0 | 0.2 |
| spine/test_event_spine | 9/9 | 0 | 0.3 |
| spine/test_spine_sanitize | 6/6 | 0 | 0.2 |
| spine/test_spine_single_surface | None/None | 0 | 0.2 |
| spine/test_spine_multidomain | 9/9 | 0 | 1.5 |
| tg/test_tg_center | 30/30 | 0 | 0.8 |
| tg/test_tg_api | 24/24 | 0 | 0.2 |
| tg/test_tg_surface_router | 12/12 | 0 | 0.1 |
| tg/test_tg_route_seam | 12/12 | 0 | 0.3 |
| tg/test_tg_hold_policy | 9/9 | 0 | 0.4 |
| tg/test_surface_policy | 24/24 | 0 | 1.4 |
| tg/test_tg_leg_tasks | 16/16 | 0 | 0.3 |
| tg/test_tg_input_surface_policy | 20/20 | 0 | 0.1 |
| tg/test_tg_canonical_access_model | 8/8 | 0 | 2.4 |
| tg/test_callback_routing | 6/6 | 0 | 0.3 |

## BLOCKED

- **run_all.py**: run_all بدونِ pin ِ ORG_ROOT فایل‌های زندهٔ STOP-ORGANISM/RESTART-REQUESTED می‌سازد (سابقهٔ ثبت‌شده). اجرای full فقط در worktree ِ ایزوله با ORG_ROOT=<worktree> مجاز است — فازِ E2E.