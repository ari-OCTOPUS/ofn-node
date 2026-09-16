---
type: experiment
experiment_id: ZM-EXP-001
project: ZIMAN
status: planned
risk: yellow
updated: 2026-07-12
---

# EXP-001 — Warm network first sale (batch ≤10)

```yaml
hypothesis: "Warm contacts convert faster than cold IG posts for C3 shadow boxes."
strategy_family: warm_network
product_ids: []   # fill after SKU cards
audience: acquaintances / Sydney Iranian warm list
channel: private_DM_human_only
inventory_batch: 10
duration: 7d
budget_cap_aud: 0
primary_metric: paid_orders
secondary: [qualified_inquiry, reply_rate]
success_threshold: ">=1 paid order OR >=3 qualified inquiries"
failure_threshold: "0 replies after 15 human-sent DMs"
stop_conditions: ["capacity breach", "owner halt", "brand claim violation"]
execution_mode: human-executed
external_action: true   # human sends
approval_required: true
rollback: "stop DMs; no public posts; inventory unchanged"
```

# EXP-002 — Occasion content (no paid ads)

```yaml
hypothesis: "Occasion-led captions (birthday/housewarming) lift inquiry quality vs generic posts."
strategy_family: occasion_led_content
channel: Instagram_organic_drafts_only
inventory_batch: 5
duration: 14d
budget_cap_aud: 0
primary_metric: qualified_inquiry
guardrails: [no_fresh_flower_claim, D4, human_publish_only]
execution_mode: human-executed
approval_required: true
```

# EXP-003 — Hero C3 positioning

```yaml
hypothesis: "C3 framed shadow box as hero increases willingness-to-inquire vs mixed catalog posts."
strategy_family: hero_product_positioning
product_family: C3
channel: content_review_then_human_post
inventory_batch: 5
duration: 14d
primary_metric: inquiry_to_C3
success_threshold: ">=2 C3-specific inquiries"
failure_threshold: "engagement without inquiry after 6 posts"
execution_mode: human-executed
approval_required: true
```

## Rules
- One main hypothesis per experiment
- Prefer paid order + margin over vanity metrics
- Failures stored; only verified outcomes → procedural memory
