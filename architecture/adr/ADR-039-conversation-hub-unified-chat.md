# ADR-039: Conversation Hub — Unified Chat Architecture

**Status:** Accepted (Phase 1 implemented)
**Date:** 2026-08-12
**Context:** `pasted-text-20260812-233148-154d839d.txt` (original proposal) +
`pasted-text-20260812-233106-7132695a.txt` (GPT-5.6 Terra review)

---

## Problem

The Octopus Mini App has **four parallel chat paths** with heterogeneous response schemas:

| Path | Endpoint | Response Schema | Auth |
|---|---|---|---|
| Collab | `POST /api/collab` | `owner-console.reply.v1` | owner-initdata |
| Ask | `POST /api/ask` | `{ok, answer, source, ...}` | owner-initdata |
| Mirror | `POST /api/mirror` | `{text, history, ...}` | owner-initdata |
| Guide | `POST /api/brain-guide` | `{text, kind, ...}` | owner-initdata |

Each has different field names, error shapes, and source representations. The UI
must handle 4 code paths. There is no unified intent routing — the user picks a mode
chip manually.

## Existing Infrastructure (~80% already built)

The Hub does **NOT** build from scratch. It orchestrates existing modules:

| Module | Role | Used By |
|---|---|---|
| `ask_vault.py` | Retrieval-augmented Q&A over Obsidian vault | `/api/ask` tier 1 |
| `ask_brain.py` | Free-form QA from organism state | `/api/ask` tier 2 |
| `collaborator.py` | Conversational AI (wraps `conversation.py`) | `/api/collab`, `/api/ask` fallback |
| `conversation.py` | ~20 intent patterns via regex | `collaborator.py` |
| `epistemics/schemas.py` | Claim/TestPlan/EvidenceReceipt/GateDecision | hypothesis engine |
| `epistemics/canonical.py` | SHA-256 content hashing | evidence chain |
| `provenance.py` | Stamped numbers (LIVE/HELD/CONSTANT) | telemetry |
| `octopus_mcp/server.py` | 5 tools: list_tree, read_file_slice, hash_file, search_hybrid, propose_action | standalone stdio |
| `cortex/` | Runtime organism state | read-only via `get_runtime_snapshot()` |
| `miniapp_gateway.py` | Auth, rate limit, redaction | all miniapp traffic |

## Decision

Build a **Conversation Hub** (`_ops/conversation_hub/`) as a façade/orchestrator:
- Single entry point: `handle(req) -> ChatReply`
- Single response schema: `octopus.chat.reply.v1`
- Deterministic intent routing (no LLM for routing)
- Provenance event per interaction
- Feature flag gate: `OCTOPUS_UNIFIED_CHAT=0` (default OFF)

## Architecture

### Route Authority Table

| Route | Source | Authority | External Effect |
|---|---|---|---|
| `ask` | vault → brain → collab (3-tier) | observe | ❌ |
| `vault` | ask_vault | observe | ❌ |
| `brain` | ask_brain | observe | ❌ |
| `collab` | collaborator | observe | ❌ |
| `runtime` | cortex read-model snapshot | observe | ❌ |
| `mcp` | MCP broker (3 read tools) | observe | ❌ |
| `epistemic` | epistemics projection | observe | ❌ |
| `guide` | owner guidance | propose | ❌ |
| `propose` | proposal queue | queue-only | ❌ |
| `approve` | **separate endpoint** | authorize | ❌ |
| `execute` | **FORBIDDEN from chat** | — | — |

### Response Schema (`octopus.chat.reply.v1`)

```python
class ChatReply(BaseModel, frozen=True):
    schema_version: str = "octopus.chat.reply.v1"
    ok: bool = True
    answer: str
    route: str
    epistemic_status: str = "not_applicable"  # see rules below
    confidence: str = "unknown"                # evidenced|derived|inferred|unknown
    sources: list[SourceRef]
    run_id: str | None
    trace_id: str | None
    receipt_ids: list[str]
    proposals: list[dict]
    provenance_event_id: str | None
    may_authorize: bool = False
    external_effect: bool = False              # ALWAYS False
    limitations: list[str]
```

### Epistemic Status Rules

| Route | epistemic_status | Rationale |
|---|---|---|
| `epistemic` | `supported`/`refuted`/`inconclusive`/`blocked` | Real epistemic evaluation |
| All others | `not_applicable` | Retrieval/observation, not knowledge claim |
| Phase 1 stubs | `inconclusive` (epistemic) / `not_applicable` (others) | Cannot determine |

### Confidence Levels

| Level | When |
|---|---|
| `evidenced` | Explicit mode override (research/guide/propose) |
| `derived` | Keyword match score ≥ 3 |
| `inferred` | Single keyword hit |
| `unknown` | No keyword match (fallback to ask) |

### Intent Router (Deterministic, No LLM)

```
1. Explicit mode (research→epistemic, guide→guide, propose→propose)
2. Keyword scoring:
   وضعیت/سیستم/pulse/status/cycle → runtime
   فایل/خط/کد/ADR/commit → mcp
   یادت/remember/حافظه/memory → memory
   آیا/فرضیه/hypothesis/claim → epistemic
   تمرکز/focus → guide
   اصلاح/fix/patch → propose
3. Fallback → ask (vault → brain → collab)
```

## Hard Constraints (Non-negotiable)

1. **`execute` NEVER from chat endpoint** — `/api/octopus/chat` is observe+propose only.
   Approval and execution use separate endpoints with nonce + payload-hash.
2. **Cortex only read-model** — `get_runtime_snapshot()` and `get_health()` only.
   Never `cortex.run_cycle()` from chat.
3. **MCP completely server-side** — Browser must never know MCP/stdio/filesystem.
4. **`OCTOPUS_UNIFIED_CHAT=0` default OFF** — Endpoint returns 404/FEATURE_DISABLED when off.
5. **Improve don't rewrite** — collaborator, ask_vault, ask_brain, conversation,
   epistemics/schemas, canonical are untouched. Hub rides on top.
6. **`epistemic_status` honest** — Never label a retrieval answer as "supported".
   Only Claim+Plan+Receipt routes get real epistemic labels.
7. **`confidence` precise enum only** — `evidenced|derived|inferred|unknown`.
   Never free-form text.
8. **Source paths: logical only** — `cortex/cortex.py`, never `F:\backup\...`.
9. **ARCHITECTURE-BIBLE:49-51** — Never phenomenal consciousness/qualia/sentience.
10. **autonomy_grant.py hard deny** — payment/external_send/apply/commit/secret/PII/flag.

## Phase Plan

| Phase | Scope | Dependency |
|---|---|---|
| **1** (done) | Core: schemas, router, service, stub adapters, tests | — |
| **2** | Real adapters: vault, brain, collab, MCP broker (3 read tools), runtime, memory, epistemic | Phase 1 ✅ |
| **3** | `POST /api/octopus/chat` in gateway + flag + GET runs/receipts | Phase 2 ✅ |
| **4** | Epistemic projection — retrieve/display Claim + Receipt | Phase 3 ✅ |
| **5** | UI unification — single mode toggle in app.js + sources panel + epistemic badge | Phase 3 ✅ |
| **6** | Shadow rollout — owner-only 24h, dual-read Hub vs /api/collab | Phase 5 ✅ |

## What Is Intentionally NOT Done

- ❌ Replacing `collaborator.py` or `conversation.py` — Hub orchestrates, not replaces
- ❌ Cortex invocation from chat endpoint
- ❌ `execute` from chat endpoint — always forbidden
- ❌ Converting the Web App into an MCP client
- ❌ Rewriting `ask_vault`, `ask_brain`, `chat_room.py`, or `epistemics/schemas.py`
- ❌ Free-form confidence values
- ❌ Dangerous tools in MCP broker (run_shell, write_any_file, git_commit, restart_service)

## Files Added (Phase 1)

| File | Lines | Purpose |
|---|---|---|
| `_ops/conversation_hub/__init__.py` | 24 | Package exports |
| `_ops/conversation_hub/schemas.py` | 118 | Pydantic v2 frozen models |
| `_ops/conversation_hub/router.py` | 144 | Deterministic intent classifier |
| `_ops/conversation_hub/service.py` | 205 | handle() entry point + stub adapters |
| `_ops/tests/test_conversation_hub.py` | 333 | 11 tests (t_a–t_k) |
