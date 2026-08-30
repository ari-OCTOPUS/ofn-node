# -*- coding: utf-8 -*-
"""SYNTHESIS-NODE-PACKS advisory organ beat (U03 close).

Gated by WIRING flags.synthesis_node_packs_hook.
Read-only load of SYNTHESIS-NODE-PACKS.pointer + packs_dir registry metadata.
Advisory only: never invents pack contents, never claims LIVE promote,
no Telegram / money / PWM / secrets / URLs invented.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .flags import enabled, load_wiring
from .paths import ORGANS_STATE, assert_not_telegram

HOOK_FLAG = "synthesis_node_packs_hook"
POINTER_DEFAULT = (
    Path(__file__).resolve().parent.parent
    / "evidence_plane"
    / "SYNTHESIS-NODE-PACKS.pointer.json"
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_hashes(packs_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    hp = packs_dir / "HASHES.sha256"
    if not hp.is_file():
        return out
    try:
        for line in hp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                out[parts[-1].lstrip("*")] = parts[0]
    except OSError:
        pass
    return out


def _pack_advisory_meta(path: Path, expected_sha: str | None) -> dict[str, Any]:
    """Extract safe registry metadata only — do not invent pack contents."""
    meta: dict[str, Any] = {
        "filename": path.name,
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
        "sha256_expected": expected_sha,
        "sha256_actual": None,
        "hash_ok": None,
        "node_id": None,
        "node_role": None,
        "pack_version": None,
        "collected_at": None,
        "open_questions_count": None,
        "live_promote_claimed": False,
    }
    if not path.is_file():
        return meta
    try:
        actual = _sha256_file(path)
        meta["sha256_actual"] = actual
        if expected_sha:
            meta["hash_ok"] = actual == expected_sha
    except OSError as e:
        meta["hash_error"] = str(e)
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        meta["parse_error"] = str(e)
        return meta
    if not isinstance(blob, dict):
        meta["parse_error"] = "not-a-object"
        return meta
    node = blob.get("node") if isinstance(blob.get("node"), dict) else {}
    meta["node_id"] = node.get("node_id")
    meta["node_role"] = blob.get("node_role")
    meta["pack_version"] = blob.get("pack_version")
    meta["collected_at"] = blob.get("collected_at")
    oq = blob.get("open_questions")
    meta["open_questions_count"] = len(oq) if isinstance(oq, list) else 0
    # surface lock receipt flags only (booleans), never invent promotion
    lock = blob.get("synthesis_lock")
    if isinstance(lock, dict):
        meta["synthesis_lock_flags"] = {
            k: bool(v) for k, v in lock.items() if isinstance(v, bool)
        }
    return meta


def _resolve_packs_dir(wiring_hook: dict[str, Any], pointer: dict[str, Any]) -> Path | None:
    pts = (pointer.get("points_to") or {}) if isinstance(pointer, dict) else {}
    for candidate in (
        wiring_hook.get("packs_dir"),
        pts.get("packs_dir"),
    ):
        if candidate:
            p = Path(str(candidate))
            if p.is_dir():
                return p
    return None


def beat(*, emit: bool = True, state_root: Path | None = None) -> dict[str, Any]:
    """Advisory consumer for synthesis_node_packs_hook.

    Returns flag-off when disarmed. When armed: read pointer + pack registry
    metadata, write advisory sidecar. Never claims LIVE promote.
    """
    if not enabled(HOOK_FLAG, False):
        return {
            "ok": False,
            "reason": "flag-off",
            "hook": HOOK_FLAG,
            "consumer_fired": False,
            "flag_drift": False,
            "live_promote_claimed": False,
            "mode": "advisory",
        }

    wiring = load_wiring()
    hook_meta = ((wiring.get("hooks") or {}).get("synthesis_node_packs") or {})

    pointer_path = POINTER_DEFAULT
    pointer: dict[str, Any] = {}
    pointer_ok = False
    pointer_error = None
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        pointer_ok = isinstance(pointer, dict) and bool(pointer.get("enabled"))
    except (OSError, ValueError) as e:
        pointer_error = str(e)

    packs_dir = _resolve_packs_dir(hook_meta, pointer)
    order = list(hook_meta.get("order") or ["business", "sensorium", "laptop"])

    packs: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    if packs_dir is not None:
        hashes = _load_hashes(packs_dir)
        # Prefer wiring order mapping to NODE-PACK-<ROLE>.json; also include any extras found
        seen: set[str] = set()
        for role in order:
            fname = f"NODE-PACK-{str(role).upper()}.json"
            p = packs_dir / fname
            packs.append(_pack_advisory_meta(p, hashes.get(fname)))
            seen.add(fname)
        for p in sorted(packs_dir.glob("NODE-PACK-*.json")):
            if p.name not in seen:
                packs.append(_pack_advisory_meta(p, hashes.get(p.name)))

    present = [p for p in packs if p.get("exists")]
    missing = [p.get("filename") for p in packs if not p.get("exists")]
    hash_mismatches = [
        p.get("filename") for p in packs if p.get("hash_ok") is False
    ]
    open_q_total = sum(int(p.get("open_questions_count") or 0) for p in present)

    out: dict[str, Any] = {
        "ok": True,
        "hook": HOOK_FLAG,
        "consumer": "organs.synthesis_node_packs.beat",
        "mode": "advisory",
        "consumer_fired": True,
        "flag_drift": False,
        "live_promote_claimed": False,
        "pointer_enabled": bool(pointer.get("enabled")) if pointer else False,
        "pointer_ok": pointer_ok,
        "pointer_path": str(pointer_path),
        "pointer_error": pointer_error,
        "packs_dir": str(packs_dir) if packs_dir else None,
        "packs_dir_exists": packs_dir is not None,
        "order": order,
        "packs_present": len(present),
        "packs_expected": len(order),
        "packs_missing": missing,
        "hash_mismatches": hash_mismatches,
        "open_questions_total": open_q_total,
        "packs": packs,
        "do_not": [
            "invent_pack_contents",
            "claim_LIVE_promote",
            "telegram_broadcast",
            "money_unlock",
            "pwm",
            "invent_secrets_or_urls",
            "organism_restart",
        ],
        "stamp_unix": time.time(),
        "enabled_flag": hook_meta.get("enabled_flag") or HOOK_FLAG,
        "synthesis_json": hook_meta.get("synthesis_json")
        or ((pointer.get("points_to") or {}).get("synthesis_json") if pointer else None),
        "sha256_synthesis": hook_meta.get("sha256")
        or ((pointer.get("points_to") or {}).get("sha256") if pointer else None),
    }

    if emit:
        root = Path(state_root) if state_root is not None else ORGANS_STATE
        root.mkdir(parents=True, exist_ok=True)
        path = root / "synthesis-node-packs-advisory.json"
        assert_not_telegram(path)
        path.write_text(
            json.dumps(out, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        out["advisory_path"] = str(path)

    return out


if __name__ == "__main__":
    print(json.dumps(beat(), indent=2, default=str))
