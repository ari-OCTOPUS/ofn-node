---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 2 — Alignment & Governance Reviewer: HITL + Anchor Ledger

Role: reviewer of the explicit rules the system checks its own outputs against, and of whether human
verdicts are an irreversible, tamper-evident root of trust that no agent or config path can act
above.

## Explicit self-check rules (what exists)
1. Output guardrail `src/guardrails.py:14-21` — rejects empty/short output and "suspicious claim
   without a verification caveat" via keyword lists (`SUSPICIOUS`, caveat terms). Keyword-level only.
2. Panel stances `src/panel.py:14-20, 33-42` — strict/lenient/balanced, but decided by Python
   heuristics, not the model (see Pass 1 P1-08 / Pass 4).
3. Grounding gate `igk/kernel.py:135-171` against `held_out.json` — advisory by default (Pass 1 P1-04).
4. Prompt self-update guardrail `self_update.py:45-59` + allow-list `src/evals.py:96-106` — governs
   only prompt text mutations.

These are the "constitution as code." All are heuristic/keyword or structural; none is a semantic
verifier. [Certain]

## Findings

### P2-01 [High] Human verdicts are written to the UNSIGNED audit log — not a tamper-evident root of trust
The HITL gate records the human decision via `AuditLog` (`src/hitl.py:27-32`,
`self.audit.log("hitl_decision","human-gate",...)`). `AuditLog` (`src/tracing.py`) is a hash chain
using **plain SHA-256 truncated to 16 hex chars** with **no secret key** (`src/tracing.py:53-55`).
Because the algorithm is public and unkeyed, anyone who can write `logs/audit.jsonl` can edit a past
`hitl_decision` (e.g. flip `approved:false`→`true`), then recompute every subsequent hash, and
`verify_chain()` (`src/tracing.py:74-90`) will report the file as intact. The only signed log is the
IGK kernel's own `logs/igk_state/audit.jsonl` (HMAC, `igk/kernel.py:62-63,76-84`), and it records
`permit_issued`/`actuation` for finalize — **not the human APPROVE/REJECT content**. Therefore the
irreplaceable artifact (the human verdict itself) has no cryptographic protection. This is a
forensic-integrity failure, not a live-bypass (live actuation is still gated by `consume`), so
High, not Critical. [Certain]

### P2-02 [High] There is no dedicated append-only "Anchor Ledger" for human verdicts
The task's "Anchor Ledger" maps, in this repo, to three partial artifacts: the held-out grounding
anchor (`igk/held_out.json`), the signed kernel audit, and the versioned prompt store
(`prompts.json`). None is a purpose-built, append-only, tamper-evident ledger of human root-of-trust
verdicts. Human decisions land in the unsigned main log (P2-01). "Append-only" is by convention
(`open(..., "a")`) only — nothing enforces it and nothing signs it. [Certain]

### P2-03 [Medium] Verdicts are bound to a string actor, not to any human identity or signature
`HITLGate.request` passes `actor="human-gate"` as a literal (`src/hitl.py:27,30`). Any code holding
the shared `AuditLog` instance can emit a forged `hitl_decision`/`approved:true` record; nothing
binds a verdict record to an actual human input event or to a credential. Combined with P2-01, a
fabricated approval is indistinguishable from a real one in the log. [Certain]

### P2-04 [Medium] The HITL gate can be satisfied programmatically by an injected approver
`Orchestrator(hitl_approver=...)` accepts any callable (`src/orchestrator.py:34,53`). `run.py`
wires `--auto-approve` → `lambda: True` (`run.py:36-38`). This is intended for tests, but it means
"human above the gate" is only true when no auto-approver is injected. Any caller constructing the
Orchestrator can pass an always-approve function and the finalize gate becomes a no-op (the IGK
`consume` still runs, but `consume` does not represent human consent — it only checks STOP + permit
validity). [Certain]

### P2-05 [Medium] `external_write` is declared sensitive but never gated anywhere
`config.py:40` `HITL_REQUIRED_FOR = {"finalize","external_write"}`, yet `grep` shows `external_write`
appears only in `config.py`; no code path ever calls `hitl.request("external_write", ...)` or
`gate.act("external_write", ...)`. The only real HITL gate is `finalize` (`src/orchestrator.py:123`).
The declared control for external writes is aspirational. [Certain]

## What sits correctly above agents (positive)
- Panel-split → mandatory human escalation (`src/orchestrator.py:103-109`). [Certain]
- Finalize always requires approval in default config because `finalize ∈ HITL_REQUIRED_FOR`
  and the gate is unconditionally consulted before actuation (`src/orchestrator.py:123-131`). [Certain]
- No agent imports the HITL gate; only the orchestrator invokes it. [Certain]

## Gaps I could not verify
- Whether, in a real deployment, the console approver (`src/hitl.py:35-43`) is ever replaced by a
  weaker approver — depends on the caller, not visible in-repo.
- Any external/off-box copy of the audit log that might restore tamper-evidence — none referenced.
