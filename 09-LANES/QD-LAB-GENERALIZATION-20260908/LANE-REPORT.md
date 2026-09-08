# LANE-REPORT — QD-LAB-GENERALIZATION-20260908

GOV_VERSION=V8 · LADDER=L2 · no owner vote consumed · no production authority claimed

## What was done

Owner forwarded the delivered OCTOPUS QD Lab package (ZIP, sha256 `6107e313686076f07385d23ef7e2eba82bc976ec981cdd4ba512282fa0e82839`). Per the package's own handoff megaprompt (priority test #1: held-out generalization), this lane (1) independently verified the deliverable at runtime-evidence level, then (2) preregistered and executed the held-out generalization study.

1. **Verification** — all 4 scientific code hashes MATCH `study.json`; 67/67 tests green; all 9 receipt chains VALID (504 receipts each); all 89 files match shipped `SHA256SUMS.txt`; single-elite replay exact; report numbers match run summaries. Findings: (a) full-archive batch replay on this platform (Win/Py3.13.7/NumPy2.3.4) is bit-exact for 2,970/3,681 elites only — 4 elites exceed 0.01 fitness error (max 0.049), 3 exceed 0.05 BD error (max 0.687); cause = cross-platform FP rounding amplified by collision discontinuities; batch vs single evaluation identical here, so all study comparisons are internally consistent. The shipped zero-error claim is true on the producer's platform. (b) During verification `validate.py` overwrote `results/full_archive_replay.json`; original restored from ZIP, package re-verified pristine.
2. **Generalization study GEN-v1** — preregistered (`results_gen/study_gen.json`, sha256 `05e904c2...d06fe`, hashed into ledger event 0 BEFORE any held-out evaluation): 6 unseen mazes (seeds 101–106, same grammar, deterministic validity rules, all accepted first attempt), start-shift conditions, fresh-random baseline n=256/maze, all 6 primary+mutation archives, 93 condition rows, receipts via the package's own SHA-256 chain (94 events, verify VALID).
   - **OQD-H4 SUPPORTED_IN_THIS_LAB**: unseen-maze mean retention 96.65% (range 94.5–98.9; threshold 75%), elite−random advantage +0.4667 (range +0.425..+0.505; threshold +0.15); kill condition (memorization) not triggered. Mutation archives robustness mean 95.2%.
   - **OQD-H5 SUPPORTED_IN_THIS_LAB**: 0.02 start shifts retention mean 99.14%, min 98.89%.
   - Interpretive finding: cell_transfer_fraction = 0.00 — endpoints do NOT transfer, quality DOES: elites are generic reactive control policies, not trajectory memory.
   - Boundary: within-grammar transfer only (same maze family, same start corner); E5 (sensor noise, actuator faults) NOT done; no Core/organism/hardware/money involvement; package remains production_authorized=false, action=NONE.

Full Persian report: `REPORT-GEN-20260908.md`.

## What remains / offered next

- Out-of-family maze generalization (separate the "generic skill" claim from within-family interpolation).
- E5 fault-injection battery (sensor noise, motor degradation) on the same elites.
- Controlled archive-consumption intervention and real-mission descriptors — per package megaprompt, untouched.

## What failed

- First study launch crashed on a `random_base` KeyError before any held-out evaluation; partial ledger preserved as `results_gen/receipts_gen.crashed-1.jsonl` (never rewritten); bug fixed, rerun clean.

## Evidence paths

- `package/` — pristine delivered ZIP contents
- `results_gen/study_gen.json`, `rows_gen.json`, `hypothesis_records_gen.json`, `descriptive_combined.json`, `receipts_gen.jsonl`, `integrity_gen.json`, `gen1_h4_transfer.png`, `gen2_h5_and_combined.png`
- `verify_chains.py`, `verify_divergence.npz`, `REPORT-GEN-20260908.md`

## Rollback

Delete this lane folder — nothing outside it was modified (the one overwritten package file was restored byte-identical and SHA256SUMS re-verified 89/89). No flags, no organism restart, no spend, no external effect.
