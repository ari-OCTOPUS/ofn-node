# L7 PASS CRITERION (written before scanning outputs)
Lane: L7 Contract and snapshot tests
Written: 2026-09-01T23:50:00+10:00
Read-only: no (owned: tests/contract/, tests/snapshot/, 09-LANES/L7/)
Forbidden: src/ (do not import src; do not edit src/)
Depends on: L0 (contradictions.csv present)

This lane PASSES iff all of:
1. PASS-CRITERION.md exists and is hashed before any assertion of contract JSON contents.
2. Either (a) existing JSON contract files under F:\backup\contracts (or other pre-existing vault JSON named as contracts, not invented) are snapshotted/asserted for required keys, OR (b) the report states BLOCKED because src is forbidden and F:\backup\contracts is absent.
3. "Context bundle contract asserted" means: named keys from an EXISTING file are listed with source path; no synthetic keys, no invented metrics.
4. "Routing boundary snapshotted" means: a routing-related boundary is copied from an EXISTING vault artifact (JSON/md/ledger), or BLOCKED is recorded with the missing path.
5. Optional pytest, if written, only reads JSON under contracts/ or 09-LANES and asserts keys exist. It must not import src.
6. No flags enabled. No network. No rm. No git push. No Telegram.

Baselines: persistence (reuse L0/L1 hashes if still on disk), prior-only (do not treat prior reports as new contracts), random (not used).
Every number needs a source path or the token unverified.
