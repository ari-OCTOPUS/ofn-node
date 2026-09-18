"""Layer 3: laptop->138 SSH local-forward /healthz. Bind 127.0.0.1 only.

Does not enable flags, bind 0.0.0.0, write on 138, decide 180 role, or claim a live organism.
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
OUT = LANE / "LAYER3-RECEIPT.json"
REMOTE = "ari@192.168.0.138"
NODE180 = "ari@192.168.0.180"
# laptop 8791 is harvest ingest — never forward onto it.
FORWARDS = (
    {"local": 18791, "remote": 8791, "role": "ziman"},
    {"local": 18792, "remote": 8792, "role": "lead"},
    {"local": 18793, "remote": 8793, "role": "studio"},
    {"local": 18794, "remote": 8794, "role": "owner"},
    {"local": 18796, "remote": 8796, "role": "bridge"},
)
ROLE_SOURCE = "F:/ofn-node/ofn/config.py:294"


def _now() -> tuple[str, str]:
    local = datetime.now().astimezone().isoformat(timespec="seconds")
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return local, utc


def _tcp(host: str, port: int, timeout: float = 0.4) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def _listen_rows(ports: list[int]) -> list[dict]:
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$ports = @(" + ",".join(str(p) for p in ports) + "); "
                "Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
                "Where-Object { $ports -contains $_.LocalPort } | "
                "Select-Object LocalAddress, LocalPort, OwningProcess | "
                "ConvertTo-Json -Compress"
            ),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = (proc.stdout or "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if isinstance(data, dict):
        return [data]
    return list(data)


def _pid_cmd(pid: int) -> str | None:
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                f"$p = Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}' "
                "-ErrorAction SilentlyContinue; if ($p) { $p.CommandLine }"
            ),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    line = (proc.stdout or "").strip()
    return line or None


def _healthz(port: int) -> dict:
    rec: dict = {"port": port, "url": f"http://127.0.0.1:{port}/healthz", "http": None, "ok": None, "err": None, "n": 0, "body": None}
    try:
        req = urllib.request.Request(rec["url"])
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read()
            rec["http"] = int(r.status)
            rec["n"] = len(raw)
            text = raw.decode("utf-8", errors="replace")
            rec["body"] = json.loads(text)
            if isinstance(rec["body"], dict):
                rec["ok"] = bool(rec["body"].get("ok"))
    except Exception as e:
        rec["err"] = f"{type(e).__name__}"
    return rec


def _start_tunnel() -> dict:
    arglist = [
        "-N",
        "-o", "BatchMode=yes",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ConnectTimeout=15",
        "-o", "ServerAliveInterval=30",
    ]
    for fwd in FORWARDS:
        arglist.extend(["-L", f"127.0.0.1:{fwd['local']}:127.0.0.1:{fwd['remote']}"])
    arglist.append(REMOTE)
    # Independent of this Python job object so the tunnel can stay up.
    ps = (
        "$p = Start-Process -FilePath 'ssh' -ArgumentList @("
        + ",".join("'" + a.replace("'", "''") + "'" for a in arglist)
        + ") -WindowStyle Hidden -PassThru; Write-Output $p.Id"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    pid = None
    out = (proc.stdout or "").strip()
    if out.isdigit():
        pid = int(out)
    return {
        "ssh_start_exit": proc.returncode,
        "ssh_pid": pid,
        "stderr": (proc.stderr or "").strip()[:400] or None,
        "argv_bind": "127.0.0.1 only",
        "gateway_ports": False,
        "remote": REMOTE,
    }


def _probe_180() -> dict:
    tcp22 = _tcp("192.168.0.180", 22, timeout=3.0)
    proc = subprocess.run(
        [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10",
            "-o", "PreferredAuthentications=publickey",
            "-o", "NumberOfPasswordPrompts=0",
            NODE180,
            "true",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    err = (proc.stderr or "").strip().replace("\r", "")
    # One publickey attempt only. Do not retry other users or guess passwords.
    return {
        "tried": NODE180,
        "ssh_exit": proc.returncode,
        "stderr": err[:300] if err else None,
        "host_reachable_tcp22": tcp22,
        "password_guesses": 0,
        "root_tried": False,
        "role": "UNDECIDED",
        "role_decided_by_this_lane": False,
        "tunnel_138_to_180": "not_attempted_no_180_auth_and_no_ssh_write_on_138",
        "status": "auth_failed" if proc.returncode != 0 else "unexpected_ok",
    }


def main() -> int:
    local_ts, utc_ts = _now()
    harvest_listen = _tcp("127.0.0.1", 8791)
    harvest_cmd = None
    rows_8791 = [r for r in _listen_rows([8791]) if str(r.get("LocalPort")) == "8791"]
    harvest_pid = None
    if rows_8791:
        harvest_pid = int(rows_8791[0]["OwningProcess"])
        harvest_cmd = _pid_cmd(harvest_pid)

    occupied_local = []
    for fwd in FORWARDS:
        if _tcp("127.0.0.1", fwd["local"]):
            occupied_local.append(fwd["local"])

    tunnel = {"started_this_run": False}
    if occupied_local:
        tunnel["started_this_run"] = False
        tunnel["note"] = "local forward ports already open; reused"
        tunnel["already_open"] = occupied_local
        # Best-effort existing ssh pid from listen table.
        rows = _listen_rows([f["local"] for f in FORWARDS])
        pids = sorted({int(r["OwningProcess"]) for r in rows if r.get("OwningProcess") is not None})
        tunnel["listen_pids"] = pids
        if pids:
            tunnel["ssh_pid"] = pids[0]
            tunnel["ssh_cmd"] = _pid_cmd(pids[0])
    else:
        tunnel = _start_tunnel()
        tunnel["started_this_run"] = True
        deadline = time.time() + 12
        while time.time() < deadline:
            if all(_tcp("127.0.0.1", f["local"]) for f in FORWARDS):
                break
            time.sleep(0.25)

    listen_after = _listen_rows([f["local"] for f in FORWARDS] + [8791])
    bind_addrs = sorted({str(r.get("LocalAddress")) for r in listen_after if int(r.get("LocalPort", 0)) in {f["local"] for f in FORWARDS}})
    bind_ok = bind_addrs == ["127.0.0.1"]
    if any(a in {"0.0.0.0", "::"} for a in bind_addrs):
        # Fail closed: never leave a wildcard bind.
        pid = tunnel.get("ssh_pid")
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        raise SystemExit("wildcard_bind_detected")

    healthz = {}
    for fwd in FORWARDS:
        rec = _healthz(fwd["local"])
        rec["remote_port"] = fwd["remote"]
        rec["role"] = fwd["role"]
        rec["loopback_open"] = _tcp("127.0.0.1", fwd["local"])
        healthz[str(fwd["remote"])] = rec

    laptop_8791 = _healthz(8791)
    laptop_8791["role_on_this_host"] = "harvest_ingest"
    laptop_8791["listen_pid"] = harvest_pid
    laptop_8791["listen_cmd"] = harvest_cmd

    ofn_ok = all(
        (healthz.get(str(p)) or {}).get("http") == 200 and (healthz.get(str(p)) or {}).get("ok") is True
        for p in (8791, 8792, 8793, 8794)
    )
    bridge_ok = (healthz.get("8796") or {}).get("http") == 200 and (healthz.get("8796") or {}).get("ok") is True

    node180 = _probe_180()
    local_ts, utc_ts = _now()
    receipt = {
        "schema": "octopus.layer3-receipt.v1",
        "measured_at": local_ts,
        "measured_at_utc": utc_ts,
        "vantage": "ssh_local_forward_from_laptop_191",
        "scope": "this_host_only plus node138 via tunnel",
        "claim_type": "observation",
        "live_organism_claim": False,
        "layer": 3,
        "pass": bool(ofn_ok and bind_ok and harvest_listen),
        "canonical_body": "node138",
        "this_host": {
            "hostname": "DESKTOP-KA9RFN5",
            "wifi": "192.168.0.191",
            "not_node180": True,
        },
        "collision_avoidance": {
            "laptop_8791_left_alone": True,
            "laptop_8791_listen": harvest_listen,
            "laptop_8791_pid": harvest_pid,
            "laptop_8791_cmd": harvest_cmd,
            "forward_ports_used": [f["local"] for f in FORWARDS],
            "note": "harvest ingest already owns 127.0.0.1:8791; forwards use 18791-18794 and 18796",
        },
        "tunnel": {
            **tunnel,
            "direction": "laptop_191_to_138_loopback",
            "bind": "127.0.0.1",
            "bind_addrs_observed": bind_addrs,
            "bind_ok_localhost_only": bind_ok,
            "map": [f"{f['local']}->127.0.0.1:{f['remote']}" for f in FORWARDS],
            "listen_table": listen_after,
            "ssh_write_on_138": False,
            "wildcard_bind": False,
        },
        "healthz_via_tunnel": healthz,
        "ofn_legs_healthz_200": ofn_ok,
        "bridge_8796_healthz_200": bridge_ok,
        "leg_roles": {
            "8791": "ziman",
            "8792": "lead",
            "8793": "studio",
            "8794": "owner",
            "8796": "octopus_bridge.run",
            "role_source": ROLE_SOURCE,
        },
        "laptop_8791_healthz": laptop_8791,
        "this_host_8792_8794_8796": {
            "8792": _tcp("127.0.0.1", 8792),
            "8793": _tcp("127.0.0.1", 8793),
            "8794": _tcp("127.0.0.1", 8794),
            "8796": _tcp("127.0.0.1", 8796),
            "note": "ofn.run legs still absent on this host; empty 8792-8794 is body_not_on_this_host",
        },
        "node180": node180,
        "not_done_this_layer": [
            "HOLD_EXTERNAL remains closed",
            "180 role remains UNDECIDED (owner)",
            "138->180 tunnel not opened (no 180 auth; no SSH write on 138)",
            "no live-organism claim",
        ],
        "source": "verify_layer3.py",
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "pass": receipt["pass"],
        "out": str(OUT),
        "ssh_pid": tunnel.get("ssh_pid"),
        "ofn_ok": ofn_ok,
        "bridge_ok": bridge_ok,
        "bind_ok": bind_ok,
        "node180": node180.get("status"),
    }, ensure_ascii=False))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
