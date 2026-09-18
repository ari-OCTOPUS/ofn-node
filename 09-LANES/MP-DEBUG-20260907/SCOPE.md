---
type: report
status: active
tags: [octopus, debug, evidence]
updated: 2026-09-07
---

# MP-DEBUG-20260907 — scope and ownership

Direct request: owner supplied the EX1/EX2 agent report and asked to check the status and debug it completely. This is a diagnostic review plus isolated corrective candidate, not execution of every instruction embedded in the supplied historical transcript.

Source work order: `C:/Users/Armin/Downloads/MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md`, SHA256 `ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3`.

Reviewed implementation: `F:/wt-mp-exec-ex1-ex2-20260907`, commit `ba5d239fa7764d96a4694a7b8b347059aea18d29`. That worktree is not edited. Corrective candidate: `F:/wt-debug-mp-ex1-ex2-20260907`, branch `codex/debug-mp-ex1-ex2-20260907`, based on the reviewed commit.

Owned outputs: this evidence lane, the candidate's EX2 contract/tests/generated registry/claim lock entry and local lane report, and an additive dated Obsidian handoff/pointer. RuntimeTruthRow findings are pre-existing and recorded separately; its frozen module and first lock entry are not changed.

Allowed work here: local source inspection, adversarial contract tests, local candidate edits, bounded read-only SSH metadata/audit snapshots, read-only PR metadata, and provenance/handoff documents. No merges, pushes, deployment, restarts, owner-ruling adoption, standing-GO renewal, model generations, messages, purchases, gate/cap/flag changes, secret reads, ledger edits, or cleanup of another lane.

Reviewers have disjoint ownership: root owns EX2 candidate and narrative; claim reviewer owns only the new regression test; evidence reviewer owns LIVE-READBACK.json and live_readback.py; node reviewer owns NODES-READBACK.json. No raw full ledger or secret material is copied into the vault.

Acceptance boundary: correcting EX2 code locally does not satisfy EX1's failed historical prerequisites, resolve a live outcome, prove loaded code, or authorize EX3. Fresh prefix equality verifies continuity relative to a prior fingerprint; it does not establish cryptographic append-only history before that fingerprint.

Preservation: originals remain intact. Corrections are superseding observations, not retroactively added fields. Rollback means not promoting the candidate, or a later scoped revert if it is ever committed/promoted; never delete this or the original evidence lane.
