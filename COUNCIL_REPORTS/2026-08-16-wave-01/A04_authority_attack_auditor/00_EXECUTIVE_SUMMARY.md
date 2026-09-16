# A04 — EXECUTIVE SUMMARY

**Agent:** A04_authority_attack_auditor · **Mode:** READ_ONLY · **Date:** 2026-08-16
**Verdict (end of report):** `READY_FOR_NEXT_WAVE` (with 4 REQUIRES_OWNER_DECISION items)

## What was audited
All authority-reaching surfaces of OCTOPUS (`F:\backup`): shell/subprocess, filesystem writers, Telegram cockpit + approvals, loopback HTTP servers (8770-8778, 8787) and the single non-loopback board control plane (:8801), provider egress, MCP, memory/vault RAG, web research, code-autonomy/self-patch, secrets handling, prompt-injection boundaries, recovery paths, and the wiring status of every declared policy choke point. 38 evidence rows (03_EVIDENCE.jsonl), 31 findings (02_FINDINGS.md). Organism observed LIVE during audit (beat 38516, state mutations within 60 s of observation).

## The single most important truth
**OCTOPUS's real authority model is federated module-local gates, not the documented central Policy Gate.** The two strongest, best-designed choke points — `octopus_v3.P0ExecutionGate` (kill→taint→owner-approval→budget→lease→INTENT-ledger) and the `containment/` G8 package — are `WIRED=False` with zero live consumers. The live ADR-033 PolicyGate enforces only two paths: `protective_halt` and the collaborator **draft** path. Every consequential executor (raw shell, code-apply, outbound email, OpsActionEngine, restart/power) is protected by its own deterministic checks (activation flags, kill files, owner chat-id, allowlists, approval stores) — real, but with no shared enforcement point, so a bug in any one module's gate is a system-level hole. The repo is honest about this (docstrings declare WIRED=False); documents that imply central enforcement overstate reality.

## Top findings
1. **HIGH — Raw shell armed & reachable:** `/sh <cmd>` (owner-only Telegram) → `subprocess.run(shell=True)` at repo root, beside live `.env`. Regex deny-list doesn't cover `python -c`/`pip`/file-redirection into source. Never executed so far (no audit rows). (F-001, F-002, E-001..E-004)
2. **HIGH — Dead central gates:** P0ExecutionGate + containment/G8 unwired; PolicyGate coverage narrow. (F-003, F-004, F-006, E-006..E-010)
3. **HIGH — Maximal armed posture:** all 15 activation flags on (RAW-SHELL, CODE-AUTONOMY, SELF-IMPROVE-AUTO, REPLICATION, GO-LIVE…); only STOP-CODE-AUTONOMY present as counterweight. Single owner-auth failure ⇒ shell+secrets exposure. (F-015, E-017)
4. **MEDIUM — Unfenced web→brain path:** `web_research` (flag-gated, default off) fetches search-result pages with no allowlist/SSRF/size checks; content enters `improve()`/synthesis context with no UNTRUSTED fence — inconsistent with the repo's own `fetch_guard`/`public_web` hardening. (F-009, E-021, E-022)
5. **MEDIUM — Memory/vault RAG unlabelled:** live (`OCTOPUS_WIRE_VAULT_RAG=1`); snippets reach reasoning prompts with no trust/provenance markers. (F-010, E-023)
6. **MEDIUM — Approval semantics:** PolicyGate checks approval_id presence only; Telegram callback HMAC binding exists but its flag is default-off; two independent PolicyGate implementations acknowledged in-repo as INV-4 divergence. (F-005, F-023, F-025)

## What is actually solid (worth saying)
Deterministic owner auth (env chat-id, fail-closed, silent non-owner drop); loopback-only servers with CSRF guard default-on; `output_guard` inert-artifact policy; `target_guard` resolve-containment; 8-gated code-apply with self-protective deny-list; effect legs genuinely propose/intent-only or default-off (mining = intent file only, SMTP behind flag+consent+staleness, PocketSmith/writeback off); recovery paths only degrade authority (fugu→glm→local→None, auto-freeze on canary red); ledger live and hash-chained; `identity_health` live (0.542); chat authorizations recorded but never executed.

## Stop-rule assessment
No path found where **untrusted** input reaches a consequential side effect **without a deterministic authorization boundary**: web/memory content bottoms out in propose-only flows (owner tap + shadow-green required); shell/restart/OpsActionEngine require deterministic owner chat-id / initData-HMAC / Bearer gates. Deny/allow lists are weak in places but deterministic. **Not CRITICAL_SAFETY_BLOCK.** The untrusted→effect *buffering*, however, rests on per-module convention in several spots — the reason the dead central gates matter.

## Owner decisions requested
OD-A: wire or formally retire octopus_v3 gate + containment/G8 (one choke point, or document federation as the design). OD-B: harden/disarm raw shell (see 06_RECOMMENDATIONS). OD-C: enable OCTOPUS_WIRE_CB_TOKEN (HMAC callback binding). OD-D: reconcile the two PolicyGate implementations and the unfenced web_research path with fetch_guard.

READY_FOR_NEXT_WAVE
