---
type: reference
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, octopus, integration, control-plane]
created: 2026-07-13
updated: 2026-07-13
---

# 05 · Octopus Integration Readiness

> «Octopus» = مغز مرکزی / control-plane آری (MYCELIAL / Architect System). Accounting یک **node** زیر آن است. خبر خوب: درزِ اتصال **از قبل وجود دارد** — این نوت فقط آن را صریح می‌کند.

## درزِ اصلی: `contracts/adapter.yaml`
رابط **read-only** که Accounting را به مغز مرکزی وصل می‌کند:

| interface | method | برمی‌گرداند |
|---|---|---|
| `status` | read | `{gate_open, register_complete_pct, ledger_active, bas_next_due}` |
| `report` | read(period) | `{income_by_source, expenses_by_category, gst_payable, bas_draft}` |
| `compliance_scan` | read | `list[flag:{type, amount, entity_hash, severity}]` |
| `audit` | read | `list[decision]` |

`autonomous_allowed: []` — فعلاً هیچ اکشن خودکار. `hard_gated_actions`: lodge، پرداخت، تغییر قاعدهٔ مالیاتی، write بدون verdict، ارسال PII.

## نقاط اتصال بالادست (tax touchpoints)
هر پروژهٔ دیگر هنگام درآمد، **یک خط append** به دفتر Accounting می‌زند (Lead/Mining/Crypto/Project-F/Ziman) — نگاشت کامل در [[02-Data-Flow]] و `adapter.yaml#upstream_tax_touchpoints`.

## چک‌لیست آمادگی (چه چیزی برای اتصال امن لازم است)
| بُعد | وضعیت | یادداشت |
|---|---|---|
| مرزِ اکشن (action boundary) | ✅ | `adapter.yaml` فقط read؛ forbidden صریح |
| kill-switch | ✅ | MANIFEST: gate closed → همه read-only؛ lodge/pay = تابع وجود ندارد |
| بارگذاری config متمرکز | 🟡 | `importer/config.js` هست؛ env بات جدا (`.env` خارج repo) |
| منبع حقیقت state | ✅ | `PROJECT.md#Active-Context` + `MANIFEST.status_snapshot` |
| مرزِ PII | ✅ قاعده / 🟡 اجرا | قاعده روشن؛ tokenization هنوز کد نشده |
| audit trail | 🟡 | `DecisionLog`/`VERDICT_QUEUE` دستی؛ append-only خودکار = طراحی‌شده |
| logging hook یکنواخت | ⚪ | `_events/*.jsonl` برای finance هست؛ سراسری نه هنوز |
| budget cap | ✅ | MANIFEST: Claude API ماهانه AU$۵–۱۵، زیر سقف Cowork |

## کمترین کاری که Octopus-readiness را کامل می‌کند
۱ یک **tokenizer PII** قبل از هر inference (تنها شکاف اجراییِ قاعدهٔ ۴).
۲ استانداردسازی logging → همه‌جا `_events/*.jsonl` append-only.
۳ پیاده‌سازی خواندنِ `adapter.yaml` توسط مغز مرکزی (contract الان فایل است، هنوز endpoint نیست).

> هیچ integration جعلی نساختم. سطحِ اتصال **حداقلی و صریح** است؛ وقتی مغز مرکزی خواست، فقط `adapter.yaml` را می‌خواند — بدون تغییر در core.
