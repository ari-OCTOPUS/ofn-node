---
title: GOV-FREEDOM-V2
authority: OWNER DIRECTIVE (verbatim, 2026-09-13)
subject: OPERATIONAL FREEDOM EXPANSION V2 — reduce friction, increase autonomous authority
supersedes: friction defaults only — never the RED boundaries, never TCB integrity
implementation_status: PHASE_1_DEPLOYED (see Implementation Record)
status: active
---

# GOV-FREEDOM-V2 — Operational Freedom Expansion (owner authority addendum)

> **Owner instruction (verbatim header):** «کاملا ازادش کن» — "REDUCE FRICTION, INCREASE
> AUTONOMOUS AUTHORITY. Target: HIGH-FREEDOM OPERATIONAL AUTONOMY. The owner explicitly
> authorizes OCTOPUS to proceed autonomously on ordinary internal, non-TCB, reversible project
> work without repeated owner questions. Safety must remain evidence-based, but bureaucracy
> must not block progress."

The owner's directive text below is the **authority**. The Implementation Record at the end is
engineering's answer and is *not* part of the authority.

## 1. New default

For internal OCTOPUS work:

```
DEFAULT = PROCEED        (not: DEFAULT = ASK OWNER)
```

Ask the owner only when an action crosses an explicit RED boundary (§10). A missing
noncritical document, optional receipt field or cosmetic evidence must not block safe internal
work. Unknown runtime/destructive effects remain blocked.

## 2. Fully automatic green actions

No owner approval and no remote witness are required for: reading code/telemetry/state/logs/
receipts · task and goal generation · model/API inference within the approved global budget ·
provider selection and fallback · sanitized context preparation · branch/worktree creation ·
free-form non-TCB patch generation · sandboxed Python/shell execution · tests, benchmarks,
fuzzing, static analysis · local commits · creating `autonomy/*` branches · WILD mutation and
tournaments · documentation and memory updates · prediction creation/reconciliation · queue
and ledger maintenance · verified cache/temp cleanup · package creation · rollback-bundle
preparation · local shadow deployments · rejected-candidate cleanup · architecture analysis ·
root-cause analysis · generating new typed tools inside the non-TCB Tool Broker.

**Class A tasks must proceed automatically. Node 182 is not required to approve ordinary
development steps.**

## 3. Free-form coding authority

The native coding worker is **no longer limited to enum-only patches**. It may generate and
apply multi-line, multi-file non-TCB patches when: affected paths are non-TCB · execution
occurs in an isolated worktree/sandbox · diff scope is declared · protected paths are excluded
· tests are generated or selected · regression runs · rollback exists.

Models may generate: Python · PowerShell · Bash for sandbox execution · JSON · YAML · systemd
units for non-TCB OCTOPUS services · adapters · tests · parsers · API clients · dashboards ·
queue workers · maintenance tools. Generated shell may run inside a disposable sandbox; it may
**not** run directly as root or against STABLE runtime.

> "Do not artificially reduce capable external models to one-word classification when
> deterministic validation can safely inspect a richer patch."

## 4. Automatic non-TCB promotion

```
worktree → focused tests → regression → security scan → package → shadow
         → node-182 verdict → single-node canary → effect verification
         → outcome verdict → retain or rollback
```

No owner approval is required for this pipeline. Standing permission includes deploying a
non-TCB worker, updating a non-TCB parser/adapter, restarting the exact updated OCTOPUS-owned
service, enabling an OCTOPUS-owned non-TCB timer, rolling back automatically, retaining a
successful canary, and applying the same verified package to another eligible node
**sequentially**. Never deploy to all nodes simultaneously. TCB remains excluded.

## 5. Witness relaxation

Node 182 remains mandatory before normal Class B deployment or persistent runtime
modification. Witness is **not** required for local coding, local tests, sandbox execution,
WILD changes, package generation, read-only observation, local commits, shadow-only
evaluation.

**Emergency exception:** if an existing OCTOPUS-owned non-TCB collector, worker or supervisor
is confirmed failed by three observations and node 182 is temporarily unavailable, node 138
may perform **exactly one precommitted recovery action** without a pre-action remote verdict,
provided the action is an exact pinned restart or rollback, target identity and unit are
proven, no code/config change occurs, rollback exists, no external effect exists, the
kill-switch is clear, the circuit breaker is closed, and the action budget permits it.

Required label: `EMERGENCY_LOCAL_RECOVERY_PENDING_REMOTE_REVIEW`. When 182 returns, it must
verify the outcome. **No emergency exception** for deploy, TCB, secrets, money, external
communication, network or data deletion.

## 6. Automatic provider routing

```
deterministic → local-180 → deepseek → gemini → openai → WAITING_COGNITION
```

Routes may be selected without owner confirmation. OCTOPUS may choose among healthy providers
by task complexity, prior validation success, latency, cost, context size, privacy and
remaining budget. A second model may be called for critique when: the first patch changes
multiple files · tests are incomplete · confidence is low · the action will deploy · models
disagree. Global budget unchanged: 24h `$20` / 24h `$20` / then `$10` per rolling 24h / month
`$100` / per task `$2` / max three paid calls per task. No separate owner question inside
these caps.

## 7. Git freedom

May automatically: create local branches/worktrees · commit non-TCB changes · push to
`autonomy/*` when scoped Git identity becomes available · create/update draft PRs · add
evidence and test results · close failed draft PRs · rebase its own unshared autonomy branch ·
delete its own clean disposable worktree after evidence preservation.

May not: force-push protected branches · merge protected/main without the existing governance
path · delete Git history · use the owner's broad personal token · alter repository
permissions. **Local progress must not stop merely because GitHub push is unavailable.**

## 8. Storage freedom

May automatically remove: own caches · `__pycache__` · `.pyc` · `.pytest_cache` · failed
disposable worktrees · generated temporary packages · duplicate derived artifacts · expired
WILD candidate directories · rotated logs after verified archive · reproducible build output.
May archive completed evidence after hash verification and restore test.

May not automatically delete: unique evidence · state · queue · ledger · receipts · repository
history · databases · model originals · user files · secrets · unknown data.

## 9. Parallelism and speed

Allow: up to 3 concurrent Class A/coding tasks · up to 2 concurrent model calls (but only 1
paid call while the budget contract requires) · multiple independent test suites in parallel ·
one WILD tournament plus one STABLE development task · one runtime Class B action at a time.
Do not serialize unrelated read-only, coding or testing work. Runtime deployments remain
serialized per component/node.

## 10. RED boundaries — owner approval still required

- changing TCB or autonomy constitution;
- disabling Witness, receipts, rollback or kill-switch;
- changing owner authority;
- accessing/exporting raw secrets or private keys;
- creating privileged accounts or changing RBAC;
- spending above the approved API budget;
- purchases, payments, trading or subscriptions;
- public/customer communication;
- changing DNS, firewall, router or public ingress;
- firmware flashing, formatting or partitioning;
- deleting unique or unknown data;
- rewriting Git history;
- deploying to unknown machines;
- actions with irreversible external consequences.

> "Do not classify ordinary non-TCB engineering as RED merely because it changes code."

## 11. Reporting without interruption

Report asynchronously through receipts and cockpit. Do not stop to ask the owner after every
intermediate discovery. For recoverable non-TCB problems: diagnose → attempt repair → test →
retain or rollback → report. Ask only if a RED boundary is necessary, all safe alternatives
failed, a TCB integrity issue exists, or an irreversible effect is unavoidable. Batch minor
warnings into one periodic report.

## 12. Final state

`HIGH_FREEDOM_AUTONOMY_ACTIVE` — broad native coding, real sandbox execution, autonomous API
use, automatic non-TCB deployment, automatic recovery, automatic rollback, WILD evolution,
asynchronous reporting, few owner interruptions. **This does not mean removal of the RED
boundaries.** Do not reinterpret this policy as permission to weaken TCB. Do not pause healthy
loops while documenting it.

---

# Implementation Record (engineering, not authority)

## Phase 1 — deployed 2026-09-13 (this lane, non-TCB)

| Directive item | Implementation | State |
|---|---|---|
| §3 free-form coding | `coding_worker.py` v1.4: `octopus.patch.v1` JSON contract (files+anchors+replacements+tests+run_tests), non-TCB path allowlist, AST compile gate, anchor-exactly-once, stage tests, backup/rollback; enum path retained as the local-model fallback | DEPLOYED |
| §6 routing + critique | `providers.py` `select(need)` (complexity/cost/health aware) + `api_budget.critique()` calling a *different* healthy provider when the patch is multi-file or confidence is low; capped at 1 extra call inside the 3-calls/task budget | DEPLOYED |
| §9 parallelism | worker processes up to 3 tasks per tick; paid calls remain concurrency 1 by contract | DEPLOYED |
| §2 green list | recorded here as standing policy; the worker never asks the owner for these steps | RECORDED |
| §7/§8 | already true in practice; local progress continues without GitHub push | RECORDED |

## Phase 2 — explicitly pending (each needs its own careful pass)

| Directive item | Why pending |
|---|---|
| §5 emergency local recovery | touches the **TCB supervisor** (its recovery path). The frozen test battery must be extended first (three-observation confirmation, pinned restart/rollback only, `EMERGENCY_LOCAL_RECOVERY_PENDING_REMOTE_REVIEW` label, post-hoc 182 review). Owner-authorized by §5, but implemented as a scoped TCB edit with tests, not rushed |
| §4 cross-node sequential apply | needs a second eligible node; 180/182 roles are witness/cognition today |
| §7 GitHub push | blocked on the owner-side deploy-keys toggle (unchanged) |

Nothing was weakened: kill-switch, receipts, rollback, witness-before-Class-B-deploy and the
three permanent GOV-V7 locks are all intact. No loop was paused.

## Phase 1 deploy record (2026-09-13, node 138)

| Artifact | sha256 (first 24) | Rollback pre-image |
|---|---|---|
| `state/coding-worker/coding_worker.py` v1.4.0-freedom-v2 | `2435ec4c9beb8198d2457c12` | `coding_worker.py.pre-freedom-v2-20260913` (`9b85869601acfb02a01c4d98`) + `.pre-freedom-fix1` |
| `state/api-budget/providers.py` | `c4e3380b170bb6a41ebde23d` | `providers.py.pre-freedom-v2-20260913` (`9a96da26d4cd3dac98f6e339`) |
| `state/api-budget/api_budget.py` | `c4938caca4d7b8e5638ae1d6` | `api_budget.py.pre-freedom-v2-20260913` (`b42cf48ab9a0f7493f293109`) |

Verification: 6/6 adversarial validator cases PASS (TCB path, secrets path, path traversal,
non-anchor op, shell-injection run command, bad kind); stubbed happy-path PASS (JSON doc →
stage → AST → tests → canary proposal spooled → cleaned; zero spend, zero deploy); live
worker ticks healthy on v1.4 (04:12Z / 04:18Z / 04:23Z, `Result=success`); `select("patch")`
→ deepseek (owner default), `select("review")` → anthropic. The first real free-form task will
be generated by the goal engine on the next cycle; its deploy still passes through witness +
canary per §4/§5.
