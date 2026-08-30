"""
fleet/hashrate_oracle.py — Live hashrate oracle
================================================
Reads fleet_state.json (written by manager.py every 60s) and updates
the FLEET_HASHRATE_HS constant used by edge_classifier.py.

This bridges real hardware performance into the EdgeClassifier so the
ENERGY edge evaluation uses actual fleet hashrate, not static estimates.

Called:
  - Automatically by coordinator/run.py before each cycle
  - Or standalone: python -m fleet.hashrate_oracle

Output:
  - Updates coordinator/fleet_config.json (runtime override)
  - Logs to stdout
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

ROOT         = Path(__file__).parent.parent
FLEET_STATE  = ROOT / "fleet" / "data" / "fleet_state.json"
FLEET_CFG    = ROOT / "coordinator" / "fleet_config.json"
STALE_SECS   = 300    # 5 min — if fleet_state older than this, use estimates

log = logging.getLogger("fleet.oracle")


def get_live_fleet_hashrate(algo: str = "yespower") -> dict:
    """
    Returns dict with:
      total_hashrate_hs: float  — live measured or estimated
      source: str               — "MEASURED" | "ESTIMATED" | "MISSING"
      alive_workers: int
      mining_workers: int
      last_updated: float
    """
    result = {
        "total_hashrate_hs": 0.0,
        "source": "MISSING",
        "alive_workers": 0,
        "mining_workers": 0,
        "last_updated": 0.0,
    }

    if not FLEET_STATE.exists():
        log.warning("fleet_state.json not found — using model estimate")
        return _estimated(algo, result)

    try:
        state    = json.loads(FLEET_STATE.read_text())
        stats    = state.get("stats", {})
        age      = time.time() - stats.get("timestamp", 0)

        if age > STALE_SECS:
            log.warning("fleet_state stale (%.0fs old) — using model estimate", age)
            return _estimated(algo, result)

        # Use real measured hashrate if workers are actively mining this algo
        current_algo = stats.get("current_algo", "")
        total_hr     = stats.get("total_hashrate_hs", 0.0)
        alive        = stats.get("alive_workers", 0)
        mining       = stats.get("mining_workers", 0)

        if mining > 0 and current_algo.lower() == algo.lower() and total_hr > 0:
            result.update({
                "total_hashrate_hs": total_hr,
                "source": "MEASURED",
                "alive_workers": alive,
                "mining_workers": mining,
                "last_updated": stats.get("timestamp", 0),
            })
            log.info("Live fleet hashrate: %.0f H/s (%s, %d miners)",
                     total_hr, algo, mining)
        else:
            # Workers alive but mining different algo — estimate for requested algo
            result = _estimated(algo, result)
            result["alive_workers"]  = alive
            result["mining_workers"] = 0
            result["source"] = "ESTIMATED_WORKERS_ALIVE"

    except Exception as e:
        log.error("hashrate_oracle read error: %s", e)
        return _estimated(algo, result)

    return result


def _estimated(algo: str, base: dict) -> dict:
    """Fall back to model-based estimate."""
    from fleet.models import fleet_hashrate_for_algo
    est = fleet_hashrate_for_algo(algo)
    base.update({
        "total_hashrate_hs": est,
        "source": "ESTIMATED",
        "last_updated": time.time(),
    })
    log.info("Estimated fleet hashrate: %.0f H/s (%s)", est, algo)
    return base


def update_fleet_config(algo: str = "yespower") -> dict:
    """
    Write coordinator/fleet_config.json with latest hashrate.
    coordinator/confluence_scorer.py reads this to override FLEET_HASHRATE_HS.
    """
    data = get_live_fleet_hashrate(algo)
    FLEET_CFG.write_text(json.dumps(data, indent=2))
    return data


def load_fleet_config() -> Optional[dict]:
    """Load last-written fleet_config.json (used by coordinator)."""
    if FLEET_CFG.exists():
        try:
            return json.loads(FLEET_CFG.read_text())
        except Exception:
            return None
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = update_fleet_config("yespower")
    print(json.dumps(cfg, indent=2))
