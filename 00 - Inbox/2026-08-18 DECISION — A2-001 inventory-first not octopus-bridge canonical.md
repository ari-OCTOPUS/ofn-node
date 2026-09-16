---
type: knowledge
status: inbox
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2, a2-001, inventory, canonical, wave0]
sources:
  - "[[../02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
  - "[[../06-EVIDENCE/A2-001-CANONICAL-DECISION-2026-08-18]]"
  - "[[../04-SYSTEMS/OFN-NODE]]"
---

# DECISION — A2-001 inventory-first; octopus-bridge is not canonical

`.191` **refuses to rubber-stamp `octopus-bridge`** as the canonical repo for A2-001. Inventory gate first. Guessing the path is forbidden.

Proposal origin `.138` is accepted for **order** (verifier before memory). `.138` does not choose the tree. Execution remains intended for Lab `.180` **after** `.191` has exactly one proven path that matches vault SoT.

**This session verdict: `UNKNOWN_CANONICAL`.** Implementation halted. No worktree, no schemas written, no CLI.

Canonical block: [[../02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]. Inventory table: [[../06-EVIDENCE/A2-001-CANONICAL-DECISION-2026-08-18]]. Earlier first-task lock (still: `.180` not started): [[2026-08-18 DECISION — A2 lab first task = mirror manifest verifier]].

## Why inventory failed the one-path rule

On this laptop there is **not** a single A2-001 home:

1. Live vault `F:\backup\octopus-bridge\` = two-file OFN stub. No `schemas/`. No `mirror_verify.py`. Vault SoT already says stub / board package — [[../04-SYSTEMS/OFN-NODE]] · [[../00 - Inbox/2026-08-15 REPORT — Forgotten Gaps for Next Agent]].
2. Germline branch `ofn/bridge` (`e21f20d`) = a **different** full `octopus_bridge/` package at repo root (board half). Also no `schemas/`, no `mirror_verify.py`.
3. Owner assumed an empty `octopus-bridge/schemas/`. That directory **does not exist** here.

Zero A2-001-shaped trees (schemas + `mirror_verify.py`). More than one plausible "octopus-bridge" root. No owner-documented SoT in this vault that A2-001 lives in `octopus-bridge`. Stop.

## Binding (short)

- STATUS OWNER-APPROVED-PROPOSAL · EXECUTION NODE `.180` · PROPOSAL ORIGIN `.138` · CANONICAL AUTHORITY `.191`
- A2_SANDBOX_ONLY · WAVE0_OBSERVE_ONLY · EFFECT NONE
- Order: A2-001 now → A2-002 Envelope v2 later → A2-003 Memory Write Contract **draft only** later
- Receipt hash-chain = `integrity_hint: hash-chain-unkeyed` only; no HMAC/keys
- Promotion never automatic
