"""تنظیمِ محیطِ تست.

فقط دو کار می‌کند:
  ۱. ریشه‌ی پروژه را به sys.path اضافه می‌کند.
  ۲. برای وابستگی‌های غایبِ محیطِ تست (dotenv/httpx) stub می‌سازد —
     فقط در محیطی که نصب نیستند؛ روی ماشینِ اصلی همان پکیج‌های واقعی load می‌شوند.

هیچ تغییری در کدِ اصلی نمی‌دهد.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _stub(name: str, **attrs) -> None:
    """اگر ماژول واقعی موجود بود هیچ کاری نکن؛ وگرنه stub حداقلی بساز."""
    try:
        __import__(name)
        return
    except Exception:
        m = types.ModuleType(name)
        for k, v in attrs.items():
            setattr(m, k, v)
        sys.modules[name] = m


_stub("dotenv", load_dotenv=lambda *a, **k: False)
_stub("httpx")  # فقط برای importِ ماژول‌های llm؛ هیچ تستی تماسِ شبکه‌ای ندارد
