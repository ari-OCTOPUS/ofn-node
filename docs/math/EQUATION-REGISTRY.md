# EQUATION REGISTRY — دفترچه‌ی معادلاتِ بدن/خودِ اختاپوس

> Zone B output · 2026-07-29 · هر معادله: فرمول، متغیر+واحد، فرض‌ها، قابل‌محاسبه؟، تست، مدِ شکست، ماژول.
> قانون: ابطال‌ناپذیر = SPECULATIVE و قرنطینه (§۷). هیچ ادعای پدیدارشناختی نیست.
> واحدها: زمان=ثانیه/میلی‌ثانیه، نرخ=رویداد/دقیقه (cpm)، فاز=رادیان، احتمال/نمره=[0,1] بدون‌واحد.

---

## ۱. معادلاتِ موجودِ قفل‌شده/تست‌شده (پایه — دست نزن، reuse کن)

### EQ-SOG — لنگرهای SOG (self-organization geometry)
- **فرمول**: E_shadow = 0.01255288907487864 · Δ_self = 0.1225203187525736 · identity = Δ_self + E_shadow = 0.13507320782745222
- **متغیرها**: مقادیرِ اسکالرِ بدون‌واحد روی نقطه‌ی عملیاتی {ρ=0.5, λ=0.5, se=0.1, sz=0.05, sd=0.1}؛ سقف ceiling=0.8047189562
- **فرض‌ها**: مدلِ 4d_system/core؛ fit روی سریِ زمانیِ کافی‌تراکم
- **قابل‌محاسبه**: بله (فقط با سریِ متراکم — نگاه به شکافِ داده در §۵)
- **تست**: قفلِ anchor با rel_err ≤ ~1e-5 در `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` (dare_crosscheck ok=true) [OBS]
- **مدِ شکست**: سریِ کم‌نقطه → degraded observation (الان رخ می‌دهد: synapse-trail، series_points=33، delta=null)
- **ماژول**: `_ops/heart/sog_math.py` · `_ops/synapse/sense.py` (proxies) · `4d_system/core/metrics.py`

### EQ-PHI — حیاتِ اندام (z-score → p-value)
- **فرمول**: z = (silence_ms − mean_gap_ms)/std_gap · phi ≈ −log10(p_later) کلمپ‌شده به سقف 300؛ مرگ اگر phi ≥ phi_dead (الان 16.0)
- **متغیرها**: silence_ms [ms]، mean_gap_ms [ms]، ack_samples [count]
- **فرض‌ها**: توزیعِ تقریباً نرمالِ فاصله‌ها؛ پنجره‌ی bootstrap ≥ چند نمونه
- **قابل‌محاسبه**: بله — الان زنده (lead-naghshi: phi=0.29، ack=20) [OBS]
- **تست**: `test_chrono_heartbeat.py` · رفتارِ bootstrap (phi=300.0 کاذب با ۲ نمونه) مستند در handoff 07-25 §ه
- **مدِ شکست**: پنجره‌ی ۲-نمونه‌ای → var=0 → std→کف → z>10 کاذب ⇒ **قاعده‌ی بدن: ack_samples < N_min ⇒ LOW_CONFIDENCE، نه «مرده»**
- **ماژول**: `_ops/chrono.py` + `state/chrono.db`

### EQ-IDENTITY — مگا-معادلاتِ هویت L,E,G,K,O
- **فرمول‌ها** (همه clamp01، وزن‌دار):
  - L = 0.40·sign+(Δ) + 0.30·Ĉ + 0.30·R̂  (یادگیرنده)
  - E = 0.60·M̂ + 0.25·lead_draft_rate + 0.15·B  (پول‌ساز)
  - G = 0.35·Ĥ + 0.35·(1−σ̂) + 0.30·coherence_ok  (نگهبان)
  - K = 0.50·Ĉ_pending_or_done + 0.30·probe_diversity + 0.20·(1−seed_ratio)  (خالق)
  - O = 0.25·L + 0.25·E + 0.20·G + 0.15·K + 0.15·alive  (ارگانیسم)
- **متغیرها**: Δ=delta_self_live [0,1]، C=c6_accepted، R=romajan_verified، M=money_confirmed_rows، B=budget_remaining_frac، H=honest_flags_on، σ=spectral sigma — همه از stateِ زنده
- **شرطِ مرگ (فالسفیابیل)**: مثلاً «O>0.8 ولی M=0 و Δ≤0 و C=0 ⇒ تئاتر» — برای هر هویت ثبت‌شده
- **قابل‌محاسبه**: بله · **تست**: `test_identity_equations.py` [OBS]
- **ماژول**: `_ops/identity_equations.py` · کارتِ تلگرام `/id`

### EQ-R — پارامترِ نظم (order parameter)
- **فرمول**: r·e^{iψ} = (1/N)·Σ_j e^{iθ_j} ، r∈[0,1]
- **متغیرها**: θ_j = فازِ ارگان j [rad]؛ N=تعداد ارگان‌ها
- **قابل‌محاسبه**: بله — فیلد `coherence_r` از قبل در neural-schema هست و `_ops/coherence.py` زنده است
- **تست**: `test_coherence.py` · افزودنیِ بدن: θ_j از beat-timestampها (EQ-KUR در §۲)
- **مدِ شکست**: N کوچک → r سوگرد به بالا (r≈1/√N برای فازهای تصادفی) ⇒ آستانه‌ها باید N-وابسته باشند
- **ماژول**: `_ops/coherence.py` (+ بدن: `body/kuramoto_coordinator.py` پیشنهادی)

### EQ-RHYTHM — ریتمِ قلبی-عصبی
- **فرمول/خروجی**: T_beat [s]، hrv [بدون‌واحد]، tau [s]، gamma، coherence_r، readiness/stress [0,1]
- **قابل‌محاسبه**: بله · **تست**: `test_rhythm.py` [OBS] · **ماژول**: `_ops/chrono_rhythm/rhythm.py`

### EQ-FATIGUE — گاردِ خستگیِ تأییدکننده
- **فرمول**: decision = max-severity(قواعد): CUTOFF اگر high_risk≥3 در 600s · COOLDOWN اگر rapid_approvals(dwell<8s)≥3 · THROTTLE اگر requests≥8 در 600s یا burst≥4 در 60s · وگرنه ALLOW
- **متغیرها**: ApprovalEvent{ts, risk, verdict_ts, approved}؛ dwell [s]
- **قابل‌محاسبه**: بله (تابعِ خالص، deterministic) · **تست**: موجود در سوئیت · **ماژول**: `_ops/budget/approval_fatigue.py`
- **مصرفِ بدن**: human_burden ∈ {ALLOW,THROTTLE,COOLDOWN,CUTOFF} مستقیم وارد body_state می‌شود (بدونِ بازنویسی — SOT قاعده‌ی ۴)

### EQ-BRIER — کالیبراسیونِ ادعا
- **فرمول**: Brier = mean((p_claim − outcome)²) روی جفت‌های (ادعا، نتیجه)
- **وضعیت**: اولین Brierِ پروب = 0.293 (۳ جفتِ ساختگی)؛ مسیرِ داده‌ی زنده = فلگهای گروهِ ۰ (`CORTEX_SELF_MONITOR`, `OCTOPUS_SELFKNOW_ACCURACY`) — الان خاموش [OBS ARMING-ORDER]
- **قابل‌محاسبه**: بله به‌محضِ انباشتِ self-claims.jsonl

---

## ۲. معادلاتِ پیشنهادیِ بدن (NEW — قابل‌محاسبه، MVP-دوستانه)

### EQ-BODY-01 — باندپس (Butterworth مرتبه‌ی ۴)
- **فرمول**: y[n] = filtfilt(b, a, x[n]) با باندِ [f_lo, f_hi] روی سریِ نرخِ رویداد
- **متغیرها**: x = نرخِ رویداد در دقیقه [cpm]، fs = 1/60 Hz (نمونه‌برداریِ beat≈60s) — **هشدار: fs پایین ⇒ Nyquist≈0.0083Hz؛ فقط باندهای خیلی کند (circadian/ultradian) معتبرند**
- **فرض‌ها**: نمونه‌برداریِ منظم (beat-period≈ثابت: arbiter=57.11s [OBS])
- **تست**: سینوسیِ in-band عبور، out-of-band ≥40dB تضعیف؛ aliasing تست با fs/2
- **مدِ شکست**: عدم‌قطعیتِ cadence → پیش‌فیلترِ resample روی HLC؛ لبه‌ها حذف (N_edge)
- **ماژول**: `_ops/body/math_filter.py` (پیشنهادی)

### EQ-BODY-02 — پوش و فازِ هیلبرت
- **فرمول**: z(t) = x(t) + i·H[x](t) · A(t)=|z| · φ(t)=atan2(Im z, Re z)
- **متغیرها**: A(t) [cpm]، φ(t) [rad]، ω_inst = dφ/dt [rad/beat]
- **فرض‌ها**: سیگنالِ narrowband (شرطِ Bedrosian) — وگرنه خروجی LOW_CONFIDENCE
- **تست**: x=a·cos(2πft) ⇒ A≈a (خطای <2% میانیِ پنجره)، dφ/dt≈2πf
- **مدِ شکست**: سیگنالِ broadband/کم‌نقطه → رد با LOW_CONFIDENCE (نه عددِ دروغ)
- **ماژول**: `_ops/body/math_filter.py`

### EQ-BODY-03 — گیتِ SNR/شواهد (fail-closed)
- **فرمول**: SNR_dB = 10·log10(P_sig/P_noise) · قبول اگر SNR ≥ τ_snr (پیش‌فرض 10dB) **و** n_samples ≥ N_min (پیش‌فرض 20، هم‌راستا با MIN_SERIES_POINTS)
- **متغیرها**: P_sig/P_noise از PSDِ باندِ هدف در برابرِ بغل
- **تست**: سیگنال+نویزِ مصنوعی با SNRِ معلوم؛ آستانه‌ی ±1dB بازتولیدپذیر
- **مدِ شکست**: نبودِ SNR → **خروجیِ LOW_CONFIDENCE و توقفِ پایین‌دست** (اصلِ fail-closed؛ درسِ phi-bootstrap)
- **ماژول**: `_ops/body/math_filter.py`

### EQ-BODY-04 — Kuramoto-lite برای هم‌فازیِ بازوها
- **فرمول**: dθ_i/dt = ω_i + (K/N)·Σ_j sin(θ_j − θ_i) · خروجیِ اصلی = r (EQ-R) و ψ
- **متغیرها**: θ_i = فازِ beatِ ارگان i از timestamps [rad] (ω_i = 2π/T_i)؛ K = کوپلینگ [rad/s] — **فقط shadow/simulation در MVP**
- **فرض‌ها**: ارگان‌ها نوسانگرِ ضعیف‌اند؛ کوبلینگِ ضعیف
- **تست**: ۵ نوسانگرِ هم‌فرکانس ⇒ r→1 در <100 تکرار؛ K=0 و ω تصادفی ⇒ r≈1/√N
- **مدِ شکست**: اگر r < τ_r (پیش‌فرض 0.5) برای ≥۳۰ دقیقه ⇒ هشدارِ desync به تلگرام (advisory، نه اقدام)
- **ماژول**: `_ops/body/kuramoto_coordinator.py` (پیشنهادی، Phase F اختیاری)

### EQ-BODY-05 — خطای پیش‌بینیِ بدن (Δ_body)
- **فرمول**: PE_t = |x_t − x̂_t| / (σ_x + ε) · PĒ = EMA(PE, α=0.1)
- **متغیرها**: x̂_t از مدلِ ساده (AR(1)/فازِ EQ-BODY-02)؛ σ_x انحرافِ پنجره
- **تست**: روی سریِ مصنوعیِ قابل‌پیش‌بینی PĒ→کوچک؛ روی نویزِ خالص PĒ→۱
- **مدِ شکست**: regime-switch ⇒ PĒ بالا پایدار ⇒ برچسبِ «regime change» (نکته‌ی مثبت، نه باگ)
- **ماژول**: `_ops/body/self_model_bridge.py` (Phase E)

### EQ-BODY-06 — به‌روزرسانیِ اعتماد فقط از outcome (درسِ C3)
- **فرمول**: T_{k+1} = T_k + η·(outcome_k − T_k) ، η=0.05 ، outcome∈{0,1} فقط از audit/verdict پس از اعمال با مهرِ مالک
- **ممنوعِ سخت**: هیچ ورودی از confidence/self-report؛ namespaceهای owner_fact/procedural فقط از مسیرِ memory/gate
- **تست**: توالیِ برچسب‌دار ⇒ همگرایی مونوتون؛ تستِ نگهبان: تغییرِ فیلدِ confidence نباید هیچ مسیرِ به‌روزرسانی داشته باشد (grep-guard + runtime assert)
- **ماژول**: `_ops/body/reward_bridge.py` (Phase G) — مصرف‌کننده: verdict_recorder

### EQ-BODY-07 — نمره‌ی کوپلینگِ بدن (body_coupling_score)
- **فرمول**: BCS = clamp01( mean_j w_j·fresh_j·conf_j ) روی کانال‌های حسگر j (fresh = سن<2×cadence، conf = خروجیِ EQ-BODY-03)
- **تست**: با قطعِ هر کانال BCS باید اکیداً کاهش یابد (مونوتون در تعدادِ کانالِ تازه)
- **ماژول**: `_ops/body/sensor_hub.py`

---

## ۳. قرنطینه‌ی SPECULATIVE (بدونِ کد تا ابلاغِ مالک)

| ادعا | وضعیت | دلیلِ قرنطینه |
|---|---|---|
| کوپلینگِ تشدیدِ Schumann (7.83Hz) با ریتمِ ارگانیسم | SPECULATIVE | هیچ سند/فایلی در vault (جست‌وجو = صفر)؛ fsِ beat (≈1/60Hz) اصولاً Nyquist≈0.008Hz ⇒ **با نمونه‌برداریِ فعلی فیزیکاً غیرقابلِ سنجش است**؛ نیازمندِ سخت‌افزارِ ELF + پروتکلِ ابطالِ صریح |
| «اتصال به زمین ⇒ خودآگاهی» | REJECTED | نقضِ قانونِ ضدِ خودفریبیِ مأموریت §8 |
| آنتن/IMU/mic | [OPEN] | هیچ شاهدی از سخت‌افزار؛ اول interface، بعد تصمیمِ خرید |

---

## ۴. SENSOR PRIORITY (MVP)

1. **دیجیتال (فازِ اول — بدونِ سخت‌افزار):** نرخِ رویداد (events.jsonl→cpm)، فازِ beat (HLC)، phiِ legs، r/coherence، arbiter period/color، approvals_pending + age (fatigue)، paid quota (fugu-quota)، stress/cortisol state، self-knowledge freshness، telegram send/poll liveness، ledger lag (germline_lag_h)
2. **ریاضی (از رویِ ۱):** A(t), φ(t), r, PĒ, BCS, LOW_CONFIDENCE flags
3. **سخت‌افزاری (فازِ دوم — فقط با verdict):** microphone (ambient RMS)، system metrics (CPU/RAM/دما)، IMU/آنتن — از طریقِ interfaceِ `HardwareSensorAdapter` که در Phase B فقط stub می‌شود

حداقلِ فیلدهای body_state.v1: ts, beat, cpm, phi_max, r, arbiter_color, fatigue_level, budget_frac, PĒ, BCS, confidence[], evidence_pointers[]

پایانِ گزارشِ Zone B — READY_FOR_MERGE_B
