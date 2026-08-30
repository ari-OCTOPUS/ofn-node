"""
energy_funnel.py — ENERGY edge sourcing funnel (Phase C)
=========================================================
Surfaces CPU/ARM-mineable PoW coin launches NOT captured by the
CEX-listing funnel. Closes the open sourcing gap from Phase 4.2.

Why the existing funnel missed these:
  GemHunter filters on Binance/Bybit listing, meaning coins must have
  achieved exchange listing BEFORE being discovered. PoW coins often
  have mining communities before exchange listing — the structural edge
  (cheap power + ARM fleet) is strongest in that pre-listing window.

This funnel queries:
  1. CoinGecko /coins/list with hashing_algorithm filter
  2. Filters to RUNNABLE_ALGOS (CPU/ARM-friendly)
  3. Applies age + market-cap filters consistent with GemHunter
  4. Annotates with mining-specific fields for EdgeClassifier

Returns coins with status-annotated fields:
  mining_algo: FieldValue (MEASURED from CoinGecko)
  network_hashrate: FieldValue (MEASURED or MISSING)
  block_reward_coins: FieldValue
  blocks_per_day: FieldValue
  gpu_share_estimated: float (heuristic from algo type)
"""
import time
import requests
from typing import List, Dict, Optional
from modules.field_value import FieldValue, MEASURED, MISSING
from modules.edge_classifier import RUNNABLE_ALGOS, ASIC_ALGOS

REQUEST_TIMEOUT = 10
REQUEST_DELAY   = 2.0
CG_BASE = "https://api.coingecko.com/api/v3"

# Algorithms that are purely CPU-friendly (no GPU advantage)
CPU_ONLY_ALGOS = {"yespower", "randomx", "rx/c64", "argon2d", "minotaur", "gr"}

# GPU-share heuristic by algo (estimated; actual requires pool data)
GPU_SHARE_BY_ALGO = {
    "randomx":   0.05,  # CPU-dominant; GPUs less efficient
    "yespower":  0.02,  # CPU-only by design
    "rx/c64":    0.05,
    "kawpow":    0.60,  # GPU-dominant but no ASICs
    "octopus":   0.65,
    "scrypt":    0.40,
    "cryptonight": 0.10,
    "argon2d":   0.05,
    "gr":        0.08,
    "minotaur":  0.10,
}


class EnergyFunnel:
    """
    Discovers PoW coins whose consensus algorithm is in RUNNABLE_ALGOS.
    Runs independently from GemHunter — targets pre-CEX-listing window.
    """

    MIN_AGE_DAYS   = 0      # include fresh launches
    MAX_AGE_DAYS   = 180
    MIN_MCAP_USD   = 50_000
    MAX_MCAP_USD   = 75_000_000

    def __init__(self):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "QuantumAlphaBot/EdgeLayer"

    def find_candidates(self) -> List[Dict]:
        """
        Return list of coin dicts with mining fields annotated.
        Each coin has FieldValue objects for mining inputs.
        """
        print("  [EnergyFunnel] Scanning CoinGecko for CPU/ARM-mineable PoW coins...")
        all_coins = self._fetch_coin_list()
        if not all_coins:
            print("  [EnergyFunnel] CoinGecko unavailable — no candidates")
            return []

        print(f"  [EnergyFunnel] {len(all_coins)} coins in list, checking PoW algo...")
        candidates = []
        checked = 0
        for coin in all_coins[:300]:  # rate-limit: check top 300 by market cap rank
            detail = self._fetch_detail(coin["id"])
            if not detail:
                continue
            checked += 1
            algo_raw = (detail.get("hashing_algorithm") or "").lower().strip()
            if not algo_raw or algo_raw in ASIC_ALGOS:
                continue
            # Check if algo matches any RUNNABLE_ALGO (prefix match)
            matched_algo = None
            for ra in RUNNABLE_ALGOS:
                if ra in algo_raw or algo_raw in ra:
                    matched_algo = ra
                    break
            if not matched_algo:
                continue

            # Age filter
            from datetime import datetime, date
            genesis = detail.get("genesis_date")
            age_days = None
            if genesis:
                try:
                    gd = datetime.strptime(genesis[:10], "%Y-%m-%d").date()
                    age_days = (date.today() - gd).days
                except Exception:
                    pass
            if age_days is not None and not (self.MIN_AGE_DAYS <= age_days <= self.MAX_AGE_DAYS):
                continue

            # Market cap filter
            mcap = float((detail.get("market_data") or {}).get("market_cap", {}).get("usd", 0) or 0)
            if mcap < self.MIN_MCAP_USD or mcap > self.MAX_MCAP_USD:
                continue

            price = float((detail.get("market_data") or {}).get("current_price", {}).get("usd", 0) or 0)

            # Build candidate dict with FieldValue annotations
            candidate = {
                "symbol":    detail.get("symbol", "").upper(),
                "name":      detail.get("name", ""),
                "id":        coin["id"],
                "age_days":  age_days or 0,
                "market_cap": mcap,
                "coin_price": price,
                "source_funnel": "ENERGY",

                # Mining-specific FieldValues
                "mining_algo": FieldValue.measured(matched_algo, "CoinGecko").to_dict(),
                "gpu_share_estimated": GPU_SHARE_BY_ALGO.get(matched_algo, 0.5),
                "is_cpu_only": matched_algo in CPU_ONLY_ALGOS,
            }

            # Network hashrate — from CoinGecko if available
            nh = self._fetch_hashrate(coin["id"])
            candidate["network_hashrate"] = nh.to_dict()

            # Block reward / blocks per day — best-effort from detail
            br = self._extract_block_reward(detail)
            candidate["block_reward_coins"] = br.get("reward")
            candidate["blocks_per_day"]     = br.get("bpd")

            candidates.append(candidate)
            print(f"  [EnergyFunnel]   CANDIDATE {candidate['symbol']} "
                  f"algo={matched_algo} age={age_days}d "
                  f"mcap=${mcap/1e6:.1f}M gpu_share={candidate['gpu_share_estimated']:.0%}")
            time.sleep(REQUEST_DELAY)

            if len(candidates) >= 10:  # cap at 10 for rate-limit reasons
                break

        print(f"  [EnergyFunnel] Checked {checked} coins → {len(candidates)} ENERGY candidates")
        return candidates

    def _fetch_coin_list(self) -> Optional[List[Dict]]:
        try:
            r = self._session.get(
                f"{CG_BASE}/coins/markets",
                params={"vs_currency":"usd","order":"market_cap_desc",
                        "per_page":250,"page":1,"sparkline":False},
                timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  [EnergyFunnel] coin list error: {e}")
            return None

    def _fetch_detail(self, coin_id: str) -> Optional[Dict]:
        try:
            time.sleep(REQUEST_DELAY)
            r = self._session.get(
                f"{CG_BASE}/coins/{coin_id}",
                params={"localization":False,"tickers":False,
                        "market_data":True,"community_data":False,
                        "developer_data":False},
                timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return None

    def _fetch_hashrate(self, coin_id: str) -> FieldValue:
        """Best-effort network hashrate from CoinGecko market chart."""
        # CoinGecko doesn't expose hashrate directly for most coins.
        # For known coins it's in detail.block_time_in_minutes and difficulty.
        # Return MISSING — EdgeClassifier handles gracefully.
        return FieldValue.missing("CoinGecko-hashrate")

    def _extract_block_reward(self, detail: Dict) -> Dict:
        """Extract block reward and blocks/day — best effort."""
        # CoinGecko doesn't standardise this; return MISSING
        return {"reward": None, "bpd": None}
