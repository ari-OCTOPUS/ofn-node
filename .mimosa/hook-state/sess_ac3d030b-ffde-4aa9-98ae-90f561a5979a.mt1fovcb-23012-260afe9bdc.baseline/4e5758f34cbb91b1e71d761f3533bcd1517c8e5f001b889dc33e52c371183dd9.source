"""
brain/web_research.py — موتور جستجوی وبِ رایگان

منابع بدون API key:
  ۱. Wikipedia REST API — مقالات دایرة‌المعارف
  ۲. arXiv API — مقالات علمی AI/ML/شناختی
  ۳. DuckDuckGo HTML — جستجوی عمومی وب

هیچ کلیدی لازم نیست. همه‌چیز رایگان و بدون auth.
"""
from __future__ import annotations

import httpx
import time
import re
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

# خطاها قبلاً با print به stdout می‌رفتند و در outputs/system.log ثبت نمی‌شدند
logger = logging.getLogger(__name__)


_HEADERS = {
    "User-Agent": "IdeaYab/1.0 (autonomous-research@local; Python/httpx)"
}


@dataclass
class WebResult:
    """نتیجه‌ی یک جستجوی وب."""
    source: str           # "wikipedia" | "arxiv" | "duckduckgo"
    title: str
    snippet: str          # خلاصه‌ی کوتاه
    url: str
    content: str = ""     # متن کامل (اگه fetch شده)
    relevance: float = 0.5  # 0..1


def search_wikipedia(query: str, max_results: int = 3) -> list[WebResult]:
    """جستجو در Wikipedia."""
    results = []
    try:
        # Search API
        r = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
            },
            headers=_HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return results

        data = r.json()
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            # Clean HTML from snippet
            snippet_raw = item.get("snippet", "")
            snippet = BeautifulSoup(snippet_raw, "html.parser").get_text()

            # Get full summary via REST API
            content = ""
            try:
                s = httpx.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
                    headers=_HEADERS, timeout=10, follow_redirects=True,
                )
                if s.status_code == 200:
                    content = s.json().get("extract", "")
            except Exception:
                pass

            results.append(WebResult(
                source="wikipedia",
                title=title,
                snippet=snippet[:200],
                url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                content=content[:1500],
                relevance=0.7,
            ))
            time.sleep(0.3)  # polite

    except Exception as e:
        logger.warning("[wikipedia] error: %s", e)
    return results


def search_arxiv(query: str, max_results: int = 5) -> list[WebResult]:
    """جستجو در arXiv — مقالات علمی."""
    results = []
    try:
        r = httpx.get(
            "https://export.arxiv.org/api/query",
            params={
                "search_query": f"all:{query}",
                "max_results": max_results,
                "sortBy": "relevance",
            },
            timeout=20,
            follow_redirects=True,
        )
        if r.status_code != 200 or not r.text:
            return results

        # Parse Atom XML
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        root = ET.fromstring(r.text)

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            title_text = title.text.strip().replace("\n", " ") if title is not None else ""

            summary = entry.find("atom:summary", ns)
            summary_text = summary.text.strip().replace("\n", " ") if summary is not None else ""

            link = entry.find("atom:id", ns)
            url = link.text.strip() if link is not None else ""

            published = entry.find("atom:published", ns)
            year = published.text[:4] if published is not None else ""

            results.append(WebResult(
                source="arxiv",
                title=f"{title_text} ({year})",
                snippet=summary_text[:200],
                url=url,
                content=summary_text[:1500],
                relevance=0.9,  # peer-reviewed science
            ))

    except Exception as e:
        logger.warning("[arxiv] error: %s", e)
    return results


def search_duckduckgo(query: str, max_results: int = 5) -> list[WebResult]:
    """جستجوی عمومی در DuckDuckGo (HTML parsing)."""
    results = []
    try:
        r = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=_HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return results

        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", class_="result__a", limit=max_results):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            # DDG wraps URLs
            if "uddg=" in href:
                import urllib.parse
                href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])

            # Get snippet from sibling
            snippet = ""
            snip_div = a.find_parent("div", class_="result")
            if snip_div:
                s = snip_div.find("a", class_="result__snippet")
                if s:
                    snippet = s.get_text(strip=True)

            results.append(WebResult(
                source="duckduckgo",
                title=title,
                snippet=snippet[:200],
                url=href,
                content=snippet,
                relevance=0.5,
            ))

    except Exception as e:
        logger.warning("[duckduckgo] error: %s", e)
    return results


def fetch_url(url: str, max_chars: int = 3000) -> str:
    """دانلود و استخراج متن از یک URL."""
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        logger.warning("[fetch_url] error: %s", e)
        return ""


def multi_search(query: str, max_per_source: int = 3) -> list[WebResult]:
    """
    جستجوی همزمان در همه‌ی منابع.
    مرتب‌شده بر اساس relevance.
    """
    all_results = []

    # arXiv (highest relevance — science)
    all_results.extend(search_arxiv(query, max_per_source))

    # Wikipedia (conceptual grounding)
    all_results.extend(search_wikipedia(query, max_per_source))

    # DuckDuckGo (general web)
    all_results.extend(search_duckduckgo(query, max_per_source))

    # Deduplicate by title similarity
    seen = set()
    unique = []
    for r in all_results:
        key = r.title.lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # Sort by relevance
    unique.sort(key=lambda r: r.relevance, reverse=True)
    return unique


def synthesize_knowledge(query: str, results: list[WebResult]) -> str:
    """
    ترکیب نتایج جستجو به یک متنِ دانشِ فشرده.
    برای ورود به LLM.
    """
    lines = [f"# تحقیق: {query}", f"# {len(results)} منبع پیدا شد\n"]

    for i, r in enumerate(results, 1):
        lines.append(f"## [{i}] {r.source.upper()}: {r.title}")
        if r.content:
            lines.append(r.content[:800])
        elif r.snippet:
            lines.append(r.snippet)
        lines.append(f"🔗 {r.url}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Web Research Engine Test ===\n")

    query = "self-aware AI architecture metacognition"
    print(f"Query: {query}\n")

    results = multi_search(query, max_per_source=3)
    print(f"Found {len(results)} results:\n")

    for r in results:
        print(f"[{r.source:5s}] {r.title[:70]}")
        print(f"        {r.snippet[:100]}")
        print()

    print("\n=== Synthesized Knowledge ===\n")
    print(synthesize_knowledge(query, results)[:2000])
