"""
launch_cluster.py — First-N-block coordinated launch detection  (Phase 2.2)
============================================================================
Reads the first FIRST_BLOCKS_TO_CHECK blocks of token-transfer events from
Etherscan / Basescan (free tier, no key needed for basic queries).

Algorithm
---------
1. Fetch the token's creation block from the contract deployment tx.
2. Fetch all Transfer events in blocks [creation, creation+FIRST_BLOCKS].
3. Build a directed graph: sender → receiver for each transfer.
4. Find the largest cluster: set of receivers that share a common upstream
   sender within those first blocks.
5. cluster_pct = tokens received by largest cluster / total tokens transferred
   in those blocks.

Thresholds
----------
  MAX_CLUSTER_PCT = 0.35   cluster holds >35% of early transfers → coordinated
  FIRST_BLOCKS    = 10     analyse first 10 blocks after deployment

Supported chains: ethereum, base  (Basescan API mirrors Etherscan interface)
Principle P-D: if API unavailable → FieldValue.missing(), never PASS.
"""
import requests
import time
from typing import Optional
from modules.field_value import FieldValue

FIRST_BLOCKS    = 10
MAX_CLUSTER_PCT = 0.35
REQUEST_TIMEOUT = 8

# Free-tier API endpoints (no key required for basic token transfer queries)
CHAIN_APIS = {
    "ethereum": "https://api.etherscan.io/api",
    "base":     "https://api.basescan.org/api",
}

# Rate limiting — free tier allows ~5 req/s
REQUEST_DELAY = 0.25


class LaunchClusterChecker:
    """
    Detects coordinated wallet clusters in the first N blocks after launch.

    Usage:
        checker = LaunchClusterChecker()
        result = checker.check(token_address, chain)
        # result.value: float (0.0–1.0) cluster fraction, or None if MISSING
        # result.status: MEASURED | MISSING
    """

    def check(self, token_address: Optional[str], chain: str) -> FieldValue:
        chain = chain.lower()
        if chain not in CHAIN_APIS or not token_address:
            return FieldValue.missing("LaunchCluster")

        api_url = CHAIN_APIS[chain]

        # 1. Get creation block
        creation_block = self._get_creation_block(api_url, token_address)
        if creation_block is None:
            return FieldValue.missing("LaunchCluster")

        end_block = creation_block + FIRST_BLOCKS

        # 2. Fetch early transfers
        transfers = self._get_transfers(api_url, token_address,
                                        creation_block, end_block)
        if transfers is None:
            return FieldValue.missing("LaunchCluster")
        if len(transfers) == 0:
            # No transfers in first blocks — cannot assess
            return FieldValue.missing("LaunchCluster")

        # 3. Build sender→receivers graph
        graph: dict[str, set] = {}
        total_value = 0
        receiver_value: dict[str, int] = {}

        for tx in transfers:
            sender   = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            try:
                value = int(tx.get("value", "0"))
            except (ValueError, TypeError):
                value = 0
            if sender and receiver and value > 0:
                graph.setdefault(sender, set()).add(receiver)
                receiver_value[receiver] = receiver_value.get(receiver, 0) + value
                total_value += value

        if total_value == 0:
            return FieldValue.missing("LaunchCluster")

        # 4. Find largest cluster (receivers sharing a common early sender)
        max_cluster_value = 0
        for sender, receivers in graph.items():
            cluster_val = sum(receiver_value.get(r, 0) for r in receivers)
            if cluster_val > max_cluster_value:
                max_cluster_value = cluster_val

        cluster_pct = max_cluster_value / total_value
        return FieldValue.measured(round(cluster_pct, 4), "LaunchCluster")

    # ── API helpers ───────────────────────────────────────────────────────────

    def _get_creation_block(self, api_url: str,
                            token_address: str) -> Optional[int]:
        params = {
            "module":  "account",
            "action":  "txlist",
            "address": token_address,
            "page":    1,
            "offset":  1,
            "sort":    "asc",
        }
        data = self._call(api_url, params)
        if data is None:
            return None
        txs = data.get("result", [])
        if not txs or not isinstance(txs, list):
            return None
        try:
            return int(txs[0].get("blockNumber", 0))
        except (ValueError, TypeError):
            return None

    def _get_transfers(self, api_url: str, token_address: str,
                       start_block: int, end_block: int) -> Optional[list]:
        params = {
            "module":          "account",
            "action":          "tokentx",
            "contractaddress": token_address,
            "startblock":      start_block,
            "endblock":        end_block,
            "page":            1,
            "offset":          200,
            "sort":            "asc",
        }
        data = self._call(api_url, params)
        if data is None:
            return None
        result = data.get("result", [])
        if not isinstance(result, list):
            return None
        return result

    def _call(self, url: str, params: dict) -> Optional[dict]:
        try:
            time.sleep(REQUEST_DELAY)
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "1":
                return data
            # status=0 may mean "no transactions" (not an error)
            if data.get("message") in ("No transactions found", "No records found"):
                return {"result": []}
            return None
        except Exception as e:
            print(f"  [LaunchCluster] API error: {e}")
            return None
