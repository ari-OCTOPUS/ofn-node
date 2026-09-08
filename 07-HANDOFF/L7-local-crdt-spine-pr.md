status: open
requires: owner_or_operator_push
lane: L7
date: 2026-09-08
source: this-host session; `.cursor/hooks/deny_egress.py`; GitHub API 403

# LOCAL_CRDT first spine — PR publish blocked

Owner vote locked: LOCAL_CRDT. Schema + empty store are on local branch
`cursor/event-envelope-local-crdt-3830` (HEAD `2528285`, parent `c48c9d6`).

## Block
- Shell `git push` / `gh pr` denied by `.cursor/hooks/deny_egress.py`
  (message: record the need in 07-HANDOFF/).
- GitHub MCP `create_branch` returned 403: organization `ari-OCTOPUS`
  forbids the fine-grained PAT (lifetime > 366 days).
- `ManagePullRequest` needs the branch on the remote first.

## Not a product defect
This is an egress/token policy stop, not a schema failure.
Local pytest: 15 passed / 0 failed / exit 0 on
`tests/test_event_envelope_v1.py` (this-host).

## Operator next step
From a host allowed to publish: push the branch and open a PR against
`main`. Do not edit `FROZEN.lock`. No writer cutover.
