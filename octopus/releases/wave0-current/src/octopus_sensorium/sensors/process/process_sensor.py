"""OCT-SENSE-052 process and service sensor.

Watchlist is mandatory. Never scan-and-publish every PID.
Command lines are not published. Restart is an event, not a gauge.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections import Counter, defaultdict
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from octopus_sensorium.isolation import IsolationViolation, assert_no_pwm_write
from octopus_sensorium.sensors.base import BaseSensor, DiscoveryResult, RawObservation, SelfTestResult, SensorError

PROC = Path("/proc")
SLICE = Path("/sys/fs/cgroup/system.slice")
INVOCATION_DIR = Path("/run/systemd/units")
MAX_OBS_PER_CYCLE = 20

TOKEN_RE = re.compile(r"(?i)(?:token|api[_-]?key)\s*[:=]\s*\S+")
BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")
BCRYPT_RE = re.compile(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{22,}")
URL_CRED_RE = re.compile(r"(?i)://[^/@:\s]+:[^/@\s]+@")

STATE_MAP = {
    "R": "running",
    "S": "sleeping",
    "D": "disk_sleep",
    "T": "stopped",
    "t": "stopped",
    "Z": "zombie",
    "I": "idle",
}


def redact_secret_text(text: str) -> str:
    text = TOKEN_RE.sub("[REDACTED_TOKEN]", text)
    text = BEARER_RE.sub("Bearer [REDACTED]", text)
    text = BCRYPT_RE.sub("[REDACTED_BCRYPT]", text)
    text = URL_CRED_RE.sub("://[REDACTED_CRED]@", text)
    return text


def assert_no_command_line(payload: Any) -> None:
    blob = str(payload).lower()
    for needle in ("command_line", "process.command_line", "process.command_args"):
        if needle in blob:
            raise SensorError("command line must not be published")


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def read_unit(unit: str) -> dict[str, Any]:
    """ActiveState+SubState without D-Bus (board has no system bus)."""
    cg = SLICE / unit
    inv = INVOCATION_DIR / f"invocation:{unit}"
    invocation_id = None
    active_enter = None
    if inv.exists() or inv.is_symlink():
        try:
            invocation_id = os.readlink(inv)
        except OSError:
            invocation_id = None
        try:
            active_enter = int(inv.lstat().st_mtime)
        except OSError:
            active_enter = None
    procs: list[int] = []
    populated = False
    if cg.exists():
        raw_procs = _read_text(cg / "cgroup.procs") or ""
        procs = [int(x) for x in raw_procs.split() if x.strip().isdigit()]
        events = _read_text(cg / "cgroup.events") or ""
        populated = "populated 1" in events or bool(procs)
    if populated and procs:
        active_state, sub_state = "active", "running"
    elif cg.exists() and not procs:
        active_state, sub_state = "active", "exited"
    elif invocation_id:
        active_state, sub_state = "inactive", "dead"
    else:
        active_state, sub_state = "inactive", "dead"
    healthy = active_state == "active" and sub_state == "running"
    return {
        "unit": unit,
        "active_state": active_state,
        "sub_state": sub_state,
        "healthy": healthy,
        "pids": procs,
        "invocation_id": invocation_id,
        "active_enter_timestamp": active_enter,
        "found": bool(cg.exists() or invocation_id),
    }


def _exe_name(pid: int) -> str | None:
    try:
        return Path(os.readlink(f"/proc/{pid}/exe")).name
    except OSError:
        comm = _read_text(Path(f"/proc/{pid}/comm"))
        return comm.strip() if comm else None


def _arg_count(pid: int) -> int:
    raw = Path(f"/proc/{pid}/cmdline").read_bytes() if Path(f"/proc/{pid}/cmdline").exists() else b""
    if not raw:
        return 0
    return len([p for p in raw.split(b"\0") if p])


def _cmdline_bytes(pid: int) -> bytes:
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return b""


def _stat_fields(pid: int) -> tuple[str, int, int, int] | None:
    raw = _read_text(Path(f"/proc/{pid}/stat"))
    if not raw:
        return None
    rparen = raw.rfind(")")
    rest = raw[rparen + 2 :].split()
    if len(rest) < 22:
        return None
    state = rest[0]
    utime = int(rest[11])
    stime = int(rest[12])
    starttime = int(rest[19])
    return state, utime + stime, starttime, pid


def _status_map(pid: int) -> dict[str, str]:
    raw = _read_text(Path(f"/proc/{pid}/status")) or ""
    out: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k] = v.strip()
    return out


def _rss_bytes(pid: int) -> int:
    status = _status_map(pid)
    rss = status.get("VmRSS", "0").split()[0]
    try:
        return int(rss) * 1024
    except ValueError:
        return 0


def _threads(pid: int) -> int:
    status = _status_map(pid)
    try:
        return int(status.get("Threads", "1"))
    except ValueError:
        return 1


def _clock_ticks() -> float:
    try:
        return float(os.sysconf("SC_CLK_TCK"))
    except (OSError, ValueError):
        return 100.0


class ProcessSensor(BaseSensor):
    sensor_type = "process"
    capabilities = {
        "unit_state",
        "process_liveness",
        "restart_event",
        "resource_growth",
        "aggregate_process_count",
    }

    def __init__(self, manifest: dict[str, Any]) -> None:
        super().__init__(manifest)
        watch = manifest.get("watchlist") or {}
        self.units = list(watch.get("units") or [])
        self.processes = list(watch.get("processes") or [])
        if not self.units and not self.processes:
            raise SensorError("OCT-SENSE-052 watchlist is empty; refusing full PID scan")
        privacy = manifest.get("privacy") or {}
        self.redact_command_line = privacy.get("redact_command_line", True)
        self.collect_command_args = privacy.get("collect_command_args", False)
        self.collect_environment = privacy.get("collect_environment", False)
        if self.collect_command_args or self.collect_environment:
            raise SensorError("command args and environment collection are forbidden")
        self._prev_invocation: dict[str, str | None] = {}
        self._restart_counts: dict[str, int] = defaultdict(int)
        self._prev_cpu: dict[int, tuple[int, float]] = {}
        self._rss_history: dict[str, list[int]] = defaultdict(list)

    async def discover(self) -> DiscoveryResult:
        found = [read_unit(spec["unit"]) for spec in self.units]
        return DiscoveryResult(
            present=PROC.exists(),
            details={"units_found": [u["unit"] for u in found if u["found"]], "units_missing": [u["unit"] for u in found if not u["found"]]},
        )

    async def self_test(self) -> SelfTestResult:
        units = [read_unit(spec["unit"]) for spec in self.units]
        found = [u["unit"] for u in units if u["found"]]
        missing = [spec["unit"] for spec in self.units if spec["unit"] not in found]
        pwm_ok = True
        pwm_detail = "pwm not writable"
        unit_control_denied = True
        control_detail = "systemctl restart denied"
        if os.geteuid() == 0:
            pwm_detail = "skipped_as_root; agent must run as octopus"
            control_detail = "skipped_as_root; agent must run as octopus"
        else:
            try:
                assert_no_pwm_write()
            except IsolationViolation as exc:
                pwm_ok = False
                pwm_detail = str(exc)
            proc = subprocess.run(
                ["systemctl", "--dry-run", "restart", "nats-server.service"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            unit_control_denied = proc.returncode != 0
            control_detail = proc.stderr.strip() or proc.stdout.strip() or f"rc={proc.returncode}"
        ok = (not missing) and pwm_ok and unit_control_denied
        return SelfTestResult(
            passed=ok,
            message=f"units={found} pwm={pwm_detail} unit_control={control_detail}",
            measurements={"units_found": found, "missing": missing, "pwm_ok": pwm_ok, "unit_control_denied": unit_control_denied},
        )

    def _match_group(self, spec: dict[str, Any]) -> list[int]:
        pattern = re.compile(spec.get("match_executable") or "^$")
        label = spec.get("label") or ""
        matched: list[int] = []
        for entry in PROC.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            name = _exe_name(pid) or ""
            if not pattern.search(name):
                continue
            if label == "sensorium_python":
                cmdline = _cmdline_bytes(pid)
                if b"octopus_sensorium" not in cmdline and pid != os.getpid():
                    continue
            matched.append(pid)
        return matched

    def _cpu_util(self, pid: int, ticks: int) -> float:
        import time

        now = time.monotonic()
        prev = self._prev_cpu.get(pid)
        self._prev_cpu[pid] = (ticks, now)
        if not prev:
            return 0.0
        dt = now - prev[1]
        if dt <= 0:
            return 0.0
        d_ticks = ticks - prev[0]
        return max(0.0, min(1.0, (d_ticks / _clock_ticks()) / dt))

    def _process_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for entry in PROC.iterdir():
            if not entry.name.isdigit():
                continue
            fields = _stat_fields(int(entry.name))
            if not fields:
                continue
            counts[STATE_MAP.get(fields[0], "other")] += 1
        return dict(counts)

    def _observations(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for spec in self.units:
            unit = spec["unit"]
            info = read_unit(unit)
            critical = bool(spec.get("critical"))
            prev_inv = self._prev_invocation.get(unit)
            if prev_inv is not None and info["invocation_id"] and info["invocation_id"] != prev_inv:
                self._restart_counts[unit] += 1
                items.append(
                    {
                        "observed_property": "octopus.unit.restart",
                        "value": {
                            "unit": unit,
                            "invocation_id": info["invocation_id"],
                            "previous_invocation_id": prev_inv,
                            "n_restarts_observed": self._restart_counts[unit],
                        },
                        "unit": "1",
                        "observation_type": "event",
                        "otlp_name": "octopus_unit_restarts_total",
                    }
                )
            if info["invocation_id"]:
                self._prev_invocation[unit] = info["invocation_id"]
            items.append(
                {
                    "observed_property": "octopus.unit.healthy",
                    "value": {
                        "unit": unit,
                        "critical": critical,
                        "active_state": info["active_state"],
                        "sub_state": info["sub_state"],
                        "healthy": 1 if info["healthy"] else 0,
                    },
                    "unit": "1",
                    "observation_type": "measurement",
                    "otlp_name": "octopus_unit_healthy",
                }
            )
            items.append(
                {
                    "observed_property": "octopus.unit.restarts_total",
                    "value": {"unit": unit, "count": self._restart_counts[unit]},
                    "unit": "1",
                    "observation_type": "measurement",
                    "otlp_name": "octopus_unit_restarts_total",
                }
            )
        for spec in self.processes:
            label = spec["label"]
            pids = self._match_group(spec)
            rss = sum(_rss_bytes(pid) for pid in pids)
            threads = sum(_threads(pid) for pid in pids)
            cpu = 0.0
            for pid in pids:
                fields = _stat_fields(pid)
                if fields:
                    cpu = max(cpu, self._cpu_util(pid, fields[1]))
            in_range = 1
            if spec.get("minimum_count") is not None and len(pids) < int(spec["minimum_count"]):
                in_range = 0
            if spec.get("maximum_count") is not None and len(pids) > int(spec["maximum_count"]):
                in_range = 0
            exe = _exe_name(pids[0]) if pids else spec.get("match_executable")
            published = {
                "process.executable.name": exe,
                "process.arg_count": _arg_count(pids[0]) if pids else 0,
                "group": label,
            }
            items.append(
                {
                    "observed_property": "process.cpu.utilization",
                    "value": {"utilization": round(cpu, 4), **published},
                    "unit": "1",
                    "observation_type": "measurement",
                    "otlp_name": "process.cpu.utilization",
                }
            )
            items.append(
                {
                    "observed_property": "process.memory.usage",
                    "value": {"usage_bytes": rss, **published},
                    "unit": "By",
                    "observation_type": "measurement",
                    "otlp_name": "process.memory.usage",
                }
            )
            items.append(
                {
                    "observed_property": "process.thread.count",
                    "value": {"count": threads, **published},
                    "unit": "1",
                    "observation_type": "measurement",
                    "otlp_name": "process.thread.count",
                }
            )
            items.append(
                {
                    "observed_property": "octopus.process.group.count",
                    "value": {"group": label, "count": len(pids), "in_range": in_range},
                    "unit": "1",
                    "observation_type": "measurement",
                    "otlp_name": "octopus_process_group_count",
                }
            )
            history = self._rss_history[label]
            history.append(rss)
            self._rss_history[label] = history[-8:]
            if len(history) >= 3 and history[0] > 0 and rss > history[0] * 1.25:
                items.append(
                    {
                        "observed_property": "octopus.process.memory_growth",
                        "value": {
                            "group": label,
                            "from_bytes": history[0],
                            "to_bytes": rss,
                            "kind": "HYPOTHESIS",
                        },
                        "unit": "By",
                        "observation_type": "event",
                        "hypothesis": True,
                        "otlp_name": "process.memory.usage",
                    }
                )
        counts = self._process_counts()
        items.append(
            {
                "observed_property": "system.process.count",
                "value": counts,
                "unit": "1",
                "observation_type": "measurement",
                "otlp_name": "system.process.count",
            }
        )
        if len(items) > MAX_OBS_PER_CYCLE:
            items = items[:MAX_OBS_PER_CYCLE]
        for item in items:
            assert_no_command_line(item)
            item["value"] = _scrub_value(item["value"])
        return items

    async def observe(self) -> AsyncIterator[RawObservation]:
        items = self._observations()
        payload = {"sequence": self.next_sequence(), "observations": items, "count": len(items)}
        assert_no_command_line(payload)
        yield RawObservation(payload=payload, source_id="procfs_and_systemd", bytes_len=len(str(payload)))


def _scrub_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _scrub_value(v) for k, v in value.items() if k not in {"command_line", "command_args", "environ"}}
    if isinstance(value, str):
        return redact_secret_text(value)
    if isinstance(value, list):
        return [_scrub_value(v) for v in value]
    return value
