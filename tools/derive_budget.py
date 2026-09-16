#!/usr/bin/env python3
"""R-2 — derive BUDGET.json from ofn/config.py (canonical) + receipt.

Kills the four-generations contradiction (RCA-2): BUDGET.json becomes a
read-only derived cache. Running this script rewrites BUDGET.json ONLY from
config.py constants + preserves live counters (messages_sent_today,
spend_today_aud) if present. The Day-1 boost block is dropped — its
expires_local_date (2026-09-05) passed and it had zero code consumers.
"""
import hashlib
import json
import time
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ofn import config  # noqa: E402  (canonical constants)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def derive(preserve_counters_from: Path | None = None) -> dict:
    counters = {}
    if preserve_counters_from and preserve_counters_from.is_file():
        try:
            old = json.loads(preserve_counters_from.read_text(encoding="utf-8"))
            counters = {k: old[k] for k in
                        ("messages_sent_today", "spend_today_aud") if k in old}
        except (ValueError, OSError):
            counters = {}
    return {
        "schema": "budget.derived/1",
        "canonical_source": "ofn/config.py",
        "derived_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "daily_message_cap": config.D27_DAILY_SEND_CAP,
        "daily_spend_cap_aud": config.D27_DAILY_SPEND_CAP_AUD,
        "monthly_burnable_capital_aud": config.MONTHLY_BURNABLE_CAPITAL_AUD,
        "per_board_budget_default_aud": config.D27_PER_BOARD_BUDGET_DEFAULT,
        "paid_ads_cap_usd": 0,
        "paid_ads_policy": "OWNER-FORBID-until-explicit GO",
        "on_cap_reached": "halt",
        "kill_switch": config.D27_KILL_SWITCH,
        "rollback_window_hours": config.D27_ROLLBACK_WINDOW_HOURS,
        "runway_formula": "floor(remaining_monthly_cents / "
                          "max(real_spend_last_7d_daily_cents, floor_cents)) — "
                          "conservative until monthly_survival_cost_aud is set "
                          "(AMEND-1); auto-freeze at runway_days < 14, no vote",
        **counters,
    }


def main() -> int:
    bpath = REPO / "BUDGET.json"
    before = json.loads(bpath.read_text(encoding="utf-8")) if bpath.is_file() else {}
    before_sha = sha(bpath) if bpath.is_file() else None
    derived = derive(preserve_counters_from=bpath if bpath.is_file() else None)
    cpath = REPO / "ofn" / "config.py"
    receipt = {
        "schema": "budget-canon-receipt/1",
        "id": "BUDGET-CANON-1",
        "at_utc": derived["derived_at_utc"],
        "order": "MP-ROOTFIX R-2 + AMEND-1 (monthly 500 AUD)",
        "before": {k: before.get(k) for k in
                   ("daily_message_cap", "daily_spend_cap_aud",
                    "burnable_capital_aud", "date", "gov_version")},
        "before_note": "stale Day-1 boost 250/500 dated 2026-09-05, never "
                       "reverted (expires had 0 code consumers); prior_cache "
                       "held V7 20/$5",
        "after": {k: derived[k] for k in
                  ("daily_message_cap", "daily_spend_cap_aud",
                   "monthly_burnable_capital_aud")},
        "config_py_sha256": sha(cpath),
        "budget_json_sha256_before": before_sha,
        "invariant_test": "tests/test_budget_canon.py::test_derived_matches_canonical",
    }
    bpath.write_text(json.dumps(derived, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    receipt["budget_json_sha256_after"] = sha(bpath)
    out = REPO / "rca" / "BUDGET-CANON-1.json"
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"derived": receipt["after"],
                      "budget_sha_after": receipt["budget_json_sha256_after"][:16],
                      "receipt": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
