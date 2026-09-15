"""Three-way rebase: ART_V3 = LIVE + (ART_V2 - PRE).

Verifies G8 hunks do not overlap G27 hunks, applies the G8 opcodes onto the
live (G27-fixed) glass_runner, and writes the result only if every check
passes. Read-only on the live file; output goes to stage/W24-G8-ROUTING-v3.
"""
import difflib
import hashlib
import py_compile
import shutil
import sys
from pathlib import Path

PRE = Path("/home/ari/ofn/state/owner_dialogue/preimage/glass_runner.py.ddee3da482361c15.orig")
ART = Path("/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v2/glass_runner.py")
LIVE = Path("/home/ari/ofn/ofn/agents/glass_runner.py")
STAGE3 = Path("/home/ari/ofn/state/coding-worker/stage/W24-G8-ROUTING-v3/glass_runner.py")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def opcodes(a: list[str], b: list[str]):
    return [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in
            difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
            if t != "equal"]


def ranges(ops):
    return [(i1, i2) for _, i1, i2, _, _ in ops]


def overlaps(r1, r2) -> bool:
    return any(a < e2 and s2 < e1 for a, e1 in r1 for s2, e2 in r2)


def main() -> int:
    pre_lines = PRE.read_text().splitlines(keepends=True)
    art_lines = ART.read_text().splitlines(keepends=True)
    live_lines = LIVE.read_text().splitlines(keepends=True)

    print(f"pre={sha(PRE)[:16]} art={sha(ART)[:16]} live={sha(LIVE)[:16]}")
    if sha(LIVE) != "02fb704da2d4190a9f4b902edf7300e6704a37cabcd074bfc601a76b77a1ffbe":
        print("ABORT: live sha moved — re-verify before rebase")
        return 1

    g8_ops = opcodes(pre_lines, art_lines)
    g27_ops = opcodes(pre_lines, live_lines)
    print(f"g8_ops={len(g8_ops)} g27_ops={len(g27_ops)}")
    if overlaps(ranges(g8_ops), ranges(g27_ops)):
        print("ABORT: G8 and G27 hunks overlap — manual merge required")
        return 2

    # Apply G8 opcodes (expressed on PRE indices) onto LIVE.
    out, cursor = [], 0
    for _, i1, i2, j1, j2 in g8_ops:
        out.extend(live_lines[cursor:i1])
        out.extend(art_lines[j1:j2])
        cursor = i2
    out.extend(live_lines[cursor:])

    STAGE3.parent.mkdir(parents=True, exist_ok=True)
    STAGE3.write_bytes("".join(out).encode())
    py_compile.compile(str(STAGE3), doraise=True)

    text = STAGE3.read_text()
    checks = {
        "route_fn": text.count("def _route_owner_message"),
        "g27_guard": text.count("_had_error"),
        "money_lane": text.count("money"),
        "len_delta": len(text.splitlines()) - len(live_lines),
    }
    print(f"checks={checks} new_sha={sha(STAGE3)}")
    if checks["route_fn"] < 1 or checks["g27_guard"] < 1 or checks["money_lane"] < 2:
        print("ABORT: marker check failed")
        STAGE3.unlink(missing_ok=True)
        return 3

    # Pre-image of the current live file for rollback.
    pi = Path("/home/ari/ofn/state/owner_dialogue/preimage/glass_runner.py.02fb704da2d4190a.orig")
    if not pi.exists():
        shutil.copyfile(LIVE, pi)
        print(f"preimage_written={pi.name}")
    print("REBASE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
