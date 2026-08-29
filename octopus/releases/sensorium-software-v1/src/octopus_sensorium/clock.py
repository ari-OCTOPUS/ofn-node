"""Clock trust. RTC invalidity is a first-class observation, not a silent guess."""

from __future__ import annotations

import pathlib
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

ClockTrust = Literal["UNTRUSTED", "MONOTONIC_ONLY", "SYNCED_NTP", "SYNCED_PTP"]

TIMESYNC_STAMP = pathlib.Path("/run/systemd/timesync/synchronized")
RTC_DEVICE = pathlib.Path("/dev/rtc0")
RTC_NAME = pathlib.Path("/sys/class/rtc/rtc0/name")


@dataclass(frozen=True)
class ClockStatus:
    clock_trust: ClockTrust
    ntp_synchronised: bool
    rtc_valid: bool
    rtc_battery_present: str
    monotonic_available: bool
    max_acceptable_offset_ms: int
    utc_now: str
    rtc_name: str

    def as_dict(self) -> dict:
        return {
            "clock_trust": self.clock_trust,
            "ntp_synchronised": self.ntp_synchronised,
            "rtc_valid": self.rtc_valid,
            "rtc_battery_present": self.rtc_battery_present,
            "monotonic_available": self.monotonic_available,
            "max_acceptable_offset_ms": self.max_acceptable_offset_ms,
            "utc_now": self.utc_now,
            "rtc_name": self.rtc_name,
        }


def _timesyncd_running() -> bool:
    procs = pathlib.Path("/sys/fs/cgroup/system.slice/systemd-timesyncd.service/cgroup.procs")
    try:
        if procs.read_text(encoding="utf-8").strip():
            return True
    except OSError:
        pass
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", "systemd-timesyncd"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return proc.stdout.strip() == "active"
    except (OSError, subprocess.SubprocessError):
        return False


def _ntp_synchronised() -> bool:
    if not _timesyncd_running():
        return False
    if TIMESYNC_STAMP.exists():
        return True
    try:
        proc = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return proc.stdout.strip() == "yes"
    except (OSError, subprocess.SubprocessError):
        return False


def _rtc_valid(max_offset_s: float = 5.0) -> bool:
    epoch_path = pathlib.Path("/sys/class/rtc/rtc0/since_epoch")
    try:
        epoch = int(epoch_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    if epoch <= 0:
        return False
    return abs(epoch - time.time()) <= max_offset_s


def probe_clock(max_acceptable_offset_ms: int = 250) -> ClockStatus:
    ntp = _ntp_synchronised()
    rtc_ok = _rtc_valid()
    rtc_name = ""
    try:
        rtc_name = RTC_NAME.read_text(encoding="utf-8").strip()
    except OSError:
        rtc_name = "absent"
    if ntp:
        trust: ClockTrust = "SYNCED_NTP"
    elif pathlib.Path("/proc/uptime").exists():
        trust = "MONOTONIC_ONLY"
    else:
        trust = "UNTRUSTED"
    return ClockStatus(
        clock_trust=trust,
        ntp_synchronised=ntp,
        rtc_valid=rtc_ok,
        rtc_battery_present="unknown",
        monotonic_available=True,
        max_acceptable_offset_ms=max_acceptable_offset_ms,
        utc_now=datetime.now(timezone.utc).isoformat(),
        rtc_name=rtc_name,
    )
