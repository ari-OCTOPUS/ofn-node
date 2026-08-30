#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit one WAVE0 evidence-envelope cycle. No TCB edit. No flag delete. No --quiet.

Run from anywhere:
  python -X utf8 F:\\backup\\_ops\\handshake\\emit_cycle.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from handshake.envelope import (  # noqa: E402
    RECEIVER_FEET,
    RECEIVER_SENSORIUM,
    dumps,
    local_now_iso,
    make_envelope,
    sha256_file,
    validate_envelope,
    write_atomic,
)

CHANGELOG_SEQ = 1
MAX_CAPTURE = 4000


def _run(cmd: list[str], timeout: int = 60) -> dict:
    ts = local_now_iso()
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, cwd=str(_ROOT),
        )
        out = (p.stdout or "")[-MAX_CAPTURE:]
        err = (p.stderr or "")[-MAX_CAPTURE:]
        return {
            "command": " ".join(cmd),
            "stdout": out,
            "stderr": err,
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


def _curl_8801() -> dict:
    # retry up to 3 (envelope max_retries)
    last = {}
    for _ in range(3):
        last = _run([
            "curl.exe", "-sk", "--max-time", "8", "-w", " HTTP=%{http_code}",
            "https://127.0.0.1:8801/api/board-cp/pull",
        ], timeout=15)
        if last.get("exit") == 0 and "HTTP=401" in (last.get("stdout") or ""):
            return last
    return last


def _daemon_slice() -> dict:
    p = _ROOT / "4d_system" / "outputs" / "daemon_state.json"
    ts = local_now_iso()
    if not p.exists():
        return {"command": f"type {p}", "stdout": "ABSENT", "stderr": "", "exit": 1, "ts": ts}
    raw = json.loads(p.read_text(encoding="utf-8"))
    slice_ = {k: raw.get(k) for k in (
        "pid", "resumed_at", "last_tick_at", "tick_this_run", "errors_this_run",
    )}
    return {
        "command": f"python -c daemon_state_slice {p}",
        "stdout": json.dumps(slice_, ensure_ascii=False),
        "stderr": "",
        "exit": 0,
        "ts": ts,
        "host": os.environ.get("COMPUTERNAME", ""),
        "bytes": p.stat().st_size,
        "sha256": sha256_file(p),
    }


def _flag_line() -> dict:
    p = _OPS / "backup" / "GITWRITE-FAILED.flag"
    ts = local_now_iso()
    if not p.exists():
        return {"command": f"type {p}", "stdout": "ABSENT", "stderr": "", "exit": 1, "ts": ts}
    txt = p.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    return {
        "command": f"Get-Content {p}",
        "stdout": txt.splitlines()[0] if txt.strip() else "(empty)",
        "stderr": "",
        "exit": 0,
        "ts": ts,
        "bytes": p.stat().st_size,
        "mtime": str(p.stat().st_mtime),
    }


def _commands() -> dict:
    db = _OPS / "state" / "board_cp" / "commands.sqlite"
    ts = local_now_iso()
    if not db.exists():
        return {
            "command": f"sqlite3 {db} SELECT state",
            "stdout": "ABSENT",
            "stderr": "",
            "exit": 1,
            "ts": ts,
        }
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = [
            {"id_prefix": r[0][:8], "state": r[1], "updated_at": r[2]}
            for r in con.execute(
                "SELECT message_id, state, updated_at FROM commands ORDER BY created_at"
            )
        ]
        con.close()
        return {
            "command": f"sqlite3 {db} 'SELECT substr(message_id,1,8), state, updated_at FROM commands'",
            "stdout": json.dumps(rows, ensure_ascii=False),
            "stderr": "",
            "exit": 0,
            "ts": ts,
        }
    except sqlite3.Error as exc:
        return {
            "command": f"sqlite3 {db}",
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
            "exit": 2,
            "ts": ts,
        }


def _tags_dry() -> dict:
    return _run([
        "git", "-C", str(_ROOT), "push", "--dry-run",
        "E:/germline/vault.git", "--tags",
    ], timeout=90)


def _equip_tips() -> dict:
    local = _run(["git", "-C", str(_ROOT), "rev-parse", "equip/g10-cognition-20260816"])
    remote = _run([
        "git", "--git-dir=E:/germline/octopus.git", "rev-parse",
        "refs/heads/equip/g10-cognition-20260816",
    ])
    return {
        "command": "git rev-parse local-equip && git --git-dir=octopus.git rev-parse remote-equip",
        "stdout": f"local={ (local.get('stdout') or '').strip() }\nremote={ (remote.get('stdout') or '').strip() }",
        "stderr": (local.get("stderr") or "") + (remote.get("stderr") or ""),
        "exit": 0 if local.get("exit") == 0 and remote.get("exit") == 0 else 1,
        "ts": local_now_iso(),
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
        "Laptop WAVE0 envelope cycle-1: :8801 returns 401 without bearer; "
        "4d daemon is ticking; GITWRITE-FAILED remains; hourly --tags is rejected "
        "on tag pre-deploy-2026-07-25; equip tip matches germline octopus.git."
    )
    repro = (
        "curl.exe -sk --max-time 8 -w \" HTTP=%{http_code}\" "
        "https://127.0.0.1:8801/api/board-cp/pull"
        " && git -C F:\\backup push --dry-run E:/germline/vault.git --tags"
        " && git -C F:\\backup rev-parse equip/g10-cognition-20260816"
        " && git --git-dir=E:/germline/octopus.git rev-parse refs/heads/equip/g10-cognition-20260816"
    )
    return make_envelope(
        receiver=receiver,
        task_id="envelope-cycle-01",
        claim=claim,
        raw=raw,
        reproduction_command=repro,
        goal="Issue typed Evidence Envelope without changing autonomy or TCB.",
        decisions=OWNER_PENDING,
        artifacts=artifacts,
        uncertainty_notes=[
            "SSH to 192.168.0.138 was publickey-denied in the prior session; feet mount options not re-verified this cycle.",
            "Tag dry-run is the live failing command; do not treat a green --all as a green hourly path.",
        ],
        escalation_on_fail=(
            "If reproduction disagrees, do not retry more than 3 times. Escalate to owner. "
            "Do not delete GITWRITE-FAILED.flag. Do not ack 01a00d3d."
        ),
        changelog_seq=CHANGELOG_SEQ,
    )


def main() -> int:
    raw = [
        _curl_8801(),
        _daemon_slice(),
        _flag_line(),
        _commands(),
        _equip_tips(),
        _tags_dry(),
    ]
    artifacts = [
        _artifact(_ROOT / "4d_system" / "outputs" / "daemon_state.json"),
        _artifact(_OPS / "backup" / "GITWRITE-FAILED.flag"),
        _artifact(_ROOT / "06-EVIDENCE" / "HOURLY-PUSH-EMPTY-ERR-2026-08-18.md"),
        _artifact(_ROOT / "06-EVIDENCE" / "LAPTOP-CHANNEL-RESTORE-2026-08-17.md"),
    ]
    out_dir = _ROOT / "06-EVIDENCE" / "envelopes"
    out_dir.mkdir(parents=True, exist_ok=True)
    live_dir = _OPS / "state" / "handshake"
    live_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for receiver, slug in (
        (RECEIVER_SENSORIUM, "sensorium"),
        (RECEIVER_FEET, "feet"),
    ):
        env = build_for(receiver, raw, artifacts)
        errs = validate_envelope(env)
        if errs:
            print("INVALID", slug, errs)
            return 2
        blob = dumps(env)
        tracked = out_dir / f"cycle-01-{slug}.json"
        live = live_dir / f"cycle-01-{slug}.json"
        latest = live_dir / f"latest-{slug}.json"
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
            "bytes": w1.get("bytes"),
            "sha256": w1.get("sha256"),
            "path": w1.get("path"),
            "valid": results[-1]["errors"] == [],
        }, ensure_ascii=False))
    return 0 if all(r["errors"] == [] for r in results) else 4


if __name__ == "__main__":
    raise SystemExit(main())
