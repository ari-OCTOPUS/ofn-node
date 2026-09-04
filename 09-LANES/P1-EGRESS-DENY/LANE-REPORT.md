# LANE-REPORT — P1-EGRESS-DENY (session 2026-09-04T00:06Z)

Lane declared: P1-EGRESS-DENY. `09-LANES/LANE-MATRIX.csv` has L0–L9 only
(no P1 row). File-lock: `ofn/kernel/egress_class.py`,
`ofn/kernel/deny_pin.py`, matching tests + chaos, this report,
`docs/octopus-surgery/architecture/2026-09-02/receipts/P1-EGRESS-DENY-20260904.json`.
Incidents append on existing `docs/octopus-os-incidents-20260902` only
(session lxxxiii; unpublished lxxxi/lxxxii remain first identifiers).

## What was done

- Trigger PR #126 (`feat/p1-unknown-seal-20260902`
  @`7682cee291e9a6fa5b8dafe46bd0b85c61d2bf24`) failed
  `require-independent-approval` (job 100860161478). REVIEW_REQUIRED
  by design (author `cursor[bot]`, issue #51, GOV-V6; required one of
  Elahe-z or aram-ui). Did not merge. Did not weaken the gate. No
  admin bypass. `/workspace` stayed on
  `cursor/taskenvelope-system-hardening-5103` @`7682cee` and was not
  written.
- `origin/main` this-run: `72a4c3d5cea6f0877200396cc30a13a116b2f46d`
  (`#153`). Those merges are git-log measurements, not actions of
  this body.
- Complementary P1 egress deny on isolated worktree
  `/tmp/ofn-p1-egress-deny` from `origin/main`. Destination class is
  not a send. UNKNOWN dest is not FALSE. Timeout does not prove
  concurrent writing. HALT stops `admit_leave` (START) and does not
  stop classify. `campaign_envelope_ready` structurally ≠
  `send_authorized`. Not wired into `run_store.py`. Distinct from
  #126 unknown_seal, #145 send_fence/campaign_bind, #116 write_fence,
  #76 campaign_envelope.
- Docs first-read: MASTER-BLUEPRINT.md and CONTRIBUTING.md **absent**
  on `origin/main` @`72a4c3d`. UNKNOWN, not FALSE. D-27 SHA-256
  `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9`
  (5469 bytes) MATCH. D-28 SHA-256
  `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a`
  (16212 bytes) MATCH. Evidence level B (git blob / this-host file
  hash). Filesystem immutability: UNKNOWN. Not claimed immutable.

## What remains

- Independent CODEOWNERS review of this PR and of already-open
  complementary P1 PRs including #126. Merge blocked until then.
  Engineering not blocked.
- Wiring into `run_store.py` deferred.
- `quote_sent` / `send_authorized` remain owner-blocked (no newer
  scoped authorization after the later disarm/hold).
- Incidents append is on the existing incidents branch, not this
  branch. Do not mint a fifth incidents PR. Do not force-push.

## What failed

- `python3 -m pytest` was absent on this host
  (`ModuleNotFoundError`). stdlib unittest used. Suite green.
- Shell `git push` / `gh pr` are denied by
  `.cursor/hooks/deny_egress.py`. Publish path is the configured
  `open_git_pr` tool.
- PR #126 remains REVIEW_REQUIRED. Not treated as an engineering
  defect.

## Evidence paths

| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| Combined suite | 236 passed / 0 failed / 0 skipped | command below · `2026-09-04T00:06:53Z` · parent `72a4c3d5cea6f0877200396cc30a13a116b2f46d` · exit 0 | E3 | measured this run |
| egress_class tests | 30 passed | `tests/test_egress_class.py` · exit 0 | E3 | measured this run |
| deny_pin tests | 17 passed | `tests/test_deny_pin.py` · exit 0 | E3 | measured this run |
| chaos egress-deny | 10 passed | `tests/test_chaos_egress_deny.py` · exit 0 | E3 | measured this run |
| kernel purity | 10 passed | `tests/test_kernel_purity.py` · exit 0 | E3 | measured this run |
| grants_send | False | `ofn/kernel/egress_class.py` `grants_send()` | E3 | tested |
| ready ≠ authorized | names distinct; both sealed as dest | `tests/test_egress_class.py` `test_ready_is_not_authorized` | E3 | tested |
| D-27 hash | `c55f9085…41ea9` / 5469 bytes | `origin/main` blob of D-27 source | B | MATCH |
| D-28 hash | `c79f0e74…3f28a` / 16212 bytes | this-host file / same path | B | MATCH |
| filesystem immutability | not claimed | this report | — | UNKNOWN |

Command:

```
python3 -X utf8 -m unittest tests.test_egress_class tests.test_deny_pin tests.test_chaos_egress_deny tests.test_kernel_purity tests.test_envelope tests.test_run_store tests.test_token_ceiling tests.test_run_gate tests.test_chaos_owner_absent tests.test_tmpdir -q
```

Receipt pointer:
`docs/octopus-surgery/architecture/2026-09-02/receipts/P1-EGRESS-DENY-20260904.json`
(hash + byte size filled after commit). Filesystem immutability: NOT
claimed.

## Rollback steps

- `git revert` the commit on `feat/p1-egress-deny-20260904`, or delete
  the branch if unmerged.
- Package is additive (new files only). No shared file edited.
- Do not prune the worktree. Do not re-arm send.
