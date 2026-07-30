#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_input_surface_policy — ورودی هم سیاست دارد، نه فقط خروجی.

شکافی که می‌بندد: تا امروز فقط **خروجی** سیاست داشت (`surface_router`)، پس
گروه می‌توانست فرمانِ هسته‌ای بگیرد حتی وقتی هیچ خروجیِ هسته‌ای به آن نمی‌رفت.
قرارداد: `_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`.

ماژول عمداً صداکننده ندارد (`center.py` هانکِ بیگانه دارد) — پس این فایل خودِ
تابع را اجرا می‌کند، نه grep ِ سورس.
"""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-input-policy")

_TC = str(Path(__file__).resolve().parent.parent / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import input_surface_policy as isp  # noqa: E402

OWNER = 6150431610
STRANGER = 999
GROUP = -1004475788460
# کلیدها عمداً همان‌هایی‌اند که `center-config.json` واقعاً دارد — نه یک نمونهٔ
# سه‌تایی. فیکسچرِ کوچک باعث شد حلقهٔ پوششِ نامِ فارسی فقط دو پا را بسنجد و
# بقیه بی‌صدا رد شوند؛ فیکسچری که از واقعیت کوچک‌تر است، پوششِ کاذب می‌سازد.
TOPICS = {"lead": 11, "ziman": 12, "mining": 13, "crypto": 14,
          "accounting": 15, "studio_pf": 16, "system": 17,
          "knowledge": 18, "cartographer": 19, "mirror": 20}


def _msg(*, chat_id, chat_type, from_id=OWNER, text="", thread=None):
    m = {"chat": {"id": chat_id, "type": chat_type},
         "from": {"id": from_id}, "text": text}
    if thread is not None:
        m["message_thread_id"] = thread
    return {"message": m}


def _c(upd, role="outer"):
    return isp.classify(upd, bot_role=role, owner_id=OWNER, group_id=GROUP,
                        topics=TOPICS)


# ── DM ──────────────────────────────────────────────────────────────────────
def t_outer_dm_owner_gets_full_conversation():
    d = _c(_msg(chat_id=OWNER, chat_type="private", text="هدفت این هفته چیه؟"))
    assert d["allow"] is True and d["mode"] == "core_conversation", d


def t_outer_dm_accepts_core_commands_that_the_group_rejects():
    for cmd in ("/panic", "/budget", "/capabilities", "/goal"):
        d = _c(_msg(chat_id=OWNER, chat_type="private", text=cmd))
        assert d["allow"] is True, (cmd, d)


def t_inner_dm_is_status_and_approval_not_free_chat():
    ok = _c(_msg(chat_id=OWNER, chat_type="private", text="/status"), role="inner")
    assert ok["allow"] is True and ok["mode"] == "status_approval", ok
    chat = _c(_msg(chat_id=OWNER, chat_type="private",
                   text="نظرت دربارهٔ استراتژی چیه؟"), role="inner")
    assert chat["allow"] is False and chat["mode"] == "clarify", chat
    assert chat["redirect"] == "outer_dm", chat


# ── گروه: تاپیکِ پا ─────────────────────────────────────────────────────────
def t_a_leg_topic_allows_leg_scoped_talk():
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                text="وضعیتش چیه؟"))
    assert d["allow"] is True and d["mode"] == "leg_scoped", d
    assert d["leg"] == "lead", d


def t_general_is_denied_and_redirected():
    """General = بدونِ thread. همان حکمِ تاپیکِ ناشناخته."""
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", text="سلام"))
    assert d["allow"] is False and d["mode"] == "deny", d
    assert d["redirect"] == "outer_dm", d
    assert "general-or-unknown" in d["reason"], d


def t_an_unknown_topic_is_denied_not_guessed():
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=9999,
                text="وضعیت؟"))
    assert d["allow"] is False and d["redirect"] == "outer_dm", d


def t_core_commands_in_a_leg_topic_are_denied():
    """حتی از مالک، حتی در تاپیکِ درست، حتی read-only."""
    for cmd in ("/panic", "/stop", "/budget", "/capabilities", "/goal",
                "/discovery", "/doctor", "/memory", "/flag"):
        d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11, text=cmd))
        assert d["allow"] is False, (cmd, d)
        assert d["redirect"] == "outer_dm", (cmd, d)
        assert "core-command" in d["reason"], (cmd, d)


def t_core_topics_in_natural_language_are_denied_too():
    """فرمان نبودن یعنی بی‌خطر نبودن — متنِ آزادِ هسته‌ای هم رد می‌شود."""
    for txt in ("کلِ سیستم رو ری‌استارت کن", "بودجه چقدره؟",
                "کشفِ دنیا چی شد؟", "توکن رو عوض کن"):
        d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11, text=txt))
        assert d["allow"] is False, (txt, d)


def t_cross_leg_talk_asks_instead_of_guessing():
    """حدس‌زدنِ اینکه کدام پا منظور است، همان «مسیریابی به فلگِ خاموش» است."""
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                text="وضعیتِ mining چطوره؟"))
    assert d["allow"] is False and d["mode"] == "clarify", d
    assert "cross-leg" in d["reason"], d
    assert isp.redirect_text(d), "متنِ clarify خالی است"


def t_the_same_leg_named_in_its_own_topic_is_fine():
    """گاردِ ضدِ بیش‌بست: نامِ خودِ پا در تاپیکِ خودش cross-leg نیست."""
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                text="lead چطور پیش می‌رود؟"))
    assert d["allow"] is True and d["mode"] == "leg_scoped", d


def t_cross_leg_is_detected_when_the_owner_writes_in_persian():
    """جملهٔ دقیقِ گیت ۶ِ ACCEPTANCE-RUNBOOK — و باگی که تستِ سبز نگرفت.

    بندِ بالا با «وضعیتِ mining چطوره؟» می‌سنجید: واژهٔ **لاتین** داخلِ جملهٔ
    فارسی. ولی کلیدهای تاپیک لاتین‌اند و مالک فارسی می‌نویسد، پس تشخیص در عملِ
    واقعی کور بود — «ماینینگ را متوقف کن» در تاپیکِ lead اجازهٔ `leg_scoped`
    می‌گرفت. الگو روی نمونه‌ای کالیبره شده بود که قطعاً می‌گیرد."""
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                text="ماینینگ را متوقف کن"))
    assert d["allow"] is False, d
    assert d["mode"] == "clarify", d
    assert "cross-leg" in d["reason"] and "mining" in d["reason"], d


def t_every_leg_with_a_persian_name_is_detected_across_topics():
    """پوششِ کامل: هر پایی که نامِ فارسی دارد باید از تاپیکِ یک پای دیگر
    گرفته شود — وگرنه فهرست نیمه‌کاره است و همان کوریِ نقطه‌ای برمی‌گردد."""
    for key, aliases in isp.LEG_ALIASES.items():
        if key not in TOPICS or key == "lead":
            continue
        for alias in aliases:
            d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11,
                        text=f"{alias} را بررسی کن"))
            assert d["allow"] is False and d["mode"] == "clarify", (key, alias, d)
            assert key in d["reason"], (key, alias, d)


def t_a_legs_own_persian_name_in_its_own_topic_is_not_cross_leg():
    """ضدِ بیش‌بست، فارسی: «نقاشی» در تاپیکِ lead خودِ همان پاست."""
    for txt in ("نقاشی چطور پیش می‌رود؟", "لید تازه داریم؟"):
        d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11, text=txt))
        assert d["allow"] is True and d["mode"] == "leg_scoped", (txt, d)


def t_common_persian_words_are_not_mistaken_for_leg_names():
    """بیش‌بست به‌اندازهٔ کم‌بست بد است: clarify ِ بی‌مورد یعنی مالک یاد
    می‌گیرد گیت را جدی نگیرد. واژه‌های عمومی نباید نامِ پا شمرده شوند."""
    for txt in ("حساب کن ببین چقدر شد", "سیستمش خوب کار می‌کند",
                "ارزش این کار چقدره؟"):
        d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11, text=txt))
        assert d["mode"] != "clarify", (txt, d)


# ── غیرمالک و ابهام ────────────────────────────────────────────────────────
def t_a_non_owner_is_denied_everywhere():
    for chat_id, ctype, thread in ((OWNER, "private", None),
                                   (GROUP, "supergroup", 11),
                                   (GROUP, "supergroup", None)):
        d = _c(_msg(chat_id=chat_id, chat_type=ctype, from_id=STRANGER,
                    text="/status", thread=thread))
        assert d["allow"] is False and d["reason"] == "non-owner", d


def t_the_inner_bot_has_no_voice_in_the_group():
    d = _c(_msg(chat_id=GROUP, chat_type="supergroup", thread=11, text="وضعیت؟"),
           role="inner")
    assert d["allow"] is False and d["reason"] == "inner-bot-in-group", d


def t_an_unknown_chat_is_denied():
    d = _c(_msg(chat_id=-100999, chat_type="supergroup", thread=11, text="x"))
    assert d["allow"] is False and d["reason"] == "unknown-chat", d


def t_malformed_input_never_raises_and_never_allows():
    for bad in (None, {}, {"message": None}, {"message": {"chat": None}},
                {"message": {"chat": {}, "from": {}}}, "not-a-dict", 42):
        d = isp.classify(bad, bot_role="outer", owner_id=OWNER,
                         group_id=GROUP, topics=TOPICS)
        assert d["allow"] is False, (bad, d)


def t_an_unknown_bot_role_is_denied():
    d = _c(_msg(chat_id=OWNER, chat_type="private", text="x"), role="third-bot")
    assert d["allow"] is False and "unknown-bot-role" in d["reason"], d


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_input_surface_policy: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
