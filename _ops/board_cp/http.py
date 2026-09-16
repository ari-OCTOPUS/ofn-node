"""HTTP برای gateway: enqueue مالک (initData) و pull/ack برد (Bearer)."""
from __future__ import annotations

import json

from . import config
from . import service

_JSON = "application/json; charset=utf-8"
_OUR = frozenset({
    "/api/board/commands",
    "/api/board-cp/pull",
    "/api/board-cp/ack",
})


def _header(headers, name: str) -> str:
    try:
        return str(headers.get(name) or headers.get(name.lower()) or "")
    except Exception:  # noqa: BLE001
        return ""


def _body(headers) -> dict:
    raw = b""
    try:
        raw = headers.get("_body") or b""
    except Exception:  # noqa: BLE001
        raw = b""
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8") or "{}")
    except Exception:  # noqa: BLE001
        return {}


def _json(status: int, obj: dict) -> tuple:
    return status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), _JSON


def dispatch(method: str, path: str, headers, *, owner_ok: bool = False) -> tuple | None:
    p = str(path or "").split("?", 1)[0]
    if p not in _OUR:
        return None
    m = str(method or "").upper()
    if p == "/api/board/commands":
        return _enqueue(m, headers, owner_ok=owner_ok)
    if p == "/api/board-cp/pull":
        return _pull(m, headers)
    if p == "/api/board-cp/ack":
        return _ack(m, headers)
    return None


def _enqueue(method: str, headers, *, owner_ok: bool) -> tuple:
    if method != "POST":
        return 405, b"", "text/plain; charset=utf-8"
    if not owner_ok:
        return _json(403, {"ok": False, "reason": "owner_auth_required"})
    body = _body(headers)
    kind = str(body.get("kind") or "ask").strip().lower()
    try:
        result = service.enqueue(
            kind=kind,
            text=str(body.get("text") or body.get("action") or ""),
            target_agent=str(body.get("target_agent") or "ofn"),
            target_instance=str(body.get("target_instance") or "panel"),
            source="miniapp",
        )
    except ValueError as exc:
        return _json(400, {"ok": False, "reason": str(exc)})
    result["ok"] = True
    result["queued_for_pull"] = bool(result.get("armed") and not result.get("owner_required"))
    return _json(200, result)


def _board_auth(headers) -> bool:
    auth = _header(headers, "Authorization") or _header(headers, "authorization")
    return config.bearer_ok(auth)


def _pull(method: str, headers) -> tuple:
    if method != "GET":
        return 405, b"", "text/plain; charset=utf-8"
    if not _board_auth(headers):
        return _json(401, {"ok": False, "reason": "board_bearer_required"})
    return _json(200 if config.is_armed() else 503, service.pull())


def _ack(method: str, headers) -> tuple:
    if method != "POST":
        return 405, b"", "text/plain; charset=utf-8"
    if not _board_auth(headers):
        return _json(401, {"ok": False, "reason": "board_bearer_required"})
    body = _body(headers)
    mid = str(body.get("message_id") or "").strip()
    if not mid:
        return _json(400, {"ok": False, "reason": "message_id"})
    out = service.ack(mid, outcome=str(body.get("outcome") or ""))
    return _json(200 if out.get("ok") else 400, out)
