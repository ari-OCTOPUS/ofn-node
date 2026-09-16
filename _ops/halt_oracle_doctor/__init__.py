"""halt_oracle_doctor — read-only, offline coverage doctor for the canonical halt oracle.

Built under OD-1 clause 3 / OD-4 owner card (2026-09-17). Answers one question per
approved consumer: does the canonical halt oracle actually stop this effect?

Boundaries, enforced rather than asserted:
  * `safety_check.certify()` runs first and raises FailClosedError on any violation.
  * No transport import, no subprocess, no dynamic execution, no env read.
  * The ONE allowlisted `ofn` import is `ofn.kernel.halt` (pure predicate), verified
    mechanically at runtime instead of trusted.
  * Writes go only into `receipts/`; `_guard_write()` refuses anything else.
  * No HALT file is created, deleted, or armed. `mutations_performed` is always 0.
  * No live-node access. Node-observed state is accepted as an input (Half B) and
    otherwise recorded as NOT_PERFORMED.

Entry point:
    python -m _ops.halt_oracle_doctor.doctor --repo F:/ofn-node --phase PRE
"""

__all__ = ["canon", "safety_check", "resolver", "coverage"]
