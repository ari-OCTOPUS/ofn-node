# OCTOPUS preservation restore

Base HEAD: `53e527aef95c9bb30a3822e3ac278df59590e1d4`

1. Verify `BUNDLE-MANIFEST.sha256`.
2. In a clean worktree based on the HEAD above, run `git apply --binary --3way tracked-content.patch`.
3. Review `untracked-source/`; copy each path only if its destination is absent.
4. Verify every restored path against `SOURCE-MANIFEST.json`.
5. Runtime state, databases, logs, tokens, credentials, caches and generated dashboards are excluded; see `EXCLUSIONS.json`.
