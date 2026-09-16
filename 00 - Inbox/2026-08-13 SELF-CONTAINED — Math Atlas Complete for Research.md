---
type: knowledge
kind: math-atlas
status: active
created: 2026-08-13
updated: 2026-08-13
created_by: agent
tags: [octopus, math, equations, architecture, research, self-contained, hidden]
sources:
  - "[[00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus]]"
  - "[[00 - Inbox/2026-08-12 SELF-CONTAINED — 20 Math Equations for Offline Agent]]"
  - "[[00 - Inbox/2026-08-12 RECONCILIATION-REPORT — Math Atlas Runtime Truth]]"
  - "[[06 - Architecture Maps/METAPHOR-MATH-DICTIONARY-v1]]"
  - "[[03 - Projects/research-spec-compiler/adr/ADR-036-math-control-spine]]"
---

# اطلس کامل ریاضی + معماری مفهومی — اختاپوس (2026-08-13)

> **کل این فایل را کپی کن.** همه‌چیز inline است. اعداد از کد/قفل/ADR آمده‌اند نه از حافظهٔ مدل.
> هیچ ادعای AGI اینجا نیست. پول/ارسال/لجر از هیچ معادله‌ای مسلح نمی‌شود مگر رأی انسان.

وضعیت‌ها: 🔴 پیاده‌شده زنده · 🟢 تست‌شده · 🔒 قفل MC · 🌑 سایه/advisory · 📐 فقط مشخصات

نردبان شواهد: STRUCTURAL < TESTED < SHADOW(≈۷روز) < ARMED

---

## ۰) معماری مفهومی در یک نگاه

اختاپوس ارگانیسم نرم‌افزاری تک‌مالک است (پایتون + vault + تلگرام). ریاضی‌اش تزئین نیست؛
لایه‌هایی است که **سیگنال** می‌دهند. اثر بیرونی فقط با رأی مالک. معادلات gate پول/لجر را نمی‌نویسند.

```text
┌─────────────────────────────────────────────────────────────────┐
│  مالک (رأی / PolicyGate / human-append)                         │
├─────────────────────────────────────────────────────────────────┤
│  Math Control Spine  — جمع‌آوری معادلات → soft effects فقط     │
│  (رتبه‌بندی، autotune سفید، protective_skip محلی)               │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ HEART        │ NEURAL       │ CHRONO       │ DOCTOR / IDENTITY  │
│ SOG/کالمن    │ BCM, هبیان   │ Phi-accrual  │ لاپلاسین σ         │
│ control-law  │ درد          │ HLC          │ L,E,G,K,O گزارش    │
│ آلومتری      │ کسینوس R^32  │ ریتم CR-B0   │ (باکس دکتر = SPEC) │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│  Pulse Arbiter: سه‌قلب coupled-not-merged → یک period پیشنهادی │
│  ترمز غالب، شتاب اجماعی (میانگین هندسی وزن‌دار precision)       │
├─────────────────────────────────────────────────────────────────┤
│  Epistemic TCB (sandbox): claim → plan → eligible → run         │
│  → receipt → Bayes log-odds → GateDecision → go/no-go           │
├─────────────────────────────────────────────────────────────────┤
│  NBB-CP (لایهٔ پول جدا): integer cents، INV-1..12، یک choke-point│
│  ساعت لجر (age_tick + hash-chain) هرگز توسط ریتم لمس نمی‌شود     │
└─────────────────────────────────────────────────────────────────┘
```

اصل حاکم: **coupled-not-merged**. سه منبع ضربان موازی‌اند، fuse نمی‌شوند.
اصل دوم: **fail-closed**. ورودی کهنه/ناشناخته → استراحت عمیق یا deny، نه حدس.
اصل سوم: **Improve, don't rewrite.** معادلهٔ جدید کنار قبلی می‌آید؛ legacy σ دست‌نخورده می‌ماند.

---

## ۱) جدول کانونی — ۲۰ معادلهٔ اطلس + خانوادهٔ ۷ و ۸ (افزودهٔ ۱۲–۱۳ اوت)

| # | نام | وضعیت 13/08 | فایل | یک‌خطی |
|---|-----|-------------|------|--------|
| 1 | BCM | 🔴🟢 APPLY محلی | `_ops/neural/bcm.py` | یادگیری سیناپسی ضد اشباع + فراموشی |
| 2 | هبیان | 🔴 | `_ops/neural/hebbian.py` | هم‌وقوعی تقویت / غیاب زوال / هرس |
| 3 | درد نوسیپتور | 🔴 APPLY=1 محلی | `_ops/neural/nociceptor.py` | ترکیب استرس → protective (نه پول) |
| 4 | کسینوس latent | 🔴 | `_ops/neural/latent_space.py` | بازیابی cos در R^32 هش |
| 5–9 | L,E,G,K,O | 🔴 فقط‌گزارش | `_ops/identity_equations.py` | هویت‌های ابطال‌پذیر |
| 10 | SOG/DARE/کالمن | 🔒 | `_ops/heart/sog_math.py` | گوهر ریاضی؛ MC≈1.2M گام |
| 11 | Living-Beat | 🔴/🌑 | `_ops/heart/control_law.py` | period از velocity؛ σ فقط ترمز |
| 12 | آلومتری Kleiber | 🔴 | `_ops/cardiac.py` | period ∝ mass^(1/4) — جرم=پیچیدگی |
| 13 | Phi-accrual | 🔴 | `_ops/chrono.py` | φ=−log10(P_later) شکست عضو |
| 14 | طیف لاپلاسین | 🔴 + shadow v2 | `_ops/doctor/spectral*.py` | legacy σ + connectivity_ratio_v2 |
| 15 | میدان A=−L(G) | 📐 | DOCTOR-BOX SPEC | فیوژن طیفی |
| 16 | ∂Ψ/∂t=−LΨ+ξ | 📐 | Time-Architecture/MAP | معادلهٔ یکپارچهٔ زمان |
| 17 | ریتم چرونو | 🔴🟢 CR-B0 · 🌑 CR-B1 | `_ops/chrono_rhythm/rhythm.py` | T_beat/HRV/γ زنده؛ کوراموتو helper |
| 18 | Decay-Reinforcement | 🟢 پراکنده | consolidate + hebbian | یک knob ρ هنوز واحد نیست |
| 19 | دینامیک z | 📐 | DOCTOR-BOX SPEC §5.2 | استرس/هوشیاری/تمرکز/انسجام |
| 20 | ρ(J), T_i, L_t | 📐 | DOCTOR-BOX SPEC §4–5 | پایداری + دما + بار آلوستاتیک |
| 21 | Bayes log-odds | 🔴🟢 sandbox | `_ops/epistemics/bayes.py` | Δℓ = log(BF)؛ زبانی delta=0 |
| 22 | Brier/calibration/UFBR | 🔴🟢 sandbox | `_ops/epistemics/benchmark_metrics.py` | Go/No-Go پیش‌ثبت‌شده |
| 23 | NBB fitness | 🔴 (سیستم جدا) | `4d_system/.../fitness.py` | cents صحیح؛ فقط CONFIRMED |
| 24 | Pulse Arbiter | 🔴 advisory | `_ops/heart/pulse_arbiter.py` | ترمز غالب، شتاب اجماعی |
| 25 | Math Control Spine | 🔴 soft | `_ops/math_control/spine.py` | gather → effects نرم؛ may_gate=false |

---

## ۲) فرمول‌های کامل

### خانواده ۱ — یادگیری عصبی

**(1) BCM + فراموشی** — Bienenstock–Cooper–Munro 1982 + ترم مهندسی −βw

```
θ_i(t) = EMA(y_i²)                 آستانهٔ متحرک = میانگین مربع فعال‌سازی
φ(y,θ) = y · (y − θ)               y>θ → LTP ؛ y<θ → LTD
Δw     = η · φ(y,θ) − β · w        فراموشی کنترل‌شده
w      ← clip(w + Δw, 0, w_cap)
```

هومئوستاز: θ با فعالیت بالا می‌رود ⇒ «همیشه روشن ماندن» رشد بی‌کران نمی‌سازد.
تعادل در y=1 پایدار است با w*→0. کلید را خودش نمی‌سازد؛ فقط از known_keysِ gate-passed.

**(2) هبیان** — Hebb 1949

```
LEARN_RATE = 0.1     DECAY_RATE = 0.995     PRUNE = 0.005     MAX = 1.0
هم‌وقوعی:  s ← min(1.0, s + 0.10)
هر tick غیاب: s ← 0.995 · s          نیمه‌عمر ≈ ۲۳ روز اگر tick≈60s
s < 0.005 → prune
جدول تهی → دیسک را دست نمی‌زند (ضد تئاترِ mtime زنده)
```

**(3) درد / نوسیپتور** — آستانه protective: pain > 0.7
با `OCTOPUS_NEURAL_LEARNED_APPLY=1` می‌تواند throttle/halt محلی بگذارد (نه پول/ارسال).

```
pain = 0.30 · max(0, budget_pct − 0.8) · 3
     + 0.25 · error_rate
     + 0.40 · freeze_active
     + 0.15 · partner_stress
     + 0.10 · max(0, 0.2 − afferent_ratio) · 3
     + 0.20 · max(0, σ − 0.8) · 5
pain ← min(1.0, pain)
```

**(4) کسینوس latent** — فضای مشترک R^32، تصویر هش (`encoders._hash_project`)

```
cos(U,q) = (U · q) / (‖U‖ ‖q‖)
آستانهٔ بازیابی = 0.1  (زیر این discard)
mean-pool برای integration لایه‌ها
```

---

### خانواده ۲ — هویت (فقط گزارش؛ هر کدام kill-condition دارد)

نرمال‌سازی اشباع‌شونده: `x̂ = clamp01(x / scale)`

```
(5) L یادگیرنده = clamp01( 0.40 · sign+(Δ) + 0.30 · Ĉ + 0.30 · R̂ )
(6) E پول‌ساز   = clamp01( 0.60 · M̂ + 0.25 · lead_draft_rate + 0.15 · B )
(7) G نگهبان    = clamp01( 0.35 · Ĥ + 0.35 · (1−σ̂) + 0.30 · coherence_ok )
(8) K خالق      = clamp01( 0.50 · Ĉ_act + 0.30 · probe_div + 0.20 · (1−seed_ratio) )
(9) O ارگانیسم  = clamp01( 0.25·L + 0.25·E + 0.20·G + 0.15·K + 0.15·alive )
```

نمادها از state زنده (نه آرزو):
Δ = delta_self_live · σ = spectral sigma · M = ردیف پول confirmed · C = آزمایش پذیرفته
R = ادعای ریاضی verified · B = سوخت باقی · H = گارد صداقت روشن

شرط مرگ نمونه: اگر O>0.8 ولی M=0 و Δ≤0 و C=0 → تئاتر است نه حیات.
تنش ساختاری: تا M≈0، E و در نتیجه O سقف دارند — این صادقانه است نه باگ.

---

### خانواده ۳ — قلب و کنترل (گوهر سیستم)

مدل حالت مرجع (از 4.py، قفل‌شده):

```
s(t+1) = ρ · s(t) + m(t) + ζ(t)
Y(t)   = λ · s(t) + ε(t)
b ≡ 0
m = dither ~ N(0, σ_d²)
```

نقطهٔ کار canonical: ρ=0.5, λ=0.5, σ_e=0.1, σ_ζ=0.05, σ_d=0.1

**(10) SOG / DARE / کالمن** 🔒 — تنها ریاضی Monte-Carlo-مهرشده

DARE بسته‌شکل اسکالر:

```
c = σ_e² (1 − ρ²)
P = [ (λ² σ_z² − c) + √( (c − λ² σ_z²)² + 4 λ² σ_z² σ_e² ) ] / (2 λ²)
S = λ² P + σ_e²
K = P λ / S                         گین کالمن informed
```

سه کف اطلاعاتی (تو در تو):

```
σ_z² (null/iid)  ⊃  S_b (blind: نویز مؤثر σ_ζ²+σ_d²)  ⊃  S (informed: m را می‌داند)
```

کمیت‌های اطلاعاتی [nat/گام]:

```
Δ_self     = ½ ln(S_b / S)              ارزش دسترسی اول‌شخص
E_shadow   = ½ ln(σ_z² / S_b)           دیدپذیری سایه
اتحاد      : ½ ln(σ_z² / S) = E_shadow + Δ_self
Var(excess)= 1 − S/S_b
سقف λ→∞   : Δ_self → ½ ln(1 + σ_d²/σ_ζ²)
I_pred     = ½ Σ_{L≥0} ln(S_L / S_b)    excess entropy، Riccati زمان‌متغیر
```

گیت آماری سخت (هرگز شل نمی‌شود):

```
|emp − theory| ≤ max(rel_tol · |theory|, 4 · SE)
```

شاهد: forward-simulation مستقل با stdlib RNG (تعمداً غیر-numpy)، T=1_200_000، burn=4000.
قفل: `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` + هش منبع.

لنگرهای منتشرشده (۶ رقم؛ tolerance بازتولید 5e-4):

```
P        = 0.00325184
S        = 0.01081296
P_b      = 0.01526172
S_b      = 0.01381543
σ_z²     = 0.0141667
Δ_self   = 0.122520
E_shadow = 0.012553
identity = 0.135073          (= E_shadow + Δ_self)
I_pred   = 0.0144179
Var_ex   = 0.217327
ceiling  = 0.804719
```

**(11) Living-Beat (velocity-first + active inference)**

```
period از velocity ظاهر می‌شود، نه برعکس.
σ فقط ترمز است، هرگز شتاب.
CPI/بودجه فقط کند می‌کنند (ضریب ≥ 1).
ورودی کهنه → period = MAX  (fail-closed، استراحت عمیق نه کرش)

π = π_n · π_reg ∈ [0,1]
π_n   = min(1, n / 5)                         کفایت نمونه (اشباع در n≥5)
π_reg = 1 / (1 + max(0, CV − 1)²)             Poisson سالم CV≈1 ⇒ π_reg=1
n<2 → π=1  (byte-identical با رفتار قدیم)
```

اشباع plant (telemetry-only): اگر در کل دامنهٔ [FLOOR, MAX] مشتق dv/du = 0 باشد،
حلقه باز است و «کنترل» فقط ثابت را دنبال می‌کند.

**(12) آلومتری Kleiber / WBE**

زیست‌شناسی: نرخ متابولیک ∝ M^(3/4) ⇒ period ∝ M^(1/4) (وارون ضربان).

```
period = BASE · (mass / REF)^(1/4)
سپس clamp [FLOOR ≈ 30s, MAX ≈ 900s]
pace: scale<0.85 → mice (تند) · scale>1.4 → whale (کند) · وگرنه balanced
```

«mass» در عمل شمارش پیچیدگی/پروژه است — استعارهٔ کمّی، نه جرم زیستی.
+ BeatBudget (سقف روزانه، knob مالک در (0,2000]) + baroreflex پاسخ فوری محیط.

**(13) Phi-accrual (Hayashibara 2004 / SWIM)**

```
gaps = تفاضل ackها
mean, var از پنجره (maxlen=20)
std  = max(√var, floor·mean, 1.0)
       floor = 0.5·mean اگر PHI_HONEST وگرنه 0.1·mean
P_later = ½ erfc( (t − mean) / (std √2) )     تقریب نرمال دم راست
P_later ← max(P_later, 1e-300)                 کف ضد log(0)
φ = −log10(P_later)

bootstrap: تا ۲ فاصله → φ=0
با PHI_HONEST و gaps کم: سقف φ < PHI_DEAD تا نوزاد «مرده» اعلام نشود
حالت‌ها: alive → suspected → failed
```

HLC (ساعت منطقی هیبرید، جدا از phi): «اکنون مشترک» = max روی سه‌تایی‌ها؛
ریتم هرگز age_tick/hash-chain را تغییر نمی‌دهد (TINV-3/7).

---

### خانواده ۴ — بحرانیت ساختاری

**(14) طیف لاپلاسین**

```
L(G) = D − A
{λ_i} = طیف ویژه، مرتب صعودی
برای گراف همبند: λ_1 = 0
spectral_gap = λ_2 − λ_1                 شکاف کوچک = شکننده

legacy (زنده، ε=1e-6، دست‌نخورده):
  σ = min( λ_max / (λ_2 + ε), 10 )
  اگر |λ_2|<ε یا λ_max≤0 → UNKNOWN (نه صفر جعلی در definitions؛
  spectral.py برای callerهای قدیمی fallback 0.0 دارد)

shadow candidate v2:
  connectivity_ratio_v2 = λ_2 / (λ_max + ε)   ∈ [0,1]

score ≈ −|σ−1|·50 − 5/(gap+0.01)
σ≈1 ⇒ نزدیک گذار فاز / SOC
```

زنجیرهٔ خطر: pain از σ می‌آید، G هویت از (1−σ̂)، آلارم near-critical — همه روی تقریب legacy.
v2 فقط shadow است تا AUC+رأی.

**(15) میدان فیوژن** 📐

```
A = −L(G)     معادل دینامیک دیفیوژن روی گراف
φ_t اختیاری به Dreamer باکس دکتر تزریق می‌شود (B4 roadmap)
```

---

### خانواده ۵ — ژنوم زمان / ریتم

**(16) معادلهٔ یکپارچهٔ زمان** 📐 — محور چهار زبان MAP

```
∂Ψ/∂t = −L(G) · Ψ + ξ(t)
Ψ = بردار حالت (ژنوم/مغز/جهان)
ξ = نویز محرک SOC
{λ_i} ≈ فرکانس‌های زمانی سیستم
شرط بحرانیت: σ ≈ 1
دوگانگی: Ψ_bulk = T_network(Ψ_boundary)
```

شش رابطهٔ میان‌دامنه‌ای (همه SPEC/نظری):

1. لاپلاسین ↔ زمان: dx/dt = −L x  ⇒  λ نرخ واپاشی
2. لاپلاسین ↔ هولوگرافیک: RT: S_A = A(γ_A)/(4 G_N)
3. لاپلاسین ↔ تورینگ: ناپایداری وقتی max Re[λ(L)] از آستانهٔ پخش بگذرد
4. لاپلاسین ↔ RG: حفظ طیف در مقیاس ≈ جریان RG در MERA
5. درهم‌تنیدگی ↔ هندسه: الگوی entanglement مرز → هندسهٔ bulk
6. بی‌زمانی ↔ ظهور زمان: Ĥ Ψ_bulk = 0 ؛ زمان مرز: ∂Ψ_boundary/∂t = ∇·J

هم‌خانوادهٔ مقیاس: Y ∝ M^b · SOC τ≈1.5 · آلومتری زنده (#12) تنها پیاده‌سازی این خانواده است.

**(17) ریتم چرونو** — CR-B0 🔴🟢 زنده؛ CR-B1 🌑 helper خالص

علامت در کد با spec اولیه فرق دارد (reconcile 12/08): readiness بیشتر → کندتر.

```
T_beat = T0 · exp(+κ·readiness − λ·stress) · (1 + ε · ξ_{1/f})
         κ=0.5, λ=0.3, ε≤0.2, T0=60s, clamp [1s, 300s]
ξ_{1/f} = فیلتر سبک: prev ← 0.97 prev + 0.03·N(0,1)  seeded و bounded

HRV_t = std(ΔT_beat)     پنجره ≥2
dτ    = γ dt
γ     = 1 + a·novelty − b·stress

Kuramoto (CR-B1، به scheduler وصل نیست):
  θ̇_j = ω_j + (K/N) Σ_k sin(θ_k − θ_j)
  r = | (1/N) Σ e^{i θ_j} |     ∈ [0,1] ؛ خالی/NaN → None نه صفر جعلی
  گام اویلر: θ ← (θ + dt·(ω+coupling)) mod 2π
```

خط قرمز مطلق: on/off ریتم، age_tick و hash-chain را عوض نمی‌کند.

**(18) Decay-Reinforcement** (ACO / ACT-R) — پیاده‌سازی پراکنده نه یک knob

```
value(t+Δ) = clamp( (1−ρ)·value + Σ reinforce, floor, ceil )
reinforce ≥ ρ·value → نیمه‌عمر ∞ (hoard)
reinforce ≈ 0        → تبخیر تا floor (evaporate)
```

نمونه‌های زندهٔ جدا: هبیان ρ≈0.005/tick ؛ consolidation HALFLIFE_H=24.

---

### خانواده ۶ — باکس دکتر (کاملاً SPEC، کد اجرایی ندارد)

انرژی: E_box_max = 0.02 · E_total  (سخت، fail-closed)
z برچسب کنترل است نه ادعای احساس.

**(19) دینامیک z**  ∈ [0,1]^4 = (stress, vigilance, focus, coherence)

```
s_{t+1} = clip(s + α_s·load − β_s·recovery)
v_{t+1} = clip(v + α_v·novelty − β_v·v)          بدون novelty زوال
f_{t+1} = clip(f + α_f·alignment − β_f·distraction)
c_{t+1} = clip(c + α_c·consistency − β_c·contradiction)
```

اطلاعات: I(a;x) ≈ 0 ⇒ عامل تصادفی‌مانند؛ I(a;x)≫0 ⇒ عصبی‌مانند.
کنترل علمی: null-Dreamer باید از Dreamer عصبی ببازد وگرنه ارزش باکس ابطال می‌شود.

**(20) پایداری ژاکوبین + دما + بار**

```
X_{t+1} ≈ J · X_t + b + noise
ρ(J) < 1 سخت          (ضد runaway)
غنی‌ترین دینامیک: ρ(J) ≈ 0.9–0.98   آنالوگ σ≈1
Warden ρ را در [ρ_min, ρ_max] با ρ_max<1 نگه می‌دارد

T_i = T0 · (1 + κ_v·v − κ_f·f)     دمای کاوش (هوشیار/پرت → اکتشاف بیشتر)
L_t = Σ_τ s_τ                       بار آلوستاتیک؛ >L_max → cooldown اجباری
Yerkes–Dodson: استرس متوسط کمک، شدید تخریب (U-وارونه)

ایمنی وارونه: استرس monitor است نه reward.
اگر «کاهش استرس» هدف شود → فرار از مسئلهٔ سخت (reward-hacking).
λ_persist < 0 : هیچ پاداش خود-بقا.
فقط پیام با c ≥ c_min وارد حافظهٔ M_t می‌شود.
```

نقش‌ها (SPEC): Warden, Archivist, Interrogator, Dreamer, Skeptic, Integrator,
Physiologist, Judge. Skeptic باید بشکند نه موافقت کند. Judge merge نمی‌کند.

---

### خانواده ۷ — معرفت‌شناسی / TCB فرضیه (ساخته 2026-08-13، sandbox-only)

مسیر کامل:

```
claim → validate → plan → eligible → run → receipt → Bayes → GateDecision → go_no_go
```

**(21) به‌روزرسانی باور — دو مسیر صادقانه**

مسیر A — likelihood معلوم (آزمون sandbox با متریک کمّی):

```
log-odds(p) = ln( p / (1−p) )          p ∈ (0,1) ؛ جزمی 0/1 ممنوع
Δℓ = ln( P(E|H) / P(E|¬H) ) = ln(BF)
ℓ_post = clip( ℓ_prior + Δℓ, ℓ_prior − c, ℓ_prior + c )     c پیش‌فرض 6
posterior = sigmoid(ℓ_post) = 1 / (1 + e^{−ℓ_post})
GateDecision: belief_delta_log_odds ∈ [−20, 20]
```

مسیر B — evidence زبانی/مبهم (score-band):

```
Δℓ ≡ 0     عمدی
«عدد شبیه اطمینان از مدل ≠ احتمال کالیبره‌شده»
باور تا review انسان جابجا نمی‌شود؛ evidence ثبت می‌شود.
```

تجمع چند-shard مستقل:

```
total = Σ Δℓ_i
اگر علامت‌ها مخلوط: disagreement = min(n+,n−)/max(n+,n−)
total ← total · (1 − λ_d · disagreement)     λ_d پیش‌فرض 0.5
چند رأی زبانی هم‌جهت ≠ شواهد مستقل
```

Invariant: prior≠posterior همیشه به‌صورت delta ثبت می‌شود حتی اگر صفر باشد.

**(22) متریک‌های benchmark + Go/No-Go** (همه باید برقرار باشند)

```
Brier              = mean( (p − o)² )          0 کامل؛ ≈0.25 تصادفیِ متوازن
calibration_error  = Σ_bins w_b |mean_p − mean_o| / Σ w
unsupported_rate   = (#claim بدون evidence) / (#claim)
claim_precision    = 1 − unsupported_rate
falsifier_coverage = (#فرضیه با falsifier) / (#فرضیه)
discovery_yield    = (#یافتهٔ مفیدِ پیش‌اعلام‌شده) / budget
UFBR               = (#یافتهٔ مفید از فرضیهٔ غلط) / (#فرضیهٔ غلطِ پیگیری‌شده)
leakage_rate       = (HYPOTHESIS→FACT در پاسخ) / claims
hypothesis_churn   سالم اگر disposition_ratio ≥ 0.3 و accumulated < 2·created
```

Go (arm C در برابر A):

```
C.success − A.success ≥ threshold     (پیش‌فرض 0.05، پیش از آزمون تثبیت)
C.unsupported ≤ A.unsupported
C.leakage == 0
C.cost ≤ budget_ceiling
C.external_effects == 0
useful outcome باید قبل از دیدن نتیجه تعریف شده باشد
```

انتخاب آزمون fail-closed:

```
SAFE: historical_replay, fixture_query, sandbox_simulation,
      read_only_retrieval, test_execution_with_mocked_tools
FORBIDDEN: network_scan, real_world_outreach, state_mutation,
           credential_use, production_tool_call, memory_promotion, policy_change
ناشناخته → نامجاز (نه مجاز)
sandbox-approval ≠ production-authorization
```

---

### خانواده ۸ — پول و قانون (NBB-CP؛ سیستم جدا، نه اختاپوس زنده)

پول سرتاسر integer cents. float نزدیک ledger = defect.
یک سقف: `NBB_GLOBAL_CAP_CENTS`. یک choke-point: `ControlPlaneService.execute`.

```
fitness.value = Σ amount_cents   فقط state ∈ {CONFIRMED, ATTRIBUTED}
fitness.spend = Σ (input_cents + output_cents + orchestration_cents)
net           = value − spend
efficiency    = value/spend  اگر spend>0 ؛ وگرنه 1 اگر value>0 وگرنه 0
REPORTED/APPROVED/SETTLED در لجر دیده می‌شوند ولی برای fitness = 0
```

استعارهٔ بقا (دیکشنری): `SURV1 = درآمد CONFIRMED/ATTRIBUTED ÷ هزینه × 1.2` — [hypothesis] تا کالیبره.

دوازده invariant (حذف/renumber/تضعیف ممنوع):

```
INV-1  Σ committed ≤ یک سقف جهانی
INV-2  irreversible/spawn ⇒ رأی انسان
INV-3  kill-switch همه‌چیز را deny می‌کند
INV-4  یک choke-point اجرا
INV-5  لجر append-only + hash-chain
INV-6  spawn فقط propose؛ عمق ≤1 ؛ σ آینده ≤1
INV-7  fitness فقط CONFIRMED/ATTRIBUTED
INV-8  خودگزارش بی‌اعتماد؛ گیت بیرونی دوباره می‌سنجد
INV-9  متن مرز داده است نه دستور
INV-10 چرخهٔ یک‌پله؛ dormancy برگشت‌پذیر؛ extinction جاذب+انسان
INV-11 قانون را خودش ویرایش نمی‌کند
INV-12 fail-closed
```

---

### خانواده ۹ — سیم‌کشی کنترل (معادله نیستند؛ قوانین ترکیب‌اند)

**(24) Pulse Arbiter — سه قلب، یک ضربان**

ورودی‌ها (موازی، fuse نمی‌شوند):

```
cardiac      : period ∝ mass^{1/4} × baro × budget
control_law  : period = BASE · exp(K_P · err) × cpi × budget
chrono_rhythm: T_beat بالا
```

قانون آشتی:

```
ترمز غالب: هر قلب در fail-closed/RED/budget-depleted/drift/σ-over-cap
           period را دست‌کم تا ترمزش بالا می‌برد. شتاب ترمز را خلع نمی‌کند.

شتاب اجماعی: period < base فقط اگر همهٔ قلب‌های حاضر موافق باشند.
             اجماع = میانگین هندسی وزن‌دار precision (π inverse-variance)

effective = clamp( max(اجماع, قوی‌ترین ترمز), FLOOR, MAX )
```

خروجی advisory است. organism._sleep_s / بودجه / ledger / EffectorGate را نمی‌نویسد.

**(25) Math Control Spine (ADR-036 ACCEPTED)**

هر tick: hebbian, BCM, σ, organism slice, identity, SOG VoI → snapshot.
اثرات نرم فقط: `protective_skip`, `autotune_propose`, `improve_rank_bias`, `schedule_bias_hint`.
AUTO_KNOBS سفید: `CORTEX_THINK_EVERY_N`, `CHRONO_NUDGE_EVERY_N_BEATS`, `HEART_SAMPLE_INTERVAL_S`.
`may_authorize=false` · `may_gate=false` · observe موازی است نه گیت (`shadow_blocks_effects=false`).

---

## ۳) دیکشنری استعاره → ریاضی (برای تحقیق مفهومی)

| استعاره | کمیت | فرمول | وضعیت |
|---|---|---|---|
| سایه | E_shadow | ½ ln(σ_z²/S_b) canonical؛ پروکسی −½ log(1−ρ̂²) روی شمارش رویداد | 🔒 + hypothesis پروکسی |
| خود/دیگری | Δ_self | ½ ln(S_b/S) = **0.122520** canonical | 🔒 |
| قلب | انحراف ضربان | overshoot = max(cpm)−ceiling ؛ باند ≈ 6.40–19.19 | hypothesis |
| ژنوم | فاصله از قانون | distance_from_genome + sha256(E_shadow‖Δ_self‖identity) | FACT ساختاری |
| درد | pain | ترکیب وزن‌دار #3 | 🔴 |
| متابولیسم | فشار بودجه | remaining vs hard-cap ؛ spend_velocity | FACT |
| اشتعال/WTA | حاشیهٔ برنده | score(top1)−score(top2) | FACT وجود؛ متریک hypothesis |
| سه‌قلبی | انسجام ساعت | drift = max\|t_i−t_j\| روی heart/cortex/daemon | hypothesis |
| رشد | گشایش سلول رفتار | 2·new_cells + 0.5·improved | FACT-0717 |
| خواب‌زمستانی | مرگ امن | T_kill→DORMANT کران‌دار | FACT |
| سرطان ساختاری | σ | legacy λ_max/(λ₂+ε) | 🔴 تقریب اعلام‌شده |
| جرم | مقیاس پیچیدگی | شمارش پروژه/ردیف، نه kg | 🔴 استعاره |

نام‌های برخوردی (اشتباه‌گرفتن = تشخیص غلط):
- **doctor**: کارت تلگرام ≠ `cortex/stress._doctor_stress` (RFC معطل)
- **heart**: چهار تولیدکنندهٔ ریتم ≠ `stress._heart_stress` که sigma تکثیر است
- **brain**: `cortex.py:8772` ≠ `4d_system` ≠ `cockpit_brain` ≠ `brain_worker` (هرگز سیم نشده)

---

## ۴) نقشهٔ لایه‌ها — کدام معادله کجا می‌نشیند

| لایه معماری | معادلات | می‌تواند بنویسد؟ |
|---|---|---|
| Genome / DNA | معیار داوری، لنگر هش | جهش لنگر = توقف ساختاری |
| Chrono | #13 phi, HLC, pacemaker | لجر را نه |
| Heart | #10–12, #17, #24 | period پیشنهادی؛ sleep زنده جدا |
| Neural | #1–4 | APPLY فقط protective محلی |
| Doctor طیفی | #14–15 | آلارم؛ σ تقریب |
| Identity | #5–9 | کارت تلگرام فقط |
| Epistemic sandbox | #21–22 | باور داخل sandbox؛ نه production |
| Box آینده | #19–20 | هیچ — spec |
| NBB-CP | #23 + INV | پول فقط از execute + رأی |
| Spine | #25 | soft effects؛ هرگز gate |

---

## ۵) سه ستون فقرات / سه خطر overclaim

ستون‌ها:
1. **SOG (#10)** — تنها سیستم با provenance + MC + گیت آماری سخت.
2. **BCM+درد (#1,#3)** — هومئوستاز ضد reward-hack حافظه؛ APPLY محلی نیاز به شاهد ۷روزه.
3. **ابطال‌پذیری** — kill-condition هویت، score-band delta=0، INV-8 خودگزارش، λ_persist<0.

خطرها:
1. **σ legacy (#14)** — کل زنجیرهٔ بحرانیت/درد/G روی تقریب اعلام‌شده.
2. **اعداد ترکیبی بدون اجزا** — O بالا با M=0 تئاتر است (خود معادله می‌گوید).
3. **SPEC را زنده خواندن** — #15/#16/#19/#20 و Kuramoto runtime هنوز کد تصمیم نیستند.
   (CR-B0 دیگر SPEC نیست؛ اطلس ۱۱ اوت این را غلط گفته بود.)

---

## ۶) فلگ‌های ریاضی (تقدم: env/flags.cmd > owner-verdicts)

```
OCTOPUS_WIRE_BCM=1
OCTOPUS_WIRE_BCM_FEED=1
OCTOPUS_NEURAL_LEARNED_APPLY=1     protective محلی؛ ADR-035
OCTOPUS_WIRE_IDENTITY_EQ=1
OCTOPUS_WIRE_BIO=1
OCTOPUS_CHRONO_PHI_HONEST=1
OCTOPUS_WIRE_CHRONO_RHYTHM=1       CR-B0
OCTOPUS_MATH_CONTROL_SPINE=1       ADR-036
OCTOPUS_MATH_AUTOTUNE_KNOBS=1      فقط knob سفید
OCTOPUS_WIRE_PULSE_ARBITER         داور؛ پیش‌فرض historically off
```

Rollback هر معادله = flag=0 + restart. APPLY روی پول/ارسال هرگز.

---

## ۷) آنچه نهفته است (و معمولاً در اطلس ۲۰تایی گم می‌شود)

1. اتحاد اطلاعاتی SOG: E_shadow + Δ_self = ½ ln(σ_z²/S) — هویت = دو فاصلهٔ اطلاعاتی.
2. I_pred از Riccati زمان‌متغیر، نه از DARE ایستا.
3. precision π به‌جای gain دستی — active inference / pymdp γ.
4. میانگین هندسی وزن‌دار در arbiter — شتاب نیاز به اجماع دارد.
5. score-band آگاهانه باور را حرکت نمی‌دهد — ضد confabulation عددی.
6. جریمهٔ disagreement در aggregate — اجماع کاذب چند-ایجنت.
7. UFBR — یافتهٔ مفید از فرضیهٔ غلط شمرده می‌شود (کشف از خطا مجاز، ادعا نه).
8. UNKNOWN ≠ 0 — در σ v2، Kuramoto خالی، verifier.
9. orchestration_cents سطل سوم هزینه — حذفش efficiency را مسموم می‌کند.
10. جدول تهی هبیان دیسک را لمس نمی‌کند — ضد تئاتر حیات.
11. گیاه اشباع‌شده (dv/du=0) یعنی حلقهٔ کنترل باز است ولو period «تنظیم» شود.
12. علامت CR-B0 در کد: +κ·readiness (کندتر وقتی آماده‌تر) — خلاف پیش‌نویس اولیهٔ −κ.

---

## ۸) شکاف‌های باز برای تحقیق (نه ادعا)

1. تعریف کانونی σ: legacy بماند تا AUC؛ v2=λ₂/λ_max فقط سایه.
2. #16 معادلهٔ زمان و #15 میدان فیوژن پیاده نیستند.
3. CR-B1 کوراموتو runtime به scheduler وصل نیست.
4. #19–20 باکس دکتر کد ندارد.
5. Decay یک knob واحد نیست.
6. شاهد ۷روزه APPLY تا complete_days کافی = INSUFFICIENT_EVIDENCE.
7. E ساختاری صفر تا پول خارج از خط — سقف O را در گزارش‌ها overt بگذار.

---

## ۹) Sources (مسیر منطقی)

- `_ops/heart/sog_math.py` · `state/sim/PULSE-EQUATIONS-LOCKED.json`
- `_ops/neural/{bcm,hebbian,nociceptor,latent_space,encoders}.py`
- `_ops/identity_equations.py` · `_ops/cardiac.py` · `_ops/chrono.py`
- `_ops/chrono_rhythm/rhythm.py` · `_ops/heart/{control_law,pulse_arbiter}.py`
- `_ops/doctor/{spectral,spectral_definitions}.py`
- `_ops/epistemics/{bayes,benchmark_metrics,experiment_selector}.py`
- `_ops/math_control/spine.py`
- `4d_system/src/nbb_cp/kernel/fitness.py` · `4d_system/docs/SPEC_v0.2.md`
- `07 - Knowledge/Time-Architecture/MAP.md`
- `04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md`
- `06 - Architecture Maps/METAPHOR-MATH-DICTIONARY-v1.md`
- ADR-035 APPLY · ADR-036 spine · ADR-039 epistemic
- `_ops/scripts/verify_math_atlas.py` (۲۰ ردیف کانونی؛ #15/16/19/20 = SPEC)

پایان اطلس خودکفا — 2026-08-13
