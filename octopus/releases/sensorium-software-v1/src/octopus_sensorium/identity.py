"""Stable board identity. Hostname is not an identifier."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

SOC_NAME = "rk3588s"
MODEL_SLUG = "opi5pro"
DEFAULT_MACHINE_ID_PATH = pathlib.Path("/etc/machine-id")
DEFAULT_CPUINFO_PATH = pathlib.Path("/proc/cpuinfo")
DEFAULT_DT_MODEL_PATH = pathlib.Path("/sys/firmware/devicetree/base/model")


@dataclass(frozen=True)
class BoardIdentity:
    board_id: str
    hostname: str
    soc: str
    machine_id: str
    serial: str
    model: str
    agent_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "board_id": self.board_id,
            "hostname": self.hostname,
            "soc": self.soc,
            "machine_id": self.machine_id,
            "serial": self.serial,
            "model": self.model,
            "agent_id": self.agent_id,
        }


def _read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip().strip("\x00")
    except OSError:
        return ""


def read_serial(cpuinfo_path: pathlib.Path = DEFAULT_CPUINFO_PATH) -> str:
    for line in _read_text(cpuinfo_path).splitlines():
        if line.lower().startswith("serial"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def derive_board_id(serial: str, model_slug: str = MODEL_SLUG) -> str:
    token = (serial or "unknown").replace(":", "").lower()
    if len(token) < 8:
        token = (token + "00000000")[:8]
    return f"sensorium-{model_slug}-{token[:8]}"


def load_identity(
    *,
    agent_id: str = "agent://octopus/sensorium-board/main",
    machine_id_path: pathlib.Path = DEFAULT_MACHINE_ID_PATH,
    cpuinfo_path: pathlib.Path = DEFAULT_CPUINFO_PATH,
    model_path: pathlib.Path = DEFAULT_DT_MODEL_PATH,
) -> BoardIdentity:
    serial = read_serial(cpuinfo_path)
    machine_id = _read_text(machine_id_path) or "unknown"
    model = _read_text(model_path) or "Orange Pi 5 Pro"
    return BoardIdentity(
        board_id=derive_board_id(serial),
        hostname=os.uname().nodename,
        soc=SOC_NAME,
        machine_id=machine_id,
        serial=serial,
        model=model,
        agent_id=agent_id,
    )
