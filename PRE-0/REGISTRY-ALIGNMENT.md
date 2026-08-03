# 🧭 Registry Alignment — اتصال پروژه‌ها به جهان‌بینی Architect/_ops

> هدف: تبدیل هر پروژه به entity قابل‌دیدن برای رئیس اختاپوس / registry / risk ladder.  
> این فایل secret-free و PII-free است.

---

## Entity schema پیشنهادی

هر entity باید این فیلدهای حداقلی را داشته باشد:

```yaml
entity_id: string
name: string
kind: tenant | brain | tool
owner: owner-code
risk_level: low | medium | high | critical
risk_tier: R1 | R2 | R3 | R4-pending | R4
autonomy_floor: read-only | propose-only | alert-only | inform-only | shadow-only
status: active | paused | planned | archived
control_contract: path
adapter: path | none
primary_gate: string
hard_gated_actions: list
public_alias: string
pii_policy: string
boss_alignment: Architect/_ops compatible
```

---

## Registry table

| entity_id | kind | risk | risk_tier | autonomy_floor | contract | adapter | primary blocker |
|---|---|---:|---|---|---|---|---|
| Accounting | tenant | high | R3 | read-only/draft-only | `03 - Projects/Accounting/MANIFEST.yaml` | `contracts/adapter.yaml` | accountant + structure |
| Lead-Painting | tenant | medium | R2 | propose-only | `03 - Projects/Lead-نقاشی/MANIFEST.yaml` | `contracts/adapter.yaml` | experiment #1 + channel |
| Mining | tenant | medium | R2 | INFORM-only | `03 - Projects/Mining/MANIFEST.yaml` | `contracts/adapter.yaml` | hardware registry |
| Crypto-eToro | tenant | critical | R4-pending | alert-only | `03 - Projects/Crypto - etoro/MANIFEST.yaml` | `contracts/adapter.yaml` | portfolio registry + bug |
| Ziman | tenant | low | R1 | propose-only | `03 - Projects/Ziman Galerry/MANIFEST.yaml` | `contracts/adapter.yaml` | capacity + product photos |
| Project-F | tenant | high | R3/R4-contained | contained propose-only | `PROJECT-F-CONTROL-MANIFEST.json` | embedded | GATE 0 |
| NBB-CP | brain | critical | R4-pending | shadow/control-plane | `app/MANIFEST.yaml` | none | role vs Architect/_ops |
| 4D | brain | high | R3 | owner-approved run | `4d_system/MANIFEST.yaml` | none | run decision + sandbox risk |
| VaultScanner | tool | low | R1 | read-only | `نقشه اختاپوس/MANIFEST.yaml` | none | retarget scan |

---

## Drift notes

- Older docs mark Security Gate closed; newer owner-provided Brain/HANDOFF mark it LIFTED on 2026-07-06.
- `app/NBB-CP` should not be assumed to replace `Architect/_ops`; decide role first.
- `Project-F` uses golden manifest; do not expand identity/content outside its folder.
- Some code referenced as `_code/` is absent from current distilled workspace; locate only if mounted.

---

## Next alignment actions

1. Add/update per-project `REGISTRY.md` for tenant entities.
2. Add per-project `RUNBOOK.md` with allowed commands and hard-gates.
3. Add per-project `VERDICT_QUEUE.md` or link to root queue.
4. Sync stale docs that still say Security Gate closed, without rewriting historical context.
5. Produce a fresh scanner report for current workspace if owner confirms.
