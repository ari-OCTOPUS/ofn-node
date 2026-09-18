"""Layer 1 receipt: laptop library heartbeat. This-host only. No start, no flags."""
from __future__ import annotations

import json
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OPS = Path(r"F:\backup\_ops")
OUT = Path(__file__).resolve().parent / "LAYER1-VERIFY.json"
NEED_LISTEN = ((8771, "organism"), (8772, "cortex"))


def _iso_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _listen(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def _get_organism() -> dict:
    req = urllib.request.Request(
        "http://127.0.0.1:8771/api/organism",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return {
            "http": int(resp.status),
            "body": json.loads(resp.read().decode("utf-8")),
        }


def main() -> int:
    today = datetime.now().date().isoformat()
    stop = (OPS / "STOP-ORGANISM").exists()
    listens = {
        f"{host}:{port}": {"role": role, "open": _listen(host, port)}
        for port, role in NEED_LISTEN
        for host in ("127.0.0.1",)
    }
    bind_all = {str(port): _listen("0.0.0.0", port) for port, _ in NEED_LISTEN}
    api: dict = {}
    err = None
    try:
        api = _get_organism()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        err = type(e).__name__
    body = api.get("body") or {}
    ts = str(body.get("ts") or "")
    checks = {
        "stop_absent": not stop,
        "8771_loopback": listens["127.0.0.1:8771"]["open"],
        "8772_loopback": listens["127.0.0.1:8772"]["open"],
        "api_http_200": api.get("http") == 200,
        "ts_today": ts.startswith(today),
        "stop_organism_false": body.get("stop_organism") is False,
        "no_all_iface_8771": not bind_all["8771"],
    }
    receipt = {
        "schema": "octopus.layer1-library-verify.v1",
        "measured_at": _iso_local(),
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vantage": "this_host_only",
        "scope": "this_host_only",
        "claim_type": "observation",
        "live_organism_claim": False,
        "layer": 1,
        "checks": checks,
        "pass": all(checks.values()),
        "api_ts": ts or None,
        "api_beat": body.get("beat"),
        "api_started": body.get("started"),
        "api_error": err,
        "listens": listens,
        "source": "verify_layer1.py",
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass": receipt["pass"], "out": str(OUT), "ts": ts, "beat": body.get("beat")}, ensure_ascii=False))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
