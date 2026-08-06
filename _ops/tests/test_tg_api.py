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
    assert c.set_commands([("start", "منو")], scope={"type": "all_private_chats"}) is False
    assert c.delete_commands() is False
    assert c.delete_commands(scope={"type": "all_private_chats"}) is False
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


def t_c2_send_to_dm_never_sets_message_thread_id():
    """آیتم ۳ِ TG-P2: فرستادنِ message_thread_id به چتِ خصوصی (DM، chat_id ≥ ۰) =
    ۴۰۰ Bad Request. حتی اگر topic_id داده شود، در DM باید نادیده گرفته شود.

    پاریتیِ گروه سالم می‌ماند (تستِ t_c با سوپرگروهِ forum CENTER=-1009999); این
    تست فقط مسیرِ DM را قفل می‌کند. جهش (حذفِ گاردِ ``cid < -1000``) این تست را
    قرمز می‌کند."""
    c, net = _client({"sendMessage": {"ok": True, "result": {"message_id": 9}}})
    # chat_id=OWNER=777 (مثبت = DM) + topic_id داده شده ⇒ باید نادیده گرفته شود
    mid = c.send("سلامِ خصوصی", topic_id=7, chat_id=OWNER)
    assert mid == 9
    body = net.posts[0][2]
    assert body["chat_id"] == OWNER
    assert "message_thread_id" not in body, \
        "DM نباید message_thread_id بگیرد (۴۰۰ از تلگرام)"


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


def t_e2_delete_payload_and_failsoft():
    """۲۰۲۶-۰۸-۰۶: کارتِ رأیِ تأییدشده/ردشده حذف می‌شود، نه ادیت — این تست خودِ
    متدِ delete() را می‌سنجد؛ رفتارِ سرِ callback در test_tg_center.py."""
    c, net = _client()
    assert c.delete(9, chat_id=CENTER) is True
    m, _, body = net.posts[0]
    assert m == "deleteMessage"
    assert body == {"chat_id": CENTER, "message_id": 9}
    # بدونِ token/chat/id معتبر → False، صفر شبکه
    c2, net2 = _client(token="")
    assert c2.delete(9) is False and not net2.posts
    assert c.delete(None) is False
    # پاسخِ ok=False از API (مثلِ پیامِ >۴۸ساعته) → False، نه استثنا
    c3, _ = _client({"deleteMessage": {"ok": False, "error_code": 400}})
    assert c3.delete(9) is False
    # خطای شبکه → False، fail-soft
    c4, net4 = _client()
    net4.raise_on.add("deleteMessage")
    assert c4.delete(9) is False


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
    # پیش‌فرض (بدونِ scope) = بدنهٔ دیروز بایت‌به‌بایت — هیچ کلیدِ scope
    assert "scope" not in body, "بدونِ scope نباید کلیدِ scope برود"
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


def t_zz_diagnostics_no_token_leak():
    """diagnostics() اطلاعاتِ سیم‌کشی را بدونِ نشتِ token/chat-id برمی‌گرداند (فاز G)."""
    c, _ = _client()
    d = c.diagnostics()
    assert d["wired"] is True
    assert d["token_present"] is True
    assert d["token_mask"].endswith("…") or d["token_mask"] == "∅"
    assert TOKEN not in str(d), "token نباید در diagnostics نشت کند"
    assert d["owner_configured"] is True
    assert d["center_configured"] is True
    assert d["is_forum_center"] is True     # CENTER < -1000


def t_za_token_source_tracked():
    """token_source نشان می‌دهد توکن از کجا آمده (explicit/TG_CENTER/MAIN)."""
    # mute alerts برای این تست تا fallback-alert واقعی نرود
    from telegram_center import tg_api as _t
    orig_alert = _t._alert_soft
    _t._alert_soft = lambda *a, **k: None
    try:
        # explicit
        c1, _ = _client()
        assert c1._token_source == "explicit"
        # محیطی: TG_CENTER_BOT_TOKEN اگر ست باشد (در این تست env پاک شده، پس fallback)
        os.environ.pop("TG_CENTER_BOT_TOKEN", None)
        os.environ["TELEGRAM_BOT_TOKEN"] = TOKEN
        net = FakeNet()
        c2 = TgClient(owner_chat_id=OWNER, post_fn=net.post, get_fn=net.get)
        assert c2._token_source == "FALLBACK_TELEGRAM_BOT_TOKEN", c2._token_source
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    finally:
        _t._alert_soft = orig_alert


def t_y_429_retry_after_respected_then_succeeds():
    """آیتم ۵ِ TG-P2: پاسخِ ۴۲۹ با retry_after → صبر (با sleep تزریقی) + یک retry.

    تلگرام می‌گوید ``parameters.retry_after``؛ ما تا سقفِ امن احترام می‌گذاریم و یک
    تلاشِ مجدد می‌کنیم. این تست sleep واقعی نمی‌کند (``_sleep`` مونکی‌پچ می‌شود تا فقط
    مدت را ثبت کند). FakeNet دفعهٔ اول ۴۲۹ می‌دهد و دفعهٔ دوم موفق.

    جهش (حذفِ retry) ⇒ شمارشِ تماس‌ها ۱ می‌ماند و mid = None برمی‌گردد ⇒ قرمز."""
    slept = []
    ra_seen = []

    def fake_sleep(s):
        slept.append(s)

    # state برای برگرداندنِ ۴۲۹ در دفعهٔ اول، موفق در دفعهٔ دوم
    state = {"calls": 0}

    def post_429_then_ok(url, body, timeout_s=10.0):
        state["calls"] += 1
        if state["calls"] == 1:
            return {"ok": False, "error_code": 429,
                    "parameters": {"retry_after": 5},
                    "description": "Too Many Requests"}
        return {"ok": True, "result": {"message_id": 71}}

    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=post_429_then_ok, get_fn=FakeNet().get)
    c._sleep = fake_sleep
    mid = c.send("پیامِ پس ازِ rate-limit")
    assert mid == 71, f"باید بعد از retry موفق شود: {mid}"
    assert state["calls"] == 2, f"باید دقیقاً ۲ بار POST زده باشد: {state['calls']}"
    assert slept == [5.0], f"باید retry_after=5 را خوابیده باشد: {slept}"


def t_y2_429_retry_after_capped_at_safe_ceiling():
    """retry_after خطرناکِ بزرگ (مثلاً ۳۶۰۰s) باید تا سقفِ ۳۰s کلاه‌گذاری شود —
    هیچ retry_afterای کلاینت را ساعت‌ها نخواباند."""
    slept = []
    state = {"calls": 0}

    def post(url, body, timeout_s=10.0):
        state["calls"] += 1
        if state["calls"] == 1:
            return {"ok": False, "error_code": 429,
                    "parameters": {"retry_after": 3600}}
        return {"ok": True, "result": {"message_id": 1}}

    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=post, get_fn=FakeNet().get)
    c._sleep = slept.append
    c.send("x")
    assert slept == [30.0], f"retry_after=3600 باید به ۳۰ کلاه بخورد: {slept}"


def t_y3_429_then_second_429_is_failsoft_no_storm():
    """اگر retry هم ۴۲۹ بدهد → fail-soft (None) و فقط دو تماس (نه retry-storm)."""
    slept = []
    state = {"calls": 0}

    def post(url, body, timeout_s=10.0):
        state["calls"] += 1
        return {"ok": False, "error_code": 429,
                "parameters": {"retry_after": 1}}

    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=post, get_fn=FakeNet().get)
    c._sleep = slept.append
    assert c.send("x") is None
    assert state["calls"] == 2, f"نباید بیشتر از یک retry بزند: {state['calls']}"
    assert slept == [1.0], f"فقط یک sleep قبل از retry: {slept}"


def t_y4_non_429_failure_still_single_attempt():
    """خطای غیرِ ۴۲۹ (مثلاً ۴۰۰) همچنان یک تلاش، بی‌retry، fail-soft.
    این ضمانت می‌کند که retry فقط مخصوصِ ۴۲۹ است و رفتارِ بقیه دست‌نخورده است."""
    c, net = _client({"sendMessage": {"ok": False, "error_code": 400,
                                      "description": "Bad Request: chat not found"}})
    assert c.send("x") is None
    assert len(net.posts) == 1, "خطای ۴۰۰ نباید retry کند"


def t_y5_poll_updates_429_sleeps_before_returning_empty():
    """مسیرِ poll هم رویِ ۴۲۹ باید قبل از برگشتنِ [] صبر کند (نه spin).
    اگر خواب نکند، حلقهٔ poll فوراً دوباره getUpdates می‌زند و ۴۲۹ِ بیشتر می‌سازد."""
    slept = []

    class _Net429Get:
        def __init__(self):
            self.gets = []

        def post(self, url, body, timeout_s=10.0):
            return {"ok": True, "result": {}}

        def get(self, url, timeout_s):
            self.gets.append(url)
            return {"ok": False, "error_code": 429,
                    "parameters": {"retry_after": 3}}

    net = _Net429Get()
    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=net.post, get_fn=net.get)
    c._sleep = slept.append
    assert c.poll_updates(offset=0) == []
    assert slept == [3.0], f"poll باید retry_after=3 را خوابیده باشد: {slept}"


# ── فایلِ ورودی: getFile + دانلود (لِینِ ویس، منشور رأی ۹) ────────────────────
class FakeDl:
    """transportِ دانلودِ جعلی: (url, timeout_s, max_bytes) → bytes. صفر شبکه."""

    def __init__(self, blob=b"OggS-voice", raise_exc=None):
        self.calls = []
        self.blob = blob
        self.raise_exc = raise_exc

    def __call__(self, url, timeout_s, max_bytes):
        self.calls.append((url, timeout_s, max_bytes))
        if self.raise_exc is not None:
            raise self.raise_exc
        return self.blob


def _dest(name="voice.oga"):
    return str(Path(ENV["ops"]) / "state" / "tmp" / name)


def t_p1_get_file_returns_path_and_never_sends_a_receipt():
    """getFile یک **ورودی** است: هیچ ردیفِ رسیدِ ارسال نباید بنویسد."""
    c, net = _client({"getFile": {"ok": True, "result": {
        "file_id": "AF1", "file_path": "voice/file_9.oga", "file_size": 4096}}})
    seen = []
    from telegram_center import tg_api as _t
    orig = _t._send_log_record
    _t._send_log_record = lambda **kw: seen.append(kw)
    try:
        info = c.get_file("AF1")
    finally:
        _t._send_log_record = orig
    assert info["file_path"] == "voice/file_9.oga", info
    assert net.posts[0][0] == "getFile"
    assert net.posts[0][2] == {"file_id": "AF1"}
    assert seen == [], "دانلودِ ورودی نباید رسیدِ ارسال بنویسد (آلودنِ سنجه)"


def t_p2_get_file_guards_size_cap_and_bad_shapes():
    """>۲۵MB ⇒ None **قبل از** هر دانلودی؛ پاسخِ بی‌file_path هم ⇒ None."""
    big = tg_api._FILE_MAX_BYTES + 1
    c, _ = _client({"getFile": {"ok": True, "result": {
        "file_path": "voice/big.oga", "file_size": big}}})
    from telegram_center import tg_api as _t
    orig = _t._alert_soft
    _t._alert_soft = lambda *a, **k: None
    try:
        assert c.get_file("AF-big") is None, "فایلِ بزرگ‌تر از سقف باید رد شود"
    finally:
        _t._alert_soft = orig
    c2, _ = _client({"getFile": {"ok": True, "result": {"file_size": 10}}})
    assert c2.get_file("AF2") is None, "بدونِ file_path نتیجه بی‌معناست"
    c3, net3 = _client()
    assert c3.get_file("") is None and net3.posts == []   # id خالی ⇒ صفر شبکه
    c4, _ = _client({"getFile": {"ok": False, "error_code": 400}})
    assert c4.get_file("AF4") is None


def t_p3_download_writes_atomically_to_the_file_endpoint():
    dl = FakeDl(b"OggS-abc")
    net = FakeNet()
    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=net.post, get_fn=net.get, download_fn=dl)
    dest = _dest("ok.oga")
    assert c.download_file("voice/file_9.oga", dest) is True
    assert Path(dest).read_bytes() == b"OggS-abc"
    assert not Path(dest + ".part").exists(), "فایلِ نیم‌کاره جا ماند"
    url, timeout, cap = dl.calls[0]
    assert url == f"https://api.telegram.org/file/bot{TOKEN}/voice/file_9.oga"
    assert cap == tg_api._FILE_MAX_BYTES and timeout > 0


def t_p4_download_rejects_traversal_absolute_and_oversized_blobs():
    """`file_path` از بیرون می‌آید ⇒ گاردِ مسیر؛ و سقف روی بایت‌های واقعی."""
    dl = FakeDl()
    net = FakeNet()
    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=net.post, get_fn=net.get, download_fn=dl)
    for bad in ("../../etc/passwd", "/etc/passwd", "C:/Windows/x.dll",
                "voice/../../secret", "", "   "):
        assert c.download_file(bad, _dest("bad.oga")) is False, bad
    assert dl.calls == [], f"مسیرِ خطرناک نباید حتی دانلود شود: {dl.calls}"
    assert c.download_file("voice/ok.oga", "") is False
    # سقف روی بایتِ واقعی (transportِ تزریقی هم باید بخورد)
    huge = FakeDl(b"x" * (tg_api._FILE_MAX_BYTES + 1))
    c2 = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                  post_fn=net.post, get_fn=net.get, download_fn=huge)
    from telegram_center import tg_api as _t
    orig = _t._alert_soft
    _t._alert_soft = lambda *a, **k: None
    try:
        assert c2.download_file("voice/huge.oga", _dest("huge.oga")) is False
    finally:
        _t._alert_soft = orig
    assert not Path(_dest("huge.oga")).exists(), "فایلِ بزرگ نوشته شد"


def t_p5_download_is_failsoft_and_429_aware():
    """خطای transport ⇒ False (نه استثنا)؛ ۴۲۹ ⇒ همان یک retry، نه storm."""
    net = FakeNet()
    from telegram_center import tg_api as _t
    orig = _t._alert_soft
    _t._alert_soft = lambda *a, **k: None
    try:
        boom = FakeDl(raise_exc=OSError("net down (fake)"))
        c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                     post_fn=net.post, get_fn=net.get, download_fn=boom)
        assert c.download_file("voice/x.oga", _dest("x.oga")) is False
        assert len(boom.calls) == 1, "خطای غیر-۴۲۹ نباید retry کند"

        import io
        import json as _json
        import urllib.error
        state = {"n": 0}

        def dl_429_then_ok(url, timeout_s, max_bytes):
            state["n"] += 1
            if state["n"] == 1:
                body = _json.dumps({"ok": False, "error_code": 429,
                                    "parameters": {"retry_after": 2}}).encode()
                raise urllib.error.HTTPError("u", 429, "Too Many Requests", {},
                                             io.BytesIO(body))
            return b"OggS-after-429"

        slept = []
        c2 = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                      post_fn=net.post, get_fn=net.get, download_fn=dl_429_then_ok)
        c2._sleep = slept.append
        dest = _dest("retry.oga")
        assert c2.download_file("voice/r.oga", dest) is True
        assert state["n"] == 2 and slept == [2.0], (state, slept)
        assert Path(dest).read_bytes() == b"OggS-after-429"
    finally:
        _t._alert_soft = orig


def t_p6_empty_body_is_a_failure_not_an_empty_file():
    """پاسخِ خالی = شکست؛ نوشتنِ فایلِ صفربایتی یعنی «ویس داریم» ِ دروغ."""
    net = FakeNet()
    c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                 post_fn=net.post, get_fn=net.get, download_fn=FakeDl(b""))
    dest = _dest("empty.oga")
    assert c.download_file("voice/e.oga", dest) is False
    assert not Path(dest).exists(), "فایلِ صفربایتی ساخته شد"


def t_p7_fetch_file_composes_both_steps_and_unwired_is_zero_network():
    c, net = _client({"getFile": {"ok": True, "result": {
        "file_path": "voice/f.oga", "file_size": 100}}})
    dl = FakeDl(b"OggS-fetch")
    c._download = dl
    dest = _dest("fetch.oga")
    assert c.fetch_file("AF9", dest) is True
    assert Path(dest).read_bytes() == b"OggS-fetch"
    # getFile شکست ⇒ هیچ دانلودی
    c2, _ = _client({"getFile": {"ok": False}})
    dl2 = FakeDl()
    c2._download = dl2
    assert c2.fetch_file("AFx", _dest("no.oga")) is False and dl2.calls == []
    # not wired ⇒ صفرِ مطلقِ شبکه
    net3 = FakeNet()
    dl3 = FakeDl()
    c3 = TgClient(post_fn=net3.post, get_fn=net3.get, download_fn=dl3)
    assert c3.get_file("AF1") is None
    assert c3.download_file("voice/x.oga", _dest("nw.oga")) is False
    assert c3.fetch_file("AF1", _dest("nw.oga")) is False
    assert net3.posts == [] and dl3.calls == []


def t_p8_default_file_transport_blocks_foreign_hosts_and_caps_bytes():
    """transportِ پیش‌فرضِ دانلود: فقط endpointِ فایلِ تلگرام، و سقفِ بایت."""
    for bad in ("https://evil.example.com/file/bot1/x.oga",
                "https://api.telegram.org/bot123/getMe",           # نه /file/
                "http://api.telegram.org.evil.tld/file/botx/a"):
        try:
            tg_api._url_bytes_get(bad, 1.0, 10)
            raised = False
        except ValueError:
            raised = True
        assert raised, bad


def t_p9_token_never_appears_in_any_alert_from_the_file_path():
    """URLِ فایل token دارد ⇒ هیچ هشدار/خطایی نباید آن را echo کند."""
    alerts = []
    from telegram_center import tg_api as _t
    orig = _t._alert_soft
    _t._alert_soft = alerts.append
    try:
        net = FakeNet()
        c = TgClient(token=TOKEN, owner_chat_id=OWNER, center_chat_id=CENTER,
                     post_fn=net.post, get_fn=net.get,
                     download_fn=FakeDl(raise_exc=OSError("boom")))
        c._last_alert.clear()
        assert c.download_file("voice/x.oga", _dest("t.oga")) is False
        cbig, _ = _client({"getFile": {"ok": True, "result": {
            "file_path": "v.oga", "file_size": tg_api._FILE_MAX_BYTES + 1}}})
        cbig._last_alert.clear()
        assert cbig.get_file("AF") is None
    finally:
        _t._alert_soft = orig
    assert alerts, "شکستِ دانلود باید دیده شود (سکوت ممنوع)"
    dump = " ".join(str(a) for a in alerts)
    assert TOKEN not in dump and "api.telegram.org" not in dump, dump


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_api: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
