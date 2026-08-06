# No-Regression Plan

1. Back up touched files before each phase.
2. Keep outbound flags OFF.
3. Add pure function tests for scoring before wiring UI.
4. Add store migration tests for new SQLite tables.
5. Run `python3 -m py_compile` for touched modules.
6. Run existing HTTP/owner tests and new painting tests.
7. Instantiate `build_node(config.load())` before service restart.
8. Restart `ofn.service` only after tests pass.
9. Verify `/healthz`, live HTML markers, and database schema.
10. Roll back by restoring files from `/home/ari/ofn/backups/painting-*` and restarting service.
