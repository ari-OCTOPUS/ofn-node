#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security C1-C4 fixture contracts — expected RED before the patch.

No network, no live Telegram, no production memory writes, no paid calls.
All state is isolated under harness.setup(). Registered/executed counts remain
separate in the security baseline receipt.
"""
from __future__ import annotations

import hashlib
import hmac
import importlib
import json
import os
import sqlite3
import sys
import threading
import urllib.parse
from pathlib import Path

import harness

ENV = harness.setup("security-c1-c4")
_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import miniapp_gateway as mg  # noqa: E402
import tg_api  # noqa: E402

NOW = 1_785_500_000.0
TOKEN = "123456789:AA" + "s" * 32
OWNER = "777"
os.environ["TG_CENTER_BOT_TOKEN"] = TOKEN
os.environ["TELEGRAM_OWNER_CHAT_ID"] = OWNER


def _init_data(*, auth_date=NOW, user=None, token=TOKEN, extra=None,
               tamper_hash=False, duplicate_pair=None):
    data = {
        "auth_date": str(auth_date),
        "query_id": "AAE-security-fixture",
        "user": json.dumps(user if user is not None else {"id": 777, "first_name": "آری"},
                           ensure_ascii=False),
    }
    if extra:
        data.update(extra)
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    digest = hmac.new(secret, dcs.encode("utf-8"), hashlib.sha256).hexdigest()
    if tamper_hash:
        digest = ("0" if digest[0] != "0" else "1") + digest[1:]
    pairs = list(data.items())
    if duplicate_pair is not None:
        # Sign the canonical last-value view, but emit the same key twice.
        key, first_value = duplicate_pair
        last_value = data[key]
        pairs = [(k, v) for k, v in pairs if k != key]
        pairs.extend([(key, first_value), (key, last_value)])
    pairs.append(("hash", digest))
    return urllib.parse.urlencode(pairs)


def _fetch():
    calls = []

    def fn(path):
        calls.append(path)
        return 200, b'{"ok":true}', "application/json"

    fn.calls = calls
    return fn


# ── C1: initData freshness/HMAC ────────────────────────────────────────────
def t_c1_valid_age_zero_boundary():
    assert mg.validate_init_data(_init_data(auth_date=NOW), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is not None


def t_c1_valid_age_299():
    assert mg.validate_init_data(_init_data(auth_date=NOW - 299), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is not None


def t_c1_expired_age_301_rejected():
    assert mg.validate_init_data(_init_data(auth_date=NOW - 301), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is None


def t_c1_valid_future_skew_minus_29():
    assert mg.validate_init_data(_init_data(auth_date=NOW + 29), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is not None


def t_c1_future_skew_minus_31_rejected():
    assert mg.validate_init_data(_init_data(auth_date=NOW + 31), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is None


def t_c1_auth_date_zero_and_malformed_rejected():
    for value in (0, "not-a-number"):
        assert mg.validate_init_data(_init_data(auth_date=value), bot_token=TOKEN,
                                     owner_id=OWNER, now=NOW) is None


def t_c1_tampered_and_fake_hash_rejected():
    assert mg.validate_init_data(_init_data(tamper_hash=True), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is None
    raw = _init_data()
    assert mg.validate_init_data(raw.replace("first_name", "first_namf", 1),
                                 bot_token=TOKEN, owner_id=OWNER, now=NOW) is None


def t_c1_wrong_or_missing_owner_rejected():
    assert mg.validate_init_data(_init_data(user={"id": 888}), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is None
    assert mg.validate_init_data(_init_data(user={}), bot_token=TOKEN,
                                 owner_id=OWNER, now=NOW) is None


def t_c1_duplicate_keys_fail_closed():
    raw = _init_data(duplicate_pair=("auth_date", str(int(NOW - 100))))
    assert mg.validate_init_data(raw, bot_token=TOKEN, owner_id=OWNER, now=NOW) is None


def t_c1_unicode_input_and_compare_digest():
    called = []
    real = mg.hmac.compare_digest

    def spy(a, b):
        called.append(True)
        return real(a, b)

    mg.hmac.compare_digest = spy
    try:
        raw = _init_data(extra={"start_param": "آزمایش-امن"})
        assert mg.validate_init_data(raw, bot_token=TOKEN, owner_id=OWNER, now=NOW)
    finally:
        mg.hmac.compare_digest = real
    assert called, "HMAC comparison must use hmac.compare_digest"


def t_c1_public_auth_failure_is_empty_403_zero_dispatch():
    for headers in ({}, {"X-Tg-Init-Data": _init_data(tamper_hash=True)}):
        fetch = _fetch()
        status, body, _ = mg.handle("GET", "/api/miniapp", headers,
                                    fetch_fn=fetch, now=NOW)
        assert status == 403 and body == b""
        assert fetch.calls == []


# ── C2: decision-bound one-time nonce ledger ───────────────────────────────
def _decision_module():
    try:
        return importlib.import_module("miniapp_decision_ledger")
    except ModuleNotFoundError as exc:
        raise AssertionError("C2 decision nonce ledger is not implemented") from exc


def _ledger(clock=NOW):
    mod = _decision_module()
    return mod.DecisionLedger(Path(ENV["ops"]) / "state" / "decision-ledger.db",
                              clock=lambda: float(clock))


def _issue(ledger, nonce="nonce-security-fixture", expires_at=NOW + 60):
    return ledger.issue(proposal_id="prop_fixture", card_id="card_fixture",
                        nonce=nonce, owner_ref="owner:fixture",
                        scope_hash="a" * 64, expires_at=expires_at)


def t_c2_nonce_binding_first_consume_and_no_raw_nonce():
    ledger = _ledger()
    issued = _issue(ledger)
    assert issued["state"] == "PENDING"
    out = ledger.consume(proposal_id="prop_fixture", card_id="card_fixture",
                         nonce="nonce-security-fixture", owner_ref="owner:fixture",
                         scope_hash="a" * 64)
    assert out["ok"] and out["state"] == "CONSUMED"
    raw = Path(ledger.path).read_bytes()
    assert b"nonce-security-fixture" not in raw
    ledger.close()


def t_c2_replay_after_consumed_is_409():
    ledger = _ledger()
    _issue(ledger)
    kwargs = dict(proposal_id="prop_fixture", card_id="card_fixture",
                  nonce="nonce-security-fixture", owner_ref="owner:fixture",
                  scope_hash="a" * 64)
    assert ledger.consume(**kwargs)["ok"]
    replay = ledger.consume(**kwargs)
    assert not replay["ok"] and replay["status_code"] == 409
    assert replay["state"] == "REPLAY_REJECTED"
    ledger.close()


def t_c2_expired_nonce_has_fixed_410_contract():
    ledger = _ledger(clock=NOW)
    _issue(ledger, expires_at=NOW - 1)
    out = ledger.consume(proposal_id="prop_fixture", card_id="card_fixture",
                         nonce="nonce-security-fixture", owner_ref="owner:fixture",
                         scope_hash="a" * 64)
    assert not out["ok"] and out["status_code"] == 410 and out["state"] == "EXPIRED"
    ledger.close()


def t_c2_owner_scope_and_card_mismatch_fail_closed():
    ledger = _ledger()
    _issue(ledger)
    base = dict(proposal_id="prop_fixture", card_id="card_fixture",
                nonce="nonce-security-fixture", owner_ref="owner:fixture",
                scope_hash="a" * 64)
    for key, value in (("owner_ref", "owner:other"), ("scope_hash", "b" * 64),
                       ("card_id", "card_other"), ("proposal_id", "prop_other")):
        args = dict(base); args[key] = value
        out = ledger.consume(**args)
        assert not out["ok"] and out["status_code"] == 409
    ledger.close()


def t_c2_concurrent_consumers_have_one_winner():
    ledger = _ledger()
    _issue(ledger)
    results = []
    lock = threading.Lock()
    start = threading.Event()

    def worker():
        start.wait()
        out = ledger.consume(proposal_id="prop_fixture", card_id="card_fixture",
                             nonce="nonce-security-fixture", owner_ref="owner:fixture",
                             scope_hash="a" * 64)
        with lock:
            results.append(out)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads: thread.start()
    start.set()
    for thread in threads: thread.join()
    assert sum(1 for row in results if row.get("ok")) == 1
    assert sum(1 for row in results if row.get("state") == "REPLAY_REJECTED") == 7
    ledger.close()


# ── C3: full retry_after (no cap of Telegram prohibition) ──────────────────
def t_c3_retry_after_75_is_not_capped():
    data = {"error_code": 429, "parameters": {"retry_after": 75}}
    assert tg_api._retry_after_from_429(data) == 75.0


# ── C4: durable scheduler / queue ──────────────────────────────────────────
def _queue_module():
    try:
        return importlib.import_module("rate_limit_queue")
    except ModuleNotFoundError as exc:
        raise AssertionError("C4 durable rate-limit queue is not implemented") from exc


def _queue(now=NOW):
    mod = _queue_module()
    return mod.RateLimitQueue(Path(ENV["ops"]) / "state" / "rate-queue.db",
                              clock=lambda: float(now), jitter=lambda: 0.0)


def t_c4_duplicate_enqueue_and_fifo():
    q = _queue()
    a = q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1", priority=10)
    dup = q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1", priority=10)
    b = q.enqueue(message_key="m2", chat_hash="c1", payload_hash="p2", priority=10)
    assert not a["duplicate"] and dup["duplicate"]
    assert [row["message_key"] for row in q.due(limit=10)] == ["m1", "m2"]
    q.close()


def t_c4_retry_not_before_survives_restart():
    path = Path(ENV["ops"]) / "state" / "rate-restart.db"
    mod = _queue_module()
    q = mod.RateLimitQueue(path, clock=lambda: NOW, jitter=lambda: 0.0)
    q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    q.defer("m1", retry_after=75)
    q.close()
    q2 = mod.RateLimitQueue(path, clock=lambda: NOW + 74, jitter=lambda: 0.0)
    assert q2.due(limit=10) == []
    q2.set_clock(lambda: NOW + 75)
    assert [r["message_key"] for r in q2.due(limit=10)] == ["m1"]
    q2.close()


def t_c4_business_and_delivery_attempts_are_separate():
    q = _queue()
    q.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1",
              business_attempts=1)
    q.mark_delivery_attempt("m1")
    row = q.get("m1")
    assert row["business_attempts"] == 1 and row["delivery_attempts"] == 1
    q.close()


def t_c4_42_findings_coalesce_to_one_digest():
    q = _queue()
    for i in range(42):
        q.enqueue_finding(group_key="scanner:seam", finding_key=f"f{i}", now=NOW + i)
    rows = q.pending_digests()
    assert len(rows) == 1
    assert rows[0]["count"] == 42 and rows[0]["first_seen"] == NOW
    assert rows[0]["last_seen"] == NOW + 41
    q.close()


def t_c4_poison_goes_dlq_and_confirmed_never_resends():
    q = _queue()
    q.enqueue(message_key="bad", chat_hash="c1", payload_hash="p1")
    q.dead_letter("bad", reason="poison")
    q.enqueue(message_key="ok", chat_hash="c1", payload_hash="p2")
    q.confirm("ok", message_id=900)
    assert q.due(limit=10) == []
    assert q.get("bad")["state"] == "DLQ"
    assert q.get("ok")["state"] == "CONFIRMED"
    q.close()


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_security_c1_c4: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
