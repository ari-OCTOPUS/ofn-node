"""Shopify OAuth bridge for Ziman — public HTTPS via ziman.master-painting.com.

Routes (unauthenticated, host must be the ziman tenant):
  GET /api/v1/shopify/app              — app_url landing (no secrets)
  GET /api/v1/shopify/oauth/start      — begin install (optional ?shop=)
  GET /api/v1/shopify/oauth/callback   — exchange code, store Admin token

Credentials come from env (secrets.env / node.env). Access token is written
only to secrets.env as OFN_SHOPIFY_ADMIN_TOKEN — never returned in JSON body
beyond a boolean ok, never logged.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Mapping

from ofn.adapters.http_api import Response

_SHOP_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*\.myshopify\.com$")
_DEFAULT_SCOPES = "read_products,write_products,read_orders"
_APP_PATH = "/api/v1/shopify/app"
_START_PATH = "/api/v1/shopify/oauth/start"
_CALLBACK_PATH = "/api/v1/shopify/oauth/callback"
_PUBLIC_BASE = "https://ziman.master-painting.com"
# secrets.env is under ProtectHome=read-only for ofn.service; state dir is writable.
_SECRETS_PATH = Path.home() / ".config/ofn/secrets.env"
_STATE_TOKEN_PATH = Path(
    os.environ.get("OFN_STATE_DIR") or str(Path.home() / ".local/share/ofn")
) / "shopify_oauth.env"


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _configured_shop() -> str:
    shop = _env("OFN_SHOPIFY_SHOP_DOMAIN").lower()
    if shop and _SHOP_RE.match(shop):
        return shop
    return ""


def _allowed_shops() -> set[str]:
    """Primary + aliases (Shopify may return permanent *.myshopify.com handle)."""
    out: set[str] = set()
    primary = _configured_shop()
    if primary:
        out.add(primary)
    for part in (_env("OFN_SHOPIFY_SHOP_ALIASES") or "").split(","):
        s = part.strip().lower()
        if _SHOP_RE.match(s):
            out.add(s)
    return out


def _client_id() -> str:
    return _env("OFN_SHOPIFY_CLIENT_ID")


def _client_secret() -> str:
    return _env("OFN_SHOPIFY_CLIENT_SECRET")


def _scopes() -> str:
    return _env("OFN_SHOPIFY_SCOPES") or _DEFAULT_SCOPES


def _state_key() -> bytes:
    raw = _env("OFN_SHOPIFY_OAUTH_STATE_SECRET") or _client_secret()
    return raw.encode("utf-8") if raw else b""


def _make_state(shop: str) -> str:
    ts = str(int(time.time()))
    msg = f"{shop}|{ts}".encode("utf-8")
    sig = hmac.new(_state_key(), msg, hashlib.sha256).hexdigest()[:32]
    # Use | separators — shop hostnames contain dots.
    return f"{shop}|{ts}|{sig}"


def _parse_state(state: str) -> str | None:
    raw = urllib.parse.unquote(state or "")
    parts = raw.split("|")
    if len(parts) != 3:
        return None
    shop, ts, sig = parts
    if not _SHOP_RE.match(shop):
        return None
    try:
        age = abs(int(time.time()) - int(ts))
    except ValueError:
        return None
    if age > 3600:
        return None
    msg = f"{shop}|{ts}".encode("utf-8")
    expect = hmac.new(_state_key(), msg, hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expect, sig):
        return None
    return shop


def handle_shopify_http(
    method: str,
    path: str,
    query: Mapping[str, str] | str,
    *,
    tenant_name: str | None,
) -> Response:
    if isinstance(query, str):
        parsed = urllib.parse.parse_qs(query or "")
        query = {k: (v[0] if v else "") for k, v in parsed.items()}
    elif not isinstance(query, dict):
        query = {}
    if method != "GET":
        return Response(405, {"error": "method not allowed"})
    if tenant_name != "ziman":
        return Response(404, {"error": "not found"})
    if path.rstrip("/") == _APP_PATH.rstrip("/") or path == _APP_PATH:
        return Response(
            200,
            {
                "ok": True,
                "app": "OCTOPUS",
                "tenant": "ziman",
                "shop": _configured_shop() or None,
                "oauth_start": _PUBLIC_BASE + _START_PATH,
            },
        )
    if path == _START_PATH:
        return _oauth_start(query)
    if path == _CALLBACK_PATH:
        return _oauth_callback(query)
    return Response(404, {"error": "unknown shopify path"})


def _oauth_start(query: Mapping[str, str]) -> Response:
    if not _state_key() or not _client_id():
        return Response(
            503,
            {
                "ok": False,
                "error": "shopify oauth not configured",
                "rule": "shopify:missing-client",
            },
        )
    shop = (query.get("shop") or _configured_shop()).lower().strip()
    if not _SHOP_RE.match(shop):
        return Response(400, {"ok": False, "error": "invalid shop"})
    allowed = _allowed_shops()
    if allowed and shop not in allowed:
        return Response(
            403,
            {"ok": False, "error": "shop mismatch", "rule": "shopify:shop-mismatch"},
        )
    redirect_uri = _PUBLIC_BASE + _CALLBACK_PATH
    params = {
        "client_id": _client_id(),
        "scope": _scopes(),
        "redirect_uri": redirect_uri,
        "state": _make_state(shop),
    }
    url = (
        f"https://{shop}/admin/oauth/authorize?"
        + urllib.parse.urlencode(params)
    )
    return Response(302, None, headers={"Location": url})


def _oauth_callback(query: Mapping[str, str]) -> Response:
    if not _client_id() or not _client_secret():
        return _html(503, "Shopify OAuth not configured on this node.")
    state_shop = _parse_state(query.get("state") or "")
    if not state_shop:
        return _html(400, "Invalid or expired OAuth state.")
    shop = (query.get("shop") or "").lower().strip()
    allowed = _allowed_shops()
    if not allowed or shop not in allowed or state_shop not in allowed:
        return _html(400, "Shop/state mismatch.")
    code = (query.get("code") or "").strip()
    if not code:
        return _html(400, "Missing OAuth code.")
    token, err = _exchange(shop, code)
    if err or not token:
        return _html(502, f"Token exchange failed: {err or 'empty'}")
    try:
        _store_admin_token(token)
    except Exception:
        return _html(500, "Token received but failed to store securely.")
    return _html(
        200,
        "OCTOPUS connected to Shopify for Ziman Gift. "
        "Admin API token stored on the board. You can close this tab.",
    )


def _exchange(shop: str, code: str) -> tuple[str, str]:
    url = f"https://{shop}/admin/oauth/access_token"
    payload = json.dumps(
        {
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "code": code,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return "", f"http {exc.code}"
    except Exception:
        return "", "network"
    token = str(body.get("access_token") or "").strip()
    if not token:
        return "", "no access_token"
    return token, ""


def _store_admin_token(token: str) -> None:
    """Persist Admin token where the sandboxed service can write.

    ofn.service uses ProtectHome=read-only; only OFN_STATE_DIR is writable.
    Best-effort mirror into secrets.env when that path is writable.
    """
    path = _STATE_TOKEN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        '# Shopify Admin API token via OAuth callback - do not commit\n'
        + 'OFN_SHOPIFY_ADMIN_TOKEN=' + token + '\n'
    )
    path.write_text(body, encoding='utf-8')
    os.chmod(path, 0o600)
    try:
        sec = _SECRETS_PATH
        if sec.parent.exists() and os.access(str(sec.parent), os.W_OK):
            old = sec.read_text(encoding='utf-8') if sec.exists() else ''
            kept = [
                line for line in old.splitlines()
                if not line.startswith('OFN_SHOPIFY_ADMIN_TOKEN=')
            ]
            while kept and kept[-1].strip() == '':
                kept.pop()
            text = (
                '\n'.join(kept).rstrip()
                + '\n\n# Shopify Admin API token via OAuth callback\n'
                + 'OFN_SHOPIFY_ADMIN_TOKEN=' + token + '\n'
            )
            sec.write_text(text, encoding='utf-8')
            os.chmod(sec, 0o600)
    except OSError:
        pass


def _html(status: int, message: str) -> Response:
    safe = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    html = (
        "<!doctype html><html><head><meta charset=utf-8>"
        "<title>OCTOPUS Shopify</title></head><body>"
        f"<h1>OCTOPUS x Shopify</h1><p>{safe}</p></body></html>"
    )
    return Response(
        status,
        None,
        raw=html.encode("utf-8"),
        content_type="text/html; charset=utf-8",
    )
