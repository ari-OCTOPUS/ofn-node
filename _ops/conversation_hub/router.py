# _ops/conversation_hub/router.py — deterministic intent router
# ADR-040 §route: No LLM for routing — purely keyword + pattern based.
#
# Priority order:
#   1. Explicit mode override (research/guide/propose) → direct, no matching
#   2. Keyword matching on text → route by highest-signal category
#   3. Fallback → "ask" (escalation: vault → brain → collab)
#
# confidence levels:
#   - evidenced: explicit mode (user chose research/guide/propose)
#   - derived:   keyword match with high-signal pattern or >= 2 hits
#   - inferred:  single keyword hit
#   - unknown:   no keyword matched (fallback)
from __future__ import annotations

from typing import Dict, List, Tuple

from .schemas import RouteDecision

# Keyword → route mapping.
# Each entry: (route, [keywords], high_signal_keywords)
# high_signal keywords score as 2 hits (prevents ambiguity with short words).
_ROUTE_TABLE: List[Tuple[str, List[str], List[str]]] = [
    ("runtime", [
        # Persian
        "وضعیت", "سیستم", "پالس", "چرخه", "هم‌آهنگی", "زنده",
        "پورت", "serv", "هزار",
        # English
        "status", "system", "pulse", "cycle", "coherence", "alive",
        "health", "uptime", "port",
    ], ["status", "وضعیت", "پالس", "pulse"]),

    ("mcp", [
        # Persian
        "فایل", "خط", "کد", "محتوا", "جستجو",
        # English
        "file", "line", "code", "content", "search", "grep",
        "find", "read", "adr", "commit",
    ], ["file", "فایل", "adr", "commit"]),

    ("memory", [
        # Persian
        "یادت", "حافظه", "به‌خاطر", "قبلاً",
        # English
        "remember", "memory", "recall", "previous",
    ], ["یادت", "remember"]),

    ("epistemic", [
        # Persian
        "آیا", "ثابت", "فرضیه", "ادعا", "شواهد", "آزمون",
        "اثبات", "falsif",
        # English
        "is it true", "prove", "hypothesis", "claim", "evidence",
        "testable", "falsif", "supported", "refuted",
    ], ["hypothesis", "فرضیه", "evidence", "شواهد"]),

    ("guide", [
        # Persian
        "تمرکز", "فوکوس", "بررسی", "دنبال کن",
        # English
        "focus", "investigate", "look into", "prioritize",
    ], ["تمرکز", "focus"]),

    ("propose", [
        # Persian
        "اصلاح", "رفع", "اضافه", "تست اضافه", "تغییر بده",
        # English
        "fix", "patch", "add test", "modify", "change",
        "create", "implement", "refactor",
    ], ["fix", "اصلاح", "patch"]),
]


def _match_keywords(text: str) -> List[Tuple[str, str, int]]:
    """Return (route, keyword, score) for each keyword hit in text."""
    text_lower = text.lower()
    hits = []
    for route, keywords, high_signal in _ROUTE_TABLE:
        for kw in keywords:
            if kw in text_lower:
                score = 2 if kw in high_signal else 1
                hits.append((route, kw, score))
    return hits


def classify_intent(text: str, mode: str = "auto") -> RouteDecision:
    """Classify user intent into a route.

    When mode is explicit (research/guide/propose), bypasses keyword matching
    and returns directly. For auto/ask, runs keyword scoring.
    """
    # --- Explicit mode override (highest priority) ---
    if mode == "research":
        return RouteDecision(
            route="epistemic",
            confidence="evidenced",
            reason="explicit mode=research → epistemic",
        )
    if mode == "guide":
        return RouteDecision(
            route="guide",
            confidence="evidenced",
            reason="explicit mode=guide → owner guidance",
        )
    if mode == "propose":
        return RouteDecision(
            route="propose",
            confidence="evidenced",
            reason="explicit mode=propose → proposal queue",
        )

    # --- Keyword matching for auto/ask ---
    hits = _match_keywords(text)
    if not hits:
        return RouteDecision(
            route="ask",
            confidence="unknown",
            reason="no keyword match → fallback ask (vault → brain → collab)",
        )

    # Score by route: sum scores per route
    scores: Dict[str, Tuple[int, List[str]]] = {}
    for route, kw, score in hits:
        if route not in scores:
            scores[route] = (0, [])
        s, kws = scores[route]
        scores[route] = (s + score, kws + [kw])

    # Best route by total score
    best_route = max(scores, key=lambda r: scores[r][0])
    best_score, best_keywords = scores[best_route]

    # Determine confidence level
    if best_score >= 3:
        confidence = "derived"
    else:
        confidence = "inferred"

    return RouteDecision(
        route=best_route,
        confidence=confidence,
        reason=f"keyword match: {best_route} (score={best_score})",
        keywords=best_keywords,
    )
