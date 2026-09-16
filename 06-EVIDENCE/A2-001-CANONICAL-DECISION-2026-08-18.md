---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [octopus, a2, a2-001, sandbox, inventory, unknown-canonical]
author: "laptop agent DESKTOP-KA9RFN5 — WAVE0 A2-001 inventory halt"
---

# A2-001 canonical decision + inventory (2026-08-18 ~02:59 +10)

Host `DESKTOP-KA9RFN5` (.191). WAVE0_OBSERVE_ONLY. `A2_SANDBOX_ONLY`. EFFECT NONE.

**Verdict: `UNKNOWN_CANONICAL`.** Implementation did **not** proceed. No worktree, no `_ops/mirror_verifier/`, no merge, no `.180` activation.

Canonical decision copy: [[../02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]. Inbox: [[../00 - Inbox/2026-08-18 DECISION — A2-001 inventory-first not octopus-bridge canonical]].

Envelopes (`octopus-handshake-envelope/1`, `may_authorize=false`, `autonomy_delta=0`):

| receiver | sha256 | path |
|---|---|---|
| continuity | `9d7758737cbfdf9fa665522fffc3776066dd42b6413666cd0d4047c262c41194` | `06-EVIDENCE/envelopes/a2-001-continuity.json` |
| sensorium | `db120060cae76d46ceef4f77bd7037c4ddc415d11464d387612b92bff9a0206a` | `06-EVIDENCE/envelopes/a2-001-sensorium.json` |
| feet | `a80ea393983abae33c375e9329029e205d65ef7c71fcf5c780914ff2fabe82f3` | `06-EVIDENCE/envelopes/a2-001-feet.json` |

`.191` refuses to rubber-stamp `octopus-bridge` as the A2-001 home. Guessing the path is forbidden.

## Owner block (verbatim)

```text
DECISION ID: A2-001
TITLE: Mirror Manifest Verifier — sandbox implementation

STATUS: OWNER-APPROVED-PROPOSAL
EXECUTION NODE: .180
PROPOSAL ORIGIN: .138
CANONICAL AUTHORITY: .191
AUTONOMY: A2_SANDBOX_ONLY
WAVE: WAVE0_OBSERVE_ONLY
EFFECT AUTHORITY: NONE

SCOPE:
- Implement manifest.v1 and receipt.v1 schemas.
- Implement a read-only verifier CLI.
- Verify local-tree content against a supplied manifest.
- Emit deterministic JSON reports and reproducible report hashes.
- Create test fixtures and deterministic tests.

INPUT:
- Manifest entries: relative_path, sha256, size_bytes, algorithm.
- Local read-only tree.
- Prior sync receipts, if supplied.

OUTPUT:
- Exit code 0: PASS
- Exit code 1: MISMATCH
- Exit code 2: MALFORMED_INPUT
- JSON report with report_hash.
- Quarantined patch, test receipt, and Evidence Envelope.

REQUIRED TESTS:
- Golden pass.
- One-byte tamper.
- Missing file.
- Unexpected file.
- Size mismatch.
- Malformed manifest.
- Replayed receipt.
- Out-of-order receipt.
- Denylisted path exclusion.
- Two deterministic runs with byte-identical reports.

FORBIDDEN:
- Network access, SSH, SMB writes, rsync, git push, merge, deploy.
- Auto-remediation, deletion, rename, or copy.
- TCB, policy, secret, credential, provider, systemd, NBB-CP,
  ActionBridge, business-leg, or production-path changes.
- HMAC/signature/key generation in v0.

MODEL ROLES:
- Fugu non-Ultra: proposed implementation only.
- DeepSeek V4 Flash: independent code review only.
- Deterministic tests: acceptance authority.

BUDGET:
- One isolated job.
- One fresh worktree.
- Maximum three repair loops.
- Stop on baseline-red, canonical ambiguity, denied-path touch,
  secret finding, non-deterministic output, or failed test.

PROMOTION:
- Never automatic.
- QUARANTINED_PASS is not merge authorization.
- Owner review on .191 is required for every promotion.
```

## Final A2 order (binding)

| order | id | what | when |
|---|---|---|---|
| 1 | A2-001 | Mirror Manifest Verifier | now — **halted** at inventory |
| 2 | A2-002 | Evidence Envelope v2 | later |
| 3 | A2-003 | Memory Write Contract **Draft only** | later; never canonical schema from `.180` / `.138` |

## Receipt v1 shape (integrity_hint only)

Hash-chain is **not** signature or authorization. No HMAC/keys in v0.

```yaml
receipt_id: "rcpt_<uuid>"
schema_version: "receipt.v1"
snapshot_id: "snap_<sha256-prefix>"
manifest_hash: "<sha256>"
previous_receipt_hash: null
observed_at: "<UTC ISO-8601>"
observer_node: ".180"
result: "PASS|MISMATCH|MALFORMED"
report_hash: "<sha256>"
integrity_hint: "hash-chain-unkeyed"
```

## Inventory (local .191 only — no SSH / network / SMB write)

Live tree: `F:\backup` HEAD `d10887cbb5c80ec2c3e347f070556ba8276d8a79` branch `equip/g10-cognition-20260816` remote `E:/germline/octopus.git`.

| path | git remote / identity | HEAD | `schemas/` | `octopus_bridge/mirror_verify.py` | notes |
|---|---|---|---|---|---|
| `F:\backup\octopus-bridge\` | live vault; remote germline=`E:/germline/octopus.git` | `d10887c` | **ABSENT** | **ABSENT** | two tracked stubs only: `__init__.py`, `models.py` |
| `F:\backup\.claude\worktrees\organism-alive-69a5db\octopus-bridge\` | worktree of same repo | `bfc673f` `claude/deep-scans-octopus-automation-732592` | **ABSENT** | **ABSENT** | second working copy of the same stub |
| `E:\germline\octopus.git` `refs/heads/equip/g10-cognition-20260816` | bare germline | `d10887c` | no `octopus-bridge/schemas` | no | same two blobs as live |
| `E:\germline\octopus.git` `refs/heads/ofn/bridge` | bare germline | `e21f20d7c690e4660894226b1cef1bd47b219b5a` | **ABSENT** (no `schemas/` at all) | **ABSENT** | **different tree**: package at repo root `octopus_bridge/` + `tests/` + `deploy/octopus-bridge.service` — board half, 2026-08-16 |
| `E:\germline\vault.git` HEAD `master` | vault remote (not the live F:\backup remote) | `8b7e6e834f6fe1edc0472f4d193eee9559282c8d` | no `octopus-bridge/schemas` | no | same two stub blobs as live |
| `E:\germline\octopus-wave-20260721.git` HEAD | wave bare | `55544dab…` | no `octopus-bridge` path | no | no match |
| `E:\germline\octopus.git` HEAD `backup/before-cleanup-2026-07-19` | germline default HEAD | `a2183c3` | no `octopus-bridge` path | no | older branch, no package |

Unrelated empty `schemas/` on live tree (not under `octopus-bridge`): `F:\backup\_ops\world_discovery\schemas` (0 children). Other `schemas/` dirs (`_ops/action_bridge/schemas`, mining, `4d_system/docs/schemas`) are **not empty** and are **not** A2-001 candidates.

No `F:\backup-wt-a2-001`. No `F:\backup\_ops\mirror_verifier\`. No `F:\backup\_ops\a2_quarantine\`. Other listed worktrees have **no** `octopus-bridge/` except `organism-alive-69a5db`.

Branch name hits: `remotes/germline/ofn/bridge` (live); `vault.git` also has `claude/octopus-event-bridge` / `claude/octopus-event-bridge-aligned` (event-bridge, not this package).

## Why not exactly-one proven SoT

Proceed required: **exactly one** proven path **and** it matches owner-documented SoT in this vault (quote file+line).

Vault SoT documents `octopus-bridge` as the **OFN / board trust-boundary stub**, not as A2-001 mirror-verifier home:

- [[../04-SYSTEMS/OFN-NODE]] line 27: `بستهٔ کد سمت ارشد: octopus-bridge/octopus_bridge/`
- [[../04-SYSTEMS/OCTOPUS]] line 52: `بستهٔ کد: octopus-bridge/octopus_bridge/`
- [[../00 - Inbox/2026-08-15 REPORT — Forgotten Gaps for Next Agent]] line 132: ``octopus-bridge/` در ریشه = دو فایل stub، بدون I/O``
- [[../COUNCIL_REPORTS/2026-08-16-wave-01/A01_repo_cartographer/FILESYSTEM_TREE]] line 73: `octopus-bridge/octopus_bridge/ bridge package`

Owner narrative assumed an **empty** `octopus-bridge/schemas/`. That directory **does not exist** on `.191`.

Two plausible roots without a single A2-001 SoT: (1) vault stub `F:\backup\octopus-bridge`, (2) full board package on `ofn/bridge`. Guessing which one should receive `manifest.v1` is forbidden → stop.

## What did not happen

No SSH to `.180` / `.138` / `.182`. No git push, merge, deploy. No TCB edit. No HMAC/key generation. GITWRITE-FAILED not cleared. Tests not registered in `run_all.py`. Fugu/DeepSeek did not run. `.180` lab not started.

## Reproduction (local, read-only)

```
git -C F:\backup rev-parse HEAD
git -C F:\backup ls-files octopus-bridge
git --git-dir=E:\germline\octopus.git ls-tree -r --name-only refs/heads/ofn/bridge
git --git-dir=E:\germline\octopus.git ls-tree -r --name-only equip/g10-cognition-20260816 -- octopus-bridge
```

## Uncertainty

- Tests were not run; this halt is inventory, not a verifier PASS/FAIL.
- `.180` was not executed.
- Fugu/DeepSeek did not run.
- `_ops/mirror_verifier/` and `F:\backup-wt-a2-001` were **not** created this session (old layout never landed).
- `E:\germline` holds bare git dirs, not a second live checkout of `ofn/bridge`.
- Sydney August = AEST UTC+10 (OS offset +1000), not UTC+11.
