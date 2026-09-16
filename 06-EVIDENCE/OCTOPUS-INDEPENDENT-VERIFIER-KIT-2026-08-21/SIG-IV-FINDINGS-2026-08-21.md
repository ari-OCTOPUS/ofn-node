---
type: evidence
date: 2026-08-21
scope: sig-iv-megaprompt-1
exact_verified_head: bfbb03f36a6510eafe6d4910625895a127c14e7c
verdict: SECURITY_SHADOW_PASS
---

# SIG-IV — Megaprompt 1 findings (2026-08-21)

Independent identity: `sig-iv-0a7b37c5-independent-20260821`.
Attestation: [[INDEPENDENT-SESSION-ATTESTATION]].
Machine verdict: [[INDEPENDENT-VERDICT.json]].
Required output: [[MEGAPROMPT-1-REQUIRED-OUTPUT.json]].

## Ancestry (measured)

- `fa38d16` ⊂ `d301339` ⊂ live line via `94fa59f` (organs restore) ⊂ … ⊂ **`bfbb03f`** ⊂ live HEAD `9223507`.
- Kit descendant `cc267048` is a **parallel** child of `d301339` (branch `repair/organs-suite-reproducible-20260821`), not an ancestor of `bfbb03f`. Merge-base with live HEAD = `d301339`.
- Organs blobs at `cc267048` / `94fa59f` / `bfbb03f` are **identical**.
- `git diff bfbb03f HEAD -- _ops` is **empty**. Live `_ops` at HEAD matches verified head.

Owner allowed `cc267048` **or** a newer child such as `bfbb03f` after reproducing the 163. This run used **`bfbb03f`**.

## Suites

163/163 at exact head `bfbb03f…` in sparse worktree `F:\backup\.claude\worktrees\sig-iv-bfbb03f`.
Worktree production-path delta: `[]`.

## Side effects

- Attempt 1: send-log +1 row, `stream=edit`, classified live-center background → `FAILED_SAFE` (preserved).
- Attempt 2 (retry2): memory ingest, miniapp hits, and send-log **byte-identical**. `delta_rows=0`.

## C3 / C4 (code at worktree)

- `TgClient._defer_queue = None` until `attach_defer_queue`.
- `center.py` has **no** `sender_bridge` / `SenderBridge` / `attach_defer` matches.
- Message keys: SHA-256 hex (64) of sendMessage chat+text; non-send methods return `None`.
- `retry_after` parsed in full; sync sleep capped; long sendMessage prohibitions durable-deferred.
- Crash after transport → `UNCERTAIN_SEND_OUTCOME`; no auto-resend in fixtures.

## Next state

`authorized_next_state = WAVE1_CANARY_READY`.

This does **not** authorize a live Telegram send, webhook, or paid call.
Megaprompt 2 (single-message canary) still needs an explicit owner gate.
