# Post-campaign roadmap

Envelope: `node_id=octopus-continuity-180`, `scope=this_host_only`.
This is a map, not authorization.

## GOVERN

- Keep D1, D7, OWNER_KEY, secret rotation and deploy as owner-only.
- Do not merge the vault branch into public `ofn-node`.
- `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN`.
- Selective export is complete as PR #6 (`OPEN_AS_PR_6`). Merge remains `NOT_AUTHORIZED`.

## MAP

- Keep the cognition AST guard, lab-gateway fence and hermetic runner as the
  authority map.
- Treat cortex→provider as `SAFE_INFERENCE_BOUNDARY`, not execution authority.
- Treat `code_brain → code_autonomy` as `APPROVED_EXECUTOR_BOUNDARY`.
- Keep `observation_record.py` and `observation_v1.parse_body` as two families
  until a later migration explicitly joins them.

## MEASURE

- Observatory runner, claim store and Brier producers are
  `NOT_FOUND_IN_CURRENT_LINEAGE`.
- Historical 0.80 / 0.99 / n=114 values remain narrative.
- OWNER-09 executed: `HERMETIC_BOUNDARY_VIOLATION` (770/827). Do not run it again
  as a campaign gate. Do not copy prose formulas into production.
- Next local engineering priorities after owner review of PR #6:
  1. Eliminate the 12 tracked-state writes from hermetic execution.
  2. Re-run the complete hermetic suite after that repair.
  3. Build a fixture-only observatory replacement.
  4. Perform a disposable restore drill.
  5. Prepare one read-only physical sensor pilot.

## MANAGE

- Isolated worktree:
  `docs/octopus-surgery` on branch
  `surgery/cognition-authority-denylist-20260830-170620`
- Canonical vault: `<vault-root>`
- Germline remote: `<germline-remote>`
- Primary working tree remains dirty with pre-existing unknown files. Do not
  reset, stash or overwrite them.
- next_move for mesh: wait for the SSH tunnel from board 138 to
  `127.0.0.1:8791-8794` and `8796`. Do not treat 138 outbox counts as sent.
