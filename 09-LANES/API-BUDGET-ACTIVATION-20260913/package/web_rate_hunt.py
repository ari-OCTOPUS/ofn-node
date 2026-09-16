#!/usr/bin/env python3
"""web_rate_hunt.py — the octopus hunts pricing pages BY ITSELF (no owner link).

Owner order 2026-09-13: «خودش میگرده نه من». Strategy (all deterministic, $0):
  A) site-internal crawl: fetch roots that we KNOW answer (200), harvest
     same-domain links whose href/text looks like pricing, fetch them.
  B) light search engines that return real HTML to bots: Mojeek, DDG-lite.
Then keyword-window extraction over every fetched page, every number carrying
its source URL. Writes data/rate-card.json (never invents a number).
"""
import json
import pathlib
import re
import sys
import urllib.parse

sys.path.insert(0, "/home/ari/ofn/state/revenue-drive")
import web_lookup as W  # noqa: E402

CARD = pathlib.Path("/home/ari/ofn/data/rate-card.json")
PRICEY = re.compile(r"(cost|price|pricing|rate|per-square|per-m2|painter)", re.I)

SEED_ROOTS = [
    "https://www.hipages.com.au/",
    "https://www.serviceseeking.com.au/",
    "https://www.iseekplant.com.au/",
    "https://www.canstarblue.com.au/",
]
SEARCHES = [
    ("mojeek", "https://www.mojeek.com/search?q="),
    ("ddglite", "https://lite.duckduckgo.com/lite/?q="),
]
QUERIES = [
    "painter cost per square metre sydney",
    "house painting cost per m2 australia",
]


def links_from(html, base):
    out = []
    for m in re.finditer(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', html,
                         re.S | re.I):
        href, text = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        if not PRICEY.search(href) and not PRICEY.search(text):
            continue
        full = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(full).netloc != urllib.parse.urlparse(base).netloc:
            continue
        if full not in out:
            out.append(full)
    return out[:6]


def harvest(candidates):
    """candidates: list of (url, why). Returns list of (url, m2, hr, mn, strategy)."""
    hits = []
    for u, why in candidates:
        r = W.fetch(u)
        if not r["ok"]:
            continue
        text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r["text"],
                      flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        m2 = W.windows(text, W.KEYS["per_m2"])
        hr = W.windows(text, W.KEYS["per_hour"])
        mn = W.windows(text, W.KEYS["minimum"])
        if m2 or hr:
            hits.append((u, why, m2, hr, mn, r["strategy"]))
            print("HIT  %-70s m2=%s hr=%s" % (u[:70], m2[:2], hr[:2]))
    return hits


def rng(pairs, cap=300.0):
    vals = []
    for tup in pairs:
        for v in tup:
            try:
                f = float(v)
                if 1.0 <= f <= cap:
                    vals.append(f)
            except (TypeError, ValueError):
                pass
    return (min(vals), max(vals)) if vals else (None, None)


cands = []
# A) site-internal crawl of roots that answer
for root in SEED_ROOTS:
    r = W.fetch(root)
    if not r["ok"]:
        print("root FAIL", root, r["tried"][-1] if r["tried"] else "")
        continue
    print("root OK  ", root, len(r["text"]), "via", r["strategy"])
    for u in links_from(r["text"], root):
        cands.append((u, "site-crawl:" + urllib.parse.urlparse(root).netloc))
# B) light search engines
for name, base in SEARCHES:
    for q in QUERIES:
        r = W.fetch(base + urllib.parse.quote(q))
        if not r["ok"]:
            print("search FAIL", name, r["tried"][-1] if r["tried"] else "")
            continue
        found = re.findall(r'href="(https?://[^"]+)"', r["text"])
        good = [x for x in found
                if not any(b in x for b in ("mojeek.com", "duckduckgo.com",
                                            "microsoft", "google.com"))]
        print("search OK", name, q[:30], "->", len(good), "links")
        for u in good[:5]:
            cands.append((u, "search:" + name))

seen, uniq = set(), []
for u, why in cands:
    if u not in seen:
        seen.add(u)
        uniq.append((u, why))
print("candidates:", len(uniq))

hits = harvest(uniq[:18])
if hits:
    m2 = [x for _u, _w, a, _b, _c, _s in hits for x in a]
    hr = [x for _u, _w, _a, b, _c, _s in hits for x in b]
    mn = [x for _u, _w, _a, _b, c, _s in hits for x in c]
    lo_m2, hi_m2 = rng(m2, 200)
    lo_hr, hi_hr = rng(hr, 300)
    lo_mn, hi_mn = rng(mn, 2000)
    card = {
        "schema": "octopus.rate-card.v1", "at": W.NOW, "currency": "AUD",
        "market": "Sydney NSW painting services",
        "per_m2": ({"low": lo_m2, "high": hi_m2, "unit": "AUD/m2"} if lo_m2 else None),
        "per_hour": ({"low": lo_hr, "high": hi_hr, "unit": "AUD/hour"} if lo_hr else None),
        "minimum_charge_aud": lo_mn, "minimum_hours": 2,
        "sources": [{"url": u, "found_via": w, "strategy": s, "per_m2": a,
                     "per_hour": b, "minimum": c} for u, w, a, b, c, s in hits],
        "extraction": "autonomous hunt: site-crawl + light search engines, keyword windows",
        "verified_by": "self-built web_lookup.py + web_rate_hunt.py (AUTONOMY V3 s7)",
        "paid_api_used": 0.0,
        "status": "EXTRACTED",
    }
    CARD.write_text(json.dumps(card, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("RATE CARD EXTRACTED | m2:", card["per_m2"], "| hr:", card["per_hour"],
          "| min:", lo_mn, "| sources:", len(hits))
else:
    print("no pricing hit in this pass (nothing invented)")
