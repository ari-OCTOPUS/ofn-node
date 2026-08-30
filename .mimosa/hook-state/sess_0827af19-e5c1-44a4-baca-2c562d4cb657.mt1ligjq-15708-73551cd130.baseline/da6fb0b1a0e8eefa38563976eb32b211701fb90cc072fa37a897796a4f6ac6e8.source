#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_restart_center_wiring — سیمِ /restart در center.py (Task #105، ۲۰۲۶-۰۸-۰۷).

ادعاهای باربر:
  ۱) /restart در _CENTER_SLASH است — وگرنه مامور (owner_console) پیام را
     می‌بلعد و هرگز به جدولِ خودِ مرکز نمی‌رسد (همان اشکالِ outer-bot-4 که
     /heart /brain /doctor برایش به این مجموعه اضافه شدند).
  ۲) /restart با فلگِ خاموش → پیامِ روشن، صفر job.
  ۳) /restart با scope نامعتبر → رد، صفر job.
  ۴) /restart موفق → کارتِ ap:ok/ap:no برمی‌گردد و job واقعی در approval_store
     با type=process_restart می‌نشیند.
  ۵) /restart وقتی از قبل یک درخواست در جریان است → رد (گاردِ هم‌زمانی).
  ۶) ap:ok e2e (از راهِ handle_update، نه صدازدنِ مستقیمِ متد) روی jobِ
     process_restart → execute_restart صدا زده می‌شود.
  ۷) ap:no e2e روی jobِ process_restart → cancel_request صدا زده می‌شود و
     is_restart_in_flight بلافاصله False می‌شود (وگرنه رد برای همیشه
     /restart بعدی را مسدود می‌کرد).

هیچ subprocessِ واقعی این‌جا اجرا نمی‌شود — restart_control.execute_restart
مانکی‌پچ می‌شود (مثلِ مانکی‌پچِ runner_mod در t_x_mission_test_flag_on_invokes_runner).
subprocessِ واقعیِ RESTART-ALL.ps1 خودش در test_restart_control.py پوشش دارد.
"""
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("restart-center-wiring")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib          # noqa: E402
import center           # noqa: E402
import approval_store as aps  # noqa: E402
import mission as mission_mod  # noqa: E402
import restart_control as rc  # noqa: E402

# ⚠️ approval_store.py/mission.py مسیرهاشان را **نسبت به فایلِ خودشان** حساب
# می‌کنند (`Path(__file__).resolve().parent.parent`), نه از رویِ envِ
# sandboxِ harness — یعنی پیش‌فرضشان مستقیم به F:\backup ِ زنده می‌رود. اگر
# این‌جا redirect نشوند، اولین ap:ok/ap:no ِ e2e سعی می‌کند approvals.json/
# رکوردِ legacy را روی state ِ واقعیِ ارگانیسم بنویسد؛ live_state_guard آن را
# می‌بلعد (LiveStateWriteError) و کالبک به‌جای اجراشدن، «خطا» می‌خورَد —
# دقیقاً همان الگویی که یک بار همین امشب، در یک اسکریپتِ دیباگِ بی‌احتیاط
# (بدونِ این redirect)، approvals.json ِ واقعی را با jobهای تستی کثیف کرد
# و باید دستی پاک می‌شد. test_tg_center.py دقیقاً همین redirect را دارد؛
# این‌جا هم‌الگو.
_E2E_SANDBOX = Path(tempfile.mkdtemp(prefix="octopus-restart-wiring-e2e-"))


def _redirect_octopus_paths():
    shutil.rmtree(_E2E_SANDBOX / "_octopus", ignore_errors=True)
    shutil.rmtree(_E2E_SANDBOX / "_ops" / "state" / "telegram" / "missions", ignore_errors=True)
    shutil.rmtree(_E2E_SANDBOX / "_ops" / "state" / "telegram" / "approvals", ignore_errors=True)
    aps._OCTOPUS_STATE = _E2E_SANDBOX / "_octopus" / "state"
    aps._APPROVALS_JSON = aps._OCTOPUS_STATE / "approvals.json"
    aps._AUDIT_PATH = _E2E_SANDBOX / "_octopus" / "logs" / "audit.log"
    aps._LEGACY_DIR = _E2E_SANDBOX / "_ops" / "state" / "telegram" / "approvals"
    aps._ROOT = _E2E_SANDBOX
    mission_mod._STATE_DIR = _E2E_SANDBOX / "_ops" / "state" / "telegram" / "missions"
    mission_mod._MISSIONS_JSON = mission_mod._STATE_DIR / "missions.json"
    mission_mod._AUDIT_JSONL = mission_mod._STATE_DIR / "mission-audit.jsonl"


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


class FakeClient:
    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.calls = []
        self._next_mid = 100

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False, stream=None):
        self.calls.append(("send", {"text": text, "keyboard": keyboard, "chat_id": chat_id}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def delete(self, message_id, chat_id=None):
        self.calls.append(("delete", {"message_id": message_id, "chat_id": chat_id}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _fake_render():
    legs = {}

    def collect_feeds():
        return {}

    def render_status(feeds):
        return "STATUS"

    def render_leg_digest(leg_key, leg):
        return ""

    def render_decision(item):
        return "", None

    return types.SimpleNamespace(LEGS=legs, collect_feeds=collect_feeds,
                                 render_status=render_status,
                                 render_leg_digest=render_leg_digest,
                                 render_decision=render_decision)


def _reset():
    rc._clear_request()
    _redirect_octopus_paths()


def _mk_center():
    return center.Center(client=FakeClient(), clock=Clock(), render_mod=_fake_render())


def _jid_from_card(card):
    """jid را از خودِ callback_data ِ کارت بخوان — مثلِ یک تپِ واقعی روی دکمه،
    نه فرضِ اینکه pending[0] همان job است (سندباکس‌های harness می‌توانند
    از قبل jobِ دیگری هم داشته باشند، مثلِ پیشنهادهای goal_action_bridge)."""
    _txt, kb = card
    return kb[0][0]["callback_data"].split(":", 2)[2]


# ════════════════════════════════════════════════════════════════════════════
# (۱) عضویتِ _CENTER_SLASH — رگرسیونِ همان کلاسِ اشکالِ outer-bot-4
# ════════════════════════════════════════════════════════════════════════════
def t_restart_is_in_center_slash():
    assert "/restart" in center._CENTER_SLASH, (
        "بدونِ این، مامور پیامِ /restart را می‌بلعد و هرگز به handlers نمی‌رسد")


def t_restart_has_handler_methods():
    c = _mk_center()
    for name in ("_restart_cmd", "_restart_card", "_trigger_restart_execution"):
        assert callable(getattr(c, name, None)), f"{name} وجود ندارد"


# ════════════════════════════════════════════════════════════════════════════
# (۲)+(۳) فلگ خاموش / scope نامعتبر
# ════════════════════════════════════════════════════════════════════════════
def t_restart_cmd_flag_off_message_zero_jobs():
    _reset()
    with _Flag(rc.FLAG, None):
        out = _mk_center()._restart_cmd("/restart")
    assert isinstance(out, str) and "خاموش" in out, out
    assert aps.load_pending() == []


def t_restart_cmd_invalid_scope_zero_jobs():
    _reset()
    with _Flag(rc.FLAG, "1"):
        out = _mk_center()._restart_cmd("/restart everything")
    assert isinstance(out, str) and "نامعتبر" in out, out
    assert aps.load_pending() == []


# ════════════════════════════════════════════════════════════════════════════
# (۴) /restart موفق → کارت + jobِ واقعی
# ════════════════════════════════════════════════════════════════════════════
def t_restart_cmd_success_returns_card_and_pending_job():
    _reset()
    with _Flag(rc.FLAG, "1"):
        out = _mk_center()._restart_cmd("/restart organism")
    assert isinstance(out, tuple) and len(out) == 2, out
    txt, kb = out
    assert "organism" in txt
    flat = [b["callback_data"] for row in kb for b in row]
    assert any(cd.startswith("ap:ok:") for cd in flat), flat
    assert any(cd.startswith("ap:no:") for cd in flat), flat
    pending = aps.load_pending()
    assert len(pending) == 1 and pending[0]["type"] == "process_restart", pending
    assert rc.is_restart_in_flight() is True


def t_restart_cmd_bare_defaults_to_scope_all():
    _reset()
    with _Flag(rc.FLAG, "1"):
        out = _mk_center()._restart_cmd("/restart")
    txt, _kb = out
    assert "all" in txt, txt
    rec = rc._load_request()
    assert rec["scope"] == "all", rec


# ════════════════════════════════════════════════════════════════════════════
# (۵) گاردِ هم‌زمانی از راهِ /restart
# ════════════════════════════════════════════════════════════════════════════
def t_restart_cmd_second_call_while_in_flight_is_rejected():
    _reset()
    with _Flag(rc.FLAG, "1"):
        out1 = _mk_center()._restart_cmd("/restart organism")
        assert isinstance(out1, tuple)
        out2 = _mk_center()._restart_cmd("/restart center")
    assert isinstance(out2, str) and "در جریان" in out2, out2
    assert len(aps.load_pending()) == 1, "دومی نباید jobِ دوم بسازد"


# ════════════════════════════════════════════════════════════════════════════
# (۶) ap:ok e2e → execute_restart صدا زده می‌شود
# ════════════════════════════════════════════════════════════════════════════
def t_ap_ok_on_process_restart_triggers_execute_restart_e2e():
    _reset()
    called = {}

    def fake_execute(scope=None):
        called["scope"] = scope
        return {"ok": True, "pid": 123, "log_path": "x.log"}

    orig = rc.execute_restart
    rc.execute_restart = fake_execute
    try:
        with _Flag(rc.FLAG, "1"):
            fc = FakeClient(owner_id=777)
            c = center.Center(client=fc, clock=Clock(), render_mod=_fake_render())
            card = c._restart_cmd("/restart organism")
            assert isinstance(card, tuple)
        jid = _jid_from_card(card)
        u = {"update_id": 1, "callback_query": {
            "id": "c1", "from": {"id": 777}, "data": f"ap:ok:{jid}",
            "message": {"message_id": 1, "chat": {"id": 777, "type": "private"}}}}
        res = c.handle_update(u)
        assert res and res["kind"] == "approval" and res["ok"] is True, res
        assert "scope" in called, "execute_restart هرگز صدا زده نشد"
    finally:
        rc.execute_restart = orig


def t_ap_ok_execute_failure_notifies_owner_but_approve_still_stands():
    """اجرای شکست‌خورده (مثلاً اسکریپت گم) نباید approve را نامعتبر کند —
    فقط باید به مالک خبر بدهد."""
    _reset()

    def fake_execute_fail(scope=None):
        return {"ok": False, "reason": "restart_all_script_missing"}

    orig = rc.execute_restart
    rc.execute_restart = fake_execute_fail
    try:
        with _Flag(rc.FLAG, "1"):
            fc = FakeClient(owner_id=777)
            c = center.Center(client=fc, clock=Clock(), render_mod=_fake_render())
            card = c._restart_cmd("/restart organism")
        jid = _jid_from_card(card)
        u = {"update_id": 1, "callback_query": {
            "id": "c1", "from": {"id": 777}, "data": f"ap:ok:{jid}",
            "message": {"message_id": 1, "chat": {"id": 777, "type": "private"}}}}
        res = c.handle_update(u)
        assert res["ok"] is True, "approve خودش باید موفق بماند"
        sent = fc.named("send")
        assert any("restart_all_script_missing" in s["text"] for s in sent), sent
    finally:
        rc.execute_restart = orig


# ════════════════════════════════════════════════════════════════════════════
# (۷) ap:no e2e → cancel_request صدا زده می‌شود
# ════════════════════════════════════════════════════════════════════════════
def t_ap_no_on_process_restart_cancels_and_unblocks_next_request_e2e():
    _reset()
    with _Flag(rc.FLAG, "1"):
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=_fake_render())
        card = c._restart_cmd("/restart organism")
        assert rc.is_restart_in_flight() is True
        jid = _jid_from_card(card)
        u = {"update_id": 1, "callback_query": {
            "id": "c1", "from": {"id": 777}, "data": f"ap:no:{jid}",
            "message": {"message_id": 1, "chat": {"id": 777, "type": "private"}}}}
        res = c.handle_update(u)
        assert res and res["action"] == "no" and res["ok"] is True, res
        assert rc.is_restart_in_flight() is False, (
            "cancel_request صدا زده نشد -- /restart بعدی برای همیشه رد می‌شود")
        out2 = c._restart_cmd("/restart center")
        assert isinstance(out2, tuple), out2


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_restart_center_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
