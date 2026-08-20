---
type: proposal
status: draft
tags: [octopus, judge-bias, phase2, paid, pre-registration]
created: 2026-08-20
updated: 2026-08-20
created_by: agent B (ZCode) — متن کارت طبق دستور مالک #۱۱ §۴ (حاکم)
execution: 0 تا امضای Ed25519 مالک روی همین کارت (رأی چت کافی نیست — R10)
separate_from: PRE-REG-FULL-LOOP-FLASH-2026-08-20 (بودجه‌ها قاطی نمی‌شوند)
---

# PRE-REG-JUDGE-BIAS-PHASE2-2026-08-20 — UNSIGNED

```yaml
card: PRE-REG-JUDGE-BIAS-PHASE2-2026-08-20
objective: سنجش سوگیری جایگاه و طول در داورهای واقعی
tasks: 20            # 10 استدلالی + 10 خلاقانه (همان چارچوب LAB-1 فاز ۱)
pairs: 120
permutations: 2
judges_paid: 2       # فقط مسیر ارزان؛ داورهای غیرپولی جدا
planned_calls: 480
hard_max_calls: 600
hard_stop_aud: 0.20
per_call_cap: unchanged
concurrency: 1
budget_source: existing_science_bucket
cap_increase: false

design_locks:
  quality_and_length: decorrelated
  seeds: fixed_and_recorded
  hash: PYTHONHASHSEED=0 یا هش قطعی
  fisher_direction: two_sided
  flip_rate_on: only_pairs_with_advantage
  void_rule: unstable_judgment_is_VOID

power:
  target_effect: rho = 0.5
  min_n_for_correlation: 29
  report_underpowered_cells: mandatory

acceptance:
  - هر عدد با n و بازهٔ اطمینان
  - هیچ ادعای بهبود بدون baseline
  - رسید هزینه با task_id و run_id
execution_condition: امضای Ed25519 مالک روی همین کارت
executable: false
```

## مبنای هزینه (از دادهٔ واقعی T35)

۶۰ فراخوان K=9 = ‏AU$0.011723 ⇒ ~AU$0.000195/فراخوان ⇒ ‏
۶۰۰≈AU$0.117 · ۱۲۰۰≈AU$0.234 · ۲۴۰۰≈AU$0.469. با ۴۸۰ فراخوان برنامه‌ریزی و
سقف AU$0.20.

## زیرساخت آماده

- چارچوب: `research/judge_bias/` (framework/metrics/run_offline) — فاز ۱ با
  ۷/۷ فرضیه روی داورهای تزریقی اعتبارسنجی شد.
- گیت قضاوت: flip-rate روی جفت‌های دارای برتری (حکم ۳ دستور #۱۱).
- مجموعهٔ طلایی: `GOLDEN-SET-LABELS-template.json` (۱۲۰ ردیف؛ برچسب‌گذاری مالک).
- RealJudge در کد fail-closed است و فقط با همین کارتِ امضاشده باز می‌شود.

## رأی مالک

- [ ] **رد**
- [ ] **امضا ۴۸۰ فراخوان / AU$0.20 / دو داور پولی هم‌خانواده با افشا**
- [ ] **امضا با تغییر:** ______ فراخوان / ______ AUD / داور: ______

امضا: ________ · تاریخ: ________ · Ed25519 (verify با لنگر
`2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2`)

تا امضا: **اجرا = ۰.**
