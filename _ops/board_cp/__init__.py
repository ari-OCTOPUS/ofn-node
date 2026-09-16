"""board_cp — Control Plane ویندوز برای فرمانِ board-pull به برد.

وب‌اپ/چت/پنل فقط enqueue می‌کنند. برد با Bearer از این‌جا می‌کشد.
ویندوز هرگز به :8796 یا /api/* برد POST نمی‌زند.

فلگ پیش‌فرض خاموش: OCTOPUS_BOARD_CP=0
"""
from __future__ import annotations

FLAG = "OCTOPUS_BOARD_CP"

__all__ = ["FLAG"]
