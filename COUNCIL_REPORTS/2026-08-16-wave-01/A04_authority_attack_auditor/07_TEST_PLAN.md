# A04 — TEST PLAN

Proposed tests only — none executed (READ_ONLY). All runnable offline, `$0, no network, no side effects beyond temp dirs.

## T1 · PolicyGate approval semantics (target: F-005)
- Construct RequestContext with `approval_id="forged"`, action in approval_actions → expect ALLOW from the gate layer (documents the gap), then assert the *caller-side* verifier rejects it. If callers have no verifier, this test fails red today — that's the finding made executable.

## T2 · Gate wiring invariants (target: F-003, F-004, F-006)
- Static test: import graph assertion that no module outside `octopus_v3/`/`tests/` imports `octopus_v3` (proves WIRED=False mechanically, alerts the day someone wires it silently).
- Same for `containment.` imports outside `containment/`.
- Positive test: `wiring.request_protective_halt` and `owner_console.collaborator.handle` produce `policy.*` events in evidence_plane log (talk path enforcement alive).

## T3 · Shell deny-list adversarial suite (target: F-001/F-002) — `check()` only, never `run()`
- For each expected-DENY pattern (rm -rf, git push, .env access, curl, sudo, schtasks, STOP-file touch) assert `shell_capability.check(cmd)[0] is False`.
- For each known GAP (`python -c "import shutil…"`, `pip install x`, `echo … > _ops/wiring.py`, `git add -A && git commit`) assert current behaviour and mark `xfail` — flip to DENY-expectation when OD-B lands.
- Assert `active()` fail-closed matrix: no flag → False; flag+STOP → False; halted → False.

## T4 · code_autonomy gates (target: F-007) — extend existing suites
- `allowed_target` traversal battery: `..\\..\\.git`, drive-letter, UNC, nul-byte, symlinked state path, `_ops/state/../policy/x` → all reject.
- 8-gate ordering: any single gate falsified → no write, no commit, audit row present.
- STOP-file precedence: ACTIVATION armed + STOP present → `active()` False (matches live T0 observation).

## T5 · Injection fences (target: F-009, F-010)
- `web_research` mocked-opener returning a page containing instruction-like text → assert output written to research-latest.json IS fenced/marked (red today).
- `vault_bridge.search_vault_evidence` output schema includes trust/provenance field (red today).
- Quarantine plane: `evidence_plane.quarantine.admit(text with injection_signals=True)` → `may_draft_reply` False.

## T6 · Telegram auth & approvals (target: F-011, F-023)
- Non-owner update (`from.id` ≠ env owner) through `handle_update` → None, disposition logged, zero handler side effects (shell/restart/approve unreachable).
- approval_store: double-approve second call returns False (atomic single-use); expired job + `OCTOPUS_WIRE_CB_TOKEN=1` + wrong HMAC → rejected; destination ≠ owner/center chat → rejected.
- `/sh` handler unit: `_is_owner` False → `_shell_cmd` never invoked (mock import).

## T7 · Loopback servers (target: F-013, F-028)
- cortex `/ask` POST with `Origin: https://evil.example` → 403; no Origin/Referer (curl) → allowed; guard module unimportable → 503 (fail-closed) unless OCTOPUS_HTTP_AUTH explicitly off.
- board_cp: no cert → server exits; wrong/absent Bearer → 401; `is_armed()` False → pull returns 503 with empty queue.

## T8 · Recovery non-expansion (target: F-019)
- model_router with both providers failing → returns None-tier with reason, never falls back to a higher-authority executor.
- `freeze_autonomy` on canary red writes KILL file + alert (idempotent).
- cortex revive duplicate-safe: second launch while 8772 alive exits `:already` (assert via log, not by executing on live system — run in temp copy).

## T9 · Secrets hygiene (target: F-014)
- Repo-wide test: no file matching `*.env*` outside `.gitignore`d set is tracked (`git ls-files` assertion); `mail_credentials.resolve()` dict contains no password key (structure assertion, no values).
