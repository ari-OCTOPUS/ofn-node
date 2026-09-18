---
type: knowledge
project: "[[09-LANES/N3V2-MATH-20260905T031103Z/PROJECT]]"
status: active
tags: [octopus, memory, experiment]
created: 2026-09-05
updated: 2026-09-05
sources:
  - "[[09-LANES/N3V2-MATH-20260905T031103Z/04-MEMABL-AND-MEMORY]]"
  - "[[09-LANES/N3V2-MATH-20260905T031103Z/LANE-REPORT]]"
---

# تشخیص شکست منجمد MEMABL — بدون تکرار علمی

این نوت بازخوانی رسیدهای موجود و کد پین‌شده است. آزمایش دوباره اجرا نشد. Gate B بسته می‌ماند. آستانه، k، seed و M/X/C بازنشده‌اند.

## حکم ثبت‌شده

هر دو اجرای علمی یک‌باره `H1_STRONG_FAIL` هستند. verifier محاسباتی همهٔ چک‌ها را `true` کرده؛ یعنی اعداد بازتولید شده‌اند، نه اینکه فرضیه قبول شده باشد. `SIG_IV` همچنان PENDING است.

| seed | Brier M | Brier S | Brier C | Brier X | M−S | CI95 M−S | M−X | CI95 M−X | verdict | source |
|---|---:|---:|---:|---:|---:|---|---:|---|---|---|
| 271828 | 0.28036900037792895 | 0.23627405413120833 | 0.2405457535692118 | 0.2777856670445956 | 0.04409494624672062 | [0.024258269425208336, 0.06494975800883537] | 0.0025833333333333407 | [-0.02077777777777777, 0.026222222222222227] | H1_STRONG_FAIL | `receipts/MEMABL-271828-obs.json` |
| 141421 | 0.26729203278533636 | 0.23231454393578613 | 0.24140438094755415 | 0.2856809216742252 | 0.03497748884955025 | [0.015327313983920248, 0.05459059970859569] | -0.018388888888888885 | [-0.03927777777777778, 0.0024444444444444453] | H1_STRONG_FAIL | `receipts/MEMABL-141421-obs.json` |

جمعیت امتیازدهی: 360 resolved / 40 unresolved excluded (هر دو obs). متریک: mean Brier؛ تفاوت زوجی = M منهای comparator (`receipts/MEMABL-PREREG-271828.json` / `MEMABL-PREREG-141421.json`).

قاعدهٔ حکم از `harness/n3b_memabl_obs.py` خط 141: `strong_fail = scores["M"] >= scores["S"] - 0.005`. هر دو seed خیلی بالاتر از این آستانه‌اند. `H1_STRONG_PASS` نیاز دارد M حداقل 0.020 بهتر از S، 0.010 بهتر از C، 0.020 بهتر از X، و هر سه CI کاملاً منفی باشد (خطوط 134–140 همان فایل). هیچ‌کدام برقرار نیست.

## چرا M نمی‌تواند S را در این fixture بزند

این‌ها استنباط از کد پین‌شده‌اند، نه اندازه‌گیری همسایهٔ تازه‌اجرا شده.

1. **مولد داده به S نزدیک است.** در `n3-candidate/octopus_observation/obs_fixture.py` خطوط 69–76، `feature_a` و `feature_b` مستقل‌اند و `outcome ~ Bernoulli(0.25 + 0.5 * feature_a)`. در `producer_strategy.py` خطوط 22–24، S همان رابطه را با نویز هش کوچک پیاده می‌کند. S تقریباً مدل مولد است؛ انتظار Brier نزدیک به `E[p(1-p)]` است. اعداد ثبت‌شدهٔ S (~0.236 و ~0.232) با آن سازگارند (`status: inference` از کد + Brier ثبت‌شده؛ histogram همسایه اندازه‌گیری نشد).

2. **M تأخیر علّی دارد.** `causal_knn_prediction` فقط ردیف‌هایی را می‌گیرد که `resolved_at < observed_at`؛ اگر خالی باشد 0.5 برمی‌گرداند (`n3b_memabl_obs.py` خطوط 49–63). `resolved_at` بین 2 تا 25 ساعت بعد از `observed_at` است و مشاهده‌ها ساعتی‌اند. ادعاهای اولیه تاریخچهٔ خالی یا کم دارند. این cold-start است، نه باگ harness.

3. **M میانگین 0/1 است؛ S احتمال پیوستهٔ کالیبره.** حتی با k=10 همسایه، میانگین پیامد دودویی واریانس بیشتری از `p = 0.25 + 0.5 * feature_a` دارد.

4. **X همان سیاست است روی `feature_b` نامرتبط.** در seed اصلی M≈X و CI صفر را در بر دارد. در replica نقطهٔ M−X منفی است ولی CI صفر را قطع می‌کند و به آستانهٔ strong-pass (−0.020 و CI تماماً منفی) نمی‌رسد. یعنی حتی «آیا feature_a در kNN علّی بهتر از sham است» در این پروتکل اثبات قوی نمی‌شود.

5. **P از `feature_b` استفاده می‌کند** (`producer_persistence.py` خطوط 16–18). C = 0.5·S + 0.5·P، S را رقیق می‌کند ولی همچنان از M بهتر است.

6. **Scorer مستقل W-C در MEMABL مصرف نشد.** `n3-candidate/octopus_observation/scorer.py` Brier جداگانه دارد؛ runner خودش Brier می‌نویسد. نبود hash پیش‌اجرای scorer همان شکاف C08 است، نه علت verdict.

## آنچه این نتیجه نیست

- شکست verifier نیست: هر دو `MEMABL-*-verify.json` دارای `ok: true` و تمام `checks: true` هستند.
- تناقض با two-cycle نیست: `MEMORY-TWO-CYCLE-RESULT.json` فقط ثابت می‌کند یک fixture مهندسی `memory_id` را می‌خواند و پیش‌بینی 0.5 را به 0 عوض می‌کند. آن فرضیه غیر از «kNN علّی روی 360 ادعا از S بهتر است» است.
- عملکرد حافظهٔ تولیدی نیست. `mode` هر دو obs: `fixture_only_no_network_no_llm`.
- مجوز retry، retune، یا adoption نیست.

## پیشنهاد برای گیت مالک (اجرا نشده)

`status: open, requires: owner_decision`

- نگه داشتن نتیجهٔ منجمد و بسته ماندن Gate B؛ یا
- preregistration جدید با تخمین‌گر/fixture جدا، با حفظ baseline و `scientific_retries=0` روی پروتکل فعلی؛ یا
- ادامهٔ جدا برای 30 رابطه، 9 قرنطینه، hash scorer، Doctor واقعی — بدون تکرار MEMABL برای زیباتر کردن verdict.

هیچ‌کدام از این‌ها از این نوت استنتاج مجوز live نمی‌شود.
