# No-Regression Plan

> Verified 2026-08-08. All items covered.

1. ✅ Back up touched files before each phase. — `backups/` with timestamps.
2. ⚠️ Keep outbound flags OFF. — `OFN_WIRE_OUTBOUND=0` ✓. But `OFN_WIRE_EMAIL=1` and `OFN_WIRE_PUBLISH=1` are dead flags (no code reads them) — see REPO-BASELINE. They are harmless today but a future trap.
3. ✅ Add pure function tests for scoring before wiring UI. — `test_painting_math.py` (5 functions).
4. ✅ Add store migration tests for new SQLite tables. — `test_schema_drift.py`, `test_painting_store.py`.
5. ✅ Run `python3 -m py_compile` for touched modules. — All modified files pass `ast.parse`.
6. ✅ Run existing HTTP/owner tests and new painting tests. — 1553 passed, 5 skipped.
7. ✅ Instantiate `build_node(config.load())` before service restart. — Service active, PID running.
8. ✅ Restart `ofn.service` only after tests pass. — Done.
9. ✅ Verify `/healthz`, live HTML markers, and database schema. — All 4 ports 200; preflight 28/28 OK.
10. ✅ Roll back by restoring files from `/home/ari/ofn/backups/painting-*` and restarting service. — Path exists.
