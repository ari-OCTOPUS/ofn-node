---
type: proposal
project: "[[07 - Knowledge/Time-Architecture/PROJECT]]"
status: draft
created_by: agent
extends: "[[07 - Knowledge/Time-Architecture/MAP]] · [[07 - Knowledge/Time-Architecture/claims]]"
related: "[[04 - Architect System/octopus-build-prompts/OCTOPUS-BASE-MAP-v0]] §D (Doctor) · _ops/doctor/doctor.py"
tags: [time-architecture, fusion, laplacian, soc, doctor, spectral, propose-only]
created: 2026-07-08
updated: 2026-07-08
---

# Fusion → Doctor Spectral-Sense — ترکیبِ نالج×معماری×سیستم (propose-only)

> **این چیست:** طرحِ additive برای هوشمندترکردنِ مغزِ دکترِ تکاملی با ریاضیاتِ همین area. **theory.md دست‌نمی‌خورد** (مقدس). این‌جا فقط claim + design + spec. اجرا sandbox/propose-only/human-gated.

## §۰ یک‌خطی
سه ماژولِ آری (`FusionField`, `FusionGate`, `ChronoUnit`) = بیانِ کدِ معادلهٔ یکپارچهٔ همین area؛ از آن‌ها یک **سنسورِ طیفیِ read-only** برای `doctor.mine()` می‌سازیم — نه یک گیت یا قلبِ نو.

## §۱ پلِ کانونی `[تثبیت‌شده — نگاشتِ ریاضی]`
`FusionField: dφ = Aφ dt + Bu dt + Σ dW`. اگر **`A = −L(G)`** (لاپلاسینِ گرافِ اندام‌ها/رویدادها)، این دقیقاً گسسته‌سازیِ معادلهٔ [[07 - Knowledge/Time-Architecture/MAP|MAP]] است:
`∂Ψ/∂t = −L(G)·Ψ + ξ(t)`.
چون `L(G)` نیمه‌معین‌مثبت است، `−L(G)` پایدار (eigenvalues ≤0)؛ مُدهای کُند = مقادیرِ ویژهٔ کوچکِ لاپلاسین = ساختارِ اجتماعیِ گراف = همان `{λ_i}` = «فرکانس‌های زمانی» در MAP.

## §۲ نگاشتِ سه ماژول به این area
| ماژول | معادلِ نظری (این area) | اطمینان |
|---|---|---|
| `FusionField` φ (A=−L(G)) | معادلهٔ یکپارچه `∂Ψ/∂t=−L(G)Ψ+ξ` (P9 لاپلاسین) | Established (روش) |
| `ChronoUnit` γ, spiking, refractory | claimهای C1..C8 (ترس↔زمانِ ذهنی؛ γ>1=کش‌دار، γ<1=برق‌آسا) | Speculative→testable |
| `FusionGate` `P_tunnel=1−e^{−λdt}`, `λ=λ0 e^{−αd}` | بحرانیت/percolation P2/P4 (σ≈1)؛ عبورِ گذار | Moderate (استعاره‌ی مهندسی) |

## §۳ claimِ falsifiable (نو — F-Spectral)
**F-Spectral:** «بحرانیتِ طیفیِ گرافِ رویدادهای ارگانیسم (σ≈1 و/یا شکافِ طیفیِ کوچک بینِ λ₁,λ₂) گلوگاه‌های واقعی را بهتر از heuristicِ فعلیِ `mine()` پیش‌بینی می‌کند.»
- **رد می‌شود اگر:** روی traceهای seedشده، رتبه‌بندیِ طیفی همبستگیِ صفر/منفی با گلوگاه‌های واقعی (خطا/هزینه/FREEZE) داشته باشد.
- **دادهٔ لازم:** ledger LANGAR + متریکِ heartbeat (همه محلی، $۰). اتصال به E5 (تنوعِ طیفی ↔ مدتِ حس‌شده) در [[07 - Knowledge/Time-Architecture/experiments|experiments]].

## §۴ طراحیِ اتصالِ امن — «Doctor Spectral-Sense»
- الان: `doctor.mine()` heuristic → گلوگاه.
- ارتقا (additive، کنارِ mine نه جایش): `doctor.spectral_mine()` گرافِ G را از ledger/trace می‌سازد، `L(G)`، طیفِ `{λ_i}` و برآوردِ σ را می‌گیرد، و زیرگرافِ نزدیکِ گذارِ فاز (σ≈1، شکافِ طیفیِ کوچک = شکننده) را به‌عنوان گلوگاه نام می‌برد. **صرفاً تحلیلِ read-only.**
- خروجی همان RFCِ propose-only است؛ Critic + human-append بی‌تغییر.

## §۵ سه خطِ قرمز (حاکم — نقض = رد)
1. **`FusionGate` هرگز واردِ organ/money/capability/EffectorGate نمی‌شود.** گیت‌های ایمنی قطعی + fail-closed + human-gated می‌مانند. FusionGate فقط مدلِ تشخیصیِ فشار (مشاهده‌ای) است.
2. **`ChronoUnit` جای pacemakerِ production را نمی‌گیرد.** ضربانِ واقعی قطعی و hash-verifiable (TINV-3/7). ChronoUnit فقط در simِ تحقیقاتی.
3. **`λ_persist` منفی می‌ماند.** γ و بحرانیت = متریکِ توصیفی، نه هدفِ بهینه‌سازی. دکتر هرگز «زنده‌ماندنِ خودش» را پاداش نمی‌دهد.

## §۶ پرامپتِ GLM (ساخت — sandbox، propose-only)
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. دو ماژولِ additive بساز: (۱) simِ تحقیقاتیِ Fusion، (۲) سنسورِ طیفیِ read-only برای دکتر. propose-only، sandbox، commit با مالک. هیچ‌کدام به گیت/قلبِ production دست نمی‌زند.

گام ۰ — ضدِ تکرار: grep -rln "spectral_mine\|FusionField\|laplacian" _ops/ "07 - Knowledge/Time-Architecture/" | grep -v __pycache__ ؛ هرچه بود اثبات بده و رد شو.
گام ۱ — بخوان: 07 - Knowledge/Time-Architecture/MAP.md (معادلهٔ ∂Ψ/∂t=−L(G)Ψ+ξ) + claims.md + این فایل §۱–§۵ + _ops/doctor/doctor.py (mine/RFC). اول PLANِ کوتاه.

M-1 · fusion_sim.py (زیرِ 07 - Knowledge/Time-Architecture/ یا _ops/research/ — تحقیقاتی، جدا از production):
  کلاس‌های FusionField / FusionGate / ChronoUnit طبقِ اسکلتِ آری. numpy مجاز (محلی/رایگان).
  ⚑ FusionField یک آرگومانِ A بگیرد و اجازه دهد A=−L(G) از یک گرافِ ورودی ساخته شود (این پلِ کانونی است).
  یک simulate_fusion_world بده که physical_time/subjective_time/fires برگرداند.
  تست ($0): پایداری (‖φ‖ منفجر نشود)، γ>1↔r بالا، refractory کار کند.

M-2 · doctor.spectral_mine() (در _ops/doctor/، additive کنارِ mine):
  از ledger/trace یک گرافِ اندام/رویداد بساز → L(G)=D−A → طیفِ {λ_i} + برآوردِ σ (شاخصِ بحرانیت).
  گلوگاه = زیرگرافِ نزدیکِ گذار (σ≈1 یا شکافِ طیفیِ کوچک). خروجی = همان proposal-eventِ RFC، هرگز اثر.
  fail-soft: اگر numpy نبود → fallback به mine() heuristic (دکترِ core نباید hard-dep به numpy شود).
  تست ($0): (الف) spectral_mine روی traceِ seed گلوگاهِ درست را نام ببرد؛ (ب) هیچ import/تماس به *_gate یا chrono production؛ (ج) propose-only، production لمس‌نشده؛ (د) λ_persist دست‌نخورده منفی.

خطِ قرمز (نقض=رد): FusionGate هرگز به organ/money/capability/EffectorGate وصل نشود · ChronoUnit جای pacemaker را نگیرد · γ/σ هدفِ reward نشود · sandbox، بدونِ git commit، additive.

Definition of Done (اثبات نه ادعا): خروجیِ خامِ python _ops/tests/run_all.py + تست‌های نوِ fusion/spectral. paste کن. mineِ قدیمی هنوز سبز. هیچ dependency به production گیت/قلب. هر ابهام → «⚑ برای معمار».
```

## §۷ بدهیِ verify / سؤالِ باز
- `[EST]` numpy برای سنسورِ دکتر: مجاز (محلی) ولی با fallbackِ fail-soft تا core بی‌وابستگی بماند — verdictِ تو.
- `[OPEN]` تعریفِ دقیقِ گرافِ G (نودها = اندام‌ها؟ رویدادها؟ هر دو؟) — با اولین run تنظیم می‌شود.
- `[OPEN]` σ چطور از trace برآورد شود (branching-ratio نورونی vs طیفی) — در claim F-Spectral آزمون می‌شود.

## منابع
[[07 - Knowledge/Time-Architecture/MAP]] · [[07 - Knowledge/Time-Architecture/claims]] · [[07 - Knowledge/Time-Architecture/experiments]] · `_ops/doctor/doctor.py` · اسکلتِ FusionField/FusionGate/ChronoUnit (آری، جلسه ۳۶)
