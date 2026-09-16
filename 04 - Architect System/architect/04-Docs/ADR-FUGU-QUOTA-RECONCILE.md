# ADR: Reconcile Fugu Quota Systems

> **Status:** Accepted · **Date:** 2026-08-08 · **Depends on:** WP1 (fugu_proxy), WP3 (db.py)

## Context

دو سیستم سهمیهٔ Fugu به‌طور موازی وجود دارند:

1. **`fugu_quota.py`** (در `cortex/`) — سهمیهٔ **attempt-based**: cap=300/day،
   attempt-counted (قبل از تماس +۱)، STOP-FUGU auto-trip (۸ شکست پیاپی).
   مدخل: `model_router._ask_paid()` → `fugu_quota.reserve()` قبل از هر call.

2. **`provider_usage`** (در `owner_cockpit/db.py`) — سهمیهٔ **token/cost-based**:
   هر call با input/output/cached/orchestration tokens + cost_usd ثبت می‌شود.
   مدخل: `fugu_proxy.py` → `log_provider_usage()` بعد از هر response.

## Decision

این دو سیستم **متضاد نیستند** — نقش‌های مکمل دارند:

| سیستم | نقش | تصمیم‌گیری | زمان |
|---|---|---|---|
| `fugu_quota` | **Circuit breaker** (ضدِ loop) | deny/allow قبل از تماس | قبل از call |
| `provider_usage` | **Financial tracking** (داشبورد) | فقط ثبت، بدون deny | بعد از response |

**قاعده:** `fugu_quota` تصمیم می‌گیرد (gate). `provider_usage` ثبت می‌کند (ledger).
هیچ‌کدام دیگری را override نمی‌کند. اگر `fugu_quota` deny کند، call نمی‌شود و
`provider_usage` چیزی برای ثبت ندارد.

## Future: budget enforcement از provider_usage

فعلاً `provider_usage` فقط ثبت می‌کند (observability). در آینده می‌تواند یک
budget gate اضافه شود (مثلاً `daily_cost_cap_usd`) که قبل از call چک می‌کند —
اما این **پشت فلگ جدا** خواهد بود و `fugu_quota` را جایگزین نمی‌کند.

## Consequences

- مثبت: دو لایه حفاظتی مستقل (loop protection + cost tracking)
- مثبت: داشبورد می‌تواند cost واقعی نشان دهد بدون اینکه gate را دور بزند
- منفی: دو نقطهٔ config (cap=300/day در fugu_quota + pricing در fugu_pricing.json)
- ریسک: اگر کسی `fugu_quota` را خاموش کند، فقط loop protection از دست می‌رود،
  نه cost tracking
