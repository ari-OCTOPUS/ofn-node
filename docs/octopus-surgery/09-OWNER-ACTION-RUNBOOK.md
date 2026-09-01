# Owner Action Runbook — OCTOPUS

This file is for the owner only. An agent must not execute these actions.
No secret, private key or token belongs in this file.

Default envelope: `node_id=octopus-continuity-180`, `scope=this_host_only`.

Campaign branch: `surgery/cognition-authority-denylist-20260830-170620`
Final implementation commit before this closeout: `1a18c3e6559f5e7a548751d19dc80f1dadec96a6`

---

## OWNER-01: Do not merge this vault branch into public ofn-node

Status: BLOCKED
Why owner-only: `ari-OCTOPUS/ofn-node` is PUBLIC. This vault lineage and `github/main` (`c1969bce5384f3371b916470299c991627c3d63c`) have no merge base. A PR would publish the Obsidian vault.
Preconditions:
- Read [[14-FINAL-CAMPAIGN-REPORT]]
- Confirm `gh repo view ari-OCTOPUS/ofn-node --json isPrivate` still reports public
Risk: CRITICAL
Exact action:
1. Do not `git push github HEAD` of this branch.
2. Do not open a PR of this branch against `main`.
3. If publication is required, export only the surgery file list onto a new branch that already shares history with `ofn-node`.
Expected output: no vault history on the public remote.
Evidence to save: owner note in DECISIONS that publish remains blocked.
Rollback: if a leak push occurred, rotate exposed credentials offline and request GitHub history removal. That is outside this campaign.
Do not do:
- force push
- squash-merge a vault dump
- `--admin` bypass
Completion test: `gh pr list --repo ari-OCTOPUS/ofn-node --head surgery/cognition-authority-denylist-20260830-170620` stays empty unless a designed export branch is used.
Next unlocked gate: OWNER-02 (designed export) or skip publish and keep germline-only.

---

## OWNER-02: Review the sanitised observation export PR

Status: READY after focused CI reports on the current head
Why owner-only: merge remains `NOT_AUTHORIZED`.
Preconditions: OWNER-01 accepted. Vault/surgery branches were not pushed.
Risk: HIGH
Exact action:
1. Open https://github.com/ari-OCTOPUS/ofn-node/pull/6
2. Confirm the title is observation.v1 only, not “surgery guards”.
3. Confirm `headRefOid` after the reconciliation push (recorded in the PR body).
4. Confirm focused observation CI on that SHA. Do not treat mergeable_state=clean as CI pass.
5. Do not merge, deploy, open D7, or rotate secrets.
Expected output: owner review note; merge still `NOT_AUTHORIZED`.
Do not do: reopen or merge superseded PR #5.
Completion test: PR #6 diff contains no `07 - Knowledge` vault notes and no `_ops` private tree.
Next unlocked gate: none automatically.

---

## OWNER-03: Owner signing-key ceremony

Status: BLOCKED (until a workload that needs a signature exists)
Why owner-only: the signing key is owner identity.
Preconditions: D1/D7 workloads ready to sign.
Risk: MEDIUM
Exact action:
1. Generate an Ed25519 key pair offline.
2. Store the private key outside Git, Obsidian and chat.
3. Register only the public key fingerprint in the project.
4. Sign a seen payload and keep a receipt.
Expected output: receipt with public fingerprint, UTC time, payload SHA-256.
Evidence to save: `receipts/owner-signing-<date>.json`
Rollback: revoke the key and repeat the ceremony; record the reason in DECISIONS.
Do not do:
- put a private key in Git, Obsidian, a prompt or a log
- let an agent generate the key
- sign an unseen payload
Completion test: a verify script accepts the signature with the registered public key.
Next unlocked gate: D1 signature, D7 authorization.

---

## OWNER-04: Secret rotation

Status: BLOCKED
Why owner-only: rotation requires secret access.
Preconditions: [[PRE-0/ROTATION_CHECKLIST.md]] reviewed offline.
Risk: HIGH
Exact action: follow the existing rotation checklist offline. Do not set `OFN_KEEP_GATES_OPEN`.
Expected output: updated rotation status without secrets in Git.
Evidence to save: rotation receipt with item IDs only.
Rollback: revoke leaked credentials.
Do not do: paste secrets into chat or commit `.env`.
Completion test: CRITICAL vault items marked rotated by the owner, not by an agent.
Next unlocked gate: none automatically.

---

## OWNER-05: D1 independent external audit

Status: BLOCKED
Why owner-only: D1 is an external audit decision.
Preconditions: campaign merged or kept local by owner choice.
Risk: MEDIUM
Exact action: commission an independent auditor; do not treat this campaign as D1.
Expected output: auditor receipt separate from campaign receipts.
Evidence to save: auditor identifier and scope, no secrets.
Rollback: reject the audit if scope drifted.
Do not do: ask the implementing agent to certify D1.
Completion test: `OFFICIAL_D1_STATUS` changes only after owner evidence.
Next unlocked gate: none.

---

## OWNER-06: Staging deployment approval

Status: BLOCKED
Why owner-only: merge is not deploy.
Preconditions: [[11-MERGE-DEPLOY-CHECKLIST]] gate B green; restore drill planned.
Risk: HIGH
Exact action: approve staging only after an explicit second confirmation.
Expected output: staging heartbeat inside the observation window.
Evidence to save: staging receipt.
Rollback: documented rollback command in file 11.
Do not do: treat staging approval as production approval.
Completion test: staging health checks recorded; production untouched.
Next unlocked gate: physical sensor pilot, not D7.

---

## OWNER-07: Physical read-only sensor pilot

Status: BLOCKED
Why owner-only: hardware and real-world grounding.
Preconditions: observation.v1 record contract present (Surgery 5).
Risk: MEDIUM
Exact action: one low-risk read-only sensor with calibration and uncertainty. No actuator.
Expected output: physical `observation.v1` records that cannot be unlabeled simulated.
Evidence to save: sensor calibration receipt.
Rollback: disconnect the sensor; keep replay fixtures.
Do not do: wire the sensor to action authority.
Completion test: replay of the physical fixture still passes the 15 foundation invariants.
Next unlocked gate: measurement accumulation, not D7.

---

## OWNER-08: Restore drill on disposable fixtures

Status: BLOCKED
Why owner-only: restore can destroy data if aimed at production.
Preconditions: disposable fixture set.
Risk: HIGH
Exact action: restore onto a disposable copy; keep a receipt.
Expected output: `receipts/restore-drill-<date>.json`
Evidence to save: before/after hashes.
Rollback: discard the disposable copy.
Do not do: restore onto the live vault or production state.
Completion test: restored fixture hash matches the recorded backup.
Next unlocked gate: D7 discussion only after this and observatory replacement exist.

---

## OWNER-09: 826-suite hermetic evaluation

Status: EXECUTED
Result: `HERMETIC_BOUNDARY_VIOLATION`
Why owner-only: duration and failure triage, not because it needs secrets.
Preconditions: Surgery 3 hermetic runner.
Risk: LOW
Exact action: executed once without `--live` at HEAD `b394b999b43ab12573ad574f33a5621a57c66686`.
Expected output: exact pass/fail/skip counts and a log hash.
Evidence to save: [[receipts/verification-03-hermetic-full-suite.json]]
  SHA-256 `c6395c0308fef9d418d4375baf0037b4384db28a1230863a391e316c679a285f`
Observed:
- hermetic executed 827; passed 770; failed 57; live skipped 1; timed out 0
- exit 1; duration 1446s
- live suite excluded; capability marker untouched
- 12 tracked `_ops/state`, `_ops/budget` and `06-EVIDENCE` files were mutated, then restored
Do not do: enable the live provider suite to “make it green”; do not repair in this task.
Completion test: measurement receipt exists; residue restored.
Next unlocked gate: classify/repair is a later task; next owner decision is local lineage, not publish.

---

## OWNER-10: D7 external-action authorization

Status: BLOCKED
Why owner-only: D7 is external effect authority.
Preconditions: OWNER-06 through OWNER-08 complete; observatory replacement exists.
Risk: CRITICAL
Exact action: authorize or refuse D7 in writing. This campaign must not imply readiness.
Expected output: signed owner decision.
Evidence to save: decision receipt, not a chat paraphrase.
Rollback: keep D7 unauthorized.
Do not do: infer readiness from test counts.
Completion test: `OFFICIAL` D7 status changes only after the written decision.
Next unlocked gate: 90% acceptance in [[12-90-PERCENT-GATES.yaml]].
