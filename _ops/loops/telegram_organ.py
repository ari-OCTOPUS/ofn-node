# -*- coding: utf-8 -*-
"""Telegram as a loop-closure organ — dry_run by default.

Never live-sends unless LIVE-TELEGRAM.flag exists AND transport is injected.
Idempotent on update_id. Allowlist. Redaction. Digest+rate-limit.
Business retry is separate from delivery retry.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

# Telegram bot tokens look like 123456789:AA... — never log the raw form.
_BOT_TOKEN = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}")
_KEYISH = re.compile(
    r"(?i)(api[_-]?key|secret|token|authorization)([\"'\s:=]+)([^\s\"']{8,})"
)
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")

LIVE_FLAG_NAME = "LIVE-TELEGRAM.flag"
DEFAULT_RATE_S = 3600.0
MAX_LOOPS_IN_DIGEST = 3


def _canonical_live_flag_path() -> Path:
    """Prefer _ops/LIVE-TELEGRAM.flag (SoT unlock token), not state_dir."""
    try:
        return Path(__file__).resolve().parents[1] / LIVE_FLAG_NAME
    except Exception:  # noqa: BLE001
        return Path(LIVE_FLAG_NAME)


def _flag_enabled(state_dir: Path) -> bool:
    """True when canonical ops flag enabled, else legacy state_dir flag file."""
    try:
        import sys as _sys
        _tc = str(Path(__file__).resolve().parents[1] / "telegram_center")
        if _tc not in _sys.path:
            _sys.path.insert(0, _tc)
        import live_telegram_gate as _gate  # type: ignore
        return bool(_gate.live_mode_allowed())
    except Exception:
        pass
    if (Path(state_dir) / LIVE_FLAG_NAME).is_file():
        return True
    canon = _canonical_live_flag_path()
    if canon.is_file():
        try:
            raw = json.loads(canon.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return bool(raw.get("enabled", True))
        except (OSError, ValueError):
            return True
    return False


def redact(text: str) -> str:
    s = str(text or "")
    s = _BOT_TOKEN.sub("[REDACTED_BOT_TOKEN]", s)
    s = _BEARER.sub("Bearer [REDACTED]", s)
    s = _KEYISH.sub(r"\1\2[REDACTED]", s)
    return s


def chat_fingerprint(chat_id: Any) -> str:
    return hashlib.sha256(str(chat_id).encode("utf-8")).hexdigest()[:12]


class TelegramOrgan:
    """Outbox + ingest. Transport is optional and never the Telegram HTTP API
    unless the caller injects one after LIVE flag + safety tests."""

    def __init__(
        self,
        state_dir: Path,
        *,
        allowlist: set[int] | None = None,
        live: bool = False,
        transport: Callable[[int, str], bool] | None = None,
        rate_s: float = DEFAULT_RATE_S,
        now: Callable[[], float] | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.allowlist = set(allowlist or ())
        self.live = bool(live) and _flag_enabled(self.state_dir)
        self.transport = transport
        self.rate_s = float(rate_s)
        self._now = now or time.time
        self.seen_path = self.state_dir / "seen-update-ids.json"
        self.outbox_path = self.state_dir / "telegram-outbox.jsonl"
        self.cursor_path = self.state_dir / "telegram-cursor.json"
        self.nonces_path = self.state_dir / "callback-nonces.json"

    def _load_json(self, path: Path, default):
        try:
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default
        return default

    def _save_json(self, path: Path, obj) -> None:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def seen_ids(self) -> set[int]:
        raw = self._load_json(self.seen_path, {"ids": []})
        return {int(x) for x in (raw.get("ids") or []) if str(x).lstrip("-").isdigit()}

    def _mark_seen(self, update_id: int) -> None:
        ids = self.seen_ids()
        ids.add(int(update_id))
        # keep last 4000
        keep = sorted(ids)[-4000:]
        self._save_json(self.seen_path, {"ids": keep})

    def nonces(self) -> dict:
        d = self._load_json(self.nonces_path, {})
        return d if isinstance(d, dict) else {}

    def issue_nonce(self, card_id: str) -> str:
        n = hashlib.sha256(f"{card_id}:{self._now()}".encode()).hexdigest()[:16]
        d = self.nonces()
        d[card_id] = {"nonce": n, "ts": self._now()}
        self._save_json(self.nonces_path, d)
        return n

    def accept_callback(self, card_id: str, nonce: str) -> dict[str, Any]:
        d = self.nonces()
        row = d.get(card_id) or {}
        if not row or row.get("nonce") != nonce:
            return {"ok": False, "reason": "stale_or_unknown_nonce"}
        d.pop(card_id, None)
        self._save_json(self.nonces_path, d)
        return {"ok": True, "card_id": card_id}

    def _chat_id(self, update: dict) -> int | None:
        msg = update.get("message") or {}
        cb = update.get("callback_query") or {}
        chat = (msg.get("chat") or {}) or ((cb.get("message") or {}).get("chat") or {})
        cid = chat.get("id")
        if cid is None:
            cid = (cb.get("from") or {}).get("id") or (msg.get("from") or {}).get("id")
        try:
            return int(cid) if cid is not None else None
        except (TypeError, ValueError):
            return None

    def ingest_update(self, update: dict) -> dict[str, Any]:
        uid = update.get("update_id")
        if uid is None:
            return {"status": "rejected", "reason": "missing_update_id"}
        try:
            uid = int(uid)
        except (TypeError, ValueError):
            return {"status": "rejected", "reason": "bad_update_id"}
        if uid in self.seen_ids():
            return {"status": "duplicate", "update_id": uid, "effect": "none"}
        chat_id = self._chat_id(update)
        self._mark_seen(uid)  # mark even denials so restart does not retry
        if chat_id is None:
            return {"status": "rejected", "reason": "no_chat", "update_id": uid}
        if self.allowlist and chat_id not in self.allowlist:
            return {
                "status": "denied_allowlist",
                "update_id": uid,
                "chat_fp": chat_fingerprint(chat_id),
            }
        text = ""
        msg = update.get("message") or {}
        if isinstance(msg.get("text"), str):
            text = msg["text"]
        cb = update.get("callback_query") or {}
        if cb.get("data"):
            text = str(cb.get("data"))
        return {
            "status": "accepted",
            "update_id": uid,
            "chat_fp": chat_fingerprint(chat_id),
            "text_redacted": redact(text)[:500],
        }

    def _append_outbox(self, rec: dict) -> None:
        rec = dict(rec)
        rec["text"] = redact(rec.get("text") or "")
        rec.setdefault("ts", self._now())
        rec.setdefault("delivery_retry", 0)
        rec.setdefault("business_retry", 0)
        with self.outbox_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def enqueue_unowned_alert(
        self,
        *,
        name: str,
        stream: str,
        message_key: str,
        text: str,
        correlation_id: str,
    ) -> dict:
        """Outbox-only incident. No task_id (unowned). Never live-sends."""
        cursor = self._load_json(self.cursor_path, {})
        seen = cursor.get("alert_keys") if isinstance(cursor.get("alert_keys"), dict) else {}
        now = self._now()
        prev = seen.get(message_key) or {}
        last = float(prev.get("ts") or 0)
        if last and (now - last) < self.rate_s:
            return {
                "ok": True, "sent": False, "status": "rate_limited",
                "task_id": None, "event_id": None,
                "correlation_id": correlation_id, "message_key": message_key,
                "terminal": "BLOCKED",
            }
        rec = {
            "kind": "unowned_alert",
            "loop_id": "LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT",
            "type": ["ORPHAN", "LOST_ACK"],
            "severity": "HIGH",
            "status": "OPEN",
            "name": name,
            "stream": stream,
            "message_key": message_key,
            "correlation_id": correlation_id,
            "task_id": None,
            "event_id": None,
            "run_id": None,
            "text": redact(text)[:500],
            "mode": "dry_run",
            "sent": False,
            "terminal": "BLOCKED",
            "direct_telegram_send": False,
        }
        self._append_outbox(rec)
        inc_path = self.state_dir / "incidents.jsonl"
        with inc_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "loop_id": rec["loop_id"], "type": rec["type"],
                "severity": rec["severity"], "status": rec["status"],
                "name": name, "message_key": message_key,
                "correlation_id": correlation_id, "task_id": None,
                "event_id": None, "run_id": None, "sent": False,
                "terminal": "BLOCKED", "ts": rec.get("ts") or now,
            }, ensure_ascii=False) + "\n")
        seen[message_key] = {"ts": now, "name": name}
        cursor["alert_keys"] = seen
        self._save_json(self.cursor_path, cursor)
        return {
            "ok": True, "sent": False, "status": "outboxed",
            "task_id": None, "event_id": None,
            "correlation_id": correlation_id, "message_key": message_key,
            "terminal": "BLOCKED",
        }

    def enqueue_digest(
        self,
        loops: list[dict],
        *,
        chat_id: int,
        force: bool = False,
    ) -> dict[str, Any]:
        """Coalesce open loops into one digest. Never 1:1 with seams."""
        cursor = self._load_json(self.cursor_path, {})
        last = float(cursor.get("last_digest_ts") or 0)
        now = self._now()
        if not force and last and (now - last) < self.rate_s:
            return {
                "status": "rate_limited",
                "wait_s": round(self.rate_s - (now - last), 1),
                "sent": False,
            }
        if self.allowlist and chat_id not in self.allowlist:
            return {"status": "denied_allowlist", "sent": False}
        n = len(loops)
        head = loops[:MAX_LOOPS_IN_DIGEST]
        lines = ["🐙 loop digest (dry_run)" if not self.live else "🐙 loop digest"]
        for e in head:
            lines.append(f"- {e.get('loop_id')}: {e.get('class')} · {e.get('title', '')[:80]}")
        extra = n - len(head)
        if extra > 0:
            lines.append(f"- … and {extra} more (not listed — coalesced)")
        text = redact("\n".join(lines))
        rec = {
            "kind": "digest",
            "n_loops": n,
            "listed": len(head),
            "coalesced": extra,
            "chat_fp": chat_fingerprint(chat_id),
            "text": text,
            "mode": "live" if self.live else "dry_run",
            "sent": False,
        }
        sent = False
        if self.live and self.transport is not None:
            try:
                sent = bool(self.transport(chat_id, text))
            except Exception:  # noqa: BLE001 — delivery failure must not drop business result
                rec["delivery_retry"] = 1
                rec["delivery_error"] = "transport_failed"
                sent = False
        rec["sent"] = sent
        self._append_outbox(rec)
        cursor["last_digest_ts"] = now
        cursor["last_n"] = n
        self._save_json(self.cursor_path, cursor)
        return {
            "status": "sent" if sent else ("dry_run" if not self.live else "queued"),
            "sent": sent,
            "n_loops": n,
            "coalesced": extra,
            "text_redacted": text,
        }

    def consume_spine_count(self, db_path: Path) -> dict[str, Any]:
        """Read-only count of domain=telegram events. Does not send."""
        import sqlite3
        if not db_path.is_file():
            return {"status": "unlocated", "n": None}
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            n = con.execute(
                "SELECT COUNT(*) FROM events WHERE domain='telegram'"
            ).fetchone()[0]
            con.close()
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "n": None, "error": type(e).__name__}
        cursor = self._load_json(self.cursor_path, {})
        prev = cursor.get("spine_telegram_n")
        cursor["spine_telegram_n"] = n
        cursor["spine_consumed_at"] = self._now()
        self._save_json(self.cursor_path, cursor)
        return {
            "status": "consumed",
            "n": n,
            "prev_n": prev,
            "delta": None if prev is None else (n - int(prev)),
        }
