---
type: evidence
task: fx-source-divergence
tags: [rba, fx, divergence, canonical, live-b, 2026-08-20]
created: 2026-08-20T18:40+10:00
created_by: agent B (ZCode) — به‌دستور مالک «FX_SOURCE_DIVERGENCE را پیش از Full-loop با raw RBA artifact حل کن»
paid_calls: 0 · probe_rerun: 0 (ممنوع به‌دستور مالک)
---

# حلِ FX_SOURCE_DIVERGENCE — 2026-08-20 (با artifact خام)

## اندازه‌گیری (fetch تازه از هر دو منبع)

| منبع | تاریخ | نرخ AUD/USD | artifact |
|---|---|---|---|
| CSV رسمی F11.1 (canonical — FXRUSD) | 20-Aug-2026 | **0.7116** | raw_sha256 `40237d01…b3402` · parser verdict PASS |
| صفحهٔ HTML overview | 20 Aug 2026 | **0.7101** | sha256 `1e9b2a03…c22` |

- تاریخ‌ها یکسان‌اند؛ **نرخ‌ها واگرا** (Δ=0.0015).
- **تشخیص ریشه:** مقدار HTML (0.7101) دقیقاً برابر نرخ 18-Aug است (سری
  مشاهده‌شده: 17-Aug=0.7114 · 18-Aug=0.7101 · 19-Aug=0.7070) → سلول جدول
  overview برای تازه‌ترین تاریخ، یک روز عقب است (lag روزانه)، نه اختلاف واقعی بازار.

## حکم

```text
FX_SOURCE_DIVERGENCE: RESOLVED
canonical_source      : CSV رسمی F11.1 (FXRUSD) — طبق دستور «منبع canonical فایل جدول رسمی است، نه overview»
pinned_rate           : 0.7116 (FX-PIN-20260820-01 · receipt 5539dd43… · از CSV)
html_rate             : 0.7101 (مشکوک به lag یک‌روزه — 18-Aug)
resolution            : پین از CSV دست‌نخورده؛ HTML فقط ثبت شد
probe_rerun           : 0 (دستور مالک)
action_taken          : هیچ — پین موجود صحیح است؛ divergence مستند شد
```

## درس

قاعدهٔ `FX_SOURCE_CONFLICT → BLOCK` دقیقاً برای همین طراحی شده بود: در لحظهٔ
انتشار، چکرِ تاریخ‌محور من قبلاً با تفاوت فرمت (خط‌فاصله) فریب خورد و بعد با
نرمال‌سازی، فقط تاریخ را سنجید. **درس: مقایسهٔ منبع‌ها باید نرخ را هم بسنجد،
نه فقط تاریخ را** — این مورد به‌عنوان اصلاح پیشنهادی در backlog ثبت می‌شود
(منجمد تا حلقهٔ بسته — §۱ مگادستور #۱۳؛ اعمال بعداً).

## مربوط

- پین: `_ops/state/cortex/fx-pin-receipts.jsonl` (receipt ‏5539dd43…) ·
  probe receipt: `06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json`
