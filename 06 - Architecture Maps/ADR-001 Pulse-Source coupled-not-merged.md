---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [pulse, doctor, cardiac, safety]
created: 2026-07-10
updated: 2026-07-10
aligns_to: "[[07 - Knowledge/CARDIAC-ALLOMETRY-v1]]"
---

# ADR-001 — منبعِ نبض: coupled، نه merged (Heart ⟂ Doctor)

> **status:** accepted (2026-07-10) · **deciders:** ari (owner) + Claude · **supersedes:** — · **superseded_by:** —
> **حکمِ یک‌خطی:** یک سیستمِ دینامیکی، **دو ماژولِ نرم‌افزاری**. به‌هم‌بسته (coupled)، نه یکی‌شده (merged).

## زمینه (Context)
سؤال: کنترلرِ ریتم/tempo (**Heart**) و موتورِ selection + supervision + evolution (**Doctor / دکترِ تکاملی**) — یک ماژولِ ادغام‌شده (ایدهٔ ۲) یا دو ماژولِ جدا با یک interface (ایدهٔ ۱)؟

سه معنای «قلب» در اسناد قاطی شده بود و اول de-metaphor شد:

| استعارهٔ «قلب» | معادلِ مهندسی | قطب |
|---|---|---|
| ledger (Chrono) | LANGAR: root-of-trust، irreversibility، `age_tick` | ساده و قابل‌اعتماد |
| pacemaker | metronomeِ liveness (`chrono.py`) — سند صریح: pacemaker ≠ قلب | ساده و قابل‌اعتماد |
| ریتمِ زیستی (منشور) | limit-cycle + σ (VariabilityMonitor) | ساده و قابل‌اعتماد |
| **دکترِ تکاملی** | supervision (OTP) + eval-harness + selection + خودبهبودی (H-4) | **پرتلاطم و پرریسک** |

انضباطِ ساختاریِ کلِ معماری = جداکردنِ قطبِ «ساده/قابل‌اعتماد» (Heart، به هر سه معنا) از قطبِ «پرریسک/در‌حالِ‌تکامل» (Doctor).

## تصمیم (Decision)
**ایدهٔ ۱ (جدا) پذیرفته؛ ایدهٔ ۲ (ادغام) رد.** با یک اصلاحِ interface: **Doctor پارامتر/setpoint می‌نویسد، نه نرخ.** نرخ از dynamicsِ Heart *ظاهر* می‌شود (cascaded control: حلقهٔ داخلیِ سریع = رفلکس/نبض؛ حلقهٔ بیرونیِ کند = planning/selection).

## گروندینگ به کدِ واقعی — **formalismِ فعلی FHN نیست**
یافتهٔ کلیدی (تعیین‌کنندهٔ جزئیاتِ interface):

- **pacemaker** = `_ops/chrono.py` — HLC metronomeِ ساده («chrono substrate»، گزارشِ P1-HEART).
- **لایهٔ ریتم** = `_ops/cardiac.py` — **allostatic-allometric**: `period ∝ mass^(1/4)` + `BeatBudget` + `Baroreflex`. صراحتِ فایل: «فقط `period_s` را **advisory** پیشنهاد می‌دهند — **pacemaker تصمیم می‌گیرد**» (cardiac.py:14, `effective_period`)؛ پشتِ `OCTOPUS_WIRE_BIO`، پیش‌فرض خاموش.
- **σ** = از `replication.py`، تغذیه‌شده از رویدادهای **CONFIRMED** (attribution) — نه خودگزارشِ Doctor. (`cardiac.estimate_mass` هم `confirmed` را از `fitness-latest.json` می‌خواند، cardiac.py:66-70.)
- **verifier-independence از قبل enforce شده:** `doctor.py` صراحتاً «معیارِ خودش را ویرایش نمی‌کند»؛ `capability_gate` فقط CONFIRMED.
- **FHN / PulseCore پیاده نشده** — در منشور به‌عنوانِ milestone `M-♥` (آینده).

**نتیجه (طبقِ trichotomyِ خودِ verdict):** چون formalismِ فعلی **allostatic = setpoint-modulation** است، طبق شاخهٔ سومِ خودت **سمتِ Doctor می‌نشیند**. مبنای FHN «v-fast/w-slow» تنها از `M-♥` فعال می‌شود. حکم (جدا) در هر سه حالت ثابت است؛ فقط interface مطابقِ formalismِ فعلی مشخص شد.

## Interface (مرزِ سختی که نباید بشکنی)
```text
# Doctor → Heart  (فقط setpoint، هرگز نرخِ اسکالر)
HeartParams { target_sigma, viable_band:(lo,hi), epoch_seq,
              # نگاشتِ allostatic به کدِ فعلی:
              target_mass_scale, daily_beat_cap, baroreflex_gain }

# Heart → Doctor  (فقط سیگنال؛ read-only از منظرِ Doctor)
HeartSignal { beat_seq, period_s (tempo), sigma_now, baro_factor (arousal) }

# منبعِ حقیقتِ σ — بیرونِ هر دو، در LANGAR:
sigma_now ← از رویدادهای CONFIRMED محاسبه می‌شود، نه ادعای Doctor
```
**seam از قبل هست:** `cardiac.effective_period(...)` همان نقطهٔ advisory است؛ تنها تغییر = setpointها از Doctor بیایند (per-epoch)، نه محاسبهٔ محلی. σ در Heart سنجیده می‌شود ولی از CONFIRMED تغذیه — پس نه Heart می‌تواند σ را جعل کند، نه Doctor. (بستنِ R6 + گپِ σ-integrity هم‌زمان.)

## پیامدها (چهار دلیلِ جداسازی — به‌ترتیبِ اهمیت)
1. **حلقهٔ حرام (قاطع):** ادغام یعنی Doctor هم σ را می‌سازد، هم می‌سنجد، هم بر پایهٔ σ spawn/cull می‌کند = خودنمره‌دهی → reward-hacking → محورِ سرطان (R6, H-4). جداسازی «سنجشِ σ» را ساختاری از «مصرفِ σ» جدا نگه می‌دارد (external-gate در سطحِ توپولوژیِ ماژول).
2. **دامنهٔ شکستِ مشترک (E15):** Doctor همان supervisor است. اگر Heart داخلش ادغام شود، crashِ Doctor = توقفِ ضربان = مرگِ کامل، بی‌هیچ reaperِ بیرونی. جداسازی می‌گذارد Heartِ ساده بتپد حتی وقتی Doctorِ پیچیده می‌میرد؛ **reaperِ برون‌حلقه (C2)** Doctor را restart کند. → هرگز robustترین و شکننده‌ترین اجزا در یک failure-domain.
3. **عدم‌تطابقِ timescale/formalism:** Heart = حلقهٔ سریعِ پیوسته؛ Doctor = حلقهٔ کندِ گسسته/رویدادی (epoch روزانه، re-plan هفتگی). ادغامِ oscillatorِ سریع با selection-engineِ کندِ episodic = category error (دو ساعتِ رقیب در یک جعبه). در M-♥ با FHN: `v-fast`=نبضِ عملیاتی، `w-slow`=مدولاتورِ Doctor؛ coupling ریاضی ≠ fusion نرم‌افزاری.
4. **anti-pattern «نرخ‌دادن»:** اگر Doctor یک BPMِ اسکالر بدهد، «ساعت» ساخته‌ای نه «قلب» (منشور §۳.۱). پس interface = setpoint، نرخ ظاهرشونده.

## موارد باز / نامعلوم (Open)
- **`unknown` — نیازمندِ cross-check:** ادعای «M0.5 سبز نیست · ledger از ردیفِ ۶۸ خراب · restore path شکسته» از اسنادِ آپلودیِ مالک است که این ایجنت نخوانده. در vault، scarِ زنجیرهٔ genome که دیده شد در **line 40** بود (نه ۶۸)، و organism در ۲۰۲۶-۰۷-۱۰ زنده و در حالِ نوشتنِ state است. باید وضعیتِ واقعیِ ledger/restore جداگانه تأیید شود پیش از coupling.
- **`draft`:** FHN (M-♥) هنوز کد نشده؛ interfaceِ بالا برای هر دو حالت (allostatic حالا، FHN بعد) کار می‌کند.
- **سؤالِ باز (رفع‌شده در این ADR):** formalismِ فعلی → allostatic (نه FHN، نه replicator). اگر بعداً σ خودش با replicator/branching مدل شد، آن ریاضی متعلق به Doctor است و Heart فقط σ را می‌خواند.

## ترتیبِ اجرا (grounded)
1. **حالا:** pacemakerِ ساده (نرخِ ثابت، فقط liveness) + قفلِ interfaceِ typed از همین حالا.
2. **بعد از سبزشدنِ health-gate (M0.5):** Doctor فقط `HeartParams` بنویسد (per-epoch). σ همچنان از CONFIRMED.
3. **`M-♥`:** دینامیکِ FHN (`v-fast`) جایگزینِ pacemakerِ ثابت؛ «نرخِ ظاهرشونده» فعال. Doctor همان `w-slow` می‌ماند.
4. **reaperِ برون‌حلقه (C2)** قبل از هر خودبهبودیِ H-4 اجباری.

## جدولِ تصمیم (۱۰ = بهترین در آن محور)
| محور | ایدهٔ ۱ (جدا+coupled) | ایدهٔ ۲ (merged) |
|---|---|---|
| هزینه/زمانِ اولیه | 6 | 7 |
| Complexity (مدیریت‌پذیر) | 8 | 4 (god-module) |
| Scalability | 9 | 4 |
| Maintainability (تستِ مستقل) | 9 | 3 |
| Security/Safety | 9 | 2 (self-grading + shared failure) |

با ارزش‌های صریحِ پروژه (safety-before-capability، fail-closed، external-gate)، ایدهٔ ۱ برندهٔ روشنِ ROI است.
