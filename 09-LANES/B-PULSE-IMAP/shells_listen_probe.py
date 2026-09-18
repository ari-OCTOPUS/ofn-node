#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only this-host listen table for the four OFN shells.

Lane: B-PULSE-IMAP

Reads the OS listen table (Windows Get-NetTCPConnection) and the owning
process command line (Win32_Process). Prints identity + the four rooms
plus cheap neighbours (8795/8796/877x/8895/143/993).

Does not bind. Does not start ofn.run. Does not open a client socket.
Does not talk to 138.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone

LANE = "B-PULSE-IMAP"
FOUR = (8791, 8792, 8793, 8794)
NEIGHBOURS = (8795, 8796, 8771, 8772, 8773, 8774, 8775, 8776, 8777, 8895, 143, 993)
WATCH = FOUR + NEIGHBOURS

PS_LISTEN = r"""
$ErrorActionPreference = 'SilentlyContinue'
$ports = @(8791,8792,8793,8794,8795,8796,8771,8772,8773,8774,8775,8776,8777,8895,143,993)
$rows = @()
$conns = Get-NetTCPConnection -State Listen | Where-Object { $ports -contains $_.LocalPort }
foreach ($c in $conns) {
  $proc = Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $c.OwningProcess)
  $cmd = ''
  $name = ''
  if ($proc) {
    $name = [string]$proc.Name
    $cmd = [string]$proc.CommandLine
  }
  $rows += [pscustomobject]@{
    LocalAddress = [string]$c.LocalAddress
    LocalPort = [int]$c.LocalPort
    OwningProcess = [int]$c.OwningProcess
    ProcessName = $name
    CommandLine = $cmd
  }
}
$rows | ConvertTo-Json -Compress -Depth 3
"""

PS_IDENTITY = r"""
$ErrorActionPreference = 'SilentlyContinue'
$wifi = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -match 'Wi-Fi|WiFi|WLAN' -and $_.PrefixOrigin -eq 'Dhcp' } |
  Select-Object -First 1 IPAddress, InterfaceAlias, PrefixLength
$lan = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -like '192.168.0.*' -and $_.PrefixOrigin -eq 'Dhcp' } |
  Select-Object -First 1 IPAddress, InterfaceAlias, PrefixLength
[pscustomobject]@{
  Hostname = [string]$env:COMPUTERNAME
  WifiIP = [string]$wifi.IPAddress
  WifiAlias = [string]$wifi.InterfaceAlias
  Lan192IP = [string]$lan.IPAddress
  Lan192Alias = [string]$lan.InterfaceAlias
} | ConvertTo-Json -Compress
"""


def _ps_json(script: str) -> object:
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"powershell exit {completed.returncode}: {completed.stderr.strip()}"
        )
    raw = (completed.stdout or "").strip()
    if not raw:
        return None
    return json.loads(raw)


def _as_rows(payload: object) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    return []


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ident = _as_rows(_ps_json(PS_IDENTITY))
    ident0 = ident[0] if ident else {}
    rows = _as_rows(_ps_json(PS_LISTEN))

    print(f"lane={LANE}")
    print(f"measured_at_utc={now}")
    print(f"hostname={ident0.get('Hostname') or socket.gethostname()}")
    print(f"wifi_ip={ident0.get('WifiIP') or 'unverified'}")
    print(f"wifi_alias={ident0.get('WifiAlias') or 'unverified'}")
    print(f"lan_192_ip={ident0.get('Lan192IP') or 'unverified'}")
    print(f"vantage=this_host_only")
    print(f"scope=this_host_only")
    print(f"claim_type=runtime")
    print(f"bind=none started=none ssh=none client_socket=none")
    print(f"pid_self={os.getpid()} argv={sys.argv[0]}")
    print("source=Get-NetTCPConnection -State Listen + Win32_Process.CommandLine")
    print("---four-rooms---")
    print("port,bind,pid,process,cmdline")

    by_port: dict[int, list[dict]] = {p: [] for p in WATCH}
    for row in rows:
        try:
            port = int(row.get("LocalPort"))
        except (TypeError, ValueError):
            continue
        if port in by_port:
            by_port[port].append(row)

    for port in FOUR:
        hits = by_port.get(port) or []
        if not hits:
            print(f"{port},absent,-,-,absent")
            continue
        for hit in hits:
            addr = hit.get("LocalAddress") or "?"
            pid = hit.get("OwningProcess")
            name = (hit.get("ProcessName") or "").replace(",", " ")
            cmd = (hit.get("CommandLine") or "").replace("\r", " ").replace("\n", " ")
            print(f"{port},{addr},{pid},{name},{cmd}")

    print("---neighbours---")
    for port in NEIGHBOURS:
        hits = by_port.get(port) or []
        if not hits:
            print(f"{port},absent,-,-,absent")
            continue
        for hit in hits:
            addr = hit.get("LocalAddress") or "?"
            pid = hit.get("OwningProcess")
            name = (hit.get("ProcessName") or "").replace(",", " ")
            cmd = (hit.get("CommandLine") or "").replace("\r", " ").replace("\n", " ")
            print(f"{port},{addr},{pid},{name},{cmd}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
