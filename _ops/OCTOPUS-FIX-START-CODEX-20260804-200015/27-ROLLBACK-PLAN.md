# 27 — Rollback plan

This session's own commit (report tree + eval harness) can be undone with:

```
git -C <worktree> revert <this-session-commit-hash>
```

Safe and clean: the commit is a pure addition (two new paths, zero modifications to any
existing tracked file), so a revert simply deletes them again with no merge conflicts
possible.

If instead only the eval harness or only the report tree needs removing, they are
independent additions and can be deleted/reverted separately without affecting the other.

The underlying P0 code fix (commit `2a99aa3`) is **not** part of this session's commit and
has its own independent rollback path documented in `16-ARM-GATE-ROLLBACK.md` (arm_gate
side) and implicitly covers latent_space/intel_spine too, since they're the same commit:
`git revert 2a99aa3`.
