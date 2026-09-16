# 11-FINAL — رأی مالک «کمترین محدودیت» → فاز N فعال (2026-08-12)

> حکم مالک: «همه چیز با کمترین محدودیت» = رأی فاز M انتخاب ۳ (اثر محدود).
> ثبت‌شده در `_ops/owner-verdicts.yaml` (tracked): `limited_effect_phase_n=3` · ADR-037.

---

## رأی ثبت‌شده (tracked)

```yaml
limited_effect_phase_n:
  env: OCTOPUS_LIMITED_EFFECT_PHASE_N
  value: "3"            # انتخاب ۳ — اثر محدود
  adr: ADR-037
  expires_to: "0 (advisory-only) only by explicit owner rollback"
```

**تأیید زنده:**
```
vote value: 3
limited_effect.enabled(): True
missing-fields → DENY (fail-closed)
```

## چه چیزی با رأی فعال شد

| جزء | قبل | بعد |
|-----|-----|-----|
| `limited_effect.evaluate()` | همیشه DENY (ENABLED=False) | رأی ۳ → دروازهٔ proposal باز؛ فیلد ناقص → DENY |
| `record_effect()` | — | ثبت audit در `state/limited-effects/active.jsonl` |
| اثرها | — | throttle · pause_proposal · reduce_concurrency · block_suspicious_proposal · request_human_approval |
| اجرای واقعی | — | **همیشه فقط proposal** — از PolicyGate می‌گذرد، `applied=false` |

## مرزهای سخت (با وجود «کمترین محدودیت» حفظ شد)

- **اجرای واقعی هرگز در این ماژول نیست** — فقط `ALLOWED_AS_PROPOSAL`؛ PolicyGate تصمیم نهایی
- `applied=false` · `may_authorize=false` در هر رکورد
- ممنوع همیشگی: تغییر کد/policy · بازنویسی حافظهٔ معنایی · اجرای proposal بدون PolicyGate · پیام خارجی · secret/Project-F
- ۵ فیلد الزامی + رأی؛ غایب → `DENY`
- فایل‌های قفل‌شده (flags/registry/run_all/ADR-033-036/pulse/rhythm/ledger/policy_gate): **صفر تغییر**
- `math_control_spine`/`math_autotune_knobs` (ADR-036) دست‌نخورده — رأی جداگانهٔ مالک

## Shadow Influence — پنجرهٔ ۷ روزه در جریان

```
[records so far: 2]   # probe 1: tick 32668 · probe 2: tick بعدی
real=continue · shadow=continue · divergence=false · applied=false
```

فاز L تا رسیدن به ۱۰۰ نمونه/۷ روز → `KEEP_ADVISORY`؛ بعد `READY_FOR_VOTE`/`REVIEW_REQUIRED`.

## تست‌ها — همه سبز

| suite | نتیجه |
|-------|-------|
| `test_phase_jn.py` | **13/13 PASS** ✅ (J×3 · K×2 · L×3 · N×5) |
| `test_awareness_ask_bridge.py` | 6/6 ✅ |
| `test_memory_ask_recall.py` | 6/6 ✅ |
| `test_miniapp_gateway.py` | 49/49 ✅ |
| `test_owner_verdicts.py` | 15/15 ✅ |
| compile (5 ماژول) | OK ✅ |

## فایل‌های این موج

| فایل | وضعیت |
|------|--------|
| `_ops/owner-verdicts.yaml` | + رأی `limited_effect_phase_n=3` (ADR-037) |
| `_ops/memory/limited_effect.py` | رأی‌خوان (enabled()) + `record_effect()` + audit JSONL |
| `_ops/tests/test_phase_jn.py` | تست‌های رأی/deny/audit به‌روز |
| `state/shadow-influence/divergence.jsonl` | 2 رکورد |
| `10-PHASES-J-N-IMPLEMENTED.md` / `11-FINAL` | گزارش |

## چگونه rollback شود

```bash
# رأی را برگردان (advisory-only):
#   _ops/owner-verdicts.yaml → limited_effect_phase_n.value = "0"
# یا فوری:
set OCTOPUS_LIMITED_EFFECT_PHASE_N=0   # در flags.cmd + restart gateway
```

## خلاصهٔ نهایی

> اختاپوس اکنون با **کمترین محدودیت** کار می‌کند: می‌خواند، یادآوری می‌کند،
> شاهد می‌آورد، معادلات را به‌صورت advice ارائه می‌دهد، و — با رأی مالک —
> **proposal های اثر محدود** (throttle/pause/…) را می‌سازد.
> اما هیچ‌کدام اجرا نمی‌شود مگر از PolicyGate؛ `applied` همیشه false؛
> و هیچ policy/ledger/code/send خودکاری وجود ندارد.
