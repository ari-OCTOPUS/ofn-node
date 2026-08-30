# A04 — CRITICAL SAFETY FINDINGS

## Stop-rule determination
**CRITICAL_SAFETY_BLOCK: NOT triggered.**

The rule fires if untrusted input can cause a consequential side effect **without a deterministic authorization boundary**. Systematic check of every untrusted source:

| Untrusted source | Furthest reachable point | Deterministic boundary that stops it |
|---|---|---|
| Web content (web_research) | improve()/synthesis **proposals** | owner tap + shadow-green + target allow-list before any apply |
| Vault notes / memory (RAG live) | evidence snippets in prompts | effects remain propose-only / owner-gated |
| Lead emails | lead pipeline cards | outbound flag OFF + consent + staleness refuse |
| Non-owner Telegram | nothing | `handle_update` from.id drop (deterministic, pre-handler) |
| LLM output | drafts, patch proposals, sandbox commands | output_guard, allow/deny lists, approval store, owner gates |
| Board/agent inputs | queue entries | TLS/Bearer/HMAC-signature gates (fail-closed) |

Deny/allow lists are weaker than their intent (see B-1/B-2) but they are *deterministic* boundaries in the rule's sense. No unauthenticated untrusted→effect path exists.

## Findings classified CRITICAL by consequence-if-auth-fails (owner-scope, not outsider-scope)

### CS-1 · Armed raw shell adjacent to live secrets (HIGH)
`/sh` = `shell=True` at repo root, `.env` in cwd, regex charter deny-list with known semantic gaps (`python -c`, `pip`, file writes; library-level network egress not blocked). Protected solely by owner Telegram identity. Zero uses so far. — E-001..E-004. Owner decision OD-B.

### CS-2 · All capability flags armed simultaneously (HIGH posture)
15/15 ACTIVATION flags present incl. RAW-SHELL, CODE-AUTONOMY, SELF-IMPROVE-AUTO, REPLICATION, GO-LIVE. Any single future wiring bug inherits a fully armed organism. Counterweights today: STOP-CODE-AUTONOMY only (+ env flag defaults off for money paths). — E-017. OD-B + flag-hygiene review.

### CS-3 · Central authority gates unwired (HIGH governance)
P0ExecutionGate WIRED=False; containment/G8 consumer-less; PolicyGate live on 2 narrow paths; approval_id presence-only. The architecture that documents "no execute before INTENT ledger + owner approval" is exactly the part not running. — E-006..E-010. OD-A.

## Not safety-critical but tracked
CS-4 unfenced web/vault→brain (MEDIUM, F-009/F-010) · CS-5 `.env.bak` at root (MEDIUM, F-014) · CS-6 callback HMAC dormant (MEDIUM, F-023) · CS-7 board_cp 0.0.0.0 bind (LOW-MED, F-028).

## What would flip this report to CRITICAL_SAFETY_BLOCK
Evidence of any of: (a) a live beat writer that can create/delete `_ops/STOP-*`/`ACTIVATION-*`; (b) any wiring of PolicyGate/P0 with unverified approval_id on an effect path; (c) `OCTOPUS_WIRE_WEB_RESEARCH` or sandbox drivers enabled without fences while cortex output can reach `command_runner` without owner tap; (d) non-owner chat-id passing `_is_owner` in the running process. Waves 2+ should re-test (a) specifically (Q6).
