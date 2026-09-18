---
type: test-receipt
lane: D-S0-HUNT
measured_at: 2026-09-03T20:29+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: Get-NetIPAddress Wi-Fi this session
scope: this_host_only
claim_type: runtime
owner_decision: "پنج ضربه — فقط پنج test_doctor_lane_*.py"
---

# Doctor lane pytest — five files only

Lane: **D-S0-HUNT**. Laptop `DESKTOP-KA9RFN5` / Wi-Fi `192.168.0.191` (`hostname` + `Get-NetIPAddress` this session). Not board 180.

Owner pick: run **only** the five `test_doctor_lane_*.py` files. Suite not run. `_ops/tests` not collected.

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: runtime
```

## Counts (source = log)

Primary log: `09-LANES/D-S0-HUNT/receipts/pytest-doctor-lane-20260903T1029Z.txt`

| field | value | source |
|---|---|---|
| files on disk | 5 | `Get-ChildItem F:\ofn-node\tests -Filter test_doctor_lane_*.py` this session |
| collected | 41 | log line `collecting ... collected 41 items` |
| passed | 41 | log line `41 passed in 0.92s` |
| failed | 0 | same summary line (no `failed`) |
| skipped | 0 | same summary line (no `skipped`) |
| errors / INTERNALERROR | 0 | no `INTERNALERROR`; `---- exit_code=0 ----` |
| python | `C:\Program Files\Python313\python.exe` 3.13.7 | log header + `platform` line |
| pytest | 9.1.1 | log `pytest-9.1.1` |
| cwd | `F:\ofn-node` | log header |
| runner | `09-LANES/D-S0-HUNT/run_doctor_lane_tests.ps1` | this lane |

Earlier same-five run (wrapper first cut, log has NUL bytes): `receipts/pytest-doctor-lane-20260903T1028Z.txt` — shell also printed `41 passed in 4.22s` / `EXIT=0`. Durations **0.92s** vs **4.22s**, `resolution: null`, `status: open` (two runs, same five paths).

## Grade

**E2** on designed input (tmp_path vaults + bundled contract). **UNDERPOWERED** (n=41 tests / 5 files). Not E3+. Not held-out. Not scaffold-variation.

Prior note `DOCTOR-ARCHITECTURE.md` (20:16+10) said pytest `not_run` / E1. This increment ran. Both dated values kept.

## repair_api

| path | Test-Path this session |
|---|---|
| `F:\ofn-node\tests\test_repair_api.py` | False |
| `F:\ofn-node\ofn\repair_api.py` | False |

Not invented. Not started.

## Not done

No fetch. No flags. No `OFN_KEEP_GATES_OPEN`. No `ofn/config.py` edit. No `ofn.run`. No send/merge. No C/A edits. No commit. No accounting. Tests under `F:\ofn-node\tests` were not edited.
