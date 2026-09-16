---
type: architecture
status: active
created: 2026-08-11
updated: 2026-08-12
tags: [octopus, metaphor-decode, architecture, governance, explanatory]
related:
  - ADR-033
  - ADR-034
  - architecture/signals-registry.yaml
  - architecture/capabilities-registry.yaml
  - _ops/state/adr-033/reports/INVENTORY.md
---

# Octopus Metaphor Decode — Engineering Reality

> **این نوت توضیح‌دهنده است، نه source of truth اجرایی.**  
> وضعیت واقعیِ signal/capability از registryها، ADRها و test/evidence artifactها می‌آید.
> Invariants: metaphors≠authority · signals≠authorize · PolicyGate+owner · SPEC_NOT_BUILT≠runtime.  
> هدف: جلوگیری از drift مفهومی — نام‌های زیستی اختیار نمی‌سازند.

## یک‌خطی

سنگین‌ترین ارزش واقعی Octopus در **governance، auditability، failure detection و orchestration** است؛ نه در نام‌های زیستی یا ادعاهای شناختی.

---

## جدول دکوپد — استعاره ← واقعیتِ مهندسی

| استعاره | واقعیتِ مهندسی | کجا | بارِ واقعی؟ |
|---|---|---|---|
| **قلب** (cardiac/control_law) | **زمان‌بندِ دینامیکِ حلقهٔ اصلی** — فاصلهٔ بین tickها (period) را بر اساس سرعتِ کار و بودجه تنظیم می‌کند | `heart/control_law.py` | 🟢 باربر — سرعتِ چرخه را واقعاً کنترل می‌کند |
| **سه‌قلب/یک‌ضربان** (pulse_arbiter) | **رأی‌گیری بین سه زمان‌بند** با patternِ coupled-not-merged | `heart/pulse_arbiter.py` | 🟢 الگوی معماری درست |
| **درد** (nociceptor) | **آلارمِ تهی‌شدن منبع + تریپ‌وایر تشخیصی** — مجموع وزنیِ (بودجه، خطا، یخ‌زدگی، σ) با آستانه؛ پس از ADR-034 فقط `PainAssessment` / `protective_proposal` / SHADOW_ALERT — **نه halt مستقیم** | `neural/nociceptor.py` · `neural/pain_assessment.py` · `wiring.emit_pain_assessment` | 🟢 SHADOW diagnostic / protective proposal؛ بدون halt مستقیم |
| **BCM** | **فراموشیِ تطبیقیِ ایندکسِ حافظه** — θ=EMA(y²)، φ=y(y−θ)، −βw؛ معادل: پاکسازیِ هوشمندِ کش با نرمال‌سازیِ فراوانی | `neural/bcm.py` | 🟡 TESTED/SHADOW؛ advisory trace-only |
| **هبیان** | **جدولِ هم‌رخدادی با زوالِ نمایی** — associations با نیمه‌عمر ~۲۳ روز؛ معادل co-occurrence + recency weighting | `neural/hebbian.py` | 🟢 سیم‌کشی (eventclock) |
| **رفلکس** | **قواعدِ if-then ایستای محافظ** — σ>1→throttle proposal، بودجه→slow، freeze→pause؛ یادگیری نیست | `neural/reflex.py` | 🟢 ساده ولی واقعی |
| **ژنوم** | **لایهٔ governance غیرقابل‌تغییرِ پیش‌فرض** — baseline فقط‌خواندنی با amendment process | `genome-system/genome/` | 🟢 ستونِ اصلی |
| **هویت (L,E,G,K,O)** | **بالانس-اسکورکارتِ سلامت** + شرطِ مرگِ ابطال‌پذیر — داشبوردِ خودارزیابی، نه consciousness | `identity_equations.py` | 🟡 فقط-گزارش |
| **σ / بحرانیت** | **شاخصِ توپولوژیکِ سلامتِ گرافِ رویدادها** — شرط‌عددِ تقریبیِ ماتریس | `doctor/spectral.py` · `doctor/criticality_v2.py` | 🟡 ⚠️ تقریبِ اعلام‌شده |
| **Phi-accrual** | **آشکارسازِ مرگِ پروسه (failure detector)** — φ=−log10(P(بدون heartbeat))؛ Cassandra-class، نه AI | `chrono.py` | 🟢 باربر (TINV-4) |
| **SOG/کالمن/DARE** | **تحلیلِ ارزشِ اطلاعات (VoI)** در مدل خطی-گاوسی — information gain، نه router override | `heart/sog_math.py` | 🟢 عددیِ قفل‌شده؛ تصمیم‌ساز نیست |
| **آلومتری/کلایبر** | **قانونِ توانیِ نمادین** — period ∝ (شمارش پروژه‌ها)^(1/4)؛ «جرم» استعاره است | `cardiac.py` | 🟡 عمدتاً نمادین |
| **ریتم چرونو/کوراموتو** | **تزریقِ jitter + متریکِ همزمانی** (order parameter) | spec (CR-B0) | ⚫ SPEC_NOT_BUILT |
| **باکس دکتر (z)** | **مدلِ حالتِ soft-actor** — leaky-integrator + allostatic load | spec | ⚫ SPEC_NOT_BUILT |
| **Consolidation** | **خلاصه‌سازی با وزنِ تازگی** — پنجرهٔ tail + زوال نمایی | `cortex/consolidate.py` | 🟢 |

---

## پس واقعاً چه بود؟

هیچ «هوشِ پنهانِ عرفانی»ای در کار نیست. زیر پوستِ زیست‌شناختی، Octopus این‌هاست:

1. **زمان‌بندِ خودتنظیم** (قلب / درد-پیشنهاد / رفلکس / آلومتری) → feedback control + scheduling + circuit breakers  
2. **حافظهٔ فنی** (BCM / هبیان / consolidation / latent) → dedup + co-occurrence + recency — مثل recommendation engines  
3. **امنیت و حکمرانی** (ژنوم / phi / ledger hash-chain / kill-switch / بودجه / PolicyGate) → **اینجا سنگین‌ترین مهندسی واقعی است**  
4. **مسیریاب** (model_router + breaker + quota) → LLM orchestration با failover  
5. **خود-نمایشِ انگیزشی** (هویت، σ، آلومتری) → KPI dashboard + استعاره برای ارتباط با مالک  

### پانچ‌لاین

- **SOG** مهرشده است (Monte-Carlo + provenance) — فقط VoI می‌سنجد، تصمیم نمی‌سازد.  
- **phi-accrual** الگوریتمِ سیستم‌های توزیع‌شده است، نه «آگاهی».  
- **قوی‌ترین سرمایه:** لایهٔ governance/audit (ژنوم + ledger + گیت‌ها + ADR-033/034) — fail-closed، بدون استعارهٔ لازم برای اختیار.

## حدود ادعا

Chrono Rhythm، Doctor Box و Time Equation در وضعیت SPEC_NOT_BUILT هستند.
اگر روزی پیاده‌سازی شوند، فرضیه‌هایی برای کنترل تطبیقی، زمان‌بندی
و تخمین حالت خواهند بود؛ نه اثبات «هوش»، «آگاهی» یا خودمختاری.

هر ارتقا فقط با این شواهد معتبر است:
- implementation path و feature flag مشخص
- تست واحد، contract و chaos
- اجرای shadow با replay deterministic
- baseline و evidence حداقل هفت‌روزه
- rollback قابل‌اجرا
- approval صریح مالک

---

## مرز استعاره و اختیار

نام‌های قلب، درد، هویت، ژنوم و ریتم، رابط انسانی برای اجزای مهندسی‌اند.
هیچ‌کدام به component اختیار اجرایی اضافه نمی‌کنند.

| نام استعاری | مرز اختیار واقعی |
|---|---|
| قلب | scheduler/control proposal؛ نه policy authority |
| درد | diagnostic/protective proposal؛ نه halt مستقیم |
| BCM/Hebbian | memory/ranking signal؛ نه memory mutation بدون policy |
| هویت | health dashboard؛ نه consciousness یا permission |
| σ / بحرانیت | topology diagnostic؛ نه risk decision مستقل |
| SOG/Kalman | information/value estimate؛ نه router override |
| ژنوم | governance baseline؛ تغییر فقط از amendment path |
| kill switch | تنها کنترل توقف فوری با authority اجرایی مشخص |

> A mathematical signal may describe, warn, or rank.  
> Only versioned policy, verified state, explicit owner authorization,  
> idempotency protection, and an audited control path may permit  
> a state-changing action.

پس از ADR-034: مسیر neural → `protective_proposal` / SHADOW فقط.  
Halt اجرایی فقط از `request_protective_halt` پس از PolicyGate (approval + idempotency + kill-switch + store).

---

## Operational Sources of Truth

- Signal status, authority, and evidence:  
  `architecture/signals-registry.yaml`
- State-changing capabilities and side-effect boundaries:  
  `architecture/capabilities-registry.yaml`
- Runtime inventory:  
  `_ops/state/adr-033/reports/INVENTORY.md`
- Neural containment decision:  
  `03 - Projects/research-spec-compiler/adr/ADR-034-neural-learned-apply-containment.md`
- Evidence-control plane:  
  `03 - Projects/research-spec-compiler/adr/ADR-033-evidence-control-plane.md`

Wikilinks: [[ADR-034-neural-learned-apply-containment]] · [[ADR-033-evidence-control-plane]] · [[06 - Architecture Maps/EVIDENCE-LADDER-TAXONOMY]]
