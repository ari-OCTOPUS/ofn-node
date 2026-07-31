"""test_tg_send_receipts.py — رسیدِ سه‌حالتیِ ارسال (منشور UX-8، موج W1 لِین C).

سه سکوتِ متفاوت تا ۰۷-۳۱ در tg-send-log یک شکل بودند: هیچ. حالا هر مسیرِ
خروجِ send_text/send/edit یک ردیف می‌گذارد:
  d="attempted" (واقعاً POST شد؛ ok = نتیجه) · d="held" (سکوت/HOLD نگه داشت)
  · d="blocked" (ساختاراً نمی‌توانست برود) + bot=outer|inner + surf=dm|group|hold.

صفر شبکه: http_post/post_fn تزریقی. رسیدها پشتِ فلگِ OCTOPUS_TG_SEND_LOG
(این‌جا روشن؛ فایلِ لاگ داخلِ STATE_DIR ِ harness است، نه درختِ زنده).
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-send-receipts")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib                    # noqa: E402
import approval_channel as ac    # noqa: E402
import surface_router as sr      # noqa: E402
import tg_api                    # noqa: E402
from tg_api import TgClient      # noqa: E402

OWNER = 555
GROUP = -1004475788460
TOPICS = {"lead": 22, "system": 28}

# رسیدها فقط با فلگ ثبت می‌شوند؛ envهای تلگرام پاک تا هیچ token/chat واقعی نشت نکند.
os.environ["OCTOPUS_TG_SEND_LOG"] = "1"
for _k in ("TELEGRAM_BOT_TOKEN", "TG_CENTER_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID"):
    os.environ.pop(_k, None)


# ─── ابزارک‌ها ───────────────────────────────────────────────────────────────
def _log_path() -> Path:
    return Path(opslib.STATE_DIR) / "tg-send-log.jsonl"


def _clear_log():
    p = _log_path()
    if p.exists():
        p.unlink()


def _rows() -> list:
    p = _log_path()
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


class Post:
    """http_postِ تزریقی — فقط بدنه را نگه می‌دارد."""

    def __init__(self):
        self.bodies = []

    def __call__(self, url, body):
        self.bodies.append(body)
        return {"ok": True, "result": {"message_id": 1}}


def _chan(post, token="t" * 10, owner=OWNER):
    return ac.TelegramApprovalChannel(token=token, owner_chat_id=owner,
                                      http_post=post)


class Net:
    """post_fn/get_fn ِ تزریقیِ tg_api — (method, body) را نگه می‌دارد."""

    def __init__(self):
        self.posts = []

    def post(self, url, body, timeout_s=10.0):
        self.posts.append((url.rsplit("/", 1)[-1].split("?", 1)[0], body))
        return {"ok": True, "result": {"message_id": 7}}

    def get(self, url, timeout_s):
        return {"ok": True, "result": []}


def _quiet(chan_mod, value):
    orig = chan_mod._quiet_now
    chan_mod._quiet_now = lambda: value
    return orig


def _write_cfg():
    p = Path(opslib.STATE_DIR) / "telegram" / "center-config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"chat_id": GROUP, "topics": dict(TOPICS)},
                            ensure_ascii=False), encoding="utf-8")


# ─── (a) ساعتِ سکوت → held ──────────────────────────────────────────────────
def t_a_quiet_non_interactive_writes_held_row():
    """پیامِ محیطیِ غیرِدکمه‌دار در سکوت: نه POST، ولی ردیفِ d="held" + surf="hold"
    و ورود به ماشینِ hold (سکوت ≠ فراموشی). جهش (return False ِ لخت) ⇒ قرمز."""
    held = []

    class _SP:
        HOLD = "hold"

        def route(self, stream):
            return (None, None)

        def hold(self, stream, text):
            held.append(str(stream))
            return True

    orig_q = _quiet(ac, True)
    orig_sp = ac.load_surface_policy
    ac.load_surface_policy = lambda: _SP()
    _clear_log()
    try:
        p = Post()
        assert _chan(p).send_text("گزارشِ ساعتِ ۳ صبح", None, stream="doctor") is False
        assert not p.bodies, "ساعتِ سکوت نباید بفرستد"
        assert held == ["doctor"], "پیامِ سکوت باید واردِ ماشینِ hold شود"
        rows = _rows()
        assert rows, "رسیدِ held غایب است"
        r = rows[-1]
        assert r["d"] == "held" and r["ok"] is False, r
        assert r["bot"] == "inner" and r["surf"] == "hold", r
    finally:
        ac._quiet_now = orig_q
        ac.load_surface_policy = orig_sp


# ─── (b) حکمِ HOLD ِ سیاست → held ───────────────────────────────────────────
def t_b_hold_policy_writes_held_row():
    held = []

    class _SP:
        HOLD = "hold"

        def route(self, stream):
            return ("hold", "classify")

        def hold(self, stream, text):
            held.append(str(stream))
            return True

    orig_q = _quiet(ac, False)
    orig_sp = ac.load_surface_policy
    ac.load_surface_policy = lambda: _SP()
    _clear_log()
    try:
        p = Post()
        assert _chan(p).send_text("جریانِ محیطی", None, stream="needs") is False
        assert not p.bodies and held == ["needs"]
        r = _rows()[-1]
        assert r["d"] == "held" and r["surf"] == "hold" and r["ok"] is False, r
        assert r["bot"] == "inner", r
    finally:
        ac._quiet_now = orig_q
        ac.load_surface_policy = orig_sp


# ─── (c) not-wired → blocked ────────────────────────────────────────────────
def t_c_not_wired_writes_blocked_row():
    """کانالِ بی‌سیم هم باید رد بگذارد — «نفرستاد چون نمی‌توانست» ≠ هیچ."""
    _clear_log()
    p = Post()
    ch = _chan(p, token="", owner=None)
    assert ch.wired is False
    assert ch.send_text("پیامی که جایی ندارد") is False
    assert not p.bodies
    r = _rows()[-1]
    assert r["d"] == "blocked" and r["ok"] is False, r
    assert r["bot"] == "inner", r


# ─── (d) ارسالِ عادی → attempted + bot/surf ─────────────────────────────────
def t_d_normal_send_writes_attempted_inner_dm_and_group():
    orig_q = _quiet(ac, False)
    _write_cfg()
    _clear_log()
    try:
        # DM ِ مالک (بدونِ روتینگ)
        p = Post()
        assert _chan(p).send_text("سلام", None, stream="chat-note") is True
        r = _rows()[-1]
        assert r["d"] == "attempted" and r["ok"] is True, r
        assert r["bot"] == "inner" and r["surf"] == "dm", r
        # جریانِ پا با فلگِ روتینگ → گروه/تاپیک → surf="group"
        os.environ[ac.ROUTE_FLAG] = "1"
        try:
            p2 = Post()
            assert _chan(p2).send_text("لیدِ تازه", None, stream="lead") is True
            assert p2.bodies[-1]["chat_id"] == GROUP
            assert p2.bodies[-1]["message_thread_id"] == TOPICS["lead"]
            r2 = _rows()[-1]
            assert r2["d"] == "attempted" and r2["surf"] == "group", r2
            assert r2["topic"] == TOPICS["lead"], r2
        finally:
            os.environ.pop(ac.ROUTE_FLAG, None)
    finally:
        ac._quiet_now = orig_q


# ─── (e) tg_api: bot_role/surface از منبعِ token ─────────────────────────────
def t_e_tg_api_send_records_bot_role_and_surface():
    """توکنِ TG_CENTER_BOT_TOKEN → bot="outer"؛ chat ِ حل‌شده == مالک → surf="dm".
    توکنِ صریحِ برابر با TELEGRAM_BOT_TOKEN (مسیرِ inner ِ مرکز) → bot="inner"."""
    os.environ["TG_CENTER_BOT_TOKEN"] = "999888:OUTER-FAKE"
    _clear_log()
    try:
        net = Net()
        c = TgClient(owner_chat_id=777, post_fn=net.post, get_fn=net.get)
        assert c._token_source == "TG_CENTER_BOT_TOKEN"
        assert c.send("متنِ آزمایشی") == 7
        r = _rows()[-1]
        assert r["d"] == "attempted" and r["ok"] is True, r
        assert r["bot"] == "outer" and r["surf"] == "dm", r
        assert r["stream"] == "center", r
    finally:
        os.environ.pop("TG_CENTER_BOT_TOKEN", None)
    # مسیرِ inner ِ مرکز: توکنِ صریح == env TELEGRAM_BOT_TOKEN
    os.environ["TELEGRAM_BOT_TOKEN"] = "111222:INNER-FAKE"
    try:
        net2 = Net()
        c2 = TgClient(token="111222:INNER-FAKE", owner_chat_id=777,
                      post_fn=net2.post, get_fn=net2.get)
        assert c2.send("متنِ دوم") == 7
        r2 = _rows()[-1]
        assert r2["bot"] == "inner" and r2["surf"] == "dm", r2
    finally:
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)


# ─── (f) edit هم رسید می‌نویسد ──────────────────────────────────────────────
def t_f_edit_writes_receipt_row():
    """اسکن A T-8: ~۲۸۸ edit ِ بی‌رسید در روز (کارتِ pin و کارتِ پاها).
    حالا هر edit یک ردیفِ attempted با stream="edit" می‌گذارد."""
    _clear_log()
    net = Net()
    c = TgClient(token="123:X", owner_chat_id=777, center_chat_id=GROUP,
                 post_fn=net.post, get_fn=net.get)
    assert c.edit(9, "متنِ نو") is True
    r = _rows()[-1]
    assert r["stream"] == "edit" and r["d"] == "attempted" and r["ok"] is True, r
    assert r["surf"] == "group", r          # مقصدِ پیش‌فرض = گروهِ مرکز
    assert r["chat"] == GROUP, r


# ─── (g) resolve(interactive=True) هرگز inner نمی‌دهد ───────────────────────
def t_g_resolve_interactive_never_returns_inner():
    """روی همهٔ جریان‌های فایلِ روتینگ، در هر دو حالتِ فلگ: کارتِ دکمه‌دار
    هرگز کلاینتِ send-only ِ inner را نمی‌گیرد (BLOCK_CARD_EMISSION)."""

    class FakeClient:
        def __init__(self, name):
            self.name = name
            self.owner_chat_id = OWNER
            self.center_chat_id = GROUP

        def wired(self):
            return True

    cl = {"outer": FakeClient("outer"), "inner": FakeClient("inner")}
    streams = list(sr._load_streams().keys()) + ["no-such-stream"]
    for flag_on in (False, True):
        if flag_on:
            os.environ[sr.FLAG] = "1"
        else:
            os.environ.pop(sr.FLAG, None)
        try:
            for s in streams:
                client, _, _ = sr.resolve(s, clients=cl, cfg={"chat_id": GROUP,
                                                              "topics": dict(TOPICS)},
                                          interactive=True)
                assert client is not cl["inner"], \
                    f"جریانِ دکمه‌دارِ {s!r} (flag={flag_on}) به inner رفت"
        finally:
            os.environ.pop(sr.FLAG, None)


# ─── (h) set_commands با scope ──────────────────────────────────────────────
def t_h_set_commands_passes_scope_through():
    net = Net()
    c = TgClient(token="123:X", owner_chat_id=777, post_fn=net.post, get_fn=net.get)
    scope = {"type": "all_private_chats"}
    assert c.set_commands([("status", "وضعیت")], scope=scope) is True
    m, body = net.posts[-1]
    assert m == "setMyCommands"
    assert body["scope"] == scope, body
    assert body["commands"] == [{"command": "status", "description": "وضعیت"}]
    # بدونِ scope → بدنهٔ دیروز (هیچ کلیدِ scope)
    assert c.set_commands([("status", "وضعیت")]) is True
    assert "scope" not in net.posts[-1][1]


# ─── (i) delete_commands ────────────────────────────────────────────────────
def t_i_delete_commands_posts_deleteMyCommands():
    net = Net()
    c = TgClient(token="123:X", owner_chat_id=777, post_fn=net.post, get_fn=net.get)
    assert c.delete_commands() is True
    m, body = net.posts[-1]
    assert m == "deleteMyCommands" and body == {}, (m, body)
    scope = {"type": "chat", "chat_id": GROUP}
    assert c.delete_commands(scope=scope) is True
    m2, body2 = net.posts[-1]
    assert m2 == "deleteMyCommands" and body2 == {"scope": scope}, (m2, body2)


# ─── منوی inner: تک‌نویسنده و ≤۴ فرمانِ زنده (منشور §۱) ─────────────────────
def t_j_inner_menu_is_small_and_handlers_exist():
    """approval_channel تنها نویسندهٔ منوی inner است؛ منو ≤۴ فرمان و هر
    فرمانش handler ِ زنده دارد. جهش (برگشتِ منوی ۲۳تایی) ⇒ قرمز."""
    posts = []

    def post(url, body):
        posts.append((url.rsplit("/", 1)[-1].split("?", 1)[0], body))
        return {"ok": True}

    ch = _chan(post)
    ch._set_my_commands()
    methods = [m for m, _ in posts]
    assert methods == ["deleteMyCommands", "setMyCommands"], methods
    cmds = posts[-1][1]["commands"]
    assert 0 < len(cmds) <= 4, f"منوی inner باید ≤۴ فرمان باشد: {len(cmds)}"
    for c in cmds:
        reply = ch.handle_command("/" + c["command"])
        assert reply is not None, f"فرمانِ منو بدونِ handler: /{c['command']}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_send_receipts: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
