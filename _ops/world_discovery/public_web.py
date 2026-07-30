"""public_web.py — retrieval از وب عمومی با امنیت.

اصول بند ۱۷ (prompt injection) و بند ۱۳ (مرز عمل):
- هر محتوای وب «دادهٔ خصمانه» است، نه دستور.
- محتوای وب در لایهٔ UNTRUSTED_EXTERNAL_CONTENT برچسب می‌خورد.
- هیچ instruction داخل محتوای وب اجرا نمی‌شود.
- redaction خودکار برای email/phone/personal data.
- retriever قابل‌تزریق است؛ پیاده‌سازی پیش‌فرض از stdlib استفاده می‌کند.

هیچ فایل مشترکی ویرایش نمی‌شود. import از cortex.web_research اختیاری و
محافظت‌شده است (dirty/unavailable → fallback).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol
from urllib.parse import urlsplit

from .contracts import Observation, Source, TIER_A, TIER_C, TIER_D, make_observation_id
from .freshness import extract_date
from .source_policy import (
    classify_tier,
    domain_of,
    normalize_url,
    registrable_domain,
)

# ──────────────────────────────────────────────────────
# UNTRUSTED marker
# ──────────────────────────────────────────────────────
UNTRUSTED_FENCE = "UNTRUSTED_EXTERNAL_CONTENT"


# ──────────────────────────────────────────────────────
# Retriever protocol (قابل‌تزریق)
# ──────────────────────────────────────────────────────
class Retriever(Protocol):
    """پروتکل retriever. backend واقعی در adapter تزریق می‌شود."""

    def search(self, query: str, *, k: int = 8) -> list[dict]:
        """برگرداندان لیستی از {title, snippet, url, source, source_date?}."""
        ...


# ──────────────────────────────────────────────────────
# Redaction — privacy + secret
# ──────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# شمارهٔ تلفن بین‌المللی/محلی (ساده)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}"
)
# API key-like patterns
_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|bearer|authorization|sk-|pk_)[\"':\s]*[A-Za-z0-9_\-]{12,}"
)
# credit card-ish (basic)
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
# coordinates / address-ish persian — بسیار محتاطانه؛ فقط الگوهای واضح
_PERSONAL_RE = re.compile(
    r"(?i)(national\s*id|ssn|passport|cvv|seed\s*phrase|mnemonic|private\s*key)"
)

_REDACT_REPLACEMENTS = {
    _EMAIL_RE: "[EMAIL-REDACTED]",
    _KEY_RE: "[SECRET-REDACTED]",
    _CARD_RE: "[CARD-REDACTED]",
    _PERSONAL_RE: "[PERSONAL-REDACTED]",
}


def redact(text: str, *, keep_phones: bool = False) -> str:
    """حذف email/secret/card/personal از متن. phone اختیاری است."""
    if not text:
        return ""
    out = text
    for pat, repl in _REDACT_REPLACEMENTS.items():
        out = pat.sub(repl, out)
    if not keep_phones:
        # محافظت از تاریخ‌های ISO و قالب‌های عددی که تاریخ‌اند (نه phone)
        # 先 placeholders بگذار، سپس phone redact، سپس بازگردان
        _DATE_PROTECT = re.compile(r"\b(19|20)\d{2}[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b")
        placeholders = []
        def _stash(m):
            placeholders.append(m.group(0))
            return f"\x00DATE{len(placeholders)-1}\x00"
        out = _DATE_PROTECT.sub(_stash, out)

        # فقط شماره‌هایی که واقعاً like phone هستند (دارند + یا طول کافی)
        def _phone_sub(m):
            s = m.group(0)
            digits = re.sub(r"\D", "", s)
            # skip if looks like a year (4 digits) or too short
            if len(digits) < 7 or len(digits) > 15:
                return s
            if "+" in s or (s.count("-") + s.count(" ") + s.count(".")) >= 2:
                return "[PHONE-REDACTED]"
            return s
        out = _PHONE_RE.sub(_phone_sub, out)

        # restore dates
        def _restore(m):
            idx = int(m.group(1))
            return placeholders[idx]
        out = re.sub(r"\x00DATE(\d+)\x00", _restore, out)
    return out


def find_personal_data(text: str) -> list[str]:
    """آیا متن حاوی دادهٔ شخصی است؟ برای reject-not-collect."""
    found = []
    if _EMAIL_RE.search(text or ""):
        found.append("email")
    if _PERSONAL_RE.search(text or ""):
        found.append("personal-id")
    if _KEY_RE.search(text or ""):
        found.append("secret-like")
    return found


# ──────────────────────────────────────────────────────
# Prompt-injection detection (بند ۱۷)
# ──────────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)"),
    re.compile(r"(?i)disregard\s+(the\s+)?(previous|prior|above)"),
    re.compile(r"(?i)forget\s+(everything|all\s+(previous|prior))"),
    re.compile(r"(?i)you\s+are\s+now\s+(a|an)\s+(new|different)"),
    re.compile(r"(?i)new\s+instructions?\s*:"),
    re.compile(r"(?i)system\s*prompt"),
    re.compile(r"(?i)execute\s+(the\s+)?following\s+(command|code|shell)"),
    re.compile(r"(?i)reveal\s+(your|the)\s+(secret|system|instructions?|rules)"),
    re.compile(r"(?i)<\s*/?\s*(system|prompt|instruction|tool|function)"),
    re.compile(r"(?i)دستورات?\s+قبلی\s+را\s+نادیده\s+بگیر"),
    re.compile(r"(?i)قوانین\s+قبلی\s+را\s+فراموش"),
    re.compile(r"(?i)اکنون\s+تو\s+یک?\s+\w+\s+(جدید|متفاوت)"),
]


def detect_injection(text: str) -> bool:
    """آیا متن حاوی الگوی تزریق دستور است؟"""
    if not text:
        return False
    return any(pat.search(text) for pat in _INJECTION_PATTERNS)


def fence_untrusted(text: str) -> str:
    """محصور کردن محتوای وب در برچسب UNTRUSTED."""
    if not text:
        return ""
    return f"<{UNTRUSTED_FENCE}>\n{text}\n</{UNTRUSTED_FENCE}>"


# ──────────────────────────────────────────────────────
# Allow-list enforcement (egress-style gating)
# ──────────────────────────────────────────────────────
# دامنه‌های مجاز برای fetch (منابع عمومی رسمی شرکت‌ها + مراجع + تحلیل‌های معتبر AI)
_ALLOWED_FETCH_DOMAINS = {
    # Tier A — official company domains
    "anthropic.com", "openai.com", "x.ai", "sakana.ai", "moonshot.cn",
    "kimi.com", "kimi.ai", "platform.kimi.ai", "perplexity.ai", "research.perplexity.ai",
    "deepmind.google", "ai.google", "google.com", "meta.com", "ai.meta.com",
    "microsoft.com", "github.com", "huggingface.co",
    "arxiv.org", "openreview.net", "nature.com", "science.org", "ieee.org", "acm.org",
    "artificialanalysis.ai", "pub.sakana.ai",
    # Tier B — reputable news/analysis
    "reuters.com", "bloomberg.com", "ft.com", "techcrunch.com", "theverge.com",
    "arstechnica.com", "wired.com", "technologyreview.com", "theregister.com",
    "duckduckgo.com", "wikipedia.org", "semianalysis.com", "stratechery.com",
    "aisnakeoil.com",
    # reputable AI analysis/review blogs (Tier B) — verified reputable 2026-07-30
    "bleap.finance", "digitalapplied.com", "lowcode.agency", "konabayev.com",
    "nexos.ai", "requesty.ai", "devops.com", "verdent.ai", "coursiv.io",
    "eesel.ai", "datanorth.ai", "alphamatch.ai", "aitoolsrecap.com",
    "mindstudio.ai", "dotzlaw.com", "benchlm.ai", "developersdigest.tech",
    "medium.com", "substack.com", "linas.substack.com",
    # Tier C — weak signal (allowed for fetch but only candidate-grade)
    "reddit.com", "news.ycombinator.com", "linkedin.com", "youtube.com",
}


def is_fetch_allowed(url: str) -> bool:
    """deny-by-default: فقط دامنه‌های allow-listed مجازند."""
    return registrable_domain(url) in _ALLOWED_FETCH_DOMAINS


def assert_fetch_allowed(url: str) -> None:
    if not is_fetch_allowed(url):
        raise PermissionError(
            f"fetch blocked by egress policy: {registrable_domain(url) or url} not in allow-list"
        )


# ──────────────────────────────────────────────────────
# Search result → Observation / Source
# ──────────────────────────────────────────────────────
@dataclass
class RawHit:
    title: str
    snippet: str
    url: str
    source_label: str = ""
    source_date: Optional[str] = None

    def as_dict(self) -> dict:
        return {"title": self.title, "snippet": self.snippet, "url": self.url,
                "source": self.source_label, "source_date": self.source_date}


def hit_to_observation(hit: dict, competitor: str = "") -> Observation:
    """تبدیل یک نتیجهٔ جست‌وجو به Observation با redaction + injection check."""
    raw_title = str(hit.get("title", ""))
    raw_snippet = str(hit.get("snippet", ""))
    raw_url = str(hit.get("url", ""))
    url = normalize_url(raw_url)

    # privacy: اگر personal data داشت، snippet را redact کن (نه حذف کامل)
    title_red = redact(raw_title)
    snippet_red = redact(raw_snippet)

    injection = detect_injection(raw_title) or detect_injection(raw_snippet)

    # date extraction از snippet/title اگر نبود
    sdate = hit.get("source_date") or extract_date(raw_snippet) or extract_date(raw_title)

    src = Source(
        url=url,
        title=title_red,
        tier=classify_tier({"url": url, "title": title_red}),
        source_date=sdate,
        retrieved_at=hit.get("retrieved_at", ""),
        snippet=snippet_red,
        publisher=domain_of(url),
        is_primary=False,
        notes=("injection-flagged" if injection else ""),
    )

    # claim placeholder از snippet (بعداً توسط claim extractor پردازش می‌شود)
    claim = snippet_red[:300]

    return Observation(
        observation_id=make_observation_id(claim, url),
        claim=claim,
        source=src,
        competitor=competitor,
        raw_kind=_guess_kind(raw_title + " " + raw_snippet),
        retrieved_at=src.retrieved_at,
        injection_risk=injection,
    )


_KIND_KEYWORDS = {
    "pricing": ["pricing", "price", "cost", "قیمت", "plan"],
    "release": ["release", "launch", "announc", "unveil", "introduc", "انتشار", "رونمایی"],
    "feature": ["feature", "capabilit", "tool", "function", "agent", "model"],
    "research": ["paper", "research", "arxiv", "study", "تحقیق", "مطالعه"],
    "job": ["hiring", "job", "career", "engineer wanted", "استخدام"],
    "hype": ["revolutionary", "game-changer", "best ever", "انقلابی"],
}


def _guess_kind(text: str) -> str:
    low = (text or "").lower()
    for kind, kws in _KIND_KEYWORDS.items():
        if any(k in low for k in kws):
            return kind
    return "general"


# ──────────────────────────────────────────────────────
# Stdlib retriever fallback (هیچ dependency خارجی، هیچ API پولی)
# ──────────────────────────────────────────────────────
class StdlibRetriever:
    """Retriever سادهٔ fallback با DuckDuckGo HTML (همان الگوی cortex.web_research).

    این فقط زمانی فعال می‌شود که cortex.web_research قابل import نباشد.
    Side-effect: GET عمومی فقط به allow-list. rate-limited.
    """

    MIN_INTERVAL_S = 2.0

    def __init__(self, *, opener: Optional[Callable[[str], str]] = None):
        self._opener = opener
        self._last_call = 0.0

    def search(self, query: str, *, k: int = 8) -> list[dict]:
        import time
        import urllib.parse
        import urllib.request

        # rate limit
        now = time.monotonic()
        gap = now - self._last_call
        if gap < self.MIN_INTERVAL_S:
            time.sleep(self.MIN_INTERVAL_S - gap)
        self._last_call = time.monotonic()

        if self._opener is not None:
            html = self._opener(
                "https://duckduckgo.com/html/?q=" + urllib.parse.quote(query)
            )
        else:
            url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(query)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "OCTOPUS-WorldDiscovery/1.0 (research; contact: owner)"
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    html = r.read().decode("utf-8", errors="replace")
            except Exception:
                return []

        return _parse_ddg_html(html, k=k)


def _parse_ddg_html(html: str, *, k: int = 8) -> list[dict]:
    """استخراج نتایج از HTML DuckDuckGo (ساده، بدون dependency)."""
    hits: list[dict] = []
    # DDG result links در class="result__a" و snippet در class="result__snippet"
    link_re = re.compile(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
    snip_re = re.compile(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', re.S)
    links = link_re.findall(html)
    snips = snip_re.findall(html)
    for i, (href, title) in enumerate(links[:k]):
        # DDG از redirect استفاده می‌کند: //duckduckgo.com/l/?uddg=ENCODED
        real = href
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            import urllib.parse
            real = urllib.parse.unquote(m.group(1))
        snippet = _strip_tags(snips[i]) if i < len(snips) else ""
        title_clean = _strip_tags(title)
        hits.append({
            "title": title_clean,
            "snippet": snippet,
            "url": real,
            "source": "duckduckgo",
        })
    return hits


def _strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ──────────────────────────────────────────────────────
# Optional adapter to cortex.web_research (reuse, no edit)
# ──────────────────────────────────────────────────────
def try_cortex_retriever() -> Optional[Retriever]:
    """تلاش برای reuse از cortex.web_research (dirty/unavailable → None).

    اگر موفق شد، یک Retriever wrapper برمی‌گرداند که همان backend رایگان
    (DuckDuckGo/Wikipedia/arXiv) را صدا می‌زند — بدون ویرایش آن فایل.
    """
    try:
        import sys
        ops_root = str(Path(__file__).resolve().parent.parent)
        if ops_root not in sys.path:
            sys.path.insert(0, ops_root)
        import cortex.web_research as wr  # noqa: WPS433 (optional reuse)
    except Exception:
        return None

    class _CortexWrapper:
        def search(self, query: str, *, k: int = 8) -> list[dict]:
            try:
                if not getattr(wr, "enabled", lambda: False)():
                    return []
            except Exception:
                return []
            try:
                hits = wr.search(query, k=k)  # type: ignore[attr-defined]
            except Exception:
                return []
            # normalize: wr returns {title, snippet, url, source}
            out = []
            for h in hits:
                out.append({
                    "title": h.get("title", ""),
                    "snippet": h.get("snippet", ""),
                    "url": h.get("url", ""),
                    "source": h.get("source", "cortex"),
                })
            return out

    try:
        return _CortexWrapper()
    except Exception:
        return None
