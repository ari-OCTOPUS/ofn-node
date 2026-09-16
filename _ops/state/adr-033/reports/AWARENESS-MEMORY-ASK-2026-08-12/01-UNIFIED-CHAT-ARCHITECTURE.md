# 01-UNIFIED-CHAT-ARCHITECTURE — 2026-08-12

> معماری هدف پس از discovery: **یک جریان واحد**، بدون orchestrator جدید.

## معماری

```
Chat Box / Miniapp (app.js renderAsk)
   │  POST /api/collab | /api/ask
   ▼
miniapp_gateway.py (auth + rate-limit + redact دولایه)
   │
   ├─ /api/collab → collaborator.handle()
   │    ├─ conversation.handle() → intent (17+ قدیمی + 10 هدف جدید)
   │    ├─ owner_recall.recall_for_owner_ask() → data.facts (cite-only)
   │    ├─ equation_advice.equation_advice_snapshot() → data.equation_advice
   │    ├─ unified_context.assemble() → data.unified_context
   │    │    ├─ self_context (cortex + business_brain + 4d=false)
   │    │    ├─ shadow (records + applied=false)
   │    │    ├─ effects (policy_gate_status + enabled)
   │    │    └─ architecture (components + edges)
   │    ├─ session_memory.remember() (موقت، preview-only)
   │    └─ collab_memory.append() (content-free sha256)
   │
   ├─ /api/ask → ask_vault → ask_brain → collab-fallback
   └─ /api/mirror → mirror_room

معادلات/معماری:
   equation_explainer.explain(query)  → ۵ سطح + status واقعی + شاهد
   architecture_explainer.explain(query) → ساده + فنی (path/caller/gates)
```

## اجزای reuse (بدون بازنویسی)

| جزء | فایل | نقش |
|-----|------|-----|
| gateway | `miniapp_gateway.py` | ورودی واحد + auth + redact |
| collaborator | `collaborator.py` | روتر/assembler مکالمه |
| conversation | `conversation.py` | ۲۷+ intent |
| owner_recall | `memory/owner_recall.py` | cite-only حافظه |
| equation_advice | `memory/equation_advice.py` | advice-only معادلات |
| collab_memory | `collab_memory.py` | episodic digest |
| collab_model_adapter | `collab_model_adapter.py` | _self_context + مدل |

## اجزای جدید (additive)

| جزء | فایل | نقش |
|-----|------|-----|
| unified_context | `memory/unified_context.py` | assembler واحد (P) |
| equation_explainer | `memory/equation_explainer.py` | توضیح ۱۳ معادله با status (Q) |
| architecture_explainer | `memory/architecture_explainer.py` | ۱۱ جزء با path/caller (Q) |
| session_memory | `memory/session_memory.py` | session موقت + memory proposal (S) |
| UI | `miniapp/app.js` | رندر evidence/equation/shadow/effect + vault paths (R) |

## قرارداد پاسخ (data در collab)

```json
{
  "facts": [...],                // cite-only (owner_recall)
  "facts_rationale": "...",
  "equation_advice": {           // advice-only
    "equation_advice_only": true, "decision_effect": false, "apply_effect": false
  },
  "unified_context": {
    "intent": "...",
    "self_context": {"cortex": {...}, "business_brain": {...}, "four_d_connected": false},
    "shadow": {"shadow_records": N, "applied": false},
    "effects": {"policy_gate_status": "NOT_REQUESTED", "proposal_created": false, "applied": false},
    "architecture": {"components": [...], "edges": [...]},
    "trace_id": "uctx-...",
    "may_authorize": false
  },
  "session_turn": "...",
  "may_authorize": false,
  "external_effect": false, "send_attempted": false
}
```

## امنیت (invariants حفظ‌شده)

- `may_authorize=false` در همهٔ adapterهای گفت‌وگویی (تست‌شده)
- Chat/Memory/Equation هیچ authority تولید نمی‌کند
- external send/payment/email ممنوع (ساختاری `external_effect=false`)
- secret در response/log/test ممنوع (redact دولایه + تست)
- missing provenance = no claim (equation ناشناخته → matched=false)
- exception = DENY/fail-soft، نه allow

## Conflictهای زنده (از discovery)

| id | شرح | وضعیت |
|----|------|--------|
| C1 | chrono-rhythm TESTED/SHADOW | **حل شد** — validator ok (ادعا ≤ شواهد) |
| C2 | ADR-036 فایل ندارد | **ثبت شد** — ساخت نیازمند رأی مالک (ناحیهٔ قفل) |
