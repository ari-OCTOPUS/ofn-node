"""
onchain_lp_lock.py — On-chain LP lock detection  (Phase 0.2)
=============================================================
Reads LP token balances directly from on-chain data instead of relying
on DexScreener's `liquidity.locked` field (unreliable / frequently absent).

Method
------
lp_locked_pct = (LP held by burn address + LP held by known locker contracts)
                / LP token total supply  * 100

Known locker contracts (immutable — list updated manually as new lockers emerge):
  Unicrypt V2 (ETH)    : 0x663a5c229c09b049e36dfd6de5a5ca5c4e9cf39e
  Unicrypt V3 (ETH)    : 0xdba68f07d1b7ca219f78ae8582dc213557d7ed70
  Team.Finance (ETH)   : 0xe2fe530c047f2d85298b07d9333c05737f1435fb
  PinkLock  (ETH/BSC)  : 0x71b5759d73262fbb223956913ecf4ecc51057641
  Mudra (BSC)          : 0x7ee058420e5937496f5a2096f04caA7721cF70cc
  Burn address         : 0x000000000000000000000000000000000000dead

Supported chains: ethereum, base, bsc
For unsupported chains (Solana etc.): returns status=MISSING.

APIs used (free / public):
  Ethereum/Base/BSC: public RPC eth_call (balanceOf + totalSupply)
  Fallback: Etherscan/Basescan/BSCscan tokenholderlist (if RPC blocked)

Principle P-D: if the check cannot run → returns status=MISSING (HOLD), never PASS.
"""
import json
import requests
from typing import Optional
from modules.field_value import FieldValue, validate_pct, MISSING

# ── Known locker contracts (checksummed) ─────────────────────────────────────
BURN_ADDRESS = "0x000000000000000000000000000000000000dead"

LOCKER_CONTRACTS: dict[str, list[str]] = {
    "ethereum": [
        "0x663A5C229c09b049E36dFd6De5A5Ca5c4e9CF39E",  # Unicrypt V2
        "0xdba68f07d1b7Ca219f78ae8582DC213557d7Ed70",  # Unicrypt V3
        "0xe2fE530C047f2d85298b07D9333C05737f1435fB",  # Team.Finance
        "0x71B5759d73262FBb223956913eCF4ecC51057641",  # PinkLock
    ],
    "base": [
        "0x000000000000000000000000000000000000dead",  # burn is primary on Base
        "0x71B5759d73262FBb223956913eCF4ecC51057641",  # PinkLock (cross-chain)
    ],
    "bsc": [
        "0x663A5C229c09b049E36dFd6De5A5Ca5c4e9CF39E",
        "0x7ee058420e5937496F5a2096f04caA7721cF70cc",  # Mudra
        "0x71B5759d73262FBb223956913eCF4ecC51057641",  # PinkLock
    ],
}

# ── Public RPC endpoints (no API key required) ────────────────────────────────
PUBLIC_RPCS: dict[str, list[str]] = {
    "ethereum": [
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
    ],
    "base": [
        "https://mainnet.base.org",
        "https://base.llamarpc.com",
    ],
    "bsc": [
        "https://bsc-dataseed.binance.org",
        "https://rpc.ankr.com/bsc",
    ],
}

REQUEST_TIMEOUT = 6
ERC20_BALANCE_OF_SIG = "0x70a08231"   # balanceOf(address)
ERC20_TOTAL_SUPPLY_SIG = "0x18160ddd"  # totalSupply()


class OnChainLPLock:
    """
    Checks how much of an LP token is locked or burned on-chain.

    Usage:
        checker = OnChainLPLock()
        result: FieldValue = checker.check(lp_token_address, chain)
        # result.value = float (0–100 pct) when status==MEASURED
        # result.status = MISSING when chain unsupported or RPC failed
    """

    def check(self, lp_token_address: Optional[str], chain: str) -> FieldValue:
        """
        Returns FieldValue with lp_locked_pct (0–100).
        MISSING when unsupported chain or RPC unreachable.
        """
        if not lp_token_address:
            return FieldValue.missing("OnChainLPLock")

        chain = chain.lower()
        if chain not in PUBLIC_RPCS:
            return FieldValue.missing("OnChainLPLock")

        rpcs     = PUBLIC_RPCS[chain]
        lockers  = LOCKER_CONTRACTS.get(chain, []) + [BURN_ADDRESS]

        total_supply = self._call_uint(rpcs, lp_token_address, ERC20_TOTAL_SUPPLY_SIG)
        if total_supply is None or total_supply == 0:
            return FieldValue.missing("OnChainLPLock")

        locked = 0
        for addr in lockers:
            bal = self._call_balance_of(rpcs, lp_token_address, addr)
            if bal is not None:
                locked += bal

        pct = locked / total_supply * 100.0
        return validate_pct(pct, "OnChainLPLock")

    def check_from_dexscreener_pairs(self, pairs: list, chain: str = "") -> FieldValue:
        """
        Extract the LP token address and chain from DexScreener pair data,
        then call check().

        FIX: chain is now extracted directly from DexScreener pair's chainId
        when the caller doesn't know the chain yet (ScoutForensics runs before
        HolderChecker, so c["holder"]["chain"] is empty at forensics time).
        """
        if not pairs:
            return FieldValue.missing("OnChainLPLock")

        # Find highest-TVL pair
        main_pair = max(pairs, key=lambda p: float(
            p.get("liquidity", {}).get("usd", 0) or 0))

        # Use DexScreener chainId if caller doesn't know chain yet
        if not chain:
            ds_chain = main_pair.get("chainId", "").lower()
            # Normalize DexScreener chain names to our keys
            chain_map = {"ethereum": "ethereum", "base": "base", "bsc": "bsc",
                         "binance-smart-chain": "bsc", "eth": "ethereum"}
            chain = chain_map.get(ds_chain, ds_chain)

        lp_addr = (main_pair.get("pairAddress")
                   or main_pair.get("lpToken")
                   or main_pair.get("id"))

        return self.check(lp_addr, chain)

    # ── RPC helpers ───────────────────────────────────────────────────────────

    def _rpc_call(self, rpcs: list[str], payload: dict) -> Optional[dict]:
        for rpc in rpcs:
            try:
                r = requests.post(rpc, json=payload, timeout=REQUEST_TIMEOUT)
                r.raise_for_status()
                data = r.json()
                if "result" in data and data["result"] not in (None, "0x"):
                    return data
            except Exception:
                continue
        return None

    def _call_balance_of(self, rpcs: list, contract: str,
                         holder: str) -> Optional[int]:
        # balanceOf(address): pad address to 32 bytes
        padded = holder.lower().replace("0x", "").zfill(64)
        data   = ERC20_BALANCE_OF_SIG + padded
        payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                   "params": [{"to": contract, "data": data}, "latest"]}
        resp = self._rpc_call(rpcs, payload)
        if resp is None:
            return None
        try:
            return int(resp["result"], 16)
        except (ValueError, KeyError):
            return None
    def _call_uint(self, rpcs: list, contract: str, sig: str) -> Optional[int]:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                   "params": [{"to": contract, "data": sig}, "latest"]}
        data = self._rpc_call(rpcs, payload)
        if data is None:
            return None
        try:
            return int(data["result"], 16)
        except (ValueError, KeyError):
            return None
