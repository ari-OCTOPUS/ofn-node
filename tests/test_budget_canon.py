"""R-2 invariant — BUDGET.json must stay a faithful derived cache of
ofn/config.py (RCA-2: four generations of contradictory caps coexisted
because nothing compared them)."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ofn import config  # noqa: E402
from tools.derive_budget import derive  # noqa: E402


def test_derived_matches_canonical():
    on_disk = json.loads((REPO / "BUDGET.json").read_text(encoding="utf-8"))
    expected = derive(preserve_counters_from=REPO / "BUDGET.json")
    shared = {k: v for k, v in expected.items()
              if k not in ("derived_at_utc",)}
    for k, v in shared.items():
        assert on_disk.get(k) == v, (
            f"BUDGET.json[{k}]={on_disk.get(k)!r} != canonical {v!r} — "
            f"run tools/derive_budget.py; hand edits are forbidden")


def test_no_boost_block_survives():
    on_disk = json.loads((REPO / "BUDGET.json").read_text(encoding="utf-8"))
    assert "day1_boost" not in on_disk, "expired Day-1 boost block still present"
    assert "prior_cache" not in on_disk, "stale prior_cache block still present"


def test_amend1_monthly_cap_present():
    assert config.MONTHLY_BURNABLE_CAPITAL_AUD == 500, (
        "AMEND-1 monthly burnable capital must be the canonical 500 AUD")
