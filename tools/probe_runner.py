#!/usr/bin/env python3
"""R-4 — real end-to-end probes + PROBE-RUN receipt.

Probe kinds:
  http          : GET a URL, expect status + a substring in the body
  ssh_readonly  : run a read-only command on a host, expect a regex in stdout

Every probe result carries probe_id + probed_at. The registry
(probe/PROBE-REGISTRY.yaml) is the list of services that claim health;
anything absent from a fresh PROBE-RUN is UNPROBED by rule (RCA-4/RCA-6).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def run_http(name: str, spec: dict) -> dict:
    t0 = time.time()
    req = urllib.request.Request(spec["url"],
                                 headers={"User-Agent": "octopus-probe/1"})
    try:
        with urllib.request.urlopen(req, timeout=spec.get("timeout_s", 20)) as r:
            body = r.read(200000).decode("utf-8", "replace")
            status = r.status
    except Exception as exc:  # noqa: BLE001
        return {"probe": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
    ok = status == spec.get("expect_status", 200) and \
        (spec.get("expect_contains") or "") in body
    return {"probe": name, "ok": ok, "http_status": status,
            "expect_contains_found": (spec.get("expect_contains") or "") in body,
            "ms": round((time.time() - t0) * 1000)}


def run_ssh_readonly(name: str, spec: dict) -> dict:
    t0 = time.time()
    try:
        out = subprocess.run(
            ["ssh", spec["host"], spec["cmd"]],
            capture_output=True, text=True, timeout=spec.get("timeout_s", 30)).stdout
    except Exception as exc:  # noqa: BLE001
        return {"probe": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
    ok = re.search(spec["expect_regex"], out) is not None
    return {"probe": name, "ok": ok,
            "match": bool(re.search(spec["expect_regex"], out)),
            "ms": round((time.time() - t0) * 1000)}


RUNNERS = {"http": run_http, "ssh_readonly": run_ssh_readonly}


def load_registry() -> dict:
    reg_path = REPO / "probe" / "PROBE-REGISTRY.json"
    return json.loads(reg_path.read_text(encoding="utf-8"))


def main() -> int:
    reg = load_registry()
    results = []
    for name, spec in reg["probes"].items():
        fn = RUNNERS.get(spec["kind"])
        if not fn:
            results.append({"probe": name, "ok": False,
                            "error": f"unknown kind {spec['kind']}"})
            continue
        r = fn(name, spec)
        r["probe_id"] = f"{reg['run_prefix']}-{name}"
        r["probed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        r["claim"] = ("HEALTHY" if r["ok"] else "FAIL") + \
                     f" (probe_id={r['probe_id']}, probed_at={r['probed_at']})"
        results.append(r)
    run = {
        "schema": "probe-run/1",
        "id": reg["run_prefix"] + "-RUN-1",
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "order": "MP-ROOTFIX R-4 (RCA-4/RCA-6)",
        "results": results,
        "summary": {"probes": len(results),
                    "pass": sum(1 for r in results if r["ok"]),
                    "fail": sum(1 for r in results if not r["ok"])},
        "rule": "services absent from a fresh (<24h) PROBE-RUN report UNPROBED, never HEALTHY",
    }
    out = REPO / "rca" / "PROBE-RUN-1.json"
    out.write_text(json.dumps(run, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(run["summary"]))
    return 0 if run["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
