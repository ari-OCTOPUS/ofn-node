# -*- coding: utf-8 -*-
"""Wait for 3 unique memory beats after cortex canary. No paid calls."""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

EV = Path("06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20")
MEM = Path("_ops/state/pulse/memory-read-latest.json")
RX = Path("_ops/state/cortex/cost-receipts.jsonl")
STOP = Path("_ops/STOP-CORTEX")


def main() -> int:
    t0 = datetime.now(timezone.utc)
    start = json.loads(MEM.read_text(encoding="utf-8"))
    start_beat = int(start.get("beat") or 0)
    print("start_beat", start_beat, "stop_cortex_exists", STOP.exists())
    seen: dict[int, dict] = {}
    deadline = time.time() + 10 * 60
    while time.time() < deadline:
        s = json.loads(MEM.read_text(encoding="utf-8"))
        b = int(s.get("beat") or 0)
        if b not in seen:
            seen[b] = {
                "beat": b,
                "readback": s.get("readback"),
                "reads": s.get("memory_reads_per_cycle"),
                "status": s.get("status"),
                "executable": s.get("executable"),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            print("beat", b, s.get("readback"), "unique", len(seen))
        new = [k for k in seen if k >= start_beat]
        if max(seen) >= start_beat + 3 and len(new) >= 4:
            break
        time.sleep(15)
    subprocess.run(
        ["powershell", "-NoProfile", "-File", str(EV / "_snapshot_pids.ps1")],
        check=False,
    )
    h = hashlib.sha256(RX.read_bytes()).hexdigest()
    n = sum(1 for line in RX.open(encoding="utf-8") if line.strip())
    post = json.loads((EV / "PROCESS-PIDS.json").read_text(encoding="utf-8-sig"))
    out = {
        "schema": "canary-cortex-post/1",
        "t0": t0.isoformat(),
        "start_beat": start_beat,
        "beats": seen,
        "receipt_sha256": h,
        "receipt_lines": n,
        "pids": post,
        "stop_cortex_left_behind": STOP.exists(),
        "wave1_unlocked": False,
    }
    (EV / "CANARY-POST-CORTEX.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("cortex_pid", post.get("cortex", {}).get("pid"))
    print("daemon_pid", post.get("daemon", {}).get("pid"))
    print("live_pid", post.get("live", {}).get("pid"))
    print("receipts", n, h)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
