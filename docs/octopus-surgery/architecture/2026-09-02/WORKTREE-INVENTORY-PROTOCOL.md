# Read-only worktree inventory

purpose: census registered worktrees and classify the lock zone before any write.
status: tool + tests. Prune/remove are forbidden.

## Verdicts

| verdict | means | does not mean |
|---|---|---|
| VERIFIED | `git status --porcelain` empty and no lock | "safe forever" |
| SUSPECTED | dirty tree, index lock, or porcelain `locked` | concurrent writer proven |
| UNKNOWN | timeout or status unreadable | FALSE, absent, or concurrent write |

Timeout does not prove concurrent writing. UNKNOWN is not FALSE.

## Binding code

- `tools/worktree_inventory.py` — parse porcelain, classify, optional live census
- `tests/test_worktree_inventory.py` — parse fixture, classify matrix, AST guard against `prune`/`remove`

This run's live census is in the receipt JSON (command + UTC + exit code). It is a snapshot, not a lock.
