"""test_webpanel_reality_20260816.py — قفل برچسب صادق UI (مگاپرامپت WEBPANEL).

قفل می‌کند:
  1) سه کاکپیت ابسیدین بنر اسنپ‌شات دارند و «اجرای زندهٔ validator» نمی‌فروشند
  2) worlds/index استخراجگر را همیشه-قرمز نشان نمی‌دهد
  3) هاب/توپولوژی/ایزومتریک «دادهٔ زندهٔ ارگانیسم» ادعا نمی‌کنند
  4) octo-data.js کتابخانه است نه اسنپ‌شات

ثبت در run_all.py نشده (WORKLOCK).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "01 - Dashboard"
OCTO = ROOT / "OCTOPUS"


def test_cockpit_frozen_banners():
    for name in (
        "CONTROL-PANEL.html",
        "SYSTEM-DASHBOARD.html",
        "BRAIN-FOCUS-BOARD.html",
    ):
        text = (DASH / name).read_text(encoding="utf-8")
        assert "FROZEN-COCKPIT-BANNER" in text, name
        assert "اسنپ‌شات" in text, name


def test_control_panel_does_not_sell_live_validators():
    text = (DASH / "CONTROL-PANEL.html").read_text(encoding="utf-8")
    assert "اجرای زندهٔ validatorها" not in text
    assert "نه اجرای زنده" in text


def test_worlds_extractor_not_always_red():
    text = (OCTO / "worlds" / "index.html").read_text(encoding="utf-8")
    assert "{label:'اکسترکتور', src:null}" not in text
    assert "{label:'اکسترکتور', src:F.live}" in text


def test_flagship_does_not_sell_live_gallery():
    text = (OCTO / "index.html").read_text(encoding="utf-8")
    assert "۳۰ صحنهٔ زنده" not in text
    gal = (OCTO / "gallery-3d" / "index.html").read_text(encoding="utf-8")
    assert "۳۰ صحنهٔ زندهٔ Three.js" not in gal
    assert "۳۰ صحنهٔ مفهومیِ Three.js" in gal
    assert "۳۰ صحنهٔ مفهومی" in text
    assert "دادهٔ زنده را جابه‌جا می‌کنند" not in text


def test_topology_and_isometric_honest():
    topo = (OCTO / "01-topology.html").read_text(encoding="utf-8")
    assert "not live organism telemetry" in topo
    iso = (OCTO / "05-isometric-dashboard.html").read_text(encoding="utf-8")
    assert "synthetic demo" in iso
    d3 = (OCTO / "octopus-3d-topology.html").read_text(encoding="utf-8")
    assert "live data flow" not in d3
    assert "synthetic demo" in d3


def test_octo_data_is_reader_not_snapshot():
    text = (OCTO / "worlds" / "octo-data.js").read_text(encoding="utf-8")
    assert "library, not a snapshot" in text
    assert "window.LIVE_DATA" in text
