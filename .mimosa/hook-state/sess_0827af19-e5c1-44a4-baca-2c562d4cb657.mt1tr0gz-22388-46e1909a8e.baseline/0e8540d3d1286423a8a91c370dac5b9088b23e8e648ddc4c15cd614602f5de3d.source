"""
Scout Forensics v2 — Pre-scoring forensic kill layer  (Phase 0)
================================================================
Gates BEFORE scoring AND before LLM (Principle P-D: absence = HOLD).

Changes from v1:
  - Integrated on-chain LP lock (OnChainLPLock) — replaces DexScreener lock field
  - All forensic fields now FieldValue tri-state objects
  - Blacklisted coins get decision=KILLED, llm_decision never populated
  - forensic_hold: cannot-verify still blocks (never PASS on missing data)
"""
import time
import requests
from typing import List, Dict, Optional
from modules.field_value import FieldValue, MEASURED, MISSING, UNRELIABLE
from modules.onchain_lp_lock import OnChainLPLock
from modules.launch_cluster import LaunchClusterChecker, MAX_CLUSTER_PCT
from config import FORENSIC_BLACKLIST, DEXSCREENER_BASE_URL

MIN_MAIN_POOL_USD   = 15_000
MAX_SNIPER_RATIO    = 0.40
LP_LOCK_MIN_PCT     = 95.0     # below this = effectively unlocked
REQUEST_TIMEOUT     = 8
REQUEST_DELAY       = 0.4
WHITELISTED_HOOKS: set = set()


class ScoutForensics:

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "QuantumAlphaBot/2.0"})
        self._lp_checker      = OnChainLPLock()
        self._cluster_checker = LaunchClusterChecker()

    def apply(self, coins: List[Dict]) -> List[Dict]:
        for c in coins:
            c["forensic_vetoed"]   = False
            c["forensic_killed"]   = False   # blacklist-level hard kill
            c["forensic_reasons"]  = []
            c["forensic_hold"]     = False
            c.setdefault("asset_type", "UNKNOWN")
            # FieldValue containers — stored as dicts for JSON serialisation
            c["lp_locked_fv"]      = FieldValue.missing("ScoutForensics").to_dict()
            c["pool_tvl_fv"]       = FieldValue.missing("ScoutForensics").to_dict()
            c["hook_safe_fv"]      = FieldValue.missing("ScoutForensics").to_dict()
            c["cluster_fv"]        = FieldValue.missing("ScoutForensics").to_dict()

        for c in coins:
            sym = c.get("symbol", "?")

            # ── 0. Blacklist — instant kill, no API ──────────────────────────
            if self._check_blacklist(c):
                c["forensic_killed"]  = True
                c["forensic_vetoed"]  = True
                c["llm_decision"]     = "KILLED"
                c["llm_confidence"]   = "N/A"
                bl_reason = "BLACKLIST: " + FORENSIC_BLACKLIST.get(sym, "permanent forensic kill")
                c["llm_reasoning"]    = "FORENSIC_" + bl_reason
                c["forensic_reasons"].append(bl_reason)   # so VetoEngine can read it
                print(f"  [ScoutForensics] {sym} → KILLED (BLACKLIST)")
                continue

            # ── 1. Asset type ────────────────────────────────────────────────
            self._classify_asset_type(c)

            # ── 2. DexScreener — pool data ───────────────────────────────────
            pairs = self._fetch_dexscreener(sym)
            chain = (c.get("holder", {}) or {}).get("chain", "")

            # ── 2a. On-chain LP lock (Phase 0.2) ─────────────────────────────
            if pairs is not None:
                lp_fv = self._lp_checker.check_from_dexscreener_pairs(pairs, chain)
            else:
                lp_fv = FieldValue.missing("OnChainLPLock")
            c["lp_locked_fv"] = lp_fv.to_dict()

            if lp_fv.status == MEASURED:
                if lp_fv.value < LP_LOCK_MIN_PCT:
                    reason = (f"LP_UNLOCKED: {lp_fv.value:.1f}% locked "
                              f"(on-chain: burn+lockers / totalSupply). "
                              f"Rug-capable at any time. Threshold={LP_LOCK_MIN_PCT:.0f}%")
                    c["forensic_reasons"].append(reason)
                    c["forensic_vetoed"] = True
            else:
                # P-D: MISSING safety signal = HOLD, never PASS
                c["forensic_hold"] = True
                print(f"  [ScoutForensics] {sym} LP lock → {lp_fv.status} (HOLD)")

            # ── 2b. Pool depth ────────────────────────────────────────────────
            if pairs is not None:
                tvl_fv = self._pool_depth(pairs)
                c["pool_tvl_fv"] = tvl_fv.to_dict()
                if tvl_fv.status == MEASURED and tvl_fv.value < MIN_MAIN_POOL_USD:
                    reason = (f"THIN_LIQUIDITY: main pool TVL=${tvl_fv.value:,.0f} "
                              f"< floor=${MIN_MAIN_POOL_USD:,}. Cannot exit meaningfully.")
                    c["forensic_reasons"].append(reason)
                    c["forensic_vetoed"] = True

            # ── 2c. V4 hook safety ────────────────────────────────────────────
            if pairs is not None:
                hook_fv = self._check_v4_hooks(pairs)
                c["hook_safe_fv"] = hook_fv.to_dict()
                if hook_fv.status == MEASURED and hook_fv.value is False:
                    reason = ("UNVERIFIED_HOOK: Uniswap v4 pool with non-whitelisted hook. "
                              "Hook can override swap logic — sell-blocking risk.")
                    c["forensic_reasons"].append(reason)
                    c["forensic_vetoed"] = True

            # ── 3. Coordinated launch proxy ────────────────────────────────
            # Phase 2.2: real first-N-block cluster detection
            contract_addr = (c.get("holder", {}) or {}).get("contract_address")
            if contract_addr:
                cluster_fv = self._cluster_checker.check(contract_addr, chain)
            else:
                cluster_fv = self._check_launch_cluster_proxy(c)
            c["cluster_fv"] = cluster_fv.to_dict()
            if cluster_fv.status == MEASURED:
                if isinstance(cluster_fv.value, float) and cluster_fv.value > MAX_CLUSTER_PCT:
                    reason = (f"COORDINATED_LAUNCH: first-block cluster holds "
                              f"{cluster_fv.value*100:.1f}% of early supply "
                              f"(threshold={MAX_CLUSTER_PCT*100:.0f}%). "
                              f"Source: {cluster_fv.source}")
                    c["forensic_reasons"].append(reason)
                    c["forensic_vetoed"] = True
                elif cluster_fv.value is True:  # proxy bool path
                    reason = ("COORDINATED_LAUNCH (proxy): holder pattern consistent "
                              "with coordinated sniper cluster at launch.")
                    c["forensic_reasons"].append(reason)
                    c["forensic_vetoed"] = True

            time.sleep(REQUEST_DELAY)
            status = ("VETOED" if c["forensic_vetoed"]
                      else ("HOLD" if c["forensic_hold"] else "PASS"))
            print(f"  [ScoutForensics] {sym} → {status}  lp_lock={lp_fv.status}:{lp_fv.value}  asset_type={c['asset_type']}")

        killed  = sum(1 for c in coins if c.get("forensic_killed"))
        vetoed  = sum(1 for c in coins if c.get("forensic_vetoed") and not c.get("forensic_killed"))
        held    = sum(1 for c in coins if c.get("forensic_hold") and not c.get("forensic_vetoed"))
        passed  = len(coins) - killed - vetoed - held
        print(f"  [ScoutForensics] {len(coins)} checked — "
              f"{killed} KILLED  {vetoed} VETOED  {held} HOLD  {passed} PASS")
        return coins

    def summary_str(self, coins: List[Dict]) -> str:
        killed = [c for c in coins if c.get("forensic_killed")]
        vetoed = [c for c in coins if c.get("forensic_vetoed") and not c.get("forensic_killed")]
        held   = [c for c in coins if c.get("forensic_hold") and not c.get("forensic_vetoed")]
        parts  = []
        if killed:
            parts.append("KILLED: %s" % ", ".join(c["symbol"] for c in killed))
        if vetoed:
            tags = ["%s[%s]" % (c["symbol"],
                    "+".join(r.split(":")[0] for r in c.get("forensic_reasons", [])))
                    for c in vetoed]
            parts.append("ForensicVeto: %s" % ", ".join(tags))
        if held:
            parts.append("ForensicHold: %s (lp_lock unverified)" % ", ".join(c["symbol"] for c in held))
        return " | ".join(parts) if parts else "Forensics: clear"

    # ── Rules ─────────────────────────────────────────────────────────────────

    def _check_blacklist(self, c: Dict) -> bool:
        return c.get("symbol", "").upper() in FORENSIC_BLACKLIST

    def _classify_asset_type(self, c: Dict) -> None:
        chain = (c.get("holder", {}) or {}).get("chain", "").lower()
        evm   = {"ethereum", "base", "bsc", "polygon", "arbitrum", "optimism"}
        if chain in evm:
            surv = c.get("survival_score", 0)
            c["asset_type"] = ("INFRASTRUCTURE"
                               if surv >= 70 and c.get("on_binance") and c.get("on_bybit")
                               else "DEFI_TOKEN")
        elif chain == "":
            anti = c.get("antifragile", 0)
            age  = c.get("age_days", 0)
            c["asset_type"] = "MINING_POW" if (anti >= 40 and age >= 60) else "UNKNOWN"
        else:
            c["asset_type"] = "UNKNOWN"

    def _pool_depth(self, pairs: list) -> FieldValue:
        if not pairs:
            return FieldValue.missing("DexScreener")
        main = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
        usd  = float(main.get("liquidity", {}).get("usd", 0) or 0)
        if usd == 0:
            return FieldValue.missing("DexScreener")
        return FieldValue.measured(usd, "DexScreener")

    def _check_v4_hooks(self, pairs: list) -> FieldValue:
        v4 = [p for p in pairs if "v4" in p.get("dexId", "").lower()]
        if not v4:
            return FieldValue.missing("DexScreener")
        for p in v4:
            hook = p.get("hookAddress") or p.get("hook") or ""
            if hook and hook.lower() not in WHITELISTED_HOOKS:
                return FieldValue.measured(False, "DexScreener")
        return FieldValue.measured(True, "DexScreener")

    def _check_launch_cluster_proxy(self, c: Dict) -> FieldValue:
        holder = c.get("holder", {}) or {}
        if holder.get("status") == "HOLD_FOR_REVIEW":
            return FieldValue.missing("GoPlus")
        count   = holder.get("holder_count", 0)
        top10   = holder.get("top10_unlocked_pct", 0.0)
        age     = c.get("age_days", 999)
        single  = holder.get("max_single_pct", 0.0)
        if count <= 0:
            return FieldValue.missing("GoPlus")
        clustered = (count < 200 and top10 > 85.0 and age < 60 and single < 50.0)
        return FieldValue.measured(clustered, "GoPlus-proxy")

    def _fetch_dexscreener(self, symbol: str) -> Optional[list]:
        url = f"{DEXSCREENER_BASE_URL}/search?q={symbol}"
        try:
            r = self._session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            pairs = r.json().get("pairs") or []
            sym_u = symbol.upper()
            matched = [p for p in pairs
                       if p.get("baseToken", {}).get("symbol", "").upper() == sym_u]
            return matched or pairs[:5]
        except Exception as e:
            print(f"  [ScoutForensics] DexScreener error {symbol}: {e}")
            return None
