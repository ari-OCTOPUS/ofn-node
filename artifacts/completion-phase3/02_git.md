# Phase 3 — local git reproducibility

PHASE2_GIT_REPRODUCIBILITY: PASS
REMOTE: none
PUSH: false

- Frozen tip: branch `archive/board-life-001-50f31db` at `50f31dbb244912ddf9dc1cb237bb6655a673a05c`
- Working branch: `feat/phase3-completion` (created with `git switch -c`, worktree not rewritten from an old checkout)
- `.gitignore` now excludes live state, lab-data, WAL/SHM, GGUF, venv, secrets.env, ASK evidence, tarballs/zips, Obsidian
- Tracked: organism source, tests, adapters/benchmarks, systemd lab units, bin, docs, Phase 3 artifacts (markdown/json/csv)
- Not tracked: live `organism.db`, backups under `lab-data/`, evidence dumps, vault, validation tarballs
- OFN-L4 lives in `/opt/octopus/ofn-l4` (separate tree; not merged into board-life-001 identity)
