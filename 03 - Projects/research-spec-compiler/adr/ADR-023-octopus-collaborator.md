# ADR-023 — Octopus Collaborator: trust boundary, memory policy, no-effect invariant

- **Status:** Open — shadow/propose-only build complete; activation requires owner verdict
- **Date:** 2026-08-10
- **Spec:** `06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md`
- **Code:** `_ops/owner_console/collaborator.py`, `collab_memory.py`, `collab_digest.py`, `collab_sim.py`

## Context

The Octopus owner needs a **collaborator** — not a FAQ bot, not a chatbot display. A two-way dialogue with "why" explanation, episodic memory, clarification, proposal cards, live-truth reading, monitoring digest, and deterministic echo simulation. Built on existing Telegram WebApp + Control Panel infrastructure.

This ADR documents the scope, trust boundary, memory/PII policy, no-effect invariant, flags, rollback, resource limits, and future activation criteria.

## Scope

The Collaborator is a **harness** — a deterministic stub that validates plumbing, not efficacy. Real model injection is a separate owner-gated step.

### What is built

| Component | File | Flag | Default |
|---|---|---|---|
| Interaction contract | `OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md` | — | doc |
| Episodic memory | `collab_memory.py` | `OCTOPUS_WIRE_COLLAB_MEMORY` | OFF |
| Collaborator engine | `collaborator.py` | `OCTOPUS_WIRE_COLLAB` | OFF |
| Monitoring digest | `collab_digest.py` | `OCTOPUS_WIRE_COLLAB_DIGEST` | OFF |
| Echo simulation | `collab_sim.py` | — | manual |
| MiniApp route | (WP-E4 — handler ready, route pending owner verdict) | `OCTOPUS_WIRE_COLLAB` | OFF |

### What is NOT built (owner-gated future)

- Real model adapter injection (`OCTOPUS_COLLAB_USE_MODEL=1` + adapter)
- MiniApp gateway route patch (WP-E4 — needs reserved-file touch)
- Scheduler / automated digest delivery
- Any external effect, send, payment, or deployment

## Trust boundary

```text
Owner → MiniApp → gateway (HMAC) → collaborator.handle()
  → conversation.py (existing, wrapped not replaced)
  → collab_memory (PII-scrubbed, append-only)
  → collab_digest (read-only snapshot)
  → owner-console.reply.v1 (external_effect=false)
```

### Rule of Two

Session never has all three simultaneously:
- A: untrusted input
- B: sensitive data
- C: external effect

Collaborator has **no C** in this build. If B is needed, input is limited to scrubbed summary.

## Memory policy

- **Append-only JSONL** (`collab-memory.jsonl`)
- **PII/secret scrub** before write: api_key, email, credit-card, bearer token patterns rejected
- **Idempotent**: `turn_id` deduplication
- **UTC timestamps**
- **Bounded**: summary max 500 chars, intent max 100 chars
- **No raw model output, secret, or PII** in memory
- **Directory permissions**: directory created with `mkdir(parents=True, exist_ok=True)` — owner should set 0700 on state dir
- **SQLite WAL**: not applicable (JSONL, not SQLite); if upgraded to SQLite: `PRAGMA synchronous=FULL`
- **Bounded retention/size**: current implementation has no retention cap — owner should add rotation or size limit before arming
- **Single instance**: no concurrent writers (single-writer architecture)

## No-effect invariant

Every reply from `collaborator.handle()` MUST have:
```json
{"external_effect": false, "estimated_cost": 0, "send_attempted": false}
```

This is structurally enforced in the code, not prompt-based. Security does not depend on model cooperation — flag/HMAC/schema/transport separation are independent.

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `OCTOPUS_WIRE_COLLAB` | 0 | Main collaborator gate |
| `OCTOPUS_WIRE_COLLAB_MEMORY` | 0 | Episodic memory gate |
| `OCTOPUS_WIRE_COLLAB_DIGEST` | 0 | Monitoring digest gate |
| `OCTOPUS_COLLAB_USE_MODEL` | 0 | Real model gate (separate from wiring) |

All OFF by default. Activation = owner verdict.

## Rollback

- `git revert` the collaborator commit(s)
- Unset flags (already OFF)
- Delete `collab-memory.jsonl` (append-only, no state loss in canonical systems)
- `conversation.py` (existing system) is untouched — collaborator wraps it

## Resource limits

- **RAM**: deterministic stub uses negligible RAM; real model adapter will need budget
- **Cost**: $0 in this build (stub only); real model needs paid-call authorization
- **Disk**: memory JSONL grows unbounded — add retention cap before arming
- **Network**: none in this build

## Activation criteria (future)

1. Full run_all green (current: not yet — 4 suites LIVE_TREE_DEPENDENT)
2. Owner verdict to arm `OCTOPUS_WIRE_COLLAB=1`
3. WP-E4 route patch (MiniApp gateway)
4. Real model adapter (owner-gated, separate paid-call authorization)
5. Memory retention cap
6. Monitoring digest scheduler (owner-gated)

## Confirmed caveats

1. **Efficacy unproven**: the stub validates plumbing only. Real dialogue quality requires real model injection.
2. **No external effect**: the Collaborator cannot send, pay, deploy, or restart anything.
3. **Memory has no retention cap**: unbounded growth possible if armed without rotation.
4. **WP-E4 route pending**: MiniApp gateway route not patched (reserved file).
