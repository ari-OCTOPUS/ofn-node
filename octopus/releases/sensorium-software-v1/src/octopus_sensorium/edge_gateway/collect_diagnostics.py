"""Readonly collect_diagnostics for Edge Gateway / Sensorium command path.

Safety: mutates must be false. No PWM/GPIO/ESP32 actuation. Soft latch untouched.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIAG_COMMANDS = frozenset({"COLLECT_DIAGNOSTICS", "REQUEST_DIAGNOSTIC"})
SCHEMA = "octopus.edge.diagnostics.v1"
DEFAULT_INCLUDE = (
    "systemd",
    "nats",
    "mqtt_sot",
    "feeds",
    "homeo",
    "doctor",
    "wave0_soft",
    "disk",
)
FORBIDDEN_INCLUDES = frozenset({"pwm", "gpio", "esp32_actuate", "shell"})
EVIDENCE_ROOT = Path("/var/lib/octopus/evidence")
STATE_ROOT = Path("/var/lib/octopus/state")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _run(cmd: list[str], timeout: float = 8.0) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()[:4000]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 125, f"{type(exc).__name__}: {exc}"


def _check(cid: str, status: str, note: str = "", evidence_ref: str = "") -> dict[str, str]:
    return {"id": cid, "status": status, "note": note, "evidence_ref": evidence_ref}


def _unit_active(unit: str) -> dict[str, str]:
    code, out = _run(["systemctl", "is-active", unit])
    st = out.strip() or "unknown"
    if st == "active":
        return _check(f"systemd.{unit}", "PASS", st)
    if st in {"inactive", "failed"}:
        return _check(f"systemd.{unit}", "FAIL", st)
    return _check(f"systemd.{unit}", "UNKNOWN", st)


def collect_diagnostics(
    *,
    request_id: str,
    params: dict[str, Any] | None = None,
    sender_id: str = "",
    write_evidence: bool = True,
) -> dict[str, Any]:
    params = dict(params or {})
    mutates = params.get("mutates", None)
    include = list(params.get("include") or DEFAULT_INCLUDE)

    checks: list[dict[str, str]] = []
    artifacts: list[str] = []
    overall = "PASS"

    def bump(st: str) -> None:
        nonlocal overall
        rank = {"PASS": 0, "ABSENT": 1, "STALE": 2, "DEGRADED": 3, "UNKNOWN": 4, "FAIL": 5}
        if rank.get(st, 0) > rank.get(overall, 0):
            overall = st if st != "ABSENT" or overall == "PASS" else overall
        if st == "FAIL":
            overall = "FAIL"
        elif st in {"DEGRADED", "STALE"} and overall not in {"FAIL"}:
            overall = "DEGRADED"
        elif st == "UNKNOWN" and overall == "PASS":
            overall = "UNKNOWN"

    # Hard rails
    if mutates is not False:
        return {
            "schema": SCHEMA,
            "request_id": request_id,
            "status": "FAIL",
            "reason": "mutates_must_be_false",
            "host": {"hostname": socket.gethostname()},
            "checks": [_check("gate.mutates", "FAIL", f"mutates={mutates!r}")],
            "artifacts": [],
            "safety": {},
            "ts_utc": _utc(),
        }

    bad = [x for x in include if x in FORBIDDEN_INCLUDES]
    if bad:
        return {
            "schema": SCHEMA,
            "request_id": request_id,
            "status": "FAIL",
            "reason": "forbidden_includes",
            "host": {"hostname": socket.gethostname()},
            "checks": [_check("gate.include", "FAIL", ",".join(bad))],
            "artifacts": [],
            "safety": {},
            "ts_utc": _utc(),
        }

    host = {
        "hostname": socket.gethostname(),
        "machine_id": Path("/etc/machine-id").read_text(encoding="utf-8").strip()
        if Path("/etc/machine-id").exists()
        else "",
        "uptime_sec": None,
    }
    try:
        host["uptime_sec"] = float(Path("/proc/uptime").read_text().split()[0])
    except OSError:
        pass

    if "systemd" in include:
        for unit in (
            "octopus-sensorium.service",
            "nats-server.service",
            "mosquitto.service",
            "octopus-external-feeds.timer",
            "octopus-homeo-feeds-snapshot.timer",
        ):
            c = _unit_active(unit)
            checks.append(c)
            bump(c["status"])

    if "nats" in include:
        code, out = _run(["ss", "-lntp"])
        if ":4222" in out and "192.168.0.182:4222" in out.replace(" ", ""):
            checks.append(_check("nats.listen", "PASS", "192.168.0.182:4222"))
        elif ":4222" in out:
            checks.append(_check("nats.listen", "DEGRADED", "4222 present but bind string atypical"))
            bump("DEGRADED")
        else:
            checks.append(_check("nats.listen", "FAIL", "no :4222"))
            bump("FAIL")

    if "mqtt_sot" in include:
        sot_path = STATE_ROOT / "mqtt" / "MQTT_SOT.json"
        sot = _read_json(sot_path)
        if not sot:
            checks.append(_check("mqtt.sot", "ABSENT", str(sot_path)))
            bump("ABSENT")
        else:
            policy = (
                (sot.get("localhost") or {}).get("policy")
                or sot.get("policy")
                or ""
            )
            if policy == "LOCAL_LOOPBACK_AUTH_OPEN__WAN_KEEP_CLOSED":
                checks.append(_check("mqtt.sot", "PASS", policy, str(sot_path)))
            else:
                checks.append(_check("mqtt.sot", "DEGRADED", policy or "missing_policy", str(sot_path)))
                bump("DEGRADED")

    if "feeds" in include:
        last = STATE_ROOT / "feeds" / "LAST_RUN.json"
        # discover alternate
        candidates = list(STATE_ROOT.glob("**/LAST_RUN*.json"))[:5]
        data = _read_json(last)
        if data is None:
            for c in candidates:
                data = _read_json(c)
                if data is not None:
                    last = c
                    break
        if data is None:
            # try receipt / allowlist path used by phase A
            alt = Path("/var/lib/octopus/state/external_feeds/LAST_RUN.json")
            data = _read_json(alt)
            last = alt if data is not None else last
        if data is None:
            checks.append(_check("feeds.last_run", "UNKNOWN", "LAST_RUN not found"))
            bump("UNKNOWN")
        else:
            ok = data.get("ok_count", data.get("ok", None))
            total = data.get("total", data.get("feed_count", None))
            note = f"ok={ok}/{total} path={last}"
            if ok is not None and total and ok == total:
                checks.append(_check("feeds.last_run", "PASS", note, str(last)))
            elif ok is not None:
                checks.append(_check("feeds.last_run", "DEGRADED", note, str(last)))
                bump("DEGRADED")
            else:
                checks.append(_check("feeds.last_run", "UNKNOWN", note, str(last)))
                bump("UNKNOWN")

    if "homeo" in include:
        snap = STATE_ROOT / "homeostasis" / "feeds_snapshot.json"
        data = _read_json(snap)
        if not data:
            checks.append(_check("homeo.feeds_snapshot", "ABSENT", str(snap)))
            bump("ABSENT")
        else:
            mode = data.get("mode") or (data.get("homeostasis") or {}).get("mode") or ""
            checks.append(_check("homeo.feeds_snapshot", "PASS", f"mode={mode}", str(snap)))

    if "doctor" in include:
        # Prefer newest doctor evidence if present; else STALE/UNKNOWN
        doctor_hits = sorted(
            EVIDENCE_ROOT.glob("**/doctor*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:3]
        if not doctor_hits:
            checks.append(_check("doctor", "STALE", "no doctor json under evidence"))
            bump("STALE")
        else:
            age = time.time() - doctor_hits[0].stat().st_mtime
            if age > 6 * 3600:
                checks.append(
                    _check("doctor", "STALE", f"age_sec={int(age)}", str(doctor_hits[0]))
                )
                bump("STALE")
            else:
                checks.append(
                    _check("doctor", "PASS", f"age_sec={int(age)}", str(doctor_hits[0]))
                )

    safety: dict[str, Any] = {
        "ARMED": False,
        "actuator_authority": "UNKNOWN",
        "mqtt_policy": "UNKNOWN",
        "soft_latch": "UNKNOWN",
        "note": "soft_latch_untouched_by_collector",
    }
    if "wave0_soft" in include:
        # board.yaml / state files — read only
        board = Path("/etc/octopus/config/board.yaml")
        text = board.read_text(encoding="utf-8") if board.exists() else ""
        if "PERMITTED_SOFTWARE_A0" in text or "actuator_authority" in text:
            if "PERMITTED_SOFTWARE_A0" in text:
                safety["actuator_authority"] = "PERMITTED_SOFTWARE_A0"
            if "SOFTWARE_LATCH" in text:
                safety["estop_channel"] = "SOFTWARE_LATCH"
            checks.append(_check("wave0.board_yaml", "PASS", "read board.yaml", str(board)))
        else:
            checks.append(_check("wave0.board_yaml", "UNKNOWN", "authority markers not found", str(board)))
            bump("UNKNOWN")
        # ARMED must stay false — look for explicit true
        armed_files = list(STATE_ROOT.glob("**/ARMED*"))[:10]
        armed_true = False
        for af in armed_files:
            try:
                raw = af.read_text(encoding="utf-8")
            except OSError:
                continue
            if "true" in raw.lower() and "armed" in raw.lower():
                armed_true = True
        safety["ARMED"] = bool(armed_true)
        if armed_true:
            checks.append(_check("wave0.ARMED", "FAIL", "ARMED true unexpected"))
            bump("FAIL")
        else:
            checks.append(_check("wave0.ARMED", "PASS", "ARMED false/absent"))

    if "disk" in include:
        code, out = _run(["df", "-h", "/"])
        checks.append(_check("disk.root", "PASS" if code == 0 else "UNKNOWN", out.splitlines()[-1] if out else ""))
        if code != 0:
            bump("UNKNOWN")

    # ESP32 physical — always ABSENT unless explicitly present marker
    esp = STATE_ROOT / "esp32" / "PRESENT"
    if esp.exists():
        checks.append(_check("esp32", "PASS", "PRESENT marker", str(esp)))
    else:
        checks.append(_check("esp32", "ABSENT", "no physical ESP32 marker (not FAIL)"))

    session_rel = ""
    if write_evidence:
        session = EVIDENCE_ROOT / f"session-diag-{_utc()}-{request_id[:12]}"
        try:
            session.mkdir(parents=True, exist_ok=True)
            payload_path = session / "diagnostics.json"
            # write after assembly below
            session_rel = str(session)
        except OSError as exc:
            checks.append(_check("evidence.write", "FAIL", str(exc)))
            bump("FAIL")
            session = None  # type: ignore
    else:
        session = None

    result = {
        "schema": SCHEMA,
        "request_id": request_id,
        "sender_id": sender_id,
        "status": overall if overall != "ABSENT" else "PASS",
        "host": host,
        "checks": checks,
        "artifacts": artifacts,
        "safety": safety,
        "params": {"mutates": False, "include": include},
        "ts_utc": _utc(),
        "signature_verify": "UNVERIFIED_NO_COMMAND_TRUST_ROOT",
    }
    # Recompute overall ignoring ABSENT-only noise
    statuses = {c["status"] for c in checks}
    if "FAIL" in statuses:
        result["status"] = "FAIL"
    elif "DEGRADED" in statuses or "STALE" in statuses:
        result["status"] = "DEGRADED"
    elif "UNKNOWN" in statuses:
        result["status"] = "UNKNOWN"
    else:
        result["status"] = "PASS"

    if session is not None:
        try:
            outp = session / "diagnostics.json"
            outp.write_text(json.dumps(result, indent=2), encoding="utf-8")
            artifacts.append(str(outp))
            result["artifacts"] = artifacts
            outp.write_text(json.dumps(result, indent=2), encoding="utf-8")
        except OSError as exc:
            result.setdefault("checks", []).append(_check("evidence.write", "FAIL", str(exc)))
            result["status"] = "FAIL"

    return result


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Edge Gateway collect_diagnostics (readonly)")
    ap.add_argument("--prove", action="store_true", help="Run local prove (no NATS)")
    ap.add_argument("--request-id", default=f"prove-{_utc()}")
    ap.add_argument("--no-evidence", action="store_true")
    args = ap.parse_args()
    res = collect_diagnostics(
        request_id=args.request_id,
        params={"mutates": False, "include": list(DEFAULT_INCLUDE)},
        sender_id="local-prove",
        write_evidence=not args.no_evidence,
    )
    print(json.dumps(res, indent=2))
    raise SystemExit(0 if res.get("status") in {"PASS", "DEGRADED", "UNKNOWN"} else 1)


if __name__ == "__main__":
    main()
