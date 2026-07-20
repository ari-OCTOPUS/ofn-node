#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1-05_test_ap_binding.py — توکنِ HMACِ callbackِ ap: (Stage-1 P3، contract کامل).

قرارداد (callback_token.py + center.py، پشتِ OCTOPUS_WIRE_CB_TOKEN، secret از OCTOPUS_CB_SECRET):
- خاموش → flag_on/ready=False؛ render بدونِ mint = کارتِ tokenless بایت‌به‌بایتِ قبلی.
- روشن + secret غایب → ready=False، mint=""، verify=False (fail-closed، دکمه‌ها inert).
- توکن به (jid | action | owner_id | action_hash=content_sha256(action,jid,{type,risk}) |
  expires) مقید است. دستکاریِ هر جزء → verify=False.
- handler (فلگ روشن): توکنِ نامعتبر/legacy-tokenless → رد؛ منقضی → رد؛ مقصدِ نامعتبر → رد؛
  single-use (approve دوباره = False).
- callback_data ≤ ۶۴ بایت.
$0 آفلاین؛ handlerها با aps/mission monkeypatchِ in-memory (state واقعی لمس نمی‌شود).
"""
import os
import sys
import tempfile
import threading
import time
import types
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
import center as center_mod     # noqa: E402


class _Env:
    def __init__(self, **kv):
        self.kv = kv

    def __enter__(self):
        self.prev = {k: os.environ.get(k) for k in self.kv}
        for k, v in self.kv.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        return self

    def __exit__(self, *a):
        for k, v in self.prev.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


_AH = "deadbeef" * 8   # action_hash نمونه (۶۴ hex)


# ── callback_token unit ──────────────────────────────────────────────────────
def t_a_flag_off_is_off():
    with _Env(OCTOPUS_WIRE_CB_TOKEN=None, OCTOPUS_CB_SECRET="s"):
        assert cbtok.flag_on() is False and cbtok.ready() is False


def t_b_flag_on_no_secret_failclosed():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET=None):
        assert cbtok.flag_on() is True and cbtok.ready() is False
        assert cbtok.mint("j", "ok", 1, _AH, "999") == ""
        assert cbtok.verify("anything", "j", "ok", 1, _AH, "999") is False


def t_c_mint_verify_roundtrip():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        assert cbtok.ready() is True
        tok = cbtok.mint("job1", "ok", 111, _AH, "1900000000")
        assert tok and len(tok) == cbtok._TOKEN_LEN
        assert cbtok.verify(tok, "job1", "ok", 111, _AH, "1900000000") is True


def t_d_tamper_every_field_fails():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        tok = cbtok.mint("job1", "ok", 111, _AH, "1900000000")
        assert cbtok.verify(tok, "JOB2", "ok", 111, _AH, "1900000000") is False   # jid
        assert cbtok.verify(tok, "job1", "no", 111, _AH, "1900000000") is False    # action
        assert cbtok.verify(tok, "job1", "ok", 999, _AH, "1900000000") is False    # owner
        assert cbtok.verify(tok, "job1", "ok", 111, "0" * 64, "1900000000") is False  # action_hash
        assert cbtok.verify(tok, "job1", "ok", 111, _AH, "1234567890") is False    # expires
        assert cbtok.verify(tok[:-1] + ("0" if tok[-1] != "0" else "1"),
                            "job1", "ok", 111, _AH, "1900000000") is False          # token
        assert cbtok.verify(None, "job1", "ok", 111, _AH, "1900000000") is False


def t_e_different_secret_rejected():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="alpha"):
        t1 = cbtok.mint("j", "ok", 5, _AH, "1900000000")
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="beta"):
        assert cbtok.mint("j", "ok", 5, _AH, "1900000000") != t1
        assert cbtok.verify(t1, "j", "ok", 5, _AH, "1900000000") is False


def t_f_callback_data_within_64_bytes():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        jid = "job_task_20260720T101010"  # idِ واقع‌نما
        tok = cbtok.mint(jid, "ok", 111, _AH, "1900000000")
        cd = f"ap:ok:{jid}:{tok}"
        assert len(cd.encode("utf-8")) <= 64, len(cd)


# ── render integration ───────────────────────────────────────────────────────
def t_g_render_tokenless_when_no_mint():
    pending = [{"id": "job1", "risk": "read", "title": "x", "created_at": "t"}]
    _txt, kb = render.render_approvals_queue(pending, {}, [])   # mint=None
    assert kb[0][0]["callback_data"] == "ap:ok:job1"
    assert kb[0][1]["callback_data"] == "ap:no:job1"
    assert kb[0][2]["callback_data"] == "ap:detail:job1"


def t_h_render_with_mint_embeds_verifiable_token():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        pending = [{"id": "job1", "risk": "read", "title": "x", "created_at": "t"}]
        mint = lambda jid, act: cbtok.mint(jid, act, 111, _AH, "1900000000")
        _txt, kb = render.render_approvals_queue(pending, {}, [], mint=mint)
        ok_cb = kb[0][0]["callback_data"]
        assert ok_cb.startswith("ap:ok:job1:") and ok_cb != "ap:ok:job1"
        tok = ok_cb.split(":", 3)[3]
        assert cbtok.verify(tok, "job1", "ok", 111, _AH, "1900000000") is True
        assert kb[0][2]["callback_data"] == "ap:detail:job1"   # detail بی‌توکن


# ── handler integration (in-memory aps؛ state واقعی لمس نمی‌شود) ───────────────
class _FakeClient:
    def __init__(self, owner=777):
        self.owner_id = owner
        self.owner_chat_id = owner
        self.center_chat_id = 999
    def wired(self):
        return True
    def is_owner(self, u):
        frm = ((u.get("message") or {}).get("from")
               or (u.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id
    def edit(self, *a, **k):
        return True
    def answer_callback(self, *a, **k):
        return True
    def send(self, *a, **k):
        return 1


class _FakeAps:
    """in-memory approval store: get/approve/reject + single-use."""
    def __init__(self, job):
        self.job = dict(job)
        self.decided = False
    def get(self, jid):
        return dict(self.job) if str(jid) == str(self.job["id"]) else None
    def approve(self, jid):
        if self.decided or str(jid) != str(self.job["id"]):
            return False
        self.decided = True
        return True
    def reject(self, jid):
        if self.decided or str(jid) != str(self.job["id"]):
            return False
        self.decided = True
        return True
    def record_legacy_verdict(self, *a, **k):
        return True
    def load_pending(self):
        return [] if self.decided else [dict(self.job)]
    def summary(self):
        return {}
    def sync_to_octopus_state(self):
        return {"recent": []}


def _center_with(job):
    fc = _FakeClient()
    fake_render = types.SimpleNamespace(
        render_approvals_queue=lambda *a, **k: ("AP", [[{"text": "x", "callback_data": "mn:menu"}]]),
        scrub=lambda t: t)
    c = center_mod.Center(client=fc, render_mod=fake_render)
    aps = _FakeAps(job)
    center_mod.aps_mod = aps
    center_mod.mission_mod = types.SimpleNamespace(get=lambda x: None,
                                                   set_owner_verdict=lambda *a, **k: None)
    return c, fc, aps


def _cbq(owner_id, data, chat=777):
    return {"id": "cb1", "from": {"id": owner_id},
            "message": {"message_id": 1, "chat": {"id": chat}}, "data": data}


def t_i_handler_valid_token_approves_then_single_use():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        job = {"id": "job1", "type": "task", "risk": "read",
               "expires_epoch": int(time.time()) + 3600}
        c, fc, aps = _center_with(job)
        ah = c._ap_action_hash("ok", "job1", job)
        tok = cbtok.mint("job1", "ok", fc.owner_chat_id, ah, str(job["expires_epoch"]))
        data = f"ap:ok:job1:{tok}"
        out = c._handle_approval_callback(_cbq(fc.owner_id, data), data)
        assert out.get("ok") is True and out.get("verdict") == "ok"
        # replay → single-use (approve دوباره False)
        out2 = c._handle_approval_callback(_cbq(fc.owner_id, data), data)
        assert out2.get("ok") is False


def t_j_handler_tampered_and_legacy_rejected():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        job = {"id": "job1", "type": "task", "risk": "read",
               "expires_epoch": int(time.time()) + 3600}
        c, fc, aps = _center_with(job)
        bad = "ap:ok:job1:0000000000000000ffff"
        out = c._handle_approval_callback(_cbq(fc.owner_id, bad), bad)
        assert out.get("rejected") == "bad-token" and aps.decided is False
        # legacy tokenless (فلگ روشن) → رد
        legacy = "ap:ok:job1"
        out2 = c._handle_approval_callback(_cbq(fc.owner_id, legacy), legacy)
        assert out2.get("rejected") == "bad-token" and aps.decided is False


def t_k_handler_expired_rejected():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        past = int(time.time()) - 10
        job = {"id": "job1", "type": "task", "risk": "read", "expires_epoch": past}
        c, fc, aps = _center_with(job)
        ah = c._ap_action_hash("ok", "job1", job)
        tok = cbtok.mint("job1", "ok", fc.owner_chat_id, ah, str(past))  # HMAC معتبر ولی منقضی
        data = f"ap:ok:job1:{tok}"
        out = c._handle_approval_callback(_cbq(fc.owner_id, data), data)
        assert out.get("rejected") == "expired" and aps.decided is False


def t_l_handler_wrong_destination_rejected():
    with _Env(OCTOPUS_WIRE_CB_TOKEN="1", OCTOPUS_CB_SECRET="s3cr3t"):
        job = {"id": "job1", "type": "task", "risk": "read",
               "expires_epoch": int(time.time()) + 3600}
        c, fc, aps = _center_with(job)
        ah = c._ap_action_hash("ok", "job1", job)
        tok = cbtok.mint("job1", "ok", fc.owner_chat_id, ah, str(job["expires_epoch"]))
        data = f"ap:ok:job1:{tok}"
        # chat = 12345 (نه owner=777 نه center=999) → رد
        out = c._handle_approval_callback(_cbq(fc.owner_id, data, chat=12345), data)
        assert out.get("rejected") == "bad-destination" and aps.decided is False


def t_m_flag_off_legacy_still_works():
    """فلگ خاموش → مسیرِ tokenless قدیمی بایت‌به‌بایت (ap:ok:jid بدونِ توکن approve می‌کند)."""
    with _Env(OCTOPUS_WIRE_CB_TOKEN=None, OCTOPUS_CB_SECRET=None):
        job = {"id": "job1", "type": "task", "risk": "read"}
        c, fc, aps = _center_with(job)
        data = "ap:ok:job1"
        out = c._handle_approval_callback(_cbq(fc.owner_id, data), data)
        assert out.get("ok") is True and out.get("verdict") == "ok"


def t_n_single_use_atomic_under_concurrency():
    """approval_store.approve زیرِ قفلِ single-writer: ۱۶ مصرف‌کنندهٔ همزمان روی یک jid →
    دقیقاً یکی True، بقیه False (read-modify-write اتمیک است، نه فقط هر write)."""
    import approval_store as aps
    with tempfile.TemporaryDirectory() as td:
        prev = aps._APPROVALS_JSON
        aps._APPROVALS_JSON = Path(td) / "approvals.json"     # redirect به temp (state واقعی امن)
        try:
            jid = aps.add_pending({"id": "jobRACE", "type": "task", "risk": "read"})
            results, start = [], threading.Event()

            def _worker():
                start.wait()
                results.append(aps.approve(jid))

            ts = [threading.Thread(target=_worker) for _ in range(16)]
            for t in ts:
                t.start()
            start.set()
            for t in ts:
                t.join()
            assert sum(1 for r in results if r) == 1, f"دقیقاً یک approve باید True شود: {results}"
            assert aps.summary().get("approved", 0) == 1
        finally:
            aps._APPROVALS_JSON = prev


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} S1-05_ap_binding: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
