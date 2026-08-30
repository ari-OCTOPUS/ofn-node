"""Live system metrics for the owner's panel.

These are read-only, always-available, and never trust a single source: if a
thermal zone is missing the reading is `None`, not 0, because 0°C is a real
temperature and a plausible-looking lie is the one failure mode that matters
on a control surface.

Nothing here is cached. The panel polls every 30s; a stale cache would show
a healthy temperature next to a kill switch the owner just pressed, and that
pair is the exact shape of a decision made against the wrong screen.
"""

from __future__ import annotations

import os
from typing import Mapping


_THERMAL_BASE = "/sys/class/thermal"
_PROC_MEMINFO = "/proc/meminfo"
_PROC_LOADAVG = "/proc/loadavg"
_PROC_UPTIME = "/proc/uptime"

# Which thermal zones the panel cares about, by their `type` field. Reading
# by type (not by index) survives kernel re-ordering; the index is not a
# stable contract.
_THERMAL_TYPES = ("soc-thermal", "bigcore0-thermal", "bigcore1-thermal",
                  "gpu-thermal", "npu-thermal")

# Above this the SoC throttles on this board. The panel uses it for colour,
# not for a gate — throttling is a health signal, not an emergency.
_THROTTLE_THRESHOLD_MC = 80_000   # millidegrees


def _read_thermal() -> dict[str, float | None]:
    """Read the named thermal zones. Returns {type: degrees_c or None}.

    A board that lacks a zone (e.g. a different SoC revision) simply gets
    None for it; the panel renders '—' rather than crashing.
    """
    out: dict[str, float | None] = {t: None for t in _THERMAL_TYPES}
    try:
        zones = sorted(os.listdir(_THERMAL_BASE))
    except OSError:
        return out
    for name in zones:
        base = os.path.join(_THERMAL_BASE, name)
        type_path = os.path.join(base, "type")
        temp_path = os.path.join(base, "temp")
        try:
            with open(type_path) as f:
                t = f.read().strip()
            if t not in out:
                continue
            with open(temp_path) as f:
                mc = int(f.read().strip())
            out[t] = round(mc / 1000.0, 1)
        except (OSError, ValueError):
            continue
    return out


def _read_meminfo() -> dict[str, int]:
    """Return bytes for total, available, free."""
    out = {"total_b": 0, "available_b": 0, "free_b": 0}
    try:
        with open(_PROC_MEMINFO) as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    out["total_b"] = int(line.split()[1]) * 1024
                elif line.startswith("MemAvailable:"):
                    out["available_b"] = int(line.split()[1]) * 1024
                elif line.startswith("MemFree:"):
                    out["free_b"] = int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return out


def _read_loadavg() -> tuple[float, float, float] | None:
    try:
        with open(_PROC_LOADAVG) as f:
            parts = f.read().split()
        return float(parts[0]), float(parts[1]), float(parts[2])
    except (OSError, ValueError, IndexError):
        return None


def _read_uptime_s() -> float | None:
    try:
        with open(_PROC_UPTIME) as f:
            return float(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _read_disk(path: str) -> dict[str, int]:
    """Bytes for total, used, free on the filesystem holding `path`."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        return {"total_b": total, "free_b": free,
                "used_b": total - free}
    except OSError:
        return {"total_b": 0, "free_b": 0, "used_b": 0}


def snapshot(state_dir: str = "") -> dict:
    """One read of every metric the panel shows. Always returns a dict with
    every key present, so the panel's renderer has no missing-key branches."""
    thermal = _read_thermal()
    mem = _read_meminfo()
    load = _read_loadavg()
    uptime = _read_uptime_s()
    disk = _read_disk(state_dir) if state_dir else {"total_b": 0, "free_b": 0, "used_b": 0}

    # The hottest zone the board actually has — the one number the owner
    # scans for. None only if every zone failed.
    temps = [v for v in thermal.values() if v is not None]
    hottest = max(temps) if temps else None
    throttling = hottest is not None and hottest * 1000 >= _THROTTLE_THRESHOLD_MC

    return {
        "thermal": thermal,
        "thermal_hottest_c": hottest,
        "throttling": throttling,
        "mem": mem,
        "loadavg": list(load) if load else [],
        "uptime_s": uptime,
        "disk": disk,
    }
