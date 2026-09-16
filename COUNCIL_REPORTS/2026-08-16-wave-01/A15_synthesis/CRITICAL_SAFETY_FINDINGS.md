# CRITICAL SAFETY FINDINGS — A15 Consolidated (Wave 01)

## Stop-rule determination (A04, confirmed by A02/A03)

**CRITICAL_SAFETY_BLOCK: NOT triggered by any agent.** Systematic untrusted-source → effect chain check found a deterministic authorization boundary on every path (A04 critical-findings table; A03 critical_condition answer=false). All four agents returned READY_FOR_NEXT_WAVE.

Flipping conditions for future waves (re-test each wave, esp. Wave 2/3):
(a) a live beat writer that can create/delete `_ops/STOP-*`/`ACTIVATION-*`;
(b) any wiring of PolicyGate/P0 with unverified approval_id on an effect path;
(c) web-research/sandbox drivers enabled without fences while cortex output can reach `command_runner` without owner tap;
(d) a non-owner chat id passing `_is_owner` in the running process.
— A04#CS-table

## Consolidated HIGH/owner-scope findings (consequence-if-auth-fails)

### CS-1 · Armed raw shell adjacent to live secrets (HIGH)
`/sh` Telegram owner command → `shell_capability.run()` → `subprocess.run(shell=True)` at repo root with `.env` in cwd. Guard = owner chat-id + regex deny-list with known gaps (`python -c`, pip, file writes, library-level network not blocked). Activation flag present (owner verdict 2026-08-04 on file). **Zero executions recorded** in raw-shell-audit. Chain: Telegram account or bot-token compromise → full host shell. — A04#F-001..F-004, A03#BP-01, A02#R-014. **Owner decision OD-B.**

### CS-2 · Central authority gates documented but unwired (HIGH governance)
P0ExecutionGate (INTENT ledger, capability lease, taint latch, HARD_NO_GO) `WIRED=False`; containment/G8 has no live consumers; live PolicyGate covers 1–2 narrow paths; approval_id presence-only. The architecture that claims "no execute before INTENT ledger + owner approval" is exactly the part not running. Today's safety is structural absence of executor paths — new effector code silently inherits "allowed". — A04#F-006..F-010, A02#R-010/R-007. **Owner decision OD-A.**

### CS-3 · All capability flags armed simultaneously (HIGH posture)
15/15 ACTIVATION flags present incl. RAW-SHELL, CODE-AUTONOMY, SELF-IMPROVE-AUTO, REPLICATION, GO-LIVE; AUTONOMY_FREE/GRANT/CODE_AUTOAPPLY_LOWRISK/LEAD_OUTBOUND armed. Counterweights today: STOP-CODE-AUTONOMY + env-flag defaults for money. One wiring bug inherits a fully armed organism. — A04#F-017, A02#F-12.

### CS-4 · Unfenced untrusted text reaches prompts (MEDIUM)
Web-research content and vault-RAG evidence enter improve()/synthesis context without the DATA_NOT_INSTRUCTION fence (fence partial). Effects remain propose-only/owner-gated, so severity is MEDIUM — but this is the primary prompt-injection vector to close before any autonomy expansion. — A04#F-009/F-010.

### CS-5 · Secrets posture (MEDIUM)
`.env` (gitignored/untracked ✓) holds 3 Telegram bot tokens, Gmail app password, provider keys; stale plaintext `.env.bak-20260810` at repo root. Values were never read by any agent. — A04#F-014, A02#R-016.

### CS-6 · Lead-email lane outside action_bridge (MEDIUM)
Executes per-effect owner authorization (consent, staleness, recorded price) but bypasses the unified gate; capability is env-removable. — A03#BP-05.

### CS-7 · Ungated LLM → 4d research memory write (MEDIUM)
LLM writes persist into 4d research memory without a gate — a poisoning vector, no execution authority. — A03#BP-08.

### CS-8 · Public + LAN exposure (MEDIUM)
Named tunnel `app.master-painting.com` → 8774 (HMAC owner wall — acceptable but internet-reachable); board_cp 0.0.0.0:8801 TLS+Bearer — bind default should be narrowed. — A02#R-014, A04#F-028.

## Operational incident (not security, but safety-relevant)

**FREEZE.flag budget-settle failure (20:09:05, Errno 22 on budget-state.json)** — organism frozen by fault; budget grants fail-closed; month spend AU$0.74. Repair is owner/Windows-level, not policy. — A01 rider, A02#R-015.

## Owner decisions requested (from A04)

OD-A: wire-or-retire central gates (P0ExecutionGate/containment) · OD-B: raw-shell posture · OD-C: enable OCTOPUS_WIRE_CB_TOKEN · OD-D: route web_research through fetch_guard.
