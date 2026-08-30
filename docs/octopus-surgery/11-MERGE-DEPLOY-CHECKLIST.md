# Merge and deploy checklist

Merge (gate A) and deploy (gate B) are separate. This campaign completed
neither. `MERGE = NOT_AUTHORIZED`. `DEPLOY = NOT_AUTHORIZED`.

## Gate A — merge

| Check | Status | Evidence |
|---|---|---|
| PR exists | PASS | PR #6 |
| PR head identified | PASS | external PR state (`pr_head_sha: reported_externally_in_pr_body`) |
| Focused CI | PASS | 4/4 on the head observed before this docs commit (`ci_last_observed_before_docs_commit: PASS`) |
| Required branch checks | NONE_CONFIGURED | GitHub branch state; required branch checks not configured |
| Same-env differential | PASS | 0 public-export regressions |
| Public secret/path scan | PASS | export receipt |
| PR #5 superseded | PASS | closed, not merged |
| Owner review | PENDING | owner-only |
| Merge | NOT_AUTHORIZED | owner-only |
| This vault branch onto public `ofn-node` main | FORBIDDEN | `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN` |

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
| OWNER-06 explicit approval | NOT_GIVEN / BLOCKED |

Staging approval never includes production. D7 is not discussable until gate B,
a physical sensor slice, observatory replacement and a restore drill exist.
Deploy is not authorized.
