---
title: REAL-WORK-BRIDGE-20260913
lane: API-BUDGET-ACTIVATION-20260913
owner_order: "STOP ARTIFICIAL OPERATIONAL TASKS — connect autonomy to real work"
final_status: REAL_WORK_BRIDGE_ACTIVE
paid_spend_this_directive: "$0.0002 (one admission-gate self-test call, corrected in ledger)"
secrets_exposed: none
---

# REAL-WORK-BRIDGE — live queue now admits real work only

## Gates installed (deterministic, no LLM decides evidence existence)

| Gate | Where | Behavior |
|---|---|---|
| Task provenance | `coding_worker.py` (both enum and free-form paths) | a task without `provenance.class ∈ REAL_*` + `source` + `source_ts` + `source_hash`, or with `fixture=true`, is rejected `TASK_REJECTED_NO_REAL_WORLD_PROVENANCE` before any cognition. Verified live: no-provenance → `rejected` + receipt; with-provenance → passes to cognition |
| Paid purpose | `api_budget.paid_call()` | heartbeat / status-report / formatting / translation / fixture / demo / polling / waiting / activity purposes → `PAID_COGNITION_NOT_JUSTIFIED`. Verified live |
| Duplicate prompt | `api_budget.paid_call()` | same task + context-hash + provider already reserved → `PAID_DUPLICATE_PROMPT` (reserve rows now carry the prompt context hash). A *different* provider stays allowed for genuine second-model review. Verified live |

Live coding queue inspected: **empty** — no artificial task was sitting in it. Historical
artificial-task evidence was not deleted (directive §1).

## Reality dashboard (2026-09-13 ~04:4xZ)

| task | source | real class | state | next action | API spend | outcome |
|---|---|---|---|---|---|---|
| TASK-OPS-BUDGET-CATSCOPE-005 | deployed defect, patch packaged | REAL_CODE_DEFECT | WAITING_B8_BUDGET | auto-fire at 2026-09-14T01:49:08Z (BUDGET_NODE_24H frees); patch NOT regenerated | $0 | pending canary |
| PRED-E0E80E1D-RECONCILIATION | prediction-ledger row | REAL_PREDICTION_DUE | WAITING_DUE 06:30Z | automatic reconcile (deterministic) | $0 | pending |
| B5-STORAGE-MAINTENANCE-BREAKER | failure-signatures (cache-regen race) | REAL_CODE_DEFECT | OPEN (2nd root cause) | deterministic diagnosis; fix → B8 | $0 | open |
| NODE-138-FAILOVER-LEASE | single-executor SPOF | REAL_RUNTIME_INCIDENT | DESIGN_PENDING | lease+fencing design lane | later | open |
| WILD-IO-CONTENTION | dual-verifier timing evidence | DERIVED_FROM_REAL_EVIDENCE | LAB_READY | next WILD tournament | $0 | open |
| GITHUB-AUTONOMY-BOT | gh 422 deploy-keys-disabled | REAL_GITHUB_WORK | BLOCKED_OWNER_TOGGLE | wake = owner toggle/PAT; local git continues | $0 | blocked (owner) |
| ANTHROPIC-WORKSPACE-SCOPE | provider 400 → fixed via workspace id | REAL_CODE_DEFECT | **RESOLVED today** | none (superseded) | $0.00052 (canary) | LIVE |
| SAKANA-USAGE-LIMIT | HTTP 429 | REAL_RUNTIME_INCIDENT | PROVIDER_LIMITED | skipped by name; retries off; no IP probing | $0 | waiting provider |
| EXPOSED-CREDENTIAL-ROTATION-REVIEW | exposures on record | REAL_SECURITY_FINDING | **REVIEWED today** | owner actions below | **$0** | completed |
| NODE-191-RETIRED | SSH refused | STALE | NO_TASK | none; no repeated SSH | $0 | archived |

Registry: `state/coding-worker/real-backlog.json` (schema `octopus.real-backlog.v1`).

## Live proof — the completed real task (deterministic, zero paid API)

**EXPOSED-CREDENTIAL-ROTATION-REVIEW** (`rotation-review-20260913.json`):

1. **Chat-pasted Claude key — HIGH.** Exposure surface is an external chat transcript, outside
   organism control. OCTOPUS never read, stored or used it (verified: not in the secure file,
   758-file scan clean). *Provider-side action (owner): delete key
   `apikey_01HYoiWGnN2BiBxvDMiy8FD3`.* Deletion suffices — the organism runs on the in-file
   credential.
2. **Local backup-file window — MEDIUM.** `secrets.env.bak-*` were mode 644 from 2026-08-22
   until the 2026-09-13 hardening (local node-138 users only; `/home/ari` was 755). Contained:
   all files now 600. Misuse signals in ops receipts: **0** (absence of evidence, not proof).
   *Optional owner rotation*: `OFN_BOT_TOKEN_*` (5), `OFN_SHOPIFY_ADMIN_TOKEN`,
   `OFN_SHOPIFY_CLIENT_ID/SECRET`, `GMAIL_APP_PASSWORD`, `OFN_SESSION_SECRET`,
   `OFN_REMOTE_API_KEY`.
3. **`identity.json` at 644 — NONE.** Name-level scan found no credential variable inside.

Why paid API was not required: every step is a deterministic file-mode/hash/receipt scan —
exactly the directive's §5 gate ("deterministic logic cannot solve it" is false here).

## Honest ledger note

One admission-gate self-test consumed a single deepseek call (~$0.0002, task `gate-test-2`).
Its test purpose string (`real-defect-fix`) was misleading, so a `correction` receipt row was
appended naming it a SELFTEST, not real work. Everything else in this directive cost $0.

## Next automatic real event

`PRED-E0E80E1D` reconciliation at **2026-09-13T06:30:00Z** (deterministic, $0), then the
**B8 canary** for the budget-scoping patch at **2026-09-14T01:49:08Z** (witness-gated, $0).
