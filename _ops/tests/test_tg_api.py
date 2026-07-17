"""test_tg_api.py — کلاینتِ نازکِ تلگرامِ مرکز (telegram_center.tg_api).

صفر شبکهٔ واقعی: post_fn/get_fn جعلی تزریق می‌شوند و هر تماس capture می‌شود.
صفر نوشتنِ state خارج از دایرکتوری‌های harness (envها قبل از import ست شده‌اند).
"""
import json
import os
import sys
import urllib.parse
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-api")

# envهای تلگرام را پاک کن تا (۱) تستِ «بی‌token = no-op» قطعی باشد و (۲) هیچ
# tokenِ واقعیِ محیط به کلاینت نشت نکند — صفر شبکه، صفر secret.
for _k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_CHAT_ID", "TG_CENTER_CHAT_ID"):
    os.environ.pop(_k, None)

from telegram_center import tg_api            # noqa: E402
from telegram_center.tg_api import TgClient   # noqa: E402

OWNER = 777
CENTER = -1009999
TOKEN = "123456:TEST-FAKE"   # جعلی — فقط برای assertِ ساختِ URL؛ هرگز شبکه


class FakeNet:
    """transportِ جعلیِ تزریقی: هر تماس را capture می‌کند؛ پاسخ per-method قابل‌تنظیم؛
    raise_on برای شبیه‌سازیِ خطای شبکه. هیچ I/O واقعی."""

    def __init__(self, responses=None):
        self.posts = []   # (method, url, body)
        self.gets = []    # (method, url, timeout_s)
        self.responses = dict(responses or {})
        self.raise_on = set()

    @staticmethod
    def _method(url):
        return url.rsplit("/", 1)[-1].split("?", 1)[0]

    def post(self, url, body, timeout_s=10.0):
        m = self._method(url)
        self.posts.append((m, url, body))
        if m in self.raise_on:
            raise OSError("net down (fake)")
        return self.responses.get(m, {"ok": True, "result": {}})

    def get(self, url, timeout_s):
        m = self._method(url)
        self.gets.append((m, url, timeout_s))
        if m in self.raise_on:
            raise OSError("net down (fake)")
        return self.responses.get(m, {"ok": True, "result": []})


def _client(responses=None, token=TOKEN, owner=OWNER, center=CENTER):
    net = FakeNet(responses)
    c = TgClient(token=token, owner_chat_id=owner, center_chat_id=center,
                 post_fn=net.post, get_fn=net.get)
    return c, net


# رشته‌های ممنوع، به‌صورتِ پویا ساخته می‌شوند تا خودِ فایلِ تست هم echoشان نکند
_BANNED_DYNAMIC = ("only" + "fans", "اون" + "لی", "ص" + "با")


def t_a_unwired_no_token_all_noop_zero_network():
    """بی‌token (env هم پاک است) → wired False → همهٔ متدها no-opِ امن، صفر تماس."""
    net = FakeNet()
    c = TgClient(post_fn=net.post, get_fn=net.get)   # همه از env → همه خالی
    assert c.wired() is False
    assert c.send("سلام") is None
    assert c.send("سلام", topic_id=1, keyboard=[[{"text": "x", "callback_data": "ok:1"}]],
                  chat_id=123, pin=True) is None
    assert c.edit(1, "متن") is False
    assert c.pin_message(1) is False
    assert c.create_topic("تاپیک") is None
    assert c.set_commands([("start", "منو")]) is False
    assert c.poll_updates() == []
    assert c.poll_updates(offset=9, timeout_s=1) == []
    assert c.answer_callback("cb1", "متن") is False
    assert net.posts == [] and net.gets == []        # صفرِ مطلقِ شبکه


def t_b_unwired_token_but_no_chat_id():
    """token هست ولی هیچ chat id نیست → همچنان no-op و صفر شبکه (قراردادِ flag-off)."""
    net = FakeNet()
    c = TgClient(token=TOKEN, post_fn=net.post, get_fn=net.get)   # chatها از env → None
    assert c.wired() is False
    assert c.send("x") is None
    assert c.poll_updates() == []
    assert net.posts == [] and net.gets == []


def t_c_send_builds_correct_payload():
    c, net = _client({"sendMessage": {"ok": True, "result": {"message_id": 42}}})
    kb = [[{"text": "باشه", "callback_data": "ok:g1"},
           {"text": "نه", "callback_data": "no:g1"}]]
    mid = c.send("<b>وضعیت</b> روان", topic_id=7, keyboard=kb)
    assert mid == 42
    m, url, body = net.posts[0]
    assert m == "sendMessage"
    assert url == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert body["chat_id"] == CENTER                 # پیش‌فرض = چتِ مرکز
    assert body["text"] == "<b>وضعیت</b> روان"
    assert body["parse_mode"] == "HTML"
    assert body["message_thread_id"] == 7
    assert body["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "ok:g1"
    assert body["reply_markup"]["inline_keyboard"][0][1]["text"] == "نه"


def t_d_send_pin_and_explicit_chat():
    """pin=True → بعد از send موفق، pinChatMessage با همان message_id/chat."""
    c, net = _client({"sendMessage": {"ok": True, "result": {"message_id": 5}}})
    mid = c.send("پیامِ سنجاق", chat_id=OWNER, pin=True)
    assert mid == 5
    assert [p[0] for p in net.posts] == ["sendMessage", "pinChatMessage"]
    assert net.posts[0][2]["chat_id"] == OWNER       # chat_id صریح بر مرکز مقدم
    pin_body = net.posts[1][2]
    assert pin_body == {"chat_id": OWNER, "message_id": 5, "disable_notification": True}


def t_e_edit_and_pin_payloads():
    c, net = _client()
    assert c.edit(9, "متنِ نو", keyboard=[[{"text": "ب", "callback_data": "pg:1"}]]) is True
    m, _, body = net.posts[0]
    assert m == "editMessageText"
    assert body["chat_id"] == CENTER and body["message_id"] == 9
    assert body["text"] == "متنِ نو" and body["parse_mode"] == "HTML"
    assert body["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "pg:1"
    assert c.pin_message(3, chat_id=111) is True
    m2, _, body2 = net.posts[1]
    assert m2 == "pinChatMessage" and body2["chat_id"] == 111 and body2["message_id"] == 3
    # پاسخِ ok=False از API → False (نه crash)
    c2, _ = _client({"editMessageText": {"ok": False, "error_code": 400}})
    assert c2.edit(9, "x") is False


def t_f_create_topic():
    c, net = _client({"createForumTopic": {"ok": True,
                                           "result": {"message_thread_id": 88, "name": "n"}}})
    tid = c.create_topic("Lead-نقاشی")
    assert tid == 88
    m, _, body = net.posts[0]
    assert m == "createForumTopic"
    assert body == {"chat_id": CENTER, "name": "Lead-نقاشی"}
    # پاسخِ بد → None
    c2, _ = _client({"createForumTopic": {"ok": False}})
    assert c2.create_topic("x") is None
    # نامِ خالی → None و صفر تماس
    c3, net3 = _client()
    assert c3.create_topic("   ") is None and net3.posts == []


def t_g_set_commands():
    c, net = _client()
    assert c.set_commands([("now", "وضعیتِ الان"), ("/status", "وضعیت")]) is True
    m, _, body = net.posts[0]
    assert m == "setMyCommands"
    assert body["commands"] == [{"command": "now", "description": "وضعیتِ الان"},
                                {"command": "status", "description": "وضعیت"}]
    # لیستِ خالی/فرمِ خراب → False و صفر تماسِ اضافه
    assert c.set_commands([]) is False
    assert c.set_commands("bad-shape") is False
    assert len(net.posts) == 1


def t_h_poll_updates_offset_math():
    ups_payload = [{"update_id": 10, "message": {"text": "/now"}},
                   {"update_id": 12, "callback_query": {"id": "c1", "data": "ok:x"}},
                   "junk-not-dict"]
    c, net = _client({"getUpdates": {"ok": True, "result": ups_payload}})
    ups = c.poll_updates(offset=5, timeout_s=3)
    assert len(ups) == 2                              # غیرdict فیلتر شد
    m, url, timeout = net.gets[0]
    assert m == "getUpdates" and timeout == 3.0
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["offset"] == ["5"] and q["timeout"] == ["3"]
    assert json.loads(q["allowed_updates"][0]) == ["message", "callback_query"]
    # ریاضیِ offset: بیشینهٔ update_id + 1؛ لیستِ خالی → همان current
    assert TgClient.next_offset(ups, 5) == 13
    assert TgClient.next_offset([], 5) == 5
    assert TgClient.next_offset([{"update_id": "bad"}], 2) == 2
    # پاسخِ ok=False → []
    c2, _ = _client({"getUpdates": {"ok": False, "error_code": 409}})
    assert c2.poll_updates() == []


def t_i_answer_callback():
    c, net = _client()
    assert c.answer_callback("cb-9", "<i>ثبت شد ✅</i>") is True
    m, _, body = net.posts[0]
    assert m == "answerCallbackQuery"
    assert body["callback_query_id"] == "cb-9"
    assert body["text"] == "ثبت شد ✅"                # toast متنِ ساده: تگ‌ها strip شدند
    assert body["cache_time"] == 0
    assert c.answer_callback("", "x") is False        # id خالی → no-op
    assert len(net.posts) == 1


def t_j_is_owner_allowlist():
    c, _ = _client()
    assert c.is_owner({"message": {"from": {"id": OWNER}, "chat": {"id": CENTER}}}) is True
    assert c.is_owner({"callback_query": {"id": "c", "from": {"id": OWNER}}}) is True
    assert c.is_owner({"edited_message": {"from": {"id": OWNER}}}) is True
    assert c.is_owner({"message": {"from": {"id": 666}}}) is False      # غریبه = رد
    assert c.is_owner({"message": {"chat": {"id": OWNER}}}) is False    # from غایب = رد
    assert c.is_owner({}) is False and c.is_owner(None) is False
    # مالکِ پیکربندی‌نشده → همیشه False (fail-closed)
    c2 = TgClient(token=TOKEN, owner_chat_id=None, center_chat_id=CENTER,
                  post_fn=FakeNet().post, get_fn=FakeNet().get)
    assert c2.is_owner({"message": {"from": {"id": OWNER}}}) is False


def t_k_failsoft_transport_errors():
    """خطای transport → پیش‌فرضِ امن، هرگز exception به caller؛ فقط یک تلاش."""
    c, net = _client()
    net.raise_on.update({"sendMessage", "editMessageText", "pinChatMessage",
                         "createForumTopic", "setMyCommands", "getUpdates",
                         "answerCallbackQuery"})
    assert c.send("x") is None
    assert c.edit(1, "x") is False
    assert c.pin_message(1) is False
    assert c.create_topic("t") is None
    assert c.set_commands([("a", "b")]) is False
    assert c.poll_updates() == []
    assert c.answer_callback("cb") is False
    # هر متد دقیقاً یک تلاش (بدونِ retry-storm)
    assert len(net.posts) == 6 and len(net.gets) == 1


def t_l_containment_scrub_outgoing():
    """هیچ رشتهٔ ممنوع (containment) در بدنهٔ خروجی echo نمی‌شود — send/edit/toast/کیبورد."""
    c, net = _client({"sendMessage": {"ok": True, "result": {"message_id": 1}}})
    for banned in _BANNED_DYNAMIC:
        c.send(f"دایجست {banned} پا",
               keyboard=[[{"text": f"برو {banned}", "callback_data": "leg:studio_pf"}]])
        c.edit(1, f"وضعیت {banned}")
        c.answer_callback("cb", f"ثبت {banned}")
    dump = json.dumps([p[2] for p in net.posts], ensure_ascii=False).lower()
    for banned in _BANNED_DYNAMIC:
        assert banned.lower() not in dump, f"banned echo leaked: {banned!r}"
    # callback_dataهای کلیدی (بی‌محتوا) دست‌نخورده ماندند
    assert "leg:studio_pf" in dump


def t_m_token_never_echoed():
    """token هرگز در repr نمی‌آید؛ mask فقط ۴ نویسهٔ اول را نشان می‌دهد."""
    c, _ = _client()
    assert TOKEN not in repr(c)
    assert "1234…" in repr(c)
    assert tg_api._mask_token("") == "∅"
    assert tg_api._mask_token("ab") == "…"


def t_n_default_transport_blocks_foreign_host():
    """transportِ پیش‌فرض هر URLِ غیرِ api.telegram.org را قبل از هر شبکه‌ای رد می‌کند."""
    try:
        tg_api._url_json_get("https://evil.example.com/bot123/getUpdates", 1.0)
        raised = False
    except ValueError:
        raised = True
    assert raised
    try:
        tg_api._url_json_post("http://api.telegram.org.evil.tld/botx/sendMessage", {})
        raised = False
    except ValueError:
        raised = True
    assert raised


def t_o_empty_text_is_noop():
    """متنِ خالی/فقط‌فاصله → ارسال نمی‌شود (تلگرام هم رد می‌کرد؛ صفر تماسِ بی‌ثمر)."""
    c, net = _client()
    assert c.send("") is None
    assert c.send("   ") is None
    assert c.edit(1, "") is False
    assert net.posts == []


def t_z_edit_not_modified_is_success_no_alert():
    """400ِ «message is not modified» = وضعِ مطلوب از قبل برقرار → edit موفق، بی‌هشدار
    (قبلاً هر بوت یک ⚠️ کاذب در /alerts می‌نشاند). خطاهای دیگرِ HTTP همچنان False."""
    import io
    import json as _json
    import urllib.error

    def _herr(desc):
        body = _json.dumps({"ok": False, "error_code": 400,
                            "description": desc}).encode("utf-8")
        return urllib.error.HTTPError("u", 400, "Bad Request", {}, io.BytesIO(body))

    c, net = _client()
    calls = {"n": 0}

    def post_not_modified(url, body, timeout_s=10.0):
        calls["n"] += 1
        raise _herr("Bad Request: message is not modified")

    c._post = post_not_modified
    alerts: list = []
    c._last_alert.clear()
    from telegram_center import tg_api as _t
    orig_alert = _t._alert_soft
    _t._alert_soft = alerts.append
    try:
        assert c.edit(66, "same text") is True, "not-modified باید موفق شمرده شود"
        assert alerts == [], "not-modified نباید هشدار بدهد"
        c._post = lambda *a, **k: (_ for _ in ()).throw(_herr("Bad Request: chat not found"))
        assert c.edit(66, "x") is False, "خطای واقعی همچنان False"
        assert alerts and "chat not found" in alerts[0], "descriptionِ کوتاه در هشدار"
    finally:
        _t._alert_soft = orig_alert
    assert calls["n"] == 1


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_api: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
