# PR (local) — VBAA ArgumentProvenanceGuard

## Summary
- Add `ArgumentProvenanceGuard` so untrusted and unprovenanced fixture arguments are rejected and verified fixture provenance passes.

## Test plan
- [x] `python -m pytest tests/contract/vbaa/test_argument_provenance_guard.py -q --noconftest`
- [ ] `test_executor_handle_firewall.py` stays RED until the next branch

## Rollback
```
git checkout l7/vbaa-artifact-admission
git branch -D l7/vbaa-argument-provenance-guard
```
Or `git revert <SHA>` for this commit only. Do not `rm -rf`.

## Notes
Based on `l7/vbaa-artifact-admission`. Local only. Push/gh needs `owner_decision`.
`INV-DERIVED` xfail left in place.
