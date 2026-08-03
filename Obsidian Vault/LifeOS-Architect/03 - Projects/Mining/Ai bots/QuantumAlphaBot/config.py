"""
Coin Hunter Bot — Config
===========================
API keys + notification config.
"""
# ── Paper-trading mode ────────────────────────────────────────────────────────
# PAPER_MODE = True is the ONLY mode this codebase supports.
# Cycle output is logged to data/paper_ledger.jsonl — nothing is executed.
# To enable real orders: a separate, explicitly reviewed implementation is
# required. Setting PAPER_MODE = False only disables the ledger; it does NOT
# create an execution path (none exists in this codebase).
PAPER_MODE = True
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── LLM (Claude evaluation) ──────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Data sources (used by Coin Hunter scoring) ───────────────────────────────
CRYPTOQUANT_API  = os.getenv("CRYPTOQUANT_API",  "ogmfC4gzi0F3yJPCUVNJ3VfPhmkCHNIBCn1unrboNOlVOdf9Xx")   # exchange-flow (BTC/ETH only)
COINALYZE_API    = os.getenv("COINALYZE_API",    "bae6732b-a2da-4f6f-a7d3-1cfed8572d4f")   # OI + funding
LUNARCRUSH_API   = os.getenv("LUNARCRUSH_API",   "nab3su4ybmnj8o7fma5b4kj55mpealuh9w1l5f0a")   # social/galaxy

# ── Holder concentration (GoPlus Security — free tier, no key required) ─────
GOPLUS_API_KEY   = os.getenv("GOPLUS_API_KEY",   "")   # optional: increases rate limit

# ── Notifications ────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("QUANTUM_BOT_TOKEN",  "<REDACTED-TELEGRAM-TOKEN>")   # ربات اختصاصی QuantumAlphaBot
TELEGRAM_CHAT_ID = os.getenv("QUANTUM_CHAT_ID",    "6150431610")   # می‌تونه همون SENTINEL_CHAT_ID باشه
DISCORD_WEBHOOK  = os.getenv("DISCORD_WEBHOOK",    "")

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
