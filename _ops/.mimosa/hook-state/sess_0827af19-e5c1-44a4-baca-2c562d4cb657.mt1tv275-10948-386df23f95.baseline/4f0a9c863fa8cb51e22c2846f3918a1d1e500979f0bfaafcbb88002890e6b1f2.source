"""now_moves — additive, flag-OFF audit-fix modules (M1..M7).

Each module here is ISOLATED and DEFAULT-OFF: without its feature-flag the system
behaves exactly as before (zero behavior change). Rollback for any module = delete
its file (and remove its single flag-gated call-line at the documented call-site).
No module here rewrites, deletes, or mutates any existing file or any
ledger/genome/state without an explicit human-set flag.

Registry:
  M1  ledger_integrity_probe   flag OCTOPUS_WIRE_LEDGER_PROBE     fixes FM-3, FM-4
  (M2..M7 land as separate files under the same discipline)
"""
