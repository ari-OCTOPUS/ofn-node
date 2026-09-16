#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_inner_mirror_callback.py — کلیکِ واقعیِ مالک روی «🪞 آینه» نباید «نادیده» بگیرد.

رسیدِ زنده (۲۰۲۶-۰۹-۱۰، لِین CORTEX-CONNECT-ALL-20260910):
    inbound-log: ts=20:28:31 bot=inner update_id=732409706 kind=callback_query
                 chars=7 from_owner=true
    initiative.jsonl: کارتِ «سوال» id=8186ef67275e در 20:22:06 → ارسالِ inner در 20:22:08
    telegram_offset.json: 732409707 در 20:28:32.976 (دورِ poll تا انتها رفت)
    هیچ فایلِ state ِ دیگری در آن پنجره عوض نشد؛ هیچ هشدارِ dispatch/ACK.

کارتِ initiative دو دکمه دارد: `iv:q` (۴ کاراکتر) و `mr:know` (۷ کاراکتر). تنها
callbackِ ۷کاراکتری‌ای که از باتِ درونی می‌رود همین است. `dispatch_callback` ِ
approval_channel شاخهٔ `mr` نداشت → «نادیده». همین شکاف از ۲۰۲۶-۰۸-۰۶ در
KNOWN_OPEN_GAPS ِ test_tg_callback_emitter_parity.py ثبت و **معاف** شده بود —
یعنی ۳۵ روز دکمه‌ای که مالک می‌زد جواب «نادیده» می‌گرفت و CI سبز بود.

این فایل مرزِ واقعی را می‌سنجد، نه متن را: getUpdates ِ تزریقی → poll_once →
ردیفِ ورودی → انتخابِ handler → answerCallbackQuery → sendMessage (در صورتِ
کارت) → offset. شبکه صفر، راز صفر، مقدارِ ساختگیِ برچسب‌خورده.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness  # noqa: E402

ENV = harness.setup("tg-inner-mirror")
os.environ["OCTOPUS_TG_SEND_LOG"] = "1"      # رسیدِ ارسال باید نوشته شود (sandbox)

import approval_channel as ac  # noqa: E402
import opslib                  # noqa: E402
import tg_send_log             # noqa: E402

STATE = Path(ENV["ops"]) / "state"
OWNER = 4242
CLICK_DATA = "mr:know"          # همان ۷ کاراکتر
MIRROR_FLAG = "OCTOPUS_TG_MIRROR"
NADIDEH = "نادیده"


class QueuedHTTP:
    """getUpdates یک‌بار batch را می‌دهد، بعد خالی؛ postها ضبط می‌شوند. صفر شبکه."""

    def __init__(self, updates):
        self._batches = [list(updates), []]
        self.posts: list[tuple[str, dict]] = []

    def get(self, url, timeout):
        batch = self._batches.pop(0) if self._batches else []
        return {"ok": True, "result": batch}

    def post(self, url, body, timeout_s=10.0):
        self.posts.append((url.split("/")[-1].split("?")[0], body))
        return {"ok": True, "result": {"message_id": 1}}

    def sends(self):
        return [b for m, b in self.posts if "sendMessage" in m]

    def answers(self):
        return [b for m, b in self.posts if "answerCallbackQuery" in m]


def _cbq(data, uid=732409706, chat=OWNER):
    """شکلِ واقعیِ کلیک: پیامِ ضمیمه متنِ کارت را دارد؛ کنشگر `from` ِ callback است."""
    return {"update_id": uid,
            "callback_query": {"id": f"cbq{uid}", "data": data,
                               "from": {"id": chat},
                               "message": {"chat": {"id": chat, "type": "private"},
                                           "date": 0,
                                           "text": "❓ یک سؤال از تو دارم\n\n(بدنهٔ کارت)"}}}


def _channel(updates, tag="default"):
    """state_dir per-test: offset ِ ذخیره‌شده (telegram_offset.json) بین تست‌ها نشت
    نکند — وگرنه uid ِ کوچک‌تر از offsetِ قبلی «قدیمی» شمرده می‌شود (آرتیفکتِ
    فیکسچر، نه رفتارِ تولیدی)."""
    fh = QueuedHTTP(updates)
    ch = ac.TelegramApprovalChannel(
        token="TEST-FAKE-TOKEN-NOT-REAL", owner_chat_id=OWNER,
        state_dir=str(STATE / f"ch-{tag}"),
        http_get=fh.get, http_post=fh.post, longpoll_timeout=0)
    return ch, fh


def _inbound_rows():
    p = STATE / "telegram" / "inbound-log.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _send_rows():
    p = STATE / "tg-send-log.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _blob(x) -> str:
    return json.dumps(x, ensure_ascii=False)


# ── ۱. شکلِ دقیقِ رسیدِ کلیکِ مالک، بازتولیدشده ───────────────────────────────
def t_a_the_owner_click_shape_is_received_and_logged_as_inner():
    """ردیفِ ورودی باید دقیقاً همان شکلِ ردیفِ 732409706 را داشته باشد."""
    os.environ.pop(MIRROR_FLAG, None)
    ch, fh = _channel(tag='a', updates=[_cbq(CLICK_DATA)])
    n0 = len(_inbound_rows())
    ch.poll_once()
    new = _inbound_rows()[n0:]
    rows = [x for x in new if x.get("kind") != "disposition"]
    assert len(rows) == 1, rows
    r = rows[0]
    # OP-2 (۰۹-۱۱): کنارِ ردیفِ «رسید»، ردیفِ «چه شد» با همان update_id
    disp = [x for x in new if x.get("kind") == "disposition"]
    assert len(disp) == 1 and disp[0]["update_id"] == 732409706 and disp[0]["outcome"] == "answered", disp
    assert r["bot"] == "inner" and r["kind"] == "callback_query", r
    assert r["update_id"] == 732409706 and r["chars"] == len(CLICK_DATA) == 7, r
    assert r["from_owner"] is True and r["chat_kind"] == "private", r
    assert "text" not in r and "data" not in r, ("§۱۰: متنِ callback ذخیره نمی‌شود", r)
    assert ch._offset == 732409707, ("offset باید uid+1 شود (رسیدِ زنده: 732409707)", ch._offset)


# ── ۲. با فلگِ خاموش: توضیح، نه «نادیده» ───────────────────────────────────
def t_b_mr_know_with_mirror_off_is_answered_with_an_explanation_not_nadideh():
    """قبل از وصله: toast «نادیده». بعد: toastِ توضیح‌دار (اتاقِ آینه خاموش است).
    هر دو یک answerCallbackQuery می‌زنند؛ فرق در **معنا** است — مالک باید بفهمد چرا."""
    os.environ.pop(MIRROR_FLAG, None)
    ch, fh = _channel(tag='b', updates=[_cbq(CLICK_DATA)])
    ch.poll_once()
    ans = fh.answers()
    assert len(ans) == 1, ("دقیقاً یک answerCallbackQuery", ans)
    assert ans[0].get("callback_query_id") == "cbq732409706", ans
    text = str(ans[0].get("text", ""))
    assert NADIDEH not in text, ("کلیکِ مالک روی دکمهٔ خودِ بات نباید «نادیده» بگیرد", text)
    assert "آینه" in text, ("toast باید بگوید مسئله اتاقِ آینه است", text)
    assert not fh.sends(), "با فلگِ خاموش پیامِ نو نمی‌رود (فقط toast)"


# ── ۳. با فلگِ روشن: کارتِ «فهمِ من از خودم» به‌عنوانِ پیامِ نو + رسیدِ همبسته ──
def t_c_mr_know_with_mirror_on_sends_the_know_card_and_binds_the_receipt():
    """dict → answer «✅» + sendMessage با محتوایِ know_card ($0، بدونِ مدل).
    و رسیدِ ارسال باید با همان update_id مهر بخورد — تا امروز در لاگِ زندهٔ ۴۸ساعته
    **صفر** ردیفِ inner با update_id وجود داشت؛ این‌جا ثابت می‌شود مکانیزم برای
    پاسخِ callback کار می‌کند."""
    os.environ[MIRROR_FLAG] = "1"
    try:
        ch, fh = _channel(tag='c', updates=[_cbq(CLICK_DATA)])
        s0 = len(_send_rows())
        ch.poll_once()
        ans = fh.answers()
        assert ans and "✅" in str(ans[0].get("text", "")), ans
        sends = fh.sends()
        assert len(sends) == 1, ("کارت باید یک پیامِ نو باشد", sends)
        body = str(sends[0].get("text", ""))
        assert "فهمِ من از خودم" in body, body
        assert NADIDEH not in _blob(fh.posts)
        assert sends[0].get("chat_id") == OWNER, sends[0]
        new = _send_rows()[s0:]
        assert new, "رسیدِ ارسال نوشته نشد (OCTOPUS_TG_SEND_LOG=1 در sandbox)"
        assert new[-1].get("bot_role") == "inner", new[-1]
        assert new[-1].get("update_id") == 732409706, (
            "پاسخِ callback باید به همان update مهر بخورد", new[-1])
        assert "text" not in new[-1] and new[-1].get("sha"), ("فقط hash، نه متن", new[-1])
        assert tg_send_log.current_update() is None, "برچسب بعد از دور آزاد نشد"
    finally:
        os.environ.pop(MIRROR_FLAG, None)


def t_d_mr_corr_with_mirror_on_sends_the_corrections_card():
    os.environ[MIRROR_FLAG] = "1"
    try:
        ch, fh = _channel(tag='d', updates=[_cbq("mr:corr", uid=732409708)])
        ch.poll_once()
        sends = fh.sends()
        assert len(sends) == 1, sends
        assert "تصحیح" in str(sends[0].get("text", "")), sends[0]
        assert NADIDEH not in _blob(fh.posts)
    finally:
        os.environ.pop(MIRROR_FLAG, None)


# ── ۴. مرزِ خطا: handler می‌ترکد → حلقه نمی‌میرد، دکمه بی‌جواب نمی‌ماند، offset جلو ──
def t_e_a_broken_mirror_handler_is_fail_soft_and_still_answers():
    os.environ[MIRROR_FLAG] = "1"
    import mirror_room as _mr
    orig = _mr.know_card

    def _boom():
        raise RuntimeError("fixture: mirror exploded")
    _mr.know_card = _boom
    try:
        ch, fh = _channel(tag='e', updates=[_cbq(CLICK_DATA, uid=732409709)])
        ch.poll_once()                      # نباید استثنا بیرون بدهد
        ans = fh.answers()
        assert len(ans) == 1, ("حتی در خطا، spinner باید dismiss شود", ans)
        assert NADIDEH not in str(ans[0].get("text", "")), ans
        assert ch._offset == 732409710, ch._offset
    finally:
        _mr.know_card = orig
        os.environ.pop(MIRROR_FLAG, None)


def t_f_an_unhandled_dispatch_error_is_alerted_and_the_batch_continues():
    """مرزِ بیرونی‌ترِ poll_once: استثنایِ خودِ dispatch → هشدار (نه سکوت)، updateِ
    بعدیِ همان batch پردازش می‌شود، offset تا انتها می‌رود."""
    ch, fh = _channel(tag='f', updates=[_cbq(CLICK_DATA, uid=1001), _cbq("menu:overview", uid=1002)])
    real = ch.dispatch_callback
    calls = []

    def _dispatch(data, *a, **k):
        calls.append(data)
        if data == CLICK_DATA:
            raise RuntimeError("fixture: dispatch exploded")
        return real(data, *a, **k)
    ch.dispatch_callback = _dispatch
    alerts = opslib.ALERTS_MD
    before = alerts.read_text("utf-8") if alerts.exists() else ""
    ch.poll_once()
    after = alerts.read_text("utf-8") if alerts.exists() else ""
    assert "T-8 dispatch error" in after[len(before):], "خطای dispatch باید هشدار بدهد"
    assert calls == [CLICK_DATA, "menu:overview"], calls
    assert fh.sends(), "updateِ دوم باید پردازش شده باشد"
    assert ch._offset == 1003, ch._offset


# ── ۵. پاریتیِ رفتاری برای دقیقاً همان کارتی که مالک رویش کلیک کرد ──────────
def t_g_every_button_on_the_initiative_card_has_a_live_inner_handler():
    """نه اسکنِ نحوی — dispatchِ واقعی روی کانالِ درونی برای هر دکمهٔ initiative.card()."""
    import initiative as _iv
    _t, kb = _iv.card({"kind": "سوال", "text": "fixture-question", "why": ""})
    datas = [b["callback_data"] for row in kb for b in row if "callback_data" in b]
    assert CLICK_DATA in datas, ("کارتِ initiative دیگر mr:know ندارد؟ تست بی‌مصرف شد", datas)
    os.environ[MIRROR_FLAG] = "1"
    try:
        ch, _ = _channel(tag='g', updates=[])
        dead = {}
        for d in datas:
            r = ch.dispatch_callback(d, from_id=OWNER, external=True)
            txt = r.get("text", "") if isinstance(r, dict) else str(r)
            if NADIDEH in txt or not txt.strip():
                dead[d] = txt
        assert not dead, ("دکمهٔ مرده روی باتِ درونی", dead)
    finally:
        os.environ.pop(MIRROR_FLAG, None)


# ── ۶. این تست فقط sandbox می‌نویسد ───────────────────────────────────────────
def t_h_this_test_never_touches_the_real_vault_state():
    real = str(harness.REAL_VAULT).lower()
    assert real not in str(STATE).lower(), STATE
    assert real not in str(opslib.STATE_DIR).lower(), opslib.STATE_DIR


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_inner_mirror_callback: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
