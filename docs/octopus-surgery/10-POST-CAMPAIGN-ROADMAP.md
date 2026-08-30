# Post-campaign roadmap

Envelope: `node_id=octopus-continuity-180`, `scope=this_host_only`.
This is a map, not authorization.

## GOVERN

- Keep D1, D7, OWNER_KEY, secret rotation and deploy as owner-only.
- Do not merge the vault branch into public `ofn-node`.
- If GitHub publication is needed, use OWNER-02 designed export.
- Merge method, if any later export PR is approved: create a merge commit, not squash.

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
- Next measurement work starts from versioned fixtures and independent
  producer/scorer/verifier modules. Do not copy prose formulas into production.
- Run the 826-suite hermetic default as a dedicated evaluation (OWNER-09).

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
