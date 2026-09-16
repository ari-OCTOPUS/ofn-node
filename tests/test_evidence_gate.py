"""RCA-6 fix tests — the claim gate refuses unevidenced claim-y statuses."""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.evidence_gate import UnevidencedClaim, claim  # noqa: E402


def test_pass_without_evidence_raises():
    with pytest.raises(UnevidencedClaim):
        claim("PASS")


def test_live_with_evidence_ok():
    r = claim("LIVE", "receipt:FIRST-ORDER-RECEIPT.json")
    assert r["status"] == "LIVE"
    assert "receipt:" in r["evidence_ref"]


def test_healthy_without_probe_downgrades():
    r = claim("HEALTHY", "ops-receipts.jsonl", probed_at=None)
    assert r["status"] == "UNPROBED"
    assert r["downgraded_from"] == "HEALTHY"


def test_healthy_with_probe_ok():
    r = claim("HEALTHY", "PROBE1-ziman-store-product-page",
              probed_at="2026-09-16T10:20:00Z")
    assert r["status"] == "HEALTHY"


def test_unprobed_always_printable():
    assert claim("UNPROBED")["status"] == "UNPROBED"


def test_nonclaimy_status_needs_nothing():
    assert claim("BLOCKED", None)["status"] == "BLOCKED"
