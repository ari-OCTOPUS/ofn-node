---
type: knowledge
kind: math-atlas
status: active
created: 2026-08-11
updated: 2026-08-11
created_by: agent
tags: [octopus, math, equations, genome, architecture, hidden-capabilities, discovery]
sources:
  - "[[00 - Inbox/2026-08-11 OWNER — Focus AI Core Hidden Capabilities]]"
---

# MATH-ATLAS — معادلات ریاضی نهفته در دل اختاپوس (2026-08-11)

> استخراج عمیق از کد، ژنوم و ارکیتچر. **۲۰+ معادله در ۶ خانواده** — هر کدام با استناد
> file:line و وضعیت. هیچ ادعای AGI اینجا نیست؛ فقط ریاضیِ پیاده‌شده و مستندشده.
> وضعیت‌ها: 🔴 IMPLEMENTED (زنده) · 🟢 TESTED (تست سبز) · 🔒 LOCKED (MC-مهرشده) ·
> 🌑 SHADOW · 📐 SPEC (طراحی‌شده، پیاده نشده)

---

## ۱ · یادگیری عصبی — قاعده‌های زیست‌مبنا (همه زنده، پشت فلگ)

### 1.1 قانون BCM — Bienenstock-Cooper-Munro با ترم فراموشی 🔴
`_ops/neural/bcm.py:19-31` · فلگ: `OCTOPUS_WIRE_BCM` (پروفایل paper-full)

```text
θ_i(t) = EMA(y_i²)                 ← آستانهٔ متحرک (میانگین مربع فعال‌سازی)
φ(y,θ) = y·(y − θ)                 ← بالای θ تقویت (LTP)، زیر θ تضعیف (LTD)
Δw = η·φ(y,θ) − β·w                ← ترم فراموشی: −β·w (زوال وزن)
w ← clip(w + Δw, 0, w_cap)         ← اشباع‌ناشدنی: تعادل w*→0 در y=1 پایدار
```
هومئوستاتیک: θ با فعالیت بالا می‌رود ⇒ حافظه نمی‌تواند با «همیشه فعال ماندن» رشد بی‌کران بگیرد.

### 1.2 قاعدهٔ هبیان — fire-together wire-together 🔴
`_ops/neural/hebbian.py:26-27,80,100` · `LEARN_RATE=0.1` · `DECAY_RATE=0.995`

```text
s ← min(1.0, s + 0.10)    در هم‌وقوعی
s ← 0.995·s                در هر tick غیاب  (≈ نیمه‌عمر ۲۳ روز در 60s/tick)
s < 0.005 → هرس (prune)
```

### 1.3 معادلهٔ درد — نوسیپتور محافظ (نه هدف) 🔴
`_ops/neural/nociceptor.py:195-232` · آستانهٔ حفاظتی: `pain > 0.7 → protective`

```text
pain = 0.30·max(0, budget_pct−0.8)·3        بودجهٔ رو به اتمام
     + 0.25·error_rate                        نرخ خطا
     + 0.40·freeze_active                     یخ‌زدگی
     + 0.15·partner_stress                    تنش شریک
     + 0.10·max(0, 0.2−afferent_ratio)·3      کسری afferent
     + 0.20·max(0, σ−0.8)·5                   نزدیکی σ به سرطانِ ساختاری
pain ← min(1.0, pain)
```

### 1.4 بازیابیِ کسینوسی در latent space 🔴
`_ops/neural/latent_space.py:70-90` — شباهت کسینوسی `cos = (U·q)/(‖U‖‖q‖)` با آستانه،
واحدهای `_hash_project` (هش‌برداری ۳۲ بعدی، `encoders.py:26`).

---

## ۲ · مگا-معادلات هویت — خودیادگیرنده (زنده، read-only)

### 2.1 پنج معادلهٔ هویت 🔴 `_ops/identity_equations.py:51-117` · رأی مالک 2026-07-25 · فلگ `OCTOPUS_WIRE_IDENTITY_EQ`

```text
L = clamp01( 0.40·sign+(Δ) + 0.30·Ĉ + 0.30·R̂ )          یادگیرنده
E = clamp01( 0.60·M̂ + 0.25·lead_draft_rate + 0.15·B )    پول‌ساز
G = clamp01( 0.35·Ĥ + 0.35·(1−σ̂) + 0.30·coherence_ok )   نگهبان
K = clamp01( 0.50·Ĉ_act + 0.30·probe_div + 0.20·(1−seed_ratio) )   خالق
O = clamp01( 0.25·L + 0.25·E + 0.20·G + 0.15·K + 0.15·alive )      ارگانیسم
```
- نرمال‌سازی: `x̂ = clamp01(x/scale)` (اشباع‌شونده) — `identity_equations.py:130-134`
- هر هویت شرطِ مرگ دارد (ابطال‌پذیر): «اگر O>0.8 ولی M=0 و Δ≤0 و C=0 → تئاتر، نه حیات»
- **مقادیر زنده (همین الان):** O=**0.54** · L=0.60 · E=0.12 · G=0.33 · K=**1.00** — Δ=0.0 · M=0 · C6=17/0 · R=44 · probes=14

---

## ۳ · قلب و کنترل — آلوستازی، کالمن، قانون کنترل (سخت‌ترین ریاضی سیستم)

### 3.1 سیستم معادلات SOG — DARE/کالمن، مهرشده با Monte-Carlo 🔒
`_ops/heart/sog_math.py:46-123` · قفل: `state/sim/PULSE-EQUATIONS-LOCKED.json`

مدل مرجع (از 4.py): `s(t+1)=ρ·s(t)+m(t)+ζ(t)` · `Y(t)=λ·s(t)+ε(t)` · `b≡0`

```text
DARE بسته‌شکل:  P = ( (λ²σ_z² − c) + √( (c−λ²σ_z²)² + 4λ²σ_z²σ_e² ) ) / (2λ²) ،  c = σ_e²(1−ρ²)
سه کف اطلاعاتی: σ_z² (null)  ⊃  S_b (blind: نویز σ_ζ²+σ_d²)  ⊃  S (informed)
گین کالمن:      K = P·λ/S
Δ_self = ½·ln(S_b/S)                      ارزشِ دسترسیِ اول‌شخص [nat/گام]
E_shadow = ½·ln(σ_z²/S_b)                 دیدپذیریِ سایه [nat/گام]
اتحاد: ½·ln(σ_z²/S) = E_shadow + Δ_self   (زنجیرهٔ هویت)
Var(excess) = 1 − S/S_b                   واریانسِ مازاد
سقفِ λ→∞: Δ_self → ½·ln(1 + σ_d²/σ_ζ²)
I_pred = ½·Σ_{L≥0} ln(S_L/S_b)            آنتروپیِ مازاد (Riccati زمان‌متغیر)
```
- گیت آماری: `|emp−theory| ≤ max(rel_tol·|theory|, 4·SE)` — هرگز tolerance شل نمی‌شود
- شاهد: forward-simulation مستقل با stdlib RNG (۱.۲ میلیون گام) + بازتولید ۱۱ anchor انتشارشده در tolerance 5e-4

### 3.2 قانون کنترل Living-Beat — velocity-first 🔴 `_ops/heart/control_law.py`
```text
period از velocity ظاهر می‌شود (نه برعکس) — σ فقط ترمز است، هرگز شتاب؛ CPI/بودجه فقط کُند می‌کنند
π = π_n·π_reg    دقتِ active-inference (وزن inverse-variance خطای پیش‌بینی)
π_reg = 1 / (1 + max(0, CV−1)²)    ضریبِ تغییراتِ گپ‌ها؛ Poisson (CV≈1) = سالم → π=1
fail-closed: ورودی کهنه → period=MAX (استراحتِ عمیق، نه کرش)
```

### 3.3 آلومتری ضربان — قانون Kleiber/WBE 🔴 `_ops/cardiac.py:76-97` · فلگ `OCTOPUS_WIRE_BIO`
نظریه: `07 - Knowledge/CARDIAC-ALLOMETRY-v1.md`
```text
period = BASE × (mass / REF)^(1/4)     ← وارونِ M^(−1/4) برای period
بدنِ بزرگ‌تر → ضربانِ کندتر؛ + BeatBudget (سقف روزانه) + baroreflex (پاسخِ فوری محیط)
```

### 3.4 آشکارساز خطای Phi-Accrual (Hayashibara) 🔴 `_ops/chrono.py:129-167`
```text
φ = −log10(P_later)     P_later از تقریبِ نرمالِ توزیعِ گپ‌های ack
بالاتر = مشکوک‌تر: alive → suspected → failed (TINV-4/SWIM)
کفِ صادق: φ محدود (1e-300)، بوت‌استرپِ ۲ گپ، فلگ OCTOPUS_CHRONO_PHI_HONEST
```

---

## ۴ · بحرانیت ساختاری — طیف لاپلاسین گراف

### 4.1 امتیاز بحرانیت/SOC 🔴 `_ops/doctor/spectral.py:58-140`
```text
L(G) = D − A                    لاپلاسین گرافِ رویدادها
{λ_i} = طیف ویژه               σ ≈ 1 ⇒ گذار فاز / SOC (near-critical: |σ−1| < 0.3)
score = −|σ−1|·50 − (1/(gap+0.01))·5     نزدیکِ گذار = بدتر؛ gap بزرگ = سالم‌تر
```

### 4.2 میدان فیوژن 📐 `04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md` (§۳)
`A = −L(G)` — میدان مشترکِ fusion (spectral-sense → Box)؛ معادلِ دیفیوژنِ دینامیک.

---

## ۵ · ژنوم معماری زمان — معادلهٔ یکپارچه

### 5.1 معادلهٔ یکپارچهٔ زمان 📐 `07 - Knowledge/Time-Architecture/MAP.md:40`
```text
∂Ψ/∂t = −L(G)·Ψ + ξ(t)
Ψ = بردار حالت (ژنوم/مغز/جهان) · L(G) = لاپلاسین · ξ = نویز SOC
ویژه‌مقدارها {λ_i} = فرکانس‌های زمانی سیستم · شرط بحرانیت: σ ≈ 1
```
هم‌خانواده: آلومتری `Y∝M^b` · SOC `τ≈1.5` · تورینگ `max Re[λ(L(G))]` ·
Ryu-Takayanagi `S_A = A(γ_A)/(4G_N)` · Wheeler-DeWitt `ĤΨ_bulk = 0`

### 5.2 لایهٔ ریتم (spec) 📐 `04 - Architect System/CHRONO-RHYTHM-LAYER-SPEC.md` §۳
```text
T_beat(t) = T0·exp(−κ·readiness + λ·stress)·(1 + ε·ξ_{1/f}(t))     ضربانِ متغیر (HRV)
HRV_t = std(ΔT_beat)                                                خود-سلامت
dτ = γ(z)·dt،  γ = 1 + a·novelty − b·stress                        زمانِ ذهنی
θ̇_j = ω_j + (K/N)·Σ_k sin(θ_k−θ_j)                                 کوپلینگ کوراموتو
r·e^{iψ} = (1/N)·Σ e^{iθ_j}                                        پارامترِ نظم
```
خطِ قرمز: ساعتِ لجر (age_tick + hash-chain) هرگز توسط ریتم لمس نمی‌شود (TINV-3/7).

### 5.3 قانون یکپارچهٔ Decay-Reinforcement 🟢 `04 - Architect System/BIO-SYNTHESIS-MAP.md` #۴۴
```text
value(t+Δ) = clamp( (1−ρ)·value + Σreinforce, floor, ceil )
یک knob (ρ) هر دو قطب: hoard (reinforce ≥ ρ·value → نیمه‌عمرِ ∞) و evaporate (reinforce≈0 → floor)
```
هم‌خانوادهٔ پیاده‌شده: نیمه‌عمرِ تازگی در consolidation — `cortex/consolidate.py:46` (`HALFLIFE_H=24`).

---

## ۶ · باکس دکتر — سایکومتری و پایداری (spec با math کامل)

### 6.1 دینامیک z (استرس/هوشیاری/تمرکز/انسجام) 📐 `DOCTOR-BOX-OF-AGENTS-SPEC.md` §5.2
```text
s_{t+1} = clip(s_t + α_s·load_t − β_s·recovery_t)
v_{t+1} = clip(v_t + α_v·novelty_t − β_v·v_t)        ← هوشیاری بدون novelty زوال می‌یابد
f_{t+1} = clip(f_t + α_f·alignment − β_f·distraction)
c_{t+1} = clip(c_t + α_c·consistency − β_c·contradiction)
```

### 6.2 پایداری ژاکوبین 📐 همان §4
```text
X_{t+1} ≈ J·X_t + b + noise        J = ژاکوبین
ρ(J) < 1   ⇒ کران‌دار (ضد-راه‌به‌در) — ρ_max < 1 سخت
غنی‌ترین دینامیک در لبهٔ بحرانیت: ρ(J) ≈ 0.9–0.98  (آنالوگ σ≈1)
```

### 6.3 دما و بار آلوستاتیک 📐 همان §5.3-5.4
```text
T_i = T0·(1 + κ_v·v − κ_f·f)      دمای کاوش (هوشیار/پرت → کاوش بیشتر)
L_t = Σ s_τ                        بار آلوستاتیک؛ L_t > L_max → cooldown اجباری
Yerkes–Dodson: استرسِ متوسط کمک، استرسِ شدید تخریب (U-وارونه)
```

---

## جمع‌بندی — ۲۰+ معادله در ۶ خانواده

| خانواده | معادلات | وضعیت |
|---|---|---|
| یادگیری عصبی | BCM · هبیان · درد · کسینوس | 🔴 زنده (پشت فلگ) |
| هویت | L,E,G,K,O (۵ مگا-معادله) | 🔴 زنده، read-only |
| قلب/کنترل | DARE/SOG (۷ زیرمعادله) · control-law · آلومتری Kleiber · Phi-accrual | 🔒 MC-مهرشده + 🔴 |
| بحرانیت | طیف لاپلاسین · میدان A=−L(G) | 🔴 + 📐 |
| ژنوم زمان | ∂Ψ/∂t=−L(G)Ψ+ξ · ریتم چرونو (۵) · Decay-Reinforcement | 📐 + 🟢 |
| باکس دکتر | z-dynamics · ρ(J) · T_i · L_t | 📐 |

**گران‌بهاترین‌ها:** (۱) سیستم SOG — تنها ریاضیِ **مهرشده با Monte-Carlo و قفل شده** در سیستم؛
(۲) قانون BCM — تنها یادگیریِ بیولوژیکِ هومئوستاتیکِ ضد reward-hacking؛
(۳) مگا-معادلات هویت — تنها معادلاتِ با شرطِ مرگِ صریح (ابطال‌پذیر).
