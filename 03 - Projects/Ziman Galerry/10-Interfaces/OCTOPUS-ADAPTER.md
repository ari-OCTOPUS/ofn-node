---
type: interface
project: ZIMAN
status: active
updated: 2026-07-12
---

# OCTOPUS-ADAPTER — Ziman limb

## Identity
```yaml
limb_id: ziman
leg_id: ziman-gallery
organ: ZIMAN
parent: OCTOPUS
authority: Architect/_ops
nbb_cp: shadow-only
```

## Code surfaces
| Surface | Path | Role |
|---|---|---|
| Leg | `_ops/legs/ziman_leg.py` | OCTOPUS limb worker |
| Wiring | `_ops/wiring.make_ziman_leg` | flag `OCTOPUS_WIRE_ZIMAN` |
| Local agent | `03 - Projects/Ziman Galerry/ziman-agent/` | content drafts |
| Control brain | `03 - Projects/Ziman Galerry/control-brain/` | start/stop/RBAC |
| Manifest | `03 - Projects/Ziman Galerry/MANIFEST.yaml` | machine contract |
| Adapter (legacy) | `contracts/adapter.yaml` | read-only interface |
| Telegram | `_ops/telegram_center` key `ziman` | gateway only |
| Budget | `_ops/budget/budgets.yaml` → ZIMAN | floor AU$1 |

## Allowed autonomously
- read vault allowlist
- analyse
- draft content (local files / proposals)
- campaign_check (D4)
- memory **candidates** (provisional)
- status / digest for Telegram

## Hard-gated (human)
- publish, send, DM
- spend / pay / refund
- public price / discount
- delivery promise
- deploy / live automation
- promote prompt to active
- canonical memory write

## Heart connection
- Heart paces organism; ZimanLeg.tick() is propose-only work unit
- No rate authorship by limb (ADR-001)
- Fail-closed on STOP / FREEZE / D4

## Telegram topics (proposed)
```
10 🌸 Ziman Executive
11 📦 Products & Inventory
12 🔎 Market Research
13 📊 Experiments
14 🚚 Operations
15 🧠 Memory & Learning
16 🎨 Content Review
17 🚨 Incidents
18 📚 Reports
```

## Commands (proposed)
`/ziman_status` `/ziman_inventory` `/ziman_products` `/ziman_experiments`
`/ziman_content` `/ziman_memory` `/ziman_decisions` `/halt_ziman`
+/approve /reject /defer /rollback (global)

## Safety
- Telegram = gateway, not source of truth
- No secrets/PII in proposals or Telegram digests
- Kill: STOP-ORGANISM, control-brain halt, D4
