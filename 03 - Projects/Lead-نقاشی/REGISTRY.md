# 🎨 Lead-نقاشی REGISTRY

```yaml
entity_id: LeadPainting
name: Lead-نقاشی
kind: tenant
owner: Ari
status: active
risk_level: medium
risk_tier: R2
autonomy_floor: propose-only
role_in_ecosystem: PRIMARY_REVENUE_LEG
control_contract: MANIFEST.yaml
adapter: contracts/adapter.yaml
runbook: RUNBOOK.md
public_alias: Lead-Painting
pii_policy: customer PII hash-ref only
boss_alignment: Architect/_ops compatible
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| portfolio_inventory | read/draft | raw photos present |
| experiment_design | draft | ready |
| outreach_copy | draft-only | gated |
| lead_intake | human-gated | not active |
| accounting_touchpoint | draft | via Accounting |

---

## Hard-gated actions

- send/publish/call
- paid ads/spend
- final quote
- customer PII storage
- license/insurance claims
- public use of portfolio photos

---

## Current registry verdict

```text
Lead-Painting is the main revenue leg but remains propose-only until channel, segment, capacity, and portfolio permissions are decided.
```
