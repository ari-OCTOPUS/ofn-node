"""owner_notify — اعلان مستقیم تلگرام به مالک (Lane I، رأی Q7).

secrets.env: OFN_BOT_TOKEN_OWNER + OFN_OWNER_USER_IDS (csv).
هرگز token را لاگ نمی‌کند؛ شکستِ ارسال هرگز caller را نمی‌کشد (fail-soft)
ولی یک رسید در events.jsonl می‌گذارد تا سکوت پنهان نماند (درس GAPS-34).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SECRETS = Path.home() / ".config/ofn/secrets.env"


def _secrets() -> dict:
    d = {}
    try:
        for ln in SECRETS.read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                d[k.strip()] = v.strip()
    except Exception:  # noqa: BLE001
        pass
    # env بر فایل مقدم است (systemd محیط را می‌ریزد)
    for k in ("OFN_BOT_TOKEN_OWNER", "OFN_OWNER_USER_IDS"):
        if os.environ.get(k):
            d[k] = os.environ[k]
    return d


def send(text: str, chat_id: str | None = None) -> dict:
    s = _secrets()
    token = s.get("OFN_BOT_TOKEN_OWNER") or ""
    chats = [chat_id] if chat_id else [
        c for c in (s.get("OFN_OWNER_USER_IDS") or "").split(",") if c]
    if not token or not chats:
        opslib.append_jsonl(opslib.STATE_DIR / "legs" / "lead-inbox" /
                            "events.jsonl",
                            {"event_type": "notify.not_armed",
                             "occurred_at": opslib.now_iso(),
                             "source_component": "OwnerNotify",
                             "payload": {"token": bool(token),
                                         "chats": len(chats)}})
        return {"ok": False, "reason": "not-armed"}
    ok_any = False
    errs = []
    for chat in chats:
        try:
            body = json.dumps({"chat_id": chat, "text": text[:3800]}
                              ).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                ok_any = ok_any or r.status == 200
        except Exception as e:  # noqa: BLE001
            errs.append(f"{type(e).__name__}")
    if not ok_any:
        opslib.append_jsonl(opslib.STATE_DIR / "legs" / "lead-inbox" /
                            "events.jsonl",
                            {"event_type": "notify.failed",
                             "occurred_at": opslib.now_iso(),
                             "source_component": "OwnerNotify",
                             "payload": {"errs": errs}})
    return {"ok": ok_any, "errs": errs}


def alert_owner(text: str) -> dict:
    return send("🛎 " + text)


if __name__ == "__main__":
    print(json.dumps(send("✅ owner_notify zinda — pain-e azmoni az lane I (2026-09-01)"),
                     ensure_ascii=False))
