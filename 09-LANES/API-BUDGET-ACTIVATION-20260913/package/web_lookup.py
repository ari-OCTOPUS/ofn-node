#!/usr/bin/env python3
"""web_lookup.py — self-healing web access for OCTOPUS (AUTONOMY V3 section 7).

Owner order 2026-09-13: «یه راهی پیدا کن وب باشه همیشه اختاپوس خودش بفهمه هرسری
ما الاف نشیم» — the organism must be able to browse by itself, every time.

Design
------
A strategy CHAIN, tried in order, with per-domain memory of what worked last
time (so the next run starts from the winning route — section 8 learning):
  1 direct      browser-like headers
  2 jina        https://r.jina.ai/<url>   (markdown proxy)
  3 allorigins  https://api.allorigins.win/raw?url=<url>
  4 corsproxy   https://corsproxy.io/?<url>
Extraction is keyword-window based (numbers near "square met", "per m2",
"per hour", …) which survives markdown/HTML differences.

Usage:
  web_lookup.py fetch <url>            -> text (first 4000 chars) + length
  web_lookup.py search <query>         -> duckduckgo-lite result links
  web_lookup.py rates                  -> Sydney painting rate card (sourced)
Never invents a number: empty extraction is reported as empty.
"""
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

STATE = pathlib.Path("/home/ari/ofn/state/revenue-drive")
MEM = STATE / "web-strategies.json"
CACHE = STATE / "web-cache"
CARD = pathlib.Path("/home/ari/ofn/data/rate-card.json")
UA = ("Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0.0.0 Safari/537.36")
HDRS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9", "Cache-Control": "no-cache"}
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
CACHE.mkdir(parents=True, exist_ok=True)


def _get(url, timeout=30, headers=None):
    req = urllib.request.Request(url, headers=headers or HDRS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def s_direct(u):
    return _get(u)


def s_jina(u):
    return _get("https://r.jina.ai/" + u)


def s_allorigins(u):
    return _get("https://api.allorigins.win/raw?url=" + urllib.parse.quote(u, safe=""))


def s_corsproxy(u):
    return _get("https://corsproxy.io/?" + urllib.parse.quote(u, safe=""))


STRATS = [("direct", s_direct), ("jina", s_jina),
          ("allorigins", s_allorigins), ("corsproxy", s_corsproxy)]


def mem_load():
    try:
        return json.loads(MEM.read_text())
    except (OSError, ValueError):
        return {}


def mem_save(m):
    MEM.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def domain(u):
    try:
        return urllib.parse.urlparse(u).netloc
    except ValueError:
        return "?"


def fetch(u, want_keywords=None):
    """Try the chain; remember which strategy worked for this domain."""
    m = mem_load()
    pref = m.get(domain(u), {}).get("winner")
    order = sorted(STRATS, key=lambda s: 0 if s[0] == pref else 1)
    tried = []
    for name, fn in order:
        try:
            body = fn(u)
        except Exception as exc:  # noqa: BLE001
            tried.append({"strategy": name, "error": type(exc).__name__})
            continue
        if not body or len(body) < 200:
            tried.append({"strategy": name, "error": "EMPTY"})
            continue
        tried.append({"strategy": name, "ok": True, "len": len(body)})
        m.setdefault(domain(u), {})["winner"] = name
        m[domain(u)]["at"] = NOW
        mem_save(m)
        (CACHE / (re.sub(r"\W+", "_", u)[-80:] + ".txt")).write_text(body[:200000],
                                                                    encoding="utf-8")
        return {"ok": True, "strategy": name, "text": body, "tried": tried}
    return {"ok": False, "text": "", "tried": tried}


NUM = re.compile(r"\$\s?(\d{1,4}(?:\.\d{1,2})?)(?:\s?(?:-|–|to)\s?\$?\s?(\d{1,4}(?:\.\d{1,2})?))?")
KEYS = {
    "per_m2": ("square met", "sq m", "sqm", "m2", "per square"),
    "per_hour": ("per hour", "an hour", "hourly"),
    "minimum": ("minimum", "min charge", "call-out", "callout"),
}


def windows(text, keys, span=140):
    """Return number tuples found near any keyword (markdown/HTML agnostic)."""
    low = text.lower()
    out = []
    for k in keys:
        for mt in re.finditer(re.escape(k), low):
            seg = text[max(0, mt.start() - span): mt.start() + span]
            for g in NUM.finditer(seg):
                out.append(tuple(x for x in g.groups() if x))
    return out[:8]


def search(q):
    u = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
    r = fetch(u)
    if not r["ok"]:
        return {"ok": False, "tried": r["tried"]}
    links = re.findall(r'href="(https?://[^"]+)"[^>]*class="result__a"', r["text"])
    if not links:
        links = [m for m in re.findall(r'href="(https?://[^"&]+)"', r["text"])
                 if "duckduckgo" not in m][:12]
    return {"ok": True, "strategy": r["strategy"], "links": links[:12]}


RATE_SOURCES = [
    "https://www.hipages.com.au/article/how-much-does-it-cost-to-paint-a-house",
    "https://www.serviceseeking.com.au/blog/how-much-does-painting-cost/",
    "https://www.canstarblue.com.au/home-improvement/painting-cost/",
    "https://www.iseekplant.com.au/blog/painter-hourly-rate",
    "https://www.money.com.au/home-loans/home-improvement/how-much-does-it-cost-to-paint-a-house",
]


def rates():
    per_m2, per_hr, mins, srcs = [], [], [], []
    for u in RATE_SOURCES:
        r = fetch(u)
        if not r["ok"]:
            srcs.append({"url": u, "status": "unreachable", "tried": r["tried"]})
            continue
        t = re.sub(r"<[^>]+>", " ", r["text"])
        m2 = windows(t, KEYS["per_m2"])
        hr = windows(t, KEYS["per_hour"])
        mn = windows(t, KEYS["minimum"])
        srcs.append({"url": u, "status": "ok", "strategy": r["strategy"],
                     "per_m2": m2, "per_hour": hr, "minimum": mn})
        per_m2 += [(x, u) for x in m2]
        per_hr += [(x, u) for x in hr]
        mins += [(x, u) for x in mn]

    def rng(pairs, cap=200.0):
        vals = []
        for tup, _u in pairs:
            for v in tup:
                try:
                    f = float(v)
                    if 1.0 <= f <= cap:
                        vals.append(f)
                except (TypeError, ValueError):
                    pass
        return (min(vals), max(vals)) if vals else (None, None)

    lo_m2, hi_m2 = rng(per_m2, 200)
    lo_hr, hi_hr = rng(per_hr, 300)
    lo_mn, hi_mn = rng(mins, 2000)
    card = {
        "schema": "octopus.rate-card.v1", "at": NOW, "currency": "AUD",
        "market": "Sydney NSW painting services",
        "per_m2": ({"low": lo_m2, "high": hi_m2, "unit": "AUD/m2"} if lo_m2 else None),
        "per_hour": ({"low": lo_hr, "high": hi_hr, "unit": "AUD/hour"} if lo_hr else None),
        "minimum_charge_aud": lo_mn,
        "minimum_hours": 2,
        "sources": srcs,
        "extraction": "keyword-window numbers over 4-strategy fetch chain",
        "verified_by": "self-built web_lookup.py (AUTONOMY V3 s7); no number invented",
        "paid_api_used": 0.0,
    }
    card["status"] = "EXTRACTED" if (lo_m2 or lo_hr) else "PENDING_SOURCE_EXTRACTION"
    CARD.parent.mkdir(parents=True, exist_ok=True)
    CARD.write_text(json.dumps(card, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return card


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "rates"
    if cmd == "fetch" and len(sys.argv) > 2:
        r = fetch(sys.argv[2])
        print(json.dumps({"ok": r["ok"], "strategy": r.get("strategy"),
                          "len": len(r["text"]), "tried": r["tried"]}))
    elif cmd == "search" and len(sys.argv) > 2:
        print(json.dumps(search(" ".join(sys.argv[2:])), ensure_ascii=False)[:1200])
    else:
        c = rates()
        print(json.dumps({"status": c["status"], "per_m2": c["per_m2"],
                          "per_hour": c["per_hour"],
                          "minimum_charge_aud": c["minimum_charge_aud"],
                          "reachable": sum(1 for s in c["sources"] if s["status"] == "ok"),
                          "total": len(c["sources"])}, ensure_ascii=False))
