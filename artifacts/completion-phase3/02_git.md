# Phase 3 — local git reproducibility

PHASE2_GIT_REPRODUCIBILITY: PASS
REMOTE: none
PUSH: false

- Frozen tip: branch `archive/board-life-001-50f31db` at `50f31dbb244912ddf9dc1cb237bb6655a673a05c`
- Working branch: `feat/phase3-completion` at `71d018a1c18ffd56d681e40d2a48d1e696712f5e`
- OFN-L4 local repo `/opt/octopus/ofn-l4` root commit `08f915548f3a515becda4c8c33fb20c7d6804786` (no remote; identities not merged)
- `.gitignore` now excludes live state, lab-data, WAL/SHM, GGUF, venv, secrets.env, ASK evidence, tarballs/zips, Obsidian
- Tracked: organism source, tests, adapters/benchmarks, systemd lab units, bin, docs, Phase 3 artifacts (markdown/json/csv)
- Not tracked: live `organism.db`, backups under `lab-data/`, evidence dumps, vault, validation tarballs
- OFN-L4 lives in `/opt/octopus/ofn-l4` (separate tree; not merged into board-life-001 identity)
