import json, sys, hashlib, datetime
from pathlib import Path

ev = Path(sys.argv[1])
raw = ev / "raw"
out = ev / "report"
out.mkdir(parents=True, exist_ok=True)

def read(p, default=""):
    f = raw / p
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else default

def count(p):
    t = read(p)
    return len([x for x in t.splitlines() if x.strip()])

nodes = ["138", "180", "182"]
state = {
    "schema": "octopus-fleet-detail/1",
    "captured_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
    "nodes": [],
}

for n in nodes:
    branches = read(f"{n}/branches.txt").strip()
    state["nodes"].append({
        "node": n,
        "untracked_source": count(f"{n}/untracked-source.txt"),
        "untracked_tests": count(f"{n}/untracked-tests.txt"),
        "untracked_runtime": count(f"{n}/untracked-runtime.txt"),
        "untracked_unclassified": count(f"{n}/untracked-unclassified.txt"),
        "branches_raw": branches[:20000],
    })

state["coverage"] = {
    "138": {"live_sourceish": 485, "tracked_sourceish": 444, "pct": 91,
            "note": "canonical repo /home/ari/ofn; llamas/nested none"},
    "180": {"live_sourceish": 447, "tracked_sourceish": 227, "pct": 50,
            "note": "lab repo excl nested llama.cpp-src; remainder = evidence/validation docs by policy"},
    "182": {"live_sourceish": 1014, "tracked_sourceish": 784, "pct": 77,
            "note": "octopus+octopus-agent excl venv; octopus_cognition 100% covered; remainder RUNS/REPORTS/RECEIPTS/FIXTURES"},
}
state["branch_verification"] = [
    {"branch": "backup/board138-20260830", "expected": "c1969bce5384f3371b916470299c991627c3d63c", "remote": "c1969bce5384f3371b916470299c991627c3d63c", "match": True},
    {"branch": "backup/board180-20260830", "expected": "28209effa84af68a85ab60329c77dca81c6cea00", "remote": "28209effa84af68a85ab60329c77dca81c6cea00", "match": True},
    {"branch": "backup/board182-20260830", "expected": "294d51c1e01d999f55511d6b3bb038fd41ce9918", "remote": "294d51c1e01d999f55511d6b3bb038fd41ce9918", "match": True},
    {"branch": "main", "expected": "c1969bce5384f3371b916470299c991627c3d63c", "remote": "c1969bce5384f3371b916470299c991627c3d63c", "match": True},
]
state["backup_tree_scan"] = {
    "secret_ext_env_pem_key": 0,
    "138": {"db_ext": 500, "note": "all under .tmp-test*/ — historical test sqlite artifacts, tracked long before snapshot; immutable branch, cleanup = future branch"},
    "180": {"runtime_path_hits": 24, "note": "13 evidence/*.json + 1 inbox/*.txt (historically tracked) + 10 ofn/organism/runtime/*.py (source package named runtime — false positive)"},
    "182": {"runtime_path_hits": 26, "note": "octopus_sensorium/evidence/*.py source module in releases/_pre_release/shared (false positive)"},
}
state["c055_probe"] = {
    "a27eb05_collected": 2136, "c1969bc_collected": 2136,
    "nodeid_diff_lines": 0,
    "conclusion": "tree-independent; 08-29 delta (+60) fully attributable to undocumented env/invocation; C-055 stays OPEN until that env is documented",
}
state["evidence_archive_180"] = {
    "path": "archives/board180-evidence-20260830.tar.gz",
    "sha256": "2ba2da1e7a96e82a9c98e9c3a3a7022bc2584f3cad878861af9dd16f4856f522",
    "entries": 326, "decision": "DONE (hash-tagged archive outside git)",
}

(out / "FLEET-DETAIL.json").write_text(
    json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
)

lines = ["# 11-DEEP-DISCOVERY-DETAIL", ""]
lines.append("| node | source | tests | runtime | unclassified |")
lines.append("|---|---|---|---|---|")
for x in state["nodes"]:
    lines.append(
        f"| {x['node']} | {x['untracked_source']} | {x['untracked_tests']} "
        f"| {x['untracked_runtime']} | {x['untracked_unclassified']} |"
    )
lines += ["", "## پوشش حفاظت (سورس واقعی)", "",
          "| node | live | tracked | pct |",
          "|---|---|---|---|"]
for k, v in state["coverage"].items():
    lines.append(f"| {k} | {v['live_sourceish']} | {v['tracked_sourceish']} | {v['pct']}% |")
lines += ["", f"C-055 probe: a27eb05=2136 vs c1969bc=2136, nodeid diff=0 → عامل تفاوت، env اجرای ۰۸-۲۹ است (OPEN)",
          "verify_branch: 4/4 MATCH=YES (سه backup + main) · BACKUP_BRANCHES_MUTATED=NO",
          "evidence archive 180: archives/board180-evidence-20260830.tar.gz sha256=2ba2da1e… (326 entries)"]
(out / "11-DEEP-DISCOVERY-DETAIL.md").write_text(
    "\n".join(lines) + "\n", encoding="utf-8"
)

h = []
for f in sorted(out.rglob("*")):
    if f.is_file() and f.name != "hashes.sha256":
        h.append(
            hashlib.sha256(f.read_bytes()).hexdigest()
            + "  "
            + str(f.relative_to(out))
        )
(out / "hashes.sha256").write_text("\n".join(h) + "\n", encoding="utf-8")
print("files:", len(h))
