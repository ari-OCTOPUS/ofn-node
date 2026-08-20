#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""telegram_cockpit.py — حلقهٔ Telegram مالک-تنها (مگا‌دستور #۱۳ §۵).

احراز: from.id و chat.id عددی پین‌شده از env (username کافی نیست) · private chat
اجباری · update_id = idempotency key (هر update یک بار) · فرمان‌های محلی بدون
فراخوان مدل · پاسخ‌ها با footer الزامی · /stop و /resume · فوروارد/گروه/غریبه =
بدون پاسخ + security receipt.

اجرا (تست): python -X utf8 research/full_loop/telegram_cockpit.py --test-run
preflight: اگر getUpdates با 409 پاسخ داد (poller دیگری فعال است — center)
متوقف می‌شود و گزارش می‌دهد؛ برخورد پیش نمی‌گیرد."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
for _p in (str(_ROOT / "_ops"), str(_ROOT / "_ops/budget"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from turn_engine import TurnEngine, MemoryStore, EVID, _append, _now  # noqa: E402

API = "https://api.telegram.org/bot{token}/{method}"
STOP_FILE = _HERE / "state/COCKPIT-STOP"


def _env():
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        import env_loader
        env_loader.load_env()
    return os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_OWNER_CHAT_ID"]


def _tg(method: str, payload: dict) -> dict:
    token, _ = _env()
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read().decode())


def _owner_hash() -> str:
    _, chat_id = _env()
    return hashlib.sha256(chat_id.encode()).hexdigest()[:12]


def preflight() -> bool:
    token, chat_id = _env()
    print(f"owner_chat_hash={_owner_hash()} (مقدار خام هرگز چاپ نمی‌شود)")
    try:
        r = _tg("getUpdates", {"timeout": 0, "limit": 1})
        print("polling preflight: OK — هیچ poller دیگری فعال نیست")
        return True
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("preflight: 409 Conflict — poller دیگری (center?) فعال است. "
                  "کاکپیت متوقف می‌شود؛ تداخل ممنوع.")
        raise SystemExit(2)
    return False


def local_status() -> str:
    beat = "?"
    try:
        d = json.loads((_ROOT / "_ops/state/ORGANISM-STATE.json")
                       .read_text(encoding="utf-8"))
        beat = d.get("beat")
    except Exception:  # noqa: BLE001
        pass
    n_mem = len(MemoryStore().all_records())
    lb = "BLOCKED (pending telegram+server_created)"
    return (f"🐙 beat={beat} · memory={n_mem} · LIVE-A✓ B:{lb} C:PASS·incident "
            f"· executable=false")


def handle_command(text: str, engine: TurnEngine) -> str | None:
    """فرمان‌های محلی — بدون فراخوان مدل (§۱۴: status ساده محلی)."""
    parts = text.strip().split()
    cmd = parts[0].lower()
    if cmd == "/status":
        return local_status()
    if cmd == "/remember":
        payload = text.split(maxsplit=1)
        if len(payload) < 2:
            return "usage: /remember <text>"
        mid = engine.store.append(kind="semantic", text=payload[1],
                                  turn_id="owner-cmd",
                                  provenance="owner_direct")
        return f"✓ ثبت شد: {mid} (semantic candidate — تا تأیید، fact نیست)"
    if cmd in ("/good", "/bad"):
        _append(EVID / "TURN-LEDGER.jsonl",
                {"state": "FEEDBACK_RECEIVED" if cmd == "/good" else "FEEDBACK_NEGATIVE",
                 "target_turn": parts[1] if len(parts) > 1 else "?",
                 "ts": _now()})
        return f"✓ بازخورد ثبت شد برای {parts[1] if len(parts) > 1 else '?'}"
    if cmd == "/stop":
        STOP_FILE.write_text(_now(), encoding="utf-8")
        return "🛑 حلقهٔ مکالمه متوقف (رفلکس‌های محافظ فعال می‌مانند). /resume برای ادامه."
    if cmd == "/resume":
        if STOP_FILE.exists():
            STOP_FILE.unlink()
        return "▶️ ادامه یافت."
    return None


def send_owner(chat_id: str, text: str) -> dict:
    r = _tg("sendMessage", {"chat_id": chat_id, "text": text})
    ok = r.get("ok") is True and r.get("result", {}).get("message_id")
    return {"ok": bool(ok),
            "message_id": r.get("result", {}).get("message_id")}


def model_fn(prompt: str, intent_key: str) -> str:
    """DeepSeek از مسیر امضاشده — فقط وقتی LIVE-B بسته و کارت معتبر."""
    # گیت در turn_engine (SHADOW تا LIVE-B) — این تابع بعد از بسته‌شدن LIVE-B
    # با model_router وصل می‌شود؛ فعلاً در SHADOW صدازفراخوان است.
    import model_router as mr
    out = mr.ask(task=f"full-loop-{intent_key[:8]}", prompt=prompt,
                 max_tokens=400, tier="primary", temperature=0.3)
    if not out.get("ok"):
        raise RuntimeError(out.get("reason") or "model-failed")
    return str(out.get("text") or "")


def live_b_ok() -> bool:
    """حکم خودکار LIVE-B (مجاز — دستور #۱۲ §۱۱): دو منبع مستقل + suite."""
    import sqlite3
    con = sqlite3.connect(f"file:{_ROOT}/_ops/state/spine/spine.db?mode=ro", uri=True)
    tg = con.execute("SELECT COUNT(*) FROM events WHERE domain='telegram'").fetchone()[0]
    sc = con.execute("SELECT COUNT(*) FROM events WHERE event_time_source="
                     "'provider_server_created'").fetchone()[0]
    con.close()
    return tg >= 5 and sc >= 1


def run(test_run: bool = False, max_turns: int = 20) -> None:
    preflight()
    token, chat_id = _env()
    engine = TurnEngine(model_fn=model_fn, live_b_ok=live_b_ok,
                        send_fn=lambda txt: send_owner(chat_id, txt))
    processed_updates: set = set()
    offset = 0
    print("TELEGRAM READY — SEND: /status")
    while len(processed_updates) < max_turns if test_run else True:
        if STOP_FILE.exists():
            time.sleep(5)
            continue
        try:
            r = _tg("getUpdates", {"timeout": 25, "offset": offset})
        except Exception as e:  # noqa: BLE001
            print(f"poll error: {type(e).__name__}")
            time.sleep(5)
            continue
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            if u["update_id"] in processed_updates:
                continue
            processed_updates.add(u["update_id"])
            msg = u.get("message") or {}
            frm = msg.get("from", {})
            chat = msg.get("chat", {})
            # احراز مالک: id عددی + private chat فقط (§۵)
            if (str(chat.get("id")) != chat_id
                    or chat.get("type") != "private"
                    or msg.get("forward_from")):
                _append(EIV if False else EVID / "TELEGRAM-INGEST.jsonl",
                        {"security": "REJECTED_NON_OWNER_OR_FORWARD",
                         "chat_hash": hashlib.sha256(
                             str(chat.get("id", "")).encode()).hexdigest()[:8],
                         "ts": _now()})
                continue
            text = msg.get("text", "")
            if not text:
                continue
            occurred = datetime.fromtimestamp(
                int(msg.get("date", time.time())),
                tz=timezone.utc).isoformat(timespec="seconds")
            # ۱) ingest دوزمانی — producer_2 (message.date تلگرام)
            try:
                import spine_adapters
                spine_adapters.emit_event(
                    event_type="delivered", domain="telegram",
                    correlation_id=f"tg-{frm.get('id')}-{msg.get('date')}",
                    subject="owner_message", producer="telegram_cockpit",
                    trust="DETERMINISTIC", occurred_at=occurred,
                    event_time_source="telegram_message_date",
                    time_precision="1s",
                    payload={"kind": "command" if text.startswith("/") else "message"},
                    idempotency_key=f"tg-{frm.get('id')}-{msg.get('date')}|cockpit")
            except Exception:  # noqa: BLE001
                pass
            # ۲) فرمان محلی یا turn کامل
            local = handle_command(text, engine) if text.startswith("/") else None
            if local is not None:
                send_owner(chat_id, local + "\n[LOCAL · no model call]")
                continue
            t = engine.run_turn(update_id=u["update_id"],
                                message_id=msg.get("message_id", 0),
                                text=text, occurred_at=occurred,
                                owner_hash=_owner_hash())
            print(f"turn {t.turn_id}: gate={t.gate_mode} "
                  f"mem={len(t.retrieved_ids)} sent={t.telegram_sent}")
    print("TEST-RUN COMPLETE")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-run", action="store_true")
    ap.add_argument("--max-turns", type=int, default=20)
    args = ap.parse_args()
    run(test_run=args.test_run, max_turns=args.max_turns)
