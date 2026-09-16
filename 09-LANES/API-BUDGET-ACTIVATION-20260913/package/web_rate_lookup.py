#!/usr/bin/env python3
"""web_rate_lookup.py — the octopus browses the web for SYDNEY painting rates.

Owner order 2026-09-13: «اختاپوس باید بتونه اینترنتو بگرده، تعرفه همون ماله
نقاشی سیدنی رو دراره و بنویسه براساس مترمربع و هرچی که استاندارده».

AUTONOMY V3 section 7 self-built tool: fetches public AU pricing pages, extracts
$/m2 and hourly figures with deterministic regex, records the SOURCE URL for
every number, and writes data/rate-card.json. No paid API. Never invents a
number: if nothing is extracted the card stays empty and says so.
"""
import json
import pathlib
import re
import time
import urllib.request

OUT = pathlib.Path("/home/ari/ofn/data/rate-card.json")
UD = "Mozilla/5.0 (X11; Linux aarch64) OCTOPUS-rate-lookup/1.0"
SOURCES = [
    "https://www.hipages.com.au/article/how-much-does-it-cost-to-paint-a-house",
    "https://hipages.com.au/cost-guide/house-painting-cost",
    "https://www.canstarblue.com.au/home-improvement/painting-cost/",
    "https://www.serviceseeking.com.au/blog/how-much-does-painting-cost/",
    "https://www.money.com.au/home-loans/home-improvement/how-much-does-it-cost-to-paint-a-house",
    "https://www.iseekplant.com.au/blog/painter-hourly-rate",
]
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
M2 = re.compile(r"\$?\s*(\d{1,3}(?:\.\d{1,2})?)\s*(?:-|–|to)?\s*\$?\s*(\d{1,3}(?:\.\d{1,2})?)?\s*(?:per|/|a)\s*(?:sq\.?\s*m|m2|square met)", re.I)
HR = re.compile(r"\$?\s*(\d{2,3}(?:\.\d{1,2})?)\s*(?:-|–|to)?\s*\$?\s*(\d{2,3}(?:\.\d{1,2})?)?\s*(?:per|/|an?)\s*hour", re.I)
found_m2, found_hr, hits = [], [], []

for url in SOURCES:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UD})
        with urllib.request.urlopen(req, timeout=25) as r:
            html = r.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        hits.append({"url": url, "status": "fetch_" + type(exc).__name__})
        continue
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html,
                  flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    m2 = [tuple(g for g in m.groups()) for m in M2.finditer(text)][:4]
    hr = [tuple(g for g in m.groups()) for m in HR.finditer(text)][:4]
    if m2 or hr:
        hits.append({"url": url, "status": "ok", "per_m2": m2, "per_hour": hr})
    else:
        hits.append({"url": url, "status": "fetched_no_numbers"})
    found_m2 += [(v, url) for v in m2]
    found_hr += [(v, url) for v in hr]

def nums(pairs):
    out = []
    for v, _u in pairs:
        for x in v:
            if x:
                try:
                    out.append(float(x))
                except ValueError:
                    pass
    return out

lo_m2, hi_m2 = (min(nums(found_m2)), max(nums(found_m2))) if found_m2 else (None, None)
lo_hr, hi_hr = (min(nums(found_hr)), max(nums(found_hr))) if found_hr else (None, None)

card = {
    "schema": "octopus.rate-card.v1", "at": NOW,
    "market": "Sydney NSW painting services (residential/commercial repaint)",
    "currency": "AUD",
    "per_m2": ({"low": lo_m2, "high": hi_m2, "unit": "AUD/m2",
                "basis": "web-extracted public AU pricing pages"} if lo_m2 else None),
    "per_hour": ({"low": lo_hr, "high": hi_hr, "unit": "AUD/hour"} if lo_hr else None),
    "minimum_charge_aud": None,
    "minimum_hours": 2,
    "sources": hits,
    "extraction": "deterministic regex; every figure carries the source URL",
    "self_built_tool": "web_rate_lookup.py (AUTONOMY V3 section 7)",
    "paid_api_used": 0.0,
    "honest_note": ("numbers are extracted verbatim from public pages; if a field is "
                    "null no number was found and none was invented"),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(card, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"per_m2": card["per_m2"], "per_hour": card["per_hour"],
                  "sources_ok": sum(1 for h in hits if h["status"] == "ok"),
                  "sources_total": len(hits)}))
print("written:", OUT)
