"""source_policy.py — tiering، استقلال منابع، و normalization.

پیاده‌سازی بند ۷ (سیاست منابع) و بند ۸ (نوآوری/استقلال).

قواعد کلیدی:
- چند صفحه از یک شرکت چند منبع مستقل نیستند (same registrable domain).
- چند مقالهٔ ارجاع‌دهنده به یک press release یک منبع محسوب می‌شوند (cluster origin).
- snippet موتور جست‌وجو شاهد نهایی نیست.
- ادعای مالی/رقابتی بدون منبع اولیه حداکثر فرضیه است.
"""

from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from .contracts import (
    CANDIDATE_TIERS,
    CONFIRMING_TIERS,
    REJECTED_TIERS,
    Source,
    TIER_A,
    TIER_B,
    TIER_C,
    TIER_D,
)

# ──────────────────────────────────────────────────────────────────────
# URL / domain normalization
# ──────────────────────────────────────────────────────────────────────
_WWW_RE = re.compile(r"^www\.", re.IGNORECASE)


def normalize_url(url: str) -> str:
    """نرمال‌سازی URL برای مقایسه: strip fragment، lowercase host، remove tracking."""
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url.strip()
    scheme = parts.scheme.lower() or "https"
    host = (parts.netloc or "").lower()
    host = _WWW_RE.sub("", host)
    # حذف port‌های پیش‌فرض
    if host.endswith(":80") and scheme == "http":
        host = host[:-3]
    elif host.endswith(":443") and scheme == "https":
        host = host[:-4]
    path = parts.path or ""
    # حذف slash انتهایی (جز root)
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    # حذف fragment (همیشه)
    # query را نگه می‌داریم ولی tracking params شناخته را پاک می‌کنیم
    query = _strip_tracking(parts.query)
    return urlunsplit((scheme, host, path, query, ""))


_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "ref_src", "source",
    "igshid", "si", "feature",
}


def _strip_tracking(query: str) -> str:
    if not query:
        return ""
    pairs = []
    for pair in query.split("&"):
        if not pair:
            continue
        key = pair.split("=", 1)[0].lower()
        if key in _TRACKING_PARAMS:
            continue
        pairs.append(pair)
    return "&".join(pairs)


def domain_of(url: str) -> str:
    """registrable domain تقریبی (host بدون www). برای تشخیص استقلال."""
    norm = normalize_url(url)
    if not norm:
        return ""
    host = urlsplit(norm).netloc.lower()
    host = _WWW_RE.sub("", host)
    return host


def registrable_domain(url: str) -> str:
    """آخرین دو/سه بخش دامنه برای تشخیص استقلال (ساده، بدون PSL کامل).

    مثلاً:
      sub.anthropic.com → anthropic.com
      blog.openai.com   → openai.com
      x.ai             → x.ai
      sakana.ai        → sakana.ai
      moonshot.cn      → moonshot.cn
    توجه: برای دامنه‌های country-code دو بخشی (co.uk) ساده است؛ چون منابع
    ما غالباً دامنه‌های اصلی شرکت‌ها هستند، این سطح کفایت می‌کند. برای موارد
    دو-سطحی شناخته‌شده اصلاح اضافه می‌شود.
    """
    dom = domain_of(url)
    if not dom:
        return ""
    parts = dom.split(".")
    if len(parts) <= 2:
        return dom
    # پسوندهای دو-سطحی شناخته‌شده
    two_level_suffixes = {"co.uk", "co.jp", "com.au", "co.kr", "com.cn", "co.in"}
    last_two = ".".join(parts[-2:])
    if last_two in two_level_suffixes and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


# ──────────────────────────────────────────────────────
# Tier classification
# ──────────────────────────────────────────────────────
# نقشهٔ دامنه → tier پیش‌فرض (primary‌های شرکت‌ها + مراجع معتبر)
_PRIMARY_DOMAINS = {
    # Tier A — official company domains
    "anthropic.com", "openai.com", "x.ai", "sakana.ai", "moonshot.cn",
    "kimi.com", "kimi.ai", "perplexity.ai", "deepmind.google", "ai.google",
    "google.com", "meta.com", "ai.meta.com", "microsoft.com", "github.com",
    "huggingface.co", "arxiv.org", "openreview.net", "nature.com", "science.org",
    "ieee.org", "acm.org", "apache.org",
    # government / official data
    "gov.au", "gov.uk", "europa.eu", "data.gov",
    # Tier A: benchmarks
    "artificialanalysis.ai",
}


_NEWS_DOMAINS = {
    # Tier B — reputable news/analysis
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com", "nytimes.com",
    "washingtonpost.com", "economist.com", "techcrunch.com", "theverge.com",
    "arstechnica.com", "wired.com", "venturebeat.com", "theinformation.com",
    "semianalysis.com", "stratechery.com", "platformer.news", "aisnakeoil.com",
    "technologyreview.com", "spectrum.ieee.org", "theregister.com",
    "financialreview.com.au", "abc.net.au", "smh.com.au", "theage.com.au",
    # reputable AI analysis/review blogs (Tier B)
    "bleap.finance", "digitalapplied.com", "lowcode.agency", "konabayev.com",
    "nexos.ai", "requesty.ai", "devops.com", "verdent.ai", "coursiv.io",
    "eesel.ai", "datanorth.ai", "alphamatch.ai", "aitoolsrecap.com",
    "mindstudio.ai", "dotzlaw.com", "benchlm.ai", "developersdigest.tech",
    "medium.com",
}


_WEAK_DOMAINS = {
    # Tier C — weak signal
    "reddit.com", "news.ycombinator.com", "ycombinator.com", "twitter.com",
    "x.com", "linkedin.com", "facebook.com", "discord.com", "medium.com",
    "substack.com", "youtube.com",
}


def classify_tier(source: Source | dict) -> str:
    """طبقه‌بندی tier یک منبع.

    اولویت:
      1. اگر source.tier صریح و معتبر باشد → همان.
      2. بر اساس registrable domain.
      3. در صورت نبود اطلاعات → D (unreliable) برای failsafe.
    """
    if isinstance(source, dict):
        tier = source.get("tier")
        url = source.get("url", "")
        title = source.get("title", "")
    else:
        tier = source.tier
        url = source.url
        title = source.title

    if tier in {TIER_A, TIER_B, TIER_C, TIER_D}:
        # اعتبارسنجی: اگر Tier A ادعا شده ولی دامنه‌ی نامعتبر، تنزل نمی‌دهیم
        # ولی is_primary را دوباره محاسبه می‌کنیم در confirm
        return tier

    reg = registrable_domain(url)
    if reg in _PRIMARY_DOMAINS:
        return TIER_A
    if reg in _NEWS_DOMAINS:
        return TIER_B
    if reg in _WEAK_DOMAINS:
        return TIER_C
    # paper/repo‌های شناخته‌شده
    low_title = title.lower()
    if any(k in low_title for k in ("official blog", "press release", "changelog", "pricing")):
        return TIER_A
    if any(k in low_title for k in ("research paper", "arxiv", "preprint")):
        return TIER_A
    # default: failsafe unreliable تا کشف بدون منبع معتبر سبز نشود
    return TIER_D


def is_confirming(source: Source | dict) -> bool:
    """آیا این منبع به‌تنهایی می‌تواند کشف را تأیید کند؟"""
    return classify_tier(source) in CONFIRMING_TIERS


def is_candidate_only(source: Source | dict) -> bool:
    return classify_tier(source) in CANDIDATE_TIERS


def is_rejected(source: Source | dict) -> bool:
    return classify_tier(source) in REJECTED_TIERS


# ──────────────────────────────────────────────────────
# Source independence (بند ۷ + تست‌های ۴ و ۴-bis)
# ──────────────────────────────────────────────────────
def are_independent(a: Source | dict, b: Source | dict) -> bool:
    """دو منبع مستقل‌اند اگر registrable domain متفاوت داشته باشند.

    چند صفحه از یک شرکت مستقل نیستند.
    """
    return registrable_domain(_url(a)) != registrable_domain(_url(b))


def count_independent(sources: Iterable[Source | dict]) -> int:
    """تعداد منابع مستقل = تعداد registrable domain‌های یکتای confirming."""
    domains = set()
    for s in sources:
        if not is_confirming(s):
            continue
        domains.add(registrable_domain(_url(s)))
    return len(domains)


def _url(s: Source | dict) -> str:
    if isinstance(s, dict):
        return s.get("url", "")
    return s.url


# ──────────────────────────────────────────────────────
# Cluster origin — چند منبع که به یک press release ارجاع می‌دهند
# ──────────────────────────────────────────────────────
def cluster_origins(sources: list[Source | dict]) -> list[list[int]]:
    """گروه‌بندی اندیس‌هایی که به یک مبدأ یکسان اشاره می‌کنند.

   启发 ساده: اگر دو منبع URL/عنوانِ یک press release یکسان را در snippet
    داشته باشند، یک خوشه می‌سازند. در عمل: تطبیق روی registrable domain +
    شباهت عنوان نرمال‌شده.
    """
    clusters: list[list[int]] = []
    used = [False] * len(sources)
    for i, si in enumerate(sources):
        if used[i]:
            continue
        cluster = [i]
        used[i] = True
        for j in range(i + 1, len(sources)):
            if used[j]:
                continue
            if _same_origin(si, sources[j]):
                cluster.append(j)
                used[j] = True
        clusters.append(cluster)
    return clusters


def _same_origin(a: Source | dict, b: Source | dict) -> bool:
    return registrable_domain(_url(a)) == registrable_domain(_url(b))


def effective_source_count(sources: list[Source | dict]) -> int:
    """تعداد مؤثر منابع = تعداد خوشه‌های مستقل confirming."""
    confirming = [s for s in sources if is_confirming(s)]
    if not confirming:
        return 0
    return len(cluster_origins(confirming))


# ──────────────────────────────────────────────────────
# Evidence sufficiency gate
# ──────────────────────────────────────────────────────
def evidence_sufficient(sources: list[Source | dict], min_independent: int = 2) -> dict:
    """آیا شواهد کافی است؟ بازگشت receipt."""
    confirming = [s for s in sources if is_confirming(s)]
    independent_count = count_independent(confirming)
    clusters = cluster_origins(confirming)
    receipt = {
        "total_sources": len(sources),
        "confirming_sources": len(confirming),
        "independent_confirming": independent_count,
        "cluster_count": len(clusters),
        "min_required": min_independent,
        "sufficient": independent_count >= min_independent,
        "note": "",
    }
    if independent_count < min_independent:
        receipt["note"] = (
            f"فقط {independent_count} منبع مستقل از حداقل {min_independent}. "
            "ادعا نهایی/atable نیست؛ باید فرضیه بماند."
        )
    return receipt


def requires_stronger_evidence(claim: str) -> bool:
    """ادعاهای مالی/رقابتی شاهد قوی‌تر می‌خواهند (بند ۷)."""
    low = (claim or "").lower()
    markers = (
        "revenue", "درآمد", "$", "aud", "usd", "market share", "سهم بازار",
        " valuation", "تولید", "revenue run-rate", "arr", "mrr",
        "best", "领先", "leading", "brترین", "بهترین", "fastest",
        "outperform", "شکست", "beat",
    )
    return any(m in low for m in markers)
