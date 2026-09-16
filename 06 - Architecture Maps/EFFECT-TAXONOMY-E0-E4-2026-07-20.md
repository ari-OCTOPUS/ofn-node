---
type: architecture
status: active
tags: [architecture, effects, taxonomy, safety, gate]
created: 2026-07-20
updated: 2026-07-20
---

# قراردادِ اثر E0–E4 (gate matrix)

> کلاس‌ها منبعِ یگانه در `_ops/outcomes/taxonomy.py::EFFECT_CLASSES`. Decision Receipt
> `effect_class` را از همان‌جا اعتبارسنجی می‌کند (R0 و غیره رد). این سند = «کدام کنترل
> برای هر کلاس لازم است». v1 = spec + validation (بدونِ فلگِ بی‌خواننده — نقدِ سنتز:
> فلگِ RESERVED = آنتی‌الگوی RUNNER_APPLYِ مرده). enforcementِ producer = گامِ بعد.

## ماتریسِ گِیت

| کلاس | معنا | ledger append | کلیکِ انسان | budget reserve | EffectorGate | idempotency-key | settlement |
|---|---|---|---|---|---|---|---|
| **E0** | محاسبهٔ داخلیِ خالص | — | — | — | — | — | — |
| **E1** | نوشتِ داخلیِ پایدار | — | — | — | — | ✅ (lock+fsync/txn) | — |
| **E2** | اعلانِ فقط-مالک (کارتِ DM) | **کلیکِ مالک → LANGAR** | مالک روی کارت | — | — | ✅ (توکنِ callback) | — |
| **E3** | اقدامِ بیرونیِ برگشت‌پذیر | ✅ | ✅ | اگر پولی | ✅ | ✅ | — |
| **E4** | بیرونیِ برگشت‌ناپذیر/مالی/حقوقی | ✅ | ✅ توکنِ دوکلیک | ✅ | ✅ | ✅ | ✅ |

## carve-out کارتِ مالک (E2) از TINV-7 — رأیِ D-A
- **ارسالِ کارتِ داخلی به DM مالک = E2**؛ از LANGAR-پیش-از-ارسال معاف است (فقط مقصدِ مالک،
  redaction، بدونِ اثرِ بیرونی). **کلیک/تصمیمِ مالک روی کارت در LANGAR ثبت می‌شود** (نه خودِ ارسال).
- **هر ارسال به مشتری/گروه/شخصِ ثالث = E3/E4** و حتماً از EffectorGate + گیت‌های بالا.
- این معافیت باید در `ORGANISM-SPEC` مکتوب شود (از «فرضِ کامنتِ کد» به «قانون») — کارِ owner-gated.

## ناوردی‌ها (اجراشده)
- `effect_class` فقط E0–E4 (taxonomyِ واحد)؛ Decision Receipt غیرِ آن را رد می‌کند. `[test_decision_receipt]`
- کلاس در رسیدِ immutable ثبت می‌شود و **هیچ مدل/agent نمی‌تواند آن را ارتقا دهد** (بدونِ مسیرِ mutate).
- decision_receipt/outcome/memory/spine همه از همان `taxonomy.EFFECT_CLASSES` می‌خوانند (صفر fork).

## آنچه باقی است (owner-gated / فاز بعد)
- سیم‌کشیِ enforcement به producerهای واقعیِ E3/E4 (idempotent request API روی EffectorGate — BLACK،
  با احتیاط). idempotencyِ «phantom» فعلی در chrono باید در همان گام تست شود. **در v1 دست نخورد.**
- نوشتنِ carve-out E2 در ORGANISM-SPEC (رأیِ مالک D-A).
