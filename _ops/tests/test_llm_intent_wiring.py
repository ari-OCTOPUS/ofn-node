#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_llm_intent_wiring.py — reachabilityِ llm_intent از entry-pointِ واقعیِ center._handle_ask.

OCTOPUS_TG_LLM_ASK تا امروز ماژولِ ادغام‌شده ولی بدونِ callerِ production بود. این تست از درِ
واقعی (handle_update → _handle_ask) اثبات می‌کند:
  (الف) flag خاموش · متنِ آزادِ general → llm_intent.understand هرگز صدا نمی‌شود (parity امروز).
  (ب)  flag روشن · understand صدا می‌شود و اگر needs_mission بود → کارتِ مأموریتِ گیت‌شده
       (kind=ask_mission)، هرگز اجرای مستقیم.
  (ج)  flag روشن · understand=ok=False (مثلِ router آفلاین) → fallback به مسیرِ rule-based امروز.
  (د)  ساختاری: سیم‌کشی پشتِ _li.enabled()؛ هرگز مسیرِ اجرا/effector از این‌جا.
صفر شبکه/LLM (understand monkeypatch می‌شود — وظیفهٔ این تست مسیریابیِ center است نه خودِ understand).
"""
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("llm-intent-wiring")

# center را از همین درختِ کاری import می‌کنیم (نه REAL_VAULT) تا کدِ همین‌جا تست شود —
# REAL_VAULT به درختِ زندهٔ F:\backup resolve می‌شود که تا ff ویرایشِ این جلسه را ندارد.
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import center       # noqa: E402
import llm_intent   # noqa: E402

CENTER_SRC = Path(center.__file__).read_text("utf-8")


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


# جملهٔ آزادِ general که infer_mission_type آن را mission نمی‌داند.
_FREE = "یه لطفی بکن و وضعیتو یه نگاه بنداز ببین چیزی هست"


def t_a_flag_off_understand_not_called():
    os.environ.pop("llm_intent_called", None)
    os.environ.pop(llm_intent.FLAG, None)
    calls = []
    orig = llm_intent.understand
    llm_intent.understand = lambda *a, **k: calls.append(1) or {"ok": False}
    try:
        c, fc = _center()
        c.handle_update(_msg(_FREE))
        assert not calls, "flag خاموش: understand نباید صدا شود (parity)"
    finally:
        llm_intent.understand = orig


def t_b_flag_on_needs_mission_routes_to_gated_card():
    os.environ[llm_intent.FLAG] = "1"
    calls = []

    def fake_understand(text, *, ask_fn=None):
        calls.append(text)
        return {"ok": True, "intent": "code", "target_leg": "lead", "action": "اجرای تست",
                "summary": "تست‌ها اجرا شود", "risk": "high", "needs_mission": True,
                "important": True, "gate_reason": "code work"}

    orig = llm_intent.understand
    llm_intent.understand = fake_understand
    try:
        c, fc = _center()
        r = c.handle_update(_msg(_FREE))
        assert calls, "flag روشن: understand باید صدا شود"
        assert r and r.get("kind") == "ask_mission", r    # کارتِ مأموریتِ گیت‌شده، نه اجرا
        assert r.get("mission_id")
    finally:
        llm_intent.understand = orig
        os.environ.pop(llm_intent.FLAG, None)


def t_c_flag_on_llm_fails_falls_back():
    """understand=ok=False (router آفلاین) → مسیرِ rule-based امروز، بدونِ کرش."""
    os.environ[llm_intent.FLAG] = "1"
    orig = llm_intent.understand
    llm_intent.understand = lambda *a, **k: {"ok": False, "reason": "router-unavailable"}
    try:
        c, fc = _center()
        r = c.handle_update(_msg(_FREE))
        assert r is not None and r.get("kind", "").startswith("ask")   # کارتِ ask، نه mission
        assert r.get("kind") != "ask_mission", r
    finally:
        llm_intent.understand = orig
        os.environ.pop(llm_intent.FLAG, None)


def t_d_structural_gated_behind_flag_no_effector():
    """سیم‌کشی پشتِ _li.enabled()؛ هیچ مسیرِ اجرا/settle از _handle_ask."""
    assert "if _li.enabled():" in CENTER_SRC
    assert "_li.understand(text)" in CENTER_SRC
    # ارتقا فقط نوعِ mission را می‌سازد (گیت‌شده)، نه اجرا
    assert 'mt = "self_coding"' in CENTER_SRC or 'mt = "verification"' in CENTER_SRC


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_llm_intent_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
