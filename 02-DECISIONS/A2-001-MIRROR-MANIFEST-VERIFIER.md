---
type: decision
status: owner-approved-development-canonical
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2, a2-001, sandbox, wave0, inventory]
sources:
  - "[[../00 - Inbox/2026-08-18 DECISION — A2-001 inventory-first not octopus-bridge canonical]]"
  - "[[../06-EVIDENCE/A2-001-CANONICAL-DECISION-2026-08-18]]"
  - "[[../04-SYSTEMS/OFN-NODE]]"
---

# A2-001 — Mirror Manifest Verifier (canonical on .191)

STATUS: **OWNER-APPROVED-PROPOSAL**. EXECUTION NODE: **.180**. PROPOSAL ORIGIN: **.138**. CANONICAL AUTHORITY: **.191**. AUTONOMY: **A2_SANDBOX_ONLY**. WAVE: **WAVE0_OBSERVE_ONLY**. EFFECT AUTHORITY: **NONE**.

`.191` recorded this block. **2026-08-18 ~03:17+10 owner approved `development_canonical` only** (`F:\backup\octopus-bridge` @ `equip/g10-cognition-20260816` / `d10887c`). Implementation is **QUARANTINED_PASS_LOCAL_ONLY** on `.191` (additive verifier; OFN stubs unchanged). Not merged. Binding **DELIVERED_TO_180**. `lab_execution: NOT_STARTED`. `promotion_authority: NONE`. Next required evidence: ACK + fresh-worktree receipt from `.180`. Machine state: `06-EVIDENCE/canonical/decisions/a2-001-state-2026-08-18.json`. `deployment_mirror` (`ofn/bridge`) still write-none. Evidence: [[../06-EVIDENCE/A2-001-QUARANTINED-PASS-2026-08-18]].

PROMOTION is never automatic. `QUARANTINED_PASS` (if it ever happens) is not merge authorization.

## Final A2 order

1. **A2-001** Mirror Manifest Verifier — now (inventory halt; no code in a guessed tree).
2. **A2-002** Evidence Envelope v2 — later.
3. **A2-003** Memory Write Contract **Draft only** — later; never canonical schema from `.180` or `.138`.

## Receipt v1 — integrity_hint only

Hash-chain is **not** a signature and **not** authorization. Use `integrity_hint: hash-chain-unkeyed`. No HMAC/keys in v0.

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

## Lab status 2026-08-18 ~02:59 +10

**UNKNOWN_CANONICAL.** Stopped on canonical ambiguity (BUDGET). `.180` not started. Fugu/DeepSeek did not run. Tests are acceptance authority when a unique path exists; they were not run into a guessed tree.
