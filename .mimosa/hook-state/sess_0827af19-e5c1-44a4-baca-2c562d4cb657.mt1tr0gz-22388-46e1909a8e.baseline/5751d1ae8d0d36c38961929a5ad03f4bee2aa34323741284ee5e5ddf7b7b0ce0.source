"""
edge_classifier.py — Per-coin edge evaluation (Phase B)
=========================================================
Replaces asset_type-based routing (prior Phase 4.1) with a principled
edge-evaluation framework.

Governing principles:
  E-0: NO_EDGE is default. edge_present proven from MEASURED inputs only.
  E-1: Each edge has computable signature AND kill condition.
  E-2: PATIENCE is enabler only — never produces edge_present alone.
  E-3: {latency_hft, generic_research, narrative_timing} cannot be assigned.

For each coin, classify() produces:
  edge_result: dict with per-edge evaluation
  edge_present: list of edges where edge_present=True
  decision: str — "NO_EDGE" or the routing edge name
  reject_reason: str — why rejected (for NO_EDGE coins)
  routed_module: str — which strategy module handles this coin
"""
import math
import yaml
from pathlib import Path
from modules.field_value import FieldValue, MEASURED, MISSING

_EDGES_CONFIG = Path("edges.yaml")
_NON_ADMISSIBLE = {"latency_hft", "generic_research", "narrative_timing"}

# ── Load edges config ─────────────────────────────────────────────────────────
def _load_config() -> dict:
    with open(_EDGES_CONFIG) as f:
        data = yaml.safe_load(f)
    return data.get("config_constants", {})

_CFG = _load_config()

RUNNABLE_ALGOS  = {a.lower() for a in _CFG.get("RUNNABLE_ALGOS", [])}
ASIC_ALGOS      = {a.lower() for a in _CFG.get("ASIC_ALGOS", [])}
FLEET_HASHRATE  = float(_CFG.get("FLEET_HASHRATE_HS", 50000))
FLEET_RAM_GB    = float(_CFG.get("FLEET_RAM_GB", 32))
FLEET_DISK_GB   = float(_CFG.get("FLEET_DISK_GB", 2000))
NODE_POWER_W    = float(_CFG.get("NODE_POWER_DRAW_W", 150))
POWER_COST      = float(_CFG.get("POWER_COST_KWH", 0.05))
ENERGY_MARGIN   = float(_CFG.get("ENERGY_MARGIN", 0.20))
MIN_FLEET_SHARE = float(_CFG.get("MIN_FLEET_SHARE", 0.0001))
MAX_GPU_DOM     = float(_CFG.get("MAX_GPU_DOMINANCE", 0.85))
DD_FLOOR        = float(_CFG.get("DD_FLOOR", 35.0))
RECOVERY_SIG    = float(_CFG.get("RECOVERY_SIGNAL", -5.0))
MAX_STAKE_CAP   = float(_CFG.get("MAX_STAKE_CAPITAL", 10000))
PATIENCE_MAX    = float(_CFG.get("PATIENCE_MAX_POSITION_USD", 500))


class EdgeClassifier:
    """
    Evaluate each coin against admissible edges.

    Usage:
        ec = EdgeClassifier()
        results = ec.classify_all(coins)  # in-place annotation
    """

    def classify_all(self, coins: list) -> list:
        for c in coins:
            result = self.classify(c)
            c["edge_result"]    = result
            c["edge_present"]   = result["edge_present"]
            c["edge_decision"]  = result["decision"]
            c["edge_module"]    = result["routed_module"]
            c["edge_reject_reason"] = result.get("reject_reason", "")
        return coins

    def classify(self, c: dict) -> dict:
        """
        Returns edge evaluation dict for one coin.
        E-0: NO_EDGE unless proven otherwise from MEASURED inputs.
        """
        sym = c.get("symbol", "?")
        per_edge = {}

        # Evaluate each edge
        per_edge["ENERGY"]      = self._eval_energy(c)
        per_edge["DISLOCATION"] = self._eval_dislocation(c)
        per_edge["YIELD"]       = self._eval_yield(c)
        per_edge["PATIENCE"]    = {
            "edge_present": False,  # E-2: always False
            "note": "Enabler only — never produces edge_present alone"
        }

        active = [name for name, ev in per_edge.items()
                  if ev.get("edge_present") is True and name != "PATIENCE"]

        if not active:
            # Build informative reject reason
            reasons = []
            for name, ev in per_edge.items():
                if name == "PATIENCE": continue
                missing = ev.get("inputs_missing", [])
                failed  = ev.get("sig_failed", [])
                killed  = ev.get("kill_triggered", [])
                if missing:
                    reasons.append(f"{name}:inputs_missing={missing}")
                if failed:
                    reasons.append(f"{name}:sig_failed={failed}")
                if killed:
                    reasons.append(f"{name}:killed={killed}")
            return {
                "decision":      "NO_EDGE",
                "edge_present":  [],
                "per_edge":      per_edge,
                "routed_module": None,
                "reject_reason": "; ".join(reasons) if reasons else "no edge conditions met",
            }

        # Route to highest-conviction edge (CORE edges preferred; else first active)
        core_edges = [e for e in active
                      if per_edge[e].get("sizing") == "CORE"]
        primary = core_edges[0] if core_edges else active[0]

        return {
            "decision":      primary,
            "edge_present":  active,
            "per_edge":      per_edge,
            "routed_module": f"{primary.lower()}_strategy",
            "reject_reason": "",
        }

    # ── ENERGY edge ───────────────────────────────────────────────────────────

    def _eval_energy(self, c: dict) -> dict:
        ev = {"sizing": "CORE", "sig_satisfied": False, "kill_triggered": [],
              "inputs_missing": [], "sig_failed": [], "edge_present": False}

        # Collect required inputs
        algo_fv       = self._get_fv(c, "mining_algo")
        price_fv      = self._get_fv(c, "coin_price")
        nethash_fv    = self._get_fv(c, "network_hashrate")

        # Config inputs always MEASURED
        fleet_hs  = FieldValue.measured(FLEET_HASHRATE, "config")
        power_kw  = FieldValue.measured(POWER_COST, "config")

        # Check input completeness (E-0)
        for name, fv in [("algo", algo_fv), ("coin_price", price_fv),
                         ("network_hashrate", nethash_fv)]:
            if fv.status != MEASURED:
                ev["inputs_missing"].append(name)

        if ev["inputs_missing"]:
            ev["edge_present"] = False
            return ev

        algo  = str(algo_fv.value).lower()
        price = float(price_fv.value)
        nh    = float(nethash_fv.value)

        # Kill conditions — check first
        if algo in ASIC_ALGOS:
            ev["kill_triggered"].append(f"asic_dominated: algo={algo} is ASIC-class")
        gpu_share = c.get("gpu_share_estimated", 0.0)  # populated by energy_funnel
        if gpu_share > MAX_GPU_DOM:
            ev["kill_triggered"].append(f"gpu_farm_dominated: gpu_share={gpu_share:.0%}")

        # Signature conditions
        if algo not in RUNNABLE_ALGOS:
            ev["sig_failed"].append(f"algo_runnable: {algo} not in RUNNABLE_ALGOS")

        fleet_share = FLEET_HASHRATE / max(nh, 1)
        if fleet_share < MIN_FLEET_SHARE:
            ev["sig_failed"].append(
                f"fleet_share_viable: {fleet_share:.2e} < {MIN_FLEET_SHARE}")

        # Cost model: simplified — actual kWh/coin = block_reward_energy_kJ / fleet_coins_per_day
        # Without real data use a heuristic: estimate coins/day from fleet_share and block_reward
        block_reward = c.get("block_reward_coins", None)
        blocks_per_day = c.get("blocks_per_day", None)
        if block_reward and blocks_per_day:
            fleet_coins_per_day = fleet_share * float(block_reward) * float(blocks_per_day)
            opex_per_day = (FLEET_HASHRATE / 1e6) * 24 * POWER_COST  # rough W model
            cost_per_coin = opex_per_day / max(fleet_coins_per_day, 1e-9)
            threshold = price * (1 - ENERGY_MARGIN)
            if cost_per_coin >= threshold:
                ev["kill_triggered"].append(
                    f"cost_exceeds_price: ${cost_per_coin:.4f} >= ${threshold:.4f}")
            else:
                ev["cost_per_coin"] = round(cost_per_coin, 6)
        else:
            # Cost inputs missing — cannot verify profitability
            ev["sig_failed"].append("cost_below_price: block_reward/blocks_per_day not available")

        if ev["kill_triggered"]:
            ev["edge_present"] = False
            return ev

        ev["edge_present"] = (not ev["sig_failed"] and not ev["kill_triggered"]
                              and not ev["inputs_missing"])
        if ev["edge_present"]:
            ev["fleet_share"] = round(fleet_share, 6)
        ev["sig_satisfied"] = not ev["sig_failed"]
        return ev

    # ── DISLOCATION edge ──────────────────────────────────────────────────────

    def _eval_dislocation(self, c: dict) -> dict:
        ev = {"sizing": "SPECULATIVE", "sig_satisfied": False,
              "kill_triggered": [], "inputs_missing": [], "sig_failed": [],
              "edge_present": False}

        # Required inputs
        forensic_vetoed  = c.get("forensic_vetoed")
        forensic_reasons = c.get("forensic_reasons")
        max_dd           = c.get("max_dd_pct")
        price_7d         = c.get("price_7d_pct")
        fear_type        = c.get("fear_type")           # set by EdgeClassifier
        holder_delta     = c.get("holder_count_delta")  # set by HolderChecker

        # Check completeness
        for name, val in [("forensic_vetoed", forensic_vetoed),
                          ("forensic_reasons", forensic_reasons),
                          ("max_dd_pct", max_dd), ("price_7d_pct", price_7d)]:
            if val is None:
                ev["inputs_missing"].append(name)

        if ev["inputs_missing"]:
            ev["edge_present"] = False
            return ev

        # Kill conditions — check first
        if forensic_vetoed is True or (forensic_reasons and len(forensic_reasons) > 0):
            ev["kill_triggered"].append(
                f"forensics_flag_anything: vetoed={forensic_vetoed} "
                f"reasons={len(forensic_reasons or [])}")

        if float(max_dd) >= -DD_FLOOR:
            ev["kill_triggered"].append(
                f"no_dislocation: max_dd={max_dd:.1f}% >= -{DD_FLOOR}%")

        if fear_type in (None, "UNKNOWN", "INSIDER_DUMP"):
            ev["kill_triggered"].append(
                f"fear_justified_or_unknown: fear_type={fear_type}")

        if ev["kill_triggered"]:
            ev["edge_present"] = False
            return ev

        # Signature conditions
        if forensic_vetoed is not False or (forensic_reasons and forensic_reasons != []):
            ev["sig_failed"].append("forensics_clean: veto or reasons present")

        if float(max_dd) >= -DD_FLOOR:
            ev["sig_failed"].append(f"dislocation_present: max_dd={max_dd} >= -{DD_FLOOR}")

        if float(price_7d) < RECOVERY_SIG:
            ev["sig_failed"].append(
                f"dislocation_present: still crashing price_7d={price_7d} < {RECOVERY_SIG}")

        if fear_type not in ("PANIC_SELL", "SECTOR_CONTAGION"):
            ev["sig_failed"].append(f"fear_falsifiable: fear_type={fear_type}")

        if holder_delta is not None and int(holder_delta) < 0:
            ev["sig_failed"].append(
                f"fear_falsifiable: holder_count fell during dd (insider_dump signal)")

        ev["sig_satisfied"] = not ev["sig_failed"]
        ev["edge_present"]  = ev["sig_satisfied"] and not ev["kill_triggered"]
        return ev

    # ── YIELD edge ────────────────────────────────────────────────────────────

    def _eval_yield(self, c: dict) -> dict:
        ev = {"sizing": "CORE", "sig_satisfied": False, "kill_triggered": [],
              "inputs_missing": [], "sig_failed": [], "edge_present": False}

        ram_gb   = c.get("node_min_ram_gb")
        disk_gb  = c.get("node_min_disk_gb")
        rew_rate = c.get("reward_rate_coins_per_day")
        price    = c.get("coin_price")
        gated    = c.get("is_capital_gated")
        perm     = c.get("is_permissioned")
        min_stake= c.get("min_stake_usd")

        for name, val in [("node_min_ram_gb", ram_gb), ("node_min_disk_gb", disk_gb),
                          ("reward_rate_coins_per_day", rew_rate), ("coin_price", price)]:
            if val is None:
                ev["inputs_missing"].append(name)

        if ev["inputs_missing"]:
            ev["edge_present"] = False
            return ev

        # Kill
        opex_per_day = (NODE_POWER_W / 1000) * 24 * POWER_COST
        reward_usd   = float(rew_rate) * float(price)
        if reward_usd <= opex_per_day:
            ev["kill_triggered"].append(
                f"rewards_below_opex: reward=${reward_usd:.4f} <= opex=${opex_per_day:.4f}/day")

        if gated is True or (min_stake and float(min_stake) > MAX_STAKE_CAP):
            ev["kill_triggered"].append(
                f"capital_gated: min_stake=${min_stake} > max=${MAX_STAKE_CAP}")

        if perm is True:
            ev["kill_triggered"].append("permissioned: validator set not open")

        if ev["kill_triggered"]:
            ev["edge_present"] = False
            return ev

        # Signature
        if float(ram_gb) > FLEET_RAM_GB:
            ev["sig_failed"].append(f"node_runnable: ram={ram_gb}GB > fleet={FLEET_RAM_GB}GB")
        if float(disk_gb) > FLEET_DISK_GB:
            ev["sig_failed"].append(f"node_runnable: disk={disk_gb}GB > fleet={FLEET_DISK_GB}GB")

        ev["sig_satisfied"] = not ev["sig_failed"]
        ev["edge_present"]  = ev["sig_satisfied"] and not ev["kill_triggered"]
        return ev

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_fv(c: dict, key: str) -> FieldValue:
        """Extract a FieldValue from coin dict, or return MISSING."""
        val = c.get(key)
        if val is None:
            return FieldValue.missing("coin_dict")
        if isinstance(val, dict) and "status" in val:
            return FieldValue(value=val.get("value"), status=val["status"],
                              source=val.get("source","unknown"))
        # Raw value — treat as MEASURED
        return FieldValue.measured(val, "coin_dict")
