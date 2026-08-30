---
type: evidence
schema: octopus-heart-g4-bounded-read-root-cause/1
status: ROOT_CAUSE_FIXED_AND_VERIFIED
created: 2026-08-25
scope: test-infrastructure-only
---

# G4 validation blocker — `test_bounded_read.py` timeout

## Symptom

The first complete official runner stopped at `_ops/tests/test_bounded_read.py` with:

```text
subprocess.TimeoutExpired ... test_bounded_read.py ... timed out after 300 seconds
```

This happened after all registered G4 tests had already passed:

- `test_pulse_arbiter.py`
- `test_arbiter_consensus_rule.py`
- `test_pulse_arbiter_wire_readiness.py`
- `test_pulse_arbiter_authority.py` (`26/26` in that run)

## Isolation result

Each `t_*` function was run in a fresh Python process with a separate 180-second timeout. Eleven functions passed. Only this function timed out:

```text
t_k_100_consecutive_config_stalls_keep_cache_and_workers_bounded
```

Evidence: `BOUNDED-READ-INDEPENDENT-TIMINGS.json`.

## Root cause

The fixture globally replaced `Path.read_text` with a function that sleeps 10 seconds. Inside its 100-iteration stress loop it then called:

```python
pfile.write_text(...)
```

On this pathlib implementation, that write path was affected by the same monkeypatched path-method stack, so the fixture unintentionally stalled its generation-changing writes by 10 seconds per iteration. That alone gives a lower bound near 1,000 seconds.

Even without the accidental write stall, the loop used the production `ConfigManager` reader deadline (3 seconds) one hundred times serially, which is approximately the official runner's entire 300-second per-file timeout. This tested elapsed wall time, not bounded worker growth.

This was a fixture defect, not a production deadlock and not a G4 authority failure.

## Fix

Only the test fixture changed:

1. Generation-changing writes use `pfile.open("w")`, bypassing the monkeypatched read fixture.
2. `ConfigManager`'s existing injected-reader seam is used with the same real `bounded_io.read_text` path and a 50ms test deadline.
3. The stress contract remains unchanged: 100 consecutive stalled reads must preserve last-known-good state and keep active workers at or below 4.
4. Production `bounded_io.py`, `config_manager.py`, `center.py`, and `tg_api.py` were not changed.

## Verification

```text
test_bounded_read: 12/12 PASS
run_all.py --only ... test_bounded_read ... : exit 0
```

The corrected test still exercises real worker saturation/recovery, but it completes within a bounded validation budget instead of guaranteeing a runner timeout.
