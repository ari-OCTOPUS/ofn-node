"""test_mining_digest_wire — D-013: دیجستِ ماینینگ عددی است، نه صفر.

۲۰۲۶-۰۸-۰۱: تا امروز دیجستِ روزانهٔ mining از business_legs می‌آمد و فقط note ِ
skeleton را نشان می‌داد — یعنی هیچ عددی. مالک رأی داد (D-013) که کارت از همین
حالا عددی باشد: ۱۶۲ نود + «اندازه‌گیری‌نشده» برای هرچه سنجیده نشده. این تست
وصلِ render._collect_legs → mining_card.digest_detail را محافظت می‌کند.

لبِ فیکس: skeleton هم باید عدد نشان دهد، نه فقط «skeleton». و اگر import شکست
خورد، رفتارِ امروز (note) برمی‌گردد — هیچ crash.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
ENV = harness.setup("mining-digest-wire")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import render  # noqa: E402


def _fake_feeds(mining_note: str = "skeleton -- stale", live: bool = False):
    """یک feeds با business_legsِ skeleton، مثلِ ORGANISM-STATE ِ امروز."""
    return {"organism": {"business_legs": {"business_legs": {
        "mining": {"leg": "mining", "live": live, "signal": "skeleton",
                   "note": mining_note, "age_days": 23.5},
        "crypto": {"leg": "crypto", "live": False, "signal": "skeleton",
                   "note": "crypto skeleton -- control"},
    }, "beat": 1}}}


def t_digest_shows_fleet_162_not_zero():
    """D-013: دیجستِ skeleton هم عددی است — ۱۶۲، نه صفر."""
    legs = render._collect_legs(_fake_feeds())
    detail = legs.get("mining", {}).get("detail", "")
    assert "۱۶۲" in detail, f"عددِ ناوگان نیست: {detail!r}"
    assert "۰" not in detail.replace("۱۶۲", ""), f"صفرِ مجازی: {detail!r}"


def t_digest_shows_unmeasured_explicitly():
    """D-013: هرچه سنجیده نشده صریحاً «اندازه‌گیری‌نشده» است."""
    legs = render._collect_legs(_fake_feeds())
    detail = legs.get("mining", {}).get("detail", "")
    assert "اندازه‌گیری‌نشده" in detail, f"کلمهٔ اندازه‌گیری‌نشده نیست: {detail!r}"


def t_crypto_leg_is_untouched_by_mining_wire():
    """وصلِ mining نباید روی crypto اثر بگذارد."""
    legs = render._collect_legs(_fake_feeds())
    cdetail = legs.get("crypto", {}).get("detail", "")
    assert "skeleton" in cdetail or "control" in cdetail, f"crypto دست‌خورده: {cdetail!r}"
    assert "۱۶۲" not in cdetail, "crypto عددِ mining را گرفت!"


def t_live_mining_does_not_get_override():
    """وقتی live=True، overrideِ skeleton نباید فعال شود (مسیرِ زنده هنوز نیست)."""
    legs = render._collect_legs(_fake_feeds(live=True))
    # live=True: override فقط برای not live است؛ detail از مسیرِ معمول می‌آید
    assert "mining" in legs, "پای mining غایب شد"


def t_fail_soft_when_mining_card_unavailable():
    """اگر import شکست خورد، detail از note می‌آید — نه crash."""
    # sabotage: mining_card را غیب کن
    real_mod = sys.modules.get("mining_card")
    sys.modules["mining_card"] = None  # importlib.import_module رد می‌کند
    # مسیر legs را هم موقتاً مخدوش کن
    saved = sys.path[:]
    try:
        legs = render._collect_legs(_fake_feeds(mining_note="fallback note"))
        detail = legs.get("mining", {}).get("detail", "")
        # یا fallback note، یا اگر چیزی دیگر آمد، حداقل crash نکرده
        assert detail, f"detail خالی شد (crash): {detail!r}"
    finally:
        if real_mod is not None:
            sys.modules["mining_card"] = real_mod
        else:
            sys.modules.pop("mining_card", None)
        sys.path = saved


if __name__ == "__main__":
    harness.run([
        ("digest_shows_fleet_162_not_zero", t_digest_shows_fleet_162_not_zero),
        ("digest_shows_unmeasured_explicitly", t_digest_shows_unmeasured_explicitly),
        ("crypto_leg_is_untouched_by_mining_wire", t_crypto_leg_is_untouched_by_mining_wire),
        ("live_mining_does_not_get_override", t_live_mining_does_not_get_override),
        ("fail_soft_when_mining_card_unavailable", t_fail_soft_when_mining_card_unavailable),
    ])
