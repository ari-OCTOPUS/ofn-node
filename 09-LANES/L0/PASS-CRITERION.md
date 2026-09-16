# L0 PASS CRITERION (written before scanning outputs)
Lane: L0 Contradiction resolution
Written: 2026-09-01T23:36:00+10:00
Read-only: yes (except owned paths)
Forbidden: tests/, src/

A row is complete iff all of:
1. It names one contradicted quantity (not a vibe).
2. It records value_a and value_b without picking a winner.
3. Each value has a source path that exists on this vault, or the token unverified.
4. status is open, or resolved with a runtime source (pytest/git log/execution receipt).
5. No silent resolution. No synthetic numbers.

Exit gate: every contradicted number found in this pass has a complete row in 07-HANDOFF/contradictions.csv.
Baselines to beat or report as not beaten: persistence, prior-only, random.
This file must be hashed before any scan of ledgers or CURRENT-TRUTH.
