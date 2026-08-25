from __future__ import annotations

import socket
import time
from pathlib import Path
from typing import Any, Callable


TOOL_NAMES = ("place", "body", "neighbors", "senses")
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
CACHE_TTL_S = 15.0


def _read_text(path: Path, default: str | None = None) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except (OSError, UnicodeError):
        return default


def _read_bytes_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes().replace(b"\x00", b" ").strip()
        return raw.decode("utf-8", "replace").strip() or None
    except OSError:
        return None


def _hex_ipv4_le(raw: str) -> str | None:
    if len(raw) != 8:
        return None
    try:
        value = int(raw, 16)
    except ValueError:
        return None
    return socket.inet_ntoa(value.to_bytes(4, "little"))


def _mac_prefix(mac: str, octects: int = 3) -> str:
    parts = mac.lower().split(":")
    if len(parts) < octects:
        return mac.lower()
    return ":".join(parts[:octects])


def _local_ipv4s(fib_text: str) -> list[str]:
    found: list[str] = []
    lines = fib_text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|-- "):
            continue
        ip = stripped.split()[1]
        nxt = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if "/32 host LOCAL" not in nxt:
            continue
        if ip.count(".") == 3 and not ip.startswith("127."):
            found.append(ip)
    return found


def discover_place(root: Path = Path("/")) -> dict[str, Any]:
    hostname = _read_text(root / "proc/sys/kernel/hostname")
    model = _read_bytes_text(root / "proc/device-tree/model")
    kernel_boot_id = _read_text(root / "proc/sys/kernel/random/boot_id")
    uptime_raw = _read_text(root / "proc/uptime")
    uptime_s = None
    if uptime_raw:
        try:
            uptime_s = float(uptime_raw.split()[0])
        except (IndexError, ValueError):
            uptime_s = None
    iface = "eth0"
    mac = _read_text(root / "sys/class/net" / iface / "address")
    operstate = _read_text(root / "sys/class/net" / iface / "operstate")
    route_gateway = None
    route_text = _read_text(root / "proc/net/route")
    if route_text:
        for line in route_text.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4 and parts[0] == iface and parts[1] == "00000000":
                route_gateway = _hex_ipv4_le(parts[2])
                break
    ipv4s = _local_ipv4s(_read_text(root / "proc/net/fib_trie") or "")
    ipv4 = next((ip for ip in ipv4s if ip.startswith("192.168.0.")), None)
    if ipv4 is None and ipv4s:
        ipv4 = ipv4s[0]
    wlan_state = _read_text(root / "sys/class/net/wlan0/operstate")
    wlan_mac = _read_text(root / "sys/class/net/wlan0/address")
    tz = None
    localtime = root / "etc/localtime"
    try:
        tz = str(localtime.resolve()).rsplit("/", 1)[-1]
    except OSError:
        tz = _read_text(root / "etc/timezone")
    ifaces = []
    net_root = root / "sys/class/net"
    try:
        names = sorted(p.name for p in net_root.iterdir() if p.is_dir() or p.is_symlink())
    except OSError:
        names = []
    for name in names:
        ifaces.append(
            {
                "name": name,
                "operstate": _read_text(net_root / name / "operstate"),
                "mac": _read_text(net_root / name / "address"),
            }
        )
    return {
        "tool": "place",
        "claim_level": "OBSERVED",
        "hostname": hostname,
        "board_model": model,
        "kernel_boot_id": kernel_boot_id,
        "uptime_s": uptime_s,
        "iface": iface,
        "ipv4": ipv4,
        "mac": mac,
        "operstate": operstate,
        "gateway_ipv4": route_gateway,
        "lan_cidr": "192.168.0.0/24",
        "wlan0_operstate": wlan_state,
        "wlan0_mac": wlan_mac,
        "timezone": tz or "UNKNOWN",
        "gps": "ABSENT",
        "geo_coordinates": "UNMEASURED_NO_GPS_NO_GEOIP",
        "ifaces": ifaces,
        "unknowns": [
            name
            for name, value in (
                ("ipv4", ipv4),
                ("gateway_ipv4", route_gateway),
                ("board_model", model),
            )
            if not value
        ],
    }


def discover_neighbors(root: Path = Path("/")) -> dict[str, Any]:
    arp_text = _read_text(root / "proc/net/arp") or ""
    rows = []
    for line in arp_text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        ip, _hw, flags, mac, _mask, device = parts[:6]
        if mac == "00:00:00:00:00:00":
            continue
        rows.append(
            {
                "ip": ip,
                "mac": mac.lower(),
                "device": device,
                "reachable_flag": flags != "0x0",
            }
        )
    self_mac = _read_text(root / "sys/class/net/eth0/address")
    prefix = _mac_prefix(self_mac or "")
    for row in rows:
        row["same_mac_family_as_self"] = bool(
            self_mac and _mac_prefix(row["mac"]) == prefix
        )
    return {
        "tool": "neighbors",
        "claim_level": "OBSERVED",
        "arp": rows,
        "self_mac": self_mac,
        "count": len(rows),
    }


def discover_body(root: Path = Path("/")) -> dict[str, Any]:
    zones = []
    thermal_root = root / "sys/class/thermal"
    try:
        zone_dirs = sorted(
            p for p in thermal_root.iterdir() if p.name.startswith("thermal_zone")
        )
    except OSError:
        zone_dirs = []
    for zone in zone_dirs:
        raw = _read_text(zone / "temp")
        milli = None
        try:
            milli = int(raw) if raw is not None else None
        except ValueError:
            milli = None
        zones.append(
            {
                "name": zone.name,
                "type": _read_text(zone / "type"),
                "temp_mC": milli,
                "temp_C": None if milli is None else round(milli / 1000, 1),
            }
        )
    present = _read_text(root / "sys/devices/system/cpu/present")
    meminfo = _read_text(root / "proc/meminfo") or ""
    mem = {}
    for line in meminfo.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        token = rest.split()[0]
        try:
            mem[key] = int(token)
        except ValueError:
            continue
    emmc = {
        "name": _read_text(root / "sys/block/mmcblk0/device/name"),
        "life_time": _read_text(root / "sys/block/mmcblk0/device/life_time"),
        "pre_eol": _read_text(root / "sys/block/mmcblk0/device/pre_eol_info"),
    }
    return {
        "tool": "body",
        "claim_level": "OBSERVED",
        "cpu_present": present,
        "thermal_zones": zones,
        "MemAvailable_kB": mem.get("MemAvailable"),
        "MemTotal_kB": mem.get("MemTotal"),
        "emmc": emmc,
    }


def discover_senses(root: Path = Path("/")) -> dict[str, Any]:
    usb = []
    usb_root = root / "sys/bus/usb/devices"
    try:
        entries = sorted(usb_root.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        vendor = _read_text(entry / "idVendor")
        product = _read_text(entry / "idProduct")
        if not vendor or not product:
            continue
        usb.append(
            {
                "sys": entry.name,
                "id": f"{vendor}:{product}",
                "product": _read_text(entry / "product"),
            }
        )
    i2c = []
    i2c_root = root / "sys/bus/i2c/devices"
    try:
        entries = sorted(i2c_root.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        if not entry.name.startswith("i2c-"):
            continue
        i2c.append({"id": entry.name, "name": _read_text(entry / "name")})
    return {
        "tool": "senses",
        "claim_level": "OBSERVED",
        "usb": usb,
        "i2c_adapters": i2c,
        "camera": "NOT_FOUND",
        "microphone": _microphone_status(root),
        "gps": "NOT_FOUND",
    }


def _microphone_status(root: Path) -> str:
    pcm = _read_text(root / "proc/asound/pcm") or ""
    if "capture" not in pcm.lower():
        return "NOT_FOUND"
    if "ES8323" in pcm or "ES8388" in pcm:
        return "ES8323_CAPTURE"
    return "CAPTURE_DEVICE_PRESENT"


def run_tools(
    root: Path = Path("/"),
    *,
    force: bool = False,
) -> dict[str, Any]:
    key = str(root)
    now = time.monotonic()
    cached = _CACHE.get(key)
    if not force and cached and now - cached[0] < CACHE_TTL_S:
        return cached[1]
    payload = {
        "place": discover_place(root),
        "body": discover_body(root),
        "neighbors": discover_neighbors(root),
        "senses": discover_senses(root),
        "ran_utc": time.time(),
    }
    _CACHE[key] = (now, payload)
    return payload


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "place": discover_place,
    "body": discover_body,
    "neighbors": discover_neighbors,
    "senses": discover_senses,
}
