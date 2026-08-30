#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit WAVE0 A2-001 inventory envelopes — UNKNOWN_CANONICAL halt.

Sidecar only. No TCB. No network. No SSH. Not in run_all.py.

  python -X utf8 F:\\backup\\_ops\\handshake\\emit_a2_001.py
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

CHANGELOG_SEQ = 3
MAX_CAPTURE = 8000
TASK_ID = "a2-001-inventory"
VERDICT = "UNKNOWN_CANONICAL"

CLAIM = (
    "A2-001 halted on .191 with UNKNOWN_CANONICAL: vault octopus-bridge is a "
    "two-file OFN stub and ofn/bridge is a different full package; neither has "
    "schemas/ or mirror_verify.py, so no unique SoT path exists."
)

REPRO = (
    r"git -C F:\backup rev-parse HEAD"
    r" && git -C F:\backup ls-files octopus-bridge"
    r" && git --git-dir=E:\germline\octopus.git ls-tree -r --name-only refs/heads/ofn/bridge"
    r" && git --git-dir=E:\germline\octopus.git ls-tree -r --name-only equip/g10-cognition-20260816 -- octopus-bridge"
)

UNCERTAINTY = [
    "Tests were not run; this is inventory halt, not verifier PASS/FAIL.",
    ".180 was not executed. Fugu/DeepSeek did not run.",
    "octopus-bridge was not confirmed canonical. Guessing the implementation tree is forbidden.",
    "Owner-assumed empty octopus-bridge/schemas/ does not exist on this laptop.",
    "_ops/mirror_verifier/ and F:\\backup-wt-a2-001 were not created (old layout never landed).",
    "Sydney in August is AEST UTC+10; megaprompt UTC+11 is wrong — using OS local offset.",
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


def _exists_row(path: str) -> dict:
    p = Path(path)
    return {
        "command": f"Test-Path {path}",
        "stdout": f"exists={p.exists()} is_dir={p.is_dir()}\n",
        "stderr": "",
        "exit": 0 if p.exists() else 1,
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
    return make_envelope(
        receiver=receiver,
        task_id=TASK_ID,
        claim=CLAIM,
        raw=raw,
        reproduction_command=REPRO,
        goal=(
            "Inventory octopus-bridge clones on .191 for A2-001. Do not guess "
            "canonical path. Record OWNER-APPROVED-PROPOSAL. Halt on ambiguity."
        ),
        decisions=[
            {
                "id": "A2-001",
                "state": "owner-approved-proposal",
                "what": "Mirror Manifest Verifier; execution intended .180; canonical .191",
            },
            {
                "id": "canonical-repo",
                "state": "unknown-canonical",
                "what": "octopus-bridge not rubber-stamped; inventory found >1 plausible root",
            },
            {
                "id": "gitwrite-failed-flag",
                "state": "held-deliberately",
                "what": "GITWRITE-FAILED.flag stays",
            },
        ],
        artifacts=artifacts,
        uncertainty_notes=UNCERTAINTY,
        escalation_on_fail=(
            "Do not implement into a guessed tree. Do not SSH .180/.138/.182. "
            "Escalate path choice to owner on .191."
        ),
        changelog_seq=CHANGELOG_SEQ,
        extra={
            "verdict": VERDICT,
            "implementation_proceeded": False,
            "wave0": True,
            "integrity_hint": "hash-chain-unkeyed",
            "a2_order": ["A2-001", "A2-002", "A2-003-draft-only"],
        },
    )


def main() -> int:
    raw = [
        _run(["git", "-C", r"F:\backup", "rev-parse", "HEAD"]),
        _run(["git", "-C", r"F:\backup", "rev-parse", "--abbrev-ref", "HEAD"]),
        _run(["git", "-C", r"F:\backup", "ls-files", "octopus-bridge"]),
        _run([
            "git", "--git-dir=E:\\germline\\octopus.git",
            "ls-tree", "-r", "--name-only",
            "refs/heads/ofn/bridge",
        ]),
        _run([
            "git", "--git-dir=E:\\germline\\octopus.git",
            "ls-tree", "-r", "--name-only",
            "equip/g10-cognition-20260816", "--", "octopus-bridge",
        ]),
        _exists_row(r"F:\backup\octopus-bridge\schemas"),
        _exists_row(r"F:\backup\octopus-bridge\octopus_bridge\mirror_verify.py"),
        _exists_row(r"F:\backup-wt-a2-001"),
        _exists_row(r"F:\backup\_ops\mirror_verifier"),
    ]
    artifacts = [
        _artifact(_ROOT / "06-EVIDENCE" / "A2-001-CANONICAL-DECISION-2026-08-18.md"),
        _artifact(_ROOT / "02-DECISIONS" / "A2-001-MIRROR-MANIFEST-VERIFIER.md"),
        _artifact(_OPS / "backup" / "GITWRITE-FAILED.flag"),
    ]
    out_dir = _ROOT / "06-EVIDENCE" / "envelopes"
    out_dir.mkdir(parents=True, exist_ok=True)

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
        tracked = out_dir / f"a2-001-{slug}.json"
        w1 = write_atomic(tracked, blob)
        if not w1.get("ok"):
            print("WRITE_FAIL", slug, w1)
            return 3
        digest = (w1["sha256"] + "\n").encode("ascii")
        write_atomic(Path(str(tracked) + ".sha256"), digest)
        loaded = json.loads(tracked.read_text(encoding="utf-8"))
        results.append({"receiver": slug, "write": w1, "errors": validate_envelope(loaded)})
        print(json.dumps({
            "receiver": slug,
            "receiver_id": receiver,
            "bytes": w1.get("bytes"),
            "sha256": w1.get("sha256"),
            "path": w1.get("path"),
            "verdict": VERDICT,
            "valid": results[-1]["errors"] == [],
        }, ensure_ascii=False))
    return 0 if all(r["errors"] == [] for r in results) else 4


if __name__ == "__main__":
    raise SystemExit(main())
