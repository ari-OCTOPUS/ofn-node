#!/usr/bin/env python3
"""web_research.py — تحقیقِ وبِ رایگانِ ($0) لایهٔ فراشناختی (جلسه ۴۶، رأی مالک:
«خودش تحقیق میکنه ... وب ... رایگان بدونِ API key»).

سه منبعِ رایگانِ بدونِ کلید — همه GETِ فقط‌خواندنی، صفر دلار، بیرونِ مسیرِ پول:
  * DuckDuckGo HTML (html.duckduckgo.com) — عنوان/چکیدهٔ نتایج
  * Wikipedia opensearch + REST summary — دانشِ عمومی
  * arXiv API (export.arxiv.org) — مقالهٔ علمی

اصولِ حاکمیتی:
  * صفر دلار، بیرونِ organ_gate/budget_gate (خرج نمی‌کند).
  * پشتِ `OCTOPUS_WIRE_WEB_RESEARCH` (owner-controllable) — خاموش = هیچ egress.
  * privacy: کوئری فقط از موضوع‌های عمومیِ گپِ مدرسه ساخته می‌شود؛ **هرگز**
    محتوای خصوصیِ vault/secret به وب نمی‌رود (فراخوان مسئولِ sanitize است).
  * injectable opener (تست بدونِ شبکه)؛ rate-limit + timeout + fail-soft.
  * stdlib-only (urllib, re, html) — هیچ وابستگیِ بیرونی.
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Callable, Optional

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

TIMEOUT_S = float(os.environ.get("WEB_RESEARCH_TIMEOUT_S", "12"))
MIN_INTERVAL_S = float(os.environ.get("WEB_RESEARCH_MIN_INTERVAL_S", "2"))
_UA = "Mozilla/5.0 (compatible; OctopusResearch/1.0; +local-organism)"
_LAST_CALL = [0.0]
FLAG_ENV = "OCTOPUS_WIRE_WEB_RESEARCH"

RESEARCH_PATH = opslib.STATE_DIR / "pulse" / "research-latest.json"

# Opener = تابعی که (url) → متنِ پاسخ. تزریق‌پذیر برای تست.
Opener = Callable[[str], str]


def enabled() -> bool:
    return os.environ.get(FLAG_ENV) == "1"


def _default_opener(url: str) -> str:
    """GETِ ساده با UA + timeout. فقط http/https. هیچ کلید/کوکی/POST."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http(s)")
    # rate-limit سراسری (ادب با منابعِ رایگان)
    dt = time.time() - _LAST_CALL[0]
    if dt < MIN_INTERVAL_S:
        time.sleep(MIN_INTERVAL_S - dt)
    _LAST_CALL[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310 — http(s) فقط
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def _clean(text: str) -> str:
    return _html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _ddg(query: str, k: int, opener: Opener) -> list[dict]:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    try:
        body = opener(url)
    except Exception:  # noqa: BLE001 — fail-soft
        return []
    out = []
    for m in re.finditer(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
        href, title = m.group(1), _clean(m.group(2))
        if title:
            out.append({"title": title[:200], "url": _html.unescape(href)[:400],
                        "snippet": "", "source": "duckduckgo"})
        if len(out) >= k:
            break
    # چکیده‌ها (اگر بود) به نتایج بچسبان
    snips = [_clean(s) for s in re.findall(r'result__snippet[^>]*>(.*?)</a>', body, re.S)]
    for i, s in enumerate(snips[:len(out)]):
        out[i]["snippet"] = s[:400]
    return out


def _wikipedia(query: str, opener: Opener) -> list[dict]:
    base = "https://en.wikipedia.org"
    try:
        os_url = (base + "/w/api.php?action=opensearch&limit=1&format=json&search="
                  + urllib.parse.quote(query))
        data = json.loads(opener(os_url))
        title = (data[1] or [None])[0] if isinstance(data, list) and len(data) > 1 else None
        if not title:
            return []
        sm_url = base + "/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
        sm = json.loads(opener(sm_url))
        extract = sm.get("extract") or ""
        if not extract:
            return []
        return [{"title": sm.get("title", title)[:200], "snippet": extract[:600],
                 "url": (sm.get("content_urls", {}).get("desktop", {}).get("page", "")),
                 "source": "wikipedia"}]
    except Exception:  # noqa: BLE001
        return []


def _arxiv(query: str, k: int, opener: Opener) -> list[dict]:
    url = ("http://export.arxiv.org/api/query?search_query=all:"
           + urllib.parse.quote(query) + f"&start=0&max_results={k}")
    try:
        body = opener(url)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", body, re.S):
        e = m.group(1)
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        s = re.search(r"<summary>(.*?)</summary>", e, re.S)
        link = re.search(r'<id>(.*?)</id>', e, re.S)
        if t:
            out.append({"title": _clean(t.group(1))[:200],
                        "snippet": (_clean(s.group(1))[:500] if s else ""),
                        "url": (_clean(link.group(1)) if link else ""),
                        "source": "arxiv"})
        if len(out) >= k:
            break
    return out


def search(query: str, k: int = 4, *, opener: Optional[Opener] = None,
           sources: tuple = ("wikipedia", "duckduckgo", "arxiv")) -> list[dict]:
    """کوئریِ عمومی را در منابعِ رایگان بگرد → لیستِ {title, snippet, url, source}.
    fail-soft: هر منبعِ خطادار خالی برمی‌گرداند. صفر دلار."""
    op = opener or _default_opener
    results: list[dict] = []
    if "wikipedia" in sources:
        results += _wikipedia(query, op)
    if "duckduckgo" in sources:
        results += _ddg(query, k, op)
    if "arxiv" in sources:
        results += _arxiv(query, k, op)
    return results


def research_topics(topics: list[str], *, per_topic: int = 3,
                    opener: Optional[Opener] = None) -> dict:
    """چند موضوعِ عمومی را تحقیق کن و یک دایجستِ ماندگار بساز.
    topics باید از قبل sanitize‌شده باشند (هیچ محتوای خصوصی)."""
    findings = []
    for t in topics[:6]:
        t = str(t).strip()
        if not t:
            continue
        hits = search(t, k=per_topic, opener=opener)
        findings.append({"topic": t, "n": len(hits), "hits": hits[:per_topic]})
    digest = {"ts": opslib.now_iso(), "schema": "research-latest.v1",
              "n_topics": len(findings), "findings": findings, "cost_aud": 0}
    return digest


def run_and_persist(topics: list[str], *, opener: Optional[Opener] = None) -> dict:
    """تحقیق + نوشتنِ اتمیک به state/pulse/research-latest.json (خوراکِ improve/کابین)."""
    if not enabled():
        return {"ok": False, "skipped": f"{FLAG_ENV} خاموش — هیچ egress"}
    digest = research_topics(topics, opener=opener)
    try:
        RESEARCH_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(RESEARCH_PATH) as lj:
            lj.write(digest)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    total = sum(f["n"] for f in digest["findings"])
    return {"ok": True, "n_topics": digest["n_topics"], "n_hits": total}
