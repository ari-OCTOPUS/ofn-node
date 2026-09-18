#!/usr/bin/env python3
"""Final resolver pass for WHY-SLOW-250 weak anchors.
Rules added on top of the previous mapper:
 - strip ANY trailing annotation: " (...)", " §...", " #..."
 - try the path plus common extensions (.md/.json/.jsonl/.txt, trailing slash)
 - parenthetical containing a 7-hex sha -> resolve the lane dir via git
 - parenthetical keywords -> case-insensitive glob over 09-LANES/ and 06-EVIDENCE/
 - "ls ..." / "systemctl ..." / "grep ..." -> runtime command anchor on 138
 - bare filenames -> filename map (extended)
Anything still unresolved is labelled honestly (never faked)."""
import glob as G
import json
import pathlib
import re
import subprocess

LANE = pathlib.Path("09-LANES/OCTOPUS-WHY-SLOW-250-20260918")
J = LANE / "WHY-SLOW-250.json"
RD = "138:state/revenue-drive/"

EXTRA_FILES = {
    "season-meter": RD + "season-meter.json",
    "owner-decisions": RD + "owner-decisions.jsonl",
    "budget_allows": "138:state/api-budget/api_budget.py (budget_allows)",
    "current-truth": "OCTOPUS/CURRENT-TRUTH.md",
    "agents.md": "AGENTS.md",
    "store-meter": RD + "season-meter.json",
    "outbound-effects": RD + "outbound-effects.sqlite3",
    "forgotten-list": None,   # resolved by glob below
}
KW_GLOBS = ["09-LANES/*{}*", "06-EVIDENCE/*{}*", "01 - Dashboard/*{}*", "00-SEASON/*{}*"]
COMMANDS = ("ls ", "grep ", "systemctl", "cat ", "find ", "python3 ")


def try_paths(p: str):
    cands = [p, p.rstrip("/") + "/"]
    for ext in (".md", ".json", ".jsonl", ".txt", ".py"):
        cands.append(p + ext)
    for c in cands:
        if pathlib.Path(c).exists():
            return c
    return None


def from_sha(sha: str):
    try:
        out = subprocess.run(["git", "show", "--name-only", "--format=", sha],
                             capture_output=True, text=True, timeout=30).stdout
        lanes = sorted({ln.split("/")[1] for ln in out.splitlines()
                        if ln.startswith("09-LANES/") and len(ln.split("/")) > 1})
        if lanes:
            return "09-LANES/%s/" % lanes[0]
    except Exception:  # noqa: BLE001
        pass
    return None


def resolve(a: str):
    raw = a.strip()
    # runtime command
    if raw.startswith(COMMANDS) or "budget_allows(" in raw:
        return ("138:" + raw if not raw.startswith("138:") else raw), "runtime"
    # split "#anchor" / "@ts" suffix
    m = re.match(r"^(.*?)(\s*[#@].*)$", raw)
    head, tail = (m.group(1), m.group(2)) if m else (raw, "")
    # strip parentheticals, §, (F-xxx)
    par = None
    mp = re.search(r"\(([^)]*)\)", head)
    if mp:
        par = mp.group(1)
        head = (head[:mp.start()] + head[mp.end():]).strip()
    head = head.split(" §")[0].split(" (")[0].strip().rstrip("،,").strip()
    # sha inside the parenthetical
    if par:
        sh = re.search(r"\b([0-9a-f]{7,40})\b", par)
        if sh:
            hit = from_sha(sh.group(1))
            if hit:
                return (hit + (" #" + par if par else "")), "file"
    if head:
        p = try_paths(head)
        if p:
            return (p + tail), "file"
        low = pathlib.Path(head).name.lower() or head.lower()
        if low in EXTRA_FILES and EXTRA_FILES[low]:
            return (EXTRA_FILES[low] + tail), "runtime"
        if head.startswith(("state/", "ofn/", "tools/", "tests/")):
            return ("138:" + head + tail), "runtime"
    # keyword glob (from the parenthetical first, then the head)
    for kw in ([par] if par else []) + ([head] if head else []):
        if not kw:
            continue
        words = [w for w in re.split(r"[^0-9A-Za-z\u0600-\u06FF]+", str(kw)) if len(w) > 3]
        for w in words[:3]:
            for pat in KW_GLOBS:
                hits = [h for h in G.glob(pat.format(w)) if pathlib.Path(h).exists()]
                if len(hits) == 1:
                    return (hits[0] + (" #" + str(par) if par else "")), "file"
    return raw, "weak"


d = json.loads(J.read_text(encoding="utf-8"))
fixed = 0
still = []
for r in d["entries"]:
    out = []
    for a in r["verify_against"]:
        na, q = resolve(a)
        if q != "weak" and na != a:
            fixed += 1
        out.append(na)
    r["verify_against"] = out


def strict_weak(r):
    for a in r["verify_against"]:
        core = re.split(r"\s*@|\s+::", a)[0].strip()
        core = re.sub(r"\s*\(.*\)$", "", core).strip()
        if core.startswith(("138:", "C:/")):
            continue
        if pathlib.Path(core).exists():
            continue
        if "/" in core and pathlib.Path(core.split(" (")[0]).exists():
            continue
        return True
    return False


weak = [(r["id"], r["verify_against"][0][:70]) for r in d["entries"] if strict_weak(r)]
for r in d["entries"]:
    r["anchor_quality"] = "carries-labelled-weakness" if strict_weak(r) else "resolvable"
d["anchor_stats_v6"] = {"resolvable": 250 - len(weak), "labelled_weak": len(weak),
                        "anchors_rewritten_this_pass": fixed,
                        "at": "2026-09-18T13:25:00Z"}
J.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("anchors rewritten:", fixed)
print("resolvable:", 250 - len(weak), "/250 | weak:", len(weak))
for w in weak[:14]:
    print("   ", w[0], w[1])
