"""تست چک‌لیست #۲: کلید قطع باید آنی متوقف کند."""
import pytest
from src.killswitch import KillSwitch, KillSwitchError


def test_software_trip():
    ks = KillSwitch(stop_file="logs/STOP_test")
    ks.check()                       # ابتدا سالم
    ks.trip("تست")
    with pytest.raises(KillSwitchError):
        ks.check()


def test_external_stop_file(tmp_path):
    stop = tmp_path / "STOP"
    ks = KillSwitch(stop_file=str(stop))
    ks.check()
    stop.write_text("x")             # کلید انسانیِ بیرونی
    with pytest.raises(KillSwitchError):
        ks.check()


def test_reset(tmp_path):
    stop = tmp_path / "STOP"
    ks = KillSwitch(stop_file=str(stop))
    ks.trip("x")
    ks.reset()
    ks.check()                       # بعد از reset دوباره سالم
