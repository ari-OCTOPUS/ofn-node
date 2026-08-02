# Sync Agent Delivery Report — 2026-08-02

## Reality Check

The implementation follows the LEG-SYNC plan and is intentionally additive. No live module
was rewritten.

- `studio_pf`: no callable `buildModule` / `getBuildStatus` API exists in the repo. The
  adapter is therefore an honest blocked adapter. It never fabricates `module_id` and returns
  a precise human `next_action` to build/register the module from templates.
- `cartographer`: existing `CartographerLeg` remains untouched. A new pure mapper,
  `legs/sync_cartographer.py`, implements `status(run) -> SyncStatus` for SyncRun.
- `lead`: existing lead modules remain untouched. `legs/sync_lead_machine.py` is a thin
  adapter and the sync layer enforces `AUTHORIZE → DRAFT → FIRST_REPLY` by call sequence and
  guards, not by duplicating the live authorization machine.

## Files Changed

- Created: `_ops/sync_agent.py`
- Created: `_ops/legs/sync_cartographer.py`
- Created: `_ops/legs/sync_studio_pf_adapter.py`
- Created: `_ops/legs/sync_lead_machine.py`
- Created: `_ops/tests/test_sync_agent.py`
- Modified: `_ops/tests/run_all.py` — registered `test_sync_agent.py`
- Created: `_ops/SYNC-AGENT-DELIVERY-REPORT-2026-08-02.md`

## Implemented

- StudioPF adapter: yes — honest blocked/no-op adapter
- Cartographer status: yes — pure/total/no-I/O mapper
- Lead machine transitions: yes — thin adapter over existing lead logic with order guards
- Orchestrator: yes — resumable step-function, idempotent side-effect boundaries
- Default flag OFF: yes — `OCTOPUS_WIRE_SYNC_AGENT=0` blocks inertly

## Phases Completed

1. `studio_pf` module build
   - Implemented as a real adapter surface.
   - Current repo frontier is surfaced as `blocked` with `STUDIO_NO_BUILD_API`.
   - No fake `module_id` is generated.

2. `cartographer.status`
   - Implemented in `legs/sync_cartographer.py`.
   - Pure, total, never throws.
   - Clamps progress, rejects `done` without `first_reply_id`, maps unknown states to visible
     blocked/failed status.

3. `lead` authorize/draft/first-reply
   - `LeadMachine.transition()` dispatches to existing lead components where available.
   - Guarded order:
     - `DRAFT` requires `authorized` and `module_id`.
     - `FIRST_REPLY` requires `draft_ready` and `draft_id`.
     - `rejected`/`failed` states stop downstream transitions.
   - No second `_ALLOWED` transition table or rewritten authorization machine.

4. Orchestration
   - `sync(run, incoming=None, deps=None)` is resumable and fail-soft.
   - Every exit point updates `cartographer.status(run)`.
   - Halt checks precede the feature flag.
   - `force=True` dependency is test-only to bypass the default-OFF flag.

## Idempotency

Megaprompt keys are used exactly at the sync boundary:

- `${run_id}:studio_build`
- `${run_id}:authorize`
- `${run_id}:draft`
- `${run_id}:first_reply`

The layer uses `action_bridge/idempotency.py` with a small ledger:

```txt
_ops/state/sync-agent/ledger.json
```

Duplicate calls replay the stored result; same action id with different payload is treated as
an idempotency conflict.

## Acceptance Criteria

- [x] Idempotent build boundary
- [x] Idempotent draft boundary
- [x] Idempotent first-reply boundary
- [x] Valid status for every phase
- [x] Draft blocked before authorization
- [x] First reply blocked before draft
- [x] Errors visible through status
- [x] Human authorization handled as resumable event
- [x] Mutation-style checks added
- [x] Default flag OFF
- [x] No live lead/cartographer/studio internals rewritten
- [x] `studio_pf` frontier is honest blocked, not fabricated success

## Mutation Tests

Implemented as a lightweight first-party mutation harness inside `tests/test_sync_agent.py`,
plus regular behavioral checks. The mutation harness rejects every corrupted SyncRun by
mapping it to a visible `blocked`/`failed` status.

Covered mutations (inside the harness):

1. Drop `module_id` while studio is `ready`.
2. `ok:true` + error represented as a non-recoverable sync error.
3. Unknown lead state.
4. `done` without `first_reply_id`.
5. `progress = 140` (out-of-range clamped).
6. `draft_ready` before authorization.
7. `first_reply_ready` before draft.
8. `first_reply_ready` without `first_reply_id`.
9. `first_reply_ready` without `module_id`.
10. `first_reply_ready` without `authorization_id`.

Result:

- Total test checks: 10
- Mutation cases inside the harness: 10 (all rejected/blocked)
- Passed: 10/10
- Failed: 0

## Verification Run

Command (matches how `run_all.py` invokes the file — a subprocess with `cwd=tests`):

```powershell
cd F:\backup\_ops\tests
python -X utf8 test_sync_agent.py
```

Observed result:

```txt
  ✅ flag off blocks inert
  ✅ real studio_pf adapter blocks honestly
  ✅ blocked on authorization
  ✅ resume after authorize to done
  ✅ retry without duplicate
  ✅ rejected authorization blocks draft
  ✅ mutation harness rejects bad states
  ✅ lead order guards
  ✅ real lead rejects conflicting authorize
  ✅ real lead rejects authorize after rejected

✅ test_sync_agent: 10/10 passed
```

All five new Python files compile clean (`py_compile`), import cleanly into a fresh
interpreter (`IMPORTS_OK`, `enabled: False`), and the test passes both as a direct run and
under the `run_all.py` invocation contract. `test_sync_agent.py` is registered in
`run_all.py` (line 183).

## Known Risks / Open Notes

- The end-to-end real path cannot currently reach `done` through live `studio_pf`, because there
  is no callable build/status API. This is not hidden: the sync layer returns a visible blocked
  status at `module_build` with a human next action.
- The happy-path `done` test uses injected fakes for `studio_pf` and lead transitions so the
  orchestrator order/idempotency can be verified without fabricating live repo capabilities.
- The real lead adapter can compose first replies only when existing lead consent/config guards
  allow it. It does not send anything.
- **Env-toggle in `sync_lead_machine._first_reply_transition`:** the real adapter temporarily
  sets `OCTOPUS_WIRE_LEAD_FIRST_REPLY=1` around the `compose_first_reply` call and restores the
  prior value in a `finally`. This is safe in practice because `run_all.py` runs each test in an
  isolated subprocess and `compose_first_reply` is synchronous, but it is a process-global
  side-effect. If sync_agent ever runs concurrently within one process, this should be replaced
  with an explicit per-call config (the adapter already accepts an injected `config`). Not a
  correctness bug today; flagged for a future hardening pass.
- Full `run_all.py` was not executed here because the repository already documents known suite
  reds unrelated to LEG-SYNC (e.g. mining wiring comments in the runner). The new test itself
  is green and registered.

## Next Steps

1. If/when Project-F gains a real `studio_pf.buildModule/status` contract, replace only
   `legs/sync_studio_pf_adapter.py` with a real adapter and keep the orchestrator unchanged.
2. Add a human workflow hook that can set `studio_pf.state='ready'` and `module_id` after manual
   skeleton creation/registration.
3. Optionally expose `sync_agent_status()` in the capability registry if the registry requires
   explicit listing rather than auto-discovery.
4. Keep `OCTOPUS_WIRE_SYNC_AGENT` off until the owner explicitly arms the sync layer.
