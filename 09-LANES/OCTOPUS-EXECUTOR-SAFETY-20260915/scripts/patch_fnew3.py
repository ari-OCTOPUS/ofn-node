#!/usr/bin/env python3
"""Build the F-NEW-3 artifact on the post-TRIO live base (a255c4c0).

Owner ratified: deploy after TRIO lands (card 2026-09-15). Edit: every
OPS_B_BLOCKED emit gains a request= field so blockers join to the queue
without manual matching (the gap that hid TRIO-003's status from greps).
Four exact-string edits; each anchor must occur exactly once.
"""
import hashlib
import py_compile
import shutil
import sys
from pathlib import Path

LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = Path(
    "/home/ari/ofn/state/coding-worker/stage/EXECUTOR-SAFETY-FNEW3-20260915/ops_agent.py"
)
PREIMAGE = Path(
    "/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.a255c4c0deb380cd.orig"
)
EXPECTED_LIVE_SHA = (
    "a255c4c0deb380cdd6d2034671968c9737461798a4db4e857ea1122d9337ea51"
)

EDITS = [
    (
        'receipt("OPS_B_BLOCKED", category="B2", component=unit, reason=why_b)',
        'receipt("OPS_B_BLOCKED", category="B2", component=unit, request=unit, reason=why_b)',
    ),
    (
        'receipt("OPS_B_BLOCKED", category="B3", component="autonomy-supervisor", reason=why_b)',
        'receipt("OPS_B_BLOCKED", category="B3", component="autonomy-supervisor", '
        'request="autonomy-supervisor", reason=why_b)',
    ),
    (
        'receipt("OPS_B_BLOCKED", category="B5", component="storage-cache", reason=why_b)',
        'receipt("OPS_B_BLOCKED", category="B5", component="storage-cache", '
        'request="storage-cache", reason=why_b)',
    ),
    (
        'receipt("OPS_B_BLOCKED", category=category, component=component, reason=why_b)',
        'receipt("OPS_B_BLOCKED", category=category, component=component, '
        'request=name, reason=why_b)',
    ),
]


def main() -> int:
    live = LIVE.read_bytes()
    live_sha = hashlib.sha256(live).hexdigest()
    if live_sha != EXPECTED_LIVE_SHA:
        print(f"ABORT: live sha moved to {live_sha[:16]} — re-derive anchors")
        return 1
    text = live.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = text.count(old)
        if n != 1:
            print(f"ABORT: anchor E{i} count={n} (want 1)")
            return 2
        text = text.replace(old, new)
    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_text(text, encoding="utf-8", newline="\n")
    py_compile.compile(str(STAGE), doraise=True)
    lines = text.splitlines()
    emits = [l for l in lines if 'receipt("OPS_B_BLOCKED"' in l]
    checks = {
        "four_emits": len(emits) == 4,
        "all_carry_request": all("request=" in l for l in emits),
        "spool_uses_name": 'request=name, reason=why_b' in text,
        "no_crlf": b"\r" not in STAGE.read_bytes(),
    }
    print("checks:", checks)
    if not all(checks.values()):
        STAGE.unlink(missing_ok=True)
        return 3
    if not PREIMAGE.exists():
        PREIMAGE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LIVE, PREIMAGE)
        print("preimage_written")
    print("PATCH_OK new_sha=" + hashlib.sha256(STAGE.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
