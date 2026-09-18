#!/usr/bin/env python3
"""Follow-up #2 to patch_compute_worker_test_shard.py: clock-base fix.

Live failure 2026-09-18 (task-f09a28425d3e574c attempt 2): run_task builds
ctx["deadline_mono"] from time.time() (wall clock, despite the name). The
workload subtracted time.monotonic() from it, got ~1.8e9 s of "remaining"
budget, and subprocess raised OverflowError("timeout is too large") the
moment the run phase started (collect was capped at 90 s, which is why
collection succeeded and only the run phase died).

Fix: the workload keeps its own monotonic budget derived from
ctx["max_seconds"], independent of the caller's clock base.
"""
import hashlib
import sys
from pathlib import Path

EXPECTED_PRE = "ff7b542d7d7406ad28db8e39f6371f07aac9f773f4f05031d7dd19a1623cf135"

R1_OLD = '''    def remaining() -> float:
        return max(5.0, ctx["deadline_mono"] - time.monotonic())

    started = time.monotonic()
'''
R1_NEW = '''    # ctx["deadline_mono"] is wall-clock based in run_task (time.time despite
    # the name); derive our own monotonic budget from max_seconds instead —
    # feeding a wall-clock delta into subprocess timeouts raises OverflowError.
    budget_s = float(ctx.get("max_seconds", 120))
    started = time.monotonic()

    def remaining() -> float:
        return max(5.0, budget_s - (time.monotonic() - started))
'''

R2_OLD = 'AGENT_VERSION = "1.2.0-testshard"'
R2_NEW = 'AGENT_VERSION = "1.2.1-testshard-clockbase"'

REPLACEMENTS = [("R1 monotonic budget", R1_OLD, R1_NEW),
                ("R2 version", R2_OLD, R2_NEW)]


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else
                  "/home/ari/ofn/state/fleet-compute/compute_worker.py")
    pre = hashlib.sha256(target.read_bytes()).hexdigest()
    if pre != EXPECTED_PRE:
        print("PREIMAGE_MISMATCH", pre)
        return 2
    src = target.read_text(encoding="utf-8")
    for name, old, new in REPLACEMENTS:
        n = src.count(old)
        if n != 1:
            print(f"ABORT anchor {name} count={n}")
            return 3
        src = src.replace(old, new)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    print("PREIMAGE ", pre)
    print("POSTIMAGE", hashlib.sha256(target.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
