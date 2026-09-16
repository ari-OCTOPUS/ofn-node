---
type: prompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [pulse, doctor, sog, cardiac, simulation]
created: 2026-07-10
updated: 2026-07-10
aligns_to: "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
extends: "[[04 - Architect System/SOG-Doctor-Synthesis-A-K]]"
---

> **یادداشتِ ویرایشگر (Claude · 2026-07-10) — قبل از اجرا بخوان:**
> این build-prompt توسطِ یک workflowِ چند-ایجنتی ساخته و توسطِ ۳ منتقدِ ایمنی سخت شد. چون workflow در یک **git-worktreeِ جدا** اجرا شد، در «بخش ۰» گزارش کرد که `SOG-Doctor-Synthesis-A-K.md` و `ADR-001` «وجود ندارند». **این نادرست است — هر دو در vaultِ زنده موجودند:**
> - `04 - Architect System/SOG-Doctor-Synthesis-A-K.md` (سنتزِ A–K، ۱۹۹ ادعای تگ‌دار، evidence-map)
> - `06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged.md`
>
> پس coding agent باید از **همین نوت‌های موجود** استفاده کند و **`ADR-001` را بازنویسی نکند** (وگرنه supersede-chain کثیف می‌شود). محتوای «§C/E/F/G» هم در همان synthesis هست، علاوه بر فایل‌های `Desktop/4D`.
>
> **سیستمِ SOG-learner واقعاً ساخته شده:** `C:\Users\Armin\Desktop\4d_system` — `core/scores.py` (SMS=Δ_self، SLS=E_shadow)، `core/model.py`، `core/simulator.py` (harnessِ آماده). **مرزِ $0/پولی (رعایت کن):** `core/` ریاضیِ خالصِ numpy = **$0**؛ `brain/`+`llm/` = پولی. پس ضربان از **scoreهای $0** برانده شود؛ تحقیقِ LLM پشتِ **live-gate** (تا ۲۰۲۶-۰۷-۲۱). الگوی اتصال: `4d_system` scoreها را در یک state-file می‌نویسد → کنترلِ ضربانِ ارگانیسم (stdlib) می‌خواند؛ ارگانیسم stdlib-only می‌ماند.
>
> **سه گاردریلِ کلیدی که منتقدها اضافه کردند (رعایتشان اجباری است):** (۱) **تقارنِ accelerator/brake** — Δ_self (شتاب) هم مثلِ σ (ترمز) باید external/read-only باشد، وگرنه self-grading = محورِ سرطان؛ (۲) **Gate-0** — تا یک estimatorِ زندهٔ Δ_self با provenanceِ درست نساخته‌ای، production wiring بلاک است (فقط sim + shadowِ constant)؛ (۳) **seamِ درست** = حلقهٔ متابولیسمِ `organism.py:418-427`، **نه** Pacemaker/HLCِ `chrono.py` (که دست‌نخوردنی است).

---

# BUILD-PROMPT — «M-Heart / SOG-Pacemaker»: کوپلِ SOG ↔ Doctor ↔ Heart به‌صورتِ یک اندام، با ضربانِ ظاهرشونده

> **نوع:** octopus build-prompt (self-contained) · **مالک:** ari · **تاریخ:** 2026-07-10 · **حالت اجرا:** SIMULATE-FIRST → SHADOW → (بعداً) flag-gated wiring
> **قاعدهٔ اساسی این پرامپت:** هیچ معادلهٔ اعتبارسنجی‌نشده حق ندارد ضربانِ واقعی را براند — و هیچ **راننده‌ای** (نه شتاب‌دهنده، نه ترمز) حق ندارد از stateِ خودِ ارگانیسم تغذیه شود. تا قفل‌شدن، فقط SHADOW.
> **مخاطب:** یک coding agent که این سند را سرتاسر اجرا می‌کند. کد را **بازاستفاده** کن؛ **هرگز fuse نکن**.
> **دو محورِ تقارن که این نسخه اصلاح می‌کند:** (۱) شتاب‌دهنده (Δ_self) دقیقاً همان انضباطِ provenance را می‌گیرد که ترمز (σ) دارد — هر دو باید از منبعِ read-only و external-to-organism بیایند، وگرنه self-grading = محورِ سرطان. (۲) اثباتِ کران‌داری باید **closed-loop** باشد؛ open-loop هیچ‌وقت گیت نیست.

---

## بخش ۰ — پیش‌شرط‌های واقعیت (قبل از یک خط کد، این‌ها را بخوان و بپذیر)

پنج یافتهٔ زمینی که این پرامپت رویشان بنا شده — اگر با آن‌ها اختلاف دیدی، **STOP** و در `00 - Inbox/AGENT_QUESTIONS.md` بنویس:

1. **`04 - Architect System/SOG-Doctor-Synthesis-A-K.md` وجود ندارد.** محتوای «synthesis» بیرونِ vault است:
   - `C:/Users/Armin/Desktop/4D/4.py` — **تنها executable که هر عددِ SOG را validate می‌کند** (۴۸۷۷ بایت، clean run).
   - `C:/Users/Armin/Desktop/4D/SOG-multiagent-handoff.md` و `…handoff 2.md` — بریف/ledgerِ بازتولید.
   - `C:/Users/Armin/Desktop/4D/برداشت_من_از_دو_فایل….md` — استخراجِ E_shadow / I_pred (**self-marked ۱/۳ = unlocked**).
   - `C:/Users/Armin/Desktop/4D/12121212.txt` — بازگوییِ روایی (بدون محاسبهٔ مستقل).
   هر ارجاعِ این سند به «§C/E/F/G» یعنی این چهار فایلِ 4D.

2. **`06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged.md` وجود ندارد.** grepِ کل‌ریپو برای `HeartParams|HeartSignal|coupled-not-merged|Pulse-Source` = صفر. پس ADR-001 و interfaceِ typed **باید در همین کار authored + ratified شوند** — نه اینکه از یک artifactِ قفل‌شده خوانده شوند. (این‌که پرامپت می‌گفت «already locked» نادرست است؛ ساختنش deliverableِ فاز صفر است.)

3. **E_shadow و I_pred در این codebase نیستند** (grep در cardiac/chrono/replication = صفر) و در هیچ نوتِ داخلِ vault هم نیستند. فقط در 4D. طبقِ گاردریل، **unlocked** می‌مانند.

4. **«ضربان» کدام حلقه است — تثبیتِ seam (اصلاحِ تناقضِ نسخهٔ قبل).** grep تأیید می‌کند که `cardiac.effective_period()` هیچ‌گاه ضربانِ Pacemakerِ chrono/HLC را نمی‌راند: `chrono` هرگز `cardiac` را import نمی‌کند و Pacemaker با `PERIOD_S=60` ثابت start می‌شود (`chrono.py:646`) بدونِ آرگومانِ period (`organism.py:207-208`). تنها مصرف‌کنندهٔ واقعیِ `effective_period()` این است: **`organism.py:418-421`** که `_sleep_s = _eff["period_s"]` را می‌خواند و در `organism.py:427` `time.sleep` می‌کند. **بنابراین «ضربانِ زنده»ای که این پرامپت مدوله می‌کند صراحتاً حلقهٔ متابولیسمِ `organism.py:418-427` است — نه Pacemakerِ HLC.** تمام زبانِ نسخهٔ قبل دربارهٔ `pacemaker.period_s` / `chrono.py:631` **حذف شده**. `chrono.py` دست‌نخوردنی می‌ماند و هیچ mutationِ آینده‌ای رویش تعریف نمی‌شود مگر با sign-offِ صریحِ مالک (چون به دیوارِ HLC می‌چسبد).

5. **راننده باید یک producerِ زندهٔ واقعی داشته باشد (Gate-0) — وگرنه فقط sim.** grep در `_ops` برای `Delta_self|E_shadow|sog_period` = صفر. Δ_self امروز فقط (a) ثابتِ آفلاین `0.122520` و (b) excess-streamِ مصنوعیِ `4.py:82-90` است — هیچ‌کدام «self-modelِ اطلاعاتِ زندهٔ ارگانیسم» نیستند. **بنابراین:** تا وقتی یک estimatorِ زندهٔ Δ_self با provenanceِ درست (بخش ۲.۴، Gate-0) وجود ندارد، production wiring **بلاک** است؛ deliverableِ این build یا sim-only + shadowِ constant است، یا شامل Gate-0. هرگز وانمود نکن ضربانِ زندهٔ emergent داری در حالی که یک anchorِ منجمد می‌خورانی.

**اولین کارِ اجرایی:** اجرای `python C:/Users/Armin/Desktop/4D/4.py` و ثبتِ اینکه این anchorها بازتولید می‌شوند (اگر نه، کلِ کار STOP):
`Δ_self=0.122520, Var(ex)=0.217327, Var_eff=0.208232, ceiling=0.804719, N=4685`.

---

## بخش ۱ — ماموریت و آشتیِ coupled-not-merged (چرا ضربان باید «ظاهر شود»)

### ۱.۱ ماموریت (owner: ari)
SOG self-learning system + evolutionary Doctor + Heart را یک «مهم‌ترین اندام» کن که **beat-rateِ کلِ ارگانیسم زنده (emergent)** شود — رانده‌شده با ریاضیاتِ نوِ SOG. **اول ADAPT + SIMULATE (offline، $0)**، بعد هر wiringِ واقعی.

### ۱.۲ آشتیِ غیرقابل‌مذاکره (ADR-001 — که همین‌جا می‌نویسیم)
> **«یک دستگاهِ دینامیکی، دو/سه ماژولِ نرم‌افزاری — COUPLED، نه MERGED.»**

وحدت را با **کوپل‌کردن** می‌سازیم: `SOG-learner → Doctor → Heart`، با معادلاتِ SOG به‌عنوانِ **قانونِ کنترل (control law)** — نه با ذوبِ کد در یک god-module. fusion **رد** است چون بازمی‌سازد:
- **(a) حلقهٔ حرام (دوطرفه):** ماژولی که سیگنالِ عمل را هم **می‌سنجد** و هم برای عمل **مصرف** می‌کند = self-grading → reward-hacking → **محورِ سرطان**. این هم برای **ترمز (σ)** صادق است و هم برای **شتاب‌دهنده (Δ_self)**. نسخهٔ قبل فقط σ را external/unforgeable کرده بود و Δ_self را self-measured رها؛ این تقارنِ شکسته خودش محورِ سرطان بود و این نسخه می‌بنددش.
- **(b) دامنهٔ خطای مشترک:** crashِ ماژولِ پیچیدهٔ در حالِ تکامل = توقفِ ضربان = مرگ، بدونِ reaperِ برون‌حلقه.
- **(c) عدم‌تطابقِ timescale (fast/slow) و formalism.**

راه‌حل: ماژول‌های جدا با **یک interfaceِ typed** (بخش ۵). Doctor = مدولاتورِ **کُند (w-slow)**؛ Heart = ضربانِ **تند**؛ σ = گیتِ سلامتِ بیرونی؛ **Δ_self هم مثلِ σ از یک منبعِ read-only و external-to-organism** تغذیه می‌شود.

### ۱.۳ ADR-001 — کانالِ کوپل «هرگز scalar rate نیست»
> **قانون:** Doctor→Heart فقط **setpointهای typed (`HeartParams`)** رد و بدل می‌کند؛ Heart خودش از setpointها دوره را می‌سازد. **هیچ scalar period به‌عنوانِ کانالِ کوپل تزریق نمی‌شود.**

نسخهٔ قبل این را دوگانه گفته بود (params typed در بخش ۵، ولی scalar `period_raw` تزریق‌شده در بخش ۲/۴/۷). این نسخه یک‌دست می‌کند: قانونِ SOG **`HeartParams` می‌سازد**، و `cardiac` با plumbingِ افزودنیِ خودش آن setpointها را به period تبدیل می‌کند. اگر یک scalarِ `sog_period_s` هم محاسبه شود، **صرفاً diagnostic/log است و هرگز کانالِ کوپل نیست** (بخش ۴).

### ۱.۴ چرا «ظاهر شدن»
ضربانِ فعلی یک تایمرِ ثابت است. زندگی یعنی دورهٔ ضربان از **self-modelِ اطلاعات‌محورِ خودِ ارگانیسم** بیرون بیاید نه از یک ثابت:
- **Δ_self بالا** (بهرهٔ self-model → یادگیریِ فعال) → `baroreflex_gain` بالاتر → ضربانِ **تندتر/عمیق‌تر** — **مشروط به provenanceِ درستِ Δ_self**.
- **E_shadow پایدار** (ساختارِ پنهانِ ته‌نشین‌شده) → `target_mass_scale` → ضربانِ **استراحتیِ کندتر** — **فقط پس از lock**.
- **σ** (از رویدادهای **CONFIRMED LANGAR**) → **گیتِ سختِ سلامت / cap** — فقط کند/متوقف، هرگز شتاب.
این همان milestoneِ «FHN-successor / M-heart» است، اما با SOG به‌عنوانِ ریاضیات.

---

## بخش ۲ — قانونِ کنترلِ «ضربانِ زنده» (Living-Beat Control Law)

### ۲.۱ نگاشتِ صریح `{Δ_self, E_shadow, σ, budget} → HeartParams → period_s`
seamِ واقعیِ Heart این است: `cardiac.py:220 effective_period()` — advisory، dict برمی‌گرداند، و در `cardiac.py:238` hard-clamp می‌شود. ثابت‌ها (`cardiac.py:40-42`): `BASE_PERIOD_S=60.0`، `BIO_RESTING_FLOOR_S=30.0`، `BIO_MAX_PERIOD_S=900.0`. قانون **HeartParams** می‌سازد؛ نگاشتِ deterministicِ Heart آن‌ها را به period می‌برد. pseudocode زیر نگاشتِ کامل و **مرتبهٔ گاردهاست** (هر خطِ ترمز قبل از گیتِ بعدی):

```text
# ============================================================
#  همه‌ی رانندگان از منبعِ read-only/external تغذیه می‌شوند
#  (بخش ۲.۴). هیچ operand از stateی که Doctor/Heart می‌نویسد نمی‌آید.
# ============================================================

# ---- (0) Δ_self و ceiling به‌صورتِ زنده با فراخوانیِ P_closed، نه literal ----
Delta_self       = P_closed(live_inputs).delta_self      # reused 4.py:4-8 ; NEVER a hard-coded 0.122520
Delta_self_ceil  = ceiling_from(live_inputs)             # NEVER a hard-coded 0.804719
# provenance-assert: operandهای S,S_b باید از selfmodel_state() (بخش ۲.۴) بیایند؛
# اگر منشأشان یک state-fileی است که Doctor/Heart نوشته -> REJECT مثلِ σِ Doctor-authored.
assert selfmodel_provenance_ok(live_inputs)              # else -> whale + STOP + AGENT_QUESTIONS

# ---- (1) drift-guard: عبور از سقفِ pre-registered یعنی operand drift/gaming ----
if Delta_self > Delta_self_ceil * (1 + DRIFT_EPS):
    raise_drift_flag(); period = BIO_MAX_PERIOD_S; STOP_and_ask()   # هرگز زیرِ floor نمی‌راند
    return HeartParams(...whale...)

# ---- (2) هر دو gain صریحاً clamp — تقارن با g_rest ----
g_learn = clamp(Delta_self / Delta_self_ceil, 0.0, 1.0)   # <== EXPLICIT clamp (بود: فقط کامنت)
g_rest  = clamp(E_shadow   / E_shadow_ref,   0.0, 1.0)

# ---- (3) w_shadow فقط از فایلِ قفل بارگذاری می‌شود، هرگز literal ----
w_shadow = load_w_shadow_from_lock()   # 0.0 UNLESS فایل معتبر ∧ e_shadow_locked ∧ hashِ 4.py ∧
                                       # E_shadow/E_shadow_ref در-حال-استفاده byte-match قفل (بخش ۴)

# ---- (4) هدفِ خام قبل از هر ترمز ----
period_raw = BASE_PERIOD_S * exp( -k_fast*g_learn + w_shadow*k_slow*g_rest )

# ---- (5) ترمزِ بودجه: BeatBudget به‌عنوانِ ترمزِ درجه‌یک، قبل از گیتِ σ ----
#      وقتی remaining->0 ، budget_pressure -> بزرگ ، period به‌سمتِ whale یکنوا بالا می‌رود.
period_raw *= budget_pressure(BeatBudget.status().remaining)   # >= 1.0 ، monotone

# ---- (6) گیتِ سلامت — fail SAFE ----
sig = read_sigma_record()          # {value, produced_at, origin, producer}  از replication-latest.json
if sig is MISSING or UNPARSEABLE:                 period = BIO_MAX_PERIOD_S   # <== fail closed (بود: 0/healthy)
elif age(sig.produced_at) > SIGMA_MAX_STALENESS_S: period = BIO_MAX_PERIOD_S   # stale -> whale
elif sig.origin != "replication-loop" or sig.producer in {"doctor","heart"}:  # runtime taint
                                                   period = BIO_MAX_PERIOD_S   # forged sigma -> whale
elif sigma_now(sig) > 1.0:                          period = BIO_MAX_PERIOD_S   # constitutional σ<=1 cap
else:
    period = period_raw * cap_factor(zone(sig))    # monotone slow as σ->1 ; healthy=1.0

# ---- (7) کفِ نرخ هرگز از refreshِ σ تندتر نیست ----
floor = max(BIO_RESTING_FLOOR_S, SIGMA_REFRESH_INTERVAL_S)   # <== accelerator نمی‌تواند از cap جلو بزند
period = max(floor, min(BIO_MAX_PERIOD_S, period))           # existing clamp = last word (cardiac.py:238)

# ---- خروجی: HeartParams، نه scalar (ADR-001) ----
return HeartParams(baroreflex_gain=g_learn_map(g_learn),
                   target_mass_scale=(g_rest_map(g_rest) if w_shadow>0 else 1.0),
                   daily_beat_cap=ABSOLUTE_BUDGET_CAP,        # <== از بودجهٔ external، نه از σ (بخش ۲.۵)
                   ...)
# period بالا فقط diagnostic/shadow است؛ کانالِ کوپل = HeartParams.
```

`cap_factor(zone)`: `healthy → 1.0`، `pre-replication → 1.0`، `cancer-axis` هرگز به این شاخه نمی‌رسد (veto). با نزدیک‌شدنِ σ به ۱ یک منحنیِ یکنوای کندکننده (مثلاً `1 + α·σ_now`) اعمال کن.

`budget_pressure(remaining)`: تابعِ یکنوای `≥1.0`، در `remaining=full → 1.0`، `remaining→0 → ` بزرگ (کشاننده به whale). این **ترمزِ منفیِ واقعی** است که در نسخهٔ قبل با clampِ cardiac می‌جنگید؛ حالا **درونِ** قانون است.

پارامترها در `pulse_control.py` (env-tunable، دیفالتِ محافظه‌کار): `k_fast≈0.7, k_slow≈0.7, α≈0.5, DRIFT_EPS≈0.02` — **مقدارِ نهایی را sim تعیین می‌کند، نه حدس.**

### ۲.۲ کدام معادله مجاز است ضربان را براند — و کدام ممنوع

| کمیت | وضعیت | نقش در قانون v1 |
|---|---|---|
| **Δ_self** = ½·log(S_b/S) (op-point 0.122520) | **CANONICAL** (`4.py:31,34`، MC within 3σ) | **مجاز** — تنها راننده در v1؛ **زنده با P_closed محاسبه، نه literal** |
| **Δ_self ceiling** = ½·log(1+σ_d²/σ_ζ²) (op-point 0.804719) | **CANONICAL** (`4.py:60`) | **مجاز** — نرمال‌ساز/سقفِ g_learn؛ زنده محاسبه؛ عبور از آن = drift-flag+STOP |
| Var(ex)=0.217327، Var_eff=0.208232، N=4685 | **LOCKED/CANONICAL** | برای sim/budget، نه مستقیم در period |
| **E_shadow** = ½·log(σ_z²/S_b) (op-point 0.012553) | **UNLOCKED (۱/۳)** — در 4.py نیست؛ تناقضِ 0.135041 vs 0.135073 | **ممنوع** تا Gate-A با **MC-witness**. `w_shadow=0`. |
| **E_shadow_ref** (نرمال‌سازِ g_rest) | **UNLOCKED — knobِ آزادِ تعریف‌نشده** | باید در قفل با re-derivation + MC-witness وارد شود؛ وگرنه g_rest بی‌معنا |
| **I_pred** = ½·Σ log(S_L/S_b) | **UNLOCKED + value-conflict** (0.014422 vs 0.0144179) | **هیچ‌چیز را گیت نمی‌کند** (decoration)؛ runtime gate `i_pred_locked` را نادیده می‌گیرد |
| σ_z² = λ²(σ_ζ²+σ_d²)/(1−ρ²)+σ_ε² | **UNLOCKED** (در 4.py نیست) | **از primitiveهای 4.py بازساخته می‌شود**؛ literalِ 0.0141667 ممنوع به‌عنوانِ ورودی |

**قاعدهٔ آهنین:** در v1 فقط `Δ_self` و `Δ_self_ceiling` (هر دو 4.py-backed، **زنده‌محاسبه**) ضربان را می‌رانند. `w_shadow ≡ 0` مگر قفل. `I_pred` هیچ گیتی ندارد. σ فقط **کند/متوقف** می‌کند، هرگز شتاب.

### ۲.۳ پایداری — **closed-loop، با اثباتِ loop-gain** (نه open-loop)
runaway که باید رد شود ذاتاً feedback است: `ضربانِ تندتر → فعالیت/زمانِ بیشتر → innovationهای اندازه‌گیری‌شدهٔ بزرگ‌تر → Δ_self بالاتر → ضربانِ تندتر`. تزریقِ streamِ **از پیش‌ضبط‌شده** (open-loop) این لبه را **حذف** می‌کند و اثبات بی‌اعتبار است. پس:

- یک **plant/response model** `r(beat)` تعریف کن: نرخِ ضربان → نرخِ فعالیت → operandهای S/S_b (حتی یک پاسخِ monotoneِ خام کافی است).
- حلقه را ببند: `Δ_self_{t+1} = f(beat_t)`.
- **اثباتِ صریحِ انقباض (contraction):** بهرهٔ مرکب
  `G = (dΔ_self/dactivity) · (dactivity/dbeat) · (dbeat/dΔ_self)`
  باید در **کلِ گریدِ Δ_self** `< 1` باشد. مقدارِ `G` اندازه‌گیری‌شده در گزارش ثبت شود.
- **FAIL** اگر `G ≥ 1` یا اگر دوره روی ریلِ clamp (30 یا 900) بنشیند (pin).
- تستِ open-loop حفظ می‌شود اما **گیت نیست** — فقط سلامتِ فرمول را چک می‌کند.

### ۲.۴ provenanceِ راننده‌ها (تقارنِ Δ_self با σ) — `selfmodel_state()`
operandهای `S/S_b` که Δ_selfِ زنده را می‌سازند **باید** توسطِ یک ماژولِ read-only محاسبه شوند که نه Doctor نه Heart رویش نمی‌نویسد — آینهٔ `replication.py`:
- یک `selfmodel_state()` جدید روی یک **measurement streamِ append-only و external-to-organism** (همان انضباطِ ledgerِ APPROVAL). Doctor/Heart فقط می‌خوانند.
- Gate-B باید assert کند مسیرِ operandِ Δ_self **از هیچ state-fileی که Doctor/Heart می‌نویسد سرچشمه نمی‌گیرد**.
- **contract test:** یک Δ_self که operandهایش به state نوشته‌شدهٔ ارگانیسم trace می‌شوند باید **دقیقاً مثلِ σِ Doctor-authored رد شود** (whale).
- **decouple reward:** ضربانِ تندتر نباید به آنچه Δ_self را set می‌کند stepِ بهینه‌سازیِ بیشتری بدهد (بخش ۲.۶ + governor tick بخش ۵).

> **Gate-0 (پیش‌شرطِ production):** تا وقتی `selfmodel_state()`ی که Δ_selfِ زنده را از سیگنالِ واقعیِ runtime می‌سازد وجود ندارد، production wiring بلاک است و shadow با مقدارِ constant کار می‌کند. مشخص کن **کدام ماژول و کدام سیگنالِ واقعی** Δ_self را می‌سازد.

### ۲.۵ provenanceِ **مخرجِ** σ (سوراخِ denominator)
`σ = approved / max(1, active_cells)` (`replication.py:63-64`). `approved` external/APPROVAL است، اما `active_cells` سمتِ ارگانیسم؛ **باد کردنِ active_cells → کاهشِ σ زیرِ ۱ → خلع‌سلاحِ cap**. اصلاح:
- `active_cells`ِ مخرج از **همان منبعِ append-only/attribution-gated** که `approved` می‌آید (یا یک census منجمد که ارگانیسم وسطِ سیکل نمی‌نویسد)، **snapshot per-evaluation**.
- تصمیمِ cap علاوه بر نسبت، روی یک **سقفِ مطلقِ approved-count** هم کلید بخورد (نه فقط ratio).
- **guard/test:** یک active_cellsِ باد‌شده که σ را زیرِ ۱ می‌برد **نباید** cap را شل کند.
- مستند کن: تنها **numerator** همیشه unforgeable بود؛ این نسخه denominator را هم می‌بندد.

### ۲.۶ ایزولاسیونِ علّی + lag (Doctor خودش را از طریقِ ساعت grade نکند)
پس از wiring، `baroreflex_gain ← g_learn(Δ_self)` و Δ_self از فعالیتی می‌آید که انتخاب‌های خودِ Doctor باعثش‌اند → حلقهٔ خودتقویتی. اصلاح:
- پنجرهٔ Δ_self که `HeartParams`ِ سیکلِ `t` را set می‌کند باید روی فعالیتی سنجیده شود که **پیش از** actionِ Doctorِ سیکلِ `t` است و آن را **حذف** می‌کند (lag + exclusion).
- cadenceِ `run_cycle`/lift-measurementِ Doctor روی یک **ساعتِ governorِ ثابت** cap شود که قانونِ SOG **نمی‌تواند تندش کند** — ضربانِ تندتر فقط رزولوشنِ زیرـ‌beat می‌دهد، نه stepِ بهینه‌سازی/grading بیشتر.
- **تستِ ساختاری:** فرکانسِ تصمیمِ مؤثرِ Doctor نسبت به دورهٔ ضربان **ناوردا** باشد («more clock ≠ more reward»).

---

## بخش ۳ — فاز شبیه‌سازی (اجباری، اول، $0 آفلاین)

خروجی: `_ops/sim/pulse_sim.py` + گزارشِ `state/sim/pulse-sim-report.json` با گیتِ pass/fail. stdlib خالص، بدونِ شبکه، بدونِ نوشتن روی هیچ stateِ زنده.

### Gate-A — re-derive + **MC-witness** + pre-register + LOCK (MUST-LOCK-FIRST)

engineِ sim باید `P_closed` را از `4.py:4-8` **بازاستفاده** کند (import یا کپیِ verbatim با تستِ برابری). **هیچ lock فقط با «خودتوافقیِ scalar» مجاز نیست** — هر قفل به یک **شاهدِ مستقلِ Monte-Carlo** نیاز دارد، دقیقاً همان‌طور که 4.py مقدارِ Δ_self را با emp-vs-theory within 3σ اعتبارسنجی می‌کند.

1. **σ_z² از primitiveها بازساخته می‌شود، نه literal.** `σ_z²` را از همان ثابت‌های اولیهٔ 4.py (`rho, lam, se2, sz2, sd2` در operating point) بساز و **byte-equalityِ آن primitiveها را با مقادیرِ بخش‌ ۲ِ 4.py assert کن**، سپس `σ_z²` و `E_shadow` را از آن‌ها محاسبه کن. **ممنوع:** `0.0141667`, `0.012553`, `0.135073` هرگز به‌عنوانِ **ورودی/operand** ظاهر نشوند — فقط به‌عنوانِ anchorِ مقایسهٔ post-hoc در تست.

2. **E_shadow با MC-witness.** `E_shadow = ½·log(σ_z²/S_b)`:
   - `σ_z²` را **تجربی** به‌صورتِ `Var(z)` با `z = λ·s + ε` از MC-streamِ 4.py تخمین بزن؛ `S_b` از `Var(nub)`ِ تجربی (MC-confirmed در `4.py:96`).
   - **قفل فقط اگر** closed-formِ E_shadow با تخمینِ MC **within 3σ** بخواند.
   - معیارِ identity را فقط با کمیت‌های 4.py-backed بیان کن: `½log(σ_z²/S_b) + Δ_self = ½log(σ_z²/S)`، با `σ_z², S` anchor به MC.
   - **تناقضِ 0.135041 vs 0.135073** فقط با همین شاهدِ MC حل شود (نه با انتخابِ عددِ خودِ کد).
   - **اگر هیچ MC-witness ساخته نشد → `e_shadow_locked=false` اجباری.** هرگز با self-agreementِ scalar قفل‌شدنی نیست.

3. **E_shadow_ref هم قفل‌شونده است.** `e_shadow_ref` را با re-derivation خودش (مثلاً آنالوگِ سقفِ shadow `½log(1+σ_d²/σ_ζ²)` یا یک scaleِ MC-anchored) و **MC-witness** وارد قفل کن. گیتِ runtimeِ w_shadow باید `E_shadow_ref`ِ در-حال-استفاده را هم byte-match قفل بخواهد.

4. **I_pred — بیرونِ AUTHORIZATION.** سری Riccati `½·Σ log(S_L/S_b)` را با MC-witness بسنج و **تناقضِ 0.014422 vs 0.0144179** را حل کن. اما `i_pred_locked` **هرگز هیچ ضریبی را فعال نمی‌کند**؛ اگر با MC حل نشد → `i_pred_locked:false` و `i_pred_gates:none` صریح ثبت شود. runtime gate این فلگ را **نادیده** می‌گیرد.

5. **خروجیِ lock:** `state/sim/PULSE-EQUATIONS-LOCKED.json` با: مقادیرِ نهایی، **هش/ورژنِ 4.py**، **version-hashِ تابعِ `sog_period`** (بخش ۴)، `E_shadow` و `E_shadow_ref`ِ قفل‌شده، تاریخ، و `e_shadow_locked/i_pred_locked: true|false`. **این فایل تنها منبعِ اجازهٔ `w_shadow≠0` است** — و فقط از طریقِ **load در runtime**، نه literal.

### Gate-B — اثباتِ closed-loop خوش‌رفتاریِ دینامیک (offline)

3. **کران‌داری (open-loop، غیرگیت):** روی کلِ Δ_self گرید اثبات کن `period ∈ [floor, 900]` — بدونِ runaway/صفر/منفی. (کمکی، نه گیت.)
4. **closed-loop + loop-gain (گیت):** با plant `r(beat)` حلقه را ببند؛ `G` را در کلِ گرید بسنج؛ **FAIL اگر `G≥1` یا دوره روی ریلِ clamp pin شود.** `G` در گزارش.
5. **احترامِ σ-cap + fail-safe:** تستِ صریح — `Δ_self` بیشینه + `σ=1.2` → `period=900`؛ **σ غایب → 900؛ σ کهنه (age>staleness) → 900؛ refreshِ σ کندتر از beat → floor بالا می‌رود.**
6. **taint canary (runtime، نه static):** یک رکوردِ σِ **Doctor-authored** (origin/producer دستکاری‌شده) به `replication-latest.json` تزریق کن و assert کن قانون آن را **رد** می‌کند (whale)، نه اینکه مصرفش کند.
7. **provenanceِ Δ_self:** contract test — Δ_selfی که operandهایش به state نوشتهٔ Doctor/Heart trace می‌شوند **رد** شود (whale)؛ assert مسیرِ operand از `selfmodel_state()` می‌آید.
8. **denominatorِ σ:** active_cellsِ باد‌شده که σ را زیرِ ۱ می‌برد **نباید** cap را شل کند؛ سقفِ مطلقِ approved-count اعمال شود.
9. **ترمزِ بودجه:** با `remaining→0`، `sog_period` **یکنوا** به‌سمتِ whale بالا برود، صرف‌نظر از هر Δ_self.
10. **drift-guard:** `Δ_self > ceiling` **نباید** دوره را زیرِ floor براند و **باید** drift-flag بزند.
11. **decision-frequency invariance:** فرکانسِ مؤثرِ تصمیمِ Doctor نسبت به دورهٔ ضربان ناوردا (governor tick).
12. **بازگشت‌به‌resting:** بعدِ spikeِ Δ_self، با آرام‌شدنِ سیگنال period به baseline برمی‌گردد (نه pin).
13. **guard مقابلِ 4.py:** اگر sim با anchorهای 4.py مخالفت کرد → باگ در **خودِ sim** → STOP و report.

### گزارش و گیت
`pulse-sim-report.json` شاملِ: هر anchor + pass/fail، `G`ِ closed-loop، بازهٔ period، و **وضعیتِ per-equation به‌صورتِ un-collapsible: `locked | excluded-unlocked`**. برای اینکه `SIM_PASS` با هر چیزِ unlocked=true شود، **فیلدهای owner-acknowledged** لازم‌اند: `e_shadow_excluded:true` / `i_pred_excluded:true`. «سبز» هرگز بدونِ بیانِ صریحِ اینکه کدام معادله **validated** و کدام **excluded** است render نمی‌شود.

**گیتِ کلی:**
```
SIM_PASS = Gate-B(all closed-loop gates) ∧ loop_gain G<1
         ∧ ( e_shadow_locked==true  ∨  e_shadow_excluded==true )   # owner-ack اگر excluded
         ∧ ( i_pred: gates-nothing، همیشه بیرونِ authorization )
```
(اگر E_shadow قفل نشد، sim می‌تواند pass شود ولی **فقط** با `w_shadow=0` دائمی و `e_shadow_excluded` صریح.)

---

## بخش ۴ — گیتِ اتصال به production (تا آن لحظه: SHADOW)

اتصالِ واقعی فقط پشتِ **همهٔ** این‌ها:
```
PRODUCTION_WIRE = SIM_PASS
               ∧ equations-locked (state/sim/PULSE-EQUATIONS-LOCKED.json present & schema-valid)
               ∧ live Δ_self producer exists (Gate-0 satisfied)      # بدونِ آن، production بلاک
               ∧ sog_period version-hash == recorded lock hash       # identityِ sim↔production
               ∧ flag OCTOPUS_WIRE_BIO == on
               ∧ flag OCTOPUS_WIRE_PULSE == on
               ∧ owner activation (ACTIVATION-PULSE.flag present)
               ∧ date >= 2026-07-21
```

**تا آن لحظه: SHADOW.** قانون محاسبه می‌کند «ضربان **چه می‌شد**»، اما هرگز `organism.py:421`'s `period_s` را عوض نمی‌کند.

- **seamِ زنده = `organism.py:418-427`** (اصلاحِ بخش ۰.۴). shadow **هرگز `sog_period_s` را داخلِ همان dictی که `period_s` از آن مصرف می‌شود نمی‌نویسد.** به‌جایش، مقدارِ سایه به یک **sinkِ append-onlyِ جدا** می‌رود: `state/pulse/heart-params-shadow.jsonl`، و `effective_period()` **dictِ اصلی را دست‌نخورده برمی‌گرداند**.
  - **تستِ regression:** `effective_period()['period_s']` با و بدونِ فعال‌بودنِ محاسبهٔ shadow **bit-identical** است.
  - **تستِ static:** `organism.py` هیچ کلیدی جز `'period_s'` نمی‌خواند.
- **`w_shadow` فقط load می‌شود، هرگز literal.** در `pulse_control.sog_period()`، `w_shadow` را با خواندنِ `PULSE-EQUATIONS-LOCKED.json` در لحظهٔ فراخوانی محاسبه کن و `0.0` برگردان مگر: (فایل موجود ∧ schema-valid ∧ `e_shadow_locked==true` ∧ hashِ ثبت‌شدهٔ 4.py == hashِ فعلی ∧ `E_shadow`/`E_shadow_ref`ِ در-حال-استفاده byte-match قفل). **هیچ شاخه‌ای `w_shadow` را از یک ثابت assign نمی‌کند.** تست: flip کردنِ `e_shadow_locked` به false یا corruptِ hash → دوره **bit-identical با نتیجهٔ `w_shadow=0`**.
- **کانالِ کوپل = HeartParams، نه scalar.** production period از `cardiac`ی می‌آید که `HeartParams` را مصرف می‌کند (بخش ۵)؛ `sog_period_s` فقط diagnostic/log است.
- **identityِ sim↔production:** `cardiac` باید **دقیقاً همان symbolِ `pulse_control.sog_period`** را import و call کند (no copy/fork). `version-hash`ِ آن در قفل ثبت و در runtime gate چک می‌شود؛ `pulse_sim` هم از همان entry point می‌گذرد.
- **HLC/EffectorGate/kill-switch را لمس نکن** (`chrono.py:335-405, 625`). `chrono.py` دست‌نخوردنی است و هیچ mutationِ Pacemaker تعریف نمی‌شود مگر sign-offِ صریحِ مالک.

---

## بخش ۵ — Interface (ADR-001، دقیق و typed)

این‌ها را در `_ops/pulse_control.py` به‌صورتِ `@dataclass(frozen=True)` تعریف کن. **هرگز scalar rate کانالِ کوپل نیست.**

```python
@dataclass(frozen=True)
class HeartParams:            # Doctor (w-slow) -> Heart. Doctor computes setpoints; Heart makes the period.
    target_sigma: float
    viable_band: tuple[float, float]
    epoch_seq: int
    target_mass_scale: float   # <- g_rest (E_shadow-driven; ONLY when locked, else 1.0)
    daily_beat_cap: int        # <- ABSOLUTE external budget, NOT sigma-zone (بخش ۲.۵)
    baroreflex_gain: float     # <- g_learn (Delta_self-driven، با provenance + lag)

@dataclass(frozen=True)
class HeartSignal:            # Heart -> Doctor. READ-ONLY to Doctor.
    beat_seq: int
    period_s: float
    sigma_now: float           # از CONFIRMED (replication.py) با origin/producer stamp — unforgeable
    baro_factor: float
```

- **Doctor → Heart:** `g_learn(Δ_self) → baroreflex_gain`؛ `g_rest(E_shadow) → target_mass_scale` (فقط پس از lock، وگرنه `1.0`)؛ **`daily_beat_cap` از بودجهٔ external-gatedِ مطلق، نه از σ** (چون σ خودش قابلِ خلع‌سلاح است). `target_sigma/viable_band/epoch_seq` بی‌تغییر.
- **Heart → Doctor:** `period_s, sigma_now, baro_factor` read-only.
- **plumbingِ جدیدِ cardiac (کارِ نو، نه seamِ موجود):** `effective_period` امروز هیچ‌کدام از این setpointها را به‌عنوانِ ورودی نمی‌گیرد (`bio_rhythm()` بدونِ mass — `cardiac.py:229`؛ `Baroreflex.current_factor()` فقط از stimuliِ زمانی — `cardiac.py:188-202`؛ `BeatBudget.daily_cap` در ساخت ثابت — `cardiac.py:108-110`). پس مسیرِ اعمالِ HeartParams **plumbingِ افزودنیِ flag-gated** لازم دارد: `bio_rhythm(mass=target_mass_scale*estimate_mass())`، ورودیِ gain برای Baroreflex، و یک BeatBudget cap قابلِ rebind. این‌ها **کارِ نو** فهرست می‌شوند، نه «یک‌خط».
- **σ از CONFIRMED + stamp:** `sigma_now` از `replication.sigma_state()` (`replication.py:61-75`) با `sigma = approved / max(1, active_cells)`؛ `approved` فقط از `type=="APPROVAL"` با `origin.loop=="replication"` (`replication.py:56`). **رکوردِ σ باید `origin`/`producer`/`produced_at` داشته باشد** تا taint-check و staleness در runtime کار کند. مخرجِ `active_cells` طبقِ بخش ۲.۵ snapshot/frozen است. (این veto صراحتاً روی **ناپایداریِ replication (spawn-branching)** گیت می‌کند؛ تأیید می‌کنیم که همین سیگنالِ سلامتِ موردنظرِ ضربان است، نه جانشینِ سلامتِ کلِ ارگانیسم.)
- **Doctor = مدولاتورِ w-slow با ایزولاسیونِ علّی:** Doctor `HeartParams` را در یک **stepِ shadowِ جدید در انتهای `run_cycle` (بعد از `submit_for_approval`، بعد از `doctor.py:618`)** محاسبه و به sinkِ typed می‌نویسد، هرگز Heart را mutate نمی‌کند. پنجرهٔ Δ_self که این setpointها را می‌سازد **actionِ همان سیکل را حذف می‌کند** (lag، بخش ۲.۶). cadenceِ `run_cycle` روی **governor tickِ ثابت** cap است که SOG تندش نمی‌کند.

---

## بخش ۶ — گاردهای ایمنی (paranoid checklist)

1. **هیچ حلقهٔ حرام — دوطرفه:** نه σ نه Δ_self از stateی که Doctor/Heart می‌نویسد نمی‌آید. σ از `replication.py` CONFIRMED با stamp؛ Δ_self از `selfmodel_state()` read-only. Doctor هر دو را فقط **می‌خواند**.
2. **provenanceِ Δ_self (تقارن با σ):** operandهای S/S_b از `selfmodel_state()`؛ Δ_selfِ organism-authored **رد** می‌شود مثلِ σِ Doctor-authored. reward decouple: beatِ تندتر stepِ بهینه‌سازیِ بیشتر به تنظیم‌کنندهٔ Δ_self نمی‌دهد.
3. **fail-SAFE σ:** غایب/کهنه/tainted/unparseable → `period=900`. هرگز default صفر/healthy.
4. **کفِ نرخ ≥ refreshِ σ:** `floor=max(BIO_RESTING_FLOOR_S, SIGMA_REFRESH_INTERVAL_S)`؛ accelerator نمی‌تواند از cap جلو بزند.
5. **denominatorِ σ بسته:** active_cells frozen/snapshot از منبعِ attribution-gated؛ سقفِ مطلقِ approved-count علاوه بر ratio.
6. **ترمزِ بودجه درجه‌یک:** `budget_pressure(remaining)` **درونِ** قانون، قبل از گیتِ σ؛ دو کنترلر نمی‌جنگند.
7. **g_learn و g_rest هر دو clamp:** `clamp(...,0,1)` صریح برای هر دو؛ `Δ_self>ceiling` → drift-flag+STOP، نه pinِ floor.
8. **w_shadow فقط load، هرگز literal:** از قفلِ معتبر با hashِ 4.py + byte-matchِ E_shadow/E_shadow_ref؛ وگرنه bit-identical با صفر.
9. **verifier-independence:** `LAMBDA_PERSIST=-1.0` تنها منبع (`doctor.py:187`)، imported؛ lift از `measured_lift(rfc, eval_fn=…)` (`evolution.py:125`) بیرونی؛ Doctor هرگز معیارِ خودش نمی‌سازد (`doctor.py:753,756`).
10. **ایزولاسیونِ علّی + governor tick:** فرکانسِ تصمیمِ Doctor نسبت به دوره ناوردا؛ Δ_self پنجرهٔ pre-action.
11. **held-out canary:** `evaluate_held_out(..., internal_metric_pass=<SOG self-claim>)` (`held_out_evaluator.py:169-217`)؛ واگرایی → `anti_hacking_flag` (`:200-204`). `FIXED_CANARY_TESTS` دست‌نخورده.
12. **reaperِ برون‌حلقه:** Heart و Doctor جدا؛ crashِ یکی ضربان را متوقف نمی‌کند.
13. **propose-only:** stepِ Doctor فقط رکوردِ shadow (مثلِ pendingِ ابدی، `doctor.py:435`)؛ هرگز merge/mutate/auto-apply.
14. **σ ≤ 1 + taint runtime:** `σ>1 → 900`؛ رکوردِ σ با origin≠replication یا producer∈{doctor,heart} → 900.
15. **kill-switch supremacy:** `run_forever` روی `STOP_ORGANISM.exists() or opslib.halted()` بی‌قیدوشرط return (`chrono.py:625`) — coupling لمس نمی‌کند.
16. **$0 تا 2026-07-21:** offline/stdlib/fail-soft؛ shadow هرگز `organism.py:421`'s period را نمی‌نویسد.
17. **fail-soft:** هر افزوده به `effective_period`/`run_cycle` exception را می‌بلعد و به رفتارِ قبلی fallback (`cardiac.py:266`, `doctor.py:543`).
18. **w_shadow=0 + I_pred decoration:** تا `e_shadow_locked:true`، `w_shadow=0` حتی در production؛ `i_pred_locked` هیچ ضریبی فعال نمی‌کند و runtime gate آن را نادیده می‌گیرد.

---

## بخش ۷ — فایل‌های جدید + ویرایش‌ها (grounded)

### فایل‌های جدید
| مسیر | نقش | نکته |
|---|---|---|
| `_ops/pulse_control.py` | **قانونِ pure/testable** + `HeartParams`/`HeartSignal` + `P_closed` (reused، تستِ برابری) + `sog_period(...)` که **HeartParams** می‌سازد و diagnostic period با نگاشتِ مشترکِ Heart می‌دهد؛ + `load_w_shadow_from_lock()` | بدونِ import از chrono/effects؛ فقط stdlib + خواندنِ state |
| `_ops/selfmodel_state.py` | **منبعِ read-onlyِ operandهای Δ_self** (آینهٔ `replication.sigma_state`) روی measurement streamِ append-onlyِ external-to-organism | Doctor/Heart فقط می‌خوانند؛ Gate-0 |
| `_ops/sim/pulse_sim.py` | **harness** (Gate-A lock+MC-witness، Gate-B closed-loop)، خروجی report | stdlib، offline، بدونِ نوشتن روی stateِ زنده |
| `_ops/sim/__init__.py` | package marker (اگر نیست) | — |
| `06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged.md` | **authored** ADR (بخش ۱.۲/۱.۳ + interfaceِ ۵ + گیتِ ۴) frontmatterِ کامل | deliverable |
| `state/sim/PULSE-EQUATIONS-LOCKED.json` | خروجیِ Gate-A: مقادیر + hashِ 4.py + version-hashِ `sog_period` + E_shadow/E_shadow_ref قفل | **تنها اجازهٔ `w_shadow≠0`، فقط via load** |

### ویرایش‌ها (additive، پشتِ flag، بدونِ regression)
| مسیر | ویرایش |
|---|---|
| `_ops/cardiac.py` | plumbingِ افزودنیِ flag-gated که **`HeartParams` را مصرف** می‌کند: `bio_rhythm(mass=target_mass_scale*estimate_mass())`، ورودیِ gain برای Baroreflex، BeatBudget cap قابلِ rebind. `effective_period()` **همان symbolِ `pulse_control.sog_period` را import/call** می‌کند (no fork). خروجیِ سایه **فقط** به `state/pulse/heart-params-shadow.jsonl` می‌رود؛ dictِ `period_s` **دست‌نخورده**. fail-soft. |
| `_ops/doctor/doctor.py` | بعد از `:618`: stepِ shadowِ flag-gated که از `_gather_trace()` (read-only) + `selfmodel_state()` یک `HeartParams` می‌سازد (پنجرهٔ pre-action، lag) و به sinkِ typed + `_note("DOCTOR_PULSE_SHADOW", …)` می‌نویسد. cadence روی governor tick. propose-only، fail-soft. |
| `_ops/organism.py` | **seamِ زنده** — تأیید کن `:418-427` فقط `'period_s'` را می‌خواند؛ تستِ static این را قفل کند. (تا PRODUCTION_WIRE، هیچ تغییری در مقدارِ مصرفی.) |
| flags | `OCTOPUS_WIRE_PULSE` جدید (default off). `OCTOPUS_WIRE_BIO` بی‌تغییر. |

**دست‌نزدنی:** `_ops/chrono.py` (هیچ import از cardiac؛ Pacemaker mutate نمی‌شود مگر sign-offِ مالک)، `held_out_evaluator.FIXED_CANARY_TESTS`، `LAMBDA_PERSIST`، `replication.py` σ-source، HLC/EffectorGate/kill-switch.

---

## بخش ۸ — پذیرش (تست‌های offline، سبکِ harness.run)

همه offline/$0. اضافه به سوییتِ موجود بدونِ شکستنِ **۷۸/۷۸**.

1. **control-law کران‌دار:** روی گریدِ کامل، `sog_period(...) ∈ [floor, 900]`؛ هرگز صفر/منفی/NaN.
2. **closed-loop pin/gain:** با plant `r(beat)`، `G<1` روی کلِ گرید؛ period به‌ریلِ clamp pin نمی‌شود؛ بعدِ spike به baseline برمی‌گردد.
3. **σ-cap + fail-safe:** `σ=1.2` + بیشینه Δ_self → `900`؛ σ **غایب→900**، **کهنه→900**، **refresh کندتر از beat→floor بالا**.
4. **taint runtime:** رکوردِ σِ Doctor-authored (origin/producer دستکاری) → قانون **رد** می‌کند (900).
5. **provenanceِ Δ_self:** Δ_self با operandِ organism-authored → **رد** (900)؛ assert مسیر از `selfmodel_state()`.
6. **denominatorِ σ:** active_cellsِ باد‌شده که σ<1 → cap **شل نمی‌شود**؛ سقفِ مطلقِ approved اعمال.
7. **ترمزِ بودجه:** `remaining→0` → `sog_period` یکنوا به whale، مستقل از Δ_self.
8. **drift-guard:** `Δ_self>ceiling` → drift-flag و **نه** زیرِ floor.
9. **g_learn/g_rest clamp:** هر دو `∈[0,1]`؛ `Δ_self>ceiling` دوره را pin نمی‌کند.
10. **w_shadow load-only:** با قفل غایب/`e_shadow_locked:false`/hashِ خراب → `w_shadow==0` و دوره **bit-identical** با نتیجهٔ صفر؛ تغییرِ `E_shadow_ref` بی‌قفل → period بی‌تغییر. **(جایگزینِ تستِ trivialِ نسخهٔ قبل:)** با قفلِ معتبر و `w_shadow≠0`، assert کن g_rest **فقط** از `E_shadow_ref`ِ قفل‌شده استفاده می‌کند.
11. **Δ_self زنده، نه literal:** perturbِ ورودی‌های operating → `g_learn` رد‌پای Δ_selfِ بازمحاسبه را می‌گیرد (نه ثابت).
12. **identityِ sim↔production:** `cardiac` و `pulse_sim` **همان function object/version-hashِ `sog_period`** را صدا می‌زنند؛ hash در قفل ثبت و در gate چک.
13. **shadow هیچ set نمی‌کند:** با flag off، `organism.py`'s `period_s` قبل/بعدِ beat یکسان؛ `effective_period()['period_s']` با/بدونِ shadow **bit-identical**؛ سایه فقط به `heart-params-shadow.jsonl`.
14. **static seam:** `organism.py:418-427` هیچ کلیدی جز `'period_s'` نمی‌خواند.
15. **decision-frequency invariance:** فرکانسِ مؤثرِ تصمیمِ Doctor نسبت به دوره ناوردا.
16. **MC-witness (Gate-A):** بدونِ MC-witness، `e_shadow_locked==false` اجباری؛ با witness، closed-form within 3σ.
17. **σ_z² از primitive:** literalهای `0.0141667/0.012553/0.135073` هیچ‌جا operand نیستند (فقط anchorِ مقایسه).
18. **sim-gate:** `PRODUCTION_WIRE` با هر شرطِ غایب → `False`؛ report per-equation status و owner-ack را نشان می‌دهد.
19. **I_pred بی‌اثر:** assert کن `i_pred_locked` هیچ ضریبی فعال نمی‌کند؛ runtime gate آن را نادیده می‌گیرد.
20. **no self-grading:** `evaluate_held_out(internal_metric_pass=True)` وقتی fixed-suite/ledger fail → `anti_hacking_flag==True`.
21. **no regression:** anchorهای 4.py بازتولید؛ سوییتِ ۷۸ سبز؛ با flag off هیچ تغییری در ضربانِ زنده.

---

## بخش ۹ — نقشهٔ اجرا + «چطور این کار را بکنم» (برای مالک، چند قدمِ ساده)

**ترتیبِ اجرای agent:**
1. `agent-checkpoint:` commit (قبل از عملیاتِ دسته‌ای).
2. `python C:/Users/Armin/Desktop/4D/4.py` → تأییدِ anchorها. اگر نه → STOP + AGENT_QUESTIONS.
3. نوشتنِ `06 - Architecture Maps/ADR-001 …md` (ratify coupled-not-merged + «کانالِ کوپل فقط HeartParams»).
4. ساختِ `_ops/selfmodel_state.py` (منبعِ read-onlyِ operandهای Δ_self) — و تصمیمِ Gate-0: sim-only یا live-producer.
5. ساختِ `_ops/pulse_control.py` (قانون + dataclassها + `P_closed` reused + `load_w_shadow_from_lock` + `sog_period` که HeartParams می‌سازد).
6. ساختِ `_ops/sim/pulse_sim.py` → اجرا → `pulse-sim-report.json` + (در صورتِ MC-witnessِ موفق) `PULSE-EQUATIONS-LOCKED.json` با version-hash.
7. ویرایشِ shadow در `cardiac` (sink جدا، همان symbol، plumbingِ HeartParams) و stepِ shadow در `doctor.run_cycle` (pre-action window، governor tick).
8. اجرای هر دو validator + سوییتِ تست (۷۸/۷۸) + تست‌های بخش ۸.
9. آپدیتِ `Active Context`/`Progress` + بازنویسیِ `HANDOFF.md` (فقط wikilink) + commit.

**برای مالک (ari) — سه تصمیم، به‌ترتیب:**
- **اول چه چیز:** فقط بگذار sim اجرا شود. هیچ هزینه، هیچ ضربانِ واقعی تکان نمی‌خورد. خروجی = یک گزارش.
- **sim را کجا ببین:** `state/sim/pulse-sim-report.json` — علاوه بر pass/fail هر anchor، **بهرهٔ closed-loop `G`** و **وضعیتِ per-equation (`locked | excluded-unlocked`)** را نشان می‌دهد؛ و `state/pulse/heart-params-shadow.jsonl` (ضربان **چه می‌شد**، بدونِ اینکه چیزی شود).
- **کِی flag را روشن کنی:** فقط وقتی **همهٔ این‌ها** سبز شد: sim pass (`G<1`) ∧ قفل موجود ∧ **producerِ زندهٔ Δ_self وجود دارد (Gate-0)** ∧ version-hash می‌خواند ∧ تاریخ ≥ 2026-07-21 ∧ تو دستی `ACTIVATION-PULSE.flag` گذاشتی ∧ هر دو flag on. تا آن لحظه، هرچه ببینی «سایه» است.
- **E_shadow را کِی وارد کنی:** فقط اگر Gate-A آن را با **شاهدِ مستقلِ Monte-Carlo** قفل کرد (نه خودتوافقیِ scalar). وگرنه ضربان تا ابد فقط با Δ_selfِ کانونی می‌تپد و `w_shadow=0` می‌ماند — کاملاً امن و کافی.

> **یادآوریِ نهاییِ paranoid:** (۱) هیچ راننده‌ای — نه شتاب‌دهنده (Δ_self) نه ترمز (σ) — از stateی که خودِ ارگانیسم می‌نویسد تغذیه نمی‌شود؛ تقارنِ provenance شرطِ زنده‌بودنِ امنِ این ضربان است. (۲) کران‌داری فقط با اثباتِ **closed-loop `G<1`** پذیرفته می‌شود؛ open-loop هرگز گیت نیست. (۳) ریاضیاتِ اعتبارسنجی‌نشده هرگز، تحتِ هیچ flag، ضربانِ واقعی را نمی‌راند تا با **MC-witnessِ مستقل** در برابرِ 4.py قفل و pre-register شود، و `w_shadow` **فقط با load از فایلِ قفل** غیرصفر می‌شود، نه با هیچ literal. اگر قاعده‌ای راهت را بست: STOP و در `AGENT_QUESTIONS.md` بپرس — هرگز دورش نزن.