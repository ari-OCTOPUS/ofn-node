"""
source_quality.py — امتیازدهیِ کیفیتِ منابع (خالص و قطعی، بدونِ شبکه).

هر منبع بر اساسِ اعتبارِ دامنه، نوعِ شواهد، تازگی، ربط و ریسکِ سوگیری امتیاز می‌گیرد.
خروجی score در بازه‌ی 0..1. این جلوی «هم‌وزن‌دیدنِ یک بلاگ با meta-analysis» را می‌گیرد.
"""

from __future__ import annotations

import re
import urllib.parse

# اعتبارِ دامنه (۰..۵)
_HIGH = ("pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "arxiv.org", "nature.com",
         "sciencedirect.com", "cochrane.org", "who.int", "nih.gov", "cell.com",
         "thelancet.com", "nejm.org", "bmj.com", "jamanetwork.com", "crossref.org")
_MED = (".gov", ".edu", "wikipedia.org", "nasa.gov", "europa.eu", "oecd.org",
        ".org", "reuters.com", "apnews.com", "bbc.co", "ieee.org")
_LOW = ("medium.com", "reddit.com", "quora.com", "blogspot.", "wordpress.",
        "substack.com", "facebook.com", "twitter.com", "x.com", "pinterest.")

_STRONG_EVIDENCE = re.compile(
    r"(meta-?analysis|systematic review|randomi[sz]ed|rct|cochrane|فراتحلیل|کارآزمایی)", re.I)
_WEAK_EVIDENCE = re.compile(r"(opinion|blog|i think|به نظر من|تجربه شخصی|advert|sponsored)", re.I)
_COMMERCIAL = re.compile(r"(buy|shop|/product|coupon|discount|خرید|فروشگاه|تخفیف)", re.I)


def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""


def _authority(url: str) -> int:
    d = _domain(url)
    if any(h in d for h in _HIGH):
        return 5
    if any(m in d for m in _MED):
        return 3
    if any(low in d for low in _LOW):
        return 1
    return 2


def _relevance(query: str, text: str) -> int:
    q = {w for w in re.findall(r"\w+", (query or "").lower()) if len(w) > 2}
    if not q:
        return 3
    t = (text or "").lower()
    hits = sum(1 for w in q if w in t)
    frac = hits / len(q)
    return max(0, min(5, round(frac * 5)))


def score_source(url: str, title: str = "", snippet: str = "", query: str = "") -> dict:
    text = f"{title} {snippet}"
    authority = _authority(url)
    evidence = 5 if _STRONG_EVIDENCE.search(text) else (1 if _WEAK_EVIDENCE.search(text) else 3)
    relevance = _relevance(query, text)
    bias = -3 if _COMMERCIAL.search(text + " " + url) else 0
    # وزن‌دهی و نرمال‌سازی به 0..1 (بیشینه‌ی ممکن = 5+5+5 = 15)
    raw = authority + evidence + relevance + bias
    score = max(0.0, min(1.0, raw / 15.0))
    return {"score": round(score, 2), "authority": authority, "evidence": evidence,
            "relevance": relevance, "bias": bias}


def rank(results: list[dict], query: str = "") -> list[dict]:
    """به هر نتیجه فیلدِ _score اضافه و نزولی مرتب می‌کند."""
    scored = []
    for r in results:
        s = score_source(r.get("url", ""), r.get("title", ""), r.get("snippet", ""), query)
        rr = dict(r)
        rr["_score"] = s["score"]
        rr["_quality"] = s
        scored.append(rr)
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored


def uncertainty(ranked: list[dict]) -> dict:
    """تخمینِ عدم‌قطعیت از تعداد و پراکندگیِ کیفیتِ منابع."""
    if not ranked:
        return {"level": "high", "reason": "هیچ منبعی نیست"}
    scores = [r.get("_score", 0) for r in ranked]
    top = max(scores)
    n_good = sum(1 for s in scores if s >= 0.6)
    if top >= 0.7 and n_good >= 2:
        return {"level": "low", "reason": f"{n_good} منبعِ قوی هم‌سو"}
    if top >= 0.5:
        return {"level": "medium", "reason": "منابعِ متوسط؛ نیاز به آزمونِ شخصی"}
    return {"level": "high", "reason": "منابعِ ضعیف؛ با احتیاط"}
