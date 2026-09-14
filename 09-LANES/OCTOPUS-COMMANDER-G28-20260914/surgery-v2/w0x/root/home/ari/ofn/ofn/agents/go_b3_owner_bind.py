#!/usr/bin/env python3
"""go_b3_owner_bind.py — dedicated GO-B3 confirm binder (GO-W24).

SEPARATE from revenue-drive owner_reply.py / APPROVE_PAT / MONEY-BATCH.
Never paste secrets. Never customer send. Never GO-B4.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

STATE = Path(os.environ.get("GO_B3_BIND_STATE", str(Path.home() / "ofn/state/owner_dialogue")))
SECRETS = Path.home() / ".config/ofn/secrets.env"
REGISTRY = STATE / "go_b3_pending_registry.json"
SPOOL = STATE / "go_b3_tg_spool.jsonl"
OFFSET = STATE / "go_b3_tg_offset.txt"
DECISIONS = STATE / "owner_decision.v1.jsonl"
REJECT_PREFIXES = ("261e479c", "d7981504", "c0757788", "26cc7d4c")
CONFIRM_PAT = re.compile(r"(confirm(?:ing)?|\bpi\b|4\s*\+\s*1|تایید|تأیید)", re.I)
HEX_PAT = re.compile(r"\b([a-f0-9]{8,64})\b", re.I)
BATCH_PAT = re.compile(r"(\bpi\b.*4\s*\+\s*1|4\s*\+\s*1.*\bpi\b|all\s*five|batch)", re.I)


def _secrets() -> dict:
    d = {}
    try:
        for ln in SECRETS.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                d[k.strip()] = v.strip().strip('"')
    except Exception:
        pass
    for k in ("OFN_BOT_TOKEN_OWNER", "OFN_OWNER_USER_IDS"):
        if os.environ.get(k):
            d[k] = os.environ[k]
    return d


def owner_chat_ids() -> list[str]:
    s = _secrets()
    return [c.strip() for c in (s.get("OFN_OWNER_USER_IDS") or "").split(",") if c.strip()]


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")


def pending_rows(reg: dict) -> list[dict]:
    return [r for r in reg.get("requests", []) if r.get("status") == "pending"]


def resolve_hash(prefix: str, rows: list[dict]):
    p = prefix.lower()
    if any(p.startswith(rp) or rp.startswith(p[:8]) for rp in REJECT_PREFIXES):
        return None, "REJECT_AMBIGUOUS"
    hits = [
        r
        for r in rows
        if r["payload_sha256"].startswith(p) or p.startswith(r["payload_sha256"][: len(p)])
    ]
    if len(hits) == 1:
        return hits[0]["payload_sha256"], "OK"
    return None, "REJECT_AMBIGUOUS"


def emit_decision(verdict: str, bound, source_text: str, extra=None) -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    body = {
        "schema": "owner_decision.v1",
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": verdict,
        "bound_request_payload_sha256": bound,
        "hold_external": True,
        "external_effects": 0,
        "telegram_chat_class": "owner",
        "source_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "go": "GO-W24",
        "customer_send": False,
        "go_b4": False,
    }
    if extra:
        body.update(extra)
    with DECISIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False) + "\n")
    return body


def mark_used(reg: dict, payload_sha: str) -> None:
    for r in reg["requests"]:
        if r["payload_sha256"] == payload_sha:
            r["status"] = "consumed"
            r["consumed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_owner_text(text: str, reg=None) -> dict:
    reg = reg or load_registry()
    rows = pending_rows(reg)
    text = (text or "").strip()
    if not text:
        return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "empty"})

    if BATCH_PAT.search(text) and CONFIRM_PAT.search(text):
        batch = next((r for r in rows if r.get("request_id") == "gob3-INDEX-BATCH"), None)
        if not batch:
            return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "batch_not_pending"})
        mark_used(reg, batch["payload_sha256"])
        save_registry(reg)
        return emit_decision(
            "ACK_BATCH", batch["payload_sha256"], text, {"request_id": batch["request_id"]}
        )

    if not CONFIRM_PAT.search(text):
        return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "no_confirm_language"})

    hexes = HEX_PAT.findall(text)
    if not hexes:
        return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "confirm_without_hash"})

    hexes = sorted(set(h.lower() for h in hexes), key=len, reverse=True)
    for h in hexes:
        bound, st = resolve_hash(h, rows)
        if st == "OK" and bound:
            label = next(r.get("card") for r in rows if r["payload_sha256"] == bound)
            if re.search(r"\bbcs\b", text, re.I) and label == "SMARTER-COMMUNITIES":
                return emit_decision(
                    "REJECT_AMBIGUOUS", None, text, {"reason": "label_hash_mismatch", "card": label}
                )
            if re.search(r"\bbright\b", text, re.I) and label != "BRIGHT-AND-DUGGAN":
                return emit_decision(
                    "REJECT_AMBIGUOUS", None, text, {"reason": "label_hash_mismatch", "card": label}
                )
            mark_used(reg, bound)
            save_registry(reg)
            return emit_decision("ACK_SEEN", bound, text, {"card": label})
    return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "hash_unresolved", "hexes": hexes[:5]})


def spool_append(obj: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with SPOOL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def poll_telegram_once() -> dict:
    s = _secrets()
    token = s.get("OFN_BOT_TOKEN_OWNER") or ""
    allow = set(owner_chat_ids())
    if not token or not allow:
        return {"ok": False, "reason": "not-armed"}
    offset = 0
    if OFFSET.exists():
        try:
            offset = int(OFFSET.read_text().strip() or "0")
        except ValueError:
            offset = 0
    url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=0&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "reason": type(e).__name__}
    if not data.get("ok"):
        return {"ok": False, "reason": "tg_not_ok"}
    n = 0
    max_upd = offset
    for upd in data.get("result") or []:
        max_upd = max(max_upd, int(upd.get("update_id", 0)) + 1)
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id") or "")
        if chat_id not in allow:
            continue
        text = msg.get("text") or ""
        obj = {
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "telegram_chat_class": "owner",
            "update_id": upd.get("update_id"),
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "text": text,
        }
        spool_append(obj)
        parse_owner_text(text)
        n += 1
    OFFSET.write_text(str(max_upd), encoding="utf-8")
    return {"ok": True, "spooled": n, "offset": max_upd}


def main(argv: list[str]) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        print(json.dumps({"ok": False, "reason": "missing_registry"}))
        return 2
    if len(argv) >= 2 and argv[1] == "parse":
        text = argv[2] if len(argv) > 2 else sys.stdin.read()
        print(json.dumps(parse_owner_text(text), ensure_ascii=False))
        return 0
    if len(argv) >= 2 and argv[1] == "poll":
        print(json.dumps(poll_telegram_once(), ensure_ascii=False))
        return 0
    print(json.dumps({"ok": True, "cmds": ["parse <text>", "poll"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
