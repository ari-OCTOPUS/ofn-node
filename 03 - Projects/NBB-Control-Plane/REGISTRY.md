# 🧠 NBB-CP REGISTRY

```yaml
entity_id: NBB_CP
name: NBB Control Plane
kind: brain
owner: Ari
status: role-open
risk_level: critical
risk_tier: R4-pending
autonomy_floor: shadow/control-plane only
role_in_ecosystem: PORTABLE_CONTROL_PLANE_CANDIDATE
control_contract: MANIFEST.yaml
adapter: none
runbook: RUNBOOK.md
public_alias: NBB-CP
boss_alignment: undecided vs Architect/_ops
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| scan/audit | read-only | allowed |
| tenant governance | shadow | needs verdict |
| API | optional | no live wiring |
| registry bridge | proposed | needs design |

---

## Current registry verdict

```text
NBB-CP is powerful and tested, but must not be treated as the boss until owner decides its relationship to Architect/_ops.
```
