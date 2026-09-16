---
type: ops-policy
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, routing, model, budget]
aliases: [Route Policy, مسیریابی مدل]
---

# ROUTE-POLICY — مسیریابی مدل و سقف هزینه

> تاریخ: ۲۰۲۶-۰۸-۱۱ · مرجع: `_ops/cortex/model_router.py:116-128`

## سه لایهٔ مدل

| لایه | مدل | نقش | هزینه | چه کارهایی |
|---|---|---|---|---|
| **local** | ollama qwen2.5:1.5b | `econ` | $0 | classify, daily, think, triage, summarize, tg_intent, chord.extract, heart_setpoint, **collab_chat** |
| **secondary** | deepseek-v4-flash (reason) | `reason` | subscription/metered | research, synthesize, draft, debate_muse |
| **primary** | Fugu (orchestr) | `orchestr` | subscription/metered | orchestrate, deep, plan, governor, debate_architect |

> unmapped tasks → `local` (via `TASK_TIERS.get(task, "local")`)

## مسیر تصمیم

```text
ask(task, prompt)
  → kill-switch check (STOP_ORGANISM)
  → context_fence screen (if armed)
  → tier resolution:
      explicit tier= param  >  CORTEX_ROUTE_SCORER (if armed)  >  TASK_TIERS static map
  → if secondary + CORTEX_LOCAL_FIRST:
      try local first → quality gate → pass? return local : continue
  → if secondary/primary:
      key-aware order: [wanted] + [other paid tier with key]
      per-tier: _ask_paid → organ_gate → fugu_quota → MultiProviderClient
      circuit_breaker: OPEN → skip (fail-fast, no network)
      paid_gate closed → fallback
      all paid fail → local fallback (with fallback_from reason)
  → else: local_llm.ask directly
```

## سقف‌ها (from budgets.yaml + env)

| گیت | مقدار | منبع |
|---|---|---|
| daily call cap (Fugu) | 300 پیش‌فرض | `FUGU_DAILY_CALL_CAP` env |
| fail ceiling | 10 | `FUGU_FAIL_CEILING` env |
| breaker threshold | 5 failures | `circuit_breaker.py` |
| breaker cooldown | 60s | `circuit_breaker.py` |
| ask budget | 90s wall | `PAID_ASK_BUDGET_S` env |
| HTTP timeout | derived from max_tokens | `client._http_timeout()` |
| monthly spend | AU$30 (or US$200 window until 2026-08-13) | `budget_gate.spend_cap_now()` |
| collab soft call cap | 30/day default (suggest 20 on first arm) | `OCTOPUS_COLLAB_MODEL_DAILY_CAP` + `collab_model_adapter` counter |

## فلگ‌های مسیریابی

| فلگ | پیش‌فرض | تأثیر |
|---|---|---|
| `CORTEX_LOCAL_FIRST` | OFF | secondary از local شروع می‌کند، با quality gate |
| `CORTEX_ROUTE_SCORER` | OFF | route_scorer مشورت می‌شود برای tier (fail-soft) |
| `OCTOPUS_WIRE_ROUTE_SHADOW` | OFF | shadow log از تصمیمات routing |

## خواندن هزینهٔ روز

```bash
python _ops/scripts/daily-cost.py
```

خروجی: `cost_usd` امروز + per-tier counts + STOP-FUGU status + budget state.
