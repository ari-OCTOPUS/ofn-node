# Prompt for Next Agent — Cartographer v2 (review-hardened)

> Supersedes `NEXT-AGENT-PROMPT.md`. Fixes the self-blocking Step 4 and adds a
> mandatory graph-integrity gate. Workspace:
>
> ```text
> C:\Users\Armin\Desktop\پازل هشت پا
> ```

## Mission

Grow the memory graph from seed → full verified inventory, then advance projects —
without ever stalling on owner input and without breaking graph integrity.

## Read first (in this order)

```text
ARCHITECT-ORGANISM-CONTEXT.md
MULTI-AGENT-MEMORY-GRAPH-DESIGN.md
_memory/graph/SCHEMA.md          <-- NEW: closed vocabulary + integrity rules
_memory/graph/REVIEW-2026-07-11.md  <-- NEW: known defects
_memory/graph/nodes.jsonl
_memory/graph/edges.jsonl
REGISTRY-ALIGNMENT.md
RISK-LADDER.md
VERDICT_QUEUE.md
```

## Graph search protocol (run before writing anything)

```text
1. Load target node from nodes.jsonl by id.
2. neighborhood(target, depth=2) from edges.jsonl (both directions).
3. gates = edges where type=GATED_BY and (from=target or to=target).
4. verdicts = edges where type=REQUIRES_VERDICT touching target.
5. Load the real files at each node.path.
6. Act only if the action is not hard-gated; else write a verdict request.
```

## Work — split into UNBLOCKED (do now) and BLOCKED (needs owner)

### TRACK 1 — UNBLOCKED (proceed autonomously)

**Step 1 — Full inventory (read-only).**
List `03 - Projects`, plus `app`, `4d_system`, `نقشه اختاپوس`, `NBB-Project-Scan-2026-07-11`.
For each entity detect: README.md, PROJECT.md, MANIFEST.yaml|json, contracts/adapter.yaml,
RUNBOOK.md, REGISTRY.md, VERDICT_QUEUE.md, DecisionLog.md, OpenQuestions.md, data/, docs/.

**Step 2 — Append graph (append-only, validate against SCHEMA.md).**
Add a node per real file found (Manifest/Adapter/Runbook/Document/DataFolder) and an
`OWNS` edge from its project. Add `DEPENDS_ON`/`FEEDS`/`GATED_BY` where evidenced.
Never invent an edge/node type outside SCHEMA §2/§4.

**Step 3 — Integrity gate (MANDATORY before "done").**
Run SCHEMA §7 checklist. Report counts + any violation. If a violation exists, fix by
appending (supersede), never by deleting.

**Step 4 — Graph report.**
Update `_memory/graph/graph-report.md`: node/edge counts, per-project missing files,
high-risk edges, drift notes, recommended build order.

**Step 5 — Fill missing tenant kits (docs only, low-risk).**
Where a project lacks RUNBOOK/REGISTRY/VERDICT_QUEUE (e.g. Lead-نقاشی), create them from the
Accounting templates, adapted, marked draft. No external actions, no code.

### TRACK 2 — BLOCKED (do NOT wait; just prepare)

These need owner verdicts (see `VERDICT_QUEUE.md`). Do not execute; instead write a
`verdict-request` note listing exactly what each decision unlocks:

- Accounting final tax rules → needs ACC-V1..V6.
- NBB-CP governor wiring → needs VQ-ROOT-001.
- VaultScanner run on workspace → needs VQ-MAP-001.

When (and only when) the owner answers in chat, sync:
`03 - Projects/Accounting/{OpenQuestions,DecisionLog,REGISTRY,RUNBOOK}.md`.

## Memory append (every step)

Append one JSON line to `_memory/execution/runs.jsonl`:

```json
{"ts":"<ISO8601>","agent":"cartographer-v2","event_type":"observation|action|question|handoff","entity":"<id>","summary":"<safe>","evidence_paths":["..."],"risk":"low","requires_verdict":false,"pii_safe":true,"secret_safe":true}
```

## Hard rules

- No secret/API key/seed: never read, write, or request.
- Mask/summarize PII; never send PII to any model.
- Project-F: outside its folder use only alias `Project-F`/`ProjectF`; no platform/identity/content.
- No external action: no publish/send/spend/trade/lodge/pay/create-account/deploy.
- Additive only: never delete a graph line or overwrite history; supersede instead.
- Prefer latest canonical (Brain/HANDOFF) over older docs on conflict.

## Final answer to owner must state

1. nodes/edges before → after, and integrity result (pass/violations).
2. per-project missing files table.
3. what TRACK 1 completed.
4. exact TRACK 2 verdicts still needed and what each unlocks.
5. single recommended next action.
