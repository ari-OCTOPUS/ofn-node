# Controlled capability test report

- Recorded at: `2026-08-25T13:15Z`
- Test environment: offline tempfile/synthetic fixtures; no live database writes
- Dependency installs: `0`
- New models: `0`
- Live schema changes: `0`

## Commands and results

`python3 -m py_compile` passed for:

- `ofn/organism/growth/capabilities.py`
- `ofn/organism/growth/controlled.py`
- `ofn/organism/runtime/app.py`
- `ofn/organism/tests/test_controlled_growth.py`
- `artifacts/capability-awakening/run_canary.py`

Targeted controlled-growth, GET/LAN, and memory-gate suite:

- Tests run: `27`
- Passed: `27`
- Failed/errors: `0`

Complete organism suite:

- Tests run: `145`
- Passed: `144`
- Skipped: `1`
- Failed/errors: `0`
- Runtime: `6.859s`

The skipped test is the pre-existing optional `cbor2` canonicalization test; `cbor2` is not installed and no install was attempted.

## Controlled safeguards proven

- Capability histories reject skipped forward transitions.
- Active Inference cannot advance beyond `SHADOW`.
- Any forbidden registry invariant change is rejected.
- Self-model gap output is a non-executable `CapabilityProposal` with evidence IDs, confidence, uncertainty, and a local test.
- Consolidation records all source IDs/hashes/model/version, creates one provenance-bearing episode, and leaves raw event hashes unchanged.
- Local hypothesis uses five bounded loopback cortex calls, records only local telemetry, and makes no causal claim.
- One real heartbeat authorizes at most one experiment.
- One execution allows at most three experiments.
- Every experiment requires a successful memory receipt/evidence bundle.
- Result and complete receipt writes use the official event kernel and existing episodic writer.
- GET capability inspection remains state-pure.
- LAN token authentication and request-size limits remain intact.
- `executable_total=0`, external calls are absent, and no WAN path is imported into controlled growth.

TEST_STATUS: `PASS_TESTED`
