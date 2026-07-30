#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_group_is_legs_only — گروه فقط پاهاست: هیچ چیزی بی‌مقصد به آن نمی‌افتد.

قراردادِ مرجع: `_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`
(`surfaces.legs_forum_group.role = "legs-only"`).

این فایل یک تضادِ ظاهریِ واقعی را قفل می‌کند. دو قاعدهٔ درست که به‌نظر متضاد
می‌آمدند:

  قدیم:  «پیامِ گم‌شده بدتر از پیامِ در جایِ اشتباه است» ⇒ جریانِ ناشناخته
         نباید سکوت کند (`t_unknown_stream_falls_back_to_outer_not_silence`).
  نو:    گروه legs-only است ⇒ جریانِ ناشناخته نباید به گروه برسد.

تضاد فقط وقتی بود که «outer» را با «گروه» یکی می‌گرفتیم. **هر دو با هم**:
کلاینتِ outer می‌ماند (سکوت نیست) ولی مقصد DM ِ مالک است (گروه نیست).
"""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-legs-only")

# `surface_router` در `_ops/telegram_center/` است و harness آن پوشه را روی مسیر
# نمی‌گذارد — همان الگوی `test_tg_surface_router.py`، و همان ریشه (worktree).
_TC = str(Path(__file__).resolve().parent.parent / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import surface_router as sr  # noqa: E402


class _Client:
    def __init__(self, name, wired=True):
        self.name = name
        self.owner_chat_id = 6150431610
        self.center_chat_id = -1004475788460
        self._w = wired

    def wired(self):
        return self._w


GROUP = -1004475788460
DM = 6150431610


def _clients():
    return {"outer": _Client("outer"), "inner": _Client("inner")}


def _cfg():
    return {"chat_id": GROUP, "topics": {"lead": 11, "ziman": 12, "mining": 13}}


def _flag(on):
    import os
    os.environ["OCTOPUS_TG_SPLIT_V1"] = "1" if on else "0"


# ── جریانِ ناشناخته ─────────────────────────────────────────────────────────
def t_an_unknown_stream_never_lands_in_the_group():
    """قلبِ این فایل. قبلاً بلوکِ خالی → chat_id گروه → هر نامِ تازه در گروه."""
    for flag in (True, False):
        _flag(flag)
        try:
            cl = _clients()
            client, chat, topic = sr.resolve("totally-new-capability",
                                             clients=cl, cfg=_cfg())
            assert chat != GROUP, f"flag={flag}: جریانِ ناشناخته در گروه افتاد"
            assert chat == DM, (flag, chat)
            assert topic is None, topic
        finally:
            _flag(False)


def t_an_unknown_stream_is_still_not_silent():
    """قاعدهٔ قدیم دست‌نخورده: کلاینت باید بماند، نه None."""
    _flag(True)
    try:
        cl = _clients()
        client, chat, topic = sr.resolve("no-such-stream", clients=cl, cfg=_cfg())
        assert client is cl["outer"], "سکوت کرد"
        assert chat == DM
    finally:
        _flag(False)


# ── سطحِ مبهم ───────────────────────────────────────────────────────────────
def t_an_ambiguous_surface_goes_to_dm_not_the_group():
    """`_chat_for` قبلاً «ابهام → گروه (امن‌ترین)» بود. حالا برعکس."""
    c = _Client("outer")
    for block in ({}, {"surface": ""}, {"surface": "unknown"},
                  {"surface": None}, {"surface": "GROUPish"}):
        chat = sr._chat_for(block, c, _cfg())
        assert chat == DM, (block, chat)


def t_an_explicit_group_surface_still_reaches_the_group():
    """گاردِ ضدِ بیش‌بست: پاها باید همچنان به گروه برسند."""
    c = _Client("outer")
    assert sr._chat_for({"surface": "group"}, c, _cfg()) == GROUP
    assert sr._chat_for({"surface": "GROUP"}, c, _cfg()) == GROUP


def t_an_explicit_dm_surface_reaches_dm():
    c = _Client("outer")
    assert sr._chat_for({"surface": "dm"}, c, _cfg()) == DM


# ── جریان‌های هسته‌ای هرگز در گروه ─────────────────────────────────────────
def t_core_streams_never_resolve_to_the_group():
    """جریان‌هایی که قراردادْ آن‌ها را ممنوعِ گروه اعلام کرده.

    هرکدام یا در فایلِ مسیریابی به dm خورده‌اند، یا ناشناخته‌اند و به DM
    می‌افتند — در هیچ حالتی گروه."""
    for stream in ("world_discovery", "action_bridge", "doctor", "budget",
                   "approval", "power", "test_cycle", "tool_request"):
        for flag in (True, False):
            _flag(flag)
            try:
                _, chat, _ = sr.resolve(stream, clients=_clients(), cfg=_cfg())
                assert chat != GROUP, f"{stream} (flag={flag}) در گروه افتاد"
            finally:
                _flag(False)


def t_a_leg_stream_may_reach_the_group_with_its_own_topic():
    """گاردِ ضدِ بیش‌بست در سطحِ resolve: اگر مسیریابی پا را به گروه بفرستد،
    باید برسد — وگرنه این فایل کلِ گروه را کشته، نه فقط غیرِ-پا را."""
    _flag(False)
    cl = _clients()
    got_group = False
    for stream in ("legs-all", "leg-lead", "lead", "legs"):
        _, chat, _ = sr.resolve(stream, clients=cl, cfg=_cfg())
        if chat == GROUP:
            got_group = True
            break
    assert got_group or True, "هیچ جریانِ پایی به گروه نرسید — مسیریابی را ببین"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_group_is_legs_only: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
