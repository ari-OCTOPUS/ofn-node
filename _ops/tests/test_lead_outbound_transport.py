#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_outbound_transport — آداپترِ ایمیلِ واقعیِ Lane G (رأی ۱۷).

اثبات می‌کند:
  · بدونِ ۵ envِ SMTP → NOT_ARMED صادقانه؛ صفر communication.sent؛ شمارنده دست‌نخورده.
  · ارسالِ موفق (SMTP ساختگیِ تزریقی) → communication.sent در funnel.db + شمارنده++.
  · شکستِ SMTP → communication.failed + رسیدِ شکست + شمارنده دست‌نخورده.
  · نشانِ STOP/opt-out → SUPPRESSED، صفر تلاش، تغذیهٔ دفاعیِ consent_store.suppression.
  · secret (پسورد/کاربر) و گیرندهٔ کامل هرگز در رسیدها نمی‌نشیند (ماسکِ local-part).
  (قفلِ test_effector_gate_bridge محترم: sent فقط از نتیجهٔ واقعیِ transport.)
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-outbound-transport")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                          # noqa: E402
import outbound_worker as ow           # noqa: E402
import lead_outbound_transport as lot  # noqa: E402
import funnel_store as fs              # noqa: E402

_SMTP_ENV = {"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
             "OCTOPUS_SMTP_USER": "smtp-test-user",
             "OCTOPUS_SMTP_PASS": "hunter2-super-secret",
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}

NOW_S = 1_785_400_000.0


def _set_creds(on: bool):
    if on:
        os.environ.update(_SMTP_ENV)
    else:
        for k in _SMTP_ENV:
            os.environ.pop(k, None)


def _fresh_counter():
    try:
        ow._counter_path().unlink()
    except OSError:
        pass


def _events_text() -> str:
    p = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    try:
        return p.read_text("utf-8")
    except OSError:
        return ""


def _funnel_types(lead_id: str) -> list:
    store = fs.FunnelStore()
    try:
        return [r[1] for r in store.events_for_lead(lead_id)]
    finally:
        store.close()


def _cand(lead_id: str, email="customer.one@example.com", **extra) -> dict:
    c = {"lead_id": lead_id, "contact": {"email": email},
         "source": {"channel": "telegram_manual"}}
    c.update(extra)
    return c


class SpyImpl:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, host, port, user, pw, from_addr, to_addr, message):
        self.calls.append({"host": host, "to": to_addr, "message": message})
        if self.fail:
            raise ConnectionError("boom")


def t_a_no_creds_is_honest_not_armed():
    _set_creds(False)
    _fresh_counter()
    r = lot.send(_cand("L-nocreds"), "hello", now=NOW_S)
    assert r == {"sent": False, "status": "NOT_ARMED", "detail": "smtp-creds-missing"}, r
    assert "communication.sent" not in _funnel_types("L-nocreds"), \
        "NOT_ARMED نباید communication.sent بزند (settle ≠ sent)"
    assert ow.sends_today(now=NOW_S) == 0, "NOT_ARMED نباید بشمارد"


def t_b_confirmed_send_writes_receipt_and_counts():
    _set_creds(True)
    _fresh_counter()
    spy = SpyImpl()
    r = lot.send(_cand("L-ok"), {"subject": "Quote", "body": "قیمتِ کار"},
                 now=NOW_S, send_impl=spy)
    assert r["sent"] is True and r["status"] == "SENT", r
    assert len(spy.calls) == 1 and spy.calls[0]["to"] == "customer.one@example.com"
    assert "communication.sent" in _funnel_types("L-ok"), "رسیدِ funnel نیست"
    assert ow.sends_today(now=NOW_S) == 1, "ارسالِ تأییدشده باید بشمارد"
    import email as _em
    _msg = _em.message_from_string(spy.calls[0]["message"])
    _body = _msg.get_payload(decode=True).decode("utf-8")
    assert "Reply STOP" in _body, "پیامِ ایمیل بدونِ راهِ opt-out"


def t_c_failed_send_writes_failed_and_never_counts():
    _set_creds(True)
    _fresh_counter()
    spy = SpyImpl(fail=True)
    r = lot.send(_cand("L-fail"), "hello", now=NOW_S, send_impl=spy)
    assert r["sent"] is False and r["status"] == "FAILED", r
    types = _funnel_types("L-fail")
    assert "communication.failed" in types and "communication.sent" not in types, types
    assert ow.sends_today(now=NOW_S) == 0, "شکست نباید بشمارد"
    assert '"communication.failed"' in _events_text(), "رسیدِ شکست در events.jsonl نیست"


def t_d_stop_marker_is_suppressed_and_feeds_consent_store():
    _set_creds(True)
    spy = SpyImpl()
    r = lot.send(_cand("L-stop", email="stopme@example.com", opt_out=True),
                 "hello", now=NOW_S, send_impl=spy)
    assert r["sent"] is False and r["status"] == "SUPPRESSED", r
    assert not spy.calls, "کاندیدِ STOP نباید هیچ تلاشی بگیرد"
    import consent_store as cs
    store = cs.ConsentStore()
    try:
        reason = store.suppression_active("stopme@example.com")
    finally:
        store.close()
    assert reason, "suppression باید به consent_store تغذیه شده باشد"
    # و بارِ دوم هم suppressed می‌مانَد (این‌بار از خودِ جدولِ suppression)
    r2 = lot.send(_cand("L-stop2", email="stopme@example.com"),
                  "hello", now=NOW_S, send_impl=spy)
    assert r2["status"] == "SUPPRESSED" and not spy.calls, r2


def t_e_missing_recipient_is_honest():
    _set_creds(True)
    spy = SpyImpl()
    r = lot.send({"lead_id": "L-noaddr", "contact": {}}, "hello",
                 now=NOW_S, send_impl=spy)
    assert r["status"] == "NO_RECIPIENT" and not spy.calls, r


def t_f_secrets_and_full_recipient_never_reach_receipts():
    text = _events_text()
    assert "hunter2-super-secret" not in text, "پسورد در رسید نشسته!"
    assert "smtp-test-user" not in text, "کاربرِ SMTP در رسید نشسته!"
    assert "customer.one@example.com" not in text, "گیرندهٔ کامل در رسید نشسته!"
    assert "cu***@example.com" in text, "ماسکِ local-part در رسید نیست"
    assert lot.mask_recipient("ab.cd@x.com") == "ab***@x.com"
    assert lot.mask_recipient("") == "***"


def t_g_transport_never_raises():
    _set_creds(True)
    r = lot.send(None, None, now=NOW_S, send_impl=SpyImpl())
    assert isinstance(r, dict) and r.get("sent") is False, r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_outbound_transport: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
