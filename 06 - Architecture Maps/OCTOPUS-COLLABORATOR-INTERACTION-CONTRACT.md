---
type: knowledge
kind: architecture-map
status: active
created: 2026-08-10
updated: 2026-08-10
tags: [collaborator, interaction-contract, telegram, miniapp, shadow, propose-only]
---

# Octopus Collaborator Interaction Contract (WP-E1)

> **وضعیت:** implemented / shadow-ready. All capabilities default OFF.
> هیچ claims live/beneficial/AGI بدون evidence.

## Topology (موجود — حفظ می‌شود)

```text
Owner → Telegram WebApp (tab `ask`) → miniapp_gateway (:8774)
  → owner_console/collaborator.py (wraps conversation.py)
  → collab_memory.py (PII-safe episodic)
  → collab_digest.py (from live_snapshot)
  → owner-console.reply.v1 response
```

سیستم‌های موجود که حفظ می‌شوند:
- `miniapp/app.js` (~۲۱۰۰ خط، ۹ tab)
- `miniapp_gateway.py` روی 127.0.0.1:8774
- `conversation.py` (base handler)
- `live_snapshot.py` (read-only truth)

## Message/Card/Memory Schemas

### owner-console.reply.v1 (همان schema موجود)
```json
{
  "schema": "owner-console.reply.v1",
  "kind": "ask|clarify|capabilities|runtime|blockers|disabled",
  "text": "...",
  "keyboard": [],
  "data": {"rationale": "...", "memory_turn_id": "..."},
  "external_effect": false,
  "estimated_cost": 0,
  "send_attempted": false,
  "model_source": "deterministic-stub"
}
```

### CollabMemory.v1 (episodic)
```json
{
  "schema": "CollabMemory.v1",
  "ts": "UTC ISO",
  "turn_id": "hash16",
  "role": "owner|collaborator",
  "intent": "ask|clarify|propose",
  "summary": "scrubbed (max 500 chars)",
  "summary_hash": "hash16"
}
```

### CollabDigest.v1 (monitoring)
```json
{
  "schema": "CollabDigest.v1",
  "status": "OK|ALERT|CRITICAL",
  "verified_changes": [],
  "blockers": [],
  "critical": [],
  "interrupt_affordance": false
}
```

## Boundaries

| لایه | مجاز | ممنوع |
|---|---|---|
| **Read** | snapshot، catalog، live_snapshot | نوشتن state زنده |
| **Propose** | کارتِ propose-only با rationale | ارسال/execute/pay |
| **Hard-gated** | (هیچ — این مرحله اجرا نمی‌کند) | restart، deploy، paid call |

## Autonomy layer mapping

| سطح | شرح | flag |
|---|---|---|
| Draft | فقط گفت‌وگو + memory | OCTOPUS_WIRE_COLLAB |
| Supervised | + کارت پیشنهاد | (future) |
| Monitored | + digest فعال | OCTOPUS_WIRE_COLLAB_DIGEST |
| Guarded | + اقدام bound | (future — owner verdict) |

هیچ سطحی در این build مسلح نیست.

## Owner auth / HMAC / Rule of Two

- HMAC gate روی MiniApp (X-Tg-Init-Data مثل fetchهای موجود).
- Rule of Two: session هرگز هم‌زمان هر سه را ندارد:
  - A: untrusted input
  - B: sensitive data
  - C: external effect
- Collaborator در این مرحله C ندارد. اگر B لازم شد، input به summaryِ scrubbed محدود می‌شود.
- ایمنی به همکاریِ مدل وابسته نیست — flag/HMAC/schema/transport separation مستقل‌اند.

## Failure semantics

- flag off → no-op (kind="disabled")
- missing snapshot → UNKNOWN digest
- PII/secret detected → rejected (fail-closed)
- malformed input → clarify (fail-soft)
- model adapter not wired → fallback to stub (with warning)

## Non-goals (صریح)

- این یک FAQ chatbot نیست.
- این یک AGI نیست.
- efficacy/agency/outcome-improvement باید بعداً تجربی اثبات شوند.
- هیچ send/effect/pay بدون verdict جداگانهٔ مالک.
