#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_octopus_chat_endpoint.py — POST /api/octopus/chat (ADR-040 Phase 3).

flag-gating (404 وقتی OFF)، POST allowlist، و وقتی ON + owner-auth یک ChatReply
برمی‌گرداند. Hub handle خودش جدا تست می‌شود — این فقط لایهٔ gateway.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "tests"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("octopus-chat-endpoint")

import miniapp_gateway as mg  # noqa: E402
import opslib  # noqa: E402

# توکنِ تستی هم‌شکلِ test_miniapp_gateway (الگوی رسمی).
import hashlib, hmac, urllib.parse  # noqa: E402
NOW = 1_785_400_000.0
TOKEN = "123456789:AA" + "x" * 32
OWNER = "777"
os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER


def _valid_initdata(now=NOW):
    data = {"auth_date": str(int(now - 10)), "query_id": "AAE-test",
            "user": json.dumps({"id": int(OWNER), "first_name": "ari"},
                               ensure_ascii=False)}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode("utf-8"), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(data)


def _body_headers(initdata, payload):
    return {"X-Tg-Init-Data": initdata, "_body": json.dumps(payload).encode("utf-8")}


def t_endpoint_404_when_flag_off():
    """OCTOPUS_UNIFIED_CHAT=0 → 404 FEATURE_DISABLED (حتی با owner-auth)."""
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"
    st, body, _ = mg.handle("POST", "/api/octopus/chat",
                            headers=_body_headers(_valid_initdata(), {"text": "سلام"}),
                            now=NOW)
    assert st == 404, (st, body)
    assert b"feature_disabled" in body


def t_endpoint_in_post_allowlist():
    """مسیر در allowlist است (نه 405)."""
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"
    st, _, _ = mg.handle("POST", "/api/bogus-chat",
                         headers=_body_headers(_valid_initdata(), {"text": "x"}),
                         now=NOW)
    assert st == 405   # bogus در allowlist نیست
    # ours در allowlist است ⇒ 404 (flag) نه 405
    st2, _, _ = mg.handle("POST", "/api/octopus/chat",
                          headers=_body_headers(_valid_initdata(), {"text": "x"}),
                          now=NOW)
    assert st2 == 404


def t_endpoint_403_without_owner_auth():
    """بدون initData ِ معتبر → 403 (نه 404؛ auth قبل از flag)."""
    # توجه: flag check در handler قبل از auth است در پیاده‌سازی فعلی — پس flag-off
    # اول می‌دهد. این تست را وقتی flag ON باشد امتحان می‌کنیم.
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "1"
    try:
        st, body, _ = mg.handle("POST", "/api/octopus/chat",
                                headers={"X-Tg-Init-Data": "garbage",
                                         "_body": b'{"text":"x"}'},
                                now=NOW)
        assert st == 403, (st, body)
        assert b"owner_auth" in body
    finally:
        os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"


def t_endpoint_returns_chatreply_when_on_and_authed():
    """flag ON + owner-auth → 200 + ChatReply JSON با schema_version."""
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "1"
    try:
        st, body, ct = mg.handle("POST", "/api/octopus/chat",
                                 headers=_body_headers(
                                     _valid_initdata(), {"text": "وضعیت چیست؟"}),
                                 now=NOW)
        assert st == 200, (st, body)
        data = json.loads(body.decode("utf-8"))
        assert data["schema_version"] == "octopus.chat.reply.v1"
        assert data["ok"] is True
        assert data["external_effect"] is False
        assert data["may_authorize"] is False
        assert data["route"] in ("runtime", "ask")   # «وضعیت» → runtime معمولاً
    finally:
        os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"



def t_endpoint_real_traffic_now_none_no_message_id():
    """2026-08-15 (جاروی تست T7، رگرسیونِ باگِ int(None)):
    ترافیکِ واقعی handle را بدونِ now صدا می‌زند و کلاینتِ بدونِ message_id —
    قبلاً int(None) → TypeError → 500. حالا باید 200 + ChatReply بدهد."""
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "1"
    try:
        import time as _time
        st, body, ct = mg.handle("POST", "/api/octopus/chat",
                                 headers=_body_headers(
                                     # auth_date تازه — ولیدیشن با now=None از ساعتِ واقعی می‌سنجد
                                     _valid_initdata(now=_time.time()), {"text": "سلام"}),
                                 now=None)   # ← عینِ ترافیکِ واقعی
        assert st == 200, (st, body)
        data = json.loads(body.decode("utf-8"))
        assert data["schema_version"] == "octopus.chat.reply.v1"
        assert data["ok"] is True
        # ChatReply فیلدِ message_id را برنمی‌گرداند — شناسهٔ درون‌سازِ هاب کافی است
    finally:
        os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"

def t_endpoint_empty_text_400():
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "1"
    try:
        st, body, _ = mg.handle("POST", "/api/octopus/chat",
                                headers=_body_headers(_valid_initdata(), {"text": "  "}),
                                now=NOW)
        assert st == 400
        assert b"empty_text" in body
    finally:
        os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"


TESTS = [
    t_endpoint_404_when_flag_off,
    t_endpoint_in_post_allowlist,
    t_endpoint_403_without_owner_auth,
    t_endpoint_returns_chatreply_when_on_and_authed,
    t_endpoint_empty_text_400,
    t_endpoint_real_traffic_now_none_no_message_id,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            import traceback
            print(f"  FAIL  {_t.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    os.environ["OCTOPUS_UNIFIED_CHAT"] = "0"
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
