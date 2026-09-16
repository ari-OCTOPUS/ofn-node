# 🕸️ Graph Report — Cartographer/Memory Pass 2026-07-11

> Scope: `C:\Users\Armin\Desktop\پازل هشت پا`  
> Mode: docs/memory only; no secrets, no external actions.

---

## 1. Counts

| metric | before seed | after review | after this pass |
|---|---:|---:|---:|
| nodes | 13 | 23 | 74 |
| edges | 17 | 34 | 89 |
| dangling edges | 0 | 0 | 0 expected |
| orphan Project/Brain nodes | 0 after review | 0 | 0 expected |

---

## 2. What was added

### Per-entity memory kits created

Created missing `RUNBOOK.md`, `REGISTRY.md`, `VERDICT_QUEUE.md` for:

- Lead-نقاشی
- Ziman Galerry
- Mining
- Crypto - etoro
- Project-F
- app / NBB-CP
- 4d_system
- نقشه اختاپوس

Accounting already had these files.

### Agent memories created

New agent memory files:

- `risk-governor.md`
- `accounting-steward.md`
- `revenue-steward.md`
- `privacy-steward.md`
- `sensing-sentinel.md`
- `brain-integrator.md`
- `handoff-writer.md`

Existing:

- `orchestrator.md`
- `cartographer.md`

### Protocols

- `_memory/protocols/GRAPH-SEARCH-PROTOCOL.md`
- `_memory/graph/SCHEMA.md` updated with `Agent` node type and recency/conflict rule.

---

## 3. Entity coverage table

| Entity | README | PROJECT | MANIFEST | Adapter | RUNBOOK | REGISTRY | VERDICT_QUEUE | DecisionLog | OpenQuestions | Data/docs |
|---|---|---|---|---|---|---|---|---|---|---|
| Accounting | yes | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| Lead-نقاشی | yes | yes | yes | yes | created | created | created | yes | yes | yes |
| Ziman | yes | yes | yes | yes | created | created | created | yes | yes | yes |
| Mining | yes | yes | yes | yes | created | created | created | yes | yes | yes |
| Crypto-eToro | yes | yes | yes | yes | created | created | created | yes | yes | yes |
| Project-F | yes | yes | json manifest | embedded | created | created | created | yes | yes | yes |
| NBB-CP | yes | no/standalone | yes | n/a | created | created | created | n/a | n/a | docs/tests |
| 4D | yes | PROJECT_STATE | yes | n/a | created | created | created | n/a | n/a | code/data |
| VaultScanner | GUIDE | n/a | yes | n/a | created | created | created | n/a | n/a | report/json |

---

## 4. High-risk graph edges

| Edge | Risk | Rule |
|---|---|---|
| ProjectF → Accounting | high privacy | `FEEDS_SAFE_ALIAS` only |
| CryptoEtoro → Accounting | critical finance | alert/draft only |
| Mining → Accounting | medium/high wallet risk | inform-only, no wallet |
| NBB_CP → ArchitectOps | critical governance | `ROLE_OPEN`, needs verdict |
| FourD → ArchitectOps | high self-code | owner-approved run only |
| Accounting data | high PII | local only, no LLM |
| Crypto data | critical | alert-only, no execution |

---

## 5. Drift notes

- Several MANIFEST files still say `security_gate: closed`; workspace context says `Security Gate = LIFTED 2026-07-06`. This is historical drift. Do not rewrite all history blindly; fix only in active runbooks/registries or via explicit sync pass.
- `VaultScanner` report currently references larger `F:\backup`, not this workspace. Needs retarget verdict before trusting report.
- `NBB-CP` is built and hardened but not declared boss; role remains open.
- `4d_system` contains `.env`; do not read or copy secrets. Its runbook says owner-approved run only.

---

## 6. Recommended build order

1. Accounting — only after owner answers ACC-V1..V6.
2. Lead-نقاشی — decide experiment #1 and portfolio permission.
3. Ziman — capacity + hero product.
4. Project-F — GATE 0 content-free.
5. Mining/Crypto — registries only, no execution.
6. NBB/4D/VaultScanner — role/run/scan verdicts.

---

## 7. Integrity status

Manual schema pass:

```text
node vocabulary: pass (Project/Brain/Tool/Agent/Document/Manifest/Adapter/Runbook/Decision/Question/DataFolder)
edge vocabulary: pass (BOSS_OF, REPORTS_TO, GATED_BY, REQUIRES_VERDICT, ROLE_OPEN, FEEDS, FEEDS_SAFE_ALIAS, INFORMS, ALERTS, OWNS, CONTAINS, DEPENDS_ON, SUPPORTS)
Project-F containment: pass in root graph summaries
external actions: none performed
```

Remaining validation for a future script:

- parse JSONL programmatically
- path-existence check for all 74 nodes
- duplicate-id check
