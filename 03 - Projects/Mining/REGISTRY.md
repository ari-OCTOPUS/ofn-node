# ⛏️ Mining REGISTRY

```yaml
entity_id: Mining
name: Mining
kind: tenant
owner: Ari
status: active
risk_level: medium
risk_tier: R2
 autonomy_floor: INFORM-only
role_in_ecosystem: RESEARCH_SENSING_LEG
control_contract: MANIFEST.yaml
adapter: contracts/adapter.yaml
runbook: RUNBOOK.md
public_alias: Mining
wallet_policy: zero agent access
boss_alignment: Architect/_ops compatible
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| coin_scouting | report-only | designed |
| hardware_registry | draft | open |
| fleet_manager | no execution | code elsewhere |
| accounting_touchpoint | draft | mined coin event only |

---

## Hard-gated actions

- wallet/seed/private key access
- mining start/stop
- SSH/deploy
- buy/sell/withdraw
- electricity spend

---

## Current registry verdict

```text
Mining can research and report; it cannot operate rigs or wallets until hardware/electricity/wallet decisions are explicit.
```
