---
type: report
status: done
tags: [octopus, chord, doctor, discovery, integration-map, risk]
updated: 2026-07-18
parent: "[[../OCTOPUS-OS — استراتژی یکپارچه (تلگرام‌محور)]]"
---

# CHORD — کشف، نقشهٔ اتصال، و ثبتِ ریسک (2026-07-18)

> فازِ A پرامپتِ مالک («فیلترِ وترِ ریاضی برای دکترِ تکاملی و اجزای خودترمیم»).
> روش: خواندنِ HANDOFF/رجیستری + grep هدفمند + خواندنِ سطحِ APIهای واقعی. هیچ کدِ زنده‌ای تغییر نکرد.

## ۱) چه چیزی از قبل وجود دارد (شواهدمحور)

| جزء | مسیر | ربط به chord |
|---|---|---|
| دکترِ تکاملی | `_ops/doctor/doctor.py` — `class Doctor`، `advance_rfcs(max_n)` (خط ۶۹۲) + `evolution/self_knowledge/calibration` | مصرف‌کنندهٔ اصلیِ verdict (فاز C) |
| لایهٔ آگاهیِ off-loop | `_ops/epistemics/` — ledger هش‌زنجیره، confidence/sample_size، `authoritative=False` تا دادهٔ کافی | **الگوی معماریِ chord** — خواهرِ ساختاری؛ موازی‌کاری نشد |
| درِ واحدِ LLM | `_ops/cortex/model_router.py::ask(task,…)→{ok,tier,text,reason}` — محلی-اول (Qwen/Ollama) → GLM → Fugu، kill-switch-آگاه | تنها مسیرِ مجازِ LLM برای chord (task جدید: `chord.extract`، پیش‌فرضِ tier=local=$0) |
| مغزِ محلی | `_ops/cortex/local_llm.py::ask→{text,ms,model}|None` — rate-limit اتمیک | fallback آفلاین |
| قراردادِ mission | `mission_id`/`content_sha256` در `telegram_center/mission.py`+`approval_store` (نکته: `mission_contract.py` که HANDOFF می‌گوید untracked بود، الان روی دیسک **نیست**) | chord فقط `mission_id` را به‌عنوان رشته حمل می‌کند — وابستگیِ سخت نگرفتیم |
| Runner ایزوله | `telegram_center/mission_runner.py` — allowlist ۵-اکشنه، worktree-only، `code.apply` همیشه skip | واژگانِ `allowed_actions` chord زیرمجموعهٔ همین allowlist تعریف شد |
| تلگرام | `center.py` (🟡 poll نمی‌کند) + `approval_channel.py` (🟢) + `render.py`/`owner_views.py` | فقط کارت‌ساز pure در chord؛ وایرینگ = لِینِ سریال، flag-off |
| گیت‌های موجود | AUTONOMY-MATRIX (ردهٔ مهم) · CAPABILITY-OK (fail-closed، الان غایب) · LIVE-ENABLED (غایب=paper) | policy chord همین مرزها را تکرارِ ساختاری می‌کند، نه تضعیف |

## ۲) نقشهٔ اتصال (هدف — بعد از رأی مالک)

```
لاگ/تست/تلگرام/API ──▶ observation.py (نرمال‌ساز، scrub)
        LLM (اختیاری) ──▶ adapters/llm_adapter (JSON سخت‌گیر، cap=0.5)
                              │
                              ▼
                 state_vector.build_state_vector
                              ▼
        metrics (وتر) + uncertainty_gate + repair_policy
                              ▼
                    ChordAssessment (advisory)
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
     chord-ledger.jsonl   doctor (فاز C:     telegram_cards
     (hash-chain، سایه)   کنارِ تصمیمِ خودش   (render فقط؛ وایرینگ
                          ثبت می‌کند)         پشتِ OCTOPUS_WIRE_CHORD)
```

## ۳) ثبتِ ریسک

| # | ریسک | شدت | مهار (پیاده‌شده) |
|---|---|---|---|
| R1 | LLM توهم بزند و «شکاف» جعل کند | بالا | JSON سخت‌گیر + cap قوتِ ۰.۵ + خراب→`(None,reason)`→UNKNOWN؛ هرگز حدس |
| R2 | verdict به فرمانِ اجرا تعبیر شود | بالا | `SHADOW_ONLY=True`، `allowed_actions` ساختاراً بدونِ apply/patch/money؛ تستِ صریح |
| R3 | دورزدنِ approval از مسیرِ UI | بالا | telegram_cards فقط string؛ صفر import از telegram_center؛ وایرینگ owner-gated |
| R4 | آلودگیِ state/git (تلهٔ ORG_ROOT سندباکس) | متوسط | مسیرِ ledger از `__file__` resolve می‌شود نه CWD/env؛ تست‌ها `CHORD_STATE_DIR` موقت؛ `_ops/chord/state/` در gitignore |
| R5 | آستانه‌های v0 سلیقه‌ای باشند | متوسط | صادقانه سلیقه‌ای‌اند → دورهٔ سایه + کالیبراسیون با outcome واقعی قبل از هر گیتِ زنده |
| R6 | موازی‌کاری با epistemics/doctor | متوسط | تقسیمِ نقش مکتوب: epistemics=آگاهیِ سیستمی، chord=هندسهٔ تصمیمِ تعمیر، doctor=تصمیم‌گیر |
| R7 | ادعای شبه‌علمی دربارهٔ انسان/آگاهی | متوسط | لایهٔ تحقیق جدا در `03 - Projects/Chord/` با برچسبِ اجباریِ سطحِ شواهد؛ ورود به policy ممنوع تا آزمونِ probe |
| R8 | تداخل با فازبندی P0–P7 | پایین | additive، flag غایب، پول=P7 دست‌نخورده |

## ۴) تصمیم‌های ساختاریِ این جلسه (بدونِ سکوت)

1. مکانِ کد: `_ops/chord/` (نه پکیجِ ریشه) — هم‌قراردادِ epistemics/cortex/doctor.
2. stdlib به‌جای pydantic — قراردادِ ارگانیسم (py3.10 سندباکس / py3.13 مالک؛ صفر وابستگی).
3. `run_all.py` عمداً ویرایش نشد (تلهٔ truncate سندباکس + حرمتِ لِینِ سریال) — ثبتِ تست در run_all = یک خط، در پرامپتِ ایجنتِ بعدی.
4. سه گزارشِ جدا (DISCOVERY/INTEGRATION/RISK) در یک سند ادغام شد — ضدِ پراکندگی.
