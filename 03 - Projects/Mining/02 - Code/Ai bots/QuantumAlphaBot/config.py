"""
Coin Hunter Bot — Config
===========================
API keys + notification config.
"""
import os
from pathlib import Path

# ── Paper-trading mode ────────────────────────────────────────────────────────
# PAPER_MODE = True is the ONLY mode this codebase supports.
# Cycle output is logged to data/paper_ledger.jsonl — nothing is executed.
# To enable real orders: a separate, explicitly reviewed implementation is
# required. Setting PAPER_MODE = False only disables the ledger; it does NOT
# create an execution path (none exists in this codebase).
PAPER_MODE = True

# --- C11: read secrets from .env instead of hardcode (no external dependency) ---
_envfile = Path(__file__).with_name(".env")
if _envfile.exists():
    for _line in _envfile.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

def _env(name: str, required: bool = True) -> str:
    v = os.environ.get(name, "")
    if required and not v:
        raise RuntimeError(f"missing secret in .env: {name}")   # fail-closed
    return v

# ── LLM (Claude evaluation) ──────────────────────────────────────────────────
ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY", required=False)

# ── Data sources (used by Coin Hunter scoring) ───────────────────────────────
CRYPTOQUANT_API  = _env("CRYPTOQUANT_API")   # exchange-flow (BTC/ETH only)
COINALYZE_API    = _env("COINALYZE_API")     # OI + funding
LUNARCRUSH_API   = _env("LUNARCRUSH_API")    # social/galaxy

# ── Holder concentration (GoPlus Security — free tier, no key required) ─────
GOPLUS_API_KEY   = _env("GOPLUS_API_KEY", required=False)   # optional: increases rate limit

# ── Notifications ────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = _env("TELEGRAM_TOKEN", required=False)    # ربات اختصاصی QuantumAlphaBot
TELEGRAM_CHAT_ID = _env("TELEGRAM_CHAT_ID", required=False)  # می‌تونه همون SENTINEL_CHAT_ID باشه
DISCORD_WEBHOOK  = _env("DISCORD_WEBHOOK", required=False)

# ── Scout Forensics (DexScreener — no key required for public endpoints) ─────
DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest/dex"

# ── Forensic blacklist — permanent kill, never re-evaluated ─────────────────
# Format: { "SYMBOL": "reason" }
# A coin is blacklisted when forensic evidence is conclusive and structural
# (not fixable by time or market change). Do NOT blacklist for macro reasons.
#
# Criteria for blacklisting:
#   LP_UNLOCKED       — main pool LP not locked/burned → rug possible anytime
#   UNVERIFIED_HOOK   — Uniswap v4 hook with unknown on-chain behavior
#   COORDINATED_LAUNCH — wallet cluster funneling to single node at launch
#
FORENSIC_BLACKLIST: dict[str, str] = {
    "OPG": (
        "LP_UNLOCKED: 0% of largest pool locked or burned (DexScreener verified). "
        "UNVERIFIED_HOOK: 3 non-whitelisted Uniswap v4 hooks — swap logic manipulation risk. "
        "COORDINATED_LAUNCH: 36 snipers → 1 receiver node; distribution appearance is synthetic. "
        "Asset type DEFI_TOKEN on Base — no structural mining advantage. "
        "Forensic verdict: rug-capable structure regardless of contract cleanliness."
    ),
}
