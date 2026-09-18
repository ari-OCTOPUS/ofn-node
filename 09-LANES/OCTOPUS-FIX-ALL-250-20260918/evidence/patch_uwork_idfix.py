#!/usr/bin/env python3
"""Fix proposal id collision (hash-based) + purge acceptance-test artifacts
so no test card ever reaches the owner."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
PI = RD / "proposal_intake.py"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# --- 1. hash-based ids ---
shutil.copy2(PI, str(PI) + ".pre-uwork-idfix-" + TS)
h0 = sha(PI)
s = PI.read_text(encoding="utf-8")
old = ('    pid = prop.get("id") or ("PROP-%s-%03d" % (time.strftime("%Y%m%d"),\n'
       '                                               int(time.time()) % 1000))')
new = ('    _sig = hashlib.sha256(json.dumps([prop.get("title"), prop.get("why"),\n'
       '                                            prop.get("action")],\n'
       '                                           sort_keys=True, ensure_ascii=False)\n'
       '                               .encode("utf-8")).hexdigest()[:8]\n'
       '    pid = prop.get("id") or ("PROP-%s-%s" % (time.strftime("%Y%m%d"), _sig))')
assert s.count(old) == 1, "id anchor count=%d" % s.count(old)
s = s.replace(old, new)
s = s.replace("import json\nimport pathlib", "import hashlib\nimport json\nimport pathlib", 1)
PI.write_text(s, encoding="utf-8", newline="\n")
print("id fix:", h0[:16], "->", sha(PI)[:16])

# --- 2. purge test artifacts from the owner card queue + proposals ---
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
before = [i.get("id") for i in rv.get("items", [])]
rv["items"] = [i for i in rv.get("items", [])
               if not str(i.get("id", "")).startswith("PROP-")]
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
print("removed from owner queue:", [x for x in before if str(x).startswith("PROP-")])

pl = RD / "proposals.jsonl"
if pl.exists():
    rows = [json.loads(x) for x in pl.read_text(encoding="utf-8").splitlines() if x.strip()]
    kept = [r for r in rows if r.get("source") != "acceptance-test"]
    with pl.open("w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print("proposals kept:", len(kept), "removed:", len(rows) - len(kept))

json.dump({"schema": "octopus.fix-receipt.v1", "id": "UWORK-IDFIX-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "file": str(PI), "preimage": str(PI) + ".pre-uwork-idfix-" + TS,
           "sha_before": h0, "sha_after": sha(PI),
           "what": "proposal ids were second-granular and collided (all test proposals "
                   "got PROP-...-600); now content-hash based; acceptance-test artifacts "
                   "purged from the owner card queue so no test card ships",
           "rollback": "cp <preimage> <file>"},
          open("state/receipts/UWORK-IDFIX-%s.json" % TS, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("receipt written")
