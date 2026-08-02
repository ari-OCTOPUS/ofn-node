# G-03 / Human Interaction Wiring Report

Generated: 2026-08-02
Root: `F:\backup`

## Completed

- Confirmed `lead_outbound_transport.py` is live-wired to `OutboundWriteAheadLedger` behind `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL`.
- Confirmed `telegram_center/center.py` has the AGI2027 owner-control hook before ordinary command handlers.
- Added owner-only outbound resolution commands:
  - `/outbound mark-sent <effect_id>`
  - `/outbound cancel <effect_id>`
  - `/outbound retry <effect_id>`
- Added terminal-state guards so terminal effects are not silently rewritten:
  - sent effects cannot be cancelled afterward
  - failed/cancelled effects cannot be marked sent
  - retry never reuses the same `effect_id` and never auto-sends
- Added Telegram-safe formatting for outbound effect transitions and explicit `auto_resend=false`.
- Added tests for mark-sent, cancel, retry, and bad effect-id rejection.

## Enabled managed flags

`_ops/agi2027_runtime/managed_flags.json`:

```json
{
  "OCTOPUS_WIRE_TG_CONTROL": "1",
  "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "1",
  "OCTOPUS_WIRE_VALUE_LEDGER": "1"
}
```

## Verified

- `py_compile`: PASS
- `agi2027_control`: 23/23 PASS
- `lead_outbound_transport`: 17/17 PASS
- `test_tg_center`: 39/39 PASS
- `git diff --check`: PASS

## Files changed in this pass

- `_ops/agi2027_control/runtime.py`
- `_ops/agi2027_control/integration.py`
- `_ops/agi2027_control/tests/test_runtime.py`
- `_ops/implementation_reports/G03-HUMAN-INTERACTION-WIRING-2026-08-02.md`

Existing live wiring observed from previous pass:

- `_ops/legs/lead_outbound_transport.py`
- `_ops/telegram_center/center.py`
- `_ops/agi2027_runtime/managed_flags.json`

## Owner-facing commands now available after Telegram center restart

- `/ops`
- `/outbound status`
- `/outbound recover`
- `/outbound mark-sent <effect_id>`
- `/outbound cancel <effect_id>`
- `/outbound retry <effect_id>`
- `/repair execute repair.g03.writeahead_outbound`
- `/repair rollback repair.g03.writeahead_outbound`

## Honest boundaries

- Tests use injected fake SMTP; no real email was sent by tests.
- If the Telegram center process is already running, restart it so it loads changed Python files.
- Project-F remains blocked until `PROJECTF_API_BASE_URL` and `PROJECTF_API_TOKEN` are configured and owner approval is given.

## Clean-diff pass (2026-08-02, ZCode)

A previous parallel pass had rewritten `telegram_center/center.py` whole-file, producing a
~9000-line diff (4571 insertions / 4546 deletions) even though only 25 lines were the real
control-plane hook. Diagnosis: the file was re-indented/re-emitted, so nearly every line
showed as changed. This pass restored `center.py` to a clean HEAD and re-inserted **only**
the 25 AGI2027/Owner-Control-Plane lines at the exact anchor (`chat_id = ...` → before the
OWNER_AUTH block), preserving indentation. Result:

```text
git diff --stat _ops/telegram_center/center.py
 _ops/telegram_center/center.py | 25 +++++++++++++++++++++++++
 1 file changed, 25 insertions(+), 0 deletions(-)
```

`git diff --ignore-all-space` confirmed the 25 lines are the **only** real change — no hidden
whitespace or content churn. All suites re-verified green after the clean re-insertion:

- `test_tg_center`: 39/39 (exit 0)
- `test_lead_outbound_transport`: 17/17 (exit 0)
- `agi2027_control`: 23/23 (exit 0)
- `test_sync_agent`: 10/10 (exit 0)

## Rollback

- Set `OCTOPUS_WIRE_LEAD_OUTBOUND_WAL=0` in `_ops/agi2027_runtime/managed_flags.json` to disable WAL behavior.
- Set `OCTOPUS_WIRE_TG_CONTROL=0` to disable Telegram control commands.
- Revert `_ops/agi2027_control/runtime.py`, `_ops/agi2027_control/integration.py`, and `_ops/agi2027_control/tests/test_runtime.py` if code rollback is required.

---

## Final live verification — 2026-08-02

Final committed state:

- Production wiring commit: `50de1c8 wire owner-controlled G03 outbound WAL`
- Support files commit: `c5a047e track agi2027 control support files`
- Cleanup: `center.py` hook line endings checked/fixed after final wiring

Live Telegram smoke:

- `/ops` → OK
- `/outbound status` → OK
- `/now` → passthrough OK

Outbound WAL status observed:

```json
{"failed": 1, "sent": 4}
```

Flags:

```json
{
  "OCTOPUS_WIRE_TG_CONTROL": "1",
  "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "1",
  "OCTOPUS_WIRE_VALUE_LEDGER": "1"
}
```

Tests:

- `python _ops\agi2027_control\run_tests.py`
- Result: `Ran 23 tests — OK`

Honest remaining boundary:

- No real customer email smoke has been performed yet.
- Project-F remains blocked until `PROJECTF_API_BASE_URL` and `PROJECTF_API_TOKEN` exist.
- Full `python -m pytest _ops -q` is not a valid current gate because an older test module exits during pytest collection.
