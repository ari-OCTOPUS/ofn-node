# LANE-REPORT — P1-DIGEST-SYNC (session 2026-09-06T21:58Z)

Lane declared: P1-DIGEST-SYNC (MEASURE complementary — installer
contract). `09-LANES/LANE-MATRIX.csv` has L0–L9 only (no P1 row).
Did not edit LANE-MATRIX.csv.

Declared file-lock zone: `/tmp/ofn-221-digest-sync` on
`feat/p1-digest-sync-install-20260906` parent
`db23439c9aa7ddb00f18d99073322c165422736f` (#221 merge of main).
`/workspace` stayed on
`cursor/bc-a676ae1c-d61f-4355-b8c1-0a61304974aa-cb04` @`db23439`
and was not written.

## What was done

- Trigger: check-suite failure on `feature/systemd-digest-sync`
  @`db23439c9aa7ddb00f18d99073322c165422736f` (PR #221; jobs
  101565091639 ubuntu-latest and 101565091634 windows-latest).
  Independently confirmed from the ubuntu failed-step log:
  `TestEveryReferencedUnitExists.test_the_installer_installs_every_unit`
  SUBFAILED for `ofn-digest.service`, `ofn-digest.timer`,
  `ofn-sync.service`, `ofn-sync.timer`. CI summary
  **4 failed / 5815 passed / 15 skipped** @ 2026-09-06T21:53:58Z
  (source: `gh run view --job 101565091639 --log-failed`).
  Windows full log not independently re-read this-run — UNKNOWN,
  not FALSE. Same assertion class is the only named failure in
  the trigger annotation.
- First-read: `docs/octopus-os/MASTER-BLUEPRINT.md` and
  `CONTRIBUTING.md` **absent** on this body and on this-host
  `origin/main` @`b8340d0e757a7563583d99672b2912c30db03af3`
  (`#224`; `git ls-remote` 2026-09-06T21:57Z). UNKNOWN, not FALSE.
  Repo-root `D-27-UNLOCK-DIRECTIVE.md` / `D-28-EDGE-RUNBOOK.md`
  absent (present under
  `docs/octopus-surgery/stage-01-lineage-scan/2026-09-01/sources/`).
  D-27 pointer SHA-256
  `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9`
  (5469 bytes) MATCH vs session kkk. D-28 pointer SHA-256
  `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a`
  (16212 bytes) MATCH. Evidence level B. Filesystem immutability
  UNKNOWN. Not claimed immutable.
- #221 already contains `origin/main` (`git merge-base --is-ancestor`
  `b8340d0` `db23439` YES). F-06 stale-base is not the blocker.
  Engineering defect: unit files shipped, installer never copied.
- Isolated follow-up (not a second digest-sync PR): added four
  `install -m 0644` lines to `deploy/install.sh`. Comment pins
  "Copied but NOT enabled" and "Copy is not a start". Did not
  add `systemctl enable` or `systemctl start` for digest/sync.
  Did not rewrite unit files (`git diff -- deploy/systemd` empty).
  Did not enable outbound flags. Did not add digest/sync to the
  owner NEXT `enable --now` hint.
- Tests added in `tests/test_units.py`:
  `TestDigestSyncCopiedNotEnabled` (copy via install; executable
  lines never enable/start; NEXT block does not name digest/sync;
  outbound flags stay 0; copy-is-not-a-start comment).
- `campaign_envelope_ready` structurally ≠ `send_authorized`.
  Ready ≠ authorized. Copy ≠ enable ≠ send.

## What remains

- Push this follow-up to `feature/systemd-digest-sync` and reuse
  PR #221. Independent CODEOWNERS review. REVIEW_REQUIRED blocks
  merge, not engineering.
- Full-suite CI on ubuntu/windows after publish is UNKNOWN until
  the check suite re-runs.
- Incidents append is a separate lock-zone
  (`/tmp/ofn-inc-ppp` on published `ec18b68`). Do not mint a
  sixth incidents PR. Do not force-push.
- `quote_sent` / `send_authorized` stay owner-blocked until an
  explicit, newer, scoped authorization exists.
- Unpublished prior-memory follow-up `9181baf955c4bc816d8332f331317ec18a087d4b`
  remains first identifier for that object (ABSENT this body).
  This-body follow-up is a new object on the same PR.

## What failed

- CI on #221 @`db23439` (this trigger): installer never copied
  the four digest/sync units. That is the defect this follow-up
  addresses.
- `python3 -m pytest` is absent on this image
  (`ModuleNotFoundError`). Canonical run used stdlib unittest.
- `gh pr view` deny_egress. Open-PR rollup otherwise UNKNOWN.
  `git ls-remote` used for #221 / #187 / main / incidents.

## Evidence paths

| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| Related suite | 356 passed / 0 failed / 0 skipped / exit 0 @ 2026-09-06T21:58:56Z / parent `db23439c9aa7ddb00f18d99073322c165422736f` | docs/octopus-surgery/architecture/2026-09-06/receipts/P1-DIGEST-SYNC-INSTALL-20260906.json | E3 | verified |
| test_units | 11 passed (loader count 2026-09-06T21:58:56Z) | tests/test_units.py | E3 | verified |
| CI ubuntu @db23439 | 4 failed / 5815 passed / 15 skipped @ 2026-09-06T21:53:58Z | gh run view --job 101565091639 --log-failed | E2 | verified |
| CI windows @db23439 | exit 1 | trigger annotation job 101565091634 | E1 | UNKNOWN full log |
| D-27 blob | sha256 c55f9085… / 5469 bytes | this-host file | E2 | verified |
| D-28 blob | sha256 c79f0e74… / 16212 bytes | this-host file | E2 | verified |
| MASTER-BLUEPRINT / CONTRIBUTING on main | absent | origin/main @b8340d0 | E0 | UNKNOWN, not FALSE |
| Filesystem immutability | not claimed | — | E0 | UNKNOWN |
| Unit files rewritten | no (diff empty) | git diff -- deploy/systemd | E2 | verified |

## Rollback steps

1. Revert the follow-up commit that edits `deploy/install.sh` and
   `tests/test_units.py` on `feature/systemd-digest-sync`.
2. Do not delete archives or prune worktrees.
3. Do not rewrite unit files. Do not enable digest/sync timers.
4. Do not open a second digest-sync PR. Do not weaken gates.
