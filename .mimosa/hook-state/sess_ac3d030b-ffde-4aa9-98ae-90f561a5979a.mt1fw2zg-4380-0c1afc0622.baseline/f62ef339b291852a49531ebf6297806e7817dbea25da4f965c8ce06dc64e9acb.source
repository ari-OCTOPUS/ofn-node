"""
search_providers.py — لایه‌ی جست‌وجوی وب پشتِ یک رابطِ مشترک (مثلِ brain).

پیاده‌سازی‌ها: Brave، SerpAPI، Offline(بدونِ نتیجه). factory با fallbackِ امن.
از urllib (stdlib) استفاده می‌شود تا وابستگیِ جدید اضافه نشود.
خروجیِ search: list[dict] با کلیدهای title, url, snippet.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod

log = logging.getLogger("langar.search")


def _get_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


class BaseSearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, k: int = 5) -> list[dict]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class OfflineSearch(BaseSearchProvider):
    @property
    def name(self) -> str:
        return "offline"

    def is_available(self) -> bool:
        return True

    def search(self, query: str, k: int = 5) -> list[dict]:
        return []  # بدونِ شبکه نتیجه‌ای نیست؛ پژوهشگر این را شفاف اعلام می‌کند


class BraveSearch(BaseSearchProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "brave"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, k: int = 5) -> list[dict]:
        url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
            {"q": query, "count": k})
        data = _get_json(url, headers={"X-Subscription-Token": self.api_key,
                                       "Accept": "application/json"})
        out = []
        for r in (data.get("web", {}) or {}).get("results", [])[:k]:
            out.append({"title": r.get("title", ""), "url": r.get("url", ""),
                        "snippet": r.get("description", "")})
        return out


class SerpApiSearch(BaseSearchProvider):
    def __init__(self, api_key):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "serpapi"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, k: int = 5) -> list[dict]:
        url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(
            {"q": query, "api_key": self.api_key, "num": k})
        data = _get_json(url)
        out = []
        for r in (data.get("organic_results", []) or [])[:k]:
            out.append({"title": r.get("title", ""), "url": r.get("link", ""),
                        "snippet": r.get("snippet", "")})
        return out


def get_search_provider(config) -> BaseSearchProvider:
    choice = (getattr(config, "search_provider", "auto") or "auto").lower()
    brave = getattr(config, "brave_api_key", None)
    serp = getattr(config, "serpapi_key", None)
    if choice == "offline":
        return OfflineSearch()
    candidates = []
    if choice in ("auto", "brave") and brave:
        candidates.append(BraveSearch(brave))
    if choice in ("auto", "serpapi") and serp:
        candidates.append(SerpApiSearch(serp))
    for p in candidates:
        if p.is_available():
            log.info("search provider: %s", p.name)
            return p
    log.info("search provider: offline (fallback)")
    return OfflineSearch()
