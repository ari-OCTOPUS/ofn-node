---
type: handoff
updated: 2026-09-04
---

# OCTOPUS — integration and migration handoff

Record: `OCTOPUS-MIGRATION-20260904-01`. Evidence cutoff: `2026-09-04T08:26:14Z` for the real producer invocation. This is a portable source/state map, not proof that a full restore or hardware migration has passed. Keep the conceptual atlas and historical scans; supersede current navigation, not their original meaning.

## Current engineering entry

Canonical repository: `github.com/ari-OCTOPUS/ofn-node`, branch `main`, designated by owner decision CANON-001 and node138 evidence. Canonical board root: `/home/ari/ofn`. Code commit tested and invoked: `1c81bdf1d6eaf2c1fb466fbfd2c7fb297f1861d8`. Later documentation-only commits may have different HEADs; compare module hashes, not just note dates. No GitHub push occurred.

On node138 read `AGENTS.md`, `AGENT.md`, then `09-LANES/BOARD-EXEC-001-INTEGRATION-001/LANE-REPORT.md`. On the laptop read `F:/backup/AGENTS.md`, then `07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md`. Detailed local receipts: `F:/octo-exec/EXEC-001/parallel-followup/`; its final `FINAL-RECEIPT.json` and `STATUS.json` one directory above are the current result, not the old planning prompt.

## What became executable code

The existing `ofn.adapters.self_model_producer` now consumes an exact-byte runtime subset of EXEC-001: 18 library files plus the advisory bridge and selected-code witness. It remains one existing producer, not another orchestrator. Its `produce()` read path is write-free; its CLI persists advisory evidence. No wire, action authority, threshold, frozen scoring formula, service unit, timer, secret, or business message was changed.

Actual path:

`observed self-model rows -> sanitized source-bearing observations -> trust/world-model/homeostasis -> advisory artifact -> hash-linked journal + bitemporal recall + checkpoint + owner inbox`

At the witnessed main invocation: 20 status rows processed, selected functions in four modules matched the current source, subprocess PID matched the artifact PID, exit code 0, and four logical records were durably recorded. Primary status remained `unverifiable` because brain-probe evidence was unknown. Physiology/resource state and inter-organ connectivity remain `UNKNOWN`. Capability source existence without an observation timestamp is not a fresh physiological measurement. No outcome, CPU percentage, neural link, cost, node identity or boot identity was invented.

| Perspective | Current code / consumer | Evidence limit |
|---|---|---|
| R01 Physiology | homeostasis + resource assessment through producer sidecar | real status rows; bodily sensors missing, body UNKNOWN |
| R02 Boundary | contracts, bounded projection, safe writer paths | malformed input rejected; no external authority |
| R03 Anatomy | topology analysis of observed service identities | graph incomplete; connectivity UNKNOWN, not measured isolation |
| R04 Neural timing | topology library in declared-graph assessment | real link/deadline measurements absent |
| R05 Sensing | trust pipeline | 13 captured capability rows lacked times and stayed ineligible |
| R06 World model | deterministic source-scoped pipeline | scope is this sanitized snapshot, not global organism truth |
| R07 Memory | Experience + append-only journal | bitemporal advisory memories, not learned business outcomes |
| R08 Signalling | local TTL envelope and stable record IDs | source authentication UNVERIFIED; not network delivery proof |
| R09 Immunity | validation, integrity checks and writer confinement | tested negative contracts; no OS-wide isolation claim |
| R10 Metacognition | frozen metacontrol + calibration report | no outcome trials; n=0, calibration unknown |
| R11 Genetics | source manifest, preimage, Git lineage, code witness | immutable imported bytes; no self-modification or automatic promotion |
| R12 Chronobiology | journal-authoritative checkpoint and replay identity | malformed/torn state fails explicitly; no automatic repair |
| R13 Resource ecology | bounded artifact storage + cost-accounting library | no verified business cost inputs; no ROI claim |
| R14 Human co-regulation | one deduplicated advisory owner issue/inbox | silence remains PENDING, never approval; no inbox transport claimed |
| R15 Experimental pathology | board negative/boundary tests, prior local experiments retained | E3 for tested contracts; no held-out organism improvement or E4/E5 claim |

The earlier full Windows replay CLI, fixture factory, experiment harness and datasets were not installed on the board. They remain at the original EXEC-001 local source. R01–R15 are traceability labels, not fifteen newly proven live capabilities.

## Hardware and path roles

| Current target | Source / documentation | Mutable state / migration treatment |
|---|---|---|
| Laptop — Windows X64 | `F:/backup` evidence vault; `C:/Users/Armin/Desktop/اختاپوس بک لپ/OCTOPUS-LAB` conceptual atlas; both have `.obsidian` markers | `F:/octo-exec/EXEC-001` bounded staging/receipts; local source copies are not node138 runtime. Do not copy the bulk vault into the atlas. |
| 138 — Linux aarch64, Python 3.13.5 | `/home/ari/ofn`, `.obsidian` marker present; canonical source above | existing `state/self-model/SYSTEM-SELF-MODEL.json`; new `state/self-model/organism-shadow/`; other `state/`, `data/state/` and existing service data are separate, unchanged stores |
| 180 — Linux aarch64, Python 3.13.5 | `/opt/octopus/lab` and `/root/octopus-mesh`, each has `docs/` and Git marker | each has its own `state/`, neither an immediate `data/`; independent roots, not overwritten or equated with node138. No `.obsidian` marker found. Markdown copies do not imply Obsidian installation/synchronization. |

Owner correction: `182` and `PC_worker` were external agents from Grok desktop and are retired, not current hardware targets. Old board182/path/service claims remain historical/unverified attribution. Do not seek SSH identities for those retired agents or silently map PC_worker to the laptop.

Only laptop,138,180 are in the current physical scope. Per-destination write/readback hashes and node180 metadata are in `parallel-followup/documentation/HARDWARE-WRITES.json` and `parallel-followup/hardware/METADATA-180.json` in the local execution package. A `.obsidian` marker establishes placement, not an open application or working sync.

Additional node180 source metadata at `2026-09-04T08:28:41.026520Z`: `/opt/octopus/lab` branch `backup/board180-20260830`, HEAD `28209effa84af68a85ab60329c77dca81c6cea00`; `/root/octopus-mesh` branch `master`, HEAD `17bcff3f50bec92e381d31539f3645d31f8fd95b`. These are observed checkout identities, not proof of loaded service code or canonical ancestry. State directory contents were not inspected.

## Portable contracts and storage

```json
{
  "source_commit": "1c81bdf1d6eaf2c1fb466fbfd2c7fb297f1861d8",
  "primary_schema": "octopus.self-model.v3",
  "advisory_schema": "octopus.organism-shadow.v1",
  "pipeline_schema": "shadow-pipeline.v2",
  "journal_schema": "octopus-journal.v2",
  "checkpoint_fingerprint": "organism-shadow.v1",
  "witness_schema": "octopus.selected-code-witness.v1",
  "tested_python": "CPython 3.13.5 on Linux aarch64",
  "new_library_dependencies": "Python standard library only",
  "advisory_directory_mode": "0700 on POSIX",
  "journal_cap_bytes": 8388608,
  "journal_cap_records": 4096,
  "journal_max_line_bytes": 524288,
  "advisory_directory_cap_bytes": 20971520,
  "auto_delete_or_rotate": false,
  "restore_drill": "NOT_RUN",
  "executable": false
}
```

Journal, checkpoint and OWNER-INBOX belong together. Preserve record order, previous hashes, stable event IDs and bitemporal timestamps. Repeating identical input is idempotent. At a cap or corrupt/torn state the writer fails, retains evidence and returns a nonzero CLI outcome; archival/rotation is an explicit next maintenance decision, not silent data deletion. Existing owner/business ledgers are not replaced by this small advisory inbox.

`FINAL-SOURCE-MANIFEST.json` in the board lane pins all 23 deployed source/test files. The protected registry SHA is `e3ef142d2254c0e430b98c39f244dfb14e7e4ecd33ef58b8ad3d348daefa767b`; metacontrol SHA is `a731adcddc37517d813157ce9355686e9a4eb9d61c378dfb71b494746d5a97cf`. The tested self-model kernel SHA is `c6a60a6c75ab48181d13d97fb0864408f8e7ddf792ddff8d231abf3fda06cb50`.

Byte SHA is portable. Function-code fingerprints include Python/compiler/path details and must be remeasured after migration; they are not cross-platform binary identities. A code witness covers named functions in that invocation only, not mutable globals, dependencies or an older daemon. The long-running `ofn.service` revision remains UNVERIFIED. The existing hourly self-model timer was not changed; this follow-up witnessed a direct invocation, not a later scheduled run of the integrated package.

## Safe future migration order

1. Obtain source code at the exact recorded commit using the authorized canonical source, preserving each destination's unrelated source/worktrees. Do not substitute `F:/backup`, an export, or a similarly named directory for the source decision.
2. Inventory that destination's service-to-source binding, Python/architecture, required existing dependencies and state roots. Node180's roots are not established as a deployable clone of node138; select their role before changing source or services. Whole-organism dependency/model/config inventory remains incomplete.
3. Provision secrets privately through the owner's existing mechanism; never put secret values in this vault, manifest, journal or copied docs. Keep wire/gate state unchanged. No secret export was produced in this task.
4. With relevant writers quiesced under a separate migration authorization, copy the **scoped mutable state** to a separate owner-private destination. Preserve the original and verify hash chain/checkpoint before starting any writer. Do not copy a concurrently changing journal or accept a checkpoint ahead of its ledger. Do not include caches/models/unrelated databases by default.
5. Verify each source/test hash from `FINAL-SOURCE-MANIFEST.json`; run the same 90-test selection below on the destination. This selection tests the advisory integration, not all business/mesh services. Platform differences require new evidence, not skipped failures labelled green.
6. Invoke the existing producer with `--repo <verified-root> --output <private-isolated-output>/SYSTEM-SELF-MODEL.json`. Check exit code, source identity, selected-code match, artifact PID, persistence, unknowns and action authority. Inspect actual state readback. A normal unknown brain/physiology verdict must stay unknown.
7. Only after that isolated validation, explicitly bind/activate the intended destination consumer under its authorization and record a new same-node runtime receipt. Update this path map with a dated superseding record, preserving original evidence. Do not run both migrated writers against the same mutable journal.

Acceptance command, from the verified code root:

```text
python3 -B -m unittest -v tests.test_self_model tests.test_self_model_input_trust tests.test_kernel_purity tests.test_self_model_producer tests.test_organism_shadow tests.test_runtime_provenance
```

Observed main result: 90 passed, no failures/skips. Raw receipt `09-LANES/BOARD-EXEC-001-INTEGRATION-001/MAIN-TESTS.json`, SHA `696e887f67370dcc12d3bdae1d0c11e87542bc0ee1aa846d313d409c5228d6a0`. Existing purity tests emitted ResourceWarnings about unclosed test read handles; this was also present in the passing baseline and is not silently labelled warning-free.

Real invocation receipt: `LIVE-RUNTIME.json` in the same lane, SHA `5a8c3e0f70b6e2bcb2532ebbff9332b03dbdc27739f7eeef66df512a19602fd8`. Its selected code matches, but health status is not green. Historical scheduled evidence for the previous narrow self-model patch remains separately in the runtime observation dated08:03:18.

## Rollback and remaining work

Pre-integration source: `c75473af9eb2439b5cc96a59ca629920416349e7`; prior producer bytes retained as `self_model_producer.preimage.py`. Pre-existing main artifact retained privately as `SYSTEM-SELF-MODEL.preimage.json` in the worktree lane. Use a reviewed inverse source change after checking current hashes, not a hard reset or broad deletion. Preserve the new advisory journal as evidence even if the consumer is rolled back. Documentation preimages and exact destination hashes are retained locally; revert only this task's matching bytes, never subsequent edits.

Open engineering items: real physiology/link/cost/outcome sources; dated brain-probe evidence and its content-level validity (current reader is mtime-based); explicit node/boot identity inputs; calibration and real outcome feedback; full dependency/state/config inventory; verified node180 deployment relationship; isolated restore drill; eventual scheduled-invocation receipt and existing long-running daemon identity. These are named gaps, not missing permission to repeat the completed integration.
