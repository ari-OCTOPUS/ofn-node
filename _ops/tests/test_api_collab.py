#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_api_collab — behavioral tests for POST /api/collab route (WP-E3).

    Verifies:
      - POST /api/collab is in the POST whitelist (not 405)
      - Owner auth required (403 without valid initData)
      - Rate-limited (shares /api/ask window)
      - Empty text returns 400
      - Valid request delegates to collaborator.handle() and returns owner-console.reply.v1
      - Response is redacted (defense-in-depth)
      - Contract: external_effect=False, cost=0, send_attempted=False
      - GET /api/collab is 405
      - Survives unexpected exceptions with 500
"""
import hashlib
import hmac
import json
import os
import sys
import urllib.parse
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import harness

ENV = harness.setup("api-collab")

import miniapp_gateway as mg

NOW = 1_785_400_000.0
TOKEN = "123456789:AA" + "x" * 32
OWNER = "777"

os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER


def _init_data(user_id=777, auth_date=NOW - 10, token=TOKEN, tamper=False):
    data = {"auth_date": str(int(auth_date)),
            "query_id": "AAE-test",
            "user": json.dumps({"id": user_id, "first_name": "ari"},
                               ensure_ascii=False)}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode("utf-8"),
                      hashlib.sha256).digest()
    h = hmac.new(secret, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    if tamper:
        h = ("0" if h[0] != "0" else "1") + h[1:]
    data["hash"] = h
    return urllib.parse.urlencode(data)


def _fetch(body=b'{"money":{"month_aud":1}}', ctype="application/json"):
    calls = []

    def fn(path):
        calls.append(path)
        return 200, body, ctype

    fn._calls = calls
    return fn


def _collab_body(text="هدف فعلی چیه؟"):
    return json.dumps({"text": text}).encode("utf-8")


def _reset_ask_hits():
    """Reset the shared ask/collab rate-limit counter for test isolation."""
    mg._ASK_HITS[:] = []


# ─── POST whitelist ─────────────────────────────────────────────────────────

def t_collab_post_is_not_405():
    """POST /api/collab must be in the whitelist — not 405 like unknown POST paths."""
    _reset_ask_hits()
    st, _, _ = mg.handle("POST", "/api/collab",
                         {"X-Tg-Init-Data": _init_data(), "_body": _collab_body()},
                         fetch_fn=_fetch(), now=NOW)
    # Without auth it should be 403 (auth gate), NOT 405 (method not allowed)
    assert st != 405, "POST /api/collab must be whitelisted"


def t_collab_get_is_405():
    """GET /api/collab must be 405 (POST-only route)."""
    st, _, _ = mg.handle("GET", "/api/collab",
                         {"X-Tg-Init-Data": _init_data()},
                         fetch_fn=_fetch(), now=NOW)
    assert st == 405, (st,)


# ─── Owner auth ────────────────────────────────────────────────────────────────

def t_collab_requires_owner_auth():
    """POST /api/collab without valid initData must return 403."""
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"_body": _collab_body()},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 403, (st, payload)
    assert b"owner_auth_required" in payload


def t_collab_tampered_hash_is_403():
    """POST /api/collab with tampered HMAC hash must return 403."""
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"X-Tg-Init-Data": _init_data(tamper=True),
                                "_body": _collab_body()},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 403, (st, payload)


# ─── Empty text ────────────────────────────────────────────────────────────────

def t_collab_empty_text_is_400():
    """POST /api/collab with empty/whitespace text must return 400."""
    _reset_ask_hits()
    for text in ("", "  ", "\t"):
        st, payload, _ = mg.handle("POST", "/api/collab",
                                   {"X-Tg-Init-Data": _init_data(),
                                    "_body": json.dumps({"text": text}).encode("utf-8")},
                                   fetch_fn=_fetch(), now=NOW)
        assert st == 400, (text, st, payload)
        assert b"empty_text" in payload


def t_collab_missing_text_key_is_400():
    """POST /api/collab with no 'text' key must return 400."""
    _reset_ask_hits()
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"X-Tg-Init-Data": _init_data(),
                                "_body": json.dumps({"other": "x"}).encode("utf-8")},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 400, (st, payload)


# ─── Rate limiting ────────────────────────────────────────────────────────────

def t_collab_shares_ask_rate_limit():
    """POST /api/collab must use _ask_rate_limited (same window as /api/ask)."""
    src = Path(mg.__file__).read_text("utf-8")
    block = src[src.index('if p == "/api/collab":'):src.index('if p == "/api/miniapp":')]
    assert 'if _ask_rate_limited(now):' in block and '429' in block


# ─── Valid request delegates to collaborator ──────────────────────────────────

def t_collab_valid_request_returns_reply():
    """POST /api/collab with valid auth+text must return owner-console.reply.v1."""
    _reset_ask_hits()
    st, payload, ctype = mg.handle("POST", "/api/collab",
                                   {"X-Tg-Init-Data": _init_data(),
                                    "_body": _collab_body("هدف فعلی چیه؟")},
                                   fetch_fn=_fetch(), now=NOW)
    assert st == 200, (st, payload)
    d = json.loads(payload)
    assert d.get("schema") == "owner-console.reply.v1", (d,)
    assert "kind" in d, d


def t_collab_contract_compliance():
    """Reply must have external_effect=False, cost=0, send_attempted=False."""
    _reset_ask_hits()
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"X-Tg-Init-Data": _init_data(),
                                "_body": _collab_body("هدف فعلی چیه؟")},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 200, (st,)
    d = json.loads(payload)
    assert d.get("external_effect") is False, f"external_effect must be False: {d}"
    assert d.get("estimated_cost") == 0, f"estimated_cost must be 0: {d}"
    assert d.get("send_attempted") is False, f"send_attempted must be False: {d}"


def t_collab_model_source_is_deterministic_stub():
    """Default collaborator uses deterministic stub, not real model."""
    _reset_ask_hits()
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"X-Tg-Init-Data": _init_data(),
                                "_body": _collab_body("هدف فعلی چیه؟")},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 200, (st,)
    d = json.loads(payload)
    assert d.get("model_source") == "deterministic-stub", (d,)


def t_collab_response_has_rationale():
    """Stub should add rationale data to the reply."""
    _reset_ask_hits()
    st, payload, _ = mg.handle("POST", "/api/collab",
                               {"X-Tg-Init-Data": _init_data(),
                                "_body": _collab_body("وضعیت runtime رو نشون بده")},
                               fetch_fn=_fetch(), now=NOW)
    assert st == 200, (st,)
    d = json.loads(payload)
    data = d.get("data") or {}
    assert "rationale" in data, f"rationale missing from data: {data}"


# ─── Exception handling ──────────────────────────────────────────────────────

def t_collab_survives_exception_with_500():
    """If collaborator.handle() raises, route must return 500, not crash."""
    _reset_ask_hits()
    import sys as _sys
    _ops_path = str(_OPS)
    if _ops_path not in _sys.path:
        _sys.path.insert(0, _ops_path)

    from owner_console import collaborator as _col
    real_handle = _col.handle

    def boom(text, **kw):
        raise RuntimeError("simulated crash")

    _col.handle = boom
    try:
        st, payload, _ = mg.handle("POST", "/api/collab",
                                   {"X-Tg-Init-Data": _init_data(),
                                    "_body": _collab_body("test")},
                                   fetch_fn=_fetch(), now=NOW)
        assert st == 500, (st, payload)
        d = json.loads(payload)
        assert d.get("ok") is False and d.get("reason") == "RuntimeError", d
    finally:
        _col.handle = real_handle


# ─── Route is wired (not just registered) ─────────────────────────────────────

def t_collab_route_exists_in_source():
    """Source must contain 'if p == "/api/collab":' handler block."""
    src = Path(mg.__file__).read_text("utf-8")
    assert 'if p == "/api/collab":' in src, "/api/collab handler block missing"
    # Verify it's in the POST whitelist
    assert '"/api/collab"' in src, "/api/collab not in POST whitelist"


def t_collab_route_has_redact():
    """The /api/collab handler must redact the response before sending."""
    src = Path(mg.__file__).read_text("utf-8")
    block = src[src.index('if p == "/api/collab":'):src.index('if p == "/api/miniapp":')]
    assert "_redact(" in block, "/api/collab must redact response"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_api_collab: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
