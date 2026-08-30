"""test_ease_live_strip_20260816 — نوار زندهٔ additive روی CONTROL-PANEL.

JSON ژوئیه پاک نمی‌شود (C-032). فقط یک نوار می‌گوید validator امروز را
از این صفحه نخوان.

ثبت در run_all.py نشده (WORKLOCK).
"""
from pathlib import Path

DASH = Path(__file__).resolve().parents[2] / "01 - Dashboard" / "CONTROL-PANEL.html"


def test_live_strip_present_and_july_json_untouched():
    text = DASH.read_text(encoding="utf-8")
    assert 'id="LIVE-STRIP"' in text
    assert "validator امروز را از این صفحه نخوان" in text
    assert "validate_frontmatter.py" in text
    assert "51-WEBPANEL-REALITY-2026-08-16" in text
    assert 'id="FROZEN-COCKPIT-BANNER"' in text
    # اسنپ‌شات ژوئیه نباید با جعل عدد «درست» شود
    assert "2026-07-05" in text
