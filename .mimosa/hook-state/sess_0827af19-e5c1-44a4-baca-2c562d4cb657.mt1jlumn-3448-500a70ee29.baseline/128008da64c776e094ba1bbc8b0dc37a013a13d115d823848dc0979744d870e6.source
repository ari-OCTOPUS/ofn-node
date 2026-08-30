#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_bridge_once.py — پل ۵ دقیقه‌ای Telegram (دستور مالک 2026-08-20 شب).

به‌جای ایجنت، وضعیت OCTOPUS مستقیم در تلگرام به مالک می‌رسد. قواعد:
- هرگز getUpdates روی بات مشترک (409 با center/approval_channel — ثبت‌شده).
- push فقط روی «تغییر وضعیت» یا ≥۳۰ دقیقه از push قبلی (ضداسپم §۱۴ مگادستور #۱۳).
- رویدادهای مهم (بسته‌شدن LIVE-B، پروب، alert) همیشه push می‌شوند.
- هیچ secret؛ فقط اعداد و برچسب‌ها. خروجی یک خط برای گزارش چت."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "_ops/budget"))

STATE_FILE = _ROOT / "research/full_loop/state/tg-last-push.json"
PUSH_MIN_INTERVAL_S = 30 * 60


def _env():
    import env_loader
    env_loader.load_env()
    return (os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_OWNER_CHAT_ID"])


def _send(token: str, chat_id: str, text: str) -> bool:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode()).get("ok") is True


def snapshot() -> dict:
    import sqlite3
    out = {"ts": time.time()}
    try:
        d = json.loads((_ROOT / "_ops/state/ORGANISM-STATE.json")
                       .read_text(encoding="utf-8"))
        out["beat"] = d.get("beat")
    except Exception:  # noqa: BLE001
        out["beat"] = None
    try:
        m = json.loads((_ROOT / "_ops/state/pulse/memory-read-latest.json")
                       .read_text(encoding="utf-8"))
        out["memread"] = (m.get("status"), m.get("memory_reads_per_cycle"),
                          m.get("readback"))
    except Exception:  # noqa: BLE001
        out["memread"] = None
    con = sqlite3.connect(f"file:{_ROOT / '_ops/state/spine/spine.db'}?mode=ro",
                          uri=True)
    out["tg_events"] = con.execute(
        "SELECT COUNT(*) FROM events WHERE domain='telegram'").fetchone()[0]
    out["sc_events"] = con.execute(
        "SELECT COUNT(*) FROM events WHERE event_time_source="
        "'provider_server_created'").fetchone()[0]
    con.close()
    p = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
    out["probe"] = json.loads(p.read_text(encoding="utf-8")).get("verdict") \
        if p.exists() else "NOT_RUN"
    return out


def main(force: bool = False) -> str:
    s = snapshot()
    summary = (f"🐙 beat={s['beat']} · telegram_events={s['tg_events']} · "
               f"server_created={s['sc_events']} · probe={s['probe']} · "
               f"memread={s['memread']}")
    key = hashlib.sha256(summary.encode()).hexdigest()[:12]
    prev = {}
    if STATE_FILE.exists():
        try:
            prev = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
    changed = prev.get("key") != key
    age = time.time() - prev.get("pushed_at", 0)
    important = (s["tg_events"] > (prev.get("tg_events") or 0)
                 or s["sc_events"] > (prev.get("sc_events") or 0))
    if force or changed or important or age > PUSH_MIN_INTERVAL_S:
        token, chat = _env()
        ok = _send(token, chat, summary)
        STATE_FILE.write_text(json.dumps(
            {"key": key, "pushed_at": time.time(), **s}), encoding="utf-8")
        return f"PUSHED({ok}): {summary}"
    return f"no-push (unchanged, age={int(age // 60)}m): {summary}"


if __name__ == "__main__":
    print(main(force="--force" in sys.argv))
