"""test_business_legs_shape.py — P1 (2026-07-15): render._collect_legs هر دو شکلِ
business_legs را می‌پذیرد — تختِ قدیمی و دولایه‌ای که business_legs_beat واقعاً می‌نویسد
(ORGANISM["business_legs"] == {"business_legs": {mining,...}, "beat": N}).
پیش از فیکس، شکلِ دولایه باعث می‌شد هر ۴ پای بیزنس ساکت default رندر شوند."""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness
ENV = harness.setup("business_legs_shape")

import render  # noqa: E402

_LEG = {"leg": "mining", "live": True, "signal": "sig-m", "note": "n-m"}


def t_a_nested_shape_renders():
    """شکلِ واقعیِ organism (دولایه + beat) → پای mining سبز با signal."""
    feeds = {"organism": {"business_legs": {
        "business_legs": {"mining": dict(_LEG)}, "beat": 7}}}
    legs = render._collect_legs(feeds)
    assert legs.get("mining", {}).get("status") == "🟢", legs.get("mining")
    assert "sig-m" in legs["mining"]["detail"]


def t_b_flat_shape_still_works():
    """شکلِ تختِ قدیمی همچنان کار می‌کند (backward-compat)."""
    feeds = {"organism": {"business_legs": {"mining": dict(_LEG)}}}
    legs = render._collect_legs(feeds)
    assert legs.get("mining", {}).get("status") == "🟢", legs.get("mining")


def t_c_absent_is_calm_default():
    """غیاب → پیش‌فرضِ آرام، بدون crash."""
    legs = render._collect_legs({"organism": {}})
    assert isinstance(legs, dict)


if __name__ == "__main__":
    for f in (t_a_nested_shape_renders, t_b_flat_shape_still_works,
              t_c_absent_is_calm_default):
        f()
        print("ok", f.__name__)
    print("PASS test_business_legs_shape")
