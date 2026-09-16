#!/usr/bin/env python3
"""W0 fenced restore test — runs as uid nobody in a fresh scratch root.
Re-extracts the LAPTOP-ROUNDTRIPPED bundle (true restore of the artifact),
verifies every file hash against the on-host manifest, py_compiles code,
and proves the negative probe (production write rejected)."""
import hashlib
import json
import os
import pathlib
import py_compile
import subprocess
import sys

BUNDLE = sys.argv[1]          # path to the roundtripped tar.gz
MANIFEST = sys.argv[2]        # path to manifest-pre.json (roundtripped)
SCRATCH = pathlib.Path(sys.argv[3])
EXPECT_HOST = sys.argv[4]

man = json.loads(pathlib.Path(MANIFEST).read_text(encoding="utf-8"))
assert man["host"] == EXPECT_HOST, "manifest host mismatch"
rst = SCRATCH / "restore"
rst.mkdir(parents=True, exist_ok=True)
subprocess.run(["tar", "-xzf", BUNDLE, "-C", str(rst)], check=True)

ok, fail, skipped = 0, [], []
for f in man["files"]:
    p = rst / "root" / f["path"].lstrip("/")
    if not p.exists():
        if "RESTORE_DEPENDENCY" in f.get("note", ""):
            skipped.append(f["path"])   # deliberately not bundled (hash-pinned)
            continue
        fail.append({"path": f["path"], "reason": "ABSENT in restore"})
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != f["sha256"]:
        fail.append({"path": f["path"], "reason": "HASH MISMATCH"})
    elif p.stat().st_size != f["size"]:
        fail.append({"path": f["path"], "reason": "SIZE MISMATCH"})
    else:
        ok += 1
    if "note" in f and "RESTORE_DEPENDENCY" in f.get("note", ""):
        skipped.append(f["path"])

compiled, cfail = 0, []
for py in (rst / "root").rglob("*.py"):
    try:
        py_compile.compile(str(py), cfile=str(SCRATCH / "c.pyc"),
                           doraise=True)
        compiled += 1
    except Exception as e:
        cfail.append({"file": str(py)[-60:], "err": type(e).__name__})

# negative probe: this process (nobody) must NOT write production
probe = "REJECTED"
try:
    pathlib.Path("/home/ari/ofn/state/ops-agent/state/zz-w0-probe").write_text("x")
    probe = "WRITTEN-FENCE-FAIL"
except OSError:
    pass

result = {
    "host": EXPECT_HOST,
    "bundle": pathlib.Path(BUNDLE).name,
    "files_in_manifest": len(man["files"]),
    "restored_and_hash_ok": ok,
    "failures": fail,
    "restore_dependencies_not_bundled": skipped,
    "py_compiled": compiled, "py_compile_failures": cfail,
    "negative_probe_production_write": probe,
    "verdict": "PASS" if (not fail and not cfail and probe == "REJECTED") else "FAIL",
}
pathlib.Path(SCRATCH / "restore-result.json").write_text(
    json.dumps(result, indent=1), encoding="utf-8")
print(json.dumps(result, indent=1)[:800])
sys.exit(0 if result["verdict"] == "PASS" else 1)
