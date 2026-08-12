---
type: ops-protocol
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, discovery, talk-discovery, propose-only]
aliases: [پروتکل کشف, Discovery Protocol]
---

# DISCOVERY-PROTOCOL — مالک ↔ اختاپوس

Status: active (Talk Discovery Phase D)
Scope: AI-core hidden capability discovery. Money/lead/outbound = separate votes.

## Canonical contract

Routing / schemas / flags:  
[[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT|OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]]  
(runtime pointer: [[_ops/INTERACTION-CONTRACT|INTERACTION-CONTRACT]])

جلسه: [[00 - Inbox/2026-08-11 SESSION — Talk Discovery Implemented|SESSION Talk Discovery]]  
دفترچه: [[_ops/CAPABILITY-JOURNAL|CAPABILITY-JOURNAL]] · نردبان: [[_ops/EVIDENCE-LADDER|EVIDENCE-LADDER]]

## Daily loop (5–10 min)

1. **Owner open question** — e.g. «چه چیزی داری که من ندیدم؟»
2. **Octopus propose** — MiniApp Collaborator (default) or TG DM (`OCTOPUS_WIRE_COLLAB=1`):
   - uses `_ops/discovery/discover_facade.discover_reply_text` (catalog + journal/dark + World Discovery; Provenance + TTL; Sources/شواهد in UI)
   - draft only — TalkDiscoveryPolicy / approval_state forbids EXTERNAL_SEND even with approval; store/hash/expiry mismatch → BLOCKED
3. **Owner vote** — one of: `experiment` | `ignore` | `arm-later`
4. **Experiment** — offline test or shadow session with caps; result → journal row
5. **No auto-arm** — flags stay off until explicit live arm + restart

## Weekly loop

| Step | Action | Gate |
|---|---|---|
| Dark pulse | `python owner_console/discovery_pulse.py` | read-only |
| Digest | `collab_digest.build_digest` | build-only until `OCTOPUS_WIRE_COLLAB_DIGEST` voted |
| Journal refresh | `seed_journal_from_pulse` or manual MD edit | propose-only |
| Living card | `living_card()` text on cockpit/DM | edit-in-place; no send storm |
| Review | pick ≤3 candidates for next week | owner |

## Arm gates for real talk (model)

| Flag / knob | Meaning | Before arm |
|---|---|---|
| `OCTOPUS_WIRE_COLLAB=1` | collaborator surfaces | tests green |
| `OCTOPUS_COLLAB_USE_MODEL=1` | model_router via adapter | Gate A: intro works stub+mock |
| `OCTOPUS_COLLAB_MODEL_DAILY_CAP` | soft call cap (default **30**) | write number in this table before live |
| Organ / budgets.yaml | organism AUD caps still apply | monthly AUD 30 global |
| Kill / STOP | existing kill_seam | leave intact |

**Suggested first live arm (owner vote required):**

```text
OCTOPUS_WIRE_COLLAB=1
OCTOPUS_COLLAB_USE_MODEL=1
OCTOPUS_COLLAB_MODEL_DAILY_CAP=20
```

Then **restart** telegram/miniapp processes and confirm boot snapshot.
Do **not** arm money/lead/harvest with this protocol.

## Evidence ladder

STRUCTURAL → TESTED → SHADOW → ARMED (see [[_ops/EVIDENCE-LADDER|EVIDENCE-LADDER]]).
Journal column `level` must match ladder; claiming ARMED without boot snapshot is forbidden.

## Truth line

```text
owner↔octopus discovery loop + capped collab model
!= mass-flag-arm != vision-done != unbounded-auto-send
```
