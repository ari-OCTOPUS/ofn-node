---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, sog, math, simulation]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
sources:
  - "[[04 - Architect System/octopus-build-prompts/HYBRID-HEART-MASTER-PLAN]]"
  - "[[04 - Architect System/SOG-Doctor-Synthesis-A-K]]"
  - "[[04 - Architect System/octopus-build-prompts/M-HEART-SOG-Pacemaker-BUILD-PROMPT]]"
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
---

# HH-P0 — قفلِ ریاضیِ SOG: اعتبارسنجیِ مستقلِ Monte-Carlo برای E_shadow و I_pred

> gate خروج: **math-locked** — اثباتِ مستقل (forward-simulation)، نه دوباره‌مشتقِ همان فرمول. تا این قفل نخورد، هیچ پرامپت بعدی (HH-P1..P7) حق ندارد ضربانِ واقعی بسازد.

## مأموریت

`4.py` مالک فقط `Δ_self/S/S_b/Var_ex/Var_eff/autocov` را MC-validate کرده؛ **E_shadow و I_pred هرگز MC نشده‌اند** (SOG-Synthesis §C: draft/conflicting). این پرامپت: (۱) anchorهای 4.py را با پیاده‌سازیِ مستقل بازتولید کن، (۲) E_shadow و I_pred را با شاهدِ MCِ مستقل قفل یا صادقانه exclude کن، (۳) نتیجه را در lock-file با provenance بنویس.

## زمینِ ریاضی (از synthesis §C + کدِ `4d_system/core` — استخراج تأییدشده 2026-07-10)

- مدل مرجع: `s(t+1)=ρ·s(t)+m(t)+ζ(t)` · `Y(t)=b(t)+λ·s(t)+ε(t)`؛ نقطهٔ کار canonical: `ρ=0.5, λ=0.5, σ_ε=0.1, σ_ζ=0.05, σ_d=0.1`.
- DARE بسته‌شکل (اسکالر): `lam==0 → sz2/(1−ρ²)`؛ وگرنه `c=se2(1−ρ²)`، `disc=(c−sz2λ²)²+4λ²·sz2·se2`، `P=((sz2λ²−c)+√disc)/(2λ²)`. سپس `S=λ²P+σ_ε²`، `K=Pλ/S`. بازوی blind: همان با `σ_ζ'²=σ_ζ²+σ_d²` → `P_b,S_b,K_b`.
- `σ_z² = λ²(σ_ζ²+σ_d²)/(1−ρ²)+σ_ε²` — **از primitiveها بساز، literal ممنوع** (Gate-A).
- `Δ_self=½log(S_b/S)` · `E_shadow=½log(σ_z²/S_b)` · اتحاد: `½log(σ_z²/S)=E_shadow+Δ_self`.
- `I_pred=½Σ_{L≥0}log(S_L/S_b)` با Riccati: `P_0=σ_ζ'²/(1−ρ²)`؛ `S_L=λ²P_L+se2`؛ `P_{L+1}=ρ²·P_L·se2/S_L+σ_ζ'²`؛ n_terms=50، break `|term|<1e-12`.
- سقفِ Δ_self در `λ→∞`: `½ln(1+σ_d²/σ_ζ²)`.
- anchorهای شاهد (فقط در تست/lock، نه در مسیر production): `P=0.00325184, S=0.01081296, P_b=0.01526172, S_b=0.01381543, σ_z²=0.0141667, Δ_self=0.122520, E_shadow=0.012553, identity=0.135073, I_pred=0.0144179, Var_ex=0.217327, Var_eff=0.208232, ceiling=0.804719`.
- MC مرجع 4.py (بازتولید مستقل): `T=1.2e6, burn=4000`؛ دوقلوی Kalman: `z=λs+ε`، `ν=z−λŝ`، `ν_b=z−λŝ_b`، `s←ρs+m+ζ`، `ŝ←ρ(ŝ+Kν)+m` (informed سیاست m را می‌داند)، `ŝ_b←ρ(ŝ_b+K_b·ν_b)` (blind فقط میانگین صفر)؛ excess: `ex=½log(S_b/S)+ν_b²/(2S_b)−ν²/(2S)`.

## تحویل‌دادنی‌ها

1. **`_ops/heart/__init__.py`** — پکیجِ نو (docstring: ADR-001 + master-plan + این پرامپت).
2. **`_ops/heart/sog_math.py`** — **stdlib-only** (`math`+`random`؛ ارگانیسم numpy ندارد):
   - `solve_floors(rho,lam,se,sz,sd) → dict` (P,S,K,P_b,S_b,K_b,sigma_z2 — از primitiveها)
   - `delta_self / e_shadow / identity / i_pred_riccati / delta_self_ceiling`
   - `dare_crosscheck(n_draws=300, seed=7)` — closed-form در برابر fixed-point iteration (بازتولید بلاک ۱ 4.py)
   - `mc_witness_core(T, seed=123)` — شاهدِ MCِ Δ_self/S/S_b/corr²/Var_ex (بازتولید مستقل بلاک ۲)
   - `mc_witness_e_shadow(T, seed)` — **نو، کارِ اصلی**: روی همان مسیر، excessِ null-در-برابر-blind: `exs=½log(σ_z²/S_b)+z²/(2σ_z²)−ν_b²/(2S_b)` → `mean(exs)≈E_shadow` + شاهد دوم `Var(z)≈σ_z²`
   - `mc_witness_i_pred(n_windows, window_len, seed)` — **نو**: سگمنت‌های مجزای مسیر؛ فیلترِ blind از priorِ stationary در شروعِ هر سگمنت restart؛ واریانسِ تجربیِ innovation در offsetِ L → `S_L^emp`؛ جمعِ جزئی `½Σ_{L≤10}log(S_L^emp/S_b)` در برابر جمعِ جزئیِ تحلیلی
   - `run_lock(out_path=None, full=True) → dict` — اجرای کامل + نوشتنِ اتمیکِ lock-file + `opslib.ledger_note("SOG_MATH_LOCK", …)`
3. **lock-file: `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json`** (نامِ M-HEART Gate-A) — شامل: مقادیرِ تحلیلی، خطای نسبیِ هر شاهدِ MC، seeds/T، `e_shadow_locked: true|false`، `i_pred_locked: true|false` (وضعیتِ un-collapsible: `locked | excluded-unlocked`)، `code_sha256` (خودِ sog_math.py)، `source_4py_sha256` (اگر `C:/Users/Armin/Desktop/4D/4.py` در دسترس؛ وگرنه `"unavailable"`)، `ts`.
4. **`_ops/tests/test_heart_math.py`** (الگوی harness خانه: `harness.setup` قبل از importِ opslib-خور؛ چک‌لیست `harness.run`) + ثبت در `run_all.py`.

## گیتِ پذیرش (Gate-A — همه باید پاس شوند)

- DARE closed-form vs iteration: بیشینهٔ خطای نسبی `<1e-9` روی ۳۰۰ قرعه (تست: ۶۰ قرعه).
- anchorهای تحلیلی: خطای نسبی `<1e-4` (بازتولیدِ `run_self_test` مدل مالک).
- شاهدِ MC هسته (تست با `T≥150k`): `Var(ν)/S`, `Var(ν_b)/S_b`, `corr²−S/S_b`, `mean(ex)−Δ_self`, `Var(ex)−Var_ex` همه در تلورانس ۵٪ (قراردادِ `verify_against_model(tol=0.05)` مالک).
- شاهدِ MC E_shadow: `mean(exs)` در `max(5%·|theory|, 4·SE)` (گیتِ SE-آگاه — از MC دقتی بیش از توانِ آماری‌اش نخواه؛ ریویوی خصمانه: SE در T=1.2e6 برابر ~1.4e-4 است) + `Var(z)` در ۲٪ نسبت به `σ_z²` → فقط آن‌وقت `e_shadow_locked=true`؛ شکست = `false` صادقانه (نه سبزِ دروغ).
- **حلِ تناقض‌های عددی (مثلاً identity=0.135041 vs 0.135073) تحلیلی است، نه MC:** اتحادِ `½log(σ_z²/S)=E_shadow+Δ_self` باید تا `1e-12` بسته شود؛ MC فقط شاهدِ سازگاری است (تفکیکِ 3.2e-5 با MC آماراً ناممکن — نیازمندِ T≈9e8).
- شاهدِ MC I_pred: دنبالهٔ `S_L` per-offset در `max(2.5%, 4·SE)` + دُمِ همگرا→`S_b` → `i_pred_locked` (I_pred به‌هرحال **هیچ‌چیز را gate نمی‌کند** — decoration؛ M-HEART).
- provenance: اگر `4.py` مالک در دسترس نبود، `source_4py_sha256="unavailable"` صریح در lock بیاید (ریاضی خودبسنده است ولی گپِ provenance باید دیده شود — کابین نشانش می‌دهد).
- ساختاری: `sog_math.py` هیچ importی از `organ_gate/money_gate/budget_gate/chrono` ندارد؛ هیچ literalِ `0.122520/0.804719` در مسیرِ محاسبهٔ production (فقط تست/lock به‌عنوان witness).

## خطوطِ قرمز

stdlib-only · $0/آفلاین · هیچ دستکاریِ `chrono.py`/HLC · lock-file فقط با اجرای کاملِ full، نه تست · شکستِ هر شاهد = exclude صادقانه، نه پایین‌آوردنِ تلورانس · RNGِ مستقل (stdlib Mersenne؛ عدمِ بازتولیدِ بیت‌به‌بیتِ numpy = ویژگیِ استقلال، نقص نیست — توافقِ آماری معیار است).
