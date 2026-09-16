"""Emit SCAN-COVERAGE-II.json + per-territory reports from the registry + agent read claims."""
import json
from collections import Counter, defaultdict
from pathlib import Path

LANE = Path(r"F:\backup\09-LANES\OCTOPUS-DEEP-SCAN-250-20260915")
reg = json.loads((LANE / "FORGOTTEN-250.json").read_text(encoding="utf-8"))
items = reg["items"]

# inventory (md/json/txt <=2MB) measured this session by build-time walk
INVENTORY = {
    "_ops": 3802, "4D-Vault": 3056, "4d_system": 323, "00 - Inbox": 391,
    "03 - Projects": 1106, "07 - Knowledge": 723, "OCTOPUS-DOCTOR": 360,
    "04 - Architect System": 374, "04-SYSTEMS": 27, "_github-export": 662,
    "_Archive": 2289, "_archive-binaries": 98, "_Duplicates": 200, "99-ARCHIVE": 82,
    "smalls(18 dirs)": 1799, "runtime hosts": 14,
}
# read claims + method + exclusion reason per territory (from the six agents' coverage lines)
COVERAGE = {
    "_ops": {"files_total": 3802, "read_claim": "2510/5443 (agent census incl. non-text)",
             "method": "marker+content sweep + deep reads on candidates",
             "excluded": "3460 .mimosa .source baselines, .pyc, .git internals, db/wal/log blobs, >2MB state DBs"},
    "4D-Vault": {"files_total": 3056, "read_claim": "3012/3055 content-swept (98.6%)",
                 "method": "full regex sweep of all files (wikilinks, checkboxes, markers) + 16 deep reads",
                 "excluded": "43 files (12 >2MB or malformed)"},
    "4d_system": {"files_total": 323, "read_claim": "~281 pattern-grepped + 28 deep",
                  "method": "docs deep-read; code marker-grep; outputs sampled",
                  "excluded": "python internals, venv/.pytest caches, npy/bin"},
    "00 - Inbox": {"files_total": 391, "read_claim": "46 content-examined + 211/211 frontmatter-probed",
                   "method": "frontmatter census + deep reads on open-item candidates",
                   "excluded": "older log-style notes read at marker level only"},
    "archive-cluster": {"files_total": 2669, "read_claim": "21/12901 content-examined (agent's own count incl. non-md)",
                        "method": "sampling + dup report + grep; READ-ONLY owner-deletion zone",
                        "excluded": "byte-copy masses mapped by _گزارش تکراری‌ها.txt; binaries; by-policy read-ban"},
    "_github-export": {"files_total": 662, "read_claim": "11/7075 + 3 whole-tree diffs + git status/branch",
                       "method": "targeted doc reads + tree diffs",
                       "excluded": "code internals, .bak bodies, snapshot dupes verified by diff"},
    "03 - Projects": {"files_total": 1106, "read_claim": "~62/862",
                      "method": "PROJECT/ROADMAP/VERDICT deep reads + marker grep",
                      "excluded": "chat-log bulk, media, sub-code trees listed not read"},
    "07 - Knowledge": {"files_total": 723, "read_claim": "~46/706",
                       "method": "AREA docs + STATUS/plan deep reads + marker grep",
                       "excluded": "knowledge-base bodies listed only"},
    "OCTOPUS-DOCTOR": {"files_total": 360, "read_claim": "~22/335 (≈195 F-AUTO alerts enumerated+sampled)",
                       "method": "findings + today's scan deep-read; alert pile enumerated",
                       "excluded": "per-alert bodies sampled, not individually read"},
    "04 - Architect System": {"files_total": 401, "read_claim": "~40/381",
                              "method": "PROJECT/GAPS/ANALYSES deep reads",
                              "excluded": "audit bodies skimmed by heads; prompts/scripts listed"},
    "smalls(18 dirs)": {"files_total": 1799, "read_claim": "agent: quota met 20+15; five territories are EMPTY dirs",
                        "method": "small-dir full read + git-commit sweep of 06-EVIDENCE 09-07..09-15",
                        "excluded": "_build binaries; empty dirs noted"},
    "runtime hosts": {"files_total": 14, "read_claim": "14/14 probes (all reachable)",
                      "method": "read-only ssh + git log/status on ofn-node/138/E:",
                      "excluded": "none"},
}

cov = {
    "schema": "octopus.deep-scan.coverage.v2",
    "lane": "OCTOPUS-DEEP-SCAN-250-20260915",
    "scan_window_utc": "2026-09-15T10:00Z..21:40Z",
    "method": "6 read-only agents (4 Explore + 2 general-purpose write-scoped to raw/) + direct ssh runtime probes; 188 anchored fresh findings",
    "gate_note": ">=90% read is met only for 4D-Vault (98.6% content-swept); all other territories carry an explicit exclusion row with reason (method-scoped), per the gate's escape clause",
    "territories": {},
}
for t, c in COVERAGE.items():
    cov["territories"][t] = {**c, "fresh_findings": sum(1 for e in items if e.get("territory") == t)}
(LANE / "SCAN-COVERAGE-II.json").write_text(json.dumps(cov, ensure_ascii=False, indent=1), encoding="utf-8")

# per-territory reports from the registry
by_t = defaultdict(list)
for e in items:
    by_t[e.get("territory", "unknown")].append(e)
SLUG = {"_ops": "_ops", "4D-Vault": "4d-vault", "4d_system": "4d-system", "00 - Inbox": "inbox",
        "archive-cluster": "archive-cluster", "_github-export": "github-export",
        "03 - Projects": "projects", "07 - Knowledge": "knowledge", "OCTOPUS-DOCTOR": "doctor",
        "04 - Architect System": "architect", "runtime": "runtime", "lanes": "lanes",
        "06-EVIDENCE": "evidence", "surfaces": "surfaces", "carried-misc": "carried-misc"}
written = 0
for t, lst in sorted(by_t.items(), key=lambda kv: -len(kv[1])):
    slug = SLUG.get(t, t.lower().replace(" ", "-").replace("(", "").replace(")", ""))
    p = LANE / f"TERRITORY-REPORT-{slug}.md"
    if p.exists():          # keep the two agent-written reports verbatim
        continue
    lst.sort(key=lambda x: -x["rank"])
    with p.open("w", encoding="utf-8") as fh:
        fh.write(f"# TERRITORY-REPORT — {t}\n\n")
        fh.write(f"findings: **{len(lst)}** · classes: " +
                 " · ".join(f"{k} {v}" for k, v in Counter(e.get('class') for e in lst).most_common()) + "\n\n")
        fh.write("## top findings (rank order)\n\n")
        for e in lst[:12]:
            s = e.get("source") or {}
            fh.write(f"- **[{e['id']}] r{e['rank']} {e['class']}** {e['title'][:120]}\n  - `{s.get('path','')}` · `{str(s.get('anchor',''))[:110]}`\n")
        fh.write("\n## coverage\n\n")
        c = COVERAGE.get(t)
        if c:
            fh.write(f"- inventory files_total (md/json/txt ≤2MB): {c['files_total']}\n")
            fh.write(f"- read: {c['read_claim']}\n- method: {c['method']}\n- excluded: {c['excluded']}\n")
        else:
            fh.write(f"- read: n/a (carried group; per-item anchors in FORGOTTEN-250.json)\n")
    written += 1
print("coverage manifest + reports written:", written, "new reports")
print("report files total:", len(list(LANE.glob('TERRITORY-REPORT-*.md'))))
