#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_telegram_pep_shadow — DA-4-P1: تست‌های منفیِ PEP سایهٔ مرز ارسال.

قرارداد: deny-by-default · تک‌مصرف (replay رد) · انقضا · hash-mismatch ·
kill توزیع‌شده (ابطال محلی) · ناظر fail-soft (هرگز مرز را نمی‌کشد) ·
هوک‌های زنده نصب‌اند (سطح source) · پاکیِ import (هیچ شبکه‌ای در ماژول).
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("telegram-pep-shadow")
sys.path.insert(0, str(ENV["ops"] / "budget"))

import telegram_pep_shadow as pep  # noqa: E402


def _lease(st, action="sendMessage", params=None, ttl=30.0):
    params = params or {"chat_id": 1, "text": "سلام"}
    L = pep.Lease(action, params, ttl_s=ttl)
    st.leases[L.lease_id] = L
    return L


def t_deny_by_default_without_lease():
    st = pep.PepState()
    r = st.evaluate("sendMessage", {"chat_id": 1, "text": "x"}, None)
    assert r["verdict"] == "deny" and "no-lease" in r["reason"], r


def t_valid_lease_allows_once_then_replay_denied():
    st = pep.PepState()
    p = {"chat_id": 1, "text": "x"}
    L = _lease(st, params=p)
    r1 = st.evaluate("sendMessage", p, L)
    r2 = st.evaluate("sendMessage", p, L)
    assert r1["verdict"] == "allow", r1
    assert r2["verdict"] == "deny" and "replay" in r2["reason"], r2


def t_expired_lease_denied():
    st = pep.PepState()
    p = {"chat_id": 1, "text": "x"}
    L = _lease(st, params=p, ttl=-1.0)
    r = st.evaluate("sendMessage", p, L)
    assert r["verdict"] == "deny" and "expired" in r["reason"], r


def t_hash_mismatch_denied():
    st = pep.PepState()
    L = _lease(st, params={"chat_id": 1, "text": "اصل"})
    r = st.evaluate("sendMessage", {"chat_id": 1, "text": "دستکاری‌شده"}, L)
    assert r["verdict"] == "deny" and "hash" in r["reason"], r


def t_distributed_kill_denied_locally():
    st = pep.PepState()
    p = {"chat_id": 1, "text": "x"}
    L = _lease(st, params=p)
    st.revoked.add(L.lease_id)          # ابطالِ محلی — بدون پرسش از مرکز
    r = st.evaluate("sendMessage", p, L)
    assert r["verdict"] == "deny" and "revoked" in r["reason"], r


def t_observer_failsoft_and_logs():
    with tempfile.TemporaryDirectory() as td:
        pep.STATE = Path(td)
        r = pep.observe("unit-test", "sendMessage", {"chat_id": 1, "text": "x"})
        assert r["verdict"] == "deny", r                # بدون lease = رد
        rows = [json.loads(l) for l in
                (Path(td) / "telegram-pep-shadow.jsonl").read_text(encoding="utf-8").splitlines()]
        assert rows and rows[0]["mode"] == "shadow" and rows[0]["sender"] == "unit-test"
        # fail-soft: حتی با STATE خراب، observe مرگ نمی‌گیرد
        pep.STATE = Path(td) / "unwritable" / "deep" / "x.jsonl"
        r2 = pep.observe("unit", "send", {})
        assert "verdict" in r2


def t_live_hooks_installed():
    ops = Path(r"F:\backup\_ops")
    tg = (ops / "telegram_center" / "tg_api.py").read_text(encoding="utf-8")
    ap = (ops / "budget" / "approval_channel.py").read_text(encoding="utf-8")
    assert "telegram_pep_shadow" in tg and "_call_post" in tg
    assert "telegram_pep_shadow" in ap and "_url_json_post" in ap


def t_module_has_no_network():
    src = Path(pep.__file__).read_text(encoding="utf-8")
    for b in ("import socket", "import urllib", "import requests",
              "import http.client", "import subprocess"):
        assert b not in src, b


CHECKS = [
    ("بدون lease ⇒ deny-by-default", t_deny_by_default_without_lease),
    ("lease معتبر یک‌بار؛ replay رد", t_valid_lease_allows_once_then_replay_denied),
    ("lease منقضی رد", t_expired_lease_denied),
    ("دستکاری params (hash) رد", t_hash_mismatch_denied),
    ("kill توزیع‌شده = ردِ محلی", t_distributed_kill_denied_locally),
    ("ناظر fail-soft + لاگ سایه", t_observer_failsoft_and_logs),
    ("هوک‌های زنده نصب‌اند", t_live_hooks_installed),
    ("ماژول PEP بدون شبکه", t_module_has_no_network),
]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    sys.exit(1 if failed else 0)
