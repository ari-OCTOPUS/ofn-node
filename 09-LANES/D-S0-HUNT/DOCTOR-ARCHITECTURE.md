---
type: architecture-note
lane: D-S0-HUNT
measured_at: 2026-09-03T20:16+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: prior D Get-NetIPAddress Wi-Fi (OFN-LOCAL-ARCHITECTURE.md)
scope: this_host_only
claim_type: observation
owner_decision: "دک) فقط معماری doctor (CLI/round/backlog) — نه repair_api و نه روشن کردن فلگ"
pytest: see DOCTOR-LANE-TEST-RECEIPT.md (41 passed / 0 failed / 0 skipped; source receipts/pytest-doctor-lane-20260903T1029Z.txt). This frontmatter was not_run at 20:16+10.
---

# Doctor architecture — `ofn.doctor` (this host only)

Lane: **D-S0-HUNT**. Read of code + existing files. No fetch, no flag, no doctor round on the vault, no `repair_api`.

This laptop is `DESKTOP-KA9RFN5` / `.191`. Not board 180. Disk absence here = `body_not_on_this_host`.

Live inventory (present/absent/schema): run `09-LANES/D-S0-HUNT/doctor_schema_probe.py`. This note maps **code**. Do not collapse the probe table into this file.

Package context: `09-LANES/D-S0-HUNT/OFN-LOCAL-ARCHITECTURE.md` §4. `ofn.run` does not import `ofn.doctor` (`Select-String` on `F:\ofn-node\ofn\run.py` this hunt: zero matches).

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: observation
```

## 1. What it is / is not

**Is:** Lane-LB CLI diagnosis. Organs diagnose and propose; they do not patch themselves (`F:\ofn-node\ofn\doctor\__init__.py`). Four subcommands: `contract-map`, `round`, `backlog`, `destiny` (`cli.py` docstring).

**Is not:** an HTTP repair surface, a flag switch, a merge engine, or the vault’s `state/doctor/report.json` producer. `repair_api` / `tests/test_repair_api.py`: zero paths under `F:\ofn-node` (`Select-String` this hunt).

## 2. Modules (this checkout)

`Get-ChildItem F:\ofn-node\ofn\doctor -File` this session:

| file | bytes | role |
|---|---|---|
| `__init__.py` | 872 | Package charter; re-exports |
| `cli.py` | 5238 | `python -m ofn.doctor.cli` |
| `round.py` | 15285 | Read-only vault walk |
| `backlog.py` | 4787 | Self-backlog upsert |
| `destiny.py` | 9264 | Proposal → one of four outcomes |
| `contract_map.py` | 15470 | `LAB-DOCTOR-CONTRACT.yaml` → 16 requirements (R-01..R-16) |
| `prescription.py` | 2771 | Validate prescription shape; never apply |
| `receipts.py` | 3907 | Append-only jsonl + per-line sha256 |
| `miniyaml.py` | 6739 | YAML subset loader |

Also: `ofn/doctor/contract/LAB-DOCTOR-CONTRACT.yaml` + sibling `.gitattributes` (`eol=lf`). `__version__` in `__init__.py` = `0.1.0`.

## 3. CLI vs round vs backlog vs destiny

| surface | entry | reads | writes | refuses |
|---|---|---|---|---|
| **CLI** | `python -m ofn.doctor.cli <cmd>` | argv | only what the subcommand owns | no HTTP, no vault mutate from `round` |
| **contract-map** | `cmd_contract_map` | bundled contract | stdout only | — |
| **round** | `DoctorRound.run(vault)` | vault files (read_bytes) | `--out/findings.json` + `--out/receipt.jsonl` only | “no write mode and no flag that enables one” (`round.py` lines 5–8) |
| **backlog** | `SelfBacklog(--state)` | contract gaps | `--state` JSON (upsert) | scheduling / gate-open = owner (`upsert_from_gaps` proposed_action) |
| **destiny** | `DestinyEngine.assign` | proposals JSON + journal | journal.jsonl + `--out` outcomes | merge never an outcome; forbidden targets escalate; no PR URL → refuse `PR_CREATED` claim (`cli.py` lines 83–86) |

Four default round checks (`round.py` `DoctorRound.__init__`): `mirror_check`, `dead_ref_check`, `root_junk_check`, `contract_gap_check`. Missing vault → `SourceNotFoundError` (fail closed).

Destiny outcomes (`destiny.py` `OUTCOMES`): `PR_CREATED` | `QUEUED_WITH_REASON` | `REJECTED_WITH_REASON` | `ESCALATED_TO_OWNER`. No `PENDING`. Crash mid-flight → recover as `ESCALATED_TO_OWNER`.

Backlog fields (`BACKLOG_FIELDS`, exactly nine): id, missing_capability, evidence, severity, proposed_action, test_required, owner_ruling_required, status, created_at.

`execute_mutation` always raises `SandboxNotVerifiedError` (`contract_map.py` lines 253–258). Validation of prescriptions/experiments is shape-check only.

## 4. Outputs — not `report.json`

`DoctorRound.to_machine_json` (`round.py` 76–84) writes **`findings.json`**:

```
vault_root, findings[], stats, changed_sources, read_only_proven, files_opened
```

Finding fields: id, category, severity (LOW|MEDIUM|HIGH|CRITICAL), title, evidence_path, evidence_sha256, detail, proposed_action.

CLI `round` also writes `receipt.jsonl` kinds: `round_start`, `integrity_before`, `finding`, `integrity_after`, `round_end`.

**No module in `ofn/doctor` writes `state/doctor/report.json`.** That name belongs to a different body (`octopus.doctor-report.v1` / board recipes). Do not treat the two as one doctor.

## 5. Three report stories — do not collapse hosts

| body | path on this laptop | this session | schema |
|---|---|---|---|
| Canonical S0 report | `F:\backup\state\doctor\report.json` | **ABSENT** (`Test-Path`); parent dir `state/doctor` also absent | — → status **UNKNOWN** for this host |
| ofn-node data | `F:\ofn-node\data\state\doctor\report.json` | **ABSENT**; `F:\ofn-node\data` exists but has no `state\` | — |
| Vault organism cache | `F:\backup\_ops\state\doctor\*` | **14 files** (`Get-ChildItem` this session) | not `octopus.doctor-report.v1` (probe classifies) |
| Stale evidence | `F:\backup\06-EVIDENCE\OCTOPUS-DOCTOR-REFRESH-2026-08-23\doctor-report.json` | present | `octopus.doctor-report.v1`, `status: FAIL`, `repairs_attempted: 0`; check evidence_path uses `/var/lib/octopus` → **other host** |
| 138 file claim | `~/ofn/data/state/doctor/report.json` | not on this disk | cited in `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/DEEP-REALITY-SCAN-2026-09-03/NEXT-SCAN-RESULTS-2026-09-03.md` — **not re-probed**; `body_not_on_this_host` |

`OCTOPUS-DOCTOR/90-_meta/state/doctor-vitals.json` exists; schema `doctor-vitals.v1` (not doctor-report).

## 6. Tests — names, not a run

Five files (`Get-ChildItem F:\ofn-node\tests -Filter test_doctor_lane_*.py`):

| file | bytes | covers (from `def test_` names) | grade |
|---|---|---|---|
| `test_doctor_lane_cli.py` | 3327 | `test_cli_round_backlog_destiny_end_to_end` on synthetic vault | E1 |
| `test_doctor_lane_round.py` | 6456 | healthy/missing/malformed/unreadable/stable ids/immutability/mirrors | E1 |
| `test_doctor_lane_backlog.py` | 2472 | upsert no-dup, nine fields, owner flag, round-trip, bad severity | E1 |
| `test_doctor_lane_destiny.py` | 4581 | outcomes, reject, escalate, no merge, executor fail, crash recover | E1 |
| `test_doctor_lane_contract_map.py` | 9461 | miniyaml, contract pin, R-map, refuse `execute_mutation`, prescription/experiment, receipt tamper | E1 |

**pytest later same day:** five files only. **41 passed / 0 failed / 0 skipped**, source `09-LANES/D-S0-HUNT/receipts/pytest-doctor-lane-20260903T1029Z.txt`. Grade **E2** designed input, **UNDERPOWERED**. Not E3+. This section at 20:16 said not run / E1 — both dated values kept.

`tests/test_*.py` count **155** vs README “۱۷ فایل”: both kept, `resolution: null`, `status: open` (same as OFN-LOCAL-ARCHITECTURE §1.2).

## 7. Gates — names only, not opened

From `LAB-DOCTOR-CONTRACT.yaml` `gates:`: `gate_0` `reality_and_zone_classification`, `gate_1` `novelty_archive_measurement`, `gate_2` `life_currency_economy`, `gate_3` `hard_lab_sandbox`, `gate_4` `doctor_prescriptions`, `gate_5` `governed_laws_drive_and_black_boxes`, `gate_6` `organogenesis`, `gate_7` `fair_retirement`.

Destiny `FORBIDDEN_TARGETS` includes the **string** `secret_rotation` (plus `.env`, `_ops/state/`, `flags.cmd`, `owner-key`, …). A proposal whose path contains that name escalates; this lane does not enable the gate.

AGENTS.md blocked names remain closed: `secret_rotation`, `partner_precondition`, `miner_isolation`, `D1`, `D7`, `OWNER_KEY`, `auto_email`. No `OCTOPUS_WIRE_*` / `OFN_WIRE_*` / `OBSERVATORY` / `CORTEX_HYPOTHESIS` / `OFN_KEEP_GATES_OPEN`.

## 8. Open contradictions

1. README “۱۷ فایل تست” vs 155 `test_*.py` — `resolution: null`.
2. `ofn.doctor` findings.json vs vault `state/doctor/report.json` vs `_ops/state/doctor` vs stale `octopus.doctor-report.v1` — four bodies, one word “doctor”.
3. `09-LANES/LANE-MATRIX.csv` still L0–L9 only; this folder exists (`SCOPE.md`).
4. behind-2 on `F:\ofn-node` remains `local_behind_remote_unverified` (no fetch).

## 9. Not done

Pytest of the five `test_doctor_lane_*.py` files: later increment — `DOCTOR-LANE-TEST-RECEIPT.md`. No `python -m ofn.doctor.cli round` against `F:\backup`. No fetch. No `repair_api`. No flag. No ofn-node edit.
