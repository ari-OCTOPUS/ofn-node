# LANE-REPORT — L7 VBAA RED (distinct from LANE-REPORT.md)

GOV_VERSION=V8 · LADDER=L2 (OWNER-CANCEL cash-gate 2026-09-05) · VERIFIED_CASH=0
LANE_ID=L7 · MODE=PROPOSE_ONLY · board=180 · may_authorize=false · external_api=DISABLED

Prompt 1 only: three RED pytest files. No production classes. No PR. No commit.

## What was done

Declared lane **L7** (`09-LANES/LANE-MATRIX.csv`: owns `tests/contract/`, `tests/snapshot/`, `09-LANES/L7/`; forbidden `src/`).

Confirmed in-repo:

- VBAA has 15 components: `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv` V-01 and `07-HANDOFF/wave1-pack/BUILD-WAVES.md` (both say 15 / پانزده جزء).
- Registry does **not** name a lowest-risk trio. Named in registry: ArgumentProvenanceGuard and Merkle receipts. User-named start trio recorded alongside; `status: open`.
- No `_ops/vbaa/` on disk. `gap_scan.py` probes `_ops/vbaa/` and `tests/vbaa/`.
- Vault-root `tests/` follows pytest `test_*.py` (L7 sample: `tests/contract/test_l7_json_fields.py` in git; style copied). Fixtures live under `tests/contract/vbaa/fixtures/` so L7 owns them.

Wrote three RED tests + fixture corpus. Implementations are imported from `_ops/vbaa/` (not `src/`).

## What remains

- PROMPT 2: implement the three units until these tests go green; one PR per component later.
- Owner decisions in `07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md` (C1, C2, INV-*).
- Original L7 pass criterion (`09-LANES/L7/PASS-CRITERION.md`) was not rewritten.

## What failed

- Intended RED: `vbaa.*` modules are absent (E0). pytest collection/import must fail until PROMPT 2.
- Full 15-name list: not found in vault (`unverified` identities).
- Lowest-risk ranking: not in registry.

## Evidence paths

| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| component count | 15 | `07-HANDOFF/wave1-pack/CONCEPT-CODE-GAP.csv` V-01 | E0 (concept-only) | verified as document claim |
| same count | 15 / پانزده جزء | `07-HANDOFF/wave1-pack/BUILD-WAVES.md` | E0 | verified as document claim |
| registry named set | ArgumentProvenanceGuard, Merkle receipts | CONCEPT-CODE-GAP.csv V-01 | E0 | verified as document claim |
| user start trio | ArtifactAdmission, ArgumentProvenanceGuard, ExecutorHandleFirewall | user prompt 2026-09-08 | E0 | recorded; not in registry as lowest-risk |
| `_ops/vbaa/` | absent | Test-Path this session | E0 | verified |
| pytest RED | 3 collection ERRORS, 0 passed, `ModuleNotFoundError: No module named 'vbaa'`, 1.59s | this-session `python -m pytest tests/contract/vbaa/test_artifact_admission.py tests/contract/vbaa/test_argument_provenance_guard.py tests/contract/vbaa/test_executor_handle_firewall.py -q --noconftest --tb=line` (exit 2) | E0 | verified RED |

## Public API PROMPT 2 must satisfy

Package on `sys.path` including `_ops`: **`vbaa`** → `_ops/vbaa/`.

1. `vbaa.artifact_admission.ArtifactAdmission(allowed_types, path_root)`
   - `admit(artifact: Mapping) ->` object with `.admitted: bool` and `.reason_code: str`
   - codes: `EMPTY`, `UNSIGNED`, `WRONG_TYPE`, `PATH_ESCAPE`, `OK`
2. `vbaa.argument_provenance_guard.ArgumentProvenanceGuard()`
   - `check(arguments, provenance) ->` object with `.allowed: bool` and `.reason_code: str`
   - codes: `UNPROVENANCED`, `UNTRUSTED`, `OK`
3. `vbaa.executor_handle_firewall.ExecutorHandleFirewall`
   - `TARGET_HOST_ID == "180"`
   - `scan_python_tree(root, host_id="180") ->` report with `.clean`, `.violations`, `.scanned_files`, `.host_id`
   - violation objects: `.path`, `.module`, `.statement` in `{"import", "from"}`
   - AST only; no runtime import of executor; fixture tree must not be mutated

## Test and fixture paths

- `tests/contract/vbaa/test_artifact_admission.py`
- `tests/contract/vbaa/test_argument_provenance_guard.py`
- `tests/contract/vbaa/test_executor_handle_firewall.py`
- `tests/contract/vbaa/fixtures/artifact_admission/`
- `tests/contract/vbaa/fixtures/argument_provenance/`
- `tests/contract/vbaa/fixtures/executor_firewall/{dirty_tree,clean_tree,substring_tree}/`

## Rollback steps

Move `tests/contract/vbaa/` and `09-LANES/L7/LANE-REPORT-VBAA-RED-2026-09-08.md` and `07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md` to `99-ARCHIVE/` with `archive_` prefix. Do not rm -rf. Do not touch `src/` or live `_ops` services. Revert the wikilink line in `01 - Dashboard/HANDOFF.md`.
