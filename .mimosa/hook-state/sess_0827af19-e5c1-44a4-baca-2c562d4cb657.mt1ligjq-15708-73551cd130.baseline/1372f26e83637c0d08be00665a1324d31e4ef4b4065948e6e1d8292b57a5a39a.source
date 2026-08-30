#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_owner_api.py — WP4+WP5: HMAC auth + session + approval tamper + rate limit."""
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


class TestHMACValidation:
    """WP4: HMAC initData validation — الگوریتم رسمی Telegram."""

    def test_valid_init_data(self, monkeypatch):
        """ساختِ initData معتبر و verify."""
        import owner_cockpit.owner_api as api
        bot_token = "123456:test-token"
        owner_id = "111111"
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", bot_token)
        monkeypatch.setenv("OWNER_TELEGRAM_IDS", owner_id)

        # ساخت initData معتبر
        user_json = json.dumps({"id": int(owner_id), "first_name": "Owner"})
        params = {
            "query_id": "query123",
            "user": user_json,
            "auth_date": str(int(time.time())),
        }
        dc_items = sorted(f"{k}={v}" for k, v in params.items())
        dc_string = "\n".join(dc_items)
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, dc_string.encode("utf-8"), hashlib.sha256).hexdigest()
        params["hash"] = calc_hash

        init_data = "&".join(f"{k}={v}" for k, v in params.items())
        valid, result = api.validate_init_data(init_data, bot_token, [owner_id])
        assert valid, f"should be valid: {result}"
        assert result == owner_id

    def test_bad_hash_rejected(self):
        import owner_cockpit.owner_api as api
        init_data = "query_id=q&user={}&auth_date=999&hash=fake"
        valid, reason = api.validate_init_data(init_data, "token", ["1"])
        assert not valid
        assert reason in ("bad_hash", "stale_auth")

    def test_stale_auth_rejected(self):
        import owner_cockpit.owner_api as api
        # auth_date خیلی قدیمی
        valid, reason = api.validate_init_data(
            "hash=x&auth_date=1000", "token", ["1"])
        assert not valid
        assert reason == "stale_auth"

    def test_non_owner_rejected(self, monkeypatch):
        import owner_cockpit.owner_api as api
        bot_token = "123:test"
        owner_id = "111"
        user_json = json.dumps({"id": 222})  # نه owner
        params = {"user": user_json, "auth_date": str(int(time.time())), "query_id": "q"}
        dc_items = sorted(f"{k}={v}" for k, v in params.items())
        dc_string = "\n".join(dc_items)
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        params["hash"] = hmac.new(secret_key, dc_string.encode(), hashlib.sha256).hexdigest()
        init_data = "&".join(f"{k}={v}" for k, v in params.items())
        valid, reason = api.validate_init_data(init_data, bot_token, [owner_id])
        assert not valid
        assert reason == "not_owner"


class TestRateLimit:
    """WP4: rate limiting."""

    def test_rate_limit_blocks(self, monkeypatch):
        import owner_cockpit.owner_api as api
        api._rate_buckets.clear()
        # ۳۰ request مجاز
        for i in range(30):
            assert api._rate_check("owner-1")
        # سی‌ویکمین باید block شود
        assert not api._rate_check("owner-1")

    def test_different_owners_separate(self, monkeypatch):
        import owner_cockpit.owner_api as api
        api._rate_buckets.clear()
        for i in range(30):
            api._rate_check("owner-1")
        # owner-2 جدا است
        assert api._rate_check("owner-2")


class TestSessionFlow:
    """WP4: session create + verify."""

    def test_session_create_and_verify(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OCTOPUS_WIRE_OWNER_DB", "1")
        import owner_cockpit.db as db
        import owner_cockpit.owner_api as api
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        token = api._create_session("owner-test")
        assert token and len(token) > 20
        valid, owner = api._verify_session_token(token)
        assert valid
        assert owner == "owner-test"

    def test_bad_token_rejected(self):
        import owner_cockpit.owner_api as api
        valid, _ = api._verify_session_token("fake-token")
        assert not valid
