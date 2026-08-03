#!/usr/bin/env python3
"""G3 arc — کارتِ پیشنهاد → دکمهٔ مالک → outcome → متریک ($0 آفلاین، صفر شبکه).

قوسی که تا ۲۰۲۶-۰۷-۱۷ بریده بود: router کارت می‌فرستاد، مالک جواب می‌داد، و جواب
هیچ‌جا نمی‌نشست — پس `proposal_outcomes` و `proposal_value_aud` (۲ از ۶ محورِ movedِ
goal_directed) ساختاراً همیشه صفر بودند.

این سوئیت سه چیز را اثبات می‌کند:
(الف) فلگ خاموش → رفتار دقیقاً مثل دیروز (بدونِ دکمه، بدونِ قلاب).
(ب) فلگ روشن → دکمه می‌چسبد، تپِ مالک متریک می‌سازد، و قوس تا measure بسته می‌شود.
(ج) مرزها: هیچ approve/settle، tokenِ کهنه/جعلی بی‌اثر، دو-تپ متریک را دوبرابر نمی‌کند.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("proposal-buttons")
# ⚠️ تا ۲۰۲۶-۰۸-۰۳ این `harness.REAL_VAULT` بود، پس `live_loop` از درختِ
# **زنده** import می‌شد و روی `state/channel-status.json` ِ زنده می‌نوشت.
# `SELF_OPS` قراردادِ خودِ harness است: کدِ زیرِ آزمون = همین درخت.
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_loop import LiveLoop, _InMemoryBus  # noqa: E402
from leg import Leg, TaskPacket  # noqa: E402

_FLAG = "OCTOPUS_WIRE_PROPOSAL_BUTTONS"


class _FakeChannel:
    """کانالی که reply_markup می‌فهمد (مثل approval_channel.send_text واقعی)."""

    def __init__(self):
        self.sent = []

    def send_text(self, text, reply_markup=None):
        self.sent.append({"text": text, "reply_markup": reply_markup})
        return True


class _LegacyChannel:
    """کانالِ قدیمی که فقط متن می‌گیرد — نباید router را بکشد (عقب‌روِ امن)."""

    def __init__(self):
        self.sent = []

    def send_text(self, text):
        self.sent.append(text)
        return True


def _fake_leg():
    packet = TaskPacket(leg_id="test-leg", organ="TEST",
                        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
                        tools=("draft",), budget_aud=0.0)
    return Leg(packet, organ_table={"TEST": {"floor": 0}})


def _loop_with_proposal(chan=None, amount=500):
    leg = _fake_leg()
    p = leg.emit_proposal("draft_quote", {"scope": "paint room", "expected_aud": amount})
    loop = LiveLoop(bus=_InMemoryBus(), approval_channel=chan, leg=leg)
    return loop, p


# ════════════════════════════════════════════════════════════════════════════════
# (الف) فلگ خاموش = رفتارِ دیروز
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_off_no_keyboard():
    """پیش‌فرض خاموش → هیچ دکمه‌ای، هیچ نگاشتی. byte-identical با قبل."""
    os.environ.pop(_FLAG, None)
    chan = _FakeChannel()
    loop, _ = _loop_with_proposal(chan)
    r = loop.route_leg_proposals(deliver=True)
    assert r["delivered"] == 1 and len(chan.sent) == 1
    assert chan.sent[0]["reply_markup"] is None, "فلگ خاموش نباید کیبورد بفرستد"
    assert loop._proposal_cb == {}, "فلگ خاموش نباید token ثبت کند"
    assert r["proposals"][0].get("buttons") is not True


def t_flag_off_hook_not_wired():
    """wire_proposal_buttons با فلگ خاموش → False و کانال دست‌نخورده."""
    import wiring
    os.environ.pop(_FLAG, None)
    chan = _FakeChannel()
    loop, _ = _loop_with_proposal(chan)
    assert wiring.wire_proposal_buttons(channel=chan, live_loop=loop) is False
    assert getattr(chan, "_proposal_hook", None) is None


# ════════════════════════════════════════════════════════════════════════════════
# (ب) فلگ روشن = قوس بسته
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_on_attaches_keyboard():
    """فلگ روشن → سه دکمه با قراردادِ 'prop:<verb>:<token>' و زیرِ سقفِ ۶۴ بایت."""
    os.environ[_FLAG] = "1"
    chan = _FakeChannel()
    loop, _ = _loop_with_proposal(chan)
    r = loop.route_leg_proposals(deliver=True)
    kb = chan.sent[0]["reply_markup"]
    assert kb is not None, "فلگ روشن باید کیبورد بچسباند"
    row = kb["inline_keyboard"][0]
    assert [b["callback_data"].split(":")[1] for b in row] == ["ok", "no", "later"]
    for b in row:
        cd = b["callback_data"]
        assert cd.startswith("prop:"), cd
        assert len(cd.encode("utf-8")) <= 64, f"سقفِ callback_data تلگرام: {cd}"
    assert r["proposals"][0]["buttons"] is True


def t_token_tap_records_outcome_and_value():
    """تپِ «آره» → outcome + مبلغِ انتظاری. همان دو محورِ مرده، حالا زنده."""
    os.environ[_FLAG] = "1"
    chan = _FakeChannel()
    loop, p = _loop_with_proposal(chan, amount=500)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)
    before = loop.proposal_metrics()
    assert before["proposal_outcomes"] == 0 and before["proposal_value_aud"] == 0.0
    rec = loop.record_proposal_outcome_by_token(tok, "ok")
    assert rec is not None and rec["verdict"] == "approved"
    assert rec["proposal_id"] == p.proposal_id, "token باید به idِ واقعی resolve شود"
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 1, m
    assert m["proposal_value_aud"] == 500.0, m
    assert m["proposal_positive"] == 1, m


def t_no_verdict_records_outcome_without_value():
    """«نه» هم یک پاسخِ واقعی است (outcome می‌سازد) ولی ارزش نه."""
    os.environ[_FLAG] = "1"
    chan = _FakeChannel()
    loop, p = _loop_with_proposal(chan, amount=500)
    loop.route_leg_proposals(deliver=True)
    rec = loop.record_proposal_outcome_by_token(loop._proposal_token(p.proposal_id), "no")
    assert rec["verdict"] == "rejected"
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 1 and m["proposal_positive"] == 0
    assert m["proposal_value_aud"] == 0.0, "ردشده نباید ارزش بسازد"


def t_dispatch_scheme_end_to_end():
    """قراردادِ واقعیِ کانال: dispatch_callback('prop:ok:<token>') → متریک.
    این همان مسیری است که threadِ pollerِ تلگرام طی می‌کند."""
    import wiring
    from approval_channel import TelegramApprovalChannel
    os.environ[_FLAG] = "1"
    chan_out = _FakeChannel()
    loop, p = _loop_with_proposal(chan_out, amount=1200)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)

    ch = TelegramApprovalChannel(token=None, owner_chat_id=None)   # not wired → صفر شبکه
    assert wiring.wire_proposal_buttons(channel=ch, live_loop=loop) is True
    out = ch.dispatch_callback(f"prop:ok:{tok}")
    assert isinstance(out, str) and "ثبت شد" in out, out
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 1 and m["proposal_value_aud"] == 1200.0, m
    assert len(loop.verdicts) == 0, "دکمهٔ اندازه‌گیری هرگز verdict/approval نمی‌سازد"


def t_arc_closes_to_goal_directed_measure():
    """قوسِ کامل: کارت+دکمه → تپ → متریک → ORGANISM-STATE → goal_directed.measure.
    اثباتِ اینکه دو محورِ ساختاراً-صفر واقعاً حرکت می‌کنند."""
    import json
    import goal_directed as gd
    import opslib
    os.environ[_FLAG] = "1"
    chan = _FakeChannel()
    loop, p = _loop_with_proposal(chan, amount=800)
    loop.route_leg_proposals(deliver=True)
    loop.record_proposal_outcome_by_token(loop._proposal_token(p.proposal_id), "ok")
    pm = loop.proposal_metrics()
    sp = opslib.STATE_DIR / "ORGANISM-STATE.json"
    sp.parent.mkdir(parents=True, exist_ok=True)
    try:
        sp.write_text(json.dumps({"proposal_metrics": pm}, ensure_ascii=False), "utf-8")
        now = gd.measure()["now"]
        assert now["proposal_outcomes"] == 1, now
        assert abs(now["proposal_value_aud"] - 800.0) < 0.005, now
    finally:
        if sp.exists():
            sp.unlink()


def t_real_poller_path_closes_arc():
    """آخرین حلقه: pollerِ واقعی (poll_once) با updateِ ساختگی — صفر شبکه.

    این تستِ «خطِ لوله» است نه واحد: getUpdates → allowlistِ مالک → cbq.data →
    dispatch_callback → قلاب → متریک. اگر هر حلقه‌ای مرده بود، اینجا قرمز می‌شود.
    """
    import wiring
    from approval_channel import TelegramApprovalChannel
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel(), amount=250)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)

    class _FakeHTTP:
        def __init__(self, updates):
            self.updates = list(updates)
            self.posts = []

        def get(self, url, timeout):
            batch, self.updates = self.updates, []
            return {"ok": True, "result": batch}

        def post(self, url, body, timeout_s=10.0):
            self.posts.append(body)
            return {"ok": True}

    upd = {"update_id": 1, "callback_query": {
        "id": "cb1", "data": f"prop:ok:{tok}", "from": {"id": 1},
        "message": {"chat": {"id": 1}, "text": "کارتِ پیشنهاد"}}}
    fh = _FakeHTTP([upd])
    ch = TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                 state_dir=str(_OPS / "state"),
                                 http_get=fh.get, http_post=fh.post)
    assert wiring.wire_proposal_buttons(channel=ch, live_loop=loop) is True
    ch.poll_once()
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 1, f"pollerِ واقعی قوس را نبست: {m}"
    assert m["proposal_value_aud"] == 250.0, m


def t_real_poller_rejects_non_owner():
    """allowlist: تپ از chat_idِ غیرمالک هرگز به قلاب نمی‌رسد."""
    import wiring
    from approval_channel import TelegramApprovalChannel
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel(), amount=250)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)

    class _FakeHTTP:
        def __init__(self, updates):
            self.updates = list(updates)

        def get(self, url, timeout):
            batch, self.updates = self.updates, []
            return {"ok": True, "result": batch}

        def post(self, url, body, timeout_s=10.0):
            return {"ok": True}

    upd = {"update_id": 1, "callback_query": {
        "id": "cb1", "data": f"prop:ok:{tok}", "from": {"id": 999},
        "message": {"chat": {"id": 999}, "text": "x"}}}   # ← غریبه
    fh = _FakeHTTP([upd])
    ch = TelegramApprovalChannel(token="123:abc", owner_chat_id=1,
                                 state_dir=str(_OPS / "state"),
                                 http_get=fh.get, http_post=fh.post)
    wiring.wire_proposal_buttons(channel=ch, live_loop=loop)
    ch.poll_once()
    assert loop.proposal_metrics()["proposal_outcomes"] == 0, \
        "غریبه نباید متریک بسازد (allowlistِ poll_once)"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) مرزها
# ════════════════════════════════════════════════════════════════════════════════

def t_unknown_token_is_inert():
    """tokenِ ناشناخته (کارتِ کهنه/جعلی) → None و صفر متریک."""
    os.environ[_FLAG] = "1"
    loop, _ = _loop_with_proposal(_FakeChannel())
    loop.route_leg_proposals(deliver=True)
    assert loop.record_proposal_outcome_by_token("deadbeefdeadbeef", "ok") is None
    assert loop.proposal_metrics()["proposal_outcomes"] == 0


def t_bad_verb_is_inert():
    """verbِ خارج از واژگان (از جمله verbهای پولیِ 'app') → None."""
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel())
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)
    for bad in ("approve", "", None, "pay", "settle"):
        assert loop.record_proposal_outcome_by_token(tok, bad) is None, bad
    assert loop.proposal_metrics()["proposal_outcomes"] == 0


def t_later_defers_without_burning_the_card():
    """«بعداً» تعویق است نه تصمیم — نباید کارت را بسوزاند.

    رگرسیونِ باگی که بازبینیِ خصمانه (۲۰۲۶-۰۷-۱۷، سه عدسیِ مستقل) گرفت: گاردِ
    «اولین تپ برنده» later را نهایی می‌گرفت، پس «آره»ی بعدیِ مالک بی‌صدا دور
    ریخته می‌شد و ارزشِ کار صفر ثبت می‌شد. سناریوی واقعی: صبح «بعداً»، بعدازظهر «آره».
    """
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel(), amount=5000)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)

    rec = loop.record_proposal_outcome_by_token(tok, "later")
    assert rec is not None and rec["event"] == "deferred", rec
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 0, f"تعویق نباید outcome بسازد: {m}"
    assert m["proposal_accept_rate"] == 0.0 and m["proposal_positive"] == 0

    # بعدازظهر: تصمیمِ واقعی — باید کامل ثبت شود
    ok = loop.record_proposal_outcome_by_token(tok, "ok")
    assert ok is not None, "«آره» بعد از «بعداً» نباید دور ریخته شود"
    assert ok["verdict"] == "approved"
    m2 = loop.proposal_metrics()
    assert m2["proposal_outcomes"] == 1, m2
    assert m2["proposal_value_aud"] == 5000.0, f"ارزشِ کارِ تأییدشده گم شد: {m2}"
    assert m2["proposal_accept_rate"] == 1.0, m2
    # و بعد از تصمیم، دیگر قفل است
    assert loop.record_proposal_outcome_by_token(tok, "no") is None


def t_later_toast_is_truthful():
    """toastِ «بعداً» باید بگوید کارت زنده می‌ماند — نه اینکه دروغ بگوید."""
    import wiring
    from approval_channel import TelegramApprovalChannel
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel(), amount=300)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)
    ch = TelegramApprovalChannel(token=None, owner_chat_id=None)
    wiring.wire_proposal_buttons(channel=ch, live_loop=loop)
    out = ch.dispatch_callback(f"prop:later:{tok}")
    assert "زنده" in out, out
    assert "ثبت شد" not in out, "تعویق نباید ادعای ثبت کند"
    assert loop.proposal_metrics()["proposal_outcomes"] == 0


def t_double_tap_is_idempotent():
    """دکمهٔ تلگرام ماندگار است — دو تپ نباید شمارش/ارزش را دوبرابر کند."""
    os.environ[_FLAG] = "1"
    loop, p = _loop_with_proposal(_FakeChannel(), amount=500)
    loop.route_leg_proposals(deliver=True)
    tok = loop._proposal_token(p.proposal_id)
    assert loop.record_proposal_outcome_by_token(tok, "ok") is not None
    assert loop.record_proposal_outcome_by_token(tok, "ok") is None, "تپِ دوم باید بی‌اثر باشد"
    assert loop.record_proposal_outcome_by_token(tok, "no") is None, "تغییرِ رأی هم append نمی‌کند"
    m = loop.proposal_metrics()
    assert m["proposal_outcomes"] == 1, m
    assert m["proposal_value_aud"] == 500.0, "دو-تپ نباید ارزش را دوبرابر کند"


def t_legacy_channel_fallback():
    """کانالی که reply_markup نمی‌شناسد → کارتِ بی‌دکمه، بدونِ کرش."""
    os.environ[_FLAG] = "1"
    chan = _LegacyChannel()
    loop, _ = _loop_with_proposal(chan)
    r = loop.route_leg_proposals(deliver=True)
    assert r["delivered"] == 1 and r["sent"] == 1, r
    assert len(chan.sent) == 1
    assert r["proposals"][0]["buttons"] is False, "fallback باید صادق گزارش کند"


def t_dispatch_without_hook_is_ignored():
    """کانالِ بی‌قلاب (فلگ خاموش) → schemeِ prop مثل هر ناشناخته «نادیده»."""
    from approval_channel import TelegramApprovalChannel
    ch = TelegramApprovalChannel(token=None, owner_chat_id=None)
    assert ch.dispatch_callback("prop:ok:whatever") == "نادیده"
    assert ch.dispatch_callback("prop:ok") == "نادیده"


def t_cb_map_is_bounded():
    """نگاشتِ token کران‌دار است — ارگانیسمِ ماه‌ها-زنده نباید حافظه نشت کند."""
    import live_loop as ll
    os.environ[_FLAG] = "1"
    leg = _fake_leg()
    loop = LiveLoop(bus=_InMemoryBus(), approval_channel=_FakeChannel(), leg=leg)
    for i in range(ll._PROPOSAL_CB_MAX + 25):
        leg.emit_proposal("draft_quote", {"scope": f"job-{i}", "expected_aud": 10})
        loop.route_leg_proposals(deliver=True, limit=50)
    assert len(loop._proposal_cb) <= ll._PROPOSAL_CB_MAX, len(loop._proposal_cb)


def t_button_path_never_settles():
    """خطِ قرمز: مسیرِ دکمه هیچ approve/settle/pay صدا نمی‌زند — و واقعاً به متریک وصل است.

    روی AST کار می‌کند نه grepِ متن: فقط فراخوانیِ اجراشدنی مهم است. گرپِ متنی روی
    داکستringِ «هیچ settle نمی‌کند» قرمز می‌شد — یعنی تست به نثر واکنش می‌داد نه به کد.
    """
    import ast
    tree = ast.parse((_OPS / "live_loop.py").read_text("utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
              and n.name == "record_proposal_outcome_by_token")
    called = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            called.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    forbidden = {"settle", "approve", "_do_approve", "pay", "post_journal",
                 "add_approval", "apply_ari_verdict"}
    assert not (called & forbidden), f"خطِ قرمز — مسیرِ دکمه صدا می‌زند: {called & forbidden}"
    assert "record_proposal_outcome" in called, "قوس باید واقعاً به متریک وصل باشد (نه vapor)"


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] فلگ خاموش → بدونِ کیبورد", t_flag_off_no_keyboard),
        ("[الف] فلگ خاموش → قلاب بسته نمی‌شود", t_flag_off_hook_not_wired),
        ("[ب] فلگ روشن → کیبورد + قرارداد ۶۴ بایت", t_flag_on_attaches_keyboard),
        ("[ب] تپِ آره → outcome + ارزش", t_token_tap_records_outcome_and_value),
        ("[ب] تپِ نه → outcome بدونِ ارزش", t_no_verdict_records_outcome_without_value),
        ("[ب] dispatch واقعیِ کانال e2e", t_dispatch_scheme_end_to_end),
        ("[ب] قوس تا goal_directed.measure", t_arc_closes_to_goal_directed_measure),
        ("[ب] pollerِ واقعی قوس را می‌بندد", t_real_poller_path_closes_arc),
        ("[ج] pollerِ واقعی غریبه را رد می‌کند", t_real_poller_rejects_non_owner),
        ("[ج] tokenِ ناشناخته بی‌اثر", t_unknown_token_is_inert),
        ("[ج] verbِ بد بی‌اثر", t_bad_verb_is_inert),
        ("[ج] «بعداً» کارت را نمی‌سوزاند", t_later_defers_without_burning_the_card),
        ("[ج] toastِ «بعداً» صادق است", t_later_toast_is_truthful),
        ("[ج] دو-تپ idempotent", t_double_tap_is_idempotent),
        ("[ج] کانالِ قدیمی fallback", t_legacy_channel_fallback),
        ("[ج] بی‌قلاب → نادیده", t_dispatch_without_hook_is_ignored),
        ("[ج] نگاشتِ token کران‌دار", t_cb_map_is_bounded),
        ("[ج] مسیرِ دکمه هرگز settle نمی‌کند", t_button_path_never_settles),
    ])
    sys.exit(1 if failed else 0)
