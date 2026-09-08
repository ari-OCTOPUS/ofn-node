# LANE-REPORT — QD-LAB-GENERALIZATION-20260908

GOV_VERSION=V8 · LADDER=L2 · owner GO for GEN-v2 explicitly given («گام بعدیو موافقم کامل انجام بده») · no production authority claimed

## What was done

Owner forwarded the delivered OCTOPUS QD Lab package (ZIP, sha256 `6107e313686076f07385d23ef7e2eba82bc976ec981cdd4ba512282fa0e82839`). Per the package's own handoff megaprompt, this lane (1) independently verified the deliverable, (2) executed the preregistered held-out generalization study GEN-v1, then (3) on explicit owner GO executed GEN-v2 (out-of-family transfer + E5 fault battery) and (4) wrote the next-agent megaprompt.

1. **Verification** — all 4 scientific code hashes MATCH; 67/67 tests green; all 9 receipt chains VALID (504 receipts each); 89/89 SHA256SUMS (after restoring one file my validate.py run overwrote from the ZIP); single-elite replay exact. Findings: (a) full-archive bit-exact replay is producer-platform-only — on Win/NumPy2.3.4, 711/3681 elites diverge (only ~4 macroscopically; FP rounding amplified by collision discontinuities; batch==single on my platform, so internal comparisons stay valid); (b) crashed first study launch preserved as `results_gen/receipts_gen.crashed-1.jsonl`, never rewritten.
2. **GEN-v1** (prereg `study_gen.json` sha `05e904c2...`, ledger 94 events VALID):
   - **OQD-H4 SUPPORTED** — 6 unseen same-grammar mazes (seeds 101–106): retention 96.65% (≥75), elite−random +0.4667 (≥+0.15), uniform over 3 archives; mutation robustness 95.2%.
   - **OQD-H5 SUPPORTED** — 0.02 start shifts: 99.1% mean / 98.9% min.
   - cell_transfer_fraction = 0.00 → elites are generic reactive policies, not trajectory memory.
3. **GEN-v2** (owner GO; prereg `results_gen2/study_gen2.json` sha `8d20a89b...`, ledger 76 events VALID; mazes/faults injected by temporary module-constant swaps in the harness only — package files untouched):
   - **OQD-H6 SUPPORTED** — out-of-family mazes (A open-pillar arena / B vertical chambers / C dense forest, seeds 201–202): mean retention 95.69% (range 94.5–97.0), mean advantage +0.4536 (per-family 0.450/0.452/0.458), no `family-bound` labels; mutation archives 94.2%.
   - **OQD-H7 SUPPORTED (marginal)** — E5 fault ladder on source maze: N10 retention 81.5% vs 80% threshold (honest marginal pass); graceful degradation N05 84.0 / N10 81.5 / N20 77.5 / S75 86.7 / S50 85.3; zero collapse conditions; sensor noise is the sensitive axis, actuator weakness is not.
   - Boundary: same arena/start-corner/sensors/metric throughout; noise = additive Gaussian on normalized distance, speed-authority scaling only; no real hardware; production_authorized=false, action=NONE.
4. **Next-agent megaprompt** — `MEGAPROMPT-GEN3-NEXT-AGENT.md`: mission OCTOPUS-QD-LAB-GEN-v3 = the package megaprompt's still-open priority #2 (controlled archive-consumption intervention, proposed 3-arm design T/R/F on a GEN-v2 maze), with all trusted facts, paths, prereg hashes, safety gates and end conditions preserved.

Persian reports: `REPORT-GEN-20260908.md`, `REPORT-GEN2-20260908.md` (includes cumulative hypothesis table H1–H7).

## What remains / offered next

- GEN-v3 archive-consumption intervention (megaprompt delivered, not started — next agent's job).
- Real-mission descriptors, multi-maze evolution, start-corner generalization — listed as future priorities inside the megaprompt, none authorized.

## What failed

- Nothing in GEN-v2. (GEN-v1 had one pre-evaluation crash, preserved and documented above.)

## Evidence paths

- `package/` pristine · `results_gen/` · `results_gen2/` (study, rows, hypothesis records, receipts+integrity, 4 charts) · `gen_study.py`/`analyze_gen.py`/`gen2_study.py`/`analyze_gen2.py` · `verify_chains.py` · `verify_divergence.npz` · two reports · megaprompt.

## Rollback

Delete this lane folder — nothing outside it was modified (the one overwritten package file was restored byte-identical, SHA256SUMS re-verified 89/89). No flags, no organism interaction, no spend, no external effect.
