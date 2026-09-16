#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression: LOOP-TELEGRAM-PROBE-INVALID — heartbeat must not spam Telegram.

Tests encode the incident contract BEFORE relying on live send.
No network. No paid calls. No memory.db writes.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_SCRIPTS = _OPS / "scripts"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_OPS))

import tg_bridge_once as br  # noqa: E402
from loops import telegram_organ as to  # noqa: E402


def _snap(**kw):
    base = {
        "beat": 43303,
        "tg_events": 11,
        "sc_events": 1,
        "probe": "PROBE_RESPONSE_INVALID",
        "probe_id": "probe-5539dd4362da5e7c",
        "task_id": "event-time-probe-20260820",
        "run_id": "fcc77e9a-dd4b-4bb0-8828-060a3fb50f08",
        "nonce_match": False,
        "validation_rule": "response.content == request.nonce (exact)",
        "spine_event_written": False,
        "memread": ("OK", 3, "read_ok"),
        "memread_ok": True,
    }
    base.update(kw)
    base["identity_key"] = br.identity_key(base)
    base["payload_hash"] = br.payload_hash(base)
    return base


def t_beat_change_is_not_user_facing():
    a = _snap(beat=43303)
    b = _snap(beat=43337)
    assert br.identity_key(a) == br.identity_key(b)
    d = br.classify(b, {"probe": a["probe"], "payload_hash": a["payload_hash"],
                        "user_facing_n": 2, "last_user_facing_at": 1},
                    now=10, stopped=False)
    assert d["send"] is False, d
    assert d["reason"] in ("dead_lettered", "coalesced_same_invalid", "already_notified"), d


def t_identical_invalid_probe_at_most_once_then_digest():
    s = _snap()
    d1 = br.classify(s, {}, now=1000.0, stopped=False, coalesce_s=50)
    assert d1["send"] is True and d1["kind"] == "incident", d1
    prev = {"probe": s["probe"], "payload_hash": s["payload_hash"],
            "user_facing_n": 1, "last_user_facing_at": 1000.0}
    d2 = br.classify(s, prev, now=1010.0, stopped=False, coalesce_s=50)
    assert d2["send"] is False, d2
    d3 = br.classify(s, prev, now=1000.0 + 51, stopped=False, coalesce_s=50)
    assert d3["send"] is True and d3["kind"] == "digest", d3
    prev2 = {**prev, "user_facing_n": 2, "last_user_facing_at": 1000.0 + 51}
    d4 = br.classify(s, prev2, now=1000.0 + 5000, stopped=False, coalesce_s=50)
    assert d4["send"] is False and d4["terminal"] == br.TERMINAL_DLQ, d4


def t_stop_file_suppresses_send():
    s = _snap()
    d = br.classify(s, {}, now=1, stopped=True)
    assert d["send"] is False
    assert d["reason"] == "safe_mode_stop"
    assert d["terminal"] == br.TERMINAL_BLOCKED


def t_telegram_events_count_is_not_closure():
    s = _snap(tg_events=11)
    assert s.get("memread_ok") is True
    d = br.classify(s, {"probe": INVALID if False else s["probe"],
                        "payload_hash": s["payload_hash"],
                        "user_facing_n": 2}, now=9e12, stopped=False)
    # even with memread OK and a count, closed_loop stays false
    assert br.identity_key(s)
    rec = br.tick(s=s, prev={"probe": s["probe"], "payload_hash": s["payload_hash"],
                             "user_facing_n": 2, "pushed_at": 1},
                  now=2, stopped=True, live=False,
                  state_file=Path(tempfile.mkdtemp()) / "st.json",
                  outbox_file=Path(tempfile.mkdtemp()) / "ob.jsonl",
                  telemetry_file=Path(tempfile.mkdtemp()) / "hb.jsonl")
    assert rec["state"]["closed_loop"] is False
    assert rec["sent"] is False


def t_duplicate_update_id_no_second_effect():
    td = Path(tempfile.mkdtemp())
    org = to.TelegramOrgan(td, allowlist={1}, live=False)
    u = {"update_id": 42, "message": {"text": "/x", "chat": {"id": 1}, "from": {"id": 1}}}
    a = org.ingest_update(u)
    b = org.ingest_update(u)
    assert a["status"] == "accepted"
    assert b["status"] == "duplicate" and b["effect"] == "none"


def t_invalid_has_terminal_after_bounded_retry():
    s = _snap()
    prev = {"probe": s["probe"], "payload_hash": s["payload_hash"],
            "user_facing_n": 2, "last_user_facing_at": 1}
    d = br.classify(s, prev, now=10**12, stopped=False, coalesce_s=1)
    assert d["terminal"] == br.TERMINAL_DLQ
    assert d["send"] is False


def t_existing_spam_state_does_not_resend():
    """Live tg-last-push.json already has this invalid probe → treat as notified."""
    td = Path(tempfile.mkdtemp())
    state = td / "st.json"
    state.write_text(json.dumps({
        "probe": "PROBE_RESPONSE_INVALID", "beat": 43303, "tg_events": 11,
        "pushed_at": 1787225198.6,
    }), encoding="utf-8")
    sends = []
    r = br.tick(s=_snap(beat=43337), prev=None, now=1787225198.6 + 300,
                stopped=False, live=True, send_fn=lambda t: sends.append(t) or True,
                state_file=state,
                outbox_file=td / "ob.jsonl",
                telemetry_file=td / "hb.jsonl")
    assert r["sent"] is False, r["decision"]
    assert sends == []
    assert r["decision"]["terminal"] in (br.TERMINAL_BLOCKED, br.TERMINAL_DLQ)


def t_valid_probe_does_not_claim_telegram_closure():
    s = _snap(probe="PROBE_PASS", nonce_match=True, spine_event_written=True)
    s["identity_key"] = br.identity_key(s)
    s["payload_hash"] = br.payload_hash(s)
    d = br.classify(s, {}, now=1, stopped=False)
    assert d["send"] is False
    assert d["terminal"] == br.TERMINAL_COMPLETED
    assert d["reason"] == "probe_completed_not_telegram_closure"


def t_tick_writes_internal_telemetry_without_send():
    td = Path(tempfile.mkdtemp())
    tel = td / "hb.jsonl"
    r = br.tick(s=_snap(beat=1), prev={}, now=5, stopped=True, live=False,
                state_file=td / "st.json", outbox_file=td / "ob.jsonl",
                telemetry_file=tel)
    assert tel.is_file()
    row = json.loads(tel.read_text(encoding="utf-8").splitlines()[0])
    assert row["beat"] == 1
    assert row["send"] is False
    assert r["sent"] is False


def t_redact_token_never_in_digest():
    leaked = to.redact("bot 123456789:AAThisIsAFakeTelegramBotTokenValueXXXX")
    assert "AAThisIsAFakeTelegramBotTokenValueXXXX" not in leaked
    assert "[REDACTED_BOT_TOKEN]" in leaked


def t_count_11_is_not_success():
    """telegram_events=11 across beats is evidence of an ORPHAN, not closure."""
    a = _snap(beat=43303, tg_events=11)
    b = _snap(beat=43337, tg_events=11)
    assert a["tg_events"] == b["tg_events"] == 11
    assert br.identity_key(a) == br.identity_key(b)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"{'PASS' if not failed else 'FAIL'} {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
