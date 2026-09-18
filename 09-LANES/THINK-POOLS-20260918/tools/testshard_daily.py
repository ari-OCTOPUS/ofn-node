#!/usr/bin/env python3
"""Daily fleet CI — dispatch one test_shard slice to each idle board.

Owner decision 2026-09-18 ("بله — روزانه"): boards take shards 0/1/2 (100/160/193);
the laptop's nightly task takes shards 3/4/5. Combined: the full 9,700-test suite
runs every night on otherwise-idle hardware, cgroup-bounded, with receipts.

Control-plane only (runs from octopus-testshard-daily.timer on 138).
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OFN = Path("/home/ari/ofn")
STATE = OFN / "state" / "fleet-compute"
PLAN = [("100", 0), ("160", 1), ("193", 2)]
PARAMS = {"root": "/srv/octopus-compute/ofn-suite", "shard_count": 6,
          "pylib": "/srv/octopus-compute/ofn-pylib"}


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M")
    ok = 0
    for node, shard in PLAN:
        params = json.dumps({**PARAMS, "shard_index": shard})
        cmd = [sys.executable, str(OFN / "tools" / "compute_scheduler.py"),
               "--config", str(STATE / f"compute_config.testshard-{node}.json"),
               "--state", str(STATE), "--once",
               "--enqueue-profile", "test_shard", "--enqueue-params", params,
               "--enqueue-key", f"testshard-daily-{stamp}-s{shard}-n{node}"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        out = proc.stdout or ""
        good = proc.returncode == 0 and '"ok": true' in out
        ok += 1 if good else 0
        print(json.dumps({"node": node, "shard": shard, "ok": good,
                          "rc": proc.returncode,
                          "head": out.strip().splitlines()[-1][:160] if out.strip() else ""}),
              flush=True)
    print(f"-- {ok}/{len(PLAN)} shard dispatches ok", flush=True)
    return 0 if ok == len(PLAN) else 1


if __name__ == "__main__":
    sys.exit(main())
