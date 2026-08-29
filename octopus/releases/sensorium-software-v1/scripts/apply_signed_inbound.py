#!/usr/bin/env python3
"""Verify-only apply of laptop-dropped signed bundles. Never signs. Never copies private keys."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/octopus/current/src")

from octopus_sensorium.audit import export_checkpoint, verify_chain
from octopus_sensorium.verify import SignatureError, content_hash, load_root_public_key, load_signed

INBOUND = Path("/var/lib/octopus/inbound")
REG_IN = INBOUND / "SIGNED-REGISTRY-BUNDLE"
CK_IN = INBOUND / "SIGNED-CHECKPOINT-BUNDLE"
TO_LAPTOP = INBOUND / "TO-LAPTOP"
CONFIG = Path("/etc/octopus/config")
HISTORY = Path("/var/lib/octopus/state/config-history")
REPORTS = Path("/var/lib/octopus/state/inbound-apply")
GAPS = Path("/var/lib/octopus/state/gaps")
LIVE_BOARD_ID = "sensorium-opi5pro-68e44cdf"
EXPECTED_V2 = "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"
FORBIDDEN_NAME_BITS = ("private", ".ed25519.private")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _refuse_private(root: Path) -> list[str]:
    leaked = []
    if not root.exists():
        return leaked
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        name = item.name.lower()
        if any(bit in name for bit in FORBIDDEN_NAME_BITS):
            leaked.append(str(item))
            item.unlink()
    return leaked


def _fingerprint(pub: bytes) -> str:
    return content_hash(pub)


def _wait_files(paths: list[Path], timeout_s: int = 90) -> bool:
    import time

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if all(p.is_file() and p.stat().st_size > 0 for p in paths):
            return True
        time.sleep(1)
    return all(p.is_file() and p.stat().st_size > 0 for p in paths)


def export_live_checkpoint() -> Path:
    doc = export_checkpoint()
    dest_dir = TO_LAPTOP / "OCTOPUS-AUDIT-CHECKPOINT"
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / "checkpoint.unsigned.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    src_pack = Path("/root/OCTOPUS-AUDIT-CHECKPOINT")
    for name in ("README.txt", "sign_checkpoint.py", "sign-checkpoint.bat"):
        src = src_pack / name
        if src.exists():
            shutil.copy2(src, dest_dir / name)
    Path("/root/OCTOPUS-AUDIT-CHECKPOINT/checkpoint.unsigned.json").write_text(
        json.dumps(doc, indent=2) + "\n", encoding="utf-8"
    )
    return path


def apply_registry(*, wait: bool = True) -> dict:
    leaked = _refuse_private(REG_IN)
    required = [
        REG_IN / "board.yaml",
        REG_IN / "board.yaml.sig",
        REG_IN / "registry.yaml",
        REG_IN / "registry.yaml.sig",
    ]
    have = all(p.is_file() and p.stat().st_size > 0 for p in required)
    if not have and wait:
        have = _wait_files(required)
    if not have:
        return {"ok": False, "kind": "registry", "reason": "incomplete_bundle", "need": [str(p) for p in required]}
    pub = load_root_public_key()
    fp = _fingerprint(pub)
    if fp != EXPECTED_V2:
        return {"ok": False, "kind": "registry", "reason": f"live_root_mismatch {fp}"}
    try:
        board_bytes = load_signed(REG_IN / "board.yaml", pub)
        registry_bytes = load_signed(REG_IN / "registry.yaml", pub)
    except (OSError, SignatureError) as exc:
        return {"ok": False, "kind": "registry", "reason": f"verify_failed:{exc}"}
    import yaml

    board = yaml.safe_load(board_bytes)
    registry = yaml.safe_load(registry_bytes)
    board_id = ((board or {}).get("board") or {}).get("board_id") or board.get("board_id")
    if board_id != LIVE_BOARD_ID:
        return {"ok": False, "kind": "registry", "reason": f"board_id {board_id}"}
    if registry.get("mqtt_state") != "DISABLED" or registry.get("leg_authority") != "DENIED":
        return {"ok": False, "kind": "registry", "reason": "mqtt_or_leg_not_denied"}
    if registry.get("actuator_changes") is True:
        return {"ok": False, "kind": "registry", "reason": "actuator_changes_true"}
    live_hash = content_hash((CONFIG / "registry.yaml").read_bytes())
    new_hash = content_hash(registry_bytes)
    if live_hash == new_hash:
        return {"ok": True, "kind": "registry", "reason": "already_live", "registry_sha256": new_hash}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = HISTORY / f"pre-registry-v6-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    for name in ("board.yaml", "board.yaml.sig", "registry.yaml", "registry.yaml.sig"):
        shutil.copy2(CONFIG / name, backup / name)
    milestone = Path("/var/lib/octopus/state/milestones/registry-v6")
    milestone.mkdir(parents=True, exist_ok=True)
    for src, dest_dir in ((REG_IN / "board.yaml", CONFIG), (REG_IN / "board.yaml.sig", CONFIG),
                          (REG_IN / "registry.yaml", CONFIG), (REG_IN / "registry.yaml.sig", CONFIG)):
        target = dest_dir / src.name
        target.chmod(0o644)
        shutil.copy2(src, target)
        target.chmod(0o444)
    for name in ("board.yaml", "board.yaml.sig", "registry.yaml", "registry.yaml.sig"):
        shutil.copy2(CONFIG / name, milestone / name)
    subprocess.run(["systemctl", "restart", "octopus-sensorium"], check=False)
    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/octopus/current/src"
    subprocess.run(
        [
            "/opt/octopus/venv/bin/python",
            "/opt/octopus/current/tools/verify_sensorium.py",
            "--json",
            "/var/lib/octopus/state/boot_report.json",
        ],
        check=False,
        env=env,
    )
    report = json.loads(Path("/var/lib/octopus/state/boot_report.json").read_text(encoding="utf-8"))
    result = {
        "ok": report.get("readiness_state") == "READY" and not report.get("gates_failed"),
        "kind": "registry",
        "applied": True,
        "config_version": registry.get("config_version"),
        "registry_sha256": new_hash,
        "backup": str(backup),
        "leaked_private_removed": leaked,
        "readiness_state": report.get("readiness_state"),
        "gates_failed": report.get("gates_failed"),
        "note": "096/097/099/100 shadow only; actuators/MQTT/legs unchanged",
    }
    return result


def apply_checkpoint(*, wait: bool = True) -> dict:
    leaked = _refuse_private(CK_IN)
    candidates = [
        CK_IN / "checkpoint.json",
        CK_IN / "checkpoint.unsigned.json",
    ]
    payload = next((p for p in candidates if p.is_file()), None)
    if payload is None:
        if wait and _wait_files([CK_IN / "checkpoint.json"]):
            payload = CK_IN / "checkpoint.json"
        else:
            return {"ok": False, "kind": "checkpoint", "reason": "incomplete_bundle"}
    sig = payload.with_suffix(payload.suffix + ".sig")
    if not sig.is_file():
        if wait:
            _wait_files([sig], timeout_s=90)
        if not sig.is_file():
            return {"ok": False, "kind": "checkpoint", "reason": "missing_sig"}
    pub = load_root_public_key()
    try:
        load_signed(payload, pub)
    except SignatureError as exc:
        return {"ok": False, "kind": "checkpoint", "reason": f"verify_failed:{exc}"}
    live = export_checkpoint()
    doc = json.loads(payload.read_text(encoding="utf-8"))
    ok_chain, detail = verify_chain()
    match = doc.get("head_hash") == live.get("head_hash") and doc.get("sequence") == live.get("sequence")
    closed = bool(ok_chain and match)
    gap = {
        "gap_id": "GAP-002",
        "title": "audit_head_unsigned",
        "status": "CLOSED_BY_SIGNED_CHECKPOINT" if closed else "OPEN",
        "pass": closed,
        "signed": True,
        "head_match": match,
        "chain": detail,
        "checkpoint_sequence": doc.get("sequence"),
        "live_sequence": live.get("sequence"),
        "leaked_private_removed": leaked,
    }
    _write(GAPS / "GAP-002-audit_head_unsigned.json", gap)
    if not match:
        export_live_checkpoint()
        gap["reason"] = "stale_head_reexported_unsigned_for_laptop"
        gap["ok"] = False
        return gap
    gap["ok"] = closed
    gap["kind"] = "checkpoint"
    gap["audit_integrity"] = "EXTERNALLY_CHECKPOINTED" if closed else "HASH_CHAIN_ONLY"
    return gap


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    TO_LAPTOP.mkdir(parents=True, exist_ok=True)
    export_live_checkpoint()
    kind = (sys.argv[1] if len(sys.argv) > 1 else "all").strip()
    wait = kind != "all"
    results = []
    if kind in {"all", "registry"}:
        results.append(apply_registry(wait=wait))
    if kind in {"all", "checkpoint"}:
        results.append(apply_checkpoint(wait=wait))
    out = {"timestamp": _now(), "results": results}
    _write(REPORTS / "last.json", out)
    print(json.dumps(out, indent=2))
    subprocess.run(["/opt/octopus/venv/bin/python", "/opt/octopus/scripts/write_laptop_handoff.py"], check=False)
    return 0 if all(r.get("ok") for r in results if r.get("reason") != "incomplete_bundle") else 1


if __name__ == "__main__":
    raise SystemExit(main())
