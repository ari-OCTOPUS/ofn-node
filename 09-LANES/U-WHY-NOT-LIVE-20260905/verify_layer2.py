"""Layer 2: read-only SSH census of node138 ofn legs. Does not start, bind, or send."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "LAYER2-COMPLETE.json"
REMOTE = r"""
python3 - <<'PY'
import json, urllib.request, subprocess
ports = (8791, 8792, 8793, 8794, 8796)
ss = subprocess.check_output(["ss", "-lntp"], text=True, errors="replace")
owned, health = {}, {}
for p in ports:
    owned[str(p)] = [ln.strip() for ln in ss.splitlines() if f":{p}" in ln][:2]
    rec = {"port": p, "http": None, "ok": None, "err": None, "n": 0}
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{p}/healthz")
        with urllib.request.urlopen(req, timeout=3) as r:
            raw = r.read()
            rec["http"] = int(r.status)
            rec["n"] = len(raw)
            d = json.loads(raw.decode("utf-8"))
            rec["ok"] = bool(d.get("ok")) if isinstance(d, dict) else None
    except Exception as e:
        rec["err"] = type(e).__name__
    health[str(p)] = rec
print(json.dumps({"ss": owned, "healthz": health}, ensure_ascii=False))
PY
"""


def main() -> int:
    proc = subprocess.run(
        [
            "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "ari@192.168.0.138", REMOTE,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    remote = {}
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            remote = json.loads(proc.stdout.strip().splitlines()[-1])
        except json.JSONDecodeError:
            remote = {"parse_error": True}
    hz = (remote.get("healthz") or {})
    ofn_ok = all(
        (hz.get(str(p)) or {}).get("http") == 200 and (hz.get(str(p)) or {}).get("ok") is True
        for p in (8791, 8792, 8793, 8794)
    )
    receipt = {
        "schema": "octopus.layer2-complete.v1",
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vantage": "ssh_from_laptop_191",
        "scope": "node138_only",
        "claim_type": "observation",
        "live_organism_claim": False,
        "layer": 2,
        "ssh_exit": proc.returncode,
        "canonical_body": "node138",
        "ofn_legs_healthz_200": ofn_ok,
        "remote": remote,
        "node180": "auth_failed_not_in_this_layer",
        "source": "verify_layer2.py",
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass": ofn_ok and proc.returncode == 0, "out": str(OUT)}, ensure_ascii=False))
    return 0 if ofn_ok and proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
