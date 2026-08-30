#!/usr/bin/env python3
"""Regression: Telegram PEP has a real, default-off, fail-closed lease seam."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for path in (HERE, OPS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import harness  # noqa: E402

ENV = harness.setup("telegram-pep-real-lease-20260823")

import budget.approval_channel as approval_channel  # noqa: E402
import budget.telegram_pep_shadow as pep  # noqa: E402
from telegram_center.tg_api import TgClient  # noqa: E402


def _reset() -> None:
    for name in (pep.ENFORCE_FLAG, pep.KILL_FLAG, pep.KEY_ENV):
        os.environ.pop(name, None)
    pep._REAL_STORE = None
    pep._REAL_KEY_FINGERPRINT = ""
    pep._REAL_REVOKED.clear()


def _client(calls: list) -> TgClient:
    def post(url, body):
        calls.append((url.rsplit("/", 1)[-1], dict(body)))
        return {"ok": True, "result": {"message_id": 1}}

    return TgClient(token="test-token", owner_chat_id=1, post_fn=post)


def t_shadow_default_preserves_transport() -> None:
    _reset()
    calls: list = []
    result = _client(calls)._call_post("sendMessage", {"chat_id": 1, "text": "x"})
    assert result and result["ok"] is True
    assert len(calls) == 1


def t_enforce_without_lease_blocks_before_transport() -> None:
    _reset()
    os.environ[pep.ENFORCE_FLAG] = "1"
    calls: list = []
    result = _client(calls)._call_post("sendMessage", {"chat_id": 1, "text": "x"})
    assert result is None
    assert calls == []


def t_valid_lease_allows_once_then_replay_blocks() -> None:
    _reset()
    os.environ[pep.ENFORCE_FLAG] = "1"
    os.environ[pep.KEY_ENV] = "test-only-hmac-key-32-bytes-long"
    body = {"chat_id": 1, "text": "x"}
    lease = pep.issue_real_lease("sendMessage", body)
    assert lease is not None
    calls: list = []
    client = _client(calls)
    with pep.use_real_lease(lease):
        first = client._call_post("sendMessage", body)
    with pep.use_real_lease(lease):
        replay = client._call_post("sendMessage", body)
    assert first and first["ok"] is True
    assert replay is None
    assert len(calls) == 1


def t_hash_action_expiry_revoke_and_kill_all_deny() -> None:
    _reset()
    os.environ[pep.ENFORCE_FLAG] = "1"
    os.environ[pep.KEY_ENV] = "test-only-hmac-key-32-bytes-long"
    body = {"chat_id": 1, "text": "original"}

    mismatch = pep.issue_real_lease("sendMessage", body)
    assert mismatch is not None
    with pep.use_real_lease(mismatch):
        r1 = pep.hook("test", "editMessageText", body)
    assert r1["verdict"] == "deny" and "hash-mismatch" in r1["reason"]

    expired = pep.issue_real_lease("sendMessage", body, ttl_s=1.0, now=1.0)
    assert expired is not None
    with pep.use_real_lease(expired):
        r2 = pep.hook("test", "sendMessage", body)
    assert r2["verdict"] == "deny" and r2["reason"] == "expired"

    revoked = pep.issue_real_lease("sendMessage", body)
    assert revoked is not None and pep.revoke_real_lease(revoked.lease_id)
    with pep.use_real_lease(revoked):
        r3 = pep.hook("test", "sendMessage", body)
    assert r3["verdict"] == "deny" and "revoked" in r3["reason"]

    killed = pep.issue_real_lease("sendMessage", body)
    assert killed is not None
    os.environ[pep.KILL_FLAG] = "1"
    with pep.use_real_lease(killed):
        r4 = pep.hook("test", "sendMessage", body)
    assert r4["verdict"] == "deny" and r4["reason"] == "lease-kill-active"


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps({"ok": True, "result": {"message_id": 2}}).encode("utf-8")


def t_approval_boundary_uses_same_context_lease() -> None:
    _reset()
    os.environ[pep.ENFORCE_FLAG] = "1"
    os.environ[pep.KEY_ENV] = "test-only-hmac-key-32-bytes-long"
    body = {"chat_id": 1, "text": "approval"}
    url = "https://api.telegram.org/bottest/sendMessage"
    lease = pep.issue_real_lease("sendMessage", body)
    assert lease is not None
    calls: list = []

    def fake_urlopen(*_args, **_kwargs):
        calls.append(True)
        return _Response()

    with mock.patch.object(approval_channel.urllib.request, "urlopen", fake_urlopen):
        denied = approval_channel._url_json_post(url, body)
        with pep.use_real_lease(lease):
            allowed = approval_channel._url_json_post(url, body)
    assert denied == {"ok": False, "description": "PEP_DENIED"}
    assert allowed["ok"] is True
    assert len(calls) == 1


def t_enforcement_error_is_fail_closed() -> None:
    _reset()
    os.environ[pep.ENFORCE_FLAG] = "1"
    calls: list = []
    with mock.patch.object(pep, "hook", side_effect=RuntimeError("test")):
        result = _client(calls)._call_post(
            "sendMessage", {"chat_id": 1, "text": "x"})
    assert result is None
    assert calls == []


if __name__ == "__main__":
    checks = [
        t_shadow_default_preserves_transport,
        t_enforce_without_lease_blocks_before_transport,
        t_valid_lease_allows_once_then_replay_blocks,
        t_hash_action_expiry_revoke_and_kill_all_deny,
        t_approval_boundary_uses_same_context_lease,
        t_enforcement_error_is_fail_closed,
    ]
    try:
        for check in checks:
            check()
            print("PASS", check.__name__)
    finally:
        _reset()
    print(f"PASS telegram real lease seam {len(checks)}/{len(checks)}")
