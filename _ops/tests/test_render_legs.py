#!/usr/bin/env python3
"""test_render_legs.py — WP-D: سطحی‌سازیِ پاهای زندهٔ تاریک روی داشبوردِ مرکزِ تلگرام.

اثبات می‌کند (فقط‌خواندنی، بدونِ شبکه/دیسک/سرور):
  * LEG-07 رفع شد: render._collect_legs حالا ORGANISM-STATE["ziman"] را می‌خواند →
    پای زندهٔ زیمان دیگر ⚪ (تاریک) نیست و money_link/شمارش‌هایش دیده می‌شود.
  * ۴ پای بیزنسِ تازه (mining/crypto/accounting/knowledge) از
    ORGANISM-STATE["business_legs"] سطحی می‌شوند — چه dict-به-نام چه list.
  * skeleton (live=False) note ِ صادقش را نشان می‌دهد نه پیش‌فرضِ خالی.
  * غیابِ کاملِ state → پیش‌فرضِ آرام (بدونِ crash) و LEGS دست‌نخورده (۹ کلید).
  * render_leg_digest سیگنالِ زنده را در متنِ HTML بازتاب می‌دهد.

هیچ مسیرِ زنده لمس نمی‌شود: feed دستی ساخته می‌شود، هیچ collect_feeds/organism اجرا نمی‌شود.
اجرا: python -X utf8 test_render_legs.py
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "telegram_center", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import render  # noqa: E402


def _feeds(organism: dict | None) -> dict:
    """feedِ حداقلی: فقط organism پر است؛ بقیه خالی (fail-soft)."""
    f = {k: {} for k in render.FEED_KEYS}
    if organism is not None:
        f["organism"] = organism
    return f


def test_ziman_live_not_dark() -> None:
    """ORGANISM-STATE["ziman"] موجود → پای زیمان دیگر تاریک نیست + جزئیاتش دیده می‌شود."""
    org = {"ziman": {"money_link": "active", "drafts_count": 3,
                     "proposals_total": 7, "inventory_hint": "۵ قلم آمادهٔ لیست"}}
    legs = render._collect_legs(_feeds(org))
    zi = legs["ziman"]
    assert zi["status"] == "🟢", zi                       # active → سبز، نه ⚪
    assert zi["status"] != render._LEG_DEFAULT["status"]  # قطعاً تاریک نیست
    assert "active" in zi["detail"] and "3" in zi["detail"] and "7" in zi["detail"], zi
    assert zi.get("next") == "۵ قلم آمادهٔ لیست", zi
    # سطحِ نمایش: متنِ digest واقعاً سیگنال را نشان می‌دهد
    txt = render.render_leg_digest("ziman", zi)
    assert "active" in txt and "🟢" in txt, txt


def test_ziman_incubating_is_amber_not_dark() -> None:
    """money_link=incubating ولی زنده → 🟡 (زنده اما پول‌نخفته)، نه ⚪."""
    org = {"ziman": {"money_link": "incubating", "drafts_count": 0, "proposals_total": 0}}
    legs = render._collect_legs(_feeds(org))
    assert legs["ziman"]["status"] == "🟡", legs["ziman"]
    assert legs["ziman"]["status"] != render._LEG_DEFAULT["status"]


def test_business_legs_dict_shape() -> None:
    """business_legs به‌صورتِ dict-به-نام → mining/crypto سطحی می‌شوند."""
    org = {"business_legs": {
        "mining": {"leg": "mining", "live": True, "signal": "۲ ریگ فعال", "note": "hashrate ok"},
        "crypto": {"leg": "crypto", "live": True, "signal": "پرتفوی سبز", "note": ""},
    }}
    legs = render._collect_legs(_feeds(org))
    assert legs["mining"]["status"] == "🟢", legs["mining"]
    assert legs["mining"]["detail"] == "۲ ریگ فعال", legs["mining"]
    assert legs["mining"].get("next") == "hashrate ok", legs["mining"]
    assert legs["crypto"]["status"] == "🟢", legs["crypto"]
    assert legs["crypto"]["detail"] == "پرتفوی سبز", legs["crypto"]


def test_business_legs_list_shape() -> None:
    """business_legs به‌صورتِ list → همان سطحی‌سازی (fail-soft روی هر دو شکل)."""
    org = {"business_legs": [
        {"leg": "accounting", "live": True, "signal": "تطبیق تا امروز", "note": ""},
        {"leg": "knowledge", "live": True, "signal": "۱۲ نوت تازه", "note": ""},
    ]}
    legs = render._collect_legs(_feeds(org))
    assert legs["accounting"]["status"] == "🟢" and legs["accounting"]["detail"] == "تطبیق تا امروز"
    assert legs["knowledge"]["status"] == "🟢" and legs["knowledge"]["detail"] == "۱۲ نوت تازه"


def test_business_leg_skeleton_shows_note_not_blank() -> None:
    """skeleton (live=False) → detail ِ صادق، نه پیش‌فرضِ «سیگنالِ زنده‌ای نیست».

    2026-08-10: mining leg skeleton وقتی mining_card موجود است، digest_detail
    می‌سازد که از note صادقانه‌تر است. تست باید بررسی کند که detail دقیقاً یکی
    از دو مقدارِ مجاز و مستند است: (۱) note (وقتی mining_card غایب)، یا
    (۲) خروجیِ واقعیِ mining_card.digest_detail. نه هر متنی که «خاموش» دارد."""
    note = "skeleton — no data source wired yet؛ نیازمندِ business-spec از مالک."
    org = {"business_legs": {
        "mining": {"leg": "mining", "live": False, "signal": "skeleton", "note": note},
    }}
    legs = render._collect_legs(_feeds(org))
    assert legs["mining"]["status"] == "⚪", legs["mining"]          # صادقانه تاریک
    detail = legs["mining"]["detail"]
    assert detail and detail != render._LEG_DEFAULT["detail"], \
        f"detail نباید خالی یا پیش‌فرض باشد: {detail}"
    # detail باید دقیقاً note باشد، یا خروجیِ mining_card.digest_detail.
    # هر دو مسیر را مستند کنیم و bå از یکدیگر متمایز:
    import sys as _sys
    _legs_p = str(render._OPS / "legs")
    if _legs_p not in _sys.path:
        _sys.path.insert(0, _legs_p)
    try:
        import importlib
        _mc = importlib.import_module("mining_card")
        expected_card = _mc.digest_detail(live=False, signal="skeleton")
    except Exception:
        expected_card = None  # mining_card غایب → detail باید note باشد
    if expected_card:
        assert detail == expected_card, \
            f"detail باید mining_card.digest_detail باشد: got={detail!r} expected={expected_card!r}"
    else:
        assert detail == note, \
            f"mining_card غایب، detail باید note باشد: got={detail!r}"
    assert legs["mining"].get("next") is None, legs["mining"]


def test_absent_state_safe_default_no_crash() -> None:
    """غیابِ کاملِ organism → همهٔ ۹ پا پیش‌فرضِ آرام؛ هیچ crash؛ LEGS دست‌نخورده."""
    for organism in (None, {}, {"business_legs": "garbage"}, {"ziman": 123}):
        legs = render._collect_legs(_feeds(organism if isinstance(organism, dict) else None)
                                    if organism is not None else _feeds(None))
        # ziman و ۴ پای بیزنس همه پیش‌فرض می‌مانند (هیچ سیگنالِ زنده‌ای تزریق نشده)
        for k in ("ziman", "mining", "crypto", "accounting", "knowledge"):
            assert legs[k]["status"] == render._LEG_DEFAULT["status"], (k, legs[k])
    # قراردادِ نام‌ها دست‌نخورده. ۲۰۲۶-۰۷-۲۷: عددِ خام (۹) با افزودنِ اتاقِ آینه
    # کهنه شد. آنچه واقعاً باید بماند این است که `_collect_legs` و `LEGS` **یک
    # مجموعه** باشند — وگرنه یا پایی بی‌نام می‌ماند یا نامی بی‌داده.
    assert set(legs.keys()) == set(render.LEGS.keys()), \
        set(legs.keys()) ^ set(render.LEGS.keys())


def test_partial_business_legs_only_named_surface() -> None:
    """فقط پاهای شناخته‌شده سطحی می‌شوند؛ کلیدِ ناشناس نادیده و بقیه پیش‌فرض."""
    org = {"business_legs": {
        "mining": {"leg": "mining", "live": True, "signal": "on"},
        "bogus": {"leg": "bogus", "live": True, "signal": "should be ignored"},
    }}
    legs = render._collect_legs(_feeds(org))
    assert legs["mining"]["status"] == "🟢"
    assert legs["crypto"]["status"] == render._LEG_DEFAULT["status"]   # لمس نشده
    assert "bogus" not in legs                                          # کلیدِ خارج از LEGS اضافه نمی‌شود


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_render_legs: {len(_tests)}/{len(_tests)} سبز")
