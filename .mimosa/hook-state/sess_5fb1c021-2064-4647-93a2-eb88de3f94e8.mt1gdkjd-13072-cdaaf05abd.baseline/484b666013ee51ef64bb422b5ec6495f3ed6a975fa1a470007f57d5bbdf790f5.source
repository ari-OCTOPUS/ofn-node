"""loop.py — ``tick(beat)``: نقطهٔ اتصالِ زیر-OSِ Mining به heartbeatِ اختاپوس.

هم‌الگویِ ``ziman_os.loop.tick`` / ``pf_os.bridge_beat``: خودبسنده و fail-soft —
state را می‌خواند، ``mining_beat`` را می‌سازد، snapshot را می‌نویسد، و **هرگز crash نمی‌کند**
(زیرـOS نباید tickِ ارگانیسم را بکشد). با فلگ خاموش اصلاً صدا زده نمی‌شود.
"""
from __future__ import annotations

from pathlib import Path

from .core import mining_beat
from .state import load_state, save_state

_PKG = Path(__file__).resolve().parent
_STATE_DIR = _PKG / "state"
_STATE_FILE = _STATE_DIR / "MINING-STATE.json"     # منبعِ حقیقت (اختیاری؛ نبود → skeleton)
_SNAPSHOT = _STATE_DIR / "last-beat.json"           # خروجیِ هر tick (fail-soft)


def tick(beat: int = 0) -> dict:
    """یک ضربانِ فقط‌خواندنی. state را می‌خواند، snapshot می‌نویسد، dict برمی‌گرداند. هرگز استثنا."""
    try:
        state = load_state(_STATE_FILE)          # None اگر فایل نبود → skeleton صادق
        snap = mining_beat(state)
        snap["beat"] = beat
        save_state(_SNAPSHOT, snap)              # اتمیک؛ در مسیرِ read-only بی‌صدا False
        return snap
    except Exception:  # noqa: BLE001 — زیرـOS نباید heartbeat را بکشد
        return {"leg": "mining", "live": False, "signal": "skeleton",
                "beat": beat, "note": "loop.tick fail-soft"}
