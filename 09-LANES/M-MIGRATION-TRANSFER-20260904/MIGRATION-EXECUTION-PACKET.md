---
type: handoff
status: active
tags: [octopus, migration, execution]
created: 2026-09-04
updated: 2026-09-04
---

# OCTOPUS — external migration-agent execution packet

## Copy-paste task for the next agent

You are the sole migration execution agent for OCTOPUS. The owner wants a **real, evidence-backed migration**, not a disk cleanup, a documentation exercise, or a claim that every historical project folder is one deployable organism.

Start by reading, in order:

1. `F:/backup/AGENTS.md`
2. `F:/backup/agent-prompts/_PROJECT_INSTRUCTIONS.md`
3. `F:/backup/07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md`
4. `F:/backup/09-LANES/M-MIGRATION-TRANSFER-20260904/MIGRATION-FACTS.json`
5. this file

Treat fresh same-node runtime output and file hashes as stronger evidence than all prose here. Record a contradiction rather than selecting a convenient story. Work in one new lane and one dedicated Git worktree. Do not rerun completed integration merely to produce more reports.

Your first executable deliverable is an **A→B isolated advisory self-model restore drill**. A is a new non-service root `/home/ari/drill-001` on node138; only after A has a `RESULT.json` with `PASSED` or `FAILED`, B is a new non-service root on node180. It is intentionally smaller than a production cutover, but it is a real source-and-state migration with hash, journal, checkpoint, test, and direct-invocation evidence. Use its result to build the complete dependency/state/service map required for the broader organism migration.

## Owner intent and non-negotiable boundary

The owner has authorized work on laptop, node138, and node180, including creation of an isolated target root and non-activating validation. Preserve all existing source roots, state, vault provenance, and conceptual assets. `F:/backup` is an evidence vault; `OCTOPUS-LAB` is an atlas. Neither is a substitute for the node138 runtime source.

The active owner decision at `F:/backup/07-HANDOFF/GO-MIRROR-DRILL-DECISION-2026-09-04.md` is the fresh confirmation for the bounded `origin` mirror operation described there. It does not expand authority to any other external effect. Never do any of the following without a fresh, direct owner confirmation immediately before the operation:

- publish to a remote Git host;
- quiesce a live writer or timer;
- bind/start/restart a service, change a systemd unit, activate a consumer, or cut traffic over;
- reveal/copy a secret, alter a wire/gate, send a message, or spend money;
- delete, overwrite an existing root, force-push, reset history, or use a destructive sync option.

Do not overwrite `/opt/octopus/lab`, `/root/octopus-mesh`, `/home/ari/ofn`, `F:/backup`, or `OCTOPUS-LAB`. Do not run `ofn.restore_job`, `ofn.adapters.backup.restore`, a backup/prune job, `record_assessment`, or `self_model_producer.main` against the source state. Never create an `EvidenceStore` on the source journal: it may create a lock.

## Current facts — verify before use

| Item | Current evidence | Meaning |
|---|---|---|
| Live source | node138 `/home/ari/ofn`, `main@2cd67aa43a73d6f9cf4e9a62d7e96cd52502d51e` | Only evidenced live source root. `ofn.service` was active and its WorkingDirectory matched this path. Its loaded code revision is still unverified. |
| Tested code | `1c81bdf1d6eaf2c1fb466fbfd2c7fb297f1861d8` | 23 source/test files pinned; selected board suite was 90 passed, 0 failed/skipped; one direct producer invocation succeeded. |
| Advisory state | `state/self-model/SYSTEM-SELF-MODEL.json` plus `state/self-model/organism-shadow/` | `journal.jsonl`, `checkpoint.json`, and `OWNER-INBOX.md` are one state bundle. The journal is advisory and `executable:false`. |
| Node180 roots | `/opt/octopus/lab@28209eff…`, `/root/octopus-mesh@17bcff3…` | Separate old roots, not a replica and not migration targets. `octopus-mesh/state` is large and actively written; exclude it. |
| Board data | `state/` has no tracked paths; `data/` has six tracked paths | Do not blanket-copy `data/`. An explicit allowlist is required first. |
| Source mirror | node138 is five commits ahead of observed `origin/main`; 28 untracked source entries exist | Preserve untracked state; it must never enter a commit. A rescue branch then fast-forward push is a separately approved operation. |

The full machine-readable values, artifact paths, SHA-256s, test command, and exclusions are in `MIGRATION-FACTS.json`. Detailed prior evidence is in `F:/octo-exec/EXEC-001/STATUS.json`, `F:/octo-exec/EXEC-001/parallel-followup/FINAL-RECEIPT.json`, and `/home/ari/ofn/09-LANES/BOARD-EXEC-001-INTEGRATION-001/`.

## Owner amendment now in force

`F:/backup/07-HANDOFF/GO-MIRROR-DRILL-DECISION-2026-09-04.md` is the active owner decision. It amends this packet: execute **A then B**, do not stop `octopus-selfmodel.timer` or `ofn.service`, and snapshot only during an inter-run window with before/after hash and mtime checks. MIRROR-001 registration does not wait for a successful GitHub push. The decision does not authorize service activation, production cutover, secret copy, wire/gate changes, force-push, germline, deletion, or overwrite of existing roots.

## Phase 0 — fresh, secret-safe preflight

Perform read-only observation first. Do not print `ExecStart`, environment variables, command-line arguments, credentials, or state contents. On node138 record: Git HEAD/branch, sanitized origin identity, `ofn.service` WorkingDirectory/FragmentPath/MainPID/ActiveState/SubState, Python version, relevant timer state, filesystem capacity, and source worktree cleanliness using `GIT_OPTIONAL_LOCKS=0`.

On node180 record: architecture/Python, capacity and permissions for a **new** destination root, the two existing root heads, known unit metadata limited to WorkingDirectory/FragmentPath/MainPID/ActiveState/SubState, and evidence that no service is bound to the proposed new root. Inspect state only by metadata until an explicit snapshot phase. Do not infer that an inactive named unit means no other process exists.

Write one compact receipt with command class, UTC time, sanitized identifiers, hashes/sizes only, and a phase verdict. If node138 HEAD, the source path, test manifest, source ownership, or target isolation differs from this packet, stop the affected phase and record the difference.

## Phase 1 — make the restore drill reproducible before touching live state

Create a dedicated board worktree from current `main`; do not edit `/home/ari/ofn`. Implement the narrow reusable restore validator there:

```text
module: octopus_recovery/migration_restore.py
test:   tests/test_migration_restore.py
API:    validate_advisory_restore_copy(source_root: Path, isolated_dest: Path) -> dict
```

Its source and destination must always be explicit. The validator must copy and validate **only** these files from a stable source bundle:

```text
journal.jsonl
checkpoint.json
OWNER-INBOX.md
```

Required behavior:

1. Reject non-fresh targets, source/destination overlap in either direction, symlinks/reparse points, traversal, and targets outside the declared isolated root.
2. Hash and metadata-check each source file before and after copy. If it changed, emit `SOURCE_CHANGED_DURING_READ`, do not retry, repair, or silently accept it.
3. Build `EvidenceStore` only on the copied destination journal, then validate its chain, sequence, previous hashes, caps, and torn/corrupt-tail refusal.
4. Run `verify_checkpoint(destination / "checkpoint.json", "organism-shadow.v1", store.records)`.
5. Render the destination inbox from the copied journal to a temporary derived file, then byte-compare it with the copied `OWNER-INBOX.md`.
6. Emit a content-free receipt: roles, SHA-256, sizes, validator result, and `executable:false` only.

Reuse existing guards rather than rebuilding them: `octopus_recovery/restore_drill.py`, `octopus_exec/snapshot_reader.py`, `shadow_homeostasis/evidence_store.py`, `octopus_exec/checkpoint.py`, `octopus_exec/handoff.py`, and `ofn/adapters/organism_shadow.py`. The implementation must never write to the source bundle.

At minimum test a valid fixture, source unchanged, nonfresh destination, overlap, symlink/reparse, torn/corrupt journal, checkpoint tampering, inbox mismatch, and source change during copy. Run the new test plus `tests/test_restore_drill_disposable.py`, `tests/test_organism_shadow.py`, and `tests/test_phase_d_backup.py`; then rerun the recorded 90-test selection. A failing or skipped test blocks the next phase.

Commit only the isolated worktree after green tests and a reviewable diff. Do not push it yet.

## Phase 2 — controlled, scoped source snapshot (inter-run only)

The active owner decision forbids stopping `octopus-selfmodel.timer` and `ofn.service`. Observe both, choose a naturally occurring inter-run window, and record the source bundle's hashes and mtimes immediately before and after the copy. Revalidate source path ownership and the source SHA immediately before snapshot. If any source hash or mtime changes during copy, emit `SOURCE_CHANGED_DURING_READ`, mark that attempt failed, retain the evidence, and do not retry-as-repair within the same attempt.

Copy only the validated advisory bundle listed above and its artifact if required by the current producer contract. Do not copy `data/`, general `state/`, caches, models, databases, environment files, secret material, or either node180 state tree. Use the new validator against a disposable local destination first. A failed validator stops the phase; no timer restoration action is needed because no timer stop is permitted.

## Phase 3 — isolated A then B transfer and direct validation

Only after Phase 0 passes, create A at `/home/ari/drill-001` on node138. It must be mode 0700, empty, non-symlinked, on adequate local storage, and unbound from services. Finish A and write `RESULT.json` before creating B. Then create B on node180 at `/opt/octopus/drill-001` only when that path is absent or empty and is not `/opt/octopus/lab`; if blocked, use `/root/octopus-migration-sandbox/drill-001` after a fresh preflight. Never use `/root/octopus-mesh` or overwrite either existing tree. Never use a destructive copy option and never merge a drill root with an existing tree.

Transfer the exact source through node138, preserving repository identity or an auditable source-manifest proof. Verify all 23 pinned source/test hashes from `FINAL-SOURCE-MANIFEST.json` on node180. Function-code fingerprints must be remeasured on node180; they are not expected to equal the node138 fingerprints because path/compiler details can differ.

Run the exact 90-test command from `MIGRATION-FACTS.json`. Then copy the already validated advisory bundle into the isolated target and validate it again before any writer is constructed. Invoke the existing producer directly and only against the target, using a private isolated output path:

```text
--repo <verified-target-code-root> --output <isolated-output>/SYSTEM-SELF-MODEL.json
```

The target must remain unbound: no timer, service, flag, listener, message, or external action. A normal `UNKNOWN`/`unverifiable` health result is acceptable; it is not a test failure. Success requires all of the following:

- exact code-manifest verification;
- test result with no failures or skips;
- source snapshot and destination prefix hashes match;
- valid journal chain and checkpoint before the target writer runs;
- direct invocation exit 0, source identity and selected-code witness recorded, artifact PID matched, persistence `COMMITTED_ADVISORY`, and `executable:false`;
- post-run destination evidence shows the imported journal prefix remains intact and checkpoint is valid;
- source state is re-read without mutation, the source timer is restored, and no service/flag/wire changed on either node.

This is the first honest definition of a completed migration drill. It is **not** yet a production cutover.

## Phase 4 — discover the full organism before claiming a complete migration

Build one source-of-truth matrix; do not copy folders based on names. For every observed laptop, node138, and node180 component, record only fresh evidence for:

| Required field | Question |
|---|---|
| Runtime identity | Which machine, PID/unit, port, working directory, and observation time? |
| Code | Exact root, Git SHA, clean/dirty status, dependency lock/manifest, and test command? |
| State | Immutable / reproducible / mutable / external / unknown; writer cadence and consistency method? |
| Configuration | Names and fingerprints only; secrets remain in the owner's private mechanism. |
| Interfaces | Inbound/outbound protocol, local/network dependency, and whether it is active now? |
| Migration | Target root, transfer method, health check, rollback, and cutover authority? |

Start from these known, but not universally live, areas: laptop `_ops/organism.py`, `_ops/cortex/`, `_ops/live/`, `_ops/telegram_center/`, `_ops/board_cp/`, the tunnel; node138 `/home/ari/ofn`; node180's two preserved trees. Run no `RUN-*`, `RESTART-*`, watchdog, wire, or stop scripts merely to inventory them. Treat `survival-gateway` database material as opaque until its writer/reader relationship is proven. Treat `OCTOPUS/` and `nervous-system/` as projections until a current consumer relationship is measured.

An area with unknown runtime, state, dependency, or rollback remains `unverified`; it is not bulk-copied. Complete this matrix before planning any whole-organism target layout.

## Phase 5 — production activation and full cutover gates

Never use the isolated drill result to imply that node180 is now a production replica. Before each of these actions, request a separate direct owner confirmation and attach it to the relevant receipt:

1. publish a rescue branch and then a fast-forward `main` mirror to `origin` (never force-push and never push `germline`);
2. bind or start a target service/timer and validate one consumer in a canary state;
3. move a specific mutable state owner/writer to the target;
4. stop, demote, or otherwise cut over a source service.

For each component, do source snapshot → target restore → same-node health/test receipt → canary/read-only observation → explicit cutover → source and target readback. No two writers may share the same mutable journal. If a source/target result disagrees, use the documented rollback for that component and preserve both state copies as evidence; do not delete or overwrite the losing side.

The complete migration is done only when every live component in the Phase 4 matrix has a verified target, dependency/configuration provenance, state transfer proof, target runtime receipt, cutover decision, and rollback state. Anything less must be reported as the completed subset, not as full-organism migration.

## Required final outputs and low-storage discipline

Produce only these durable items per phase: one receipt with hashes/commands/results, one current matrix, and one lane report with rollback. Update `F:/backup/07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` and the relevant Obsidian-facing handoff only when a phase actually changes reality. Link to raw evidence; do not duplicate vaults, logs, source trees, or secrets into Obsidian.

Every phase report must have exactly: scope, observed facts, changed files/services, validation, unresolved items, evidence paths, and rollback. Keep failures and contradictions. Never silently repair state, discard a bad target, or rewrite history to make a receipt look green.
