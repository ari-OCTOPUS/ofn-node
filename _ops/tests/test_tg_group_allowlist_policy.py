#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_group_allowlist_policy — گیتِ گروه از deny-list به allow-list.

قرارداد (TG-UI-CHARTER-2026-07-31، رأی allow-list): در گروه هر چیزِ
**فرمان‌گونه** به‌طورِ پیش‌فرض رد می‌شود — هر اسلش‌کامندی (لاتین و فارسی)،
هر دکمهٔ خارج از `GROUP_CALLBACK_VERBS` — ولی میزِ کارِ پا آزاد می‌ماند:
جملهٔ دلخواه/سؤال/رسانه/ریپلای در تاپیکِ پا leg_scoped است چون مدلِ Task به
همان‌ها زنده است. فقط ۸ پای `CONTRACT_LEGS` leg_scoped می‌گیرند؛ system و
mirror با اینکه تاپیک دارند پا نیستند → core_conversation (نه بلعیده‌شدن در
صفِ Task، نه کشتنِ اتاقِ آینه).

ماژولِ زیرِ آزمون خالص و stdlib است — تست مستقیم تابع را صدا می‌زند.
"""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-group-allowlist")

_TC = str(Path(__file__).resolve().parent.parent / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import input_surface_policy as isp  # noqa: E402

OWNER = 6150431610
STRANGER = 999
GROUP = -1004475788460
# نگاشتِ واقع‌نما: ۸ پای قرارداد + دو تاپیکِ غیرِ پا که config واقعاً دارد.
TOPICS = {"lead": 22, "ziman": 23, "mining": 24, "crypto": 25,
          "accounting": 26, "studio_pf": 27, "knowledge": 29,
          "cartographer": 65, "system": 28, "mirror": 205}


def _msg(*, chat_id=GROUP, chat_type="supergroup", from_id=OWNER, text="",
         thread=None, extra=None):
    m = {"chat": {"id": chat_id, "type": chat_type},
         "from": {"id": from_id}, "text": text}
    if thread is not None:
        m["message_thread_id"] = thread
    if extra:
        m.update(extra)
    return {"message": m}


def _cbq(*, data, chat_id=GROUP, chat_type="supergroup", from_id=OWNER,
         thread=None):
    m = {"chat": {"id": chat_id, "type": chat_type}}
    if thread is not None:
        m["message_thread_id"] = thread
    return {"callback_query": {"from": {"id": from_id}, "data": data,
                               "message": m}}


def _c(upd, role="outer"):
    return isp.classify(upd, bot_role=role, owner_id=OWNER, group_id=GROUP,
                        topics=TOPICS)


# ── LEG_VERBS بالاخره مصرف‌کننده دارد ───────────────────────────────────────
def t_every_leg_verb_is_allowed_in_its_own_topic():
    for verb in isp.LEG_VERBS:
        d = _c(_msg(thread=22, text=verb))
        assert d["allow"] is True and d["mode"] == "leg_scoped", (verb, d)
        assert d["leg"] == "lead", (verb, d)


def t_is_leg_verb_is_exact_match_not_substring():
    for verb in isp.LEG_VERBS:
        assert isp.is_leg_verb(verb), verb
        assert isp.is_leg_verb(verb + "؟"), verb          # نقطه‌گذاریِ انتهایی
        assert isp.is_leg_verb("  " + verb + "  "), verb  # فاصلهٔ اضافی
    # جملهٔ کاری که فعل را **در بر دارد** فعل نیست — Task است (قانونِ exact-match).
    assert not isp.is_leg_verb("وضعیتِ سایتِ مشتری را بررسی کن")
    assert not isp.is_leg_verb("/status")
    assert not isp.is_leg_verb("")
    assert not isp.is_leg_verb(None)


def t_leg_verbs_survive_future_tightening_of_core_words():
    """جهتِ ساختاری: allow-list ِ فعل‌ها بالاتر از _CORE_WORDS می‌نشیند، پس
    سخت‌ترشدنِ الگوی هسته‌ای این ۱۲ فعل را نمی‌شکند."""
    original = isp._CORE_WORDS
    try:
        import re
        isp._CORE_WORDS = re.compile(r"(وضعیت|قدم|بودجه)", re.I)  # سخت‌گیریِ فرضی
        d = _c(_msg(thread=22, text="وضعیت"))
        assert d["allow"] is True and d["mode"] == "leg_scoped", d
    finally:
        isp._CORE_WORDS = original


# ── میزِ کارِ پا آزاد می‌ماند (مدلِ Task) ──────────────────────────────────
def t_arbitrary_persian_work_sentence_stays_leg_scoped():
    for txt in ("وضعیتِ سایتِ مشتری را بررسی کن",
                "فردا با تامین‌کننده تماس بگیر و قیمت بگیر",
                "چرا گیر کردی؟"):
        d = _c(_msg(thread=22, text=txt))
        assert d["allow"] is True and d["mode"] == "leg_scoped", (txt, d)


def t_media_with_empty_text_stays_leg_scoped():
    d = _c(_msg(thread=22, text="", extra={"photo": [{"file_id": "x"}]}))
    assert d["allow"] is True and d["mode"] == "leg_scoped", d
    assert d["leg"] == "lead", d


def t_reply_to_blocked_card_stays_allowed():
    d = _c(_msg(thread=22, text="جوابِ مانع: شماره‌اش ۰۴۱۲ است",
                extra={"reply_to_message": {
                    "text": "🚧 TASK-12 گیر کرده — چه اطلاعاتی لازم است؟"}}))
    assert d["allow"] is True and d["mode"] == "leg_scoped", d


# ── اسلش‌کامند در گروه مطلقاً ممنوع — DM آزاد ──────────────────────────────
def t_any_slash_command_is_denied_in_group_even_non_core():
    """سوراخِ قدیمی (gap group-1/group-2): deny-list فقط ۴۱ فعل را می‌گرفت و
    /now /menu /funnel /missions … رد می‌شدند. حالا حکم ساختاری است."""
    for cmd in ("/panic", "/now", "/menu", "/panel", "/funnel", "/missions",
                "/verdicts", "/flags", "/deal", "/organ-approve", "/neworgan"):
        for thread in (22, 28, 205):        # پا، system، mirror — همه یک حکم
            d = _c(_msg(thread=thread, text=cmd))
            assert d["allow"] is False and d["mode"] == "deny", (cmd, thread, d)
            assert d["redirect"] == "outer_dm", (cmd, thread, d)


def t_persian_slash_commands_no_longer_bypass_the_gate():
    """_CMD قبلاً ASCII-only بود؛ «/توان» از کنارِ گیت رد می‌شد."""
    for cmd in ("/توان", "/رفتار", "/کد", "/وضعیت"):
        d = _c(_msg(thread=22, text=cmd))
        assert d["allow"] is False and d["mode"] == "deny", (cmd, d)
        assert "slash-command" in d["reason"] or "core-command" in d["reason"], d
        assert isp.redirect_text(d), (cmd, "متنِ هدایت خالی است")


def t_slash_commands_stay_allowed_in_outer_dm():
    for cmd in ("/panic", "/menu", "/funnel", "/توان"):
        d = _c(_msg(chat_id=OWNER, chat_type="private", text=cmd))
        assert d["allow"] is True and d["mode"] == "core_conversation", (cmd, d)


# ── دکمه‌ها از همان گیت رد می‌شوند ─────────────────────────────────────────
def t_core_callbacks_are_denied_in_group_topics():
    """gap boundary-2: pw:panic از تاپیکِ پا leg_scoped می‌گرفت."""
    for data in ("pw:pn", "pwc:stop", "oc:menu", "map:start", "hm:build",
                 "mn:x", "m:2", "x:1", "iv:a", "mr:b", "qt:send:1"):
        d = _c(_cbq(data=data, thread=22))
        assert d["allow"] is False and d["mode"] == "deny", (data, d)
        assert d["reason"].startswith("callback-dm-only:"), (data, d)
        assert "DM" in isp.redirect_text(d), (data, d)


def t_leg_card_callbacks_stay_allowed_in_their_topic():
    """mo (mining sub-UI) از ۱fea349 (۰۸-۰۱) عمداً به GROUP_CALLBACK_VERBS
    اضافه شد تا دکمه‌های ماینینگ داخلِ تاپیکِ پا کار کنند."""
    for data in ("tk:s:lead:TASK-1", "lg:lead", "ok:VQ-1", "no:VQ-1",
                 "later:VQ-1", "ap:ok:abc", "ms:1", "tr:x", "dg:e:trace1",
                 "mo:1"):
        d = _c(_cbq(data=data, thread=22))
        assert d["allow"] is True and d["mode"] == "leg_scoped", (data, d)
        assert d["leg"] == "lead", (data, d)


def t_all_callbacks_stay_allowed_in_dm():
    for data in ("pw:pn", "oc:menu", "map:start", "tk:s:lead:TASK-1"):
        d = _c(_cbq(data=data, chat_id=OWNER, chat_type="private"))
        assert d["allow"] is True, (data, d)


def t_callbacks_in_general_topic_stay_denied():
    d = _c(_cbq(data="tk:s:lead:TASK-1", thread=None))
    assert d["allow"] is False, d
    assert "general-or-unknown" in d["reason"], d


# ── فقط ۸ پای قرارداد leg_scoped می‌گیرند ──────────────────────────────────
def t_system_and_mirror_topics_are_not_legs_but_still_talk():
    """gap group-6/boundary-7: قبلاً system(28) و mirror(205) leg_scoped
    می‌گرفتند و صفِ Task جمله‌های اتاقِ آینه را می‌بلعید."""
    for thread, key in ((28, "system"), (205, "mirror")):
        d = _c(_msg(thread=thread, text="سلام، چه خبر؟"))
        assert d["allow"] is True, (key, d)
        assert d["mode"] == "core_conversation", (key, d)
        assert d["leg"] is None, (key, d)
        assert key in d["reason"], (key, d)


def t_every_contract_leg_topic_is_leg_scoped():
    for key in isp.CONTRACT_LEGS:
        d = _c(_msg(thread=TOPICS[key], text="یک کارِ تازه برای امروز"))
        assert d["allow"] is True and d["mode"] == "leg_scoped", (key, d)
        assert d["leg"] == key, (key, d)


def t_leg_of_helper_refuses_non_contract_keys():
    assert isp._leg_of(22, TOPICS) == "lead"
    assert isp._leg_of(28, TOPICS) is None      # system
    assert isp._leg_of(205, TOPICS) is None     # mirror
    assert isp._leg_of(9999, TOPICS) is None


def t_unknown_topic_is_denied():
    d = _c(_msg(thread=31337, text="وضعیت"))
    assert d["allow"] is False and d["redirect"] == "outer_dm", d


# ── غیرمالک و ورودیِ خصمانه ────────────────────────────────────────────────
def t_non_owner_is_denied_everywhere():
    probes = (_msg(chat_id=OWNER, chat_type="private", from_id=STRANGER,
                   text="سلام"),
              _msg(thread=22, from_id=STRANGER, text="وضعیت"),
              _msg(thread=205, from_id=STRANGER, text="سلام"),
              _cbq(data="tk:s:lead:TASK-1", thread=22, from_id=STRANGER),
              _cbq(data="pw:pn", chat_id=OWNER, chat_type="private",
                   from_id=STRANGER))
    for upd in probes:
        d = _c(upd)
        assert d["allow"] is False and d["reason"] == "non-owner", (upd, d)


def t_classify_never_raises_on_malformed_updates():
    """قراردادِ never-raises — ازجمله شکل‌هایی که نسخهٔ قبل را crash می‌کرد
    (`{"message": None, "callback_query": None}` → AttributeError روی None)."""
    shapes = (None, 42, "str", [], (),
              {}, {"message": None}, {"callback_query": None},
              {"message": None, "callback_query": None},
              {"message": "not-a-dict"}, {"message": []},
              {"callback_query": "not-a-dict"},
              {"callback_query": {}}, {"callback_query": {"message": 7}},
              {"callback_query": {"message": {}, "data": None, "from": None}},
              {"message": {"chat": None, "from": [], "text": 5}},
              {"message": {"chat": {"id": "abc", "type": 7},
                           "from": {"id": "nope"}, "text": {}}})
    for bad in shapes:
        d = isp.classify(bad, bot_role="outer", owner_id=OWNER,
                         group_id=GROUP, topics=TOPICS)
        assert isinstance(d, dict), (bad, d)
        assert d["allow"] is False, (bad, d)
    # thread ِ رشته‌ای که به عدد می‌رسد خصمانه نیست — coercion ِ نرمِ موجود.
    d = isp.classify({"message": {"chat": {"id": GROUP, "type": "supergroup"},
                                  "from": {"id": OWNER}, "text": None,
                                  "message_thread_id": "22"}},
                     bot_role="outer", owner_id=OWNER, group_id=GROUP,
                     topics=TOPICS)
    assert d["mode"] == "leg_scoped" and d["leg"] == "lead", d


def t_contract_shape_is_stable():
    """قراردادِ برگشتی با center عوض نشده: همان کلیدها، همان MODES."""
    d = _c(_msg(thread=22, text="سلام"))
    assert set(d) == {"allow", "mode", "leg", "redirect", "reason"}, d
    assert d["mode"] in isp.MODES, d
    assert isp.MODES == ("core_conversation", "status_approval", "leg_scoped",
                         "clarify", "deny")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_group_allowlist_policy: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
