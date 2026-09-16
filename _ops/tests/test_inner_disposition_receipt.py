#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_inner_disposition_receipt.py — باتِ درونی هم «چه شد» را کنارِ «رسید» می‌نویسد (OP-2، ۰۹-۱۱).

تا امروز فقط مرکز `_log_disposition` داشت؛ کلیکِ مالک 732409706 روی باتِ درونی از INFERRED
بالاتر نمی‌رفت چون مسیرِ موفقِ ACK هیچ ردیفی نمی‌نوشت. حالا هر update یک ردیفِ
`kind=disposition` با همان `update_id` می‌گیرد: answered | sent | unhandled | silent | error |
dropped-allowlist. «unhandled» همان دکمهٔ مرده است — دیگر بی‌صدا نمی‌ماند.
transport جعلی، صفر شبکه، صفر راز، فقط sandbox.
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

ENV = harness.setup("tg-inner-disposition")
os.environ["OCTOPUS_TG_SEND_LOG"] = "1"

import approval_channel as ac  # noqa: E402
import opslib                  # noqa: E402
import tg_receipts             # noqa: E402

STATE = Path(ENV["ops"]) / "state"
OWNER = 4242
MIRROR_FLAG = "OCTOPUS_TG_MIRROR"


class QueuedHTTP:
    def __init__(self, updates):
        self._batches = [list(updates), []]
        self.posts = []

    def get(self, url, timeout):
        batch = self._batches.pop(0) if self._batches else []
        return {"ok": True, "result": batch}

    def post(self, url, body, timeout_s=10.0):
        self.posts.append((url.split("/")[-1].split("?")[0], body))
        return {"ok": True, "result": {"message_id": 1}}


def _cbq(data, uid, chat=OWNER):
    return {"update_id": uid,
            "callback_query": {"id": f"cbq{uid}", "data": data, "from": {"id": chat},
                               "message": {"chat": {"id": chat, "type": "private"}, "date": 0,
                                           "text": "card body"}}}


def _msg(text, uid, chat=OWNER):
    return {"update_id": uid, "message": {"chat": {"id": chat, "type": "private"},
                                          "from": {"id": chat}, "text": text, "date": 0}}


def _channel(updates, tag):
    fh = QueuedHTTP(updates)
    ch = ac.TelegramApprovalChannel(token="TEST-FAKE-TOKEN-NOT-REAL", owner_chat_id=OWNER,
                                    state_dir=str(STATE / f"ch-{tag}"),
                                    http_get=fh.get, http_post=fh.post, longpoll_timeout=0)
    return ch, fh


def _rows():
    p = STATE / "telegram" / "inbound-log.jsonl"
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()] if p.exists() else []


def _disp(uid):
    return [r for r in _rows() if r.get("kind") == "disposition" and r.get("update_id") == uid]


def _arrival(uid):
    return [r for r in _rows() if r.get("kind") != "disposition" and r.get("update_id") == uid]


def t_a_mirror_click_with_flag_on_is_receipted_as_sent_with_ack_and_send_ok():
    os.environ[MIRROR_FLAG] = "1"
    try:
        ch, fh = _channel([_cbq("mr:know", 900001)], "a")
        ch.poll_once()
    finally:
        os.environ.pop(MIRROR_FLAG, None)
    assert len(_arrival(900001)) == 1 and len(_disp(900001)) == 1, _rows()[-3:]
    d = _disp(900001)[0]
    assert d["bot"] == "inner" and d["outcome"] == "sent" and d["reason"] == "mr", d
    assert d["ack_ok"] is True and d["send_ok"] is True, d
    assert "text" not in d and "data" not in d


def t_b_a_verb_nobody_handles_is_receipted_as_unhandled_not_silently_answered():
    """همان دکمهٔ مرده — از این پس در لاگ اسمش «unhandled» است."""
    ch, fh = _channel([_cbq("zz:qq", 900002)], "b")
    ch.poll_once()
    d = _disp(900002)
    assert len(d) == 1 and d[0]["outcome"] == "unhandled" and d[0]["reason"] == "zz", d
    assert d[0]["ack_ok"] is True and "send_ok" not in d[0], d[0]


def t_c_a_toast_only_handler_is_answered_and_a_menu_page_is_sent():
    os.environ.pop(MIRROR_FLAG, None)
    ch, fh = _channel([_cbq("mr:know", 900003), _cbq("menu:overview", 900004)], "c")
    ch.poll_once()
    assert _disp(900003)[0]["outcome"] == "answered", _disp(900003)     # فلگ خاموش ⇒ toastِ توضیح‌دار
    assert _disp(900004)[0]["outcome"] == "sent" and _disp(900004)[0]["send_ok"] is True


def t_d_non_owner_is_receipted_as_dropped_allowlist_with_no_reply():
    ch, fh = _channel([_cbq("menu:overview", 900005, chat=9999)], "d")
    ch.poll_once()
    assert not fh.posts
    d = _disp(900005)
    assert len(d) == 1 and d[0]["outcome"] == "dropped-allowlist", d


def t_e_a_handler_exception_is_receipted_as_error_with_the_type_name_only():
    ch, fh = _channel([_cbq("mr:know", 900006)], "e")

    def _boom(*a, **k):
        raise RuntimeError("fixture: secret-looking 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
    ch.dispatch_callback = _boom
    ch.poll_once()
    d = _disp(900006)
    assert len(d) == 1 and d[0]["outcome"] == "error" and d[0]["detail"] == "RuntimeError", d
    assert "1234567890" not in json.dumps(d[0]), ("پیامِ استثنا نباید ثبت شود", d[0])
    assert ch._offset == 900007


def t_f_text_messages_get_sent_or_silent_and_never_store_the_text():
    ch, fh = _channel([_msg("/queue", 900007), _msg("متنِ آزادِ بی‌جواب؟", 900008)], "f")
    ch.poll_once()
    for uid in (900007, 900008):
        d = _disp(uid)
        assert len(d) == 1 and d[0]["outcome"] in ("sent", "silent") and d[0]["reason"] == "text", d
        assert "آزاد" not in json.dumps(d[0], ensure_ascii=False)
    outcomes = {900007: _disp(900007)[0]["outcome"], 900008: _disp(900008)[0]["outcome"]}
    assert (outcomes[900007] == "sent") == bool([b for m, b in fh.posts if "sendMessage" in m][:1]), outcomes


def t_g_tg_receipts_joins_arrival_and_disposition_on_the_same_update_id():
    out = tg_receipts.collect(inbound=_rows(), sends=[])
    blob = json.dumps(out, ensure_ascii=False, default=str)
    assert "900001" in blob and "900002" in blob, blob[:300]


def t_h_sandbox_only():
    real = str(harness.REAL_VAULT).lower()
    assert real not in str(STATE).lower() and real not in str(opslib.STATE_DIR).lower()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_inner_disposition_receipt: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
