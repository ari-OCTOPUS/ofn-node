#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_route_seam — صداکنندهٔ واقعیِ surface_router.resolve و رفتارش در دو حالتِ فلگ.

بستنِ VQ-TG-OUTPUT-001: تا امروز `resolve` **صفر صداکننده** داشت — تستش ۱۲/۱۲
سبز بود و ۵۸ پیامِ هسته‌ای با topic=None در General می‌نشست. حالا مرکز از راهِ
`Center._route_send` می‌فرستد و این فایل سه چیز را قفل می‌کند:

  ۱. فلگ خاموش = رفتارِ امروز **بایت‌به‌بایت** (بلوکِ current).
  ۲. فلگ روشن = هسته به DM، alert به رباتِ inner، پالس فقط بعد از فلگ.
  ۳. دکمه‌های خانه (hm:*) در همان روترِ مرکز رسیدگی می‌شوند — نه کارتِ مرده.

⚠️ درسِ «پایهٔ زیرِ سطحِ هدف»: هر بندِ escalation یک موردِ منفی هم دارد
(فلگ خاموش نباید DM بدهد) — وگرنه جهشِ «همیشه target» سبز می‌ماند.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-route-seam")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import surface_router as sr  # noqa: E402

OWNER = 6150431610
GROUP = -1004475788460
CFG = {"chat_id": GROUP,
       "topics": {"lead": 22, "ziman": 23, "mining": 24, "system": 28}}


class _FakeClient:
    """کلاینتِ ساختگی با همان قراردادِ سنجیده‌شده در test_tg_client_contract."""

    def __init__(self, name, owner=OWNER, center=GROUP, wired=True):
        self.name = name
        self.owner_chat_id = owner
        self.center_chat_id = center
        self._wired = wired
        self.sent = []

    def wired(self):
        return self._wired

    def send(self, text, *, chat_id=None, topic_id=None, keyboard=None,
             pin=False, stream="center"):
        self.sent.append({"text": text, "chat_id": chat_id,
                          "topic_id": topic_id, "keyboard": keyboard,
                          "pin": pin, "stream": stream})
        return 1000 + len(self.sent)


def _clients():
    return {"outer": _FakeClient("outer"), "inner": _FakeClient("inner")}


def _flag(on: bool):
    if on:
        os.environ["OCTOPUS_TG_SPLIT_V1"] = "1"
    else:
        os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)


# ── ۱) فلگ خاموش — واقعیتِ امروز بایت‌به‌بایت ───────────────────────────────
def t_flag_off_center_digest_still_goes_to_system_topic():
    """پایهٔ زیرِ سطحِ هدف: بدونِ فلگ هیچ‌چیز نباید DM شود."""
    _flag(False)
    c = _clients()
    cl, cid, tid = sr.resolve("center-digest", clients=c, cfg=CFG)
    assert cl is c["outer"], "فلگ خاموش ⇒ همیشه outer"
    assert cid == GROUP and tid == 28, (cid, tid)


def t_flag_off_center_alert_stays_on_outer_in_group():
    _flag(False)
    c = _clients()
    cl, cid, tid = sr.resolve("center-alert", clients=c, cfg=CFG)
    assert cl is c["outer"] and cid == GROUP and tid == 28, (cl.name, cid, tid)


def t_flag_off_pulse_goes_nowhere_at_all():
    """پالس قبل از فلگ باید **هیچ‌جا** نرود — نه گروه، نه DM. بلوکِ none."""
    _flag(False)
    cl, cid, tid = sr.resolve("center-pulse", clients=_clients(), cfg=CFG)
    assert cl is None and cid is None and tid is None, (cl, cid, tid)


# ── ۲) فلگ روشن — قراردادِ مصوب ────────────────────────────────────────────
def t_flag_on_core_streams_reach_the_owner_dm_not_the_group():
    _flag(True)
    try:
        c = _clients()
        for s in ("center-status", "center-digest", "center-decision",
                  "center-pulse"):
            cl, cid, tid = sr.resolve(s, clients=c, cfg=CFG)
            assert cl is c["outer"], (s, cl and cl.name)
            assert cid == OWNER, f"{s} باید DM ِ مالک باشد، نه {cid}"
            assert tid is None, f"{s}: تاپیک در DM معنا ندارد (۴۰۰ Bad Request)"
    finally:
        _flag(False)


def t_flag_on_alert_moves_to_the_inner_bot_dm():
    """قراردادِ critical-alerts → رباتِ اختاپوس (inner). بی‌دکمه ⇒ بدونِ ریسکِ
    کارتِ مرده."""
    _flag(True)
    try:
        c = _clients()
        cl, cid, tid = sr.resolve("center-alert", clients=c, cfg=CFG)
        assert cl is c["inner"], "alert باید روی inner برود"
        assert cid == OWNER and tid is None, (cid, tid)
    finally:
        _flag(False)


def t_flag_on_alert_falls_back_to_outer_when_inner_is_dead():
    """نبودِ inner نباید هشدار را گم کند — سقوط به outer + DM."""
    _flag(True)
    try:
        c = {"outer": _FakeClient("outer"), "inner": None}
        cl, cid, tid = sr.resolve("center-alert", clients=c, cfg=CFG)
        assert cl is c["outer"] and cid == OWNER, (cl and cl.name, cid)
    finally:
        _flag(False)


def t_flag_on_legs_keep_their_topics():
    """ضدِ بیش‌بست: فلگ نباید پاها را از تاپیکشان بیرون کند."""
    _flag(True)
    try:
        c = _clients()
        cl, cid, tid = sr.resolve("legs-all", clients=c, cfg=CFG)
        assert cid == GROUP, "پاها در گروه می‌مانند"
    finally:
        _flag(False)


# ── ۳) صداکنندهٔ واقعی — نه فقط جدول ───────────────────────────────────────
def t_the_center_actually_calls_route_send_for_its_core_ambient_sends():
    """AST: سه سایتِ هسته‌ای (digest ادغامی، decision، alert) دیگر مستقیم
    `_client.send(topic=system)` نمی‌زنند بلکه از `_route_send` می‌روند.
    این همان بندی است که «صفر صداکننده» را برای همیشه می‌بندد."""
    import ast
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    tree = ast.parse(src)
    routed = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_route_send"
                and node.args
                and isinstance(node.args[0], ast.Constant)):
            routed.add(node.args[0].value)
    for must in ("center-digest", "center-decision", "center-alert",
                 "center-pulse"):
        assert must in routed, f"{must} از _route_send نمی‌رود: {sorted(routed)}"
    # و resolve واقعاً از داخلِ _route_send صدا زده می‌شود.
    calls_resolve = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "resolve"
        and getattr(n.func.value, "id", None) in ("_sr", "sr", "surface_router")
        for n in ast.walk(tree))
    assert calls_resolve, "هیچ فراخوانیِ resolve در center نیست — درز قطع شده"


def t_route_send_passes_the_precise_stream_label_to_the_receipt():
    """رسید باید نامِ دقیق (center-digest/…) بگیرد نه برچسبِ عمومیِ center —
    وگرنه پروبِ بعد از ری‌استارت نمی‌تواند مسیر را راستی‌آزمایی کند."""
    _flag(True)
    try:
        import center as _c
        center = _c.Center.__new__(_c.Center)
        outer = _FakeClient("outer")
        inner = _FakeClient("inner")
        center._client = outer
        center._inner = inner
        center._render = None
        sent = _c.Center._route_send(center, "center-digest", "متنِ آزمون",
                                     cfg=CFG)
        assert sent is not None
        assert outer.sent and outer.sent[-1]["stream"] == "center-digest", \
            outer.sent
        assert outer.sent[-1]["chat_id"] == OWNER, outer.sent
    finally:
        _flag(False)


def t_route_send_honours_the_deliberate_silence_of_the_none_block():
    """بلوکِ none ⇒ هیچ ارسالی — نه سقوط به گروه. (پالسِ پیش‌ازفلگ.)"""
    _flag(False)
    import center as _c
    center = _c.Center.__new__(_c.Center)
    outer = _FakeClient("outer")
    center._client = outer
    center._inner = None
    center._render = None
    got = _c.Center._route_send(center, "center-pulse", "نباید برود", cfg=CFG)
    assert got is None and not outer.sent, outer.sent


# ── ۴) خانه: هر دکمهٔ ساخته‌شده handler دارد ────────────────────────────────
def t_every_home_button_verb_is_dispatched_in_the_center_router():
    """درسِ tr/iv: دکمهٔ بی‌handler = کارتِ مرده. سنجشِ AST روی همان سورس."""
    import ast
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    tree = ast.parse(src)
    emitted = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "callback_data"
                        and isinstance(v, ast.Constant)
                        and isinstance(v.value, str)
                        and v.value.startswith("hm:")):
                    emitted.add(v.value.split(":", 1)[1])
    assert emitted, "هیچ دکمهٔ hm ساخته نمی‌شود — الگوی اسکن کهنه شده"
    handled = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left = node.left
            if isinstance(left, ast.Name) and left.id == "verb":
                for comp in node.comparators:
                    if isinstance(comp, ast.Constant):
                        handled.add(comp.value)
    assert "hm" in handled, "hm در _handle_callback ِ مرکز dispatch نمی‌شود"
    # و هر زیرفعلِ ساخته‌شده در _handle_home_callback شاخه دارد.
    for sub in emitted:
        assert sub in handled or f'"{sub}"' in src.split("_handle_home_callback")[1][:3000], \
            f"hm:{sub} ساخته می‌شود ولی شاخه ندارد"


def t_the_home_keyboard_never_exceeds_three_decision_points():
    """قانونِ ADHD: حداکثر ۳ دکمه. دکمهٔ چهارم = تصمیمِ چهارم = گیجی."""
    import center as _c
    center = _c.Center.__new__(_c.Center)
    kb = _c.Center._home_keyboard(center)
    n = sum(len(row) for row in kb)
    assert n <= 3, f"{n} دکمه — سقف ۳ است"
    for row in kb:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64, b


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_route_seam: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
