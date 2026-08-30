#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_callback_answer — مرگِ spinner (منشور §۶.۴): هر تپ answerCallbackQuery.

سه مسیرِ تاریخیِ spinner (اسکنِ ۹۲-شکاف):
  · inner-bot-16/group-14: deny ِ سیاستِ ورودی روی callback هرگز answer نمی‌داد
    — سه کارتِ زندهٔ دکتر در General دقیقاً همین بودند.
  · oc: ِ blocked (adapter بی‌جواب/خراب) بدونِ answer برمی‌گشت.
  · و قاعدهٔ کلی: هر شاخهٔ _handle_callback باید answer بدهد.

استثنای عمدی: غیرمالک answer هم نمی‌گیرد (fail-closed — پاسخ وجودِ بات را لو
می‌دهد). این‌جا قفل می‌شود تا کسی «فیکسِ spinner» را به غیرمالک تعمیم ندهد.

همه با Center ِ واقعی + FakeClient (صفر شبکه)؛ حذفِ هر answer ِ تازه ⇒ قرمز.
"""
import json
import shutil
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness

ENV = harness.setup("tg-callback-answer")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"
OWNER = 777
GROUP = -1004475788460


class FakeClient:
    def __init__(self, owner_id=OWNER):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id       # سیاستِ ورودی این را می‌خوانَد
        self.center_chat_id = GROUP
        self.calls: list = []
        self._next_mid = 100

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "chat_id": chat_id,
                                    "topic_id": topic_id}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def create_topic(self, name, chat_id=None):
        return 50

    def set_commands(self, commands, scope=None):
        return True

    def delete_commands(self, scope=None):
        return True

    def poll_updates(self, offset=0, timeout_s=25):
        return []

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _write_cfg(**extra):
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = {"chat_id": GROUP, "topics": {"lead": 22, "system": 28}}
    cfg.update(extra)
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")


def _reset():
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    _write_cfg()


def _center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=None)
    return fc, c


def _dm_cbq(data, cid="cb1"):
    """callback ِ مالک در DM (سیاستِ ورودی: core_conversation → allow)."""
    return {"update_id": 1, "callback_query": {
        "id": cid, "from": {"id": OWNER}, "data": data,
        "message": {"message_id": 5,
                    "chat": {"id": OWNER, "type": "private"}}}}


# ── ۱) deny ِ سیاستِ ورودی روی callback باید answer بدهد ────────────────────
def t_a_policy_denied_group_callback_still_dismisses_the_spinner():
    """General ِ گروه = deny + redirect؛ ولی spinner هم باید بمیرد."""
    _reset()
    fc, c = _center()
    u = {"update_id": 2, "callback_query": {
        "id": "cb-deny", "from": {"id": OWNER}, "data": "mn:st",
        "message": {"message_id": 9,
                    "chat": {"id": GROUP, "type": "supergroup"}}}}
    res = c.handle_update(u)
    assert res and res.get("kind") == "input-policy", res
    ans = fc.named("answer")
    assert ans and ans[0]["id"] == "cb-deny", \
        "تپِ deny-شده answer نگرفت — spinner تا ابد می‌چرخد (inner-bot-16)"
    assert ans[0]["text"], "answer ِ خالی — مالک نمی‌فهمد چرا رد شد"


def t_b_policy_denied_unknown_topic_callback_is_also_answered():
    """تاپیکِ ناشناخته همان حکمِ General را دارد — و همان answer را."""
    _reset()
    fc, c = _center()
    u = {"update_id": 3, "callback_query": {
        "id": "cb-unk", "from": {"id": OWNER}, "data": "tk:q:lead",
        "message": {"message_id": 9, "message_thread_id": 999,
                    "is_topic_message": True,
                    "chat": {"id": GROUP, "type": "supergroup"}}}}
    res = c.handle_update(u)
    assert res and res.get("kind") == "input-policy", res
    assert fc.named("answer"), "deny ِ تاپیکِ ناشناخته answer نداد"


# ── ۲) oc: ِ blocked ────────────────────────────────────────────────────────
def t_c_a_blocked_owner_console_callback_is_answered():
    """adapter بی‌جواب (handled=False) ⇒ blocked — ولی دیگر بی‌answer نه."""
    _reset()
    fake_pkg = types.ModuleType("owner_console")
    fake_ad = types.ModuleType("owner_console.telegram_adapter")
    fake_ad.handle_callback = lambda data, surface_decision=None: {"handled": False}
    fake_ad.handle_message = lambda text, surface_decision=None: {"handled": False}
    fake_pkg.telegram_adapter = fake_ad
    old_pkg = sys.modules.get("owner_console")
    old_ad = sys.modules.get("owner_console.telegram_adapter")
    sys.modules["owner_console"] = fake_pkg
    sys.modules["owner_console.telegram_adapter"] = fake_ad
    try:
        fc, c = _center()
        res = c.handle_update(_dm_cbq("oc:unknown-verb", cid="cb-oc"))
        assert res == {"kind": "owner-console", "console_kind": "blocked"}, res
        ans = fc.named("answer")
        assert ans and ans[-1]["id"] == "cb-oc", \
            "مسیرِ oc:blocked هنوز spinner را زنده می‌گذارد"
    finally:
        for name, old in (("owner_console", old_pkg),
                          ("owner_console.telegram_adapter", old_ad)):
            if old is not None:
                sys.modules[name] = old
            else:
                sys.modules.pop(name, None)


# ── ۳) جاروی شاخه‌های _handle_callback ──────────────────────────────────────
def t_d_every_center_callback_verb_answers_at_least_once():
    """هر verb ِ روترِ مرکز (شاملِ malformed/ناشناخته) ≥۱ answer.

    فهرست عمداً مسیرهای ارزان/ایزوله را می‌پوشاند؛ verbهای فلگ‌دار (mo/m) و
    توکن‌دار در سوییت‌های خودشان‌اند."""
    datas = ["hm:home", "hm:st", "hm:legs", "hm:held", "hm:zz",
             "tk:q:lead", "tk:zz:lead",
             "mn:st", "mn:menu",
             "map:status", "map:zz",
             "ap:zz", "ms:zz",
             "tr:list", "iv:q", "dg:e:x", "mr:know",
             "ok:dec-answers", "no:dec-answers2", "later:dec-answers3"]
    for i, data in enumerate(datas):
        _reset()
        fc, c = _center()
        res = c.handle_update(_dm_cbq(data, cid=f"cb-{i}"))
        assert res is not None, data
        assert fc.named("answer"), \
            f"«{data}» بدونِ answerCallbackQuery برگشت — spinner ِ زنده"


# ── ۴) استثنای عمدی: غیرمالک همچنان سکوتِ مطلق ─────────────────────────────
def t_e_non_owner_callback_stays_totally_silent_by_design():
    """fail-closed: answer به غیرمالک وجودِ بات را لو می‌دهد. این «باگِ
    spinner» نیست؛ قرارداد است — و این‌جا قفل می‌شود."""
    _reset()
    fc, c = _center()
    u = {"update_id": 9, "callback_query": {
        "id": "cb-stranger", "from": {"id": 666}, "data": "mn:st",
        "message": {"message_id": 5,
                    "chat": {"id": OWNER, "type": "private"}}}}
    assert c.handle_update(u) is None
    assert fc.calls == [], "غیرمالک پاسخی گرفت — fail-closed شکست"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_callback_answer: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
