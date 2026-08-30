"""
brain/budget.py — سقفِ بودجه‌ی روزانه‌ی تماس‌های LLM (مهارِ هزینه‌ی اجرای ماهانه).

تصمیمِ مالک: اجرای یک‌ماهه‌ی «جسور» با سقفِ ~۱۰۰۰ تماس در روز. چون GLM پلنِ ثابت
است و Ollama محلی/رایگان، سقف روی تماس‌های **ابری** (fugu + glm) اعمال می‌شود؛
تماس‌های محلیِ Ollama نامحدودند. وقتی سقفِ ابری پر شد، router به‌طورِ خودکار به
Ollama (رایگان) یا mock سقوط می‌کند — سیستم متوقف نمی‌شود، فقط ارزان می‌شود.

شمارنده روزانه (به وقتِ محلی) صفر می‌شود و در outputs/llm_budget.json پایدار است.
نوشتنِ اتمیک؛ رقابتِ چند فرایند (daemon + streamlit) بی‌خطر است (شمارشِ best-effort).
"""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

CLOUD_PROVIDERS = frozenset({"fugu", "glm", "langchain"})


def _cap() -> int:
    try:
        return max(0, int(os.getenv("LLM_DAILY_CALL_CAP", "1000")))
    except ValueError:
        return 1000


def _path() -> Path:
    from config.settings import OUTPUT_DIR
    return OUTPUT_DIR / "llm_budget.json"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _load() -> dict:
    p = _path()
    today = _today()
    if not p.exists():
        return {"date": today, "calls": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("date") != today:            # روزِ جدید → صفر
            return {"date": today, "calls": {}}
        if not isinstance(data.get("calls"), dict):
            data["calls"] = {}
        return data
    except Exception as e:
        logger.warning("budget load failed (%s); resetting", e)
        return {"date": today, "calls": {}}


def _save(data: dict) -> None:
    # C2 fix: نوشتنِ اتمیک با guardrail از طریقِ ابزارِ مشترک.
    from brain._io_utils import atomic_write_json
    atomic_write_json(_path(), data, indent=None, ensure_guardrail=True)


def _cloud_calls(data: dict) -> int:
    calls = data.get("calls", {})
    return sum(int(calls.get(k, 0)) for k in CLOUD_PROVIDERS)


def record_call(provider: str) -> None:
    """یک تماسِ انجام‌شده را ثبت می‌کند (هر ارائه‌دهنده جدا؛ Ollama هم برای آمار).

    C2 fix: کلِ load→modify→save داخلِ file_lock اجرا می‌شود تا daemon و
    Streamlit همزمان نتوانند تماس‌ها را double-count یا گم کنند.
    """
    from brain._io_utils import file_lock
    provider = (provider or "unknown").lower()
    with file_lock(_path()):
        data = _load()
        data["calls"][provider] = int(data["calls"].get(provider, 0)) + 1
        _save(data)


def cloud_allowed() -> bool:
    """آیا هنوز زیرِ سقفِ روزانه‌ی تماس‌های ابری هستیم؟ (cap=0 ⇒ ابری خاموش)."""
    cap = _cap()
    if cap <= 0:
        return False
    return _cloud_calls(_load()) < cap


def remaining_cloud() -> int:
    return max(0, _cap() - _cloud_calls(_load()))


def status() -> dict:
    """گزارش برای داشبورد/گزارشِ ارزیابی."""
    data = _load()
    cloud = _cloud_calls(data)
    cap = _cap()
    return {
        "date": data.get("date", _today()),
        "cap": cap,
        "cloud_calls": cloud,
        "remaining": max(0, cap - cloud),
        "exhausted": cloud >= cap if cap > 0 else True,
        "by_provider": dict(data.get("calls", {})),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("cap:", _cap(), "· cloud_allowed:", cloud_allowed())
    print("status:", status())
