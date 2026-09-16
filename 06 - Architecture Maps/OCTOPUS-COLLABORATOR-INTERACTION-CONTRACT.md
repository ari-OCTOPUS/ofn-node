---
type: knowledge
kind: architecture-map
status: active
created: 2026-08-10
updated: 2026-08-12
tags: [collaborator, interaction-contract, telegram, miniapp, shadow, propose-only, talk-discovery, canonical]
---

# Octopus Collaborator Interaction Contract

> **Canonical** architecture map for owner talk surfaces.
> Runtime pointer (thin): `_ops/INTERACTION-CONTRACT.md` → this file.
> Status: implemented / shadow-ready. All capabilities **default OFF**.
> No live/beneficial/AGI claims without evidence ladder.

## Topology

```text
Owner
  ├─ MiniApp Ask      POST /api/ask     → ask_vault → ask_brain
  ├─ MiniApp Mirror   POST /api/mirror  → mirror_room
  ├─ MiniApp Collab   POST /api/collab  → collaborator.handle
  └─ Telegram Outer DM
        center → telegram_adapter
          ├─ OCTOPUS_WIRE_COLLAB=1 → collaborator.handle  (same brain as MiniApp)
          └─ else → conversation.handle
               clarify may fall through to ask_brain
```

Preserved systems: `miniapp/app.js`, `miniapp_gateway.py` (:8774),
`conversation.py`, `live_snapshot.py`, `collab_memory.py`, `collab_digest.py`.

Talk Discovery additions: `collab_model_adapter.py` → `model_router.ask(task="collab_chat")`,
`discovery_pulse.py`, `capability_journal.py`.

## Surfaces & routing

| Surface | Entry | Brain |
|---|---|---|
| MiniApp Ask | `POST /api/ask` | ask_vault then ask_brain |
| MiniApp Mirror | `POST /api/mirror` | mirror_room |
| MiniApp Collaborator | `POST /api/collab` | `collaborator.handle` |
| Telegram Outer DM | center → telegram_adapter | collab if armed, else conversation |
| Telegram photo DM | `_capture_hook` | no vision — bare photo asks for caption |

### Routing rules

1. Center slash commands (`/menu`, …) never enter collaborator.
2. Structured intents (goal/runtime/blockers/capabilities) stay deterministic even when `OCTOPUS_COLLAB_USE_MODEL=1`.
3. `intro` / `clarify` / `chat` may call `model_router` via `collab_model_adapter` when model flag is on.
   `discover` stays deterministic (journal + dark pulse) even with model armed.
4. Photos without caption are not archived as silent notes.
5. Collaborator always `external_effect=false` / `send_attempted=false`.

## Schemas

### owner-console.reply.v1
```json
{
  "schema": "owner-console.reply.v1",
  "kind": "intro|clarify|discover|chat|capabilities|runtime|blockers|goal|disabled|…",
  "text": "...",
  "keyboard": [],
  "data": {"rationale": "...", "memory_turn_id": "..."},
  "external_effect": false,
  "estimated_cost": 0,
  "send_attempted": false,
  "model_source": "deterministic-stub|model-fallback-stub|local:…|secondary:…|primary:…"
}
```

### CollabMemory.v1 / CollabDigest.v1
Unchanged episodic + monitoring schemas (content-free summaries; interrupt = proposal only).

### CapabilityJournal.entry.v1
`candidate · level STRUCTURAL|TESTED|SHADOW|ARMED · evidence · owner_vote · next · auto_arm=false`

## Boundaries

| لایه | مجاز | ممنوع |
|---|---|---|
| **Read** | snapshot، catalog، dark pulse، journal | نوشتن state زندهٔ ارگانیسم |
| **Propose** | کارت/متن propose-only، living card | ارسال/execute/pay/auto-arm |
| **Hard-gated** | (نیاز به رأی مالک) | restart، deploy، money/lead arm، outbound send |

## Autonomy / flags

| سطح | شرح | flag |
|---|---|---|
| Draft (default UI) | گفت‌وگو + memory digests؛ پیش‌فرض chip همکار | `OCTOPUS_WIRE_COLLAB` **ARMED** |
| Model talk | + `collab_chat` via model_router | `OCTOPUS_COLLAB_USE_MODEL` **ARMED** |
| Soft call cap | daily adapter counter | `OCTOPUS_COLLAB_MODEL_DAILY_CAP=20` |
| Explicit Ask / Mirror | فقط با انتخاب chip | — |
| Monitored | digest build | `OCTOPUS_WIRE_COLLAB_DIGEST` **ARMED** |
| Guarded external | send/harvest/CRM | **hard-forbidden** in TalkDiscoveryPolicy |

Money still flows through `organ_gate` / `budgets.yaml` when a paid tier is used.
`collab_chat` is mapped **local** in `TASK_TIERS`. Collaborator = default **reply** path, never external-effect path.

## Discovery gateway

Single facade: `owner_console/discovery_facade.py` → catalog + dark/journal + World Discovery
with per-section provenance. `status.discovery()` and discover intents use it.
| Draft | گفت‌وگو + memory | `OCTOPUS_WIRE_COLLAB` |
| Model talk | + `collab_chat` via model_router | `OCTOPUS_COLLAB_USE_MODEL` |
| Soft call cap | daily adapter counter | `OCTOPUS_COLLAB_MODEL_DAILY_CAP` (default 30) |
| Monitored | digest build | `OCTOPUS_WIRE_COLLAB_DIGEST` |
| Guarded | bound action | future — owner verdict |

Money still flows through `organ_gate` / `budgets.yaml` when a paid tier is used.
`collab_chat` is mapped **local** in `TASK_TIERS` (local-first; paid only if router escalates).

## Owner auth / HMAC / Rule of Two

- HMAC gate on MiniApp (`X-Tg-Init-Data`).
- Rule of Two: session never holds A+B+C together (untrusted input / sensitive data / external effect).
- Collaborator has no C. Safety is flag/HMAC/schema — not model goodwill.

## Failure semantics

| Condition | Behavior |
|---|---|
| flag off | `kind=disabled` |
| missing snapshot | UNKNOWN digest |
| PII/secret in memory | rejected (fail-closed) |
| malformed input | clarify (fail-soft) |
| model miss/timeout/cap | stub + warning (`model-fallback-stub` / `daily-cap`) |
| bare photo | ask for caption (no fake vision) |

## Discovery (Talk Discovery C–D)

- Journal: `_ops/CAPABILITY-JOURNAL.md` + optional JSONL
- Pulse: `owner_console/discovery_pulse.py` (AI-core dark only; excludes lead/money/outbound)
- Protocol: `_ops/DISCOVERY-PROTOCOL.md`
- Law: Novel ∧ Repeatable ∧ Useful ∧ Policy-Compliant — **no auto-arm**

## Related maps

- Evidence ladder: [[_ops/EVIDENCE-LADDER|EVIDENCE-LADDER]]
- Route policy: [[_ops/ROUTE-POLICY|ROUTE-POLICY]]
- Discovery: [[_ops/DISCOVERY-PROTOCOL|DISCOVERY-PROTOCOL]] · [[_ops/CAPABILITY-JOURNAL|CAPABILITY-JOURNAL]]
- Session: [[00 - Inbox/2026-08-11 SESSION — Talk Discovery Implemented|SESSION Talk Discovery]]
- Heart invariants: [[06 - Architecture Maps/Octopus_Heart_Design_v1|Octopus_Heart_Design_v1]] (pulse untouched by this contract)
- ADR: [[03 - Projects/research-spec-compiler/adr/ADR-023-octopus-collaborator|ADR-023]]
- Evidence ladder: `_ops/EVIDENCE-LADDER.md`
- Route policy: `_ops/ROUTE-POLICY.md`
- Heart invariants: `06 - Architecture Maps/Octopus_Heart_Design_v1.md` (pulse untouched by this contract)

## Non-goals

- Not a FAQ chatbot · Not AGI · No vision pipeline · No mass money/lead arm
- No send/effect/pay without separate owner verdict

## Truth line

```text
shared-collab-brain + honest-photo + discovery-journal + capped-collab-chat
!= vision != money-live != unbounded-model != auto-arm
```
