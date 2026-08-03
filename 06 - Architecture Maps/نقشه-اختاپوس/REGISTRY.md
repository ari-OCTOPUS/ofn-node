# 🗺️ VaultScanner REGISTRY

```yaml
entity_id: VaultScanner
name: نقشه اختاپوس
kind: tool
owner: Ari
status: active
risk_level: low
risk_tier: R1
autonomy_floor: read-only
role_in_ecosystem: CARTOGRAPHER_TOOL
control_contract: MANIFEST.yaml
adapter: none
runbook: RUNBOOK.md
public_alias: VaultScanner
boss_alignment: supports RegistryAlignment
```

---

## Interfaces

| interface | mode | status |
|---|---|---|
| scan | read-only | available |
| report | write tool output | needs target verdict |
| inventory json | write tool output | needs target verdict |

---

## Current registry verdict

```text
VaultScanner may support graph enrichment, but retargeting scan to this workspace needs owner yes.
```
