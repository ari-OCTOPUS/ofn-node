---
documentation_lineage: rescue/octopus-live-tree-20260821
evidence_lineage: surgery/cognition-authority-denylist-20260830-170620
closeout_commit: b394b999b43ab12573ad574f33a5621a57c66686
evidence_commit: 470bb6031f1e51c9a8e6e1f1536c349e22a5200e
docs_branch: docs/octopus-campaign-sync-20260830
docs_base: 0f0e7f5345004284bd1355ff72b7b6ec68595dbd
deployed: false
merged_into_primary_vault: false
published_to_github: false
canonical_vault_status: NOT_SYNCED
---

# Merge and deploy checklist

Merge (gate A) and deploy (gate B) are separate. This campaign completed
neither.

## Gate A — merge

| Check | Status | Evidence |
|---|---|---|
| Final commit matches report | PENDING owner | `1a18c3e6559f5e7a548751d19dc80f1dadec96a6` plus this closeout commit |
| Required CI on that SHA | BLOCKED | No PR was created |
| Diff has no secrets, `.bak`, absolute worktree paths, runtime DBs | LOCAL_ONLY | Surgery file list in [[14-FINAL-CAMPAIGN-REPORT]] |
| Triple-match commit / manifest / receipt hashes | LOCAL_ONLY | [[06-REALITY-MANIFEST.yaml]] and `receipts/` |
| Merge method | N/A | If a later export PR exists: create a merge commit, not squash |
| This vault branch onto public `ofn-node` main | FORBIDDEN | Unrelated history + public repository |

## Gate B — staging deploy

| Check | Status |
|---|---|
| Release identifier | NOT_STARTED |
| Config diff | NOT_STARTED |
| Backup | NOT_STARTED |
| Restore test | NOT_STARTED |
| Rollback command | NOT_STARTED |
| Health / heartbeat | NOT_STARTED |
| Observation window | NOT_STARTED |
| Stop conditions | NOT_STARTED |
| OWNER-06 explicit approval | NOT_GIVEN |

Staging approval never includes production. D7 is not discussable until gate B,
a physical sensor slice, observatory replacement and a restore drill exist.
