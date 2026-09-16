# 📈 Crypto-eToro REGISTRY

```yaml
entity_id: CryptoEtoro
name: Crypto-eToro
kind: tenant
owner: Ari
status: active
risk_level: critical
risk_tier: R4-pending
autonomy_floor: alert-only
role_in_ecosystem: SENSING_INVESTMENT_LEG
control_contract: MANIFEST.yaml
adapter: contracts/adapter.yaml
runbook: RUNBOOK.md
public_alias: Crypto-eToro
key_policy: off-box, zero agent access
boss_alignment: Architect/_ops compatible
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| portfolio_registry | owner-filled | open |
| exit_rules | draft/owner | open |
| alerts | alert-only | designed |
| data_scraper | disabled | stale data archived |
| accounting_touchpoint | draft | CGT/personal note |

---

## Hard-gated actions

- BUY
- SELL
- exchange API/key access
- withdraw/deposit
- auto execution

---

## Current registry verdict

```text
Crypto-eToro is visible to graph as sensing/alert-only. No execution is allowed.
```
