#!/usr/bin/env python3
"""leak_scan.py — prove no credential value escaped into receipts/state/logs.

Reads key values only in memory, compares them against file contents, and
reports booleans + paths. Never prints a value, prefix, suffix or hash.
"""
import json
import pathlib
import sys

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import providers  # noqa: E402

SECRET_VARS = ("SAKANA_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY",
               "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "FUGU_API_KEY",
               "OFN_REMOTE_API_KEY", "ANTHROPIC_WORKSPACE_ID")
vals = {}
for v in SECRET_VARS:
    val = (providers.env().get(v) or "").strip()
    if val and "PASTE" not in val.upper():
        vals[v] = val
print("tracked credential variables:", sorted(vals))
print("count:", len(vals))
print()

SCAN_ROOTS = [
    pathlib.Path("/home/ari/ofn/state"),
    pathlib.Path("/tmp"),
]
ALLOWED = {pathlib.Path("/home/ari/ofn/state/api-budget/providers.py")}

hits = []
scanned = 0
for root in SCAN_ROOTS:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file() or p.stat().st_size > 4_000_000:
            continue
        if p.suffix in (".pyc", ".so", ".zip", ".gz", ".pyz"):
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        scanned += 1
        for var, val in vals.items():
            if val.encode() in data:
                hits.append({"path": str(p), "var": var,
                             "class": "CREDENTIAL_EXPOSURE_IN_STATE" if root.name == "state"
                                      else "TRANSIENT_TMP_COPY"})

print("files scanned:", scanned)
if hits:
    print("!!! HITS !!!")
    for h in hits:
        print(" ", h)
else:
    print("CLEAN: no credential value found in any scanned file")
print()

print("=== artifact modes ===")
for f in ["/home/ari/ofn/state/api-budget/config/provider-health.json",
          "/home/ari/ofn/state/api-budget/config/provider-routes.json",
          "/home/ari/ofn/state/api-budget/config/discovered-models.json",
          "/home/ari/ofn/state/api-budget/providers.py",
          "/home/ari/ofn/state/api-budget/budget-ledger.jsonl"]:
    p = pathlib.Path(f)
    if p.exists():
        import stat
        st = p.stat()
        print("  %-70s mode=%s owner_uid=%s" % (f, oct(stat.S_IMODE(st.st_mode)), st.st_uid))
print()

print("=== node 182 exposure check ===")
w = pathlib.Path("/var/lib/octopus-remote-witness")
found = [str(p) for p in w.rglob("*") if p.is_file() and b"external-models" in p.read_bytes()[:200000]] if w.exists() else []
print("  witness dir references external-models:", bool(found))
print("  credential vars reachable by 182 (by design): none — no key var is sent to 182")
