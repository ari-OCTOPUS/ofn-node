#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_menu_v2_honesty.py — گپ‌های Menu v2 که test_menu_v2_wiring نپوشانده بود (Wave1-A).

مکملِ test_menu_v2_wiring (Sol-T1؛ آن سوئیت parity/reachability مالک را اثبات کرده):
  (الف) غیرمالک، flag روشن: /panel → سکوتِ کامل (None، صفر تماسِ client).
  (ب)  غیرمالک، flag روشن: callbackِ m: → سکوتِ کامل (نه answer، نه edit).
  (ج)  غیرمالک، flag خاموش: همان سکوت — parity در هر دو حالتِ flag.
  (د)  هیچ صفحه‌ای از پنل دستورِ مرده تبلیغ نمی‌کند (/sync /review /books /finance) —
       brief §6: «feature ِ ناموجود باید ناموجود علامت بخورد»؛ شمارش‌ها اما دیده می‌شوند.
  (ه)  صفحهٔ ⑥ توقف به مسیرِ واقعیِ همین سطح دکمه دارد (mn:sy) نه دستورِ deadِ /panic.
  (و)  هر commandِ منوی ثبت‌شده (center.COMMANDS) از درِ واقعی handle می‌شود (سکوتِ کاذب ندارد).
صفر شبکه/تلگرام (FakeClient)؛ envهای owner_views/owner_debug قبل از import به temp پین می‌شوند.
"""
import json
import os
import sys
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("menu-v2-honesty")
# ایزوله‌سازیِ read-model ها قبل از import (owner_views/owner_debug env را در import می‌خوانند)
_TMP = Path(ENV["OPS_DIR"]) / "honesty"
_OCT = _TMP / "octopus-state"
_OPS_STATE = _TMP / "ops-state"
for _d in (_OCT, _OPS_STATE):
    _d.mkdir(parents=True, exist_ok=True)
os.environ["OCTOPUS_STATE_ROOT"] = str(_OCT)
os.environ["OPS_STATE_ROOT"] = str(_OPS_STATE)
os.environ["OCTOPUS_VAULT_ROOT"] = str(_TMP)

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import center  # noqa: E402
import menu_integration as m2  # noqa: E402

_FLAG = "OCTOPUS_WIRE_MENU_V2"
_DEAD_CMDS = ("/sync", "/review", "/books", "/finance")


class FakeClient:
    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.calls = []
        self._mid = 100

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "keyboard": keyboard}))
        self._mid += 1
        return self._mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text, "keyboard": keyboard}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id


def _center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0,
                      render_mod=types.SimpleNamespace(collect_feeds=lambda: {},
                                                       render_status=lambda f: "st",
                                                       scrub=lambda t: t))
    return c, fc


def _msg(text, uid=777):
    return {"message": {"from": {"id": uid}, "chat": {"id": uid}, "text": text, "message_id": 5}}


def _cb(data, uid=777):
    return {"callback_query": {"id": "cb1", "from": {"id": uid},
                               "message": {"message_id": 100, "chat": {"id": uid}}, "data": data}}


def _flat(text, kb) -> str:
    """متن + برچسبِ همهٔ دکمه‌ها (برای چکِ تبلیغِ dead command)."""
    parts = [str(text or "")]
    for row in (kb or []):
        for b in row:
            parts.append(str(b.get("text", "")))
    return "\n".join(parts)


def t_a_nonowner_panel_silent_flag_on():
    os.environ[_FLAG] = "1"
    try:
        c, fc = _center()
        assert c.handle_update(_msg("/panel", uid=666)) is None, "غیرمالک باید None بگیرد"
        assert fc.calls == [], f"غیرمالک = سکوتِ کامل، صفر تماس: {fc.calls}"
    finally:
        os.environ.pop(_FLAG, None)


def t_b_nonowner_m_callback_silent_flag_on():
    os.environ[_FLAG] = "1"
    try:
        c, fc = _center()
        assert c.handle_update(_cb("m:home", uid=666)) is None
        assert fc.calls == [], f"غیرمالک نباید حتی answer بگیرد: {fc.calls}"
    finally:
        os.environ.pop(_FLAG, None)


def t_c_nonowner_silent_flag_off_parity():
    os.environ.pop(_FLAG, None)
    c, fc = _center()
    assert c.handle_update(_msg("/panel", uid=666)) is None
    assert c.handle_update(_cb("m:home", uid=666)) is None
    assert fc.calls == [], fc.calls


def t_d_no_dead_command_ads():
    # stateِ مصنوعیِ accounting با صف‌های pending — تا خطِ detail واقعاً render شود
    st = _OPS_STATE / "ORGANISM-STATE.accounting"
    st.write_text(json.dumps({"synced": True, "pending_review": 3, "pending_books": 2}), "utf-8")
    os.utime(st, (time.time(), time.time()))   # تازه → سبز → detail نمایش داده می‌شود
    views = ["m:home", "m:status", "m:mytasks", "m:legs", "m:report", "m:mission", "m:stop"]
    legs_txt = ""
    for v in views:
        txt, kb = m2.dispatch(v)
        blob = _flat(txt, kb)
        for dead in _DEAD_CMDS:
            assert dead not in blob, f"صفحهٔ {v} دستورِ مرده تبلیغ می‌کند: {dead}\n{blob}"
        if v == "m:legs":
            legs_txt = blob
    # شمارش‌ها گم نشده‌اند — فقط تبلیغِ دستورِ مرده حذف شده
    assert "3" in legs_txt and "بازبینی" in legs_txt, f"شمارشِ صفِ review گم شد:\n{legs_txt}"
    assert "2" in legs_txt and "دفتر" in legs_txt, f"شمارشِ صفِ books گم شد:\n{legs_txt}"


def t_e_stop_view_routes_to_real_power_page():
    txt, kb = m2.dispatch("m:stop")
    cbs = [b.get("callback_data") for row in kb for b in row]
    assert "mn:sy" in cbs, f"صفحهٔ توقف باید به صفحهٔ پاورِ واقعیِ center دکمه بدهد: {cbs}"
    assert "نه این بات" in txt, "متن باید صادقانه بگوید /panic در این بات کار نمی‌کند"


def t_f_advertised_commands_are_handled():
    """هر command که در منوی BotFather ثبت می‌شود (center.COMMANDS) باید از درِ واقعی
    handle شود (dict، نه Noneِ «command ناشناس»). صداقتِ منو = صفر دستورِ ثبت‌شدهٔ مرده."""
    for cmd, _desc in center.COMMANDS:
        c, fc = _center()
        r = c.handle_update(_msg(f"/{cmd}"))
        assert isinstance(r, dict), f"/{cmd} ثبت شده ولی handle نمی‌شود (None)"
        assert r.get("sent"), f"/{cmd} باید پاسخ بفرستد: {r}"


def t_g_zero_network_structural():
    """پنل و viewهایش هرگز import شبکه ندارند (صفر تلگرام/HTTP در این سطح)."""
    import ast
    for name in ("menu_integration.py", "owner_menu.py", "owner_views.py", "owner_debug.py"):
        src = (_OPS / "telegram_center" / name).read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [(node.module or "").split(".")[0]]
            for m in mods:
                assert m not in ("urllib", "http", "socket", "requests"), f"{name} → {m}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_menu_v2_honesty: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
