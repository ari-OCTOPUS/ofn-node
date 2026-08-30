"""test_telegram_poll_e2e.py — جلسه ۴۶: مسیرِ کاملِ دکمه (getUpdates → dispatch → پاسخ).

تستِ unitِ dispatch سبز بود ولی معمای «نادیده» در runtime ماند. این تست حلقهٔ واقعیِ
poll_once را با httpِ تزریقی می‌راند و اثبات می‌کند:
  الف) دکمهٔ منوی معتبر → answerCallbackQuery("✅") + یک sendMessageِ نو با محتوای تب.
  ب) callbackِ بیگانه/قدیمی (نه menu:/app:/rfc:/card:/act:/pg:) → toastِ «نادیده».
      (این دقیقاً علامتی است که مالک دید → پس منبعش کدِ بیگانه/pollerِ دوم است.)
  ج) chat_idِ غیرمالک → drop کامل (نه پاسخ، offset جلو).
  د) نبضِ poll در state/pulse/telegram-poll.json نوشته می‌شود (رصدِ حیاتِ thread).
  ه) 409 Conflict → هشدارِ throttled (تشخیصِ pollerِ دوم).
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-poll-e2e")

import approval_channel as ac  # noqa: E402
import opslib                  # noqa: E402

STATE = Path(ENV["ops"]) / "state"
OWNER = 4242


class QueuedHTTP:
    """getUpdates یک‌بار batch را می‌دهد، بعد خالی؛ postها ضبط می‌شوند."""

    def __init__(self, updates):
        self._batches = [updates, []]
        self.posts: list[tuple[str, dict]] = []
        self.get_calls = 0

    def get(self, url, timeout):
        self.get_calls += 1
        batch = self._batches.pop(0) if self._batches else []
        return {"ok": True, "result": batch}

    def post(self, url, body, timeout_s=10.0):
        self.posts.append((url.split("/")[-1].split("?")[0], body))
        return {"ok": True}

    def sends(self):
        return [b for m, b in self.posts if "sendMessage" in m]

    def answers(self):
        return [b for m, b in self.posts if "answerCallbackQuery" in m]


def _cbq(data, uid=1, chat=OWNER):
    # واقع‌گرایانه: پیامِ ضمیمهٔ دکمه، متنِ خودش (بدنهٔ منو) را دارد — دقیقاً مثلِ تلگرامِ
    # واقعی. باگِ جلسه ۴۶: کد این متن را به‌جای callback data می‌خواند → «نادیده».
    return {"update_id": uid,
            "callback_query": {"id": f"cbq{uid}", "data": data,
                               "from": {"id": chat},
                               "message": {"chat": {"id": chat}, "date": 0,
                                           "text": "🐙 اختاپوس — منوی اصلی\nحالت: STEADY"}}}


def _channel(updates):
    fh = QueuedHTTP(updates)
    ch = ac.TelegramApprovalChannel(
        token="99:zz", owner_chat_id=OWNER, state_dir=str(STATE),
        http_get=fh.get, http_post=fh.post, longpoll_timeout=0)
    return ch, fh


def t_a_valid_menu_button_opens_new_message():
    """دکمهٔ منوی معتبر → answer «✅» + پیامِ نو با کیبورد (نه toastِ نادیده).
    رگرسیونِ باگِ جلسه ۴۶: callback.message.text نباید callback data را سایه بیندازد."""
    ch, fh = _channel([_cbq("menu:overview")])
    ch.poll_once()
    ans = fh.answers()
    assert ans and "✅" in json.dumps(ans[0], ensure_ascii=False), ans
    assert "نادیده" not in json.dumps(ans, ensure_ascii=False)   # ضدِ باگِ متنِ منو
    sends = fh.sends()
    assert sends, "دکمهٔ معتبر باید پیامِ نو بفرستد"
    assert sends[0].get("reply_markup"), "پیامِ تب باید کیبورد داشته باشد"
    assert "نادیده" not in json.dumps(sends, ensure_ascii=False)


def t_b_now_and_more_and_cortex_open():
    """سه دکمهٔ نوِ ADHD (now/more/cortex) همه پیامِ نو می‌دهند، نه نادیده."""
    for data in ("menu:now", "menu:more", "menu:cortex", "menu:status"):
        ch, fh = _channel([_cbq(data)])
        ch.poll_once()
        assert fh.sends(), f"{data} پیام نداد"
        blob = json.dumps(fh.posts, ensure_ascii=False)
        assert "نادیده" not in blob, f"{data} → نادیده!"


def t_c_foreign_callback_yields_nadide_toast():
    """callbackِ بیگانه/قدیمی → toastِ «نادیده» (بازتولیدِ علامتِ مالک).
    این اثبات می‌کند علامت فقط با فرمتِ ناشناخته/pollerِ بیگانه رخ می‌دهد."""
    for foreign in ("nav:overview", "tab:money", "cb:home", "menu"):
        ch, fh = _channel([_cbq(foreign)])
        ch.poll_once()
        assert not fh.sends(), f"{foreign} نباید پیامِ نو بدهد"
        ans = json.dumps(fh.answers(), ensure_ascii=False)
        assert "نادیده" in ans, f"{foreign} باید toastِ نادیده بدهد، شد: {ans}"


def t_d_nonowner_dropped_silently():
    """chat_idِ غیرمالک → هیچ پاسخ، ولی offset جلو (ضدِ لوپ)."""
    ch, fh = _channel([_cbq("menu:overview", uid=7, chat=9999)])
    ch.poll_once()
    assert not fh.sends() and not fh.answers()
    assert ch._offset == 8


def t_e_poll_heartbeat_written():
    """نبضِ حیاتِ thread: state/pulse/telegram-poll.json با batch نوشته می‌شود."""
    ch, fh = _channel([_cbq("menu:now")])
    ch.poll_once()
    hb = STATE / "pulse" / "telegram-poll.json"
    assert hb.exists(), "نبضِ poll نوشته نشد"
    d = json.loads(hb.read_text("utf-8"))
    assert d["batch"] == 1 and "ts" in d


def t_g_webhook_diagnostic_detects_competitor():
    """getWebhookInfo: webhookِ رقیب ست → هشدار (علتِ محتملِ نادیدهٔ باتِ مشترک)؛
    TELEGRAM_TAKE_OVER_WEBHOOK → deleteWebhook. بدونِ webhook → بی‌صدا."""
    # حالت ۱: webhook ست است
    ch, fh = _channel([])

    def _get_hook(url, timeout):
        if "getWebhookInfo" in url:
            return {"ok": True, "result": {"url": "https://control-brain.example/hook",
                                           "pending_update_count": 3}}
        return {"ok": True, "result": []}
    ch._http_get = _get_hook
    alerts = opslib.ALERTS_MD
    before = alerts.read_text("utf-8") if alerts.exists() else ""
    r = ch._diagnose_webhook(delete=False)
    assert r["webhook"] is True and r["deleted"] is False
    after = alerts.read_text("utf-8")
    assert "webhook" in after and len(after) > len(before)
    assert "control-brain.example" not in after   # url هرگز echo نشود
    # حالت ۲: take-over → deleteWebhook POST زده می‌شود
    ch2, fh2 = _channel([])
    ch2._http_get = _get_hook
    r2 = ch2._diagnose_webhook(delete=True)
    assert r2["deleted"] is True
    assert any("deleteWebhook" in m for m, _ in fh2.posts)
    # حالت ۳: بدونِ webhook → بی‌صدا
    ch3, fh3 = _channel([])
    ch3._http_get = lambda url, t: {"ok": True, "result": {}}
    assert ch3._diagnose_webhook()["webhook"] is False


def t_f_409_conflict_alerts_once():
    """409 (pollerِ دوم) → هشدار؛ throttle: دومی در همان ساعت هشدار نمی‌دهد."""
    ch, fh = _channel([])

    def _get409(url, timeout):
        return {"ok": False, "error_code": 409, "description": "Conflict"}
    ch._http_get = _get409
    alerts = opslib.ALERTS_MD
    before = alerts.read_text("utf-8") if alerts.exists() else ""
    ch.poll_once()
    after1 = alerts.read_text("utf-8")
    assert "409" in after1 and len(after1) > len(before), "409 باید هشدار بدهد"
    ch.poll_once()   # بلافاصله دوباره — throttle
    after2 = alerts.read_text("utf-8")
    assert after2.count("getUpdates 409") == after1.count("getUpdates 409"), "throttle نشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_telegram_poll_e2e: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
