
import os, time
from pathlib import Path

STATES = ("BOOTSTRAP","OBSERVING","STABLE","DEGRADED","SAFE_HALT","RECOVERING")
MEM_AVAILABLE_DANGER_KB = 350 * 1024
THERMAL_CRITICAL_MC = 115000
THERMAL_DANGER_MARGIN_MC = 10000
DISK_FREE_DANGER_BYTES = 1024 * 1024 * 1024

def _read(path, default=None):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default

def measure():
    now = time.time()
    def sig(name, value, unit):
        if value is None:
            return {"name": name, "state": "UNKNOWN", "value": None, "unit": unit, "ts": now}
        return {"name": name, "state": "MEASURED", "value": value, "unit": unit, "ts": now}

    mem = None
    total = None
    swap_total = None
    swap_free = None
    swap_used = None
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":", 1)
        n = int(v.split()[0])
        if k == "MemAvailable":
            mem = n
        elif k == "MemTotal":
            total = n
        elif k == "SwapTotal":
            swap_total = n
        elif k == "SwapFree":
            swap_free = n
    try:
        if swap_total is not None and swap_free is not None:
            swap_used = swap_total - swap_free
    except Exception:
        swap_used = None
    psi_mem = _read("/proc/pressure/memory")
    psi_cpu = _read("/proc/pressure/cpu")
    load = None
    try:
        load = float(Path("/proc/loadavg").read_text().split()[0])
    except Exception:
        pass
    temp = None
    try:
        temp = int(Path("/sys/class/thermal/thermal_zone0/temp").read_text())
    except Exception:
        pass
    disk_free = None
    try:
        st = os.statvfs("/")
        disk_free = st.f_bavail * st.f_frsize
    except Exception:
        pass
    unknown = 0
    signals = [
        sig("MemAvailable_kB", mem, "kB"),
        sig("MemTotal_kB", total, "kB"),
        sig("SwapUsed_kB", swap_used, "kB"),
        sig("memory_psi", psi_mem, "text"),
        sig("cpu_psi", psi_cpu, "text"),
        sig("load1", load, "n"),
        sig("soc_temp_mC", temp, "mC"),
        sig("thermal_critical_mC", THERMAL_CRITICAL_MC, "mC"),
        sig("disk_free_bytes", disk_free, "B"),
    ]
    unknown = sum(1 for s in signals if s["state"] == "UNKNOWN")
    alerts = []
    if mem is not None and mem < MEM_AVAILABLE_DANGER_KB:
        alerts.append("MEMORY_AVAILABLE_DANGER")
    if (
        temp is not None
        and THERMAL_CRITICAL_MC - temp < THERMAL_DANGER_MARGIN_MC
    ):
        alerts.append("THERMAL_DANGER")
    if disk_free is not None and disk_free < DISK_FREE_DANGER_BYTES:
        alerts.append("DISK_FREE_DANGER")
    if unknown >= 4:
        alerts.append("SIGNAL_UNKNOWN_DANGER")

    health = "OBSERVING"
    if "THERMAL_DANGER" in alerts:
        health = "SAFE_HALT"
    elif alerts:
        health = "DEGRADED"
    return {
        "health_state": health,
        "unknown_count": unknown,
        "signals": signals,
        "alerts": alerts,
        "ts": now,
    }

def transition(current, measured_health):
    # pure: no IO
    order = {s:i for i,s in enumerate(STATES)}
    if current not in order:
        current = "BOOTSTRAP"
    if measured_health == "SAFE_HALT":
        return "SAFE_HALT"
    if current == "BOOTSTRAP":
        return "OBSERVING"
    if current == "SAFE_HALT" and measured_health != "SAFE_HALT":
        return "RECOVERING"
    if current == "RECOVERING" and measured_health in ("STABLE","OBSERVING"):
        return "OBSERVING"
    if measured_health == "DEGRADED":
        return "DEGRADED"
    if measured_health == "OBSERVING" and current == "DEGRADED":
        return "RECOVERING"
    return measured_health if measured_health in STATES else current
