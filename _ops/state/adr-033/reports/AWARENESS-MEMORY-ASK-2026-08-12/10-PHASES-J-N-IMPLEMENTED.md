# 10-PHASES-J-N-IMPLEMENTED — اجرای فاز J→N (2026-08-12)

> طبق رأی مالک «همرو الان کامل کن» — با حفظ همهٔ قواعد:
> **هیچ APPLY جدید، هیچ تغییر فایل قفل‌شده، memory may_authorize=false،
> فاز N فقط با رأی صریح انتخاب ۳ فعال می‌شود (الان disabled).**

---

## جدول اجرا

| فاز | وضعیت | شاهد |
|-----|--------|------|
| **J** اتصال خودکار advice-only | ✅ کامل | `_ops/memory/equation_advice.py` + اتصال `collaborator.py` |
| **K** Shadow Influence | ✅ کامل + probe اول | `_ops/memory/shadow_influence.py` + `divergence.jsonl` (1 رکورد) |
| **L** ارزیابی | ✅ کامل (نیازمند ۷ روز) | `_ops/memory/shadow_evaluation.py` → KEEP_ADVISORY الان |
| **M** رأی مالک | 📌 ثبت پیشنهادی | انتخاب ۲ (فقط پیشنهاد) — رأی نهایی با شما |
| **N** خودکارسازی محدود | ⚠️ آماده ولی **disabled** | `_ops/memory/limited_effect.py` — ENABLED=False |

---

## ۱. فاز J — معادلات = توصیه فقط (equation_advice_only)

**جدید:** `_ops/memory/equation_advice.py`
- می‌خواند: ORGANISM-STATE (pain_assessment, math_control, replication sigma) + phi از state
- خروجی هر معادله: `{eq, value, advice: continue|slow_down}`

**اتصال additive** در `collaborator.py` (بعد از بلوک facts):
```python
data["equation_advice"] = {
    "equation_advice_only": True,
    "decision_effect": False,
    "apply_effect": False,
    "equations_consulted": [...],
    "aggregate_advice": "continue|slow_down",
}
```

**نتیجهٔ زنده** (probe اول): `equations_consulted=["spectral-sigma-legacy"]`,
pain/control در این تیک سیگنال نداشتند → صادقانه فقط σ.

## ۲. فاز K — Shadow Influence (دو مسیر، applied=false)

**جدید:** `_ops/memory/shadow_influence.py`
- `real_decision_from_state()` → تصمیم واقعی (continue/halt/protective_skip)
- `shadow_decision_from_advice()` → تصمیم فرضی از advice معادلات
- `evaluate_shadow()` → divergence + `applied=false` + `may_authorize=false`
- `record_divergence()` → append به `state/shadow-influence/divergence.jsonl`

**probe اول زنده:**
```json
{"tick": 32668, "real_decision": "continue", "shadow_decision": "continue",
 "divergence": false, "applied": false, "may_authorize": false}
```

## ۳. فاز L — ارزیابی (معیارهای ۷ روزه)

**جدید:** `_ops/memory/shadow_evaluation.py`
- معیارها: divergence_rate · shadow_slow_down_rate · false_positive_rate · churn · integrity
- آستانه: `min_samples=100` و `window_days=7`
- verdict: `KEEP_ADVISORY` (داده کافی نیست) / `READY_FOR_VOTE` / `REVIEW_REQUIRED`
- نقض integrity (`applied=true` یا `may_authorize=true`) → همیشه `REVIEW_REQUIRED`

**الان:** `KEEP_ADVISORY` — 1 رکورد. پنجرهٔ ۷ روزه شروع شده.

## ۴. فاز M — رأی مالک

**ثبت پیشنهادی (طبق طرح): انتخاب ۲ — «فقط پیشنهاد».**

| انتخاب | وضعیت |
|--------|--------|
| ۱. نه (همه advisory) | در دسترس |
| **۲. فقط پیشنهاد (تأیید تو)** | **پیشنهادی** |
| ۳. اثر محدود (throttle/pause) | بعد از شواهد فاز L |

رأی نهایی شما لازم است. تا آن زمان همه‌چیز advisory است.

## ۵. فاز N — خودکارسازی محدود (disabled)

**جدید:** `_ops/memory/limited_effect.py` — `ENABLED = False` (سخت)
- ۵ فیلد الزامی: `proposal_hash · policy_version · state_version · expiry_at · idempotency_key` + `owner_verdict`
- غایب/ناقص → `DENY`
- حتی با فیلد کامل → `ALLOWED_AS_PROPOSAL` (فقط proposal، `applied=false`)
- اجرای واقعی فقط از PolicyGate — این ماژول هرگز اجرا نمی‌کند

**فعال‌سازی:** فقط بعد از رأی صریح انتخاب ۳ در فاز M + شواهد فاز L. هیچ کد دیگری تغییر نمی‌کند.

---

## تست‌ها (همه سبز)

| suite | نتیجه |
|-------|-------|
| `test_phase_jn.py` (**جدید**) | **11/11 PASS** ✅ |
| `test_awareness_ask_bridge.py` | 6/6 ✅ (regression) |
| `test_memory_ask_recall.py` | 6/6 ✅ (regression) |
| `test_miniapp_gateway.py` | 49/49 ✅ (regression) |
| collab_model_adapter smoke | ctx 1856 chars · brains+4d ✅ |

## ثبت در run_all (WORKLOCK — گزارش، بدون تغییر)

تست‌های نو برای ثبت در `_ops/tests/run_all.py` (فعلاً دست‌نخورده طبق قفل):
- `test_phase_jn.py`

---

## فایل‌های قفل‌شده — دست‌نخورده ✅

`flags.cmd` · `signals-registry.yaml` · `capabilities-registry.yaml` · `run_all.py` ·
ADR-033/034/035 · `pulse_arbiter.py` · `rhythm.py` · `ledger.py` · `policy_gate.py` — صفر تغییر.

## مرزهای سخت (حفظ‌شده)

- memory `may_authorize=false` — در هر ۴ ماژول تست‌شده
- talk EXTERNAL_SEND blocked · `send_attempted=false`
- `vault_auto_write` arm نشد
- 4d/8 مغز revive نشد
- Neural APPLY فقط protective_skip (ADR-035)
- هیچ commit/secret/network — همه‌چیز local

---

## قدم بعدی برای تو

1. **رأی فاز M** — پیشنهاد: انتخاب ۲ (فقط پیشنهاد). انتخاب ۳ بعد از ۷ روز شواهد سایه.
2. بعد از رأی، فاز N با `ENABLED=True` + ADR کوچک + capability record فعال می‌شود.
3. برای دیدن اثر J→K در وب: مینی‌اپ را ببند/باز کن، تب پرسش → «از چی تشکیل شدی؟» →
   پاسخ شامل `data.equation_advice` با برچسب advice_only است.
