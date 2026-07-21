#!/usr/bin/env python3
"""lead_boundary_http.py — Trust-Engine P0: مرزِ امضاشدهٔ ورودیِ لید (D7).

تنها endpointی که اتوماسیونِ بیرونی (n8n) مجاز به فراخوانی است:
    POST /api/v1/lead-candidates      (فقط 127.0.0.1؛ هرگز 0.0.0.0)
قرارداد: `Trust-Engine-v1.1/PHASE-B-CONTRACTS/07a_API_BOUNDARY_DESIGN.md`.

کنترل‌ها (همه fail-closed، ترتیبِ قطعی): halt → allowlist → secret → هدرها → timestamp(±300s)
→ اندازه → HMAC-SHA256(`${ts}.${nonce}.${body}`) → nonce-replay → rate-limit → JSON → idempotency
→ submit_candidate. هر مسیر (موفق/رد) یک receipt می‌نویسد (spec §0). بدنهٔ **بی‌امضا** فقط
receiptِ سبک می‌گیرد (هش/اندازه/کد)، quarantine نمی‌شود (DoS-hardening، §6.3).

منطق (verify_and_dispatch) از HTTP جداست تا بدونِ سوکت تست شود. n8n هیچ credentialِ گیت/تأیید/
ارسال ندارد — فقط secretِ ingestion (اثباتِ ساختاری: صفر importِ approval/chrono/telegram/outbound).

stdlib-only. flag OCTOPUS_WIRE_LEAD_BOUNDARY خاموش = listener بالا نمی‌آید (صفر اثر).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib                       # noqa: E402
import lead_candidate_inbox as lci  # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_BOUNDARY"
TS_WINDOW_S = 300
DEFAULT_PORT = int(os.environ.get("OCTOPUS_LEAD_INBOX_PORT", "8774"))

_H_SOURCE = "X-Octopus-Source"
_H_TS = "X-Octopus-Timestamp"
_H_NONCE = "X-Octopus-Nonce"
_H_SIG = "X-Octopus-Signature"
_H_IDEM = "Idempotency-Key"

_RATE: dict[str, list[float]] = {}   # per-source sliding window (in-process؛ listenerِ بلندمدت)


def enabled() -> bool:
    return os.environ.get(FLAG) == "1"


def _max_bytes() -> int:
    try:
        return int(os.environ.get("OCTOPUS_INGEST_MAX_BYTES", "65536"))
    except (TypeError, ValueError):
        return 65536


def _rate_per_min() -> int:
    try:
        return int(os.environ.get("OCTOPUS_INGEST_RATE_PER_MIN", "60"))
    except (TypeError, ValueError):
        return 60


def _allowlist() -> set[str]:
    raw = os.environ.get("OCTOPUS_INGEST_SOURCES", "")
    return {s.strip() for s in raw.split(",") if s.strip()}


def _secret_for(source_id: str) -> str | None:
    key = "OCTOPUS_INGEST_SECRET_" + "".join(
        c if c.isalnum() else "_" for c in source_id.upper())
    return os.environ.get(key)


def _sign(secret: str, ts: str, nonce: str, body: bytes) -> str:
    msg = f"{ts}.{nonce}.".encode("utf-8") + body
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def _nonce_store() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox" / "nonces.json"


def _nonce_seen(source_id: str, nonce: str, now: float) -> bool:
    """True اگر nonce قبلاً برای این source دیده شده. ثبت + GCِ منقضی‌ها (پنجرهٔ ۲×ts)."""
    p = _nonce_store()
    try:
        idx = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        idx = {}
    cutoff = now - 2 * TS_WINDOW_S
    src = {k: v for k, v in (idx.get(source_id) or {}).items() if v >= cutoff}
    if nonce in src:
        return True
    src[nonce] = now
    idx[source_id] = src
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        pass
    return False


def _rate_ok(source_id: str, now: float) -> bool:
    win = [t for t in _RATE.get(source_id, []) if t > now - 60.0]
    if len(win) >= _rate_per_min():
        _RATE[source_id] = win
        return False
    win.append(now)
    _RATE[source_id] = win
    return True


def _receipt(event_type: str, corr: str, payload: dict) -> str:
    ev = uuid.uuid4().hex
    try:
        opslib.append_jsonl(opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl", {
            "event_id": ev, "event_type": event_type, "occurred_at": opslib.now_iso(),
            "correlation_id": corr, "source_component": "LeadBoundaryHTTP",
            "schema_version": "1.0", "payload": payload})
    except Exception:  # noqa: BLE001
        pass
    return ev


def _err(code: str, http: int, corr: str, payload: dict | None = None) -> tuple[int, dict]:
    rid = _receipt("lead.candidate.rejected", corr, {"code": code, **(payload or {})})
    return http, {"ok": False, "error": {"code": code}, "receipt_event_id": rid}


def verify_and_dispatch(headers: dict, body: bytes, *, now_ts: float | None = None) -> tuple[int, dict]:
    """کلِ auth + dispatch، بدونِ HTTP. خروجی: (کدِ HTTP، بدنهٔ پاسخ). هرگز استثنا."""
    now = float(now_ts if now_ts is not None else time.time())
    h = {str(k).lower(): v for k, v in (headers or {}).items()}
    source = str(h.get(_H_SOURCE.lower()) or "").strip()

    # ۱) halt: تنها receipt، صفر جهشِ state (B2).
    kill = opslib.master_halted() or opslib.halted() or (
        "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None) or (
        "FREEZE" if opslib.frozen() else None)
    if kill:
        return _err("HALTED", 503, source or "unknown", {"reason": kill, "outcome": "halted_refused"})

    # ۲) allowlist منبع.
    if not source or source not in _allowlist():
        return _err("SRC_UNKNOWN", 403, source or "unknown")
    # ۳) secretِ منبع (غایب → fail-closed).
    secret = _secret_for(source)
    if not secret:
        return _err("SRC_UNCONFIGURED", 503, source)
    # ۴) هدرهای الزامی.
    ts = str(h.get(_H_TS.lower()) or "").strip()
    nonce = str(h.get(_H_NONCE.lower()) or "").strip()
    sig = str(h.get(_H_SIG.lower()) or "").strip()
    if not (ts and nonce and sig):
        return _err("AUTH_MISSING_HEADERS", 401, source)
    # ۵) timestamp.
    try:
        ts_val = float(ts)
    except (TypeError, ValueError):
        return _err("TS_INVALID", 401, source)
    if abs(now - ts_val) > TS_WINDOW_S:
        return _err("TS_EXPIRED", 401, source, {"skew_s": round(now - ts_val, 1)})
    # ۶) اندازهٔ بدنه.
    if len(body) > _max_bytes():
        return _err("BODY_TOO_LARGE", 413, source, {"bytes": len(body)})
    # ۷) HMAC (بدنهٔ بی‌امضا فقط receiptِ سبک — quarantine نمی‌شود، §6.3).
    expected = _sign(secret, ts, nonce, body)
    if not hmac.compare_digest(expected, sig):
        return _err("SIG_INVALID", 401, source, {"body_sha": hashlib.sha256(body).hexdigest()[:12]})
    # ۸) nonce replay.
    if _nonce_seen(source, nonce, now):
        return _err("NONCE_REPLAY", 409, source)
    # ۹) rate limit.
    if not _rate_ok(source, now):
        return 429, {"ok": False, "error": {"code": "RATE_LIMITED"}, "retry_after": 60}
    # ۱۰) JSON (بدنهٔ احرازشده ولی خراب → quarantine از مسیرِ submit).
    try:
        candidate = json.loads(body.decode("utf-8"))
        if not isinstance(candidate, dict):
            raise ValueError("not an object")
    except (ValueError, UnicodeDecodeError):
        return _err("JSON_INVALID", 400, source)
    # ۱۱) idempotency-key = source:external_id.
    ext = str(((candidate.get("source") or {}).get("external_id") or "")).strip()
    idem_hdr = str(h.get(_H_IDEM.lower()) or "").strip()
    if idem_hdr and ext and idem_hdr != f"{source}:{ext}":
        return _err("IDEM_MISMATCH", 422, source, {"expected": f"{source}:{ext}"})

    # ۱۲) dispatch به آداپترِ canonical (خودش validate/firewall/routing/receipt می‌کند).
    res = lci.submit_candidate(candidate, source_id=source)
    if res.get("ok"):
        http = 202
    elif res.get("status") == "quarantined":
        http = 422
    elif res.get("status") == "halted":
        http = 503
    elif res.get("status") == "gate_off":
        http = 503   # آداپتر خاموش = سرویس در دسترس نیست
    else:
        http = 400
    return http, {"ok": bool(res.get("ok")), "status": res.get("status"),
                  "lead_id": res.get("lead_id"), "receipt_event_id": res.get("receipt_event_id")}


# ── لایهٔ نازکِ HTTP (فقط وقتی flag روشن است) ─────────────────────────────────────
def _make_handler():
    from http.server import BaseHTTPRequestHandler

    class LeadBoundaryHandler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                # فقط ops/owner؛ n8n نباید صدا بزند (چک‌لیستِ deploy).
                self._send(200, {"ok": True, "service": "lead-boundary", "halted": bool(
                    opslib.master_halted() or opslib.halted() or opslib.STOP_ORGANISM.exists())})
            else:
                self._send(404, {"ok": False, "error": {"code": "NOT_FOUND"}})

        def do_POST(self):  # noqa: N802
            if self.path != "/api/v1/lead-candidates":
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

        def log_message(self, *a):  # ساکت
            pass

    return LeadBoundaryHandler


def serve(host: str = "127.0.0.1", port: int | None = None) -> None:
    """listener را بالا بیاور — فقط اگر flag روشن باشد و فقط روی loopback."""
    if not enabled():
        opslib.alert([f"{FLAG} off — lead boundary not started"])
        return
    from http.server import HTTPServer
    port = int(port or DEFAULT_PORT)
    srv = HTTPServer((host, port), _make_handler())
    srv.serve_forever()


if __name__ == "__main__":
    print(json.dumps({"enabled": enabled(), "port": DEFAULT_PORT,
                      "note": "flag روشن + secret per-source لازم است؛ فقط 127.0.0.1"},
                     ensure_ascii=False))
