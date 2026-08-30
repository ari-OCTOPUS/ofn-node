r"""
killswitch.py — چک‌لیست #۲: کلید قطع فوری (circuit breaker).

دو راه برای توقف فوریِ کل سیستم:
  ۱) برنامه‌ای: ks.trip("reason") از داخل کد (مثلاً supervisor یا budget).
  ۲) دستی/انسانی: ساختن فایل  logs/STOP  از بیرون → سیستم در گام بعدی متوقف می‌شود.
     مثال:   touch logs/STOP      (یا در ویندوز: echo. > logs\STOP)

هر مؤلفه قبل از اقدام، ks.check() را صدا می‌زند؛ اگر tripped باشد، KillSwitchError
پرتاب و کل اجرا آنی متوقف می‌شود.
"""
from __future__ import annotations
import os


class KillSwitchError(Exception):
    pass


class KillSwitch:
    def __init__(self, stop_file: str):
        self.stop_file = stop_file
        self._tripped = False
        self._reason = ""

    def trip(self, reason: str) -> None:
        self._tripped = True
        self._reason = reason

    @property
    def is_tripped(self) -> bool:
        # کلید نرم‌افزاری یا وجود فایل STOP (کلید انسانیِ بیرونی)
        if self._tripped:
            return True
        if os.path.exists(self.stop_file):
            self._reason = "فایل STOP توسط انسان ساخته شد"
            self._tripped = True
            return True
        return False

    def check(self) -> None:
        """قبل از هر اقدام حساس صدا زده می‌شود."""
        if self.is_tripped:
            raise KillSwitchError(f"⛔ KILL-SWITCH فعال شد: {self._reason}")

    def reset(self) -> None:
        self._tripped = False
        self._reason = ""
        if os.path.exists(self.stop_file):
            os.remove(self.stop_file)
