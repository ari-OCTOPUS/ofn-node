# Exact command — L7-authorized host only (not executed)

GOV_VERSION=V8 · LADDER=L2 · may_authorize=false  
This file is a command card. L7 did **not** run it.

## Preconditions (all required)

1. Isolated self-cert green: `python -B -X utf8 -m pytest tests/contract/test_memabl_obs_preflight_hash_selfcert.py -q --noconftest`
2. `assert_ready_to_preregister` PASS on every frozen source file. **This host 2026-09-08: FAIL** (CRLF text vs byte on three `octopus_observation/*.py`).
3. Owner vote to edit the N3V2 runner allowlist so `fixture.seed=314159` is accepted. Current allowlist: 271828, 141421 only (`n3b_memabl_obs.py` lines 79–80). L7 must not make that edit.
4. Output path on the authorized lane/host. Do not write octo-exec receipts from L7.
5. `F:\ofn-node\HALT` absent.
6. Thresholds already locked in `MEMABL-OBS-THRESHOLDS-LOCKED-314159.json`. Do not change them after launch.

## Command (after preconditions)

```text
python -B -X utf8 ^
  F:\octo-exec\N3V2-MATH-20260905T031103Z\harness\n3b_memabl_obs.py ^
  --config F:\backup\09-LANES\L7\MEMABL-OBS-PREREG-314159.json ^
  --source F:\octo-exec\N3V2-MATH-20260905T031103Z\n3-candidate ^
  --output <AUTHORIZED-LANE-RECEIPT-PATH>\MEMABL-314159-obs.json
```

Then, once, the matching verifier:

```text
python -B -X utf8 ^
  F:\octo-exec\N3V2-MATH-20260905T031103Z\harness\n3b_memabl_verify.py ^
  --config F:\backup\09-LANES\L7\MEMABL-OBS-PREREG-314159.json ^
  --source F:\octo-exec\N3V2-MATH-20260905T031103Z\n3-candidate ^
  --result <AUTHORIZED-LANE-RECEIPT-PATH>\MEMABL-314159-obs.json ^
  --output <AUTHORIZED-LANE-RECEIPT-PATH>\MEMABL-314159-verify.json
```

Without the allowlist edit, the runner exits `preregistration fixture contract mismatch`.  
Without hash-agreement repair, L7 self-cert forbids launch.

scientific_retries=0. At most one scientific run.
