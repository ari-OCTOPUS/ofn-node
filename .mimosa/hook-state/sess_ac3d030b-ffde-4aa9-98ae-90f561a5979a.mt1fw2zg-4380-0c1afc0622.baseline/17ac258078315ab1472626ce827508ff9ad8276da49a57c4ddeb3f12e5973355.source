# -*- coding: utf-8 -*-
"""service_inventory -- runtime service discovery and dependency graph.

Scans the OCTOPUS process topology (organism, cortex, live, center, gateway,
MCP server) and produces a typed inventory + dependency graph.

All discovery is read-only: it reads process state via /proc or subprocess
but never starts/stops/kills anything.

Usage:
    from _ops.infra.service_inventory import get_service_inventory
    inv = get_service_inventory()
    print(inv.summary())
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]  # F:\backup

# Known OCTOPUS services with their canonical ports and process match patterns.
# Order implies dependency: a service depends on everything listed before it.
SERVICE_CATALOG: list[dict] = [
    {
        "id": "organism",
        "display": "Organism (brain)",
        "port": 8771,
        "match": "organism.py",
        "launcher": "_ops/RUN-ORGANISM.bat",
        "watchdog": "_ops/organism-watchdog.ps1",
        "restart_cmd": "_ops/RESTART-PROCESS.ps1 organism",
        "critical": True,
    },
    {
        "id": "cortex",
        "display": "Cortex (brain)",
        "port": 8772,
        "match": "cortex.py",
        "launcher": "_ops/RUN-CORTEX.bat",
        "watchdog": "_ops/cortex-watchdog.ps1",
        "restart_cmd": "_ops/RESTART-PROCESS.ps1 cortex",
        "critical": True,
    },
    {
        "id": "live",
        "display": "Live Cockpit",
        "port": 8773,
        "match": "live\\server.py",
        "launcher": "_ops/run-live-headless.bat",
        "watchdog": "_ops/live-watchdog.ps1",
        "restart_cmd": "_ops/RESTART-PROCESS.ps1 live",
        "critical": False,
    },
    {
        "id": "center",
        "display": "Telegram Center (poller)",
        "port": None,
        "match": "center.py",
        "launcher": "_ops/telegram_center/RUN-TG-CENTER.bat",
        "watchdog": None,
        "restart_cmd": "_ops/RESTART-PROCESS.ps1 center",
        "critical": True,
    },
    {
        "id": "gateway",
        "display": "Miniapp Gateway",
        "port": 8774,
        "match": "miniapp_gateway.py",
        "launcher": None,
        "watchdog": "_ops/miniapp-watchdog.ps1",
        "restart_cmd": "_ops/RESTART-PROCESS.ps1 gateway",
        "critical": False,
    },
    {
        "id": "mcp_server",
        "display": "MCP Vault Server (stdio + HTTP)",
        "port": None,  # HTTP port is dynamic unless configured
        "match": "octopus_mcp/server.py",
        "launcher": None,  # launched by .mcp.json or --http flag
        "watchdog": None,
        "restart_cmd": None,  # client-managed, not a daemon
        "critical": False,
    },
]


@dataclass
class ServiceStatus:
    """Typed status of a single OCTOPUS service."""
    id: str
    display: str
    port: Optional[int]
    running: bool
    pid: Optional[int] = None
    port_listening: bool = False
    launcher_exists: bool = False
    watchdog_exists: bool = False
    has_restart_script: bool = False
    critical: bool = False


@dataclass
class ServiceInventory:
    """Full service inventory with dependency graph."""
    services: list[ServiceStatus] = field(default_factory=list)
    scanned_at: str = ""
    python_version: str = ""
    platform: str = ""

    def summary(self) -> str:
        lines = [f"OCTOPUS Service Inventory @ {self.scanned_at}"]
        lines.append(f"  Python: {self.python_version} | Platform: {self.platform}")
        lines.append("")
        running_count = sum(1 for s in self.services if s.running)
        lines.append(f"  Services: {running_count}/{len(self.services)} running")
        lines.append("")
        for s in self.services:
            status = "RUNNING" if s.running else "DOWN"
            port_info = f"port:{s.port}" if s.port else "no-port"
            pid_info = f"pid={s.pid}" if s.pid else ""
            crit = " [CRITICAL]" if s.critical else ""
            listen = "" if not s.port or s.port_listening or not s.running else " (port not listening!)"
            lines.append(f"  {s.id:12s} {status:8s} {port_info} {pid_info}{listen}{crit}")
        return "\n".join(lines)

    def dependency_graph(self) -> list[tuple[str, str]]:
        """Return edges: (dependency, dependent) based on SERVICE_CATALOG order."""
        edges = []
        for i in range(1, len(SERVICE_CATALOG)):
            edges.append((SERVICE_CATALOG[i - 1]["id"], SERVICE_CATALOG[i]["id"]))
        return edges

    def to_dict(self) -> dict:
        return {
            "scanned_at": self.scanned_at,
            "python_version": self.python_version,
            "platform": self.platform,
            "services": [
                {
                    "id": s.id,
                    "display": s.display,
                    "port": s.port,
                    "running": s.running,
                    "pid": s.pid,
                    "port_listening": s.port_listening,
                    "launcher_exists": s.launcher_exists,
                    "watchdog_exists": s.watchdog_exists,
                    "has_restart_script": s.has_restart_script,
                    "critical": s.critical,
                }
                for s in self.services
            ],
            "dependency_graph": self.dependency_graph(),
        }


def _is_port_listening(port: int) -> bool:
    """Check if a TCP port is in LISTEN state (Windows netstat)."""
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        for line in result.stdout.splitlines():
            if f"LISTENING" in line and f":{port}" in line:
                return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def _find_python_processes(match_pattern: str) -> list[dict]:
    """Find running python processes matching a pattern via WMIC/tasklist."""
    if sys.platform != "win32":
        return []
    try:
        # wmic is deprecated but still works on Windows 10/11
        result = subprocess.run(
            ["wmic", "process", "where",
             f"name='python.exe' and commandline like '%{match_pattern}%'",
             "get", "processid,commandline", "/format:csv"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=15,
        )
        procs = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("Node") or line.startswith(","):
                continue
            # CSV from wmic: Node,ProcessId,CommandLine
            parts = line.split(",", 2)
            if len(parts) >= 3:
                try:
                    pid = int(parts[1].strip())
                except ValueError:
                    continue
                procs.append({"pid": pid, "cmdline": parts[2][:200]})
        return procs
    except (OSError, subprocess.TimeoutExpired):
        return []


def get_service_inventory() -> ServiceInventory:
    """Scan the runtime and produce a full service inventory."""
    inventory = ServiceInventory(
        scanned_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        python_version=sys.version.split()[0],
        platform=sys.platform,
    )
    for spec in SERVICE_CATALOG:
        procs = _find_python_processes(spec["match"])
        running = len(procs) > 0
        pid = procs[0]["pid"] if procs else None
        port = spec["port"]
        port_listening = False
        if port and running:
            port_listening = _is_port_listening(port)
        launcher_path = ROOT / spec["launcher"] if spec["launcher"] else None
        watchdog_path = ROOT / spec["watchdog"] if spec["watchdog"] else None
        restart_path = ROOT / spec["restart_cmd"] if spec["restart_cmd"] else None
        status = ServiceStatus(
            id=spec["id"],
            display=spec["display"],
            port=port,
            running=running,
            pid=pid,
            port_listening=port_listening,
            launcher_exists=launcher_path.exists() if launcher_path else False,
            watchdog_exists=watchdog_path.exists() if watchdog_path else False,
            has_restart_script=restart_path.exists() if restart_path else False,
            critical=spec["critical"],
        )
        inventory.services.append(status)
    return inventory


if __name__ == "__main__":
    inv = get_service_inventory()
    print(inv.summary())
    print()
    print("Dependency graph edges:", inv.dependency_graph())
