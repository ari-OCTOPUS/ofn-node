# Receipt — first real generation of SYSTEM-SELF-MODEL.json (Lane LA)

| field | value |
|---|---|
| command | `python -X utf8 -m ofn.adapters.self_model_producer --repo . --output state/self-model/SYSTEM-SELF-MODEL.json` |
| cwd | `F:\wt-self-awareness` (branch `lane/self-awareness`) |
| exit code | 0 |
| timestamp (generated_at) | 2026-09-02T08:25:52Z |
| commit reported by the model | `5f46b113eabef62ffd5a3fb8f0594cb1f7aa4eb8` (the lane DoD commit — the model read it from git itself) |
| artifact sha256 | `41c21e53a5580dade775f24e1d89b0325c7f31fe3cb2c413b7aee69261464b7b` |
| semantic digest | `4ace898e3c5f3f2efa985556ba50cb15da2df37703c19c58cab27ae2686555cc` |
| evidence copy | `docs/lanes/LA-SELF-AWARENESS/evidence/SYSTEM-SELF-MODEL-20260902T0825Z.json` (byte-identical, sha256 above) |
| model status | `unverifiable` — honest: 18 healthy readings, 0 absent, 1 unknown (brain probe: no dated run evidence on this host) |

## Host measurement findings (this Windows dev host, 2026-09-02)

- Loopback probes of the five Day-7 board ports returned **connected for 8771/8772/8773/8774** and **timeout for 8776**. The four "connected" results are almost certainly a local relay (Hyper-V/WSL port forwarding), not the board members — the model records exactly what was measured, with `tcp:127.0.0.1:<port>` as the source of each value, and does not interpret beyond the measurement.
- A closed loopback port on this host raises `TimeoutError` (not `ConnectionRefusedError`) — measured directly; `probe_port` therefore reports dead ports on this OS as inconclusive (`unknown`), never as absent-by-guess and never as alive.

## Test receipts

- Lane tests: `python -X utf8 -m pytest tests/test_self_model.py tests/test_self_model_producer.py -q` → **43 passed** (exit 0, 2.23s).
- Full CI suite (CI command verbatim): **2554 passed / 21 skipped / 0 failed** in 54.09s — baseline at base `33c9476` was 2511 passed / 21 skipped / 0 failed; delta = +43 = exactly the lane's new tests, zero regressions.
- Root hygiene: `python -X utf8 tests/test_root_hygiene.py` → `ROOT_HYGIENE_PHASE1_PASS`.

## Secret scan

- The artifact contains commit shas, loopback ports, and repo-relative paths only — no credentials, tokens, or key material (manually verified line by line; gitleaks binary not present on this host — noted as `unverified-tool`).
