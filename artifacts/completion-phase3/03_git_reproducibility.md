# Phase 3 P3 — Git reproducibility

GIT_REPRODUCIBILITY: PASS
REMOTE: none
PUSH: false
BRANCH: feat/phase3-completion
ARCHIVE: archive/board-life-001-50f31db @ 50f31db

## Classification of remaining untracked

KEEP_UNTRACKED (runtime/evidence/secrets/vendor):

- `evidence/**` soak and pre-reboot dumps
- `state/` `lab-data/` already gitignored
- `vault/` Obsidian working copy
- `validation_*` `audit/` `smoke/` tarball sidecars
- `artifacts/concept-tour-phase2/` `artifacts/prefix-cache/` `artifacts/vllm-block-size/`
- `AGENT_HANDOFF_RK35XX_VALIDATION.md` `T1_LOCKED_SOAK_ACTIVE`
- `*.gguf` `venv` `*.db` WAL/SHM PID logs secrets.env

TRACKED this phase: `ofn/` source+tests, `bin/`, `docs/`, `scripts/`, `systemd/`, `artifacts/completion-phase3/` markdown/json/csv (not SQLite backups).

## Secret scan

- `/etc/octopus/secrets.env` exists mode 0600, not in repo
- Pattern scan of `ofn/`,`bin/`,`systemd/`: only `ofn/organism/tests/test_afferent.py` fixture line `DEEPSEEK_API_KEY=not-a-telegram-key` (not a live secret)
- `cognition/secrets.py` is a loader, no key material

## Commits

Local commits on `feat/phase3-completion` after this document; no `git push`.
