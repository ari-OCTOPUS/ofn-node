#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1-05_test_ap_binding.py — توکنِ HMACِ callbackِ ap: (Stage-1 P3).

قرارداد callback_token.py (پشتِ فلگ OCTOPUS_WIRE_CB_TOKEN، secret از OCTOPUS_CB_SECRET):
- فلگ خاموش → flag_on/ready = False؛ render بدونِ mint = کارتِ tokenless بایت‌به‌بایتِ قبلی.
- فلگ روشن + secret غایب → ready=False، mint=""، verify=False (fail-closed، دکمه‌ها inert).
- فلگ روشن + secret → mint توکن می‌سازد؛ verify فقط برای همان (jid,action,owner,stamp).
- دستکاریِ jid/action/owner/stamp/token → verify=False.
- render با mint → ap:ok:<id>:<tok>؛ بدونِ mint → ap:ok:<id> (byte-identical).
$0 آفلاین، بدونِ شبکه/تلگرام.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness      # noqa: E402
harness.setup("s1-05-ap-binding")

import callback_token as cbtok  # noqa: E402
import render                   # noqa: E402


class _Env:
    """ست/بازگردانیِ چند env var به‌صورتِ ایزوله."""
    def __init__(self, **kv):
        self.kv = kv

    def __enter__(self):
        self.prev = {k: os.environ.get(k) for k in self.kv}
        for k, v in self.kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, v in self.prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_a_flag_off_is_off():
    with _Env(OCTOPUS_WIRE_CB_TOKEN=None, OCTOPUS_CB_SECRET="s3cr3t"):
        assert cbtok.flag_on() is False and cbtok.ready() is False


def t_b_flag_on_no_secret_failclosed():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET=None):
        assert cbtok.flag_on() is True
        assert cbtok.ready() is False
        assert cbtok.mint("job1", "ok", 111, "2026-07-20T00:00:00") == ""
        # هیچ توکنی معتبر نیست (fail-closed)
        assert cbtok.verify("anything", "job1", "ok", 111, "2026-07-20T00:00:00") is False
        assert cbtok.verify("", "job1", "ok", 111, "2026-07-20T00:00:00") is False


def t_c_mint_verify_roundtrip():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        assert cbtok.ready() is True
        tok = cbtok.mint("job1", "ok", 111, "2026-07-20T10:00:00")
        assert tok and isinstance(tok, str) and len(tok) == cbtok._TOKEN_LEN
        assert cbtok.verify(tok, "job1", "ok", 111, "2026-07-20T10:00:00") is True


def t_d_tamper_any_field_fails():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        tok = cbtok.mint("job1", "ok", 111, "2026-07-20T10:00:00")
        assert cbtok.verify(tok, "job2", "ok", 111, "2026-07-20T10:00:00") is False   # jid
        assert cbtok.verify(tok, "job1", "no", 111, "2026-07-20T10:00:00") is False    # action
        assert cbtok.verify(tok, "job1", "ok", 999, "2026-07-20T10:00:00") is False    # owner
        assert cbtok.verify(tok, "job1", "ok", 111, "2026-07-20T11:11:11") is False    # stamp
        assert cbtok.verify(tok[:-1] + ("0" if tok[-1] != "0" else "1"),
                            "job1", "ok", 111, "2026-07-20T10:00:00") is False          # token
        assert cbtok.verify(None, "job1", "ok", 111, "2026-07-20T10:00:00") is False


def t_e_different_secret_different_token():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="alpha"):
        t1 = cbtok.mint("j", "ok", 5, "stamp")
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="beta"):
        t2 = cbtok.mint("j", "ok", 5, "stamp")
        assert t1 != t2
        assert cbtok.verify(t1, "j", "ok", 5, "stamp") is False  # توکنِ secretِ دیگر رد


def t_f_render_tokenless_byte_identical_when_no_mint():
    pending = [{"id": "job1", "risk": "read", "title": "x", "created_at": "t"}]
    _txt, kb = render.render_approvals_queue(pending, {}, [])   # mint پیش‌فرض None
    row = kb[0]
    assert row[0]["callback_data"] == "ap:ok:job1"
    assert row[1]["callback_data"] == "ap:no:job1"
    assert row[2]["callback_data"] == "ap:detail:job1"


def t_g_render_with_mint_embeds_token():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        pending = [{"id": "job1", "risk": "read", "title": "x", "created_at": "t"}]
        mint = lambda jid, act: cbtok.mint(jid, act, 111, "t")
        _txt, kb = render.render_approvals_queue(pending, {}, [], mint=mint)
        ok_cb = kb[0][0]["callback_data"]
        assert ok_cb.startswith("ap:ok:job1:") and ok_cb != "ap:ok:job1"
        tok = ok_cb.split(":", 3)[3]
        assert cbtok.verify(tok, "job1", "ok", 111, "t") is True
        # detail بدونِ توکن (خواندنی)
        assert kb[0][2]["callback_data"] == "ap:detail:job1"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} S1-05_ap_binding: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
