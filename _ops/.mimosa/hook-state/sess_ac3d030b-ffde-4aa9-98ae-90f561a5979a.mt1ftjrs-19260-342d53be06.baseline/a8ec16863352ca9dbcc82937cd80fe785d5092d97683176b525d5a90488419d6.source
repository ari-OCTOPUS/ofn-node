#!/usr/bin/env python3
"""agent_gateway_http.py — AgentGateway v1: READ-ONLY peer-AGI discovery/share (M3.B).

The FIRST AGI-to-AGI surface in OCTOPUS. v1 is deliberately inert: it can share
owner-curated research summaries and *receive* prior-art as UNTRUSTED_DATA into a
quarantine receipt. It has ZERO effect-side — no approve/merge/send/verdict, and it
imports NONE of approval/chrono/telegram/outbound/mission (structural proof of harm-
lessness, exactly like lead_boundary_http.py's ingestion boundary).

Every external message is UNTRUSTED_DATA. It is NEVER executed as an instruction; only
typed fields of a CLOSED schema are read. There is NO channel by which a peer can assert
owner authority — owner verdicts flow only through Telegram (is_owner from.id). A peer
message that says "owner approves X" is just bytes in a quarantine log.

CLOSED schema v1 (anything else → reject, fail-closed):
    peer.hello            → capability handshake
    discovery.list        → list ids of owner-curated shareable summaries
    discovery.fetch {id}  → return one owner-curated shareable summary
    discovery.prior_art   → inbound offer; stored to quarantine receipt ONLY, not ingested

Controls (all fail-closed, deterministic order — generalized from lead_boundary_http.py):
    halt → peer-allowlist → per-peer-secret → required-headers → timestamp(±300s)
    → body-size → HMAC-SHA256(`${ts}.${nonce}.${body}`) → owner-bearer(expiry) → nonce-replay
    → rate-limit → JSON → closed-schema dispatch. Every path writes a receipt.

Flag OCTOPUS_WIRE_AGENT_GATEWAY off (default) = listener never starts = zero effect.
Loopback only (127.0.0.1), never 0.0.0.0. stdlib-only. Never raises to the socket.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib          # noqa: E402
import agent_bearer    # noqa: E402

FLAG = "OCTOPUS_WIRE_AGENT_GATEWAY"
TS_WINDOW_S = 300
DEFAULT_PORT = int(os.environ.get("OCTOPUS_AGENT_GATEWAY_PORT", "8775"))
SCHEMA_VERSION = "agent-gateway-v1"

_H_PEER = "X-Octopus-Peer"
_H_TS = "X-Octopus-Timestamp"
_H_NONCE = "X-Octopus-Nonce"
_H_SIG = "X-Octopus-Signature"
_H_BEARER = "Authorization"   # "Bearer <token>"

_ALLOWED_TYPES = {"peer.hello", "discovery.list", "discovery.fetch", "discovery.prior_art"}
_RATE: dict[str, list[float]] = {}   # per-peer sliding window (in-process)


def enabled() -> bool:
    return os.environ.get(FLAG) == "1"


def _max_bytes() -> int:
    try:
        return int(os.environ.get("OCTOPUS_AGENT_MAX_BYTES", "65536"))
    except (TypeError, ValueError):
        return 65536


def _rate_per_min() -> int:
    try:
        return int(os.environ.get("OCTOPUS_AGENT_RATE_PER_MIN", "30"))
    except (TypeError, ValueError):
        return 30


def _allowlist() -> set[str]:
    raw = os.environ.get("OCTOPUS_AGENT_PEERS", "")
    return {s.strip() for s in raw.split(",") if s.strip()}


def _secret_for(peer_id: str) -> str | None:
    key = "OCTOPUS_AGENT_SECRET_" + "".join(
        c if c.isalnum() else "_" for c in peer_id.upper())
    return os.environ.get(key)


def _sign(secret: str, ts: str, nonce: str, body: bytes) -> str:
    msg = f"{ts}.{nonce}.".encode("utf-8") + body
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def _share_dir() -> Path:
    """Owner-curated directory of summaries explicitly marked shareable. Nothing else is
    ever served. Missing dir → fail-closed (503)."""
    return opslib.STATE_DIR / "agent-gateway" / "shareable"


def _nonce_store() -> Path:
    return opslib.STATE_DIR / "agent-gateway" / "nonces.json"


def _nonce_seen(peer_id: str, nonce: str, now: float) -> bool:
    p = _nonce_store()
    try:
        idx = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        idx = {}
    cutoff = now - 2 * TS_WINDOW_S
    src = {k: v for k, v in (idx.get(peer_id) or {}).items() if v >= cutoff}
    if nonce in src:
        return True
    src[nonce] = now
    idx[peer_id] = src
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        pass
    return False


def _rate_ok(peer_id: str, now: float) -> bool:
    win = [t for t in _RATE.get(peer_id, []) if t > now - 60.0]
    if len(win) >= _rate_per_min():
        _RATE[peer_id] = win
        return False
    win.append(now)
    _RATE[peer_id] = win
    return True


def _receipt(event_type: str, peer_id: str, payload: dict) -> str:
    ev = uuid.uuid4().hex
    try:
        opslib.append_jsonl(opslib.STATE_DIR / "agent-gateway" / "events.jsonl", {
            "event_id": ev, "event_type": event_type, "occurred_at": opslib.now_iso(),
            "peer_id": peer_id, "source_component": "AgentGateway", "trust": "UNTRUSTED_DATA",
            "schema_version": SCHEMA_VERSION, "payload": payload})
    except Exception:  # noqa: BLE001
        pass
    return ev


def _prov() -> dict:
    """Our provenance stamp on every response (peer can bind it; we never trust theirs)."""
    return {"gateway": "OCTOPUS-AgentGateway", "schema": SCHEMA_VERSION,
            "ts": int(time.time()), "nonce": uuid.uuid4().hex}


def _err(code: str, http: int, peer_id: str, payload: dict | None = None) -> tuple[int, dict]:
    rid = _receipt("agent.msg.rejected", peer_id, {"code": code, **(payload or {})})
    return http, {"ok": False, "error": {"code": code}, "receipt_event_id": rid,
                  "provenance": _prov()}


def _safe_id(sid: str) -> bool:
    """Enumerated-set id, NOT a filesystem path. No separators/traversal (anti-exfil)."""
    return bool(sid) and sid.isascii() and all(
        c.isalnum() or c in ("-", "_") for c in sid) and ".." not in sid


def _list_shares() -> list[dict]:
    d = _share_dir()
    out: list[dict] = []
    try:
        for f in sorted(d.glob("*.json")):
            if not _safe_id(f.stem):
                continue
            try:
                raw = f.read_bytes()
                meta = json.loads(raw.decode("utf-8"))
            except (OSError, ValueError):
                continue
            out.append({"id": f.stem, "title": str(meta.get("title", f.stem)),
                        "sha256": hashlib.sha256(raw).hexdigest()[:16]})
    except OSError:
        pass
    return out


def _fetch_share(sid: str) -> dict | None:
    if not _safe_id(sid):
        return None
    f = _share_dir() / f"{sid}.json"
    try:
        if f.parent != _share_dir() or not f.is_file():
            return None
        return json.loads(f.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def _dispatch(msg_type: str, body_obj: dict, peer_id: str) -> tuple[int, dict]:
    """CLOSED schema. Read-only. Peer content is UNTRUSTED_DATA — never executed."""
    if msg_type == "peer.hello":
        _receipt("agent.hello", peer_id, {"peer_stated": body_obj.get("name")})
        return 200, {"ok": True, "version": "v1", "mode": "read-only",
                     "capabilities": ["discovery.list", "discovery.fetch",
                                      "discovery.prior_art(quarantine-only)"],
                     "provenance": _prov()}
    if msg_type == "discovery.list":
        d = _share_dir()
        if not d.is_dir():
            return _err("SHARE_DIR_MISSING", 503, peer_id)
        return 200, {"ok": True, "shares": _list_shares(), "provenance": _prov()}
    if msg_type == "discovery.fetch":
        sid = str(body_obj.get("id") or "").strip()
        share = _fetch_share(sid)
        if share is None:
            return _err("SHARE_NOT_FOUND", 404, peer_id, {"id": sid[:64]})
        _receipt("agent.share.served", peer_id, {"id": sid})
        return 200, {"ok": True, "id": sid, "summary": share, "provenance": _prov()}
    if msg_type == "discovery.prior_art":
        # v1: receive as UNTRUSTED_DATA → quarantine receipt ONLY. NOT ingested into memory,
        # NOT surfaced to autonomy_matrix, NOT executed. (v2, after owner vote, may route this
        # through the same owner-gate the Telegram cards use.)
        rid = _receipt("agent.prior_art.quarantined", peer_id, {
            "title": str(body_obj.get("title", ""))[:256],
            "ref": str(body_obj.get("ref", ""))[:512],
            "note": "stored as untrusted data pending owner review; not ingested; not executed"})
        return 202, {"ok": True, "accepted": False, "quarantined": True,
                     "note": "received as untrusted data; not ingested; not executed",
                     "receipt_event_id": rid, "provenance": _prov()}
    return _err("SCHEMA_UNKNOWN", 400, peer_id, {"type": str(msg_type)[:64]})


def verify_and_dispatch(headers: dict, body: bytes, *, now_ts: float | None = None) -> tuple[int, dict]:
    """Full auth + dispatch, no HTTP. Deterministic fail-closed order. Never raises."""
    now = float(now_ts if now_ts is not None else time.time())
    h = {str(k).lower(): v for k, v in (headers or {}).items()}
    peer = str(h.get(_H_PEER.lower()) or "").strip()

    # 1) halt: receipt only, zero state mutation.
    kill = opslib.master_halted() or opslib.halted() or (
        "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None) or (
        "FREEZE" if opslib.frozen() else None)
    if kill:
        return _err("HALTED", 503, peer or "unknown", {"reason": kill})
    # 2) peer allowlist.
    if not peer or peer not in _allowlist():
        return _err("PEER_UNKNOWN", 403, peer or "unknown")
    # 3) per-peer secret (absent → fail-closed).
    secret = _secret_for(peer)
    if not secret:
        return _err("PEER_UNCONFIGURED", 503, peer)
    # 4) required headers.
    ts = str(h.get(_H_TS.lower()) or "").strip()
    nonce = str(h.get(_H_NONCE.lower()) or "").strip()
    sig = str(h.get(_H_SIG.lower()) or "").strip()
    auth = str(h.get(_H_BEARER.lower()) or "").strip()
    bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not (ts and nonce and sig and bearer):
        return _err("AUTH_MISSING_HEADERS", 401, peer)
    # 5) timestamp (reject non-finite: abs(now-nan)>300 is False → would bypass the window).
    try:
        ts_val = float(ts)
    except (TypeError, ValueError):
        return _err("TS_INVALID", 401, peer)
    if not math.isfinite(ts_val) or abs(now - ts_val) > TS_WINDOW_S:
        return _err("TS_EXPIRED", 401, peer, {"skew_s": None})
    # 6) body size (before parse — cheap DoS guard).
    if len(body) > _max_bytes():
        return _err("BODY_TOO_LARGE", 413, peer, {"bytes": len(body)})
    # 7) per-peer HMAC (proves PEER identity).
    expected = _sign(secret, ts, nonce, body)
    if not hmac.compare_digest(expected, sig):
        return _err("SIG_INVALID", 401, peer, {"body_sha": hashlib.sha256(body).hexdigest()[:12]})
    # 8) owner bearer (proves OWNER authorized this peer; expiry enforced inside verify).
    ok, reason = agent_bearer.verify(bearer, peer, now=now)
    if not ok:
        return _err("BEARER_INVALID", 401, peer, {"reason": reason})
    # 9) nonce replay.
    if _nonce_seen(peer, nonce, now):
        return _err("NONCE_REPLAY", 409, peer)
    # 10) rate limit.
    if not _rate_ok(peer, now):
        return 429, {"ok": False, "error": {"code": "RATE_LIMITED"}, "retry_after": 60,
                     "provenance": _prov()}
    # 11) JSON.
    try:
        obj = json.loads(body.decode("utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("not an object")
    except (ValueError, UnicodeDecodeError):
        return _err("JSON_INVALID", 400, peer)
    # 12) closed-schema type (unknown → reject; NO free-text command field is ever parsed).
    msg_type = str(obj.get("type") or "")
    if msg_type not in _ALLOWED_TYPES:
        return _err("SCHEMA_UNKNOWN", 400, peer, {"type": msg_type[:64]})
    return _dispatch(msg_type, obj, peer)


# ── thin HTTP layer (only when flag on) ───────────────────────────────────────────
def _make_handler():
    from http.server import BaseHTTPRequestHandler

    class AgentGatewayHandler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._send(200, {"ok": True, "service": "agent-gateway", "mode": "read-only",
                                 "halted": bool(opslib.master_halted() or opslib.halted()
                                                or opslib.STOP_ORGANISM.exists())})
            else:
                self._send(404, {"ok": False, "error": {"code": "NOT_FOUND"}})

        def do_POST(self):  # noqa: N802
            if self.path != "/api/v1/agent":
                self._send(404, {"ok": False, "error": {"code": "NOT_FOUND"}})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except (TypeError, ValueError):
                length = 0
            length = min(length, _max_bytes() + 1)
            body = self.rfile.read(length) if length > 0 else b""
            code, payload = verify_and_dispatch(dict(self.headers.items()), body)
            self._send(code, payload)

        def log_message(self, *a):  # silent
            pass

    return AgentGatewayHandler


def serve(host: str = "127.0.0.1", port: int | None = None) -> None:
    """Start the listener — only if flag on, only on loopback."""
    if not enabled():
        opslib.alert([f"{FLAG} off — agent gateway not started"])
        return
    from http.server import HTTPServer
    port = int(port or DEFAULT_PORT)
    srv = HTTPServer((host, port), _make_handler())
    srv.serve_forever()


if __name__ == "__main__":
    print(json.dumps({"enabled": enabled(), "port": DEFAULT_PORT, "mode": "read-only-v1",
                      "note": "flag on + per-peer secret + owner bearer required; 127.0.0.1 only"},
                     ensure_ascii=False))
