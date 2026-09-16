#!/usr/bin/env python3
"""calltoday_send.py — CALL-TODAY card (owner channel), owner-approved 2026-09-05.

Guards identical to traffic1_send.py: HALT, BUDGET daily cap, GOV-V8 L1
external-action counter (10/day), getMe preflight, one sendMessage, LEDGER row
+ dispatch receipt. Token from the existing store; never printed. SECRETS_TOUCHED=0.

Owner authorization: structured Q&A 2026-09-05 (~10:15Z), answer «بفرست» —
L0-permitted owner-channel card (GOV-V8 ladder row L0: ارسال کارت مالک از ۱۳۸).
Template = AskUserQuestion preview shown with the vote (typo «پونزینگ»→«پینتینگ»
fixed; lead set/phones identical — delta recorded here per receipt discipline).
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HALT = ROOT / "HALT"
BUDGET = ROOT / "BUDGET.json"
LEDGER = ROOT / "ops" / "LEDGER.jsonl"
RECEIPTS = ROOT / "ops" / "receipts"
EXT_COUNTER = ROOT / "ops" / "external-actions-counter.json"
EXT_CAP = 10
STORE = Path.home() / ".config" / "ofn" / "secrets.env"
CHANNEL = "-1004440663399"
CARD_NO = "1"
RECEIPT = RECEIPTS / f"CALLTODAY-{CARD_NO}-RECEIPT.json"

TEXT = (
    "☎️ CALL TODAY — 5 لید برتر (پینتینگ B2B)\n"
    "\n"
    "1. Strata Choice [10/10] — 1300 322 213\n"
    "   (40+ سال، 30,000+ مالک)\n"
    "2. Whelan Property [9/10] — 02 9219 4111\n"
    "3. Excel Bldg Mgmt [9/10] — (02) 9518 8577\n"
    "4. National FM [9/10] — 1300 820 330\n"
    "5. Montano Strata [9/10] — (02) 9053 7637\n"
    "   (هم‌گروه IB Property — یک پیچ IB Group)\n"
    "\n"
    "مسیر پنل/تندر: Downer 1800 369 637 (Subcontractor)\n"
    "\n"
    "--- ارسال خودکار با رسید OCTOPUS ---"
)


def abort(code: str, detail: str = "") -> None:
    print(f"CALLTODAY_ABORT code={code}" + (f" detail={detail}" if detail else ""))
    sys.exit(2)


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
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8", "replace")), None
        except Exception:
            return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, str(getattr(e, "reason", e))
    except OSError as e:
        return None, type(e).__name__


def main() -> None:
    if HALT.exists():
        abort("KILL_SWITCH_PRESENT")
    if RECEIPT.exists():
        abort("ALREADY_DONE", "CALLTODAY card 1 receipt exists; one send only")
    try:
        budget = json.loads(BUDGET.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        abort("BUDGET_MISSING")
    today = time.strftime("%Y-%m-%d")
    if budget.get("date") != today:
        budget["date"] = today
        budget["messages_sent_today"] = 0
    sent = int(budget.get("messages_sent_today", 0))
    cap = int(budget.get("daily_message_cap", 0))
    if sent >= cap:
        abort("BUDGET_MESSAGE_CAP_REACHED", f"{sent}/{cap}")

    try:
        ext = json.loads(EXT_COUNTER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ext = {"date": today, "count": 0}
    if ext.get("date") != today:
        ext = {"date": today, "count": 0}
    if int(ext.get("count", 0)) >= EXT_CAP:
        abort("EXTERNAL_ACTION_CAP_REACHED", f"{ext.get('count')}/{EXT_CAP}")

    s = kv(STORE)
    token = s.get("OFN_BOT_TOKEN_OWNER", "")
    if not token:
        abort("MISSING_ENV", "token")
    me, err = tg(token, "getMe", {})
    if err:
        abort("NETWORK", err)
    if not me.get("ok"):
        abort("TOKEN_UNAUTHORIZED", str(me.get("description") or "")[:120])

    res, err = tg(token, "sendMessage", {
        "chat_id": CHANNEL, "text": TEXT,
        "disable_web_page_preview": False,
    })
    if err:
        abort("SEND_REJECTED", err)
    if not res.get("ok"):
        abort("SEND_REJECTED", str(res.get("description") or "api-refused")[:250])
    message_id = (res.get("result") or {}).get("message_id")

    payload_sha = hashlib.sha256(TEXT.encode("utf-8")).hexdigest()
    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    row = {
        "kind": "external_effect", "traffic": "CALL-TODAY", "card": CARD_NO,
        "ts_utc": now_utc, "host": socket.gethostname(),
        "channel": "telegram_channel", "chat_id": CHANNEL,
        "message_id": message_id, "payload_sha256": payload_sha,
        "utm": "utm_campaign=calltoday&utm_content=painting-b2b",
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    line = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    with LEDGER.open("ab") as fh:
        fh.write(line)
    row_sha = hashlib.sha256(line).hexdigest()

    budget["messages_sent_today"] = sent + 1
    BUDGET.write_text(json.dumps(budget, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    ext["count"] = int(ext.get("count", 0)) + 1
    EXT_COUNTER.write_text(json.dumps(ext, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "dispatch_receipt.v1",
        "traffic": "CALL-TODAY", "card": CARD_NO,
        "owner_go": "owner vote 2026-09-05 structured Q&A: «بفرست» (L0 "
                    "owner-channel card; L1 leg designated painting-B2B same vote)",
        "template_note": "text identical to approved preview except typo "
                         "پونزینگ→پینتینگ; lead set + phones unchanged",
        "ts_utc": now_utc, "host": socket.gethostname(),
        "channel": "telegram_channel", "chat_id": CHANNEL,
        "message_id": message_id, "payload_sha256": payload_sha,
        "ledger_row_sha256": row_sha,
        "budget_after": {"date": budget["date"],
                         "messages_sent_today": sent + 1,
                         "daily_message_cap": cap},
        "counters": {"EXTERNAL_EFFECTS_PERFORMED": 1,
                     "LEDGER_ROWS_WRITTEN": 1,
                     "SECRETS_TOUCHED": 0},
        "rollback": (f"delete last row of {LEDGER} (sha {row_sha}) + delete "
                     f"{RECEIPT} + restore budget counter to {sent}"),
    }
    tmp = RECEIPT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    tmp.replace(RECEIPT)
    print(f"CALLTODAY_SENT message_id={message_id}")
    print("EXTERNAL_EFFECTS_PERFORMED=1")
    print("LEDGER_ROWS_WRITTEN=1")
    print("SECRETS_TOUCHED=0")
    print(f"RECEIPT={RECEIPT}")


if __name__ == "__main__":
    main()
