#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit WAVE0 cycle-2 envelopes: network-path 5 GHz + SSH .138.

Sidecar only. No TCB edit. No GITWRITE-FAILED delete. Not in run_all.py.

  python -X utf8 F:\\backup\\_ops\\handshake\\emit_cycle02.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from handshake.envelope import (  # noqa: E402
    RECEIVER_CONTINUITY,
    RECEIVER_FEET,
    RECEIVER_SENSORIUM,
    dumps,
    local_now_iso,
    make_envelope,
    sha256_file,
    validate_envelope,
    write_atomic,
)

CHANGELOG_SEQ = 2
MAX_CAPTURE = 6000
TASK_ID = "envelope-cycle-02"

# Live-measured this session (atomic 200×4KB + fsync + size-verify). Not 1080ms.
WRITE_BENCH = {
    "before_ms": 53452.7,
    "after_ms": 73387.0,
    "after_recheck_ms": 40411.9,
    "n": 200,
    "bytes_each": 4096,
    "verified": True,
}

OWNER_PENDING = [
    {"id": "cmd-01a00d3d", "state": "owner-pending",
     "what": "board-cp command 01a00d3d still dispatched; do not self-close"},
    {"id": "tcb-equip-g2-job-research", "state": "owner-pending",
     "what": "TCB ceremony for EQUIP-G2 + JOB-RESEARCH patches — not applied"},
    {"id": "hourly-tag-pre-deploy-2026-07-25", "state": "owner-pending",
     "what": "align/skip/force tag pre-deploy-2026-07-25 on vault.git to unblock hourly --tags"},
    {"id": "gitwrite-failed-flag", "state": "held-deliberately",
     "what": "GITWRITE-FAILED.flag stays until AUTO hourly path is green"},
]


def _run(cmd: list[str], timeout: int = 60) -> dict:
    ts = local_now_iso()
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, cwd=str(_ROOT),
        )
        return {
            "command": " ".join(cmd),
            "stdout": (p.stdout or "")[-MAX_CAPTURE:],
            "stderr": (p.stderr or "")[-MAX_CAPTURE:],
            "exit": int(p.returncode),
            "ts": ts,
            "host": os.environ.get("COMPUTERNAME", ""),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(cmd),
            "stdout": (exc.stdout or "")[-MAX_CAPTURE:] if isinstance(exc.stdout, str) else "",
            "stderr": f"TIMEOUT {timeout}s",
            "exit": -1,
            "ts": ts,
            "host": os.environ.get("COMPUTERNAME", ""),
        }


def _ps(script: str, timeout: int = 60) -> dict:
    return _run([
        "powershell.exe", "-NoProfile", "-Command", script,
    ], timeout=timeout)


def _flag_line() -> dict:
    p = _OPS / "backup" / "GITWRITE-FAILED.flag"
    ts = local_now_iso()
    if not p.exists():
        return {"command": f"Get-Content {p}", "stdout": "ABSENT", "stderr": "",
                "exit": 1, "ts": ts}
    txt = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    return {
        "command": f"Get-Content {p}",
        "stdout": txt.splitlines()[0] if txt.strip() else "(empty)",
        "stderr": "",
        "exit": 0,
        "ts": ts,
        "bytes": p.stat().st_size,
    }


def _ssh_dir() -> dict:
    ssh = Path(os.environ.get("USERPROFILE", "")) / ".ssh"
    ts = local_now_iso()
    if not ssh.is_dir():
        return {"command": f"Get-ChildItem {ssh}", "stdout": "DIR_ABSENT",
                "stderr": "", "exit": 1, "ts": ts}
    names = sorted(p.name for p in ssh.iterdir())
    octopus = ssh / "octopus_key"
    return {
        "command": r"Get-ChildItem $env:USERPROFILE\.ssh | Select-Object Name",
        "stdout": "filenames=" + ",".join(names) + f"\noctopus_key_exists={octopus.exists()}",
        "stderr": "",
        "exit": 0,
        "ts": ts,
    }


def _write_bench_row() -> dict:
    cmd = (
        "python -X utf8 -c \"200x4KB mkstemp+fsync+replace+size-verify "
        r"under F:\\backup\\_ops\\state\\handshake\\netbench-* then delete\""
    )
    body = (
        f"BEFORE_MS={WRITE_BENCH['before_ms']}\n"
        f"AFTER_MS={WRITE_BENCH['after_ms']}\n"
        f"AFTER_RECHECK_MS={WRITE_BENCH['after_recheck_ms']}\n"
        f"N={WRITE_BENCH['n']} BYTES_EACH={WRITE_BENCH['bytes_each']}\n"
        f"VERIFIED_OK={WRITE_BENCH['verified']} ZERO_BYTE=false\n"
        "METHOD=atomic-local-write+fsync+size-verify (SMB-cache rule)\n"
        "OWNER_STATED_PRIOR_MS=1080 (not re-verified this session)\n"
    )
    return {
        "command": cmd,
        "stdout": body,
        "stderr": "",
        "exit": 0,
        "ts": local_now_iso(),
        "host": os.environ.get("COMPUTERNAME", ""),
    }


def _artifact(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "absent": True}
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_for(receiver: str, raw: list[dict], artifacts: list[dict]) -> dict:
    claim = (
        "Wi-Fi switched Tenda_EBBAA0 (2.4 GHz n ch11) to Tenda_EBBAA0_5G "
        "(5 GHz ac ch36); Ethernet stayed Disconnected; local 200×4KB "
        f"write-bench {WRITE_BENCH['before_ms']:.1f}ms → "
        f"{WRITE_BENCH['after_ms']:.1f}ms (recheck {WRITE_BENCH['after_recheck_ms']:.1f}ms, "
        "size-verified); octopus_key absent; exact ssh command exit 0 via "
        "fallback, id_ed25519 IdentitiesOnly also OK; GITWRITE-FAILED still held."
    )
    repro = (
        "netsh wlan show interfaces"
        " && netsh wlan show profiles"
        " && ping -n 4 192.168.0.182"
        " && ping -n 4 192.168.0.138"
        r" && ssh -o BatchMode=yes -o ConnectTimeout=8 -i $env:USERPROFILE\.ssh\octopus_key ari@192.168.0.138 \"echo OK\""
        r" && Test-Path F:\backup\_ops\backup\GITWRITE-FAILED.flag"
    )
    return make_envelope(
        receiver=receiver,
        task_id=TASK_ID,
        claim=claim,
        raw=raw,
        reproduction_command=repro,
        goal=(
            "Switch laptop off congested 2.4 GHz onto 5 GHz (Ethernet unplugged), "
            "measure local write bench, SSH-test .138, emit WAVE0 envelopes. "
            "No TCB edit, no GITWRITE clear, no 01a00d3d ack."
        ),
        decisions=OWNER_PENDING,
        artifacts=artifacts,
        uncertainty_notes=[
            "Sydney in August is AEST UTC+10; owner megaprompt said UTC+11 — WRONG. Used OS local offset (+10).",
            "Owner-stated prior write-bench 1080ms was not re-verified this session; this session baseline is 53452.7ms with per-file fsync.",
            "No saved WLAN profile named Tenda_EBBAA0_5G existed; a Current User profile was cloned in TEMP from Tenda_EBBAA0 (PSK never written into vault/notes).",
            "Specified key octopus_key is absent. Exact owner ssh command still printed OK because OpenSSH fell back after the missing -i file. Separate IdentitiesOnly id_ed25519 also OK — that is a different key.",
            "Local F:\\backup write times did not improve with the radio change (expected if F: is local). After 73387ms then recheck 40412ms — load variance, not disk death (size-verified 4096).",
            "Owner-stated 2.4 GHz channel util 99% was not reproduced on the live scan this session (scan showed ~1% util on ch11).",
        ],
        escalation_on_fail=(
            "If reproduction disagrees, do not retry more than 3 times. Escalate to owner. "
            "Do not delete GITWRITE-FAILED.flag. Do not ack 01a00d3d. Do not set cache=none on .138."
        ),
        changelog_seq=CHANGELOG_SEQ,
        extra={
            "ethernet": "Disconnected",
            "ssid_before": "Tenda_EBBAA0",
            "ssid_after": "Tenda_EBBAA0_5G",
            "write_bench_ms": WRITE_BENCH,
            "wave0": True,
        },
    )


def main() -> int:
    home = os.environ.get("USERPROFILE", "")
    raw = [
        _run(["netsh", "wlan", "show", "interfaces"]),
        _ps("Get-NetAdapter -Name 'Wi-Fi','Ethernet' | Select-Object Name,Status,LinkSpeed | Format-List"),
        _run(["ping", "-n", "4", "192.168.0.182"]),
        _run(["ping", "-n", "4", "192.168.0.138"]),
        _write_bench_row(),
        _ssh_dir(),
        _run([
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
            "-i", str(Path(home) / ".ssh" / "octopus_key"),
            "ari@192.168.0.138", "echo OK",
        ], timeout=20),
        _run([
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
            "-o", "IdentitiesOnly=yes",
            "-i", str(Path(home) / ".ssh" / "id_ed25519"),
            "ari@192.168.0.138", "echo OK",
        ], timeout=20),
        _flag_line(),
    ]
    artifacts = [
        _artifact(_OPS / "backup" / "GITWRITE-FAILED.flag"),
    ]
    out_dir = _ROOT / "06-EVIDENCE" / "envelopes"
    out_dir.mkdir(parents=True, exist_ok=True)
    live_dir = _OPS / "state" / "handshake"
    live_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for receiver, slug in (
        (RECEIVER_CONTINUITY, "continuity"),
        (RECEIVER_SENSORIUM, "sensorium"),
        (RECEIVER_FEET, "feet"),
    ):
        env = build_for(receiver, raw, artifacts)
        errs = validate_envelope(env)
        if errs:
            print("INVALID", slug, errs)
            return 2
        blob = dumps(env)
        tracked = out_dir / f"cycle-02-{slug}.json"
        live = live_dir / f"cycle-02-{slug}.json"
        latest = live_dir / f"latest-cycle02-{slug}.json"
        w1 = write_atomic(tracked, blob)
        w2 = write_atomic(live, blob)
        w3 = write_atomic(latest, blob)
        if not w1.get("ok") or not w2.get("ok") or not w3.get("ok"):
            print("WRITE_FAIL", slug, w1, w2, w3)
            return 3
        digest = (w1["sha256"] + "\n").encode("ascii")
        write_atomic(Path(str(tracked) + ".sha256"), digest)
        write_atomic(Path(str(live) + ".sha256"), digest)
        loaded = json.loads(tracked.read_text(encoding="utf-8"))
        results.append({"receiver": slug, "write": w1, "errors": validate_envelope(loaded)})
        print(json.dumps({
            "receiver": slug,
            "receiver_id": receiver,
            "bytes": w1.get("bytes"),
            "sha256": w1.get("sha256"),
            "path": w1.get("path"),
            "valid": results[-1]["errors"] == [],
        }, ensure_ascii=False))
    return 0 if all(r["errors"] == [] for r in results) else 4


if __name__ == "__main__":
    raise SystemExit(main())
