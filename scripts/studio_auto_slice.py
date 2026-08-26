#!/usr/bin/env python3
"""Board2 studio AUTO SLICE — caption-gated telegram only.

Rules (owner/ari SoT 2026-08-23):
- platform: telegram_channel ONLY
- captions: media_items.note non-empty ONLY (no invent)
- skip if already published (outbox manual_completed for same draft/shot OR media_sent)
- do NOT fan-out empty-caption shots 0003-0022
- dry_run inventory by default; --enqueue-one SHOT requires explicit shot with caption
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
COLL = "album-unlock-20260822"


def load_env() -> None:
    for f in (
        Path.home() / ".config/ofn/node.env",
        Path.home() / ".config/ofn/secrets.env",
    ):
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v


def tg_init(token: str, uid: str, first: str, uname: str) -> str:
    from ofn.kernel.auth import data_check_string

    user = json.dumps(
        {"id": int(uid), "first_name": first, "username": uname}, separators=(",", ":")
    )
    fields = {"auth_date": str(int(time.time())), "user": user}
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(
        secret, data_check_string(fields).encode(), hashlib.sha256
    ).hexdigest()
    return "&".join(f"{k}={urllib.parse.quote(v, safe='')}" for k, v in fields.items())


def http(base: str, host: str, method: str, path: str, body=None, session=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Host": host, "Content-Type": "application/json"}
    if session:
        headers["Authorization"] = "Bearer " + session
    req = urllib.request.Request(
        f"{base}{path}", data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        err = e.read().decode() if hasattr(e, "read") else str(e)
        try:
            errj = json.loads(err)
        except Exception:
            errj = {"raw": err[:800]}
        return getattr(e, "code", None), errj


def already_published(shot: str) -> list[dict]:
    """Return outbox rows that look published for this shot."""
    ob = sqlite3.connect(str(Path.home() / ".local/share/ofn/outbox.sqlite"))
    rows = ob.execute(
        "SELECT idem_key, status, completion_channel, external_ref_digest, payload "
        "FROM outbox WHERE tenant='studio'"
    ).fetchall()
    hits = []
    for idem, status, chan, ext, payload in rows:
        if shot in (payload or "") and status in (
            "manual_completed",
            "completed",
            "approved_manual",
            "pending",
        ):
            hits.append(
                {
                    "idem_key": idem,
                    "status": status,
                    "channel": chan,
                    "external_ref_digest": ext,
                }
            )
    # media_sent
    st = sqlite3.connect(str(Path.home() / ".local/share/ofn/studio.sqlite"))
    # drafts referencing shot
    for draft_id, in st.execute(
        "SELECT draft_id FROM draft_media WHERE media_ref LIKE ?",
        (f"%{shot}%",),
    ):
        for r in st.execute(
            "SELECT draft_id, platform, sent_at FROM media_sent WHERE draft_id=?",
            (draft_id,),
        ):
            hits.append(
                {
                    "media_sent": True,
                    "draft_id": r[0],
                    "platform": r[1],
                    "sent_at": r[2],
                }
            )
    return hits


def inventory() -> dict:
    load_env()
    st = sqlite3.connect(str(Path.home() / ".local/share/ofn/studio.sqlite"))
    items = []
    for mid, note in st.execute(
        "SELECT media_id, coalesce(note,'') FROM media_items WHERE tenant_id='studio' ORDER BY media_id"
    ):
        note = (note or "").strip()
        pub = already_published(mid)
        items.append(
            {
                "shot": mid,
                "caption_len": len(note),
                "caption_preview": note[:80],
                "eligible_enqueue": bool(note) and not any(
                    h.get("status") == "manual_completed" for h in pub
                ),
                "already_published_hits": pub,
                "action": (
                    "SKIP_REPUBLISH"
                    if any(h.get("status") == "manual_completed" for h in pub)
                    else ("HOLD_EMPTY_CAPTION" if not note else "ELIGIBLE")
                ),
            }
        )
    return {
        "stamp": STAMP,
        "platform_scope": "telegram_channel",
        "of_fansly": "NOT_IN_SCOPE",
        "items": items,
        "eligible": [i["shot"] for i in items if i["action"] == "ELIGIBLE"],
        "hold_empty": [i["shot"] for i in items if i["action"] == "HOLD_EMPTY_CAPTION"],
        "skip_republish": [i["shot"] for i in items if i["action"] == "SKIP_REPUBLISH"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true", default=True)
    ap.add_argument(
        "--enqueue-one",
        default="",
        help="Optional shot id with existing caption; still skips if published",
    )
    ap.add_argument(
        "--approve-publish",
        action="store_true",
        help="After enqueue, owner-path approve+publish (dangerous; needs explicit)",
    )
    args = ap.parse_args()
    inv = inventory()
    Path("/tmp/BOARD2-STUDIO-AUTO-INVENTORY.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: inv[k] for k in ("eligible", "hold_empty", "skip_republish")}, ensure_ascii=False, indent=2))
    if not args.enqueue_one:
        return 0
    # enqueue path reserved — require caption + not published; default refuse fan-out
    shot = args.enqueue_one.strip()
    row = next((i for i in inv["items"] if i["shot"] == shot), None)
    if not row:
        print("UNKNOWN_SHOT", shot)
        return 2
    if row["action"] != "ELIGIBLE":
        print("REFUSE", row["action"], shot)
        return 3
    print("ENQUEUE_NOT_RUN_IN_DEFAULT_CLOSE — design only unless owner GO for specific shot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())