#!/usr/bin/env python3
"""Follow-up to patch_compute_worker_test_shard.py: cross-field param validation.

The paired test caught it: shard_index=9 with shard_count=6 passed validate_task
(index is within its own 0..63 range) and only blew up at runtime. Envelope
validation must catch it — fail early, never dispatch work that cannot run.

R1  generic optional spec["cross_check"](params) hook in validate_task.
R2  test_shard cross-check: shard_index < shard_count -> SHARD_INDEX_GE_COUNT.
"""
import hashlib
import sys
from pathlib import Path

EXPECTED_PRE = "816de3511a6b1efd1019835b4283398b27990822fe2c2b02969ce0334495d6ce"

R1_OLD = '''    # An envelope that claims external effects is refused outright.
    if task.get("external_effects", 0) or task.get("customer_send", False):
        return False, "EXTERNAL_EFFECTS_REFUSED"
    return True, ""
'''
R1_NEW = '''    # Optional per-profile cross-field rules (e.g. shard_index < shard_count).
    cross = spec.get("cross_check")
    if cross:
        ok2, err2 = cross(params)
        if not ok2:
            return False, err2
    # An envelope that claims external effects is refused outright.
    if task.get("external_effects", 0) or task.get("customer_send", False):
        return False, "EXTERNAL_EFFECTS_REFUSED"
    return True, ""
'''

R2_OLD = '''def _work_test_shard(params: dict, ctx: dict) -> dict:
'''
R2_NEW = '''def _check_test_shard(params: dict) -> tuple[bool, str]:
    """Cross-field rule: a shard index must exist inside its shard count."""
    if int(params.get("shard_index", -1)) >= int(params.get("shard_count", 0)):
        return False, "SHARD_INDEX_GE_COUNT"
    return True, ""


def _work_test_shard(params: dict, ctx: dict) -> dict:
'''

R3_OLD = '''        "workload": _work_test_shard,
'''
R3_NEW = '''        "workload": _work_test_shard,
        "cross_check": _check_test_shard,
'''

REPLACEMENTS = [("R1 validate hook", R1_OLD, R1_NEW),
                ("R2 checker fn", R2_OLD, R2_NEW),
                ("R3 spec wiring", R3_OLD, R3_NEW)]


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
    print("PATCHED", len(REPLACEMENTS), "replacements ->", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
