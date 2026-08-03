# 🧩 Graph Schema — canonical closed vocabulary + integrity rules

> Created by the review/critic agent on 2026-07-11.  
> Reason: the design doc (`MULTI-AGENT-MEMORY-GRAPH-DESIGN.md` §3.2) declared one edge
> vocabulary, but `edges.jsonl` uses a different one. This file is the **single source
> of truth** that reconciles both. All future graph writes MUST validate against this.

---

## 1. Why this file exists (drift found)

Verified drift between spec and implementation:

| Declared in design §3.2 | Actually used in edges.jsonl | Status |
|---|---|---|
| FEEDS | FEEDS | ✅ match |
| GATED_BY | GATED_BY | ✅ match |
| REQUIRES_VERDICT | REQUIRES_VERDICT | ✅ match |
| SUPPORTS | SUPPORTS | ✅ match |
| REPORTS_TO | — (used BOSS_OF instead, reversed) | ⚠️ drift |
| — | BOSS_OF | ⚠️ undeclared |
| — | INFORMS | ⚠️ undeclared |
| — | ALERTS | ⚠️ undeclared |
| — | FEEDS_SAFE_ALIAS | ⚠️ undeclared |
| — | ROLE_OPEN | ⚠️ undeclared |

Resolution: **adopt the richer real vocabulary** (it is more expressive) and freeze it here.
Do not silently invent new types again; extend this file with a verdict/log entry.

---

## 2. Node types (closed set)

```yaml
Project        # a tenant leg (revenue/validation/sensing)
Brain          # governance/cognition (Architect/_ops, NBB-CP, 4D)
Tool           # utility (VaultScanner)
Agent          # an operational role with memory and graph-search duties
Document       # policy/registry/ladder/queue markdown
Manifest       # MANIFEST.yaml/json contract
Adapter        # contracts/adapter.yaml
Runbook        # RUNBOOK.md
Decision       # a logged decision
Question       # an open question / verdict item
Risk           # risk classification node
Gate           # a hard-gate / control point
DataFolder     # data/ receipts/ photos/ portfolio
ExternalAction # publish/send/spend/trade/lodge/pay/create-account (always gated)
```

## 3. Node record shape

```json
{"id":"UniqueId","type":"<node type>","name":"human name","risk":"low|medium|high|critical","status":"string","path":"relative/path"}
```

Rules:
- `id` unique, ASCII, stable (never rename; supersede instead).
- `path` must be a real relative path in the workspace.
- `risk` required for Project/Brain/Tool nodes.

## 4. Edge types (closed set — reconciled)

```yaml
# governance
BOSS_OF            # A governs B (Architect/_ops -> tenant)
REPORTS_TO         # B reports up to A (inverse view of BOSS_OF; pick ONE per pair)
GATED_BY           # A is constrained by control doc B
REQUIRES_VERDICT   # A needs human decision tracked in B
ROLE_OPEN          # relationship exists but role undecided (needs verdict)

# data / value flow
FEEDS              # A sends income/data to B
FEEDS_SAFE_ALIAS   # like FEEDS but privacy-contained (Project-F only)
INFORMS            # A informs B (no execution authority)
ALERTS             # A raises alert-only signal to B

# structure
OWNS               # A owns child B
CONTAINS           # A contains file/folder B
DEPENDS_ON         # A needs B to function
BLOCKED_BY         # A blocked until B resolved
SUPPORTS           # A assists B
SUPERSEDES         # A replaces B
MENTIONS           # weak reference

# safety flags (as edges to marker nodes, optional)
CONTAINS_PII
CONTAINS_SECRET_POINTER
```

Direction rule: default governance direction is **BOSS_OF** (top→down). `REPORTS_TO` is allowed as a deliberate reverse traversal edge when graph search needs tenant→boss context; if both exist for the same pair, they must not contradict each other and should be treated as inverse navigation, not a separate policy.

## 5. Edge record shape

```json
{"from":"NodeId","to":"NodeId","type":"<edge type>","summary":"short safe reason"}
```

## 6. Integrity rules (must pass before "done")

1. **No dangling edge**: every `from`/`to` must exist in `nodes.jsonl`.
2. **No orphan critical node**: every Project/Brain node must have ≥1 edge.
3. **Closed vocabulary**: every edge `type` ∈ §4; every node `type` ∈ §2.
4. **Unique ids**: no duplicate node `id`.
5. **Path truth**: every node `path` resolves to a real file/folder.
6. **Containment**: any edge touching `ProjectF` uses only alias; no platform/identity in `summary`.
7. **Append-only**: never delete a line; supersede with a new line + `SUPERSEDES` edge.
8. **Recency/conflict**: every new memory/action event needs `ts`; when documents conflict, latest canonical decision wins and older material remains historical.

## 7. Validation checklist (manual, no runtime)

```text
[ ] count nodes, count edges
[ ] list all edge.type not in §4      -> must be empty
[ ] list all node.type not in §2      -> must be empty
[ ] for each edge: from in nodes? to in nodes?
[ ] for each Project/Brain node: has >=1 edge?
[ ] any duplicate id?
[ ] any ProjectF edge leaking identity? 
```
