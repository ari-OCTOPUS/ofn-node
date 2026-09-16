---
type: handoff
kind: math-atlas-report
status: active
created: 2026-08-12
updated: 2026-08-12
created_by: agent
tags: [octopus, math, equations, handoff, next-agent, deepseek-session]
sources:
  - "[[00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus]]"
  - "[[07 - Knowledge/شناخت-اختاپوس/40-MATH-EQUATIONS-RESEARCH-ARCHITECTURE-COMPARISON-2026-08-11]]"
  - "[[07 - Knowledge/شناخت-اختاپوس/41-NEXT-AGENT-MEGAPROMPT-SENIOR-MATH-2026-08-11]]"
  - "[[06 - Architecture Maps/METAPHOR-MATH-DICTIONARY-v1]]"
  - "[[03 - Projects/research-spec-compiler/adr/ADR-035-neural-learned-apply-rearm]]"
---

# HANDOFF — ۲۰ معادلهٔ ریاضی نهفته در اختاپوس (برای ایجنت بعدی)

> **اگر ایجنت به اختاپوس/دیسک دسترسی ندارد** → فقط این را بده (همه‌چیز inline):
> [[00 - Inbox/2026-08-12 SELF-CONTAINED — 20 Math Equations for Offline Agent]]
> یا فایل دسکتاپ: `OCTOPUS-20-MATH-EQUATIONS-SELF-CONTAINED.md`
>
> منبع کامل معادلات: [[00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus]]
> پژوهش + حکم تطبیق: [[07 - Knowledge/شناخت-اختاپوس/40-MATH-EQUATIONS-RESEARCH-ARCHITECTURE-COMPARISON-2026-08-11]]
> مگاپرامپت قدیمی‌تر self-contained: [[07 - Knowledge/شناخت-اختاپوس/41-NEXT-AGENT-MEGAPROMPT-SENIOR-MATH-2026-08-11]]

**وضعیت‌ها:** 🔴 IMPLEMENTED · 🟢 TESTED · 🔒 MC-LOCKED · 🌑 SHADOW/advisory · 📐 SPEC (هنوز کد ندارد)

**تازه‌سازی ۱۲/۰۸/۲۰۲۶ (post-reconciliation):** `OCTOPUS_NEURAL_LEARNED_APPLY=1` (ADR-035 ACCEPTED owner «هردو») — protective apply مسلح، فقط محلی (protective_skip/throttle)، هیچ پول/ارسال/ایمیل/CRM. ADR-034 = حالت rollback (`APPLY=0`). رأیِ tracked در `_ops/owner-verdicts.yaml` fallback است؛ env صریح برنده.
**اصلاح مهم #17:** CR-B0 از قبل ساخته/تست/وصل است (`_ops/chrono_rhythm/rhythm.py`)، نه SPEC_NOT_BUILT. فقط CR-B1 (کوراموتو runtime) partial است. فلگ مستقل `OCTOPUS_WIRE_CHRONO_RHYTHM`.
**اصلاح #14 σ:** legacy `λ_max/(λ₂+ε)` حفظ شد؛ `connectivity_ratio_v2=λ₂/λ_max` به‌عنوان shadow candidate اضافه شد (`_ops/doctor/spectral_definitions.py`).

---

## جدول ۲۰ معادله (شماره‌گذاری کانونی — با وضعیتِ تأییدشدهٔ ۱۲/۰۸)

| # | معادله | فایل کانونی | وضعیت | مصرف‌کننده / نکته |
|---|--------|-------------|-------|-------------------|
| 1 | **BCM** θ=EMA(y²), φ=y(y−θ), Δw=ηφ−βw | `_ops/neural/bcm.py` | 🔴+🟢 | `wiring` → NeuralDriver · APPLY می‌تواند throttle/halt بگذارد |
| 2 | **هبیان** s+=0.1 / s×0.995 / prune<0.005 | `_ops/neural/hebbian.py` | 🔴 | eventclock / wiring |
| 3 | **درد نوسیپتور** pain=Σ وزن‌دار · آستانه 0.7 | `_ops/neural/nociceptor.py` | 🔴 | protective · ADR-035 APPLY=1 |
| 4 | **کسینوس latent** cos(U,q) آستانه‌دار | `_ops/neural/latent_space.py` | 🔴 | بازیابی ۳۲بُعدی هش |
| 5 | **L یادگیرنده** | `_ops/identity_equations.py` | 🔴 RO | کارت/تلگرام |
| 6 | **E پول‌ساز** | همان | 🔴 RO | M≈0 ساختاری تا رأی پول |
| 7 | **G نگهبان** | همان | 🔴 RO | |
| 8 | **K خالق** | همان | 🔴 RO | اغلب بالاست |
| 9 | **O ارگانیسم** | همان | 🔴 RO | ترکیب L,E,G,K,alive · شرط مرگ ابطال‌پذیر |
| 10 | **SOG/DARE/کالمن** P,K,Δ_self,E_shadow,… | `_ops/heart/sog_math.py` + `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` | 🔒 | گران‌بهاترین · MC + قفل provenance |
| 11 | **Living-Beat control** π=π_n·π_reg · velocity-first | `_ops/heart/control_law.py` | 🔴/🌑 | σ فقط ترمز |
| 12 | **آلومتری Kleiber** period∝(mass/REF)^(1/4) | `_ops/cardiac.py` | 🔴 | «جرم»=شمارش پروژه — استعارهٔ کمّی |
| 13 | **Phi-accrual** φ=−log₁₀(P_later) | `_ops/chrono.py` | 🔴 | `OCTOPUS_CHRONO_PHI_HONEST=1` |
| 14 | **طیف لاپلاسین** L=D−A · σ legacy + connectivity_ratio_v2 (shadow) | `_ops/doctor/spectral.py` + `_ops/doctor/spectral_definitions.py` | 🔴 | legacy ε=1e-6 دست‌نخورده؛ v2=λ₂/λ_max |
| 15 | **میدان فیوژن** A=−L(G) | DOCTOR-BOX SPEC | 📐 | |
| 16 | **زمان یکپارچه** ∂Ψ/∂t=−L(G)Ψ+ξ | Time-Architecture/MAP | 📐 | |
| 17 | **ریتم چرونو** T_beat, HRV, dτ, Kuramoto, r | `_ops/chrono_rhythm/rhythm.py` (CR-B0 🔴+🟢) · CR-B1 partial helper | 🔴+🌑 | CR-B0 ساخته/تست/فعال؛ CR-B1 کوراموتو فقط pure helper |
| 18 | **Decay-Reinforcement** value←(1−ρ)·value+Σ | `_ops/cortex/consolidate.py` + BIO-SYNTHESIS-MAP | 🟢 | یک knob ρ |
| 19 | **دینامیک z** (s,v,f,c) | DOCTOR-BOX SPEC §5.2 | 📐 | |
| 20 | **پایداری ρ(J)<1 + T_i + L_t** | DOCTOR-BOX SPEC §4–5 | 📐 | لبهٔ بحرانیت ρ≈0.9–0.98 |

> اگر زیرمعادله‌های SOG (DARE, سه کف اطلاعات، Δ_self, I_pred, …) را جدا بشماری → **۲۰+**؛ اطلس اصلی همین را «۲۰+ در ۶ خانواده» می‌گوید.

---

## ۶ خانواده (نقشهٔ ذهنی)

```text
۱ یادگیری عصبی     → 1–4     (زنده؛ APPLY روی درد/BCM)
۲ هویت             → 5–9     (زنده؛ فقط گزارش)
۳ قلب/کنترل        → 10–13   (SOG قفل‌شده = گوهر)
۴ بحرانیت          → 14–15   (طیف زنده؛ میدان SPEC)
۵ ژنوم زمان        → 16–18   (بیشتر SPEC؛ decay پراکنده)
۶ باکس دکتر        → 19–20   (SPEC کامل، کد ندارد)
```

---

## فلگ‌های مرتبط (۱۲/۰۸ زنده در `OCTOPUS-flags.cmd`)

| فلگ | نقش |
|-----|-----|
| `OCTOPUS_WIRE_BCM=1` | BCM روشن |
| `OCTOPUS_WIRE_BCM_FEED=1` | تغذیهٔ activations |
| `OCTOPUS_NEURAL_LEARNED_APPLY=1` | **جدید:** protective از درد اجرایی |
| `OCTOPUS_WIRE_IDENTITY_EQ=1` | کارت‌های L,E,G,K,O |
| `OCTOPUS_WIRE_BIO=1` | آلومتری |
| `OCTOPUS_CHRONO_PHI_HONEST=1` | phi صادق |

---

## سه گران‌بهاترین (اولویت ایجنت بعدی)

1. **SOG (#10)** — تنها ریاضی MC-مهرشده؛ الگو برای بقیه.  
2. **BCM (#1) + درد (#3)** — حالا با APPLY؛ نیاز به شاهد ۷روزه / ضد reward-hack.  
3. **ریتم چرونو (#17)** — بزرگ‌ترین شکاف SPEC→کد؛ خط قرمز: ساعت لجر را لمس نکن (TINV).

---

## شکاف‌های باز (از سند ۴۰ — هنوز معتبر)

1. σ طیفی تعریف دقیق‌تر از تقریب فعلی  
2. معادلهٔ یکپارچهٔ زمان (#16) پیاده نشده  
3. لایهٔ ریتم (#17) پیاده نشده  
4. باکس دکتر z/ρ/T (#19–20) پیاده نشده  
5. Decay یک knob واحد (#18) هنوز پراکنده است  
6. آلومتری: جرم استعاری را در اسناد overclaim نکن

---

## کار پیشنهادی برای ایجنت بعدی (نه پول/لید)

**A — اندازه‌گیری:** برای #1–14 یک جدول `eq_id → last_value → consumer → effect_class(shadow|execute|report)` از state زنده بساز.  
**B — قفل سبک:** هر معادلهٔ 🔴 بدون تست اختصاصی → یک regression باریک (الگوی `test_heart_math.py`).  
**C — طراحی نه بازنویسی:** برای #17 یک ADR نازک «CR-B0 rhythm shadow»؛ بدون دست زدن به hash-chain.  
**D — ممنوع:** invent کردن AGI · شل کردن گیت آماری SOG · APPLY روی پول/ارسال.

---

## پرامپت یک‌خطی برای ایجنت بعدی

```text
بخوان و ادامه بده:
1) 00 - Inbox/2026-08-12 HANDOFF — 20 Math Equations Atlas for Next Agent.md
2) 00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus.md
3) 07 - Knowledge/شناخت-اختاپوس/40-MATH-EQUATIONS-RESEARCH-ARCHITECTURE-COMPARISON-2026-08-11.md

ماموریت: از جدول ۲۰ معادله، وضعیت زندهٔ هر کدام را با شاهد فایل/فلگ/تست تأیید کن؛
شکاف‌های 📐 را اولویت‌بندی کن؛ برای #17 (ریتم چرونو) طرح shadow بده بدون لمس ledger.
Improve don't rewrite. Secret commit نکن. APPLY=1 را تضعیف نکن مگر شاهد regression.
```

اگر ایجنت **بدون دسترسی به دیسک** است، به‌جای بالا کل متنِ کپی‌پیست داخل
[[07 - Knowledge/شناخت-اختاپوس/41-NEXT-AGENT-MEGAPROMPT-SENIOR-MATH-2026-08-11]] را بده
و این HANDOFF را به‌عنوان «delta ۱۲/۰۸: APPLY=1 + جدول شماره‌دار ۱–۲۰» ضمیمه کن.
