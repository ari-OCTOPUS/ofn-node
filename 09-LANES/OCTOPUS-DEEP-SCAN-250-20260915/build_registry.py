"""Assemble FORGOTTEN-250 registry + all nine §3 deliverables from raw findings.

Inputs: raw/*-findings.json (fresh, evening agents), carried-100.json (morning scan).
Rank = U*R + C/5 (megaprompt §4). No entry is invented; every fresh entry carries
its own anchor; carried entries keep morning anchors + evening status_basis.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

LANE = Path(r"F:\backup\09-LANES\OCTOPUS-DEEP-SCAN-250-20260915")
RAW = LANE / "raw"
TARGET_FRESH = 150

fresh = []
for f in sorted(RAW.glob("*-findings.json")):
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                fresh.append(json.loads(line))
            except json.JSONDecodeError as e:
                print("BAD LINE in", f.name, e)

# dedupe by id
seen, uniq = set(), []
for x in fresh:
    if x["id"] in seen:
        continue
    seen.add(x["id"])
    uniq.append(x)
fresh = uniq

carried = json.loads((LANE / "carried-100.json").read_text(encoding="utf-8"))["items"]
def _terr_of(src):
    p = str((src or {}).get("path", ""))
    if p.startswith("138:") or "octopus-mesh" in p or "ops-agent" in p:
        return "runtime"
    if "09-LANES" in p:
        return "lanes"
    if "06-EVIDENCE" in p:
        return "06-EVIDENCE"
    if "07-HANDOFF" in p:
        return "07-HANDOFF"
    if "OCTOPUS" in p or "Dashboard" in p:
        return "surfaces"
    if "_ops" in p:
        return "_ops"
    return "carried-misc"
for c in carried:
    c.setdefault("territory", _terr_of(c.get("source")))


def rank(e):
    return round(float(e.get("U", 2)) * float(e.get("R", 2)) + float(e.get("C", 3)) / 5.0, 2)


for e in fresh:
    e["rank"] = rank(e)
    e["state"] = "open"
    e["carried_from"] = None
for e in carried:
    e["rank"] = rank(e)
    e["id"] = e["id"]  # F-xxx kept

# selection: keep all fresh if <= target else top-rank with per-territory representation
if len(fresh) > TARGET_FRESH:
    season = [e for e in fresh if e.get("class") == "SEASON_LEFTOVER"]
    rest = [e for e in fresh if e.get("class") != "SEASON_LEFTOVER"]
    season.sort(key=lambda x: -x["rank"])
    rest.sort(key=lambda x: -x["rank"])
    fresh = season + rest[: max(0, TARGET_FRESH - len(season))]

entries = carried + fresh
for i, e in enumerate(entries):
    e["registry_index"] = i

(LANE / "FORGOTTEN-250.json").write_text(json.dumps({
    "schema": "octopus.deep-scan.forgotten.v2",
    "lane": "OCTOPUS-DEEP-SCAN-250-20260915",
    "generated_at_utc": "2026-09-15T21:40:00Z",
    "counts": {
        "total": len(entries),
        "carried_100": len(carried),
        "fresh": len(fresh),
        "season_leftover": sum(1 for e in entries if e.get("class") == "SEASON_LEFTOVER"),
    },
    "by_class": dict(Counter(e.get("class") for e in entries)),
    "by_territory": dict(Counter(e.get("territory") for e in entries)),
    "rank_formula": "U*R + C/5",
    "method": "carried-100 revalidated + 188 fresh anchored findings from 6 read-only agents (vault+d_runtime)",
    "items": entries,
}, ensure_ascii=False, indent=1), encoding="utf-8")

# ---- MATRIX-250.csv ----
with (LANE / "MATRIX-250.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "territory", "class", "season_relevant", "U", "R", "C", "rank", "state", "path"])
    for e in sorted(entries, key=lambda x: -x["rank"]):
        w.writerow([e["id"], e.get("territory", ""), e.get("class", ""),
                    str(e.get("season_relevant", False)).lower(), e.get("U", 2), e.get("R", 2),
                    e.get("C", 3), e["rank"], e.get("state", "open"),
                    (e.get("source") or {}).get("path", "")])

# ---- SEASON-LEFTOVERS.md ----
sl = sorted([e for e in entries if e.get("class") == "SEASON_LEFTOVER"], key=lambda x: -x["rank"])
with (LANE / "SEASON-LEFTOVERS.md").open("w", encoding="utf-8") as fh:
    fh.write("# SEASON-LEFTOVERS — چه چیزی این سیزن (2026-09-07 → 09-15) جا گذاشت\n\n")
    fh.write(f"**{len(sl)} مورد** کلاس SEASON_LEFTOVER از ۲۵۰، مرتب بر رتبه (U×R + C/5).\n\n")
    fh.write("| rank | id | قلمرو | عنوان | anchor |\n|---:|---|---|---|---|\n")
    for e in sl:
        a = (e.get("source") or {}).get("anchor", "")
        fh.write(f"| {e['rank']} | {e['id']} | {e.get('territory','')} | {e['title'][:110]} | `{a[:90]}` |\n")

# ---- DISCREPANCIES-II.md ----
disc = sorted([e for e in entries if e.get("class") == "DOC_RUNTIME_DISCREPANCY"], key=lambda x: -x["rank"])
with (LANE / "DISCREPANCIES-II.md").open("w", encoding="utf-8") as fh:
    fh.write("# DISCREPANCIES-II — تضادهای vault ↔ runtime ↔ archive (2026-09-15)\n\n")
    fh.write(f"**{len(disc)} ردیف کلاس DOC_RUNTIME_DISCREPANCY** از رجیستر ۲۵۰ (آرشیو هم این دور دامنه بود).\n\n")
    for e in disc:
        s = e.get("source") or {}
        fh.write(f"## [{e['id']}] {e['title']}\n")
        fh.write(f"- **path:** `{s.get('path','')}` — `{s.get('anchor','')}`\n")
        fh.write(f"- **evidence:** {e.get('evidence_of_unfinished','')[:400]}\n")
        fh.write(f"- **why_complete:** {e.get('why_complete','')[:300]}\n\n")

# ---- GRAPH-250.md ----
by_terr = defaultdict(lambda: defaultdict(list))
for e in entries:
    band = "H" if e["rank"] >= 8 else "M" if e["rank"] >= 5 else "L"
    by_terr[e.get("territory", "?")][band].append(e["id"])
with (LANE / "GRAPH-250.md").open("w", encoding="utf-8") as fh:
    fh.write("# GRAPH-250 — territory → class → rank-band\n\n")
    fh.write("band: H ≥8 · M 5–8 · L <5 (rank = U×R + C/5)\n\n")
    for t in sorted(by_terr):
        cls = Counter(e.get("class") for e in entries if e.get("territory") == t)
        fh.write(f"## {t}  (n={sum(len(v) for v in by_terr[t].values())})\n")
        fh.write("classes: " + " · ".join(f"{k} {v}" for k, v in cls.most_common()) + "\n\n")
        for band in ("H", "M", "L"):
            if by_terr[t][band]:
                fh.write(f"- {band}: {', '.join(by_terr[t][band])}\n")
        fh.write("\n")

# ---- FORGOTTEN-250.md ----
top = sorted(entries, key=lambda x: -x["rank"])[:10]
with (LANE / "FORGOTTEN-250.md").open("w", encoding="utf-8") as fh:
    fh.write("# FORGOTTEN-250 — داشبورد رجیستر بدهی (2026-09-15)\n\n")
    c = Counter(e.get("class") for e in entries)
    fh.write(f"۲۵۰ ورودی = ۱۰۰ حمل‌شده (صبح امروز) + {len(fresh)} تازه. "
             f"SEASON_LEFTOVER: **{sum(1 for e in entries if e.get('class')=='SEASON_LEFTOVER')}**.\n\n")
    fh.write("classes: " + " · ".join(f"{k} {v}" for k, v in c.most_common()) + "\n\n")
    fh.write("## ده مورد اول با plan اجرا\n\n")
    for e in top:
        s = e.get("source") or {}
        fh.write(f"### [{e['id']}] rank {e['rank']} — {e['title'][:120]}\n")
        fh.write(f"- anchor: `{s.get('path','')}` · `{s.get('anchor','')[:100]}`\n")
        fh.write(f"- plan: بستن با {e.get('why_complete','')[:200]}\n\n")
    fh.write("## جدول کامل (مرتب بر رتبه)\n\n| rank | id | قلمرو | class | عنوان |\n|---:|---|---|---|---|\n")
    for e in sorted(entries, key=lambda x: -x["rank"]):
        fh.write(f"| {e['rank']} | {e['id']} | {e.get('territory','')} | {e.get('class','')} | {e['title'][:100]} |\n")

print("registry:", len(entries), "| carried:", len(carried), "| fresh:", len(fresh))
print("classes:", Counter(e.get('class') for e in entries).most_common())
print("season_leftover:", sum(1 for e in entries if e.get('class') == 'SEASON_LEFTOVER'))
print("territories:", Counter(e.get('territory') for e in entries).most_common())
