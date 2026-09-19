#!/usr/bin/env python3
"""Event-driven owner TG notify for OWNER_QUEUE (immediate path).
Call after enqueue/update of BLOCKED_ON_OWNER / OWNER_REQUIRED rows.
Dedup 60m · no secrets · owner_telegram only · respects notify_cap_policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/home/ari/ofn")
from ofn.agents.owner_notify import send

STATE = Path("/home/ari/ofn/state/owner_dialogue")
DEDUP = STATE / "digest_dedup.json"
TZ = ZoneInfo("Australia/Sydney")


def load(path, default):
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="decision", choices=["inform", "decision", "incident", "announce"])
    ap.add_argument("--summary", required=True)
    ap.add_argument("--fingerprint", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    summary = args.summary.strip()[:400]
    if not summary:
        print("empty")
        return 1
    low = summary.lower()
    for bad in ("cookie", "password", "tfn", "api_key", "bearer "):
        if bad in low:
            print("forbidden")
            return 2
    fp = args.fingerprint or hashlib.sha256(f"{args.kind}|{summary}".encode()).hexdigest()[:16]
    card_type = {
        "inform": "digest_evening",
        "decision": "decision_request",
        "incident": "incident",
        "announce": "digest_evening",
    }[args.kind]
    now = datetime.now(TZ)
    data = load(DEDUP, {})
    key = f"{card_type}|{fp}"
    prev = data.get(key)
    if prev:
        try:
            prev_dt = datetime.fromisoformat(prev)
            if prev_dt.tzinfo is None:
                prev_dt = prev_dt.replace(tzinfo=TZ)
            if (now - prev_dt).total_seconds() < 3600:
                print("skip_dedup")
                return 0
        except Exception:
            pass
    title = f"OCTOPUS {args.kind.upper()} {now.strftime('%Y-%m-%d %H:%M')} Syd"
    body = (
        f"{title}\n{summary}\n"
        "destination=owner_telegram · customer_send=false · secrets_in_card=false\n"
        f"fingerprint={fp}"
    )[:800]
    print("chars", len(body))
    if args.dry_run:
        print(body)
        return 0
    r = send(body)
    print("ok", bool(r.get("ok")))
    if r.get("ok"):
        data[key] = now.isoformat()
        save(DEDUP, data)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
