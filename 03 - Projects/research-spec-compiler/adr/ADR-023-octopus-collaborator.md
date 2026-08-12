# ADR-023 — Octopus Collaborator: trust boundary, memory policy, no-effect invariant

- **Status:** **Live ARMED** (Talk Discovery) — draft responses only; no external effect
- **Date:** 2026-08-10
- **Updated:** 2026-08-11 (Capability Truth + discover provenance v2 + OTLP→Alloy)
- **Spec:** `06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md`
- **Code:** `_ops/owner_console/collaborator.py`, `collab_model_adapter.py`, `_ops/discovery/discover_facade.py`, `collab_memory.py`, `collab_digest.py`
- **Policy:** `_ops/collab/talk_discovery_policy.py` · `_ops/collab/approval_sm.py` · `_ops/collab/approval_state.py`
- **Route:** `POST /api/collab` + MiniApp default chip «همکار» when `OCTOPUS_WIRE_COLLAB=1`

## Capability Truth

| Field | Value |
|---|---|
| Capability | Talk Discovery Collaborator |
| Claimed state | ARMED (draft-only) |
| Runtime path | `_ops/owner_console/collaborator.py` → `conversation.py` |
| Feature flag | `OCTOPUS_WIRE_COLLAB=1` (+ model/memory/digest optional) |
| Evidence artifact | MiniApp `/api/collab` + DM via telegram_adapter; tests `test_cognitive_unify.py` / `test_talk_discovery.py` |
| Tests | Live suite green for collab draft path |
| External effects | None permitted (`external_effect=false`, EXTERNAL_SEND hard-forbidden) |
| Promotion condition | Already ARMED for draft; further promotion (send/harvest) = owner vote + separate ADR |
| Rollback | rem flags; restore `_ops/_bak/talk-discovery-arm-*` |

### Non-claims (Collaborator)
- This ADR does not authorize EXTERNAL_SEND, harvest, CRM, payment, or policy mutation.
- Model replies remain empirical (local-first); content-free digests ≠ semantic memory.

## Capability Truth — Discovery Facade v2

| Field | Value |
|---|---|
| Capability | discover_reply_text with Provenance |
| Claimed state | SHADOW / STRUCTURAL (read-only facade) |
| Runtime path | `_ops/discovery/discover_facade.py` + `sources.py` |
| Feature flag | None (always read-only) |
| Evidence artifact | Provenance + limitations on every fact; MiniApp «Sources / شواهد» |
| Tests | `test_approval_state.py` (facade) · `test_cognitive_unify.py` |
| External effects | None permitted |
| Promotion condition | N/A — remains propose/discover only |
| Rollback | Revert adapter in `owner_console/discovery_facade.py` |

### Non-claims (Discovery)
- World Discovery July-30 report is historical; TTL marks it `stale`, not current truth.
- UI must not show only `reply.text` without Sources affordance.

## Capability Truth — Criticality C_t / Spectral

| Field | Value |
|---|---|
| Capability | Chrono Rhythm / criticality_v2 C_t |
| Claimed state | SPEC_NOT_BUILT for gating; SHADOW for metrics |
| Runtime path | `_ops/doctor/criticality_v2.py` + `spectral_metrics.py` |
| Feature flag | OTLP emit: `OCTOPUS_WIRE_CRITICALITY_OTLP=0` default |
| Evidence artifact | `state/criticality/criticality-v2.jsonl` (component scores) |
| Tests | `test_cognitive_unify.py` · spectral disconnected in `test_approval_state.py` |
| External effects | None — never gates heart/router |
| Promotion condition | Shadow implementation + 7-day evidence + owner vote |
| Rollback | N/A: not deployed as gate |

### Non-claims (C_t)
- This ADR does not assert that CR-B0 / C_t exists as a production control signal.
- Disconnected graphs must not inflate σ via ε theater (`graph_disconnected` in trace).
- OTLP goes to local Alloy (`127.0.0.1:4318`); Grafana cloud credentials must not live in Python runtime.

## Capability Truth — Approval fingerprint gates

| Field | Value |
|---|---|
| Capability | Talk Discovery approval_state |
| Claimed state | TESTED (library) / SPEC_NOT_BUILT (Redis store) |
| Runtime path | `_ops/collab/approval_state.py` (+ `approval_sm.py`) |
| Feature flag | None |
| Evidence artifact | Hash/expiry/policy/idempotency fail-closed |
| Tests | `test_approval_state.py` |
| External effects | None; forbidden actions stay BLOCKED even if «approved» |
| Promotion condition | Durable store + owner ops review |
| Rollback | In-process registry only |

## Evidence ladder (official)

```text
SPEC_NOT_BUILT -> STRUCTURAL -> TESTED -> SHADOW -> ARMED -> LOCKED
                                     \-> RETIRED
```

Every transition needs: PR/commit, test result, trace window, owner approval, rollback flag.

## Context

The Octopus owner needs a **collaborator** — not a FAQ bot. Two-way dialogue with rationale, content-free episodic digests, clarification, live-truth reading, monitoring digest. Ask and Mirror remain **explicit modes**, not the default when COLLAB is armed.

## Live arm evidence (2026-08-11)

| Flag | Value |
|---|---|
| `OCTOPUS_WIRE_COLLAB` | 1 |
| `OCTOPUS_WIRE_COLLAB_MEMORY` | 1 |
| `OCTOPUS_WIRE_COLLAB_DIGEST` | 1 |
| `OCTOPUS_COLLAB_USE_MODEL` | 1 |
| `OCTOPUS_COLLAB_MODEL_DAILY_CAP` | 20 |

Session: [[00 - Inbox/2026-08-11 SESSION — Talk Discovery ARMED]]

## What is built (ARMED / TESTED / SHADOW)

| Component | File | Flag | Live |
|---|---|---|---|
| Interaction contract | `OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md` | — | canonical |
| Collaborator engine | `collaborator.py` | `OCTOPUS_WIRE_COLLAB` | ARMED |
| Model adapter | `collab_model_adapter.py` | `OCTOPUS_COLLAB_USE_MODEL` | ARMED |
| Discovery facade v2 | `_ops/discovery/discover_facade.py` | — | SHADOW |
| Content-free memory digests | `collab_memory.py` | `OCTOPUS_WIRE_COLLAB_MEMORY` | ARMED |
| Monitoring digest (build) | `collab_digest.py` | `OCTOPUS_WIRE_COLLAB_DIGEST` | ARMED |
| MiniApp default → collab + Sources | `miniapp/app.js` + gateway inject | same | live |
| TalkDiscoveryPolicy | `collab/talk_discovery_policy.py` | — | live |
| Approval SM + approval_state | `approval_sm.py` / `approval_state.py` | — | TESTED |
| Spectral + C_t | `spectral_metrics.py` / `criticality_v2.py` | — | SHADOW |
| OTLP → Alloy | `telemetry/criticality_metrics.py` | `OCTOPUS_WIRE_CRITICALITY_OTLP` | SPEC_NOT_BUILT (default off) |

## SPEC_NOT_BUILT (remain honest)

| Item | Tag |
|---|---|
| Vision for photos/PDF | `SPEC_NOT_BUILT` |
| Scheduler auto-send of digest to Telegram | `SPEC_NOT_BUILT` |
| Semantic memory writes | `SPEC_NOT_BUILT` (forbidden by policy) |
| EXTERNAL_SEND / harvest / CRM via collaborator | `SPEC_NOT_BUILT` + hard-forbidden |
| Redis-backed approval store | `SPEC_NOT_BUILT` (SM is fail-closed in-process/file) |
| Criticality C_t gating heart/router | `SPEC_NOT_BUILT` — module is **SHADOW-only** |
| Pulse arbiter production wire | `SPEC_NOT_BUILT` — shadow divergence optional flag |
| OTLP live exporter armed | `SPEC_NOT_BUILT` until Alloy local + 7-day SHADOW evidence |

## Trust boundary

```text
Owner → MiniApp (default collab) / Outer DM
  → collaborator.handle()
  → TalkDiscoveryPolicy(RESPOND_DRAFT)  # untrusted input
  → conversation + optional model_router(collab_chat)
  → content-free memory digest (not semantic write)
  → owner-console.reply.v1 (external_effect=false, response_mode=draft)
```

Collaborator is the **default reply path**, never an external-effect path.

### Rule of Two

Session never holds A+B+C together. Collaborator has **no C**.

## Activation / rollback

- Arm: flags in `OCTOPUS-flags.cmd` + `RESTART-ALL`
- Rollback: rem `OCTOPUS_COLLAB_USE_MODEL` / cap; restore `_ops/_bak/talk-discovery-arm-*`
- OTLP: set `OCTOPUS_WIRE_CRITICALITY_OTLP=1` only with Alloy on `127.0.0.1:4318`; see `_ops/telemetry/config.alloy.example`

## Confirmed caveats

1. Efficacy of model replies still empirical — local-first `collab_chat`.
2. Content-free digests ≠ approved episodic narrative memory.
3. Ask/Mirror still available as **explicit** chips only.
4. C_t / spectral metrics are shadow observability only.
