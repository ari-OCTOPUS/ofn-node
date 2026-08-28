# TEST REPORT (2026-08-28T00:14:00Z)
- Discovery: suite = stdlib unittest (pytest.ini collects tests/); no pytest runner installed; wire flags: none exist in-tree (all suites hermetic/fake; no real providers reachable from tests — verified by no_network/test purity suites).
- Command: `python3 -m unittest discover -s tests -p "test_*.py"`
- start 2026-08-28T00:12:10Z · end 00:12:35Z · duration 24.75s
- **2028 tests: 2017 pass, 1 error, 10 skipped** — the single error is `tests/test_greeting_name` (relative-import loader error), proven pre-existing at baseline cc7a65b (isolated worktree run on 2026-08-27). Not hidden; recorded.
- Targeted: `tests.test_gate_enforcement + tests.test_shell_contract` → 58 OK.
- Gate-in-runtime check: gate enforcement lives in http_api routes + action_tiers runtime code, not only test expectations (test_no_public_surface asserts route-level; executor tests assert runtime deny).
- Backup test: performed on temp copies only; no overwrite.
- **Fake E2E**: covered pieces — auth journey (test_e2e, real HTTP, fake sessions), mesh full cycle (fake fixtures: claim→freeze→verdict→settle, live 2026-08-26/27), M1 cockpit journey (ephemeral server, 2026-08-27). **GAP-2**: a single continuous fake lead→proposal→witness→owner-approval→executor→receipt test does not exist as one script.
