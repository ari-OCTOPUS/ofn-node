# PR (local) — VBAA ExecutorHandleFirewall

## Summary
- Add AST-only `ExecutorHandleFirewall` so a fixture tree that imports `executor` is reported as a violation on host `180`, and a clean fixture tree passes.
- Does not import or scan the live organism tree.

## Test plan
- [x] `python -m pytest tests/contract/vbaa/test_executor_handle_firewall.py -q --noconftest`
- [x] All three VBAA test files together

## Rollback
```
git checkout l7/vbaa-argument-provenance-guard
git branch -D l7/vbaa-executor-handle-firewall
```
Or `git revert <SHA>` for this commit only. Do not `rm -rf`.

## Notes
Based on `l7/vbaa-argument-provenance-guard`. Local only. Push/gh needs `owner_decision`.
`INV-SUBSTRING` xfail left in place. Component-equality matching (not substring).
