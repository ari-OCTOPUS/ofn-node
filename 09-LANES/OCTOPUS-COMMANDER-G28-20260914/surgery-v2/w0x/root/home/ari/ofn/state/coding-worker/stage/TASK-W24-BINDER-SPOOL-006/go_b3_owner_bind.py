#!/usr/bin/env python3
"""go_b3_owner_bind.py — dedicated GO-B3 confirm binder (GO-W24).

SEPARATE from revenue-drive owner_reply.py / APPROVE_PAT / MONEY-BATCH.
Never paste secrets. Never customer send. Never GO-B4.

INPUT CONTRACT (owner directive 2026-09-13, wire W24-GLASS-GETUPDATES)
---------------------------------------------------------------------
`glass_runner.py` is the SOLE Telegram `getUpdates` poller for the owner bot.
It durably spools every allow-listed owner message to::

    state/revenue-drive/tg-inbox.jsonl      ({"chat","text","at"} per line)

This binder NEVER calls `getUpdates`. A second poller on the same bot both
starves and can 409-conflict the sole poller, so the binder CONSUMES that
spool instead, through its own durable cursor:

    glass spool -> B3 spool (durable, fsync) -> resolve -> owner_decision.v1
                                            -> cursor advance (fsync)

Ordering is durable-first: the B3 spool append is flushed before the cursor
moves, so a crash mid-cycle re-reads the message rather than losing it. A
re-read can never double-bind, because every emitted decision carries
`source_text_sha256` and an already-bound text is skipped.

Fail-closed dispositions (never guess which card was meant):
  REJECT_WRONG_SENDER  chat not in the owner allowlist
  REJECT_MALFORMED     spool line unparseable / missing text
  REJECT_REPLAY        this exact text was already bound
  REJECT_EXPIRED       the only matching request is past `expires_at`
  REJECT_AMBIGUOUS     no confirm language, no hash, unknown or multi-match hash
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request  # noqa: F401  (kept for import compatibility; unused)
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
STATE = Path(os.environ.get("GO_B3_BIND_STATE", str(HOME / "ofn/state/owner_dialogue")))
SECRETS = HOME / ".config/ofn/secrets.env"
REGISTRY = STATE / "go_b3_pending_registry.json"
SPOOL = STATE / "go_b3_tg_spool.jsonl"
CURSOR_DIR = STATE / "cursor"          # G19: one cursor PER spool, never shared
CURSOR = STATE / "go_b3_glass_cursor.txt"   # legacy single-cursor path (read once)
OFFSET = STATE / "go_b3_tg_offset.txt"
DECISIONS = STATE / "owner_decision.v1.jsonl"
# sole-poller output; overridable only for isolated tests
# G8: the B3 lane is the dedicated spool written by the producer router.
# The revenue spool stays as a FALLBACK so this binder is never wired to a
# file nothing writes; the fallback disappears once the router is live.
GLASS_SPOOL = Path(os.environ.get(
    "GO_B3_GLASS_SPOOL", str(HOME / "ofn/state/owner_dialogue/go_b3_inbox.jsonl")))
LEGACY_GLASS_SPOOL = Path(str(HOME / "ofn/state/revenue-drive/tg-inbox.jsonl"))


def active_spool() -> Path:
    """B3 lane if it exists, else the legacy revenue spool (forward-compatible)."""
    return GLASS_SPOOL if GLASS_SPOOL.exists() else LEGACY_GLASS_SPOOL

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


def _fsync_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def _parse_ts(s) -> datetime | None:
    try:
        return datetime.strptime(str(s), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")


def pending_rows(reg: dict, now: datetime | None = None) -> list[dict]:
    """Pending AND unexpired. Expiry is a fail-closed gate, not a hint."""
    now = now or datetime.now(timezone.utc)
    out = []
    for r in reg.get("requests", []):
        if r.get("status") != "pending":
            continue
        exp = _parse_ts(r.get("expires_at"))
        if exp is not None and now > exp:
            continue
        out.append(r)
    return out


def expired_rows(reg: dict, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    out = []
    for r in reg.get("requests", []):
        if r.get("status") != "pending":
            continue
        exp = _parse_ts(r.get("expires_at"))
        if exp is not None and now > exp:
            out.append(r)
    return out


def resolve_hash(prefix: str, rows: list[dict], expired: list[dict] | None = None):
    p = prefix.lower()
    if any(p.startswith(rp) or rp.startswith(p[:8]) for rp in REJECT_PREFIXES):
        return None, "REJECT_AMBIGUOUS"
    for pool, tag in ((rows, "OK"), (expired or [], "REJECT_EXPIRED")):
        hits = [
            r
            for r in pool
            if r["payload_sha256"].startswith(p) or p.startswith(r["payload_sha256"][: len(p)])
        ]
        if len(hits) == 1:
            return (hits[0]["payload_sha256"], tag) if tag == "OK" else (None, tag)
        if len(hits) > 1 and tag == "OK":
            return None, "REJECT_AMBIGUOUS"
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
        f.flush()
        os.fsync(f.fileno())
    return body


def mark_used(reg: dict, payload_sha: str) -> None:
    for r in reg["requests"]:
        if r["payload_sha256"] == payload_sha:
            r["status"] = "consumed"
            r["consumed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_owner_text(text: str, reg=None) -> dict:
    reg = reg or load_registry()
    rows = pending_rows(reg)
    expired = expired_rows(reg)
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

    expired_seen = False
    hexes = sorted(set(h.lower() for h in hexes), key=len, reverse=True)
    for h in hexes:
        bound, st = resolve_hash(h, rows, expired)
        if st == "REJECT_EXPIRED":
            expired_seen = True
            continue
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
    if expired_seen:
        return emit_decision("REJECT_EXPIRED", None, text,
                             {"reason": "request_expired", "hexes": hexes[:5]})
    return emit_decision("REJECT_AMBIGUOUS", None, text, {"reason": "hash_unresolved", "hexes": hexes[:5]})


def spool_append(obj: dict) -> None:
    """Durable append to the DEDICATED B3 spool (never the revenue spool)."""
    STATE.mkdir(parents=True, exist_ok=True)
    with SPOOL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def bound_text_hashes() -> set[str]:
    """Every source_text_sha256 already BOUND. The idempotency key.

    G21: a persistence FAILURE is excluded. It is recorded as a disposition (so the
    message is traceable) but it must not poison the key, or a message that failed to
    store could never be consumed even after the store recovers.
    """
    if not DECISIONS.exists():
        return set()
    out = set()
    for ln in DECISIONS.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(ln)
        except json.JSONDecodeError:
            continue
        h = row.get("source_text_sha256")
        if h and row.get("verdict") != "REJECT_PERSIST_FAILED":
            out.add(h)
    return out


def cursor_path(spool: Path) -> Path:
    """Cursor is keyed by spool path: the active lane can switch (B3 lane <->
    legacy fallback) and an index valid for one file is not valid for another."""
    key = hashlib.sha256(str(spool).encode("utf-8")).hexdigest()[:12]
    return CURSOR_DIR / ("glass-%s.txt" % key)


def read_cursor(spool: Path) -> int:
    p = cursor_path(spool)
    if not p.exists() and CURSOR.exists() and str(spool).endswith("tg-inbox.jsonl"):
        p = CURSOR                      # adopt the legacy cursor for the legacy spool
    try:
        return int(p.read_text(encoding="utf-8").strip() or "0")
    except (OSError, ValueError):
        return 0


def consume_glass_spool_once() -> dict:
    """Consume NEW lines of the glass spool. No network, no getUpdates, ever."""
    allow = set(owner_chat_ids())
    stats = {"schema": "octopus.go-b3-consume.v1", "ok": True, "read": 0, "spooled": 0,
             "bound": 0, "skipped_replay": 0, "rejected": 0, "persist_failed": 0,
             "cursor": None}
    spool_path = active_spool()
    stats["spool"] = str(spool_path)
    cur_path = cursor_path(spool_path)
    stats["cursor"] = read_cursor(spool_path)
    if not spool_path.exists():
        stats["reason"] = "glass_spool_absent"
        return stats
    lines = spool_path.read_text(encoding="utf-8", errors="replace").splitlines()
    cursor = stats["cursor"]
    if cursor > len(lines):
        stats["reason"] = "cursor_ahead_of_spool"
        return stats
    already = bound_text_hashes()
    for i in range(cursor, len(lines)):
        raw = lines[i].strip()
        if not raw:
            _fsync_write(cur_path, str(i + 1))
            continue
        stats["read"] += 1
        try:
            d = json.loads(raw)
            chat = str(d.get("chat", ""))
            text = str(d.get("text", "") or "")
        except json.JSONDecodeError:
            emit_decision("REJECT_MALFORMED", None, raw,
                          {"reason": "spool_line_not_json", "line_index": i})
            stats["rejected"] += 1
            _fsync_write(cur_path, str(i + 1))
            continue
        if not text:
            emit_decision("REJECT_MALFORMED", None, raw,
                          {"reason": "spool_line_empty_text", "line_index": i})
            stats["rejected"] += 1
            _fsync_write(cur_path, str(i + 1))
            continue
        tsha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # durable-first: record in the B3 spool before anything else can move on
        try:
            spool_append({"at": d.get("at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "telegram_chat_class": "owner",
                          "chat": chat, "text_sha256": tsha, "text": text[:600],
                          "source": "glass_spool", "line_index": i})
        except OSError as exc:
            # G20: a persistence failure used to escape as a raw traceback - the cycle
            # died with no disposition for this message. Record it, and STOP: the cursor
            # must never advance past a line that was not durably written.
            stats["persist_failed"] = stats.get("persist_failed", 0) + 1
            stats["reason"] = "spool_write_failed"
            stats["persist_error"] = type(exc).__name__
            try:
                emit_decision("REJECT_PERSIST_FAILED", None, text,
                              {"reason": "spool_write_failed", "line_index": i,
                               "error": type(exc).__name__})
            except OSError:
                pass
            break
        stats["spooled"] += 1
        if allow and chat not in allow:
            emit_decision("REJECT_WRONG_SENDER", None, text,
                          {"reason": "chat_not_in_owner_allowlist", "line_index": i})
            stats["rejected"] += 1
            _fsync_write(cur_path, str(i + 1))
            continue
        if tsha in already:
            emit_decision("REJECT_REPLAY", None, text,
                          {"reason": "text_already_bound", "line_index": i})
            stats["skipped_replay"] += 1
            _fsync_write(cur_path, str(i + 1))
            continue
        body = parse_owner_text(text)
        already.add(tsha)
        if str(body.get("verdict", "")).startswith(("ACK_", "RESOLVE")):
            stats["bound"] += 1
        else:
            stats["rejected"] += 1
        _fsync_write(cur_path, str(i + 1))
    stats["cursor"] = read_cursor(spool_path)
    return stats


def main(argv: list[str]) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        print(json.dumps({"ok": False, "reason": "missing_registry"}))
        return 2
    if len(argv) >= 2 and argv[1] == "parse":
        text = argv[2] if len(argv) > 2 else sys.stdin.read()
        print(json.dumps(parse_owner_text(text), ensure_ascii=False))
        return 0
    if len(argv) >= 2 and argv[1] in ("poll", "consume"):
        # "poll" kept as an alias so the deployed unit keeps working unchanged
        print(json.dumps(consume_glass_spool_once(), ensure_ascii=False))
        return 0
    print(json.dumps({"ok": True, "cmds": ["consume (default)", "parse <text>"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
