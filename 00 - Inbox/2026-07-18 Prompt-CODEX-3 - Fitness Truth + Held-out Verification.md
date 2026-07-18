---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, codex, fitness, epistemics]
created: 2026-07-18
updated: 2026-07-18
created_by: agent
---

> **for:** Codex · **risk:** medium (learning-loop honesty — additive)

# CODEX PROMPT 3/5 — Fitness Truth Layer (evidence-weighted + held-out)

> نقش تو: **Epistemics Engineer**. قاعدهٔ حاکم: «سیستم حق ندارد صرفاً به دلیل سبز بودن تستِ خودش، خود را هوشمندتر اعلام کند.» تو fitness نمایشی را به fitness مبتنی بر شواهد مستقل تبدیل می‌کنی.

## 0) حقیقت زمین (verified 2026-07-18)

- Repo: `F:\backup` · master · HEAD `c9b9a03`؛ کد در `7742486`.
- `_ops/telegram_center/mission.py`:
  - `fitness_template(mission_type)` (خط ~۱۹۴) · `compute_fitness(mission)` (خط ~۳۶۹) · `refresh_fitness(mid)` (خط ~۳۹۴) · `record_test(mid, name, passed, detail)` (خط ~۳۰۳) · `record_review(...)` (خط ~۳۲۲) · `cockpit_summary(limit=5)` (خط ~۴۰۱) · `mission_card(mid)` (خط ~۴۱۸)
- مشکل شناخته‌شده (گزارش رسمی + blueprint §۵/§۸): `record_test` ادعا را ثبت می‌کند بدون الزام به artifact؛ «Mission status ≠ Truth status» هنوز enforce نمی‌شود؛ `test_requested` عملاً می‌تواند با `test_passed` اشتباه شود.
- ۱۳ تست `test_tg_mission.py` سبز — همه باید سبز بمانند.
- اگر Prompt-CODEX-1 (mission_runner) قبلاً اجرا شده: artifactها در `_agent_reports/missions/<mid>/run-<ts>/` هستند — از همان قرارداد بخوان. اگر نه: قرارداد artifact را همین‌جا تعریف کن تا runner بعداً پرش کند (loose coupling).

## 1) مأموریت

1. **Evidence-bound status:** `record_test` بدون `evidence_ref` (مسیر artifact + exit_code + run_id) فقط `test_requested` ثبت کند؛ `test_passed` تنها با evidence کامل. invariant-checker کوچک: statusِ passed بدون artifact → `invalid` + audit (سناریوی ۸ ماتریس).
2. **فرمول fitness (از blueprint §۸):**
```text
fitness = goal_progress + verification_strength + reversibility + policy_compliance + runtime_stability
          − uncertainty − scope_creep − regression_risk − operator_burden
```
   v0 ساده و شفاف: هر مؤلفه ۰..۱ با منبع مشخص (signal واقعی یا proxy — صادقانه برچسب بزن `[FACT]/[PROXY]`). `confidence` بدون evidence مستقل سقف ۰.۳.
3. **Held-out check:** حداقل یک چکِ مستقل از تستِ خودِ mission — مثلاً اجرای یک تست همسایه از suite که mission لمسش نکرده + چک `no-conflict-marker` + چک redaction. در `verification.held_out_checks` ثبت شود.
4. **Done ≠ Green:** `set_state(mid,'done')` فقط وقتی: verification pass + held-out pass + (اگر side-effect داشته) monitoring window تعریف‌شده. در غیر این صورت رد + audit.
5. **کارت صادق:** `mission_card` و `cockpit_summary` باید confidence و منبع هر عدد را نشان دهند («تست سبز (self)» ≠ «راستی‌آزمایی مستقل»).

## 2) تست‌های اجباری
گسترش `test_tg_mission.py`: passed-بدون-artifact رد می‌شود · confidence بدون held-out ≤۰.۳ · فرمول با مؤلفه‌های لبه (همه صفر/همه یک) · done بدون held-out رد · rollback/failure باعث افت fitness · کارت redaction-safe. همهٔ ۱۳ تست قبلی سبز بمانند.

## 3) قانون اساسی
`git status --short` اول؛ دست‌نزدن به کار uncommitted دیگران؛ commit اتمیک؛ state-churn/`_octopus/` commit نمی‌شود؛ اثبات با `python -X utf8 _ops\tests\test_tg_mission.py` + `run_all.py` در worktree تازه؛ هیچ ادعای «هوشمندتر شد» بدون سیگنال اندازه‌گیری‌شده.

## 4) خروجی نهایی
1. کد + تست سبز (خروجی paste) 2. `_agent_reports/FITNESS-TRUTH-REPORT-<date>.md` — schema نهایی + جدول signal واقعی/proxy 3. بولت HANDOFF + PROJECT architect 4. verdict: `TRUTHFUL / PARTIAL / COSMETIC` برای لایهٔ fitness بعد از کارت.
