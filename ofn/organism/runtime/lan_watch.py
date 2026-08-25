from __future__ import annotations

import ipaddress
import json
import os
import socket
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_ALLOWLIST = Path("/opt/octopus/lab/state/LAN-WATCH-ALLOWLIST.json")
DEFAULT_STATE = Path("/opt/octopus/lab/state/LAN-WATCH.json")
ALLOWED_CIDR = ipaddress.ip_network("192.168.0.0/24")


def load_allowlist(path: Path = DEFAULT_ALLOWLIST) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cidr = ipaddress.ip_network(data.get("lan_cidr", str(ALLOWED_CIDR)))
    if cidr != ALLOWED_CIDR:
        raise ValueError("lan_cidr_must_be_this_board_subnet")
    return data


def validate_ip(raw: str, exclude: set[str] | None = None) -> str:
    addr = ipaddress.ip_address(raw)
    if addr.version != 4 or addr not in ALLOWED_CIDR:
        raise ValueError(f"ip_not_on_local_lan:{raw}")
    if addr.is_multicast or addr.is_unspecified or str(addr).endswith(".255"):
        raise ValueError(f"ip_not_probeable:{raw}")
    if exclude and str(addr) in exclude:
        raise ValueError(f"ip_excluded:{raw}")
    return str(addr)


def self_ipv4s() -> set[str]:
    found: set[str] = set()
    try:
        out = subprocess.run(
            ["/usr/bin/hostname", "-I"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        for token in out.stdout.split():
            try:
                addr = ipaddress.ip_address(token)
            except ValueError:
                continue
            if addr.version == 4:
                found.add(str(addr))
    except (OSError, subprocess.TimeoutExpired):
        found.add("192.168.0.180")
    if not found:
        found.add("192.168.0.180")
    return found


def allowed_targets(allowlist: dict[str, Any]) -> list[dict[str, Any]]:
    exclude = self_ipv4s() if allowlist.get("exclude_self", True) else set()
    targets = []
    for item in allowlist.get("targets") or []:
        ip = validate_ip(str(item["ip"]), exclude)
        ports = []
        for port in item.get("ports") or []:
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError(f"invalid_port:{port}")
            ports.append(port)
        if len(ports) > 4:
            raise ValueError("too_many_ports")
        targets.append(
            {
                "id": str(item["id"]),
                "ip": ip,
                "icmp": bool(item.get("icmp", True)),
                "ports": ports,
                "label": str(item.get("label") or item["id"]),
            }
        )
    return targets


def ping_host(ip: str, timeout_s: int = 1) -> bool:
    validate_ip(ip)
    try:
        result = subprocess.run(
            ["/bin/ping", "-c", "1", "-W", str(int(timeout_s)), ip],
            check=False,
            capture_output=True,
            timeout=timeout_s + 1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def tcp_open(ip: str, port: int, timeout_s: float = 1.0) -> bool:
    validate_ip(ip)
    try:
        with socket.create_connection((ip, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def probe_target(target: dict[str, Any], icmp_timeout_s: int, tcp_timeout_s: float) -> dict[str, Any]:
    icmp_ok = ping_host(target["ip"], icmp_timeout_s) if target["icmp"] else None
    ports = {}
    for port in target["ports"]:
        ports[str(port)] = tcp_open(target["ip"], port, tcp_timeout_s)
    reachable = bool(icmp_ok) or any(ports.values())
    if icmp_ok is None and not ports:
        reachable = False
    return {
        "id": target["id"],
        "ip": target["ip"],
        "label": target["label"],
        "icmp_ok": icmp_ok,
        "ports": ports,
        "reachable": reachable,
    }


def next_status(
    previous: str,
    reachable: bool,
    fail_streak: int,
    recover_streak: int,
    fail_threshold: int,
    recover_threshold: int,
) -> tuple[str, int, int]:
    if previous not in {"unknown", "up", "down", "down_candidate", "up_candidate"}:
        previous = "unknown"
    if reachable:
        fail_streak = 0
        recover_streak += 1
        if previous in {"unknown", "up", "up_candidate"} and recover_streak >= 1:
            return "up", fail_streak, recover_streak
        if previous in {"down", "down_candidate"} and recover_streak >= recover_threshold:
            return "up", fail_streak, recover_streak
        return "up_candidate", fail_streak, recover_streak
    recover_streak = 0
    fail_streak += 1
    if previous in {"unknown"} and fail_streak >= fail_threshold:
        return "down", fail_streak, recover_streak
    if previous in {"up", "up_candidate"} and fail_streak >= fail_threshold:
        return "down", fail_streak, recover_streak
    if previous == "down":
        return "down", fail_streak, recover_streak
    return "down_candidate", fail_streak, recover_streak


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)
