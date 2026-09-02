# LB — Self-Completing Doctor — Definition of Done

Lane: **LB / Self-Completing Doctor** (owner executive order 2026-09-02)
Base: origin/main @ 33c94763005f5cf8c766701f408390c49bba0da7
Worktree: F:\wt-self-completing-doctor · Branch: lane/self-completing-doctor
This file is the FIRST commit of the lane, per owner directive. No code precedes it.

## Measurable exit criteria (all must be true; "almost done" is not a state)

1. **Contract mapped.** Every in-scope requirement of `LAB-DOCTOR-CONTRACT.yaml`
   (doctor section, experiment_contract validation, forbidden list, security_incident_rule)
   has: `req_id → code symbol → test symbol → input → output → failure mode → receipt`,
   in `ofn/doctor/contract_map.py:REQUIREMENTS`. Out-of-scope requirements (hard sandbox
   = lane C) carry status DELEGATED_LANE_C and are ENFORCED as refusal in this lane's code.
   Counts (total/implemented/delegated/escalated/forbidden) are printed by the CLI.
2. **Read-only round, proven.** `ofn/doctor/round.py` exposes no function that writes to
   the source vault. Proof = (a) synthetic-vault test compares full tree hash before/after,
   (b) real run on F:\backup records integrity manifests (before==after) in the receipt.
   dry-run is not a flag — there is no other mode.
3. **Findings are machine-readable** (`findings.json`): id, category, severity
   (LOW/MEDIUM/HIGH/CRITICAL), title, evidence_path, evidence_sha256, detail,
   proposed_action. Stable ids across reruns (no duplicate findings).
4. **Self-backlog works.** Items carry exactly the 9 owner-mandated fields
   (id, missing_capability, evidence, severity, proposed_action, test_required,
   owner_ruling_required, status, created_at); ids stable; re-running the round
   produces zero duplicates.
5. **No proposal without destiny.** Every proposal ends in exactly one of:
   PR_CREATED | QUEUED_WITH_REASON | REJECTED_WITH_REASON | ESCALATED_TO_OWNER.
   Orphan count = 0. A crash mid-proposal cannot leave PENDING: journal recovery
   assigns a deterministic fail-closed outcome.
6. **Regression green.** `python -m pytest tests/ -k doctor_lane` fully green on this
   branch; the vault doctor suite (measured baseline 2026-09-02: **168/168, exit 0**
   — NOT the stale 157) is untouched and re-measured at close, unchanged.
7. **Independent PR** to main from this branch only; zero files owned by lane A
   (self-awareness/cockpit/brain-probe) touched; no workflow/protection/CODEOWNERS change.
8. **VERDICT_QUEUE:** no direct write; an append-payload artifact + proposed append
   location is produced under `09-LANES/LB/runs/`.
9. **Receipts verifiable.** `receipt.jsonl`: one JSON object per line, each line carrying
   its own `line_sha256`; `verify()` re-computes and rejects any tampered line.
10. **Forbidden matrix intact:** no writes to F:\backup, no outbound, no flags, no gates,
    no secrets, no self-merge, no --admin, no blind force-push.

## Non-goals (explicit)

- Building the hard lab sandbox (lane C scope; contract verdict NOT_A_VERIFIED_HARD_SANDBOX
  is respected: this lane's code REFUSES to execute untrusted mutation code).
- Executing any prescription on the vault. Doctor diagnoses and proposes; changes travel
  PR or owner ruling only.
- Any change to _ops lineage, CURRENT-TRUTH machine lineage, or OCTOPUS-DOCTOR vault code.

Valid end states for this lane: DONE | BLOCKED_BY_OWNER | BLOCKED_BY_FILE_COLLISION |
FAILED_WITH_EVIDENCE.
