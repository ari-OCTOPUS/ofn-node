"""Surgical TRIO-002 merge: TRIO artifact + the single retirefix hunk from live.

The only base->live change (109e68c0 -> c2e290fd) is the retire block becoming
conditional. TRIO kept the old block verbatim, so a targeted replacement is the
exact semantic merge. Also scans for control-byte corruption (the 0x08 lesson).
"""
import hashlib
import py_compile
import re
import shutil
import sys
from pathlib import Path

ART = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260915/ops_agent.py")

OLD = (
    '        # FIX 2026-09-14: retire the request right after submission so it cannot be\n'
    '        # re-executed. The witnessed outcome chain (OPS_B_OUTCOME_SENT/CYCLE_CLOSED)\n'
    '        # is the receipt; the executor must not run the same artifact again.\n'
    '        try:\n'
    '            os.replace(spool / name, STATE / "executed" / name)\n'
    '        except OSError:\n'
    '            receipt("EXECUTE_RETIRE_FAILED", category=category, request=name)\n'
    '        return _out\n'
)
NEW = (
    '        # FIX 2026-09-15: retire ONLY on successful execution. The 2026-09-14\n'
    '        # version retired unconditionally, which consumed G8 without deploying\n'
    '        # it (observed: proposal sent at 04:53Z, no OPS_B_EXECUTED, file moved\n'
    '        # to executed/, glass_runner stayed at the base hash).\n'
    '        if _out in ("ok", "executed", "witness-ok", "proposal-sent-ok"):\n'
    '            try:\n'
    '                os.replace(spool / name, STATE / "executed" / name)\n'
    '            except OSError:\n'
    '                receipt("EXECUTE_RETIRE_FAILED", category=category, request=name)\n'
    '        else:\n'
    '            receipt("EXECUTE_DEFERRED_NOT_RETIRED", category=category, request=name,\n'
    '                    witness_result=str(_out)[:60])\n'
    '        return _out\n'
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    art = ART.read_text()
    live = LIVE.read_text()

    assert sha(LIVE)[:16] == "c2e290fd96d42685", "live moved"
    assert art.count(OLD) == 1, f"old retire block count = {art.count(OLD)} (want 1)"
    assert live.count(NEW) == 1, "live does not contain the retirefix block verbatim"

    # control-byte scan on the artifact before merge (0x08 lesson)
    ctrl = [b for b in art.encode() if b < 0x20 and b not in (0x09, 0x0A, 0x0D)]
    if ctrl:
        print(f"ABORT: control bytes in artifact: {set(hex(b) for b in ctrl)}")
        return 1

    merged = art.replace(OLD, NEW)
    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_text(merged)
    py_compile.compile(str(STAGE), doraise=True)
    print("COMPILE_OK")

    text = STAGE.read_text()
    checks = {
        "retirefix_present": "EXECUTE_DEFERRED_NOT_RETIRED" in text,
        "old_block_gone": "right after submission so it cannot be" not in text,
        "trio_preconds": "preconditions_verified" in text,
        "trio_starvation_guard": "budget-blocked\" if _any_blocked" in text,
        "one_retirefix": text.count("EXECUTE_DEFERRED_NOT_RETIRED") == 1,
    }
    print("checks=", checks)
    if not all(checks.values()):
        print("ABORT: check failed")
        STAGE.unlink(missing_ok=True)
        return 2

    pi = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.c2e290fd96d42685.orig")
    if not pi.exists():
        shutil.copyfile(LIVE, pi)
        print("preimage_written")
    print("MERGE_OK new_sha=" + sha(STAGE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
