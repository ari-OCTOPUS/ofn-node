#!/usr/bin/env python3
"""RCA-6 fix — the claim gate: no PASS/HEALTHY/LIVE/DEPLOYED without evidence.

Every report generator must route status claims through claim(); printing a
claim-y status with empty/falsy evidence raises. This makes 'optimistic
report without receipt' a code-level impossibility instead of a prose rule.
"""
from __future__ import annotations

CLAIMY = {"PASS", "HEALTHY", "LIVE", "DEPLOYED", "VERIFIED", "GREEN"}
DOWNGRADE = "UNPROBED"


class UnevidencedClaim(RuntimeError):
    """A claim-y status was printed without a machine-checkable reference."""


def claim(status: str, evidence_ref=None, *, probed_at=None) -> dict:
    """Return a claim record, or raise. UNPROBED is always printable."""
    s = str(status).upper()
    if s == DOWNGRADE:
        return {"status": DOWNGRADE, "note": "explicitly not claimed"}
    if s in CLAIMY:
        if not evidence_ref:
            raise UnevidencedClaim(
                f"status {s} requires a non-empty evidence_ref (receipt id, "
                f"probe_id, url, or file path) — refusal is the RCA-6 fix")
        if s in ("HEALTHY",) and not probed_at:
            # R-4 rule: HEALTHY specifically requires a fresh probe stamp
            return {"status": DOWNGRADE,
                    "downgraded_from": s,
                    "reason": "HEALTHY without probed_at auto-downgrades",
                    "evidence_ref": evidence_ref}
        return {"status": s, "evidence_ref": str(evidence_ref),
                **({"probed_at": probed_at} if probed_at else {})}
    return {"status": s, **({"evidence_ref": str(evidence_ref)}
                            if evidence_ref else {})}
