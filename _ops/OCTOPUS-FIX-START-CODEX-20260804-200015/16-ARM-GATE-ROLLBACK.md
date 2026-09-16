# 16 — arm_gate rollback

Nothing was changed to `arm_gate.py` in this session (the module and its tests were already
committed at `2a99aa3`, before this run began). Nothing to roll back from this session.

## If the module itself ever needs reverting (future reference, not executed here)

```
git revert 2a99aa3
```
Safe: `arm_gate.py`'s own guarantee is that it only ever makes things *harder* to open, and
both its knobs default off, so reverting it returns exactly to pre-2a99aa3 behavior with no
other side effects (it touches no other module's logic, only adds new files + the two-line
`sensitive_enforced()`/`_ALWAYS_SENSITIVE` addition inside `guard()`).

## If a future wiring patch (per `14-ARM-GATE-PATCH-REPORT.md`) is ever applied and needs
## reverting

Revert that specific commit; `arm_gate.guard()` itself never needs to change for a rollback
of its caller — removing the caller alone returns to today's (unenforced) state.
