---
type: report
kind: reconciliation
status: done
created: 2026-08-12
updated: 2026-08-12
created_by: agent
tags: [octopus, math, equations, reconciliation, apply, chrono-rhythm, spectral, adr-035]
sources:
  - "[[00 - Inbox/2026-08-12 HANDOFF — 20 Math Equations Atlas for Next Agent]]"
  - "[[00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus]]"
  - "[[07 - Knowledge/شناخت-اختاپوس/40-MATH-EQUATIONS-RESEARCH-ARCHITECTURE-COMPARISON-2026-08-11]]"
  - "[[architecture/SPECTRAL-DEF-2026-08-12]]"
---

# گزارش آشتیِ اطلس ۲۰ معادله با حقیقت runtime (2026-08-12)

> مأموریت: تمام داده‌ها و چت‌ها را کنارِ کد واقعی اختاپوس بگذار و آپدیت کامل را اجرا کن؛
> تصمیم‌ها بر پایهٔ قوانین خودِ داده‌ها (تقدمِ runtime/owner-verdicts + Improve don't rewrite).

---

## §۰. حکم‌های نهایی (بر پایهٔ قانون تقدمِ خودِ مخزن)

قانونِ `_ops/owner-verdicts.yaml` صریح است: **env/flags.cmd برنده است؛ owner-verdicts fallback؛
واگرایی خطاست نه سکوت.** بر این اساس:

1. **APPLY = ADR-035 / ARMED.** runtime + flags.cmd + ADR-035-LIVE-VERIFY + EVIDENCE-LADDER
   همگی ADR-035 را تأیید می‌کنند. commit `d677c3c` یک revert ناقصِ paperwork بود — کد
   (`wiring.py`) را برگرداند نکرد. سه فایلِ stale (signals-registry + capability JSON +
   validator) هم‌راستا شدند.
2. **#17/CR-B0 = ساخته/تست/فعال** (`_ops/chrono_rhythm/rhythm.py`). فقط **CR-B1 کوراموتو**
   به‌صورت pure helper اضافه شد؛ runtime-disconnected. `rhythm_shadow.py` ساخته **نشده‌است** —
   تکرار بود.
3. **#14 σ = legacy دست‌نخورده.** `λ_max/(λ₂+ε)` با `ε=1e-6` تاریخی حفظ شد. `connectivity_ratio_v2=λ₂/λ_max`
   به‌عنوان shadow candidate، versioned اضافه شد. UNKNOWN برای disconnected/tiny.
4. **UNKNOWN هرگز به موفقیتِ جعلی تبدیل نمی‌شود** — در verifier، evidence aggregator، و σ.

---

## §۱. فایل‌های تغییرکرده (۳۰ فایل)

### حاکمیت APPLY (هم‌راستاسازی با ADR-035)
| فایل | تغییر |
|------|-------|
| `_ops/owner-verdicts.yaml` | رأیِ tracked `neural_learned_apply=1` + `chrono_rhythm_cr_b0=1` |
| `_ops/wiring.py` | `effective_flag()` helper؛ `rhythm_enabled()` (bare-safe)؛ APPLY از fallback استفاده می‌کند |
| `_ops/organism.py` | boot ریتم از `wire_rhythm` جدا؛ protective حالت dual-mode با `executable` |
| `architecture/signals-registry.yaml` | `neural-learned-apply`: ARMED/gate_internal/may_gate=true/production=true |
| `architecture/signals-registry.schema.json` | `forbidden_effects` مجاز شد |
| `_ops/capabilities/neural-learned-apply.json` | ARMED با forbidden_effects + مرز سخت |
| `_ops/capabilities/chrono-rhythm-cr-b0.json` | TESTED/SHADOW با code_path واقعی |
| `_ops/scripts/validate_signals_registry.py` | hard-pin به ADR-035 |
| `_ops/tests/test_signals_registry_schema.py` | انتظار ARMED |
| `_ops/tests/test_registry_semantic_validator.py` | انتظار ARMED |
| `_ops/tests/test_adr033_control_plane.py` | انتظار CR-B0 TESTED |
| `_ops/tests/test_adr034_neural_demote.py` | انتظار capability ARMED |
| `_ops/tests/test_adr035_neural_rearm.py` | +تست fallback tracked |
| `_ops/tests/test_neural_loop_close.py` | +تست unset=ARMED fallback |

### CR-B0 تقویت‌شده + CR-B1 pure (بدون duplicate)
| فایل | تغییر |
|------|-------|
| `_ops/chrono_rhythm/rhythm.py` | بازنویسی: bounded/non-finite-safe، `coherence_r=None`، `kuramoto_order_parameter()` + `kuramoto_step()` pure، `CR_B0_FORMULA_VERSION` |
| `_ops/tests/test_rhythm.py` | +۴ تست: non-finite، readiness monotonic، کوراموتو edges/step |

### σ نسخه‌دار + shadow
| فایل | تغییر |
|------|-------|
| `_ops/doctor/spectral_definitions.py` | **جدید**: legacy (`ε=1e-6`) + v2 (`λ₂/λ_max`) با version IDs |
| `_ops/doctor/spectral.py` | `estimate_sigma` به legacy delegate می‌کند؛ import مقاوم |
| `_ops/doctor/spectral_metrics.py` | +`connectivity_ratio_v2`؛ import مقاوم |
| `_ops/doctor/criticality_v2.py` | +`connectivity_ratio_v2` + metric جدا |
| `_ops/telemetry/criticality_metrics.py` | +gauge `octopus.spectral.connectivity_ratio_v2` |
| `architecture/SPECTRAL-DEF-2026-08-12.md` | **جدید**: ADR تعریف‌ها |
| `architecture/signals-registry.yaml` | +`definition_ref`، version bump |
| `_ops/tests/test_spectral_definitions.py` | **جدید**: ۲۹ تست |
| `_ops/tests/test_spectral_definitions.py` | tolerance با ε=1e-6 |

### Verifier canonical + Evidence aggregator
| فایل | تغییر |
|------|-------|
| `_ops/scripts/verify_math_atlas.py` | **جدید**: ۲۰ ردیف کانونی، AST، flag precedence، SOG lock واقعی |
| `_ops/tests/test_verify_math_atlas.py` | **جدید**: ۴۱ تست |
| `_ops/telemetry/neural_apply_evidence.py` | **جدید**: aggregator هفت‌روزه، sha256 dedup، complete_days، verdict |
| `_ops/tests/test_neural_apply_evidence.py` | **جدید**: ۱۲۲ تست |

### profile + run_all
| فایل | تغییر |
|------|-------|
| `_ops/tests/test_profile_w3.py` | +bare-safe rhythm، override دوجهته |
| `_ops/tests/run_all.py` | +۳ تست نو ثبت شد |

### اسناد
| فایل | تغییر |
|------|-------|
| `00 - Inbox/2026-08-12 HANDOFF — 20 Math Equations…md` | جدول با حقیقت اصلاح‌شده |

---

## §۲. نتایج تست (همه سبز)

| suite | نتیجه |
|-------|-------|
| test_owner_verdicts | 15/15 ✅ |
| test_profile_w3 | ✅ |
| test_relationships_wired | ✅ |
| test_pulse_arbiter | ✅ |
| test_rhythm | 17/17 ✅ |
| test_spectral | ✅ |
| test_spectral_definitions | 29/29 ✅ |
| test_signals_registry_schema | ✅ |
| test_registry_semantic_validator | ✅ |
| test_adr033_control_plane | ✅ |
| test_adr034_neural_demote | 10/10 ✅ |
| test_adr035_neural_rearm | 8/8 ✅ |
| test_neural_loop_close | ✅ |
| test_organism_protective | ✅ |
| test_frontier | ✅ |
| test_identity_equations | ✅ |
| test_heart_math | ✅ |
| test_cardiac_allometry | ✅ |
| test_chrono_heartbeat | ✅ |
| test_verify_math_atlas (pytest) | 41/41 ✅ |
| test_neural_apply_evidence (pytest) | 122/122 ✅ |

**مجموع: ۱۹ suite کلاسیک + ۱۶۳ pytest — بدون رگرسیون.**

### اعتبارسنجی‌های مستقیم
- `validate_signals_registry.py` → `{"ok": true, "errors": 0}`
- `verify_math_atlas.py` → exit 0؛ ۱۶ ردیف OK + ۴ SPEC (#15/#16/#19/#20)؛ APPLY/registry OK

---

## §۳. تصمیم‌های کلیدی و دلیل

| تصمیم | دلیل (بر پایهٔ قانون مخزن) |
|-------|-----------------------------|
| ADR-035 نه ADR-034 | تقدمِ runtime در owner-verdicts.yaml؛ کد+wiring+evidence همگی ADR-035 |
| `gate_internal` نه `trace_only` برای APPLY | validator: `production_apply_enabled=true` نیازمند `ARMED+gate_internal`؛ `SHADOW+trace_only+true` متناقض |
| `rhythm_shadow.py` ساخته نشد | `_ops/chrono_rhythm/rhythm.py` موجود است (CR-B0)؛ Improve don't rewrite |
| CR-B1 فقط pure helper | runtime phase source اختراع نشد؛ scheduler وصل نشد |
| σ legacy دست‌نخورده | مصرف‌کنندگان زنده به جهت فعلی وابسته‌اند؛ `λ₂/λ_max` فقط shadow |
| UNKNOWN برای disconnected/tiny | نبودِ داده = UNKNOWN نه صفرِ جعلی |

---

## §۴. مرزهای سختِ حفظ‌شده

- هیچ پول/ارسال/ایمیل/CRM/ledger از مسیر APPLY — `may_mutate_ledger=false`, `may_trigger_tool=false`
- ریتم هیچ IO/ledger/hash-chain لمس نمی‌کند — تستِ purity AST
- σ legacy رفتار زنده را تغییر نداد — anchor‌ها ثابت
- verifier/evidence هیچ ماژول runtime را اجرا نمی‌کنند — read-only
- هیچ commit/secret/network call انجام نشد

---

## §۵. کارهای باقی‌مانده (نیاز به رأی مالک یا پنجرهٔ ۷روزه)

1. **evidence هفت‌روزه APPLY**: aggregator ساخته شد ولی نیاز به ۷ روز دادهٔ `pain-assessment.jsonl` + incident stream دارد. تا那时 `INSUFFICIENT_EVIDENCE`.
2. **CR-B1 کوراموتو runtime**: helper خالص هست؛ وصل‌کردنش به scheduler نیاز به AUC + رأی دارد.
3. **σ v2 canonical شدن**: فقط بعد از مقایسه/AUC + رأی.
4. **مستندات اطلس دیگر** (MATH-ATLAS، سند ۴۰، سند ۴۱): جدول اصلی در HANDOFF اصلاح شد؛ بقیه می‌توانند بعداً هم‌راستا شوند.

---

*پایان گزارش آشتی — همه‌چیز با شاهد، بدون بازنویسی، بدون secret commit.*
