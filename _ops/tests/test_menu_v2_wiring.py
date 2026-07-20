#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_menu_v2_wiring.py — reachabilityِ Menu v2 از entry-pointِ واقعیِ center.handle_update.

OCTOPUS_WIRE_MENU_V2 تا امروز ORPHAN بود (صفر callerِ production؛ ممیزیِ Sol). این تست
از درِ واقعی (handle_update) اثبات می‌کند:
  (الف) flag خاموش · /panel = command ناشناسِ امروز (None، صفر send) — parity بایت‌به‌بایت.
  (ب)  flag خاموش · m:home = «نادیده» (fallbackِ امروز) — parity.
  (ج)  flag روشن · /panel → menu_integration.render_menu → send با متنِ پنل.
  (د)  flag روشن · m:home → menu_integration.dispatch → edit درجای همان پیام.
  (ه)  ساختاری: سیم‌کشی پشتِ _menu2().enabled()؛ handlerِ m: صفر settle/effector.
صفر شبکه/تلگرام؛ FakeClient؛ owner=777.
"""
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("menu-v2-wiring")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import center  # noqa: E402

CENTER_SRC = (_OPS / "telegram_center" / "center.py").read_text("utf-8")


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
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0,
                      render_mod=types.SimpleNamespace(collect_feeds=lambda: {}, scrub=lambda t: t))
    return c, fc


def _msg(text):
    return {"message": {"from": {"id": 777}, "chat": {"id": 777}, "text": text, "message_id": 5}}


def _cb(data):
    return {"callback_query": {"id": "cb1", "from": {"id": 777},
                               "message": {"message_id": 100, "chat": {"id": 777}}, "data": data}}


def t_a_flag_off_panel_parity():
    os.environ.pop("OCTOPUS_WIRE_MENU_V2", None)
    c, fc = _center()
    assert c.handle_update(_msg("/panel")) is None, "flag خاموش: /panel = command ناشناس (None)"
    assert not fc.named("send"), "flag خاموش: /panel نباید چیزی بفرستد"


def t_b_flag_off_m_verb_parity():
    os.environ.pop("OCTOPUS_WIRE_MENU_V2", None)
    c, fc = _center()
    c.handle_update(_cb("m:home"))
    assert not fc.named("edit"), "flag خاموش: m: نباید edit کند"
    ans = fc.named("answer")
    assert ans and ans[0]["text"] == "نادیده", ans   # fallbackِ امروز، بایت‌به‌بایت


def t_c_flag_on_panel_reachable():
    os.environ["OCTOPUS_WIRE_MENU_V2"] = "1"
    try:
        c, fc = _center()
        r = c.handle_update(_msg("/panel"))
        sends = fc.named("send")
        assert sends, "flag روشن: /panel باید پنلِ menu2 را بفرستد"
        assert "پنل" in sends[0]["text"], sends[0]["text"]
        assert r and r.get("sent"), r
    finally:
        os.environ.pop("OCTOPUS_WIRE_MENU_V2", None)


def t_d_flag_on_m_verb_reachable():
    os.environ["OCTOPUS_WIRE_MENU_V2"] = "1"
    try:
        c, fc = _center()
        r = c.handle_update(_cb("m:home"))
        edits = fc.named("edit")
        assert edits and "پنل" in edits[0]["text"], edits
        assert r and r.get("kind") == "menu2", r
    finally:
        os.environ.pop("OCTOPUS_WIRE_MENU_V2", None)


def t_e_structural_and_no_effector():
    import ast
    assert '_menu2()' in CENTER_SRC and 'handlers["/panel"]' in CENTER_SRC
    assert 'verb == "m"' in CENTER_SRC and '_handle_menu2_callback' in CENTER_SRC
    tree = ast.parse(CENTER_SRC)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_handle_menu2_callback"), None)
    assert fn is not None, "handlerِ m: باید وجود داشته باشد"
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"settle", "EffectorGate", "send_message", "mark_paid", "sendMessage"}, \
                f"handler نباید .{node.attr} داشته باشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_menu_v2_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
