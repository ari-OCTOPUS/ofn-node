---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# AUDIT — Fusion MVP Architectural Security Audit (consolidated)

Read-only, evidence-based audit of `.../04 - Architect System/architect/_code/ai-farm/fusion-mvp`.
Priority order followed: IGK kernel → HITL/kill-switch/audit → LANGAR → orchestrator. No code was
modified. Every finding cites file:line and carries a certainty tag. Severity scale:
Critical / High / Medium / Low.

## Findings table

| ID | Sev | Certainty | Location | Finding (evidence) |
|---|---|---|---|---|
| P1-01 / P4-02 | High | Certain (path) / Probable (attacker) | `src/orchestrator.py:42-49` | Broad `except Exception` on IGK spawn silently downgrades to cooperative mode; actuation gate (`:130-131`) and grounding (`:114`) are then skipped while the run still finalizes. Primary "external, fail-closed" guarantee lost with only a console warning. |
| P2-01 | High | Certain | `src/hitl.py:27-32` + `src/tracing.py:53-55` | Human APPROVE/REJECT is written only to the **unsigned** `logs/audit.jsonl` (unkeyed SHA-256, 16-hex). Anyone who can write the file can edit a verdict and recompute all later hashes; `verify_chain()` still passes. The claimed root-of-trust artifact has no cryptographic protection. Forensic gap (live actuation still gated by signed `consume`). |
| P4-01 / P6-07 | High | Certain | `src/panel.py:44-53` (vs `:33-42`) | Judge panel pays for a provider LLM call, then **discards** `res.text` and votes via Python string heuristics. Provider "diversity" is illusory and judge-model failure/refusal is invisible — undermining control #5 (no single point of decision) and wasting LIVE tokens. |
| P1-02 | High | Probable | `igk/kernel.py:43-54, 86-100` | `_load_or_make_key` regenerates a fresh key if `.kernel_key` is absent; `verify()` checks against the current key. Deleting the key + rewriting the chain yields a chain that verifies as "intact." No external key attestation/fingerprint. |
| P1-03 | Medium | Certain (boundary) / Guess (future) | `igk/kernel.py:41-42`; `igk/README.md:17-18`; `src/tools.py:24-26` | Key isolation is process-level only; on one OS user any process with file access can read `.kernel_key`. Not reachable today (no file/shell tool registered), but becomes High the instant such a tool is added. |
| P1-04 | Medium | Certain | `config.py:59`; `src/orchestrator.py:114-120`; `logs/igk_state/audit.jsonl` seq1 | Grounding is advisory by default (`GROUNDING_REQUIRED=False`) and, when enabled, validates raw Researcher findings against a geography/science held-out set → ratio ~0.0 on normal runs, i.e. it would halt every run. Control is effectively inert/mis-wired. |
| P1-05 | Medium | Certain | `src/orchestrator.py:73-79`; `src/killswitch.py:26-28` | Under IGK, `_kguard` consults only the external STOP file, not the in-memory `KillSwitch.trip()`. The two stop paths are not unified; a programmatic trip is invisible at the orchestrator boundary (still honored in `agents`/`panel`, and no prod code calls `trip()` — latent). |
| P1-07 | Medium | Probable | `src/orchestrator.py:36,45`; `test_igk_integration.py:20-23` | `config` is a mutable module used as live kernel configuration. In-process code that sets `config.IGK_STATE_DIR` before Orchestrator construction can relocate the kernel to an attacker-owned state dir (own `.kernel_key`/`held_out.json`/audit). |
| P2-02 | Medium/High | Certain | repo-wide | No dedicated append-only, tamper-evident **Anchor Ledger** for human verdicts; "append-only" is convention (`open(...,"a")`) and unsigned. |
| P2-03 | Medium | Certain | `src/hitl.py:27,30` | Verdicts bound to the literal string actor `"human-gate"`, not to any human identity/signature; any holder of the `AuditLog` can emit a forged `hitl_decision`. |
| P2-04 | Medium | Certain | `src/orchestrator.py:34,53`; `run.py:36-38` | HITL gate is satisfiable by an injected `hitl_approver` (`--auto-approve` → `lambda:True`); "human above the gate" holds only when no auto-approver is passed. |
| P2-05 | Medium | Certain | `config.py:40` | `external_write` declared HITL-required but never gated by any code path (only `finalize` is). Claimed control does not exist. |
| P4-03 | Medium | Certain | `config.py:27` | `MAX_STEPS` declared, never enforced (no loop bound in orchestrator). Claimed safety limit does not exist. |
| P4-04 | Medium | Certain | `src/agents.py:78-86`; `src/orchestrator.py:100` | `Supervisor.review` is dead code (panel replaced it) yet still built and documented as the decider — auditability/correctness hazard. |
| P5-01 | Medium | Certain | `logs/audit.jsonl` vs `logs/igk_state/audit.jsonl` | Two audit chains, different integrity (unkeyed vs HMAC), with no cross-reference; a full timeline can only be merged by unauthenticated timestamp. Source-of-truth is split and partially signed. |
| P5-02 | Medium | Probable | `src/tracing.py:24,33-42`; `self_update.py:64` | In-memory chain head + two `AuditLog` instances on the same default file → interleaved writes corrupt `verify_chain()`. Single-writer assumption undocumented, no lock. |
| P5-03 | Medium | Certain | `igk/held_out.json`; `logs/igk_state/held_out.json` | Grounding anchor duplicated with no canonical loader; editing one diverges "grounded" meaning by entry point. |
| P6-01 | Medium | Certain | `igk/client.py:22-26` | Blocking `readline()` on kernel IPC with no timeout/watchdog; a hung daemon hangs the orchestrator indefinitely and defeats kill-switch latency. |
| P6-02 | Medium | Certain | `src/orchestrator.py:26-30, 47-49` | Broad `except Exception` swallows errors on security-relevant paths (import stub for `PermitDenied`; IGK downgrade). |
| P6-03 | Medium | Certain | `igk/kernel.py`/`daemon.py`; `src/agents.py` | Untyped dict/str interfaces between kernel↔client and agent↔agent; key typos degrade to silent `None`; no structured claim type. |
| P1-06 | Low/Medium | Certain | `src/orchestrator.py`; `src/llm.py:40-45` | STOP honored at checkpoints, not "instantly"; a synchronous LLM call cannot be interrupted mid-flight. README "آنی/instant" overstated. |
| P4-05 | Low/Medium | Certain | `src/orchestrator.py:96,110-120` | Guardrail/panel-reject/grounding failures halt (fail-closed, safe) but do not escalate to HITL; only panel-split and finalize do. |
| P5-04 | Low/Medium | Certain | `igk/kernel.py:38,112` | Per-run budget/nonce state is memory-only; after a crash it cannot be reconciled against the logs; cross-restart replay bounded only by 30s permit expiry. |
| P6-04 | Low/Medium | Certain | `test_igk_integration.py:20-23`; `test_phase3.py:57` | Test isolation via unrestored global `config` mutation; possible cross-test contamination in-process. |
| P4-06 | Low | Certain | `src/langfuse_sink.py:38-57` | Telemetry exceptions swallowed by design; silent observability loss. |
| P5-05 | Low | Certain | `src/prompt_store.py:74-81` | `rollback` has no floor/safety validation of the reverted version. |
| P6-05 | Low | Certain | `run.py:19-28`; `self_update.py:23-31`; `smoke_live.py:22-30` | `_load_env` duplicated 3× with inconsistent quote-stripping. |
| P6-06 | Low | Certain | `src/tracing.py:54` | Audit hash truncated to 64 bits; below modern norms (rewrite attack needs no collision, but needless weakness). |

**Severity counts:** Critical 0 · High 4 (counting P1-01/P4-02 as one, P4-01/P6-07 as one) ·
Medium 14 · Low/Low-Medium 7. (Cross-listed IDs counted once.)

## What could NOT be verified (and why)
1. **LIVE mode** — no API key (moved out today), sandbox offline; all real-provider branches
   (`src/llm.py:40-52`, `src/providers.py:21-22`) unexercised.
2. **Git history for pre-move secret exposure** — `git` was not accessible from the workspace mount
   for the vault path ("not a git repository" at mount boundary). Current `.gitignore` posture is
   correct, but historical commits are unverified.
3. **OS/TEE key isolation** — single-machine assumption, not testable here.
4. **Secret values** — `.env`, `.kernel_key` moved out; correctly not read (no values cited).
5. **LANGAR bot** — not in the granted repo path; a sibling `_code` project
   (`.../ai-farm/AI-sume/langar-pro/`) outside the read exception (Pass 3). Priority-3 unmet.
6. **Real concurrency** — suite is single-threaded; P5-02/P6-01 are reasoned, not observed.

## Overall posture
The safety architecture is unusually thoughtful for an MVP: a genuine process-separated kernel with
HMAC-signed audit, permit/consume with nonce+expiry, fail-closed actuation, multiple independent
stop authorities, injectable HITL, and a versioned prompt store with an allow-list guard. The
red-team suite passes 8/8. The material risks are not "missing controls" but **silent degradations
and false-assurance gaps**: an IGK downgrade that removes the strongest control on any error
(P1-01), a human-verdict record that is not cryptographically protected (P2-01), a judge panel whose
LLM verdicts are discarded (P4-01), and several declared-but-unimplemented controls
(P2-05, P4-03) plus split sources of truth (P5-01/P5-03). Fixing the top handful converts the
system from "looks fail-closed" to "is fail-closed."
