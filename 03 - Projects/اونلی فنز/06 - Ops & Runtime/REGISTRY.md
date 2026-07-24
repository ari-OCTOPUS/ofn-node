# 🔒 Project-F REGISTRY

```yaml
entity_id: ProjectF
name: Project-F
kind: tenant
owner: Ari
status: active-contained
risk_level: high
risk_tier: R3/R4-contained
autonomy_floor: contained propose-only
role_in_ecosystem: PRIVACY_CONTAINED_VALIDATION_LEG
control_contract: PROJECT-F-CONTROL-MANIFEST.json
adapter: embedded/local
runbook: RUNBOOK.md
public_alias: Project-F
pii_policy: no cross-domain identity/content/platform echo
boss_alignment: Architect/_ops compatible with containment
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| local_status | content-free | allowed |
| research | contained | allowed |
| drafts | contained | gated |
| accounting_touchpoint | alias-only | gated |

---

## Hard-gated actions

- publish/send/spend
- content/media processing outside containment
- identity/platform echo
- any action before GATE 0

---

## Current registry verdict

```text
Project-F is graph-visible only through a privacy-safe alias and status-only metadata.
```
