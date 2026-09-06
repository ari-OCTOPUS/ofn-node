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
import time
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


def _doctor_summary(report_path: Path | None = None) -> str:
    """خلاصهٔ report.json دکتر برای خط پالس — مصرف‌کنندهٔ نهاییِ گزارش دکتر.
    غایب/کهنه/خراب = برچسب صادقانه؛ هرگز «سالم» حدسی."""
    p = report_path or (
        Path.home() / "ofn/data/state/doctor/report.json")
    try:
        import datetime as _dt
        r = json.loads(p.read_text(encoding="utf-8"))
        gen = _dt.datetime.fromisoformat(
            r["generated_at"].replace("Z", "+00:00")).timestamp()
        age_h = (time.time() - gen) / 3600.0
        if age_h > 2.5:
            return f"دکتر:کهنه({age_h:.0f}h)"
        v = r.get("verdict", "unknown")
        if v == "healthy":
            return "دکتر:سبز"
        n_un = len(r.get("unprobed", {}).get("names", [])) \
            + len(r.get("unknown", {}).get("names", []))
        un = [m["name"] for m in r.get("measurements", [])
              if m.get("verdict") == "unhealthy"]
        tail = f" · {','.join(un[:2])}" if un else \
            (f" · {n_un} blind" if n_un else "")
        return f"دکتر:{v}{tail}"
    except (OSError, ValueError, KeyError):
        return "دکتر:بدون-گزارش"


def beat() -> dict:
    import outbound_worker
    sends = -1
    try:
        sends = outbound_worker.sends_today()
    except Exception:  # noqa: BLE001
        pass
    # سقف را از worker بخوان، نه عددِ ثابتِ نمایش: override محیطی
    # (OCTOPUS_LEAD_DAILY_SEND_CAP) باید در همین خط دیده شود؛ ≤0 = بی‌سقف.
    cap_txt = "?"
    try:
        cap = outbound_worker._lead_daily_send_cap()
        cap_txt = "∞" if cap <= 0 else str(cap)
    except Exception:  # noqa: BLE001
        pass
    disk = _disk_free_pct()
    up = _uptime_s()
    line = (f"💓 بورد زنده — آپتایم {up // 3600}ساعت · دیسک {disk}% آزاد · "
            f"ارسالِ امروز {sends}/{cap_txt} · WAL {_wal_stats()} · "
            f"{_doctor_summary()}")
    res = owner_notify.send(line)
    return {"line": line, "tg": res}


if __name__ == "__main__":
    print(json.dumps(beat(), ensure_ascii=False))
