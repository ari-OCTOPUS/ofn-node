"""Three-way rebase: TRIO_V2 = LIVE + (TRIO_artifact - BASE).

TRIO-001 (base 109e68c0, artifact f6bc8d1c) is stale: live ops_agent moved to
c2e290fd (retirefix). Build TRIO-002 onto the live base with overlap check,
compile + import + marker probes, and stage it. Queueing is a separate script.
"""
import difflib
import hashlib
import importlib.util
import py_compile
import shutil
import sys
from pathlib import Path

BASE = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py.baseline-109e68c0")
ART = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260914/ops_agent.py")
LIVE = Path("/home/ari/ofn/state/ops-agent/ops_agent.py")
STAGE = Path("/home/ari/ofn/state/coding-worker/stage/SUCCESSOR-TRIO-20260915/ops_agent.py")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def opcodes(a, b):
    return [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in
            difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
            if t != "equal"]


def overlaps(r1, r2):
    return any(a < e2 and s2 < e1 for a, e1 in r1 for s2, e2 in r2)


def main() -> int:
    base_lines = BASE.read_text().splitlines(keepends=True)
    art_lines = ART.read_text().splitlines(keepends=True)
    live_lines = LIVE.read_text().splitlines(keepends=True)

    print(f"base={sha(BASE)[:16]} art={sha(ART)[:16]} live={sha(LIVE)[:16]}")
    if sha(LIVE)[:16] != "c2e290fd96d42685":
        print("ABORT: live ops_agent sha moved — re-probe before rebase")
        return 1

    trio_ops = opcodes(base_lines, art_lines)
    retire_ops = opcodes(base_lines, live_lines)
    print(f"trio_ops={len(trio_ops)} retirefix_ops={len(retire_ops)}")
    if overlaps([(i1, i2) for _, i1, i2, _, _ in trio_ops],
                [(i1, i2) for _, i1, i2, _, _ in retire_ops]):
        print("ABORT: TRIO and retirefix hunks overlap — manual merge required")
        return 2

    out, cursor = [], 0
    for _, i1, i2, j1, j2 in trio_ops:
        out.extend(live_lines[cursor:i1])
        out.extend(art_lines[j1:j2])
        cursor = i2
    out.extend(live_lines[cursor:])

    STAGE.parent.mkdir(parents=True, exist_ok=True)
    STAGE.write_bytes("".join(out).encode())
    py_compile.compile(str(STAGE), doraise=True)
    print("COMPILE_OK")

    # import probe on the merged artifact (defs only; __main__ guard respected)
    sys.path.insert(0, "/home/ari/ofn/ofn/budget")
    sys.path.insert(0, "/home/ari/ofn/ofn/agents")
    spec = importlib.util.spec_from_file_location("ops_trio002", STAGE)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    probes = {
        "budget_allows_returns_tuple": isinstance(m.budget_allows("B5", "storage-cache"), tuple),
        "read_receipts_loads": isinstance(m.read_receipts(), list),
    }

    text = STAGE.read_text()
    for marker in ("DECISION", "CATSCOPE", "starvation"):
        probes[f"marker_{marker}"] = marker.lower() in text.lower()
    ok = all(probes.values())
    print(f"probes={probes}")
    if not ok:
        print("ABORT: probe failed")
        return 3

    # pre-image of live for rollback (executor preimage dir)
    pi = Path("/home/ari/ofn/state/ops-agent/preimage/ops_agent.py.c2e290fd96d42685.orig")
    if not pi.exists():
        shutil.copyfile(LIVE, pi)
        print("preimage_written")
    print(f"REBASE_OK new_sha={sha(STAGE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
