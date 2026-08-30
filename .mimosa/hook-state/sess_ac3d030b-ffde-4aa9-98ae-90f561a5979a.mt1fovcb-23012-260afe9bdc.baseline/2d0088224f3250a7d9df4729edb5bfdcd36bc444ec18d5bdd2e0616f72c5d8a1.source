#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast 7-day effect counts. Read-only."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"F:/backup")
CUT = datetime.now(timezone.utc) - timedelta(days=7)


def parse_ts(d):
    if not isinstance(d, dict):
        return None
    ts = None
    for k, v in d.items():
        kl = str(k).lower()
        if kl in ("ts", "timestamp", "t", "at", "when", "time", "created") or "time" in kl:
            ts = v
            break
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            ts = ts / 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    if isinstance(ts, str):
        s = ts.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            if len(ts) >= 10:
                try:
                    return datetime.fromisoformat(ts[:10]).replace(tzinfo=timezone.utc)
                except ValueError:
                    return None
    return None


def scan_jsonl(path: Path):
    if not path.exists():
        return {"rel": str(path), "exists": False}
    n = n7 = n_nots = 0
    kinds = Counter()
    first_keys = None
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            n += 1
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if first_keys is None and isinstance(d, dict):
                first_keys = list(d)[:12]
            dt = parse_ts(d) if isinstance(d, dict) else None
            if dt is None:
                n_nots += 1
                continue
            if dt >= CUT:
                n7 += 1
                kind = "?"
                if isinstance(d, dict):
                    kind = str(d.get("kind") or d.get("method") or d.get("event")
                               or d.get("action") or d.get("type") or d.get("verb") or "?")[:40]
                kinds[kind] += 1
    st = path.stat()
    return {
        "rel": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        "rows": n,
        "rows_7d": n7,
        "no_ts": n_nots,
        "kinds_7d": dict(kinds.most_common(10)),
        "keys": first_keys,
    }


def main():
    files = [
        ROOT / "_ops/state/tg-send-log.jsonl",
        ROOT / "_ops/state/paid-calls.jsonl",
        ROOT / "_ops/state/telegram-pep-shadow.jsonl",
        ROOT / "4d_system/outputs/decision_packets.jsonl",
    ]
    out = {p.name: scan_jsonl(p) for p in files}
    # neural consolidation cycles
    p = ROOT / "_ops/neural/consolidation.json"
    if p.exists():
        try:
            data = json.loads(p.read_text("utf-8"))
            if isinstance(data, list):
                out["neural_cons"] = {"n": len(data), "last_keys": list(data[-1])[:8] if data else None}
            elif isinstance(data, dict):
                out["neural_cons"] = {"keys": list(data)[:16], "n_cycles": data.get("cycle") or data.get("last_cycle")}
        except Exception as e:
            out["neural_cons"] = {"error": type(e).__name__}
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
