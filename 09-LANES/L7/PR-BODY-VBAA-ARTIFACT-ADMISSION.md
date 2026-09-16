# PR (local) — VBAA ArtifactAdmission

## Summary
- Add `_ops/vbaa/` package bootstrap and the smallest `ArtifactAdmission` that locks fixture admission: empty / unsigned / wrong type / path escape reject; confined signed allowed type admits.
- Includes the L7 RED fixture corpus so the contract is reviewable without live node, Telegram, or 138 ledger.

## Test plan
- [x] `python -m pytest tests/contract/vbaa/test_artifact_admission.py -q --noconftest`
- [ ] Other two VBAA files stay RED until their branches (collection fail)

## Rollback
```
git checkout rescue/octopus-live-tree-20260821
git branch -D l7/vbaa-artifact-admission
```
If this commit is the only one on the branch: `git revert <SHA>` on a throwaway branch. Do not `rm -rf`. Move stale files to `99-ARCHIVE/` with `archive_` prefix if needed.

## Notes
Local branch only. Push/gh requires `owner_decision` (vault session: no outbound network).
`INV-CRYPTO` xfail left in place.
