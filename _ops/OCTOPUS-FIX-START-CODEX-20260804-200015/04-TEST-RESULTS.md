# 04 — Test results

All 6 tests run directly (not trusted from the commit message). First run without forcing
UTF-8 output: 5 of 6 crashed with `UnicodeEncodeError` on Windows' default cp1252 console
while trying to *print* a ✅ character — after the actual check logic had already completed.
That is a false red, not a real failure: see `23-MINIMAL-EVAL-HARNESS.md` for the fix. All
results below are from the corrected run (`PYTHONIOENCODING=utf-8 PYTHONUTF8=1`, same
env-fix `RUN-ORGANISM.bat` already applies for the same reason).

| Test file | Framework | Result | Detail |
|---|---|---|---|
| `test_arm_gate.py` | unittest | **16/16 pass** | baseline arm-token gate: TTL, HMAC, two-key, unknown-cap, pass-through |
| `test_arm_gate_p0.py` | custom | **12/12 pass** | blindspot #30: sensitive-default deny/allow, stale-token deny, no-network |
| `test_latent_space.py` | custom | **14/14 pass** | baseline embed/retrieve/persist/similarity |
| `test_latent_space_fail_closed.py` | custom | **6/6 pass** | blindspot #53: corrupt file does not wipe, quarantines, records error |
| `test_intel_spine.py` | custom | **16/16 pass** | event schema, hash-redaction, no-network |
| `test_adapters_obsidian.py` | custom | **15/15 pass** | telegram/webapp logging, obsidian marker-based update, no chat_id leak |

**Total: 79/79 checks pass, 0 fail.** (The commit message claimed "49 tests" — that number
undercounts by excluding the two pre-existing baseline files `test_arm_gate.py` (16) and
`test_latent_space.py` (14); the new-P0-specific subset is 12+6+16+15 = 49, which matches.
Both numbers are consistent once you know which subset each refers to.)

Raw captured output: `test_outputs/*.txt`.
