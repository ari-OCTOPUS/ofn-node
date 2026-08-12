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


def _query_of(topic: str) -> str:
    """اسلاگِ داخلی → عبارتِ قابلِ جستجو.

    ۲۰۲۶-۰۷-۲۸ — چرا این تابع وجود دارد. موضوع‌ها از `school-awareness.json`
    می‌آیند که دو نگاشت دارد: `A08 → 0.1584` و `titles: A08 → "perception-bias"`.
    تا امروز آن رشته **دست‌نخورده** به جستجو می‌رفت، و نتیجه‌اش این بود:

      · دیروز خودِ شناسه رفت  → «A08»            → نتیجه: «A8» (یک بزرگراه)
      · امروز عنوان رفت       → «perception-bias» → نتیجه: «Perceptual hashing»

    هیچ‌کدام غلط‌گیری نمی‌شد چون هر دو **نتیجه برمی‌گرداندند** — فقط نتیجه‌ای که
    ربطی به موضوع نداشت. یک اسلاگِ خط‌تیره‌دار عبارتِ زبانِ طبیعی نیست؛ موتور
    نزدیک‌ترین چیزِ هم‌پیشوند را می‌دهد و آن را «چیزی که یاد گرفتم» می‌نامیدیم.

    برچسبِ اصلی در `topic` دست‌نخورده می‌ماند (خوراکِ improve/کارت)؛ فقط `query`
    نرمال می‌شود، و هر دو در رکورد ثبت می‌شوند تا قابلِ ممیزی باشد.
    """
    q = re.sub(r"[-_]+", " ", str(topic))
    return re.sub(r"\s+", " ", q).strip()


def _relevant(query: str, hits: list) -> list:
    """نتیجه‌ای که هیچ واژهٔ کوئری در عنوانش نیست، جوابِ این سؤال نیست.

    ۲۰۲۶-۰۷-۲۸، نیمهٔ دومِ فیکسِ صبح. نرمال‌سازیِ اسلاگ نقصِ **مکانیکی** را برد
    (`motivation` حالا درست تطبیق می‌دهد و `self narrative` صادقانه صفر می‌دهد)،
    ولی یکی ماند:

        query='perception bias'  →  «Perceptual hashing»

    فقط هم‌پیشوند است، نه هم‌موضوع. و چون شمارِ نتایج **غیرصفر** بود، هیچ گاردی
    صدایش را درنمی‌آورد و این «چیزی که یاد گرفتم» نامیده می‌شد. همان شکلِ شکست
    که کلِ امروز تکرار شد: خروجی‌ای که فرم دارد و محتوا ندارد.

    معیار عمداً **سخت‌گیرانه و ساده** است: دستِ‌کم یک واژهٔ ≥۴حرفیِ کوئری باید
    در عنوان باشد (یا برعکس). «perception»/«bias» هیچ‌کدام در «perceptual
    hashing» نیستند ⇒ رد. هوشمندتر از این (stemming، شباهتِ برداری) وسوسه‌انگیز
    است ولی نتیجه‌اش قابلِ توضیح نیست، و گاردی که نتوانی توضیحش بدهی دیر یا زود
    چیزِ درست را هم می‌خورد.

    ردکردن یعنی صفر نتیجه — و صفرِ صادق از یک جوابِ بی‌ربط بهتر است.
    """
    toks = [w for w in re.split(r"\W+", str(query or "").lower()) if len(w) >= 4]
    if not toks:
        return list(hits or [])          # کوئریِ کوتاه: چیزی برای سنجیدن نیست
    out = []
    for h in (hits or []):
        title = str((h or {}).get("title", "")).lower()
        if not title:
            continue
        # مرزِ واژه، نه زیررشته. تفاوتش را همان روز دیدم: «habit» زیررشتهٔ
        # «habituation» است و مقالهٔ بی‌ربط را نگه می‌داشت. با `\b` هر سه موردِ
        # واقعی درست می‌شوند: attention↔«Attention economy» می‌ماند،
        # habit↔«Habituation» و perception↔«Perceptual hashing» رد می‌شوند.
        if any(re.search(r"\b" + re.escape(w) + r"\b", title) for w in toks):
            out.append(h)
    return out


def research_topics(topics: list[str], *, per_topic: int = 3,
                    opener: Optional[Opener] = None) -> dict:
    """چند موضوعِ عمومی را تحقیق کن و یک دایجستِ ماندگار بساز.
    topics باید از قبل sanitize‌شده باشند (هیچ محتوای خصوصی)."""
    findings = []
    for t in topics[:6]:
        t = str(t).strip()
        if not t:
            continue
        # شناسهٔ خامِ داخلی هرگز به موتورِ جستجو نمی‌رود. ۰۷-۲۷ «A08» هفت بار رفت و
        # هفت بار «A8» (یک بزرگراه) برگشت — و هفت بار «چیزی که یاد گرفتم» نامیده شد.
        # ردکردنش یعنی سقوط به FALLBACK_TOPICS که عبارتِ واقعی‌اند: بدترین حالتش
        # موضوعِ عمومی است، نه نویزِ بی‌ربط که شبیهِ دانش لباس پوشیده.
        if re.fullmatch(r"[A-Za-z]{1,3}\d{1,4}", t):
            continue
        q = _query_of(t)
        hits = _relevant(q, search(q, k=per_topic, opener=opener))
        findings.append({"topic": t, "query": q, "n": len(hits),
                         "hits": hits[:per_topic]})
    digest = {"ts": opslib.now_iso(), "schema": "research-latest.v1",
              "n_topics": len(findings), "findings": findings, "cost_aud": 0}
    return digest


# موضوع‌های کنجکاویِ پیش‌فرض — تا وقتی گپِ مدرسه خالی است هم یادگیری بایستد نماند
# (رأی مالک «الان یادگیری نداره»). عمومی و بی‌خطر؛ نوبتی چرخانده می‌شوند.
FALLBACK_TOPICS = [
    "autonomous ai agents", "self-improving systems", "reinforcement learning",
    "vector memory databases", "multi-agent orchestration", "local llm inference",
    "prompt engineering", "knowledge graphs", "small business lead generation",
    "painting business marketing",
]


def fallback_topics(beat: int = 0, k: int = 3) -> list[str]:
    """k موضوعِ چرخانِ پیش‌فرض بر اساس beat (تنوع بدونِ Math.random)."""
    if not FALLBACK_TOPICS:
        return []
    start = (beat // 1) % len(FALLBACK_TOPICS)
    return [FALLBACK_TOPICS[(start + i) % len(FALLBACK_TOPICS)] for i in range(k)]


def run_and_persist(topics: list[str], *, opener: Optional[Opener] = None,
                    beat: int = 0) -> dict:
    """تحقیق + نوشتنِ اتمیک به state/pulse/research-latest.json (خوراکِ improve/کابین).
    اگر موضوعی نبود، از موضوع‌های کنجکاویِ پیش‌فرض استفاده می‌شود تا یادگیری همیشه زنده باشد."""
    if not enabled():
        return {"ok": False, "skipped": f"{FLAG_ENV} خاموش — هیچ egress"}
    topics = [t for t in (topics or []) if str(t).strip()] or fallback_topics(beat)
    digest = research_topics(topics, opener=opener)
    try:
        RESEARCH_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(RESEARCH_PATH) as lj:
            lj.write(digest)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    total = sum(f["n"] for f in digest["findings"])
    # کشف را دیدنی کن: یک جملهٔ سادهٔ فارسی برای خانه/نوتیف (بی‌محتوا).
    # اولین یافته‌ای که واقعاً نتیجه دارد (نه لزوماً findings[0]).
    try:
        sys.path.insert(0, str(_HERE))
        import discoveries
        top = next((f for f in digest["findings"] if f.get("hits")), None)
        if top:
            ttl = str(top["hits"][0].get("title", "")).strip()[:80]
            discoveries.record("research",
                               f"دربارهٔ «{top['topic']}» تحقیق کردم" +
                               (f" — «{ttl}»" if ttl else "") + f" ({total} نتیجه)")
    except Exception:  # noqa: BLE001 — ثبتِ کشف نباید تحقیق را بکشد
        pass
    # ۲۰۲۶-۰۸-۱۱ — ضدِ هدررفتن: digest هر tick overwrite می‌شود؛ ingest episodic + jsonl
    # provenance می‌سازد. صفر اختیار (may_authorize=False). fail-soft.
    ingest_summary = None
    try:
        mem_dir = str(_HERE.parent / "memory")
        if mem_dir not in sys.path:
            sys.path.insert(0, mem_dir)
        import research_ingest as _ri  # noqa: WPS433
        ingest_summary = _ri.ingest_digest(digest)
    except Exception:  # noqa: BLE001
        ingest_summary = {"ok": False, "skipped": "ingest-error"}
    out = {"ok": True, "n_topics": digest["n_topics"], "n_hits": total}
    if ingest_summary is not None:
        out["memory_ingest"] = ingest_summary
    return out
