"""heartbeat — پالسِ ساعتیِ بورد به مالک (Lane I2، رأی Q7).

اصلِ dead-man-switch: سکوتِ بورد از بیرون دیده می‌شود، نه self-reportِ
«همه‌چیز خوب» وقتی خودش مرده. هر ساعت یک پیامِ کوتاه با سلامتِ واقعی:
آپتایم، دیسک، شمارِ ارسالِ امروز، وضعیت WAL. اگر ۲+ ساعت پیام نیامد،
خودِ مالک در کانال می‌بیند.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402
import owner_notify  # noqa: E402


def _disk_free_pct(path="/") -> int:
    try:
        st = os.statvfs(path)
        return int(100 * st.f_bavail / st.f_blocks)
    except Exception:  # noqa: BLE001
        return -1


def _uptime_s() -> int:
    try:
        # /proc/uptime شکلِ «ثانیه.کیفریز» دارد — اول float، بعد int
        return int(float(Path("/proc/uptime").read_text().split()[0]))
    except Exception:  # noqa: BLE001
        return -1


def _wal_stats() -> str:
    db = Path.home() / "ofn/ofn/agi2027_runtime/outbound-effects.sqlite3"
    try:
        c = sqlite3.connect(db)
        rows = c.execute("SELECT state, COUNT(*) FROM outbound_effects "
                         "GROUP BY state").fetchall()
        c.close()
        return " ".join(f"{s}:{n}" for s, n in rows) or "empty"
    except Exception as e:  # noqa: BLE001
        return f"err:{type(e).__name__}"


def beat() -> dict:
    import outbound_worker
    sends = -1
    try:
        sends = outbound_worker.sends_today()
    except Exception:  # noqa: BLE001
        pass
    disk = _disk_free_pct()
    up = _uptime_s()
    line = (f"💓 بورد زنده — آپتایم {up // 3600}ساعت · دیسک {disk}% آزاد · "
            f"ارسالِ امروز {sends}/10 · WAL {_wal_stats()}")
    res = owner_notify.send(line)
    return {"line": line, "tg": res}


if __name__ == "__main__":
    print(json.dumps(beat(), ensure_ascii=False))
