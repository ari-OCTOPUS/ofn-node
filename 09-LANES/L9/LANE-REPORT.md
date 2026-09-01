# LANE-REPORT — L9 (PC_worker install 2026-09-01)

## What was done
Installed OCTOPUS Cursor governance pack into vault root `F:\backup` only:
- `AGENTS.md`
- `.cursor/hooks.json` (interpreter set to `python`, not Store stub `python3`)
- `.cursor/mcp.json` (same interpreter change; previous file was empty `mcpServers`)
- `.cursor/hooks/*.py`, `.cursor/rules/*.mdc`
- `09-LANES/` matrix + L1 template
Offline hook smoke: egress/rm/.env/flag/unknown-MCP all denied, ledger chain 5 rows intact.

## What remains
- Cursor must Trust this workspace or project hooks will not run
- `python3` App Execution Alias still broken; keep `python` in hook commands
- Verify table items that need a live agent session (exit gate / stop hook) untested here
- Dirty vault working tree NOT included in this commit

## What failed
- `python3` on PATH is Microsoft Store stub (exit 9009). Unpatched hooks would failClosed and halt the repo.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| Pack landed | AGENTS.md sha e17ab4df | F:\backup\AGENTS.md | E2 | verified runtime hash |
| Egress deny | permission deny + ledger egress_denied | .cursor/hook-ledger.jsonl | E2 | verified |
| Destructive deny | rm -rf denied | .cursor/hook-ledger.jsonl | E2 | verified |
| Secret deny | .env denied | .cursor/hook-ledger.jsonl | E2 | verified |
| Flag incident | OCTOPUS_WIRE_X=1 denied | .cursor/hook-ledger.jsonl | E2 | verified |
| MCP allowlist | server evil denied | .cursor/hook-ledger.jsonl | E2 | verified |
| Ledger chain | 5 rows chain_ok True | .cursor/hook-ledger.jsonl | E2 | verified |
| Stop-hook exit gate | not run in live Cursor session | n/a | E0 | unverified |
| Trust workspace | owner UI | n/a | E0 | unverified |

## Rollback steps
1. `git rm -r --cached` is not required. `git checkout HEAD --` will not work if this is the first add; delete:
   `AGENTS.md`, `09-LANES/`, `.cursor/hooks.json`, `.cursor/hooks/`, `.cursor/rules/`, restore previous `.cursor/mcp.json` (`{"mcpServers":{}}`).
2. Keep `.cursor/debug-*.log` untouched.
3. Do not `rm -rf`. Move mistakes to `99-ARCHIVE/` with `archive_` prefix.
