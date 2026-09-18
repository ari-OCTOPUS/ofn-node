#!/usr/bin/env python3
"""Deploy the fleet-compute stack with digest verification and a receipt.

Every remote write is pinned to the local file's sha256 and re-read on the node
before the push is considered successful, so "deployed" is never a guess. An
existing remote file is copied to a timestamped .bak before being replaced.

Usage:
  python deploy.py --target board138 --set control
  python deploy.py --target board114 --set agent
  python deploy.py --target board138 --set control --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parent
RECEIPTS = LANE / "evidence" / "deploy-receipts.jsonl"

TARGETS = {
    # 138 runs the control plane as user ari; boards are root-only.
    "board138": {"ssh": "ari@192.168.0.138", "key": "id_ed25519", "home": "/home/ari"},
    "board114": {"ssh": "root@192.168.0.114", "key": "id_ed25519", "home": "/root"},
    "board160": {"ssh": "root@192.168.0.160", "key": "piggybank_id_ed25519", "home": "/root"},
    "board100": {"ssh": "root@192.168.0.100", "key": "piggybank_id_ed25519", "home": "/root"},
    "board193": {"ssh": "root@192.168.0.193", "key": "id_ed25519", "home": "/root"},
    "board180": {"ssh": "root@192.168.0.180", "key": "id_ed25519", "home": "/root"},
}

SETS = {
    # 138 stays the control plane only: it is the busiest board, so it is never
    # a compute target and deliberately does not receive the worker agent.
    "control": [
        ("tools/compute_core.py", "/home/ari/ofn/tools/compute_core.py", "644"),
        ("tools/compute_scheduler.py", "/home/ari/ofn/tools/compute_scheduler.py", "644"),
        ("tools/fleet_probe.py", "/home/ari/ofn/tools/fleet_probe.py", "644"),
        ("compute_config.board.json", "/home/ari/ofn/state/fleet-compute/compute_config.json", "644"),
        ("compute_config.canary.json", "/home/ari/ofn/state/fleet-compute/compute_config.canary.json", "644"),
    ],
    "agent": [
        ("tools/compute_worker.py", "/usr/local/bin/compute_worker.py", "755"),
    ],
    # Unit files are staged on 138 first, then installed with sudo after a
    # digest check (installing into /etc/systemd/system is a root action).
    "units_src": [
        ("units/octopus-compute-shadow.service",
         "/home/ari/ofn/state/fleet-compute/units/octopus-compute-shadow.service", "644"),
        ("units/octopus-compute-shadow.timer",
         "/home/ari/ofn/state/fleet-compute/units/octopus-compute-shadow.timer", "644"),
        ("units/octopus-compute-canary.service",
         "/home/ari/ofn/state/fleet-compute/units/octopus-compute-canary.service", "644"),
        ("units/octopus-compute-canary.timer",
         "/home/ari/ofn/state/fleet-compute/units/octopus-compute-canary.timer", "644"),
    ],
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ssh(target: dict, cmd: str, *, stdin_data: bytes | None = None, timeout: int = 60):
    key = Path.home() / ".ssh" / target["key"]
    full = [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8", "-i", str(key), target["ssh"], cmd,
    ]
    proc = subprocess.run(
        full, capture_output=True, timeout=timeout,
        input=stdin_data, stdin=None if stdin_data is not None else subprocess.DEVNULL,
    )
    return proc.returncode, proc.stdout.decode(errors="replace"), proc.stderr.decode(errors="replace")


def deploy_file(target: dict, local: Path, remote: str, mode: str, *, dry_run: bool) -> dict:
    data = local.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    row = {"local": str(local.relative_to(LANE)), "remote": remote, "sha256": digest, "mode": mode}

    if dry_run:
        row["status"] = "DRY_RUN"
        return row

    # Remote paths are POSIX. pathlib.Path on a Windows host would render
    # '\home\ari\...' and bash would create a junk directory named
    # 'homeariofnstate...' instead of the real parent.
    parent = remote.rsplit("/", 1)[0]
    rc, out, err = ssh(target, f"test -f {remote} && echo EXISTS || echo ABSENT")
    if rc != 0:
        row.update({"status": "FAILED", "error": f"probe_failed: {err.strip()[:200]}"})
        return row
    existed = "EXISTS" in out

    if existed:
        bak = f"{remote}.bak-fleetcompute-{utc_stamp()}"
        rc, _, err = ssh(target, f"cp -p {remote} {bak}")
        if rc != 0:
            row.update({"status": "FAILED", "error": f"preimage_failed: {err.strip()[:200]}"})
            return row
        row["preimage"] = bak

    rc, out, err = ssh(
        target,
        f"mkdir -p {parent} && cat > {remote}.incoming && "
        f"sha256sum {remote}.incoming | cut -d' ' -f1",
        stdin_data=data,
    )
    if rc != 0:
        row.update({"status": "FAILED", "error": f"write_failed: {err.strip()[:200]}"})
        return row
    arrived = out.strip().splitlines()[-1].strip() if out.strip() else ""
    if arrived != digest:
        row.update({"status": "FAILED", "error": f"digest_mismatch local={digest[:12]} remote={arrived[:12]}"})
        return row

    rc, _, err = ssh(
        target,
        f"chmod {mode} {remote}.incoming && mv {remote}.incoming {remote} && "
        f"sha256sum {remote} | cut -d' ' -f1",
    )
    if rc != 0:
        row.update({"status": "FAILED", "error": f"install_failed: {err.strip()[:200]}"})
        return row
    final = out.strip().splitlines()[-1].strip() if out.strip() else ""
    row.update({
        "status": "OK" if final == digest else "FAILED",
        "verified_sha256": final,
        "replaced_existing": existed,
    })
    if final != digest:
        row["error"] = "post_install_digest_mismatch"
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, choices=sorted(TARGETS))
    ap.add_argument("--set", required=True, choices=sorted(SETS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = TARGETS[args.target]
    rows = []
    for local_rel, remote, mode in SETS[args.set]:
        local = LANE / local_rel
        if not local.exists():
            rows.append({"local": local_rel, "remote": remote, "status": "FAILED",
                         "error": "local_missing"})
            continue
        row = deploy_file(target, local, remote, mode, dry_run=args.dry_run)
        rows.append(row)
        print(f"  [{row['status']:>7}] {row['remote']} {row.get('error','')}")

    # Dry-run cannot produce OK rows, so a dry run is "ok" when nothing failed.
    good = ("OK", "DRY_RUN") if args.dry_run else ("OK",)
    receipt = {
        "schema": "deploy_receipt.v1",
        "at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": args.target,
        "set": args.set,
        "dry_run": args.dry_run,
        "files": rows,
        "all_ok": all(r.get("status") in good for r in rows),
    }
    if not args.dry_run:
        RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
        with open(RECEIPTS, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"all_ok": receipt["all_ok"], "files": len(rows)}))
    return 0 if receipt["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())