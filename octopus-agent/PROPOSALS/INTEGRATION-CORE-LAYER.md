# PROPOSAL — Integration / "one board, one core" (PROPOSE-ONLY, no execution)
Author: Mini Scientist P0 · run-20260817T1031Z-81f8e678 · Status: AWAITING OWNER DECISION

## Finding that changes the original question
The unification discussion asked: "/opt/octopus as new unified root, or keep current
installs and add a core/ layer?" Discovery shows this is already answered by reality:

- /opt/octopus IS the canonical runtime root (live release tree + venv + releases).
- /var/lib/octopus IS the state/evidence root. /etc/octopus IS the config root.
- The "ten separate projects" impression comes from /root laptop-signing artifacts
  (OCTOPUS-ROOT-V2, OCTOPUS-REGISTRY-*, OCTOPUS-AUDIT-CHECKPOINT, octopus-ca, …)
  and internal versioned variants (cognition, shadow_validation, _pre_release),
  not from parallel runtimes.

## Proposed target (no deletion, no in-place moves)
Add shared layers under /opt/octopus (created by copy from existing code where useful):

    /opt/octopus/core/events/     shared Envelope + run_id (reuses EVENT-SCHEMA.json)
    /opt/octopus/core/policy/     PolicyGate + capability registry (OFF/TESTING/PROPOSE_ONLY/OWNER_APPROVED)
    /opt/octopus/core/evidence/   shared append-only receipts, hashes, replay
    /opt/octopus/core/sandbox/    one runner for all experiments
    /opt/octopus/core/verifier/   deterministic comparators and scoreboards
    /opt/octopus/apps/...         existing packages referenced via thin adapters only

Staged exactly per project doctrine: instrument → stream → migrate.
I1 core/events (zero behavior change) → I2 core/evidence (replay test) →
I3 adapters (structural test: no direct app-to-app imports) → I4 shared sandbox →
I5 staged cutover (shadow → opt-in → default after regression).

## What stays separate (never unified)
policy vs LLM/hypothesis · verifier vs generator · secrets vs agent context ·
production runtime vs sandbox · raw evidence vs editable model memory ·
network (single gateway) vs all modules.

## Cleanup of /root artifacts (owner decision, agent never deletes)
- Sign-and-keep: registry v6 pack and current checkpoint still await Windows
  signatures (per LAPTOP-AGENT-HANDOFF.json inbound_apply_last: both bundles
  incomplete on board).
- After signing settles: archive /root OCTOPUS-* copies into one dated folder
  (e.g. /root/archive/2026-08/) — owner-approved, reversible (move within /root,
  hash list recorded first). wipe.sh and octopus-ca stay untouched.

## Rollback
Each integration step adds new files only; rollback = remove the added layer and
restore previous release pointer. No step rewrites /var/lib/octopus history.

## Cost / risk
Low risk (additive), medium effort. Blocked until owner approves track B start
and the /root archival decision. Recommended order: finish track A through P5 first
so the shared sandbox (I4) is born already battle-tested.
