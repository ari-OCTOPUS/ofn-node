---
type: evidence
status: active
updated: 2026-08-16
session: CONTINUOUS-IMPROVE A+C+F
agent: Cursor Grok 4.6 — پنجرهٔ خودبهبودی دائمی (مالک override لانچرِ منسوخ)
created: 2026-08-16
mode: کشف→گپ→فیکس additive→تست→ثبت · TCB لمس‌نشد · فلگ صفر · حذف صفر · پوش نشد
contradiction_registered: C-029, C-030
next_free_contradiction: C-031
tests_run: "test_sog_floor_guards 5/5 · test_money_gate 9/9 · test_selfheal_ok_field PASS · test_phi_reset_on_restart PASS · test_leg_failure_reason PASS"
run_all_registration: "فایل‌های نو را گزارش می‌کنم نه ثبت — WORKLOCK روی run_all.py + lane autoflow فعال"
---

# خودبهبودی دائمی — پنجره A+C+F — 2026-08-16

فکت‌چک پیش‌فرض‌های مگاپرامپت: **C-027 آزاد نیست** (C-029 بود). `4d_system/core/` داخل TCB dirs است — فیکس آنجا = امضای مجدد. لنگرهای canonical **واقعاً بازتولید می‌شوند** (worst rel_err = 8.8e-6). SELFHEAL در flags.cmd روشن است. Tick الان می‌دود. این پنجره لانچرِ continuous را به‌خاطر فرمان مستقیم مالک اجرا کرد، نه به‌خاطر پین HANDOFF (آن پین Seam Loop را متحدکننده می‌داند).

## حوزه A — هستهٔ ریاضی SOG

**نقشه:** دو نسخهٔ موازی DARE: `4d_system/core/model.py` (TCB، `run_self_test` در guardrails/verifier) و `_ops/heart/sog_math.py` (تولید ارگانیسم + telemetry). مصرف‌کنندهٔ TCB: `brain/guardrails.check_invariants`. مصرف‌کنندهٔ _ops: `telemetry/sog_metrics_v2` · `test_heart_math`.

**گپ‌ها:**
1. `|ρ|≥۱` با `λ=0` → ZeroDivisionError در **هر دو** نسخه (۵ مسیر در sog_math قبل از فیکس).
2. `settings.ANCHORS` شامل I_pred/Var_ex است ولی `run_self_test` آن‌ها را چک نمی‌کند؛ `SETTINGS_ANCHORS` در verifier import مرده است.
3. I_pred خودش با settings می‌خواند (rel 1.7e-6) — ادعا ناقص است نه دروغ لنگر.

**فیکس (غیر TCB):** گارد `_dare_params_ok` در `sog_math.py` — منحط → `nan` + `ok=False`، بدون استثنا. canonical P بیت‌پایدار `0.0032518381359193053`.

| سنجه | قبل | بعد |
|---|---|---|
| مسیرهای منحطِ sog_math که می‌ترکند | **۵/۵** ZeroDivision | **۰/۵** (nan + ok=False) |
| canonical P | همان | همان (۱e-18) |
| TCB `core.model.P_closed(ρ=1,λ=0)` | ZeroDivision | **همچنان ZeroDivision** (رأی C-029) |

## حوزه C — مسیر پول

**نقشه:** `money_gate.check` دیوار per-action؛ `capability_gate.require` هر دو را AND می‌کند. تست قبلی فقط ۱۵ و ۵۰ AUD.

**گپ‌ها:**
1. مبلغ منفی از «≤آستانه» رد می‌شد → **allow**.
2. NaN/Inf deny تصادفی با دلیل دروغین `over-gate(AU$nan>20)`.
3. واحد AUD float است نه cents (رأی بزرگ — دست نخورد).

**فیکس:** غیرمتناهی یا `<0` → deny `amount-not-a-spend`. صفر همچنان under-gate.

| سنجه | قبل | بعد |
|---|---|---|
| `check(-1)` / `check(-0.01)` | allow | deny |
| `check(nan)` / `check(inf)` دلیل | over-gate دروغین | `amount-not-a-spend` |
| `check(15)` / `check(0)` | allow | allow (رگرسیون) |

## حوزه F — خودترمیمی

**نقشه:** `OCTOPUS_WIRE_SELFHEAL=1` در flags و env پروسه‌ها. pacemaker در organism با doctor پاس می‌شود. ۸۳ رویداد زنده، **همه** `lead-naghshi`؛ ۶۶ ردیف فقط `{leg,ts}`؛ **۰ ردیف `ok`**.

**گپ‌ها:**
1. مقدار برگشتی `restart_from_known_good` نادیده بود؛ `task.completed` حتی روی شکست ادعا می‌شد.
2. دفتر زنده فیلد موفقیت ندارد → خودشناسی دروغین.
3. تسک `organism-watchdog` هنوز twin معمار را می‌دواند نه `watchdog.py` (از قبل مستند؛ کارت تازه نیست).

**فیکس:** `ok = False` فقط اگر برگشتی صریح `False` باشد؛ `None` mockهای قدیمی = موفقیت (رگرسیون phi-reset سبز ماند). رویداد `ok` می‌نویسد؛ `task.completed` فقط اگر ok.

| سنجه | قبل | بعد |
|---|---|---|
| ردیف‌های زنده با فیلد `ok` | **۰/۸۳** | قرارداد نو: هر رویداد بعدی `ok` دارد (تست False→ok=False) |
| `task.completed` روی restart=False | ادعا می‌شد | دیگر emit نمی‌شود |

## کارت رأی

1. **گارد همان DARE در `4d_system/core/model.py` + امضای مجدد TCB** (C-029). بدون این، `check_invariants` روی ρ=1 می‌ترکد و `anchors_ok=False`.
2. وصل کردن `SETTINGS_ANCHORS` به `run_self_test` (I_pred/Var_ex) — TCB `config`+`core`.

## تست‌های نو (ثبت run_all نشده)

- `_ops/tests/test_sog_floor_guards.py` (نو)
- `_ops/tests/test_selfheal_ok_field.py` (نو)
- سه مورد افزوده به `test_money_gate.py` (از قبل در run_all است)

## آیا اختاپوس بهتر شد؟ با کدام عدد؟

بله: **۵ ترکیدگی ریاضی ارگانیسم → ۰**؛ **۲/۲ مبلغ منفی که گیت پول را دور می‌زدند → ۰**؛ دفتر خودترمیمی از «۸۳ رویداد بی‌ok» به قرارداد `ok` اجباری رسید. TCB هنوز همان ۵-کلاس ترکیدگی را دارد تا رأی امضا.
