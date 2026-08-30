"""
Holder Checker — Fix B
=======================
Fetches top-10 holder concentration for each coin via GoPlus Security API
(free tier, no key required for basic requests).

Annotates each coin with:
  top10_holder_pct    : float — sum of top-10 holders as % of total supply
  top10_unlocked_pct  : float — same, excluding wallets GoPlus tags as locked
  holder_count        : int   — total number of distinct holders on-chain
  holder_chain        : str   — chain that was successfully queried
  holder_status       : str   — "PASS" | "VETOED" | "HOLD_FOR_REVIEW"
  holder_reason       : str   — reason string (for HOLD_FOR_REVIEW or VETOED)

holder_status semantics (CRITICAL distinction):
  PASS            — data fetched, concentration below veto threshold
  VETOED          — data fetched, concentration EXCEEDS threshold → veto engine blocks
  HOLD_FOR_REVIEW — data could NOT be fetched (no contract, unsupported chain,
                    GoPlus error, anomalous response). This coin gets ZERO allocation
                    but is logged separately from vetoed coins so you can manually
                    verify whether it is safe to include.

Why HOLD_FOR_REVIEW matters:
  ROBO (Fabric Protocol) previously escaped filters because CoinGecko 429'd
  its detail call at the scoring stage. If we cannot fetch holder data, the
  correct answer is "unverified — cannot allocate", NOT "passed because fetch failed."
  A coin we cannot verify is not a coin that passed.

Age logic (inverted vs social/derivs):
  For social/derivs young coins get a soft pass — the signal hasn't formed yet.
  For holder concentration the OPPOSITE applies: a young coin where 10 wallets
  already hold most of the supply has NOT had time to distribute, which is MORE
  suspicious (team/insider hoarding before distribution). No age-based softening
  is applied here. The threshold is the same for young and mature coins.

Anomaly guard:
  If GoPlus returns holder_count < MIN_HOLDER_COUNT_VALID (e.g. 1 holder at 100%),
  the contract is almost certainly a bridge escrow or wrong address — mark
  HOLD_FOR_REVIEW rather than VETOED to avoid acting on bad data.
"""
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests

# ── GoPlus chain ID map (EVM chains with reliable holder data) ─────────────
GOPLUS_CHAIN_IDS: Dict[str, str] = {
    "ethereum":             "1",
    "binance-smart-chain":  "56",
    "base":                 "8453",
    "arbitrum-one":         "42161",
    "polygon-pos":          "137",
    "optimistic-ethereum":  "10",
    "avalanche":            "43114",
    "fantom":               "250",
    "cronos":               "25",
}

# Preference order when a token is on multiple supported chains.
# Base and Arbitrum before BSC: higher signal quality, lower wash-trading.
# (BSC data is valid but BSC is not the primary chain for most new L2 tokens.)
CHAIN_PRIORITY = [
    "ethereum", "base", "arbitrum-one",
    "binance-smart-chain", "polygon-pos", "optimistic-ethereum", "avalanche",
    "fantom", "cronos",
]

# Holder tags that identify public/exchange/LP wallets.
# If GoPlus tags a holder with any of these keywords the wallet is EXCLUDED
# from max_single_pct (it is not an insider, it is a custodian/DEX).
# For new tokens tag=[] almost universally — exclusion is a no-op today but
# becomes meaningful as GoPlus extends coverage to newer contracts.
_EXCLUDED_HOLDER_TAG_KEYWORDS = frozenset([
    "binance", "coinbase", "kraken", "huobi", "okx", "bybit",
    "kucoin", "uniswap", "pancakeswap", "curve", "sushiswap",
    "balancer", "camelot", "aave", "compound",
])

GOPLUS_BASE = "https://api.gopluslabs.io/api/v1"


class HolderChecker:
    """
    Fetches and annotates holder concentration data for each coin.
    Uses GoPlus Security API (free tier sufficient for ≤100 req/min).
    """

    DETAIL_CACHE         = Path("data/coin_hunter_details.json")
    SLEEP_BETWEEN_SEC    = 1.5    # GoPlus free tier: ~60 req/min
    REQUEST_TIMEOUT      = 15

    # Guard: fewer than this many holders → contract is probably a bridge/escrow
    MIN_HOLDER_COUNT_VALID = 20

    def __init__(self, goplus_api_key: str = ""):
        self._detail_cache = self._load_detail_cache()
        self._headers: Dict[str, str] = {}
        if goplus_api_key:
            self._headers["Authorization"] = goplus_api_key

    # ── Public API ─────────────────────────────────────────────────────────

    def fetch(self, coins: List[Dict]) -> List[Dict]:
        """
        Annotate each coin in-place with holder concentration fields.
        Prints per-coin log line. Returns the mutated list.
        """
        for i, c in enumerate(coins):
            sym = c.get("symbol", "?")
            print(f"  [HolderChecker] {sym}...", end=" ", flush=True)
            result = self._fetch_one(c)
            c.update(result)

            status = result["holder_status"]
            if status == "HOLD_FOR_REVIEW":
                print(f"HOLD_FOR_REVIEW  ({result['holder_reason']})")
            else:
                print(
                    f"top10={result['top10_holder_pct']:.1f}%  "
                    f"unlocked={result['top10_unlocked_pct']:.1f}%  "
                    f"max_single={result['max_single_pct']:.1f}%  "
                    f"deployer={result['deployer_pct']:.4f}%  "
                    f"locked_ratio={result['locked_ratio_pct']:.0f}%  "
                    f"count={result['holder_count']}  "
                    f"chain={result['holder_chain']}  "
                    f"-> {status}"
                )

            if i < len(coins) - 1:
                time.sleep(self.SLEEP_BETWEEN_SEC)

        return coins

    def summary_str(self, coins: List[Dict]) -> str:
        """One-liner for Telegram/console: shows HOLD count + any holder-vetoed coins."""
        held   = [c for c in coins if c.get("holder_status") == "HOLD_FOR_REVIEW"]
        h_veto = [c for c in coins if c.get("holder_status") == "VETOED"]
        ok     = [c for c in coins if c.get("holder_status") == "PASS"]
        parts  = []
        if h_veto:
            parts.append(
                f"{len(h_veto)} concentration-vetoed: "
                f"{', '.join(c['symbol'] for c in h_veto)}"
            )
        if held:
            parts.append(
                f"{len(held)} HOLD_FOR_REVIEW: "
                f"{', '.join(c['symbol'] for c in held)}"
            )
        if ok:
            parts.append(f"{len(ok)} holder-OK")
        return "Holder: " + " | ".join(parts) if parts else "Holder: no data"

    # ── Internal helpers ────────────────────────────────────────────────────

    def _load_detail_cache(self) -> Dict:
        if not self.DETAIL_CACHE.exists():
            return {}
        try:
            return json.loads(self.DETAIL_CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _fetch_one(self, c: Dict) -> Dict:
        """Return annotation dict for one coin."""
        base: Dict = {
            "top10_holder_pct":   0.0,
            "top10_unlocked_pct": 0.0,
            "max_single_pct":     0.0,   # largest holder excl. tagged exchange/LP wallets
            "deployer_pct":       0.0,   # current holding of contract deployer (creator_percent)
            "deployer_known":     False, # True when GoPlus returns a non-empty creator_address
            "locked_ratio_pct":   0.0,   # % of top-10 concentration that GoPlus marks is_locked=1
            "holder_count":       0,
            "holder_chain":       "",
            "holder_status":      "HOLD_FOR_REVIEW",
            "holder_reason":      "not_checked",
        }

        sym    = c.get("symbol", "?")
        detail = self._find_detail(sym)
        if detail is None:
            base["holder_reason"] = "no_detail_cache"
            return base

        platforms = detail.get("platforms", {})
        if not platforms:
            base["holder_reason"] = "no_contract_address"
            return base

        chain, addr = self._best_chain(platforms)
        if chain is None or not addr:
            # Non-EVM or unsupported chain
            non_evm = [k for k in platforms if k and k not in GOPLUS_CHAIN_IDS and platforms[k]]
            base["holder_reason"] = (
                f"unsupported_chain: {non_evm[0]}" if non_evm else "no_supported_chain"
            )
            return base

        return self._call_goplus(GOPLUS_CHAIN_IDS[chain], chain, addr, base)

    def _find_detail(self, symbol: str) -> Optional[Dict]:
        """Look up coin detail by symbol (case-insensitive) in cache."""
        sym_lower = symbol.lower()
        for detail in self._detail_cache.values():
            if detail.get("symbol", "").lower() == sym_lower:
                return detail
        return None

    def _best_chain(self, platforms: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Return (chain_name, contract_address) for the highest-priority EVM chain."""
        for chain in CHAIN_PRIORITY:
            addr = platforms.get(chain, "")
            if addr and addr.startswith("0x") and len(addr) >= 10:
                return chain, addr
        return None, None

    def _call_goplus(self, chain_id: str, chain_name: str,
                     contract: str, base: Dict) -> Dict:
        """
        Call GoPlus token_security endpoint and parse holder data.
        Mutates and returns base dict.
        """
        url    = f"{GOPLUS_BASE}/token_security/{chain_id}"
        params = {"contract_addresses": contract.lower()}

        try:
            r = requests.get(url, params=params, headers=self._headers,
                             timeout=self.REQUEST_TIMEOUT)
        except Exception as e:
            base["holder_reason"] = f"fetch_error:{str(e)[:40]}"
            return base

        if r.status_code == 429:
            base["holder_reason"] = "goplus_rate_limited"
            return base
        if r.status_code != 200:
            base["holder_reason"] = f"http_{r.status_code}"
            return base

        try:
            payload = r.json()
        except Exception:
            base["holder_reason"] = "json_parse_error"
            return base

        if payload.get("code") != 1:
            base["holder_reason"] = f"goplus_code_{payload.get('code', '?')}"
            return base

        result     = payload.get("result", {}) or {}
        token_data = result.get(contract.lower(), {}) or {}
        if not token_data:
            # Try case-insensitive match
            for k, v in result.items():
                if k.lower() == contract.lower():
                    token_data = v or {}
                    break

        if not token_data:
            base["holder_reason"] = "empty_token_data"
            return base

        holders = token_data.get("holders") or []
        if not holders:
            base["holder_reason"] = "no_holders_field"
            return base

        h_count = int(token_data.get("holder_count", 0) or 0)

        # Guard: anomalously low holder count → wrong contract (bridge/escrow)
        if h_count < self.MIN_HOLDER_COUNT_VALID:
            base["holder_count"]  = h_count
            base["holder_chain"]  = chain_name
            base["holder_reason"] = (
                f"anomalous_holder_count={h_count} -- likely bridge/escrow contract"
            )
            return base   # stays HOLD_FOR_REVIEW

        # Sum top-10 (GoPlus returns them sorted by percent descending)
        top10 = holders[:10]
        total_pct    = sum(float(h.get("percent") or 0) * 100 for h in top10)
        unlocked_pct = sum(
            float(h.get("percent") or 0) * 100
            for h in top10
            if int(h.get("is_locked") or 0) == 0
        )

        # ── NEW: max_single_pct ───────────────────────────────────────────
        # Largest single holder, excluding wallets GoPlus tags as exchange/LP.
        # For new tokens tag=[] universally, so no exclusion occurs in practice
        # today — but this correctly handles future GoPlus coverage improvements.
        # Note: we search ALL holders (not just top10) for the true maximum,
        # but in practice the largest is always within top10.
        max_single = 0.0
        for h in holders:
            tags = h.get("tag") or []
            if isinstance(tags, str):
                tags = [tags]
            # Skip wallets explicitly tagged as public exchange/LP addresses
            if tags and any(
                ex_kw in str(t).lower()
                for t in tags
                for ex_kw in _EXCLUDED_HOLDER_TAG_KEYWORDS
            ):
                continue
            pct_val = float(h.get("percent") or 0) * 100
            if pct_val > max_single:
                max_single = pct_val

        # ── NEW: deployer fields ──────────────────────────────────────────
        # creator_percent: GoPlus returns this as a fraction (same scale as
        # holder 'percent'), so multiply by 100 for % value.
        deployer_pct   = float(token_data.get("creator_percent") or 0) * 100
        creator_addr   = str(token_data.get("creator_address") or "").strip()
        deployer_known = bool(creator_addr)

        # ── NEW: locked_ratio_pct ─────────────────────────────────────────
        # Fraction of top-10 concentration that GoPlus marks as locked.
        # KNOWN LIMITATION: GoPlus cannot verify vesting contracts for most
        # new tokens (<6 months old) → is_locked=0 for almost everything.
        # locked_ratio_pct will read 0% for all new tokens in practice.
        # This soft metric becomes useful only once GoPlus extends lock detection.
        locked_top10_pct = sum(
            float(h.get("percent") or 0) * 100
            for h in top10
            if int(h.get("is_locked") or 0) == 1
        )
        locked_ratio_pct = (
            round(locked_top10_pct / total_pct * 100, 1)
            if total_pct > 0 else 0.0
        )

        base.update({
            "top10_holder_pct":   round(total_pct, 1),
            "top10_unlocked_pct": round(unlocked_pct, 1),
            "max_single_pct":     round(max_single, 1),
            "deployer_pct":       round(deployer_pct, 4),
            "deployer_known":     deployer_known,
            "locked_ratio_pct":   locked_ratio_pct,
            "holder_count":       h_count,
            "holder_chain":       chain_name,
            "holder_status":      "PASS",   # threshold applied by VetoEngine
            "holder_reason":      "ok",
        })
        return base
