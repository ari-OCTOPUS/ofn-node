# LANE-REPORT — P1-START-PERMIT (session liv, 2026-09-03)

Lane declared: P1-START-PERMIT. Not in origin `09-LANES/LANE-MATRIX.csv` (L0–L9). File-lock: `/tmp/ofn-p1-start-permit` on `feat/p1-start-permit-20260902` — `ofn/adapters/halt_flag.py`, `tests/test_halt_flag.py`, this report, `docs/octopus-surgery/architecture/2026-09-02/receipts/P1-START-PERMIT-WIN-20260903.json`. Incidents append on existing `docs/octopus-os-incidents-20260902` only. `/workspace` stayed on `cursor/taskenvelope-system-hardening-e67b` @`4d59044dd4801b85c1e5fe350c681684f2c2f845` and was not written.

## What was done

- Trigger: check-suite failure `test (windows-latest)` on `feat/p1-start-permit-20260902` @`4d59044dd4801b85c1e5fe350c681684f2c2f845` (PR #95; job 100521250381). Independently confirmed from failed-step log: `HaltFlagAdapter.test_parent_is_owner_private` (`511 != 448` = `0o777 != 0o700`) and `HaltFlagAdapter.test_write_is_canonical_one_not_a_chatty_reason` (`b'1\r\n' != b'1\n'`). CI counts: 2 failed / 3396 passed / 21 skipped / 2377 subtests · `2026-09-03T04:23:26Z`. Ubuntu/other checks were not the failing surface.
- Product fix: `write_halt` opens the tmp file in binary (`wb`) and writes `b"1\n"`. Windows text mode was the CRLF source. POSIX `chmod` 0700/0600 still attempted; the mode-bit assertion is skipped on `os.name == "nt"` (same pattern as `tests/test_run_store.py` / `tests/test_run_gate.py`). A leftover `b"1\r\n"` remains HALTED (`strip()` → `"1"`). CODEOWNERS / branch protection / required-approvals were not touched. No admin bypass.
- Docs first-read: `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` **absent** on this body and on local `origin/main` @`41b56d7a3aefea5da2f4df54cc3f752f6d037da2`. UNKNOWN, not FALSE. Repo-root `D-27-UNLOCK-DIRECTIVE.md` / `D-28-EDGE-RUNBOOK.md` absent. D-27 pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH vs memory. D-28 pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH. Evidence level B (this-host file). Filesystem immutability: UNKNOWN. Not claimed immutable.
- Did not write `start_permit.py` / `envelope.py` / `events.py` / `run_store.py` / `token_ceiling.py` / harvest / CODEOWNERS. Did not open a second start-permit PR.

## What remains

- Independent CODEOWNERS review of #76 then #87 then complementary P1 then #95 then #77. Merge blocked until then. Engineering not blocked.
- Windows runner re-check after publish — this host is Linux; CRLF cause was read from the CI log, not re-executed on windows-latest.
- `quote_sent` / `send_authorized` remain owner-blocked (no newer scoped authorization after the later disarm/hold).
- Incidents append is on existing #120 / `docs/octopus-os-incidents-20260902` only. Origin still lii `5a9ec248cc66a0ff9ca6f3dbbf7e976348db9c2e`. Unpublished liii tips remain first identifiers. This body appends liv. Do not mint a third incidents PR.

## What failed

- `python3 -m pytest` is absent on this image (`ModuleNotFoundError`). Canonical run used stdlib unittest. Exit 0.
- `git fetch` / `gh pr view` denied by `.cursor/hooks/deny_egress.py`. `gh run view --log-failed` and `gh api` refs succeeded earlier this run. Shell `git push` is denied; publish path is `open_git_pr`.

## Evidence paths

| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| Combined suite | 216 passed / 0 failed / 0 skipped / exit 0 @ 2026-09-03T04:27:18Z / parent `4d59044dd4801b85c1e5fe350c681684f2c2f845` | this report + receipt | E3 | measured this run |
| New-module + chaos | 37 passed @ 2026-09-03T04:27:14Z | unittest halt_flag/start_permit/chaos | E3 | measured this run |
| halt_flag tests | 10 run / 0 failed / 0 skipped | recount 2026-09-03T04:27:29Z | E3 | measured this run |
| write_halt bytes | `b"1\n"` | this-host write after patch | E3 | measured this run |
| CI Windows | 2 failed / 3396 passed / 21 skipped / 2377 subtests | job 100521250381 @ 2026-09-03T04:23:26Z | E3 | CI log |
| D-27 hash | `c55f9085…41ea9` / 5469 bytes | this-host surgery source | B | MATCH |
| D-28 hash | `c79f0e74…3f28a` / 16212 bytes | this-host surgery source | B | MATCH |
| filesystem immutability | not claimed | this report | — | UNKNOWN |

Command:

```
python3 -m unittest tests.test_halt_flag tests.test_start_permit tests.test_chaos_start_permit tests.test_kernel_purity tests.test_envelope tests.test_run_store tests.test_token_ceiling tests.test_run_gate tests.test_chaos_owner_absent tests.test_tmpdir -q
```

Receipt pointer: `docs/octopus-surgery/architecture/2026-09-02/receipts/P1-START-PERMIT-WIN-20260903.json` · SHA-256 pending after write · evidence level B (this-host worktree file). Filesystem immutability: NOT claimed.

## Rollback steps

- `git revert` the Windows-LF / nt-mode-skip commit on `feat/p1-start-permit-20260902`. Do not force-push. Do not prune the worktree. Do not re-arm send.
