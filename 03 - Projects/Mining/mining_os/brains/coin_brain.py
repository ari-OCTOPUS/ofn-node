"""coin_brain.py — ⛏ خلاصهٔ فقط‌خواندنیِ کاندیدهای کوین (draft؛ بدونِ scrapeِ زنده)."""
from __future__ import annotations


def summarize_coins(coins: dict) -> dict:
    cands = coins.get("candidates", []) if isinstance(coins, dict) else []
    if not isinstance(cands, list):
        cands = []
    ranked = sorted(cands, key=lambda c: c.get("survival_score", 0), reverse=True)
    top = [{"symbol": c.get("symbol", "?"), "survival_score": c.get("survival_score", 0)}
           for c in ranked[:5]]
    return {"count": len(cands), "top": top}
