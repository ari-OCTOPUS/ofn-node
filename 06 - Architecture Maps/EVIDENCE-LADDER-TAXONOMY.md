---
type: knowledge
kind: reference
status: active
created: 2026-08-10
updated: 2026-08-10
tags: [evidence-ladder, capability-status, audit, taxonomy, remediation]
---

# Evidence Ladder — تاکسونومی وضعیت قابلیت

> **منبع:** Fugu Ultra Audit Remediation (WP-A). این سند یک مرجع (reference) است؛
> هیچ کد runtime، flag یا decision را تغییر نمی‌دهد.

## هدف

برای جلوگیری از تکرار اشتباهِ «source-default = live» و «wired = effective»،
هر claim درباره یک قابلیت باید روی یکی از این پله‌ها قرار بگیرد. هیچ پله‌ای
نباید از پلهٔ پایین‌تر **استنتاج** شود — برای هر ارتقا evidence مستقل لازم است.

## هفت پله

```text
1. implemented     — کد موجود است؛ module/function تعریف شده.
2. configured      — flag/env در config یا flags.cmd صراحتاً مقدار دارد.
3. armed           — flag در runtime با مقدار فعال loaded شده (flags-loaded-*.json).
4. executed        — کد اخیراً اجرا شده (trace، journal، receipt، یا artifact با timestamp تازه).
5. consumed        — خروجی واقعاً توسط یک reader/downstream خوانده شده.
6. decision-changing — ورودیِ یک تصمیم/اقدام شده (نه فقط display/context).
7. outcome-improving — اندازه‌گیریِ کنترل‌شده نشان داده که quality/cost/error بهتر شده.
```

## قواعد طبقه‌بندی

- `implemented` ≠ `armed` — وجود کد فقط پلهٔ ۱ است.
- `armed` ≠ `executed` — flag روشن اجرا را ثابت نمی‌کند.
- `executed` ≠ `consumed` — artifact تازه بودن reader ندارد.
- `consumed` ≠ `decision-changing` — prompt-context با action تفاوت دارد.
- `decision-changing` ≠ `outcome-improving` — تغییر تصمیم لزوماً بهتر نیست.
- `missing evidence` ⇒ `UNKNOWN`، نه `false` و نه `healthy`.

## ترجمهٔ وضعیت‌های تاکسونومیک قبلی

| وضعیت قدیمی | معنای دقیق روی نردبان |
|---|---|
| `wired` | بسته به evidence: `implemented` + گاهی `armed` + گاهی `consumed` |
| `display-only` | `consumed` برای نمایش انسانی، نه `decision-changing` |
| `dead-output` | `executed` (artifact تولید شده) ولی نه `consumed` |
| `shadow` | `executed` ولی عمدتاً `not decision-changing` (observation-only) |
| `spec` | نه `implemented` |

## مثال‌های تأییدشدهٔ ممیزی (2026-08-10)

| مسیر | implemented | configured | armed | executed | consumed | decision-changing | outcome-improving |
|---|---|---|---|---|---|---|---|
| `semantic_memory` → `cortex.think()` | ✅ | ✅ | ✅ (`"1"`) | ✅ | ✅ (prompt) | UNKNOWN | UNKNOWN |
| `bcm.learned_pressure` → `protective_override` | ✅ | ✅ | ✅ | ✅ (historical `applied=true`) | ✅ (score) | UNKNOWN | UNKNOWN |
| `c6` → RFC card | ✅ | ✅ | ✅ | ✅ | ✅ | proposal-wired (human-gated) | UNKNOWN |
| `vault_bridge.rag_evidence` | ✅ | ✅ | ✅ | ✅ | ✅ (context) | UNKNOWN | UNKNOWN |
| `body_bridge` → `_ops` | ✅ | — | — | stale (Jul 14) | NONE FOUND | — | — |
| `4d_system` runtime | ✅ (deprecated) | — | — | standalone | — | — | — |
| D10-ABC benchmark | SPEC only | — | — | — | — | — | — |
