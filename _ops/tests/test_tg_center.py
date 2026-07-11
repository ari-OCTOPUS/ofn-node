"""test_tg_center.py — مرکزِ فرماندهیِ تلگرام (telegram_center/center.py).

پوشش: setup دوباره = idempotent؛ beat فقط status را edit می‌کند (هرگز sendِ دوباره)؛
cadence دایجست با clockِ تزریقی؛ callbackِ غیرمالک = سکوتِ کامل؛ okِ مالک = فایلِ
approval + توکنِ HumanAppendGuard (فقط با راز) + answer؛ فایلِ STOP حلقه را می‌ایستاند؛
و not-wired = صفر اثر. صفر شبکه (client/render ِ fake) و صفر نوشتن خارج از temp harness.
"""
import json
import os
import shutil
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-center")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"
APPROVALS = opslib.STATE_DIR / "telegram" / "approvals"
ALL_LEGS = ("lead", "ziman", "mining", "crypto", "accounting",
            "studio_pf", "system", "knowledge")


# ─── fakeها (صفر شبکه، فقط ثبتِ فراخوان‌ها) ─────────────────────────────────────
class FakeClient:
    def __init__(self, wired=True, owner_id=777):
        self._is_wired = wired
        self.owner_id = owner_id
        self.calls: list = []
        self._next_mid = 100
        self._next_topic = 10
        self.updates: list = []

    def wired(self):
        return self._is_wired

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "keyboard": keyboard, "chat_id": chat_id,
                                    "pin": pin}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def pin_message(self, message_id, chat_id=None):
        self.calls.append(("pin", {"message_id": message_id}))
        return True

    def create_topic(self, name, chat_id=None):
        self.calls.append(("create_topic", {"name": name}))
        self._next_topic += 1
        return self._next_topic

    def set_commands(self, commands):
        self.calls.append(("set_commands", {"commands": list(commands)}))
        return True

    def poll_updates(self, offset=0, timeout_s=25):
        self.calls.append(("poll", {"offset": offset}))
        ups, self.updates = self.updates, []
        return ups

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def fake_render(guidance_items=None):
    """renderِ قراردادی (پاک، بدونِ شبکه) برای تزریق به Center."""
    legs = {k: {} for k in ALL_LEGS}

    def collect_feeds():
        return {"guidance": {"items": list(guidance_items or [])}}

    def render_status(feeds):
        return "STATUS-LINE"

    def render_leg_digest(leg_key, leg):
        return f"digest:{leg_key}"

    def render_decision(item):
        did = item.get("id", "x")
        kb = [[{"text": "✅", "callback_data": f"ok:{did}"},
               {"text": "❌", "callback_data": f"no:{did}"},
               {"text": "⏳", "callback_data": f"later:{did}"}]]
        return (f"decision:{did}", kb)

    def scrub(t):
        return t

    return types.SimpleNamespace(LEGS=legs, collect_feeds=collect_feeds,
                                 render_status=render_status,
                                 render_leg_digest=render_leg_digest,
                                 render_decision=render_decision, scrub=scrub)


class Clock:
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t


def _reset():
    """state تلگرامِ temp را بینِ تست‌ها پاک کن (config حافظهٔ idempotency است)."""
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    if center.STOP_TG_CENTER.exists():
        center.STOP_TG_CENTER.unlink()


# ─── تست‌ها ──────────────────────────────────────────────────────────────────────
def t_a_double_ensure_setup_idempotent():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.ensure_setup() is True
    assert len(fc.named("create_topic")) == 8          # هر ۸ پا یک تاپیک
    assert len(fc.named("set_commands")) == 1
    sends = fc.named("send")
    assert len(sends) == 1 and sends[0]["pin"] is True  # status یک‌بار + پین
    assert c.ensure_setup() is True                     # دور دوم
    assert len(fc.named("create_topic")) == 8           # هیچ تاپیکِ تکراری
    assert len(fc.named("set_commands")) == 1
    assert len(fc.named("send")) == 1                   # status دوباره ساخته نشد
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert isinstance(cfg.get("status_message_id"), int)
    assert sorted(cfg.get("topics", {}).keys()) == sorted(ALL_LEGS)


def t_b_beat_edits_status_never_resends():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    c.ensure_setup()
    status_mid = json.loads(CFG_PATH.read_text("utf-8"))["status_message_id"]
    fc.calls.clear()
    out1 = c.beat()                                     # اولین beat: همهٔ دایجست‌ها سررسیده
    assert out1["edited"] is True and out1["digests"] == 8
    edits = fc.named("edit")
    assert len(edits) == 1 and edits[0]["message_id"] == status_mid
    assert all(s["pin"] is False for s in fc.named("send"))   # هیچ sendِ پین‌شده (status) دوباره
    fc.calls.clear()
    out2 = c.beat()                                     # بلافاصله: هیچ دایجستی سررسید نیست
    assert out2["edited"] is True and out2["digests"] == 0
    assert len(fc.named("send")) == 0                   # فقط edit، صفر send
    assert len(fc.named("edit")) == 1


def t_c_digest_cadence_respects_injected_clock():
    _reset()
    fc = FakeClient()
    clk = Clock(50_000.0)
    c = center.Center(client=fc, clock=clk, render_mod=fake_render())
    c.ensure_setup()
    fc.calls.clear()
    assert c.beat()["digests"] == 8                     # صفر سابقه → همه due
    clk.t += 3600.0
    assert c.beat()["digests"] == 0                     # هنوز ۲۴h نشده
    clk.t += 86400.0
    assert c.beat()["digests"] == 8                     # سررسیدِ دوباره
    # override per-leg از config: فقط lead هر ۶۰ ثانیه
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    cfg["cadence_s"] = {"lead": 60, "default": 86400}
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    clk.t += 61.0
    out = c.beat()
    assert out["digests"] == 1                          # فقط lead due شد
    assert fc.named("send")[-1]["text"] == "digest:lead"


def t_d_decisions_posted_once_with_keyboard_dedupe_seen():
    _reset()
    items = [{"q": "یک تصمیم؟", "why": "w", "source": "approval", "priority": "high"}]
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render(items))
    c.ensure_setup()
    fc.calls.clear()
    assert c.beat()["decisions"] == 1
    dec = [s for s in fc.named("send") if s["keyboard"]]
    assert len(dec) == 1
    assert dec[0]["keyboard"][0][0]["callback_data"].startswith("ok:")
    assert c.beat()["decisions"] == 0                   # dedupe با seen در config
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert len(cfg.get("seen", [])) == 1


def t_e_callback_from_non_owner_ignored():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 5,
         "callback_query": {"id": "cb1", "from": {"id": 666}, "data": "ok:dec-1"}}
    assert c.handle_update(u) is None                   # سکوتِ کامل
    assert len(fc.named("answer")) == 0
    assert not (APPROVALS / "dec-1.json").exists()


def t_f_ok_callback_records_file_mints_token_and_answers():
    _reset()
    os.environ["HH_HUMAN_GUARD_SECRET"] = "test-secret-123"
    try:
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        u = {"update_id": 6,
             "callback_query": {"id": "cb2", "from": {"id": 777}, "data": "ok:dec-2"}}
        res = c.handle_update(u)
        assert res and res["verdict"] == "ok" and res["recorded"] is True
        rec = json.loads((APPROVALS / "dec-2.json").read_text("utf-8"))
        assert rec["verdict"] == "ok" and rec.get("ha_token")
        # توکن واقعاً با همان راز معتبر است (mint → authorize)
        from human_append_guard import HumanAppendGuard
        g = HumanAppendGuard(b"test-secret-123")
        ok, reason = g.authorize("APPROVAL", True, token=rec["ha_token"])
        assert ok is True, reason
        answers = fc.named("answer")
        assert len(answers) == 1 and answers[0]["id"] == "cb2"
    finally:
        os.environ.pop("HH_HUMAN_GUARD_SECRET", None)


def t_g_ok_without_secret_records_without_token_no_crash():
    _reset()
    os.environ.pop("HH_HUMAN_GUARD_SECRET", None)
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 7,
         "callback_query": {"id": "cb3", "from": {"id": 777}, "data": "no:dec-3"}}
    res = c.handle_update(u)
    assert res and res["verdict"] == "no" and res["recorded"] is True
    rec = json.loads((APPROVALS / "dec-3.json").read_text("utf-8"))
    assert rec["verdict"] == "no" and "ha_token" not in rec
    assert len(fc.named("answer")) == 1


def t_h_now_command_sends_status():
    _reset()
    fc = FakeClient(owner_id=777)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    u = {"update_id": 8,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "/now"}}
    res = c.handle_update(u)
    assert res and res["kind"] == "now" and res["sent"] is True
    assert fc.named("send")[-1]["text"] == "STATUS-LINE"


def t_i_run_once_dispatches_and_advances_offset():
    _reset()
    fc = FakeClient(owner_id=777)
    fc.updates = [
        {"update_id": 41,
         "message": {"from": {"id": 777}, "chat": {"id": 777}, "text": "/now"}},
        {"update_id": 42,
         "callback_query": {"id": "c9", "from": {"id": 777}, "data": "later:dec-9"}},
    ]
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.run_once() == 2
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert cfg["last_offset"] == 43                     # restart-safe
    assert len(fc.named("answer")) == 1                 # callback جواب گرفت
    rec = json.loads((APPROVALS / "dec-9.json").read_text("utf-8"))
    assert rec["verdict"] == "later"


def t_j_stop_file_halts_run_loop():
    _reset()
    center.STOP_TG_CENTER.parent.mkdir(parents=True, exist_ok=True)
    center.STOP_TG_CENTER.write_text("halt", "utf-8")
    try:
        fc = FakeClient(owner_id=777)
        c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
        c.run_forever()                                 # باید فوراً برگردد
        assert fc.calls == []                           # حتی ensure_setup هم اجرا نشد
        assert c.run_once() == 0                        # run_once هم تسلیمِ STOP است
        assert len(fc.named("poll")) == 0
    finally:
        center.STOP_TG_CENTER.unlink()


def t_k_zero_effect_when_not_wired():
    _reset()
    fc = FakeClient(wired=False)
    c = center.Center(client=fc, clock=Clock(), render_mod=fake_render())
    assert c.ensure_setup() is False
    assert c.beat() == {"edited": False, "digests": 0, "decisions": 0}
    assert c.run_once() == 0
    u = {"update_id": 9,
         "callback_query": {"id": "cb", "from": {"id": 777}, "data": "ok:z"}}
    assert c.handle_update(u) is None
    c.run_forever()
    assert fc.calls == []                               # صفر فراخوانِ client
    assert not (opslib.STATE_DIR / "telegram").exists()  # صفر نوشتنِ state


def t_l_missing_client_module_is_safe_noop():
    """client=None و tg_api غایب → Center بدونِ crash می‌سازد و همه‌چیز no-op است."""
    _reset()
    c = center.Center(clock=Clock(), render_mod=fake_render())
    assert c.wired() is False
    assert c.ensure_setup() is False
    assert c.beat()["digests"] == 0
    assert c.run_once() == 0


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_center: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
