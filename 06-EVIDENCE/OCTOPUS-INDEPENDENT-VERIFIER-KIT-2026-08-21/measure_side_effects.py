#!/usr/bin/env python3
"""Measure run-local side effects around a dedicated fixture run.

Hashes the live production memory ingest files, miniapp hits, and Telegram
send log immediately before and after the dedicated suite run. Requires byte
identity; any drift is classified, not hidden.

Usage:
    python measure_side_effects.py before --root <repo-root> --out <json>
    python measure_side_effects.py after  --root <repo-root> --out <json> \
        --before <before-json>

Memory paths are the live organism ingest files:
  _ops/state/memory/research-ingest.jsonl
  _ops/state/memory/self-loop-ingest.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TARGETS = [
    ("memory_research_ingest",   "_ops/state/memory/research-ingest.jsonl"),
    ("memory_self_loop_ingest",  "_ops/state/memory/self-loop-ingest.jsonl"),
    ("miniapp_hits",             "_ops/state/telegram/miniapp-hits.jsonl"),
    ("tg_send_log",              "_ops/state/tg-send-log.jsonl"),
]

# patterns that classify send-log rows as live-center background (not fixtures)
LIVE_PATTERNS = ("edit", "center", "summary", "miniapp", "pulse", "decision")


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root: Path) -> dict:
    out = {}
    for key, rel in TARGETS:
        out[key] = {"sha256": sha256(root / rel)}
    return out


def classify_send_log_delta(root: Path, before_sha: str | None) -> dict:
    """When send log changed, classify the new rows as live background or not."""
    path = root / "_ops/state/tg-send-log.jsonl"
    if not path.is_file():
        return {"error": "send log missing"}
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if before_sha is None:
        return {"total": len(rows), "classification": "unmeasured"}
    # files are append-only: walk whole lines back from the end until the
    # prefix hash equals the before-hash; the remainder is the delta.
    full = path.read_bytes()
    cut = len(full)
    matched = False
    while cut > 0:
        if hashlib.sha256(full[:cut]).hexdigest() == before_sha:
            matched = True
            break
        cut = full.rfind(b"\n", 0, cut - 1) + 1  # step back one whole line
    new_rows = []
    if not matched:
        return {"delta_rows": None, "update_id_present": None,
                "all_live_center_patterns": None,
                "classification": "BEFORE_HASH_NOT_FOUND_AS_PREFIX"}
    if cut < len(full):
        tail_bytes = full[cut:]
        new_rows = [json.loads(x) for x in tail_bytes.decode("utf-8", "replace").splitlines() if x.strip()]
    n_update = sum(1 for r in new_rows if r.get("update_id"))
    all_live = all(
        any(p in str(r.get("stream", "") or r.get("source", "") or "") for p in LIVE_PATTERNS)
        for r in new_rows
    ) if new_rows else True
    return {
        "delta_rows": len(new_rows),
        "update_id_present": n_update,
        "all_live_center_patterns": all_live,
        "newest_row": new_rows[-1] if new_rows else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["before", "after"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--before", help="before-json (required for phase=after)")
    args = ap.parse_args()
    root = Path(args.root)
    if args.phase == "before":
        snap = snapshot(root)
        snap["captured_at"] = __import__("time").time()
        Path(args.out).write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(snap, ensure_ascii=False))
        return 0

    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = snapshot(root)
    result = {
        "schema": "kit-side-effects/1",
        "before": before,
        "after": after,
        "run_local": {
            key: (after[key]["sha256"] is not None and after[key]["sha256"] == before.get(key, {}).get("sha256"))
            for key, _ in TARGETS
        },
        "send_log_delta": classify_send_log_delta(root, before.get("tg_send_log", {}).get("sha256")),
    }
    result["memory_unchanged"] = (
        result["run_local"]["memory_research_ingest"] and result["run_local"]["memory_self_loop_ingest"])
    result["miniapp_hits_unchanged"] = result["run_local"]["miniapp_hits"]
    result["send_log_unchanged"] = result["run_local"]["tg_send_log"]
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
