#!/usr/bin/env python3
"""Typed Telegram poll outcomes and legacy compatibility."""
from __future__ import annotations

import io
import json
import os
import socket
import sys
import urllib.error
from pathlib import Path

import harness

ENV = harness.setup("typed-poll-outcome")
_OPS = Path(__file__).resolve().parent.parent
for _path in (str(_OPS), str(_OPS / "telegram_center")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import poll_lease  # noqa: E402
import poll_schedule  # noqa: E402
from poll_outcome import PollOutcome  # noqa: E402
from tg_api import TgClient  # noqa: E402

TOKEN = "123456789:AA" + "P" * 32
_SEQ = 0


def _token(label: str) -> str:
    global _SEQ
    _SEQ += 1
    return f"{TOKEN}-{label}-{_SEQ}"


def _client(response=None, *, exc=None, token=None):
    calls = []

    def get(url, timeout):
        calls.append((url, timeout))
        if exc is not None:
            raise exc
        return response

    client = TgClient(
        token=token or _token("client"), owner_chat_id=1, get_fn=get,
        post_fn=lambda *_args, **_kwargs: {"ok": True, "result": {}},
    )
    return client, calls


def _http_error(code: int, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    return urllib.error.HTTPError(
        "https://redacted.invalid", code, "fixture", {}, io.BytesIO(body))


def t_a_contract_validates_kinds_and_updates():
    ok = PollOutcome("OK", updates=({"update_id": 1}, "junk"))
    assert ok.ok is True and ok.retryable is False
    assert ok.updates == ({"update_id": 1},)
    assert ok.legacy_updates() == [{"update_id": 1}]
    assert PollOutcome("TIMEOUT").retryable is True
    try:
        PollOutcome("HTTP_4XX", updates=({"update_id": 1},))
        raise AssertionError("non-OK outcome cannot carry updates")
    except ValueError:
        pass
    try:
        PollOutcome("UNKNOWN")
        raise AssertionError("unknown kind must fail")
    except ValueError:
        pass
    try:
        PollOutcome("RATE_LIMITED", retry_after_s=0)
        raise AssertionError("non-positive retry must fail")
    except ValueError:
        pass


def t_b_empty_and_nonempty_success_are_ok():
    empty, calls = _client({"ok": True, "result": []})
    result = empty.poll_updates_typed(offset=5, timeout_s=2)
    assert result.kind == "OK" and result.updates == ()
    assert len(calls) == 1
    full, _ = _client({"ok": True, "result": [
        {"update_id": 7}, "junk", {"update_id": 8},
    ]})
    result = full.poll_updates_typed()
    assert result.kind == "OK"
    assert [row["update_id"] for row in result.updates] == [7, 8]


def t_c_lease_denial_performs_zero_network():
    token = _token("lease")
    acquired = poll_lease.assert_poll_lease(
        token, request_deadline=10**20)
    assert acquired["ok"] is True
    client, calls = _client({"ok": True, "result": []}, token=token)
    outcome = client.poll_updates_typed()
    assert outcome.kind == "LEASE_DENIED"
    assert outcome.reason == "request-in-flight"
    assert calls == []


def t_d_fallback_shared_token_refuses_before_network():
    main = os.environ.get("TELEGRAM_BOT_TOKEN")
    center = os.environ.get("TG_CENTER_BOT_TOKEN")
    os.environ["TELEGRAM_BOT_TOKEN"] = _token("fallback")
    os.environ.pop("TG_CENTER_BOT_TOKEN", None)
    calls = []
    try:
        client = TgClient(owner_chat_id=1, get_fn=lambda *_a: calls.append(1))
        outcome = client.poll_updates_typed()
    finally:
        if main is None:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        else:
            os.environ["TELEGRAM_BOT_TOKEN"] = main
        if center is None:
            os.environ.pop("TG_CENTER_BOT_TOKEN", None)
        else:
            os.environ["TG_CENTER_BOT_TOKEN"] = center
    assert outcome.kind == "LEASE_DENIED"
    assert outcome.reason == "dedicated-token-required"
    assert calls == []


def t_e_json_error_kinds_and_retry_after():
    cases = [
        ({"ok": False, "error_code": 409}, "CONFLICT", "positive"),
        ({"ok": False, "error_code": 429,
          "parameters": {"retry_after": 75}}, "RATE_LIMITED", 75.0),
        ({"ok": False, "error_code": 500}, "HTTP_5XX", "positive"),
        ({"ok": False, "error_code": 400}, "HTTP_4XX", "positive"),
        ({"ok": False}, "MALFORMED", "positive"),
    ]
    for payload, kind, retry in cases:
        client, _ = _client(payload)
        outcome = client.poll_updates_typed()
        assert outcome.kind == kind, (payload, outcome)
        if retry == "positive":
            assert outcome.retry_after_s is not None and outcome.retry_after_s > 0
        else:
            assert outcome.retry_after_s == retry


def t_f_http_error_body_preserves_conflict_and_rate_limit():
    conflict, _ = _client(exc=_http_error(409, {
        "ok": False, "error_code": 409, "description": "Conflict",
    }))
    conflict_outcome = conflict.poll_updates_typed()
    assert conflict_outcome.kind == "CONFLICT"
    assert conflict_outcome.retry_after_s is not None
    limited, _ = _client(exc=_http_error(429, {
        "ok": False, "error_code": 429,
        "parameters": {"retry_after": 120},
    }))
    outcome = limited.poll_updates_typed()
    assert outcome.kind == "RATE_LIMITED"
    assert outcome.retry_after_s == 120.0


def t_g_dns_timeout_and_generic_transport_are_distinct():
    dns, _ = _client(exc=urllib.error.URLError(
        socket.gaierror(socket.EAI_NONAME, "fixture")))
    assert dns.poll_updates_typed().kind == "DNS_ERROR"
    timeout, _ = _client(exc=TimeoutError("fixture timeout"))
    assert timeout.poll_updates_typed().kind == "TIMEOUT"
    generic, _ = _client(exc=OSError("fixture transport"))
    assert generic.poll_updates_typed().kind == "HTTP_5XX"


def t_h_malformed_payload_shapes_are_explicit():
    not_dict, _ = _client(["not", "dict"])
    assert not_dict.poll_updates_typed().kind == "MALFORMED"
    bad_result, _ = _client({"ok": True, "result": {"not": "list"}})
    outcome = bad_result.poll_updates_typed()
    assert outcome.kind == "MALFORMED"
    assert outcome.reason == "result-not-list"
    assert outcome.retry_after_s is not None


def t_i_typed_429_never_sleeps_legacy_adapter_may_sleep_short():
    payload = {"ok": False, "error_code": 429,
               "parameters": {"retry_after": 3}}
    typed, _ = _client(payload)
    slept = []
    typed._sleep = slept.append
    assert typed.poll_updates_typed().kind == "RATE_LIMITED"
    assert slept == []
    legacy, _ = _client(payload)
    legacy._sleep = slept.append
    assert legacy.poll_updates() == []
    assert slept == [3.0]


def t_j_retry_schedule_blocks_next_client_before_network():
    token = _token("durable")
    first, first_calls = _client({
        "ok": False, "error_code": 429,
        "parameters": {"retry_after": 30},
    }, token=token)
    outcome = first.poll_updates_typed()
    assert outcome.kind == "RATE_LIMITED"
    assert len(first_calls) == 1
    second, second_calls = _client(
        {"ok": True, "result": []}, token=token)
    blocked = second.poll_updates_typed()
    assert blocked.kind == "RATE_LIMITED"
    assert second_calls == []


def t_k_webhook_preflight_blocks_without_getupdates_or_mutation():
    calls = []
    token = _token("webhook")
    client = TgClient(
        token=token, owner_chat_id=1,
        get_fn=lambda *_args: calls.append("getUpdates"),
        post_fn=lambda *_args, **_kwargs: calls.append("post"),
        poll_preflight_fn=lambda: {"webhook": True, "url_set": True},
    )
    outcome = client.poll_updates_typed()
    assert outcome.kind == "WEBHOOK_PRESENT"
    assert outcome.retry_after_s == poll_schedule._MAX_DELAY_S
    assert calls == []
    assert poll_schedule.snapshot(token)["kind"] == "WEBHOOK_PRESENT"


def t_l_preflight_failure_is_typed_and_scheduled():
    token = _token("preflight-error")
    client = TgClient(
        token=token, owner_chat_id=1,
        get_fn=lambda *_args: (_ for _ in ()).throw(
            AssertionError("network must not run")),
        poll_preflight_fn=lambda: (_ for _ in ()).throw(
            RuntimeError("fixture preflight")),
    )
    outcome = client.poll_updates_typed()
    assert outcome.kind == "HTTP_5XX"
    assert outcome.retry_after_s is not None
    assert poll_schedule.snapshot(token)["kind"] == "HTTP_5XX"


def t_m_long_429_is_never_partially_slept():
    client, _ = _client({
        "ok": False, "error_code": 429,
        "parameters": {"retry_after": 3600},
    })
    slept = []
    client._sleep = slept.append
    assert client.poll_updates() == []
    assert slept == []


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_typed_poll_outcome: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
