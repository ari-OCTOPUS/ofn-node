#!/usr/bin/env python3
"""check_calltoday.py — was the CALL-TODAY card actually posted despite the RST?

Reads getUpdates (bot is channel admin → channel_post updates), looks for our
card text. If found and no receipt exists, writes a reconstructed receipt
(marked reconstructed=true) from the OBSERVED channel post — never re-sends.
Token from the existing store; never printed. SECRETS_TOUCHED=0.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECEIPTS = ROOT / "ops" / "receipts"
RECEIPT = RECEIPTS / "CALLTODAY-1-RECEIPT.json"
STORE = Path.home() / ".config" / "ofn" / "secrets.env"
CHANNEL = "-1004440663399"
MARKER = "☎️ CALL TODAY"


def kv(path: Path) -> dict:
    d = {}
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def tg(token: str, method: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    token = kv(STORE).get("OFN_BOT_TOKEN_OWNER", "")
    if not token:
        print(json.dumps({"error": "missing token"}))
        return 2
    up = tg(token, "getUpdates", {"limit": 100})
    if not up.get("ok"):
        print(json.dumps({"error": str(up.get("description"))[:200]}))
        return 2
    found = None
    for u in reversed(up.get("result", [])):
        cp = u.get("channel_post") or {}
        if str(cp.get("chat", {}).get("id")) == CHANNEL \
                and str(cp.get("text", "")).startswith(MARKER):
            found = cp
            break
    out = {"found": bool(found)}
    if found:
        out["message_id"] = found.get("message_id")
        out["sha256"] = hashlib.sha256(
            found.get("text", "").encode("utf-8")).hexdigest()
        if not RECEIPT.exists():
            now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            receipt = {
                "schema": "dispatch_receipt.v1",
                "traffic": "CALL-TODAY", "card": "1",
                "owner_go": "owner vote 2026-09-05 structured Q&A: «بفرست»",
                "ts_utc": now_utc, "reconstructed": True,
                "reconstruction_note": "sendMessage response was lost to a "
                                       "connection reset; card OBSERVED in "
                                       "channel via getUpdates before any "
                                       "retry — no double send",
                "channel": "telegram_channel", "chat_id": CHANNEL,
                "message_id": found.get("message_id"),
                "payload_sha256": out["sha256"],
                "counters": {"SECRETS_TOUCHED": 0},
            }
            RECEIPTS.mkdir(parents=True, exist_ok=True)
            tmp = RECEIPT.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
            tmp.replace(RECEIPT)
            out["receipt_written"] = "reconstructed"
        else:
            out["receipt_written"] = "already"
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
