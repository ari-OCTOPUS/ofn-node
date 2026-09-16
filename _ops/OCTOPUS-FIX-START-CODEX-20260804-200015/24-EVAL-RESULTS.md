# 24 — Eval results

```
=== P0 minimal eval harness - 2026-08-04 ===

[PASS] arm_gate (baseline, unittest) (test_arm_gate.py)
[PASS] arm_gate (#30 P0 sensitive-default) (test_arm_gate_p0.py)
       Pass: 12, Fail: 0
[PASS] latent_space (baseline) (test_latent_space.py)
[PASS] latent_space (#53 P0 fail-closed) (test_latent_space_fail_closed.py)
       Pass: 6, Fail: 0
[PASS] intel_spine (L0-L8 + redaction + no-outbound) (test_intel_spine.py)
       Pass: 16, Fail: 0
[PASS] adapters (telegram/webapp/obsidian) (test_adapters_obsidian.py)
       Pass: 15, Fail: 0

ALL GREEN
```
Exit code: 0. Total individual checks across all 6 files: **79 pass, 0 fail**
(16 unittest + 12 + 14 + 6 + 16 + 15). Full per-file raw output archived in
`test_outputs/`.
