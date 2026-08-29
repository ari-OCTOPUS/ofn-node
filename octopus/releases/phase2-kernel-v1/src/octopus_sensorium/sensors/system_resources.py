"""Host resource sensor. Reads /proc and df. Never invents values."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult


def _meminfo() -> dict[str, int]:
    out: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, raw = line.split(":", 1)
        parts = raw.split()
        out[key] = int(parts[0])
    return out


def _cpu_percent(sample_proc_stat: str | None = None) -> dict[str, float]:
    # Snapshot only; percent requires two samples and is computed by the plugin loop.
    line = (sample_proc_stat or Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0]).split()
    values = [int(x) for x in line[1:]]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    total = sum(values)
    return {"idle": float(idle), "total": float(total)}


def read_resources() -> dict:
    mem = _meminfo()
    total = mem["MemTotal"]
    available = mem.get("MemAvailable", mem.get("MemFree", 0))
    used_pct = (total - available) * 100.0 / total if total else 0.0
    load1, load5, load15 = Path("/proc/loadavg").read_text(encoding="utf-8").split()[:3]
    st = os.statvfs("/")
    storage_pct = (st.f_blocks - st.f_bfree) * 100.0 / st.f_blocks if st.f_blocks else 0.0
    uptime = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
    cpu = _cpu_percent()
    return {
        "memory_percent": round(used_pct, 2),
        "memory_total_kib": total,
        "memory_available_kib": available,
        "load1": float(load1),
        "load5": float(load5),
        "load15": float(load15),
        "storage_percent": round(storage_pct, 2),
        "uptime_seconds": uptime,
        "cpu_idle": cpu["idle"],
        "cpu_total": cpu["total"],
        "nproc": os.cpu_count() or 0,
    }


class SystemResourcesSensor(BaseSensor):
    sensor_type = "system_resources"
    capabilities = {"cpu_load", "memory_percent", "storage_percent", "uptime"}

    async def discover(self) -> DiscoveryResult:
        present = Path("/proc/meminfo").exists() and Path("/proc/stat").exists()
        return DiscoveryResult(present=present, details={"source": "/proc"})

    async def self_test(self) -> SelfTestResult:
        sample = read_resources()
        ok = 0 <= sample["memory_percent"] <= 100 and 0 <= sample["storage_percent"] <= 100
        return SelfTestResult(passed=ok, message="proc/fs readable" if ok else "range fail", measurements=sample)

    async def observe(self) -> AsyncIterator[RawObservation]:
        sample = read_resources()
        payload = {"sequence": self.next_sequence(), **sample}
        yield RawObservation(payload=payload, source_id="procfs", bytes_len=len(str(payload)))
