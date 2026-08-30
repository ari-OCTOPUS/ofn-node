#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_api.py — WP4+WP5: Owner API با HMAC auth + Approval tamper-proof.

قرارداد (Owner-Cockpit WP4+WP5، ۲۰۲۶-۰۸-۰۸):
  · HTTP server روی 127.0.0.1:8788 — OpenAI-compatible style.
  · ۷ لایه امنیت (طبق Kimi K3 blueprint):
    1. HMAC initData — الگوریتم رسمی Telegram
    2. Session جدا — initData فقط برای صدور session؛ بقیه با توکن ۳۰ دقیقه‌ای
    3. Owner allowlist — هم در initData هم در verify session
    4. Consume-once در confirm — WHERE status='preview_sent'
    5. CORS محدود به web.telegram.org
    6. Rate limit روی POSTها (۳۰/دقیقه per owner)
    7. Freeze بدون approval ولی در hash-chained audit ledger

  · Endpoints:
    POST /auth/session     — initData → session token
    GET  /state            — live_snapshot summary
    GET  /fugu/usage       — provider_usage aggregation
    GET  /approvals        — pending approvals
    POST /approve/:id      — confirm (consume-once + tamper check)
    POST /reject/:id       — reject
    POST /freeze           — freeze (kill switch, no approval needed)
    GET  /health           — health check

CLI:
  OCTOPUS_WIRE_OWNER_API=1 python -X utf8 _ops/owner_cockpit/owner_api.py
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))

FLAG = "OCTOPUS_WIRE_OWNER_API"
PORT = int(os.environ.get("OCTOPUS_OWNER_API_PORT", "8788"))
SESSION_TTL_S = 1800  # ۳۰ دقیقه
RATE_LIMIT_WINDOW = 60  # ۶۰ ثانیه
RATE_LIMIT_MAX = 30  # ۳۰ request per window


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


# ─── HMAC initData validation ───────────────────────────────────────────────

def validate_init_data(init_data: str, bot_token: str,
                       owner_ids: list[str]) -> tuple[bool, str]:
    """اعتبارسنجی initData تلگرام (الگوریتم رسمی).
    خروجی: (valid, owner_id or reason).
    مراحل:
    1. parse query string
    2. check auth_date freshness (≤ ۱۰ دقیقه)
    3. reconstruct data-check-string
    4. HMAC-SHA256 with secret_key = HMAC("WebAppData", bot_token)
    5. compare hash
    6. check user.id in owner allowlist
    """
    if not init_data or not bot_token:
        return False, "missing_params"

    try:
        params = dict(urllib.parse.parse_qsl(init_data))
    except ValueError:
        return False, "bad_query"

    recv_hash = params.pop("hash", "")
    if not recv_hash:
        return False, "no_hash"

    # check freshness
    try:
        auth_date = int(float(params.get("auth_date", "0")))
    except (ValueError, TypeError):
        return False, "bad_auth_date"
    if time.time() - auth_date > 600:
        return False, "stale_auth"

    # reconstruct data-check-string
    dc_items = sorted(f"{k}={v}" for k, v in params.items())
    dc_string = "\n".join(dc_items)

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, dc_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(recv_hash, calc_hash):
        return False, "bad_hash"

    # check owner
    user_json = params.get("user", "{}")
    try:
        user = json.loads(user_json)
    except ValueError:
        return False, "bad_user"
    uid = str(user.get("id", ""))
    if uid not in owner_ids:
        return False, "not_owner"

    return True, uid


# ─── session management ─────────────────────────────────────────────────────

def _new_session_token() -> tuple[str, str]:
    """تولید session token + hash. token به کاربر، hash در DB."""
    import secrets
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, token_hash


def _create_session(owner_id: str) -> str | None:
    """صدور session برای owner. token را برمی‌گرداند (نه hash)."""
    from owner_cockpit.db import create_session
    token, token_hash = _new_session_token()
    expires = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + SESSION_TTL_S))
    if create_session(token_hash, owner_id, expires):
        return token
    return None


def _verify_session_token(token: str) -> tuple[bool, str]:
    """verify session: (valid, owner_id)."""
    from owner_cockpit.db import verify_session
    if not token:
        return False, ""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return verify_session(token_hash)


# ─── rate limiting ──────────────────────────────────────────────────────────

_rate_buckets: dict[str, list[float]] = {}


def _rate_check(owner_id: str) -> bool:
    """ Rate limit: RATE_LIMIT_MAX per RATE_LIMIT_WINDOW."""
    now = time.time()
    bucket = _rate_buckets.setdefault(owner_id, [])
    # پاک‌کردنِ قدیمی‌ها
    bucket[:] = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]
    if len(bucket) >= RATE_LIMIT_MAX:
        return False
    bucket.append(now)
    return True


# ─── HTTP handler ───────────────────────────────────────────────────────────

class _OwnerAPIHandler(BaseHTTPRequestHandler):
    """Owner API handler."""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "http://web.telegram.org")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, code: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _get_session(self) -> tuple[bool, str]:
        """extract + verify session from header."""
        token = self.headers.get("X-Session-Token", "")
        return _verify_session_token(token)

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            return json.loads(raw.decode("utf-8"))
        except (ValueError, OSError):
            return {}

    def do_GET(self):
        # ── public endpoints ──
        if self.path == "/health":
            self._json(200, {"status": "ok", "flag_on": _flag_on()})
            return

        # ── auth-required endpoints ──
        valid, owner = self._get_session()
        if not valid:
            self._json(401, {"error": "unauthorized"})
            return

        if not _rate_check(owner):
            self._json(429, {"error": "rate_limited"})
            return

        if self.path == "/state":
            self._handle_state(owner)
        elif self.path == "/fugu/usage":
            self._handle_fugu_usage(owner)
        elif self.path == "/approvals":
            self._handle_approvals(owner)
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/auth/session":
            self._handle_auth()
            return

        # auth-required
        valid, owner = self._get_session()
        if not valid:
            self._json(401, {"error": "unauthorized"})
            return

        if not _rate_check(owner):
            self._json(429, {"error": "rate_limited"})
            return

        if self.path.startswith("/approve/"):
            self._handle_approve(owner, self.path.split("/approve/")[-1])
        elif self.path.startswith("/reject/"):
            self._handle_reject(owner, self.path.split("/reject/")[-1])
        elif self.path == "/freeze":
            self._handle_freeze(owner)
        else:
            self._json(404, {"error": "not_found"})

    # ── endpoint handlers ──

    def _handle_auth(self):
        body = self._read_body()
        init_data = body.get("init_data", "")
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        owner_ids_str = os.environ.get("OWNER_TELEGRAM_IDS", "")
        owner_ids = [x.strip() for x in owner_ids_str.split(",") if x.strip()]

        valid, result = validate_init_data(init_data, bot_token, owner_ids)
        if not valid:
            self._json(401, {"error": "auth_failed", "reason": result})
            return

        token = _create_session(result)
        if not token:
            self._json(500, {"error": "session_create_failed"})
            return

        from owner_cockpit.db import audit_append
        audit_append("session_create", actor=result, payload={"ip": self.client_address[0]})
        self._json(200, {"session_token": token, "owner_id": result, "expires_in": SESSION_TTL_S})

    def _handle_state(self, owner: str):
        """GET /state — live_snapshot summary."""
        try:
            from control_plane import live_snapshot
            snap = live_snapshot.snapshot(use_cache=True)
            # فقط بخش‌های امن (نه secrets)
            safe = {
                "organism": snap.get("organism", {}),
                "budget": snap.get("budget", {}),
                "flags": snap.get("flags", {}),
                "approvals": snap.get("approvals", {}),
                "health": snap.get("health", {}),
                "ts": snap.get("ts", ""),
            }
            self._json(200, safe)
        except Exception as e:  # noqa: BLE001
            self._json(200, {"status": "error", "reason": str(e)[:200]})

    def _handle_fugu_usage(self, owner: str):
        """GET /fugu/usage — provider_usage aggregation."""
        try:
            from owner_cockpit.db import get_db
            conn = get_db()
            row = conn.execute("""
                SELECT COUNT(*) as calls,
                       COALESCE(SUM(total_tokens), 0) as tokens,
                       COALESCE(SUM(cost_usd), 0.0) as cost,
                       COALESCE(SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END), 0) as ok,
                       COALESCE(SUM(CASE WHEN status!='ok' THEN 1 ELSE 0 END), 0) as errors
                FROM provider_usage
                WHERE ts >= date('now', 'start of day')
            """).fetchone()
            conn.close()
            self._json(200, {
                "today": {"calls": row["calls"], "tokens": row["tokens"],
                          "cost_usd": round(row["cost"], 4),
                          "ok": row["ok"], "errors": row["errors"]},
            })
        except Exception as e:  # noqa: BLE001
            self._json(200, {"status": "error", "reason": str(e)[:200]})

    def _handle_approvals(self, owner: str):
        """GET /approvals — pending approvals."""
        try:
            from owner_cockpit.db import get_db
            conn = get_db()
            # placeholder: از unified-approval-queue.json بخوان
            from budget import opslib
            qpath = opslib.STATE_DIR / "unified-approval-queue.json"
            if qpath.exists():
                queue = json.loads(qpath.read_text("utf-8"))
                pending = [x for x in queue if x.get("status") == "preview_sent"]
            else:
                pending = []
            conn.close()
            self._json(200, {"pending": pending[:20], "count": len(pending)})
        except Exception as e:  # noqa: BLE001
            self._json(200, {"status": "error", "reason": str(e)[:200]})

    def _handle_approve(self, owner: str, item_id: str):
        """POST /approve/:id — confirm with consume-once + tamper check."""
        body = self._read_body()
        payload_hash = body.get("payload_hash", "")

        from owner_cockpit.db import get_db, audit_append
        conn = get_db()
        try:
            # consume-once: WHERE status='preview_sent'
            row = conn.execute("""
                SELECT id, payload_hash FROM approval_items
                WHERE id=? AND status='preview_sent'
            """, (item_id,)).fetchone()

            if not row:
                self._json(409, {"error": "not_previewable", "reason": "already_consumed_or_not_found"})
                return

            # tamper check
            if payload_hash and row["payload_hash"] and row["payload_hash"] != payload_hash:
                audit_append("tamper_detected", actor=owner, target=item_id,
                             payload={"expected": row["payload_hash"], "got": payload_hash},
                             status="blocked")
                self._json(403, {"error": "tamper_detected"})
                return

            # confirm
            conn.execute("UPDATE approval_items SET status='confirmed' WHERE id=?", (item_id,))
            conn.commit()
            audit_append("approve", actor=owner, target=item_id,
                         payload={"payload_hash": payload_hash})
            self._json(200, {"status": "confirmed", "id": item_id})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"error": "internal", "reason": str(e)[:200]})
        finally:
            conn.close()

    def _handle_reject(self, owner: str, item_id: str):
        """POST /reject/:id — reject."""
        from owner_cockpit.db import get_db, audit_append
        conn = get_db()
        try:
            conn.execute("UPDATE approval_items SET status='rejected' WHERE id=?", (item_id,))
            conn.commit()
            audit_append("reject", actor=owner, target=item_id)
            self._json(200, {"status": "rejected", "id": item_id})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"error": "internal"})
        finally:
            conn.close()

    def _handle_freeze(self, owner: str):
        """POST /freeze — kill switch (no approval needed, always in audit)."""
        from owner_cockpit.db import audit_append
        from budget import opslib
        stop_file = opslib.OPS / "STOP-ORGANISM"
        try:
            stop_file.write_text(f"owner_freeze @ {time.strftime('%Y-%m-%dT%H:%M:%SZ')}\n", "utf-8")
            audit_append("freeze", actor=owner, status="applied")
            self._json(200, {"status": "frozen", "stop_file": str(stop_file)})
        except OSError as e:
            self._json(500, {"error": "freeze_failed", "reason": str(e)[:200]})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[owner_api] {fmt % args}\n")


def main():
    if not _flag_on():
        print(f"owner_api: {FLAG} خاموش است — هیچ پورتی باز نشد (خروجِ تمیز).")
        return
    server = HTTPServer(("127.0.0.1", PORT), _OwnerAPIHandler)
    print(f"owner_api: listening on 127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nowner_api: shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
