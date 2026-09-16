#!/usr/bin/env python3
"""Repoint W3G30-COMBINED-001 dependency from superseded TRIO-001 to executed TRIO-003.

Self-gating: refuses to touch anything unless native-Z-SUCCESSOR-TRIO-003.json
is already in executed/ AND its expected post-hash is the live ops_agent.py
(the G22-satisfied state W3G30 was queued behind).
"""
import hashlib
import json
import time
from pathlib import Path

S = Path("/home/ari/ofn/state/ops-agent/state")
REQ = S / "canary-requests/native-W3G30-COMBINED-001.json"
TRIO_EXEC = S / "executed/native-Z-SUCCESSOR-TRIO-003.json"
LIVE_OPS = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

assert TRIO_EXEC.exists(), "TRIO-003 not executed yet — do not bump W3G30"
trio = json.loads(TRIO_EXEC.read_text())
want = trio.get("expected_post_sha256") or trio.get("target_sha256")
have = hashlib.sha256(LIVE_OPS.read_bytes()).hexdigest()
assert have == want, f"TRIO-003 post-hash not live: {have[:16]} != {str(want)[:16]}"

w = json.loads(REQ.read_text())
old_deps = list(w.get("dependencies") or [])
new_deps = [d for d in old_deps if "SUCCESSOR-TRIO" not in d]
new_deps.append("native-Z-SUCCESSOR-TRIO-003.json")
w["dependencies"] = new_deps
w["dependency_bump"] = {
    "at_utc": now,
    "from": old_deps,
    "to": new_deps,
    "why": "TRIO-001 superseded (dep file now in superseded-tasks/, unresolvable "
           "by G22); TRIO-003 executed+verified with its post-hash live",
}
REQ.write_text(json.dumps(w, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"W3G30 deps bumped at {now}: {old_deps} -> {new_deps}")
