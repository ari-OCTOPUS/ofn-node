# LANE-REPORT - L9

## What was done
Wrote pass criterion first (`09-LANES/L9/PASS-CRITERION.md` sha 53223b05). Extended (did not discard) the PC_worker install report. Nothing applied to firewall. No `/etc/` or `src/` edits this session.

Install (kept from prior L9 text, hashes re-checked where files still exist): pack landed; `.cursor/hooks.json` interpreter is `python` not `python3` (file sha d0937b5e this session); ledger 5 rows chain_ok True (`.cursor/hook-ledger.jsonl` sha 78443439).

Proposals below are status: open, requires: owner_decision.

### Proposal 1 — python3 Store alias vs python.exe hooks already patched — residual risk
Evidence: `where.exe python` includes `C:\Program Files\Python313\python.exe` and `C:\Users\Armin\AppData\Local\Microsoft\WindowsApps\python.exe`. `where.exe python3` is `C:\Users\Armin\AppData\Local\Microsoft\WindowsApps\python3.exe`. That python3.exe Length is 0 bytes (Get-Item this session). Install L9 already recorded Store stub exit 9009 if unpatched hooks used python3. Residual risk: any new hook, MCP, or docs that call `python3` still failClosed; App Execution Alias can also shadow `python` if PATH order changes; `python --version` this session is Python 3.13.7 from the Program Files binary. Owner decision: keep `python` in hooks (current), disable Windows python3 alias, or point python3 to Python313. Not applied here.

### Proposal 2 — gitwrite 40-attempt timeout
Evidence: `_ops/backup/GITWRITE-FAILED.flag` sha 75e59b45 text: `GITWRITE-FAILED 2026-09-01_045025 : git-write lock TIMEOUT after 40 attempts on F:\backup\_ops\backup\gitwrite.lock`. `gitwrite.lock` is absent now (Test-Path False). L1 F1 already recorded the same 40 attempts. Owner decision: raise attempts/timeout, failClosed after N, or treat missing lock as recovered and archive the FAILED flag. Not applied here. Firewall not involved.

### Proposal 3 — IMAP timeout errors
Evidence persisted from L1 (governor-alerts.md sha still affb9790, 498913 bytes): 88 IMAP lines, 8 DNS_ERROR lines, last tick 2026-09-01T23:02:48 (`09-LANES/L1/LANE-REPORT.md` sha 9df6f4ea). Mailbox vs DNS root cause remains open per L1. Owner decision: ops on mailbox/DNS, mute, or change governor timeouts. Not applied here.

## What remains
- Cursor Trust workspace / live stop-hook still unverified (install L9 E0).
- python3 alias still 0-byte stub.
- IMAP and gitwrite still open.
- Baselines: persistence used (install L9 + L1 F1/F3 + current hashes). prior-only: this session claims no new patches. random: not used, not beaten.

## What failed
- python3 alias not removed (requires owner_decision / OS settings).
- gitwrite timeout not retuned.
- IMAP errors not diagnosed beyond L1 counts.
- Firewall/security-header plans: none applied; no /etc/ read this session. Header/firewall remains a proposal-only gap unless owner supplies an existing vault file (unverified beyond "not applied").

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| criterion hash | 53223b05 | 09-LANES/L9/PASS-CRITERION.md | E2 | verified |
| hooks.json sha | d0937b5e | .cursor/hooks.json | E2 | verified |
| python3.exe length | 0 | C:\Users\Armin\AppData\Local\Microsoft\WindowsApps\python3.exe | E2 | verified |
| python version | 3.13.7 | python --version this session | E2 | verified |
| gitwrite flag | 40 attempts, 2026-09-01_045025 | _ops/backup/GITWRITE-FAILED.flag sha 75e59b45 | E2 | verified |
| gitwrite.lock | absent | Test-Path | E2 | verified |
| IMAP counts | 88 IMAP, 8 DNS_ERROR | L1 report sha 9df6f4ea citing governor-alerts.md sha affb9790 | E2 | verified (persistence) |
| firewall applied | no | this session; forbidden /etc/ | E2 | verified not applied |
| live stop-hook | not run | install L9 | E0 | unverified |

## Rollback steps
Replace `09-LANES/L9/LANE-REPORT.md` and `PASS-CRITERION.md` by moving this version to `99-ARCHIVE/` with `archive_` prefix and restoring the install-only report from git if needed. Do not rm -rf. Do not change firewall, `/etc/`, `src/`, or hook interpreters in this rollback.