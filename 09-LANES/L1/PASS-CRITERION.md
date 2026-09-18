# L1 PASS CRITERION (written before mining logs)
Lane: L1 Log mining (zero-cost discovery)
Depends on: L0 first-pass csv exists (07-HANDOFF/contradictions.csv). Whole-vault L0 completeness remains unverified; this lane does not reopen L0.
Owned: 09-LANES/L1/   Forbidden: src/, tests/   Read-only: yes
Written: 2026-09-01T23:47:00+10:00

A finding counts iff:
1. It is a behaviour observed in a log or runtime file (repeat, stall, silent success, queue growth, start-limit, etc.).
2. It is not already stated in 07-HANDOFF/contradictions.csv, AGENTS.md, L0 report, or the governance pack README.
3. It has a source path + a concrete observation (count or pattern), or the token unverified.

Exit gate: three such findings, or an explicit written zero after named log files were actually opened.
Baselines: persistence / prior-only / random must be beaten or reported not beaten.
Hash this file before opening logs.
