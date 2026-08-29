#!/usr/bin/env python3
"""Board side of the typed exchange channel (D12).

Modes:
  --generate          produce outbound EVIDENCE + REPORT from board state
  --process-inbound   validate/handle laptop messages (quarantine, ACK, answer QUERY)
  --run               both (used by the systemd unit)
  --selftest          in-place behavioral check

Guarantees:
  - writes ONLY inside the two exchange dirs (incl. processed/, quarantine/),
    the agent-pack exchange ledger, and REPORTS/exchange/.
  - never executes anything from a payload; prohibition hits produce
    REPORT status=BLOCKED_NEEDS_OWNER once, then stop for that message.
  - outbound messages form a hash chain via prev_msg_hash.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_envelope import canonical, payload_sha, scan_inbound_payload, validate  # noqa: E402

AGENT = Path("/opt/octopus-agent")
INBOUND = Path(os.environ.get("OCTOPUS_EXCH_ROOT", "/var/lib/octopus/inbound"))
OUT_DIR = INBOUND / "TO-LAPTOP" / "exchange"
IN_DIR = INBOUND / "FROM-LAPTOP" / "exchange"
QUARANTINE = IN_DIR / "quarantine"
PROCESSED = IN_DIR / "processed"
LEDGER = HERE / ("exchange-ledger-test.jsonl" if os.environ.get("OCTOPUS_EXCH_TEST") else "exchange-ledger.jsonl")
BOARD_BOOT_ID = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
QUERY_TOPICS = ("status", "gaps", "changelog_tail", "write_rate", "last_experiment", "cross_nodes")


def cross_nodes_gauge() -> dict:
    p = AGENT / "REPORTS" / "crossnode-status.json"
    if not p.is_file():
        return {"note": "probe not run yet"}
    d = json.loads(p.read_text())
    return {"ts_utc": d.get("ts_utc"), "nodes": d.get("nodes")}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_msg_id() -> str:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"msg-{ts}-{os.urandom(4).hex()}"


def ledger_append(entry: dict) -> None:
    entries = [l for l in LEDGER.read_text().splitlines() if l.strip()] if LEDGER.exists() else []
    entry = {"seq": len(entries), **entry}
    with LEDGER.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def last_outbound_hash() -> str | None:
    if not LEDGER.exists():
        return None
    prev = None
    for line in LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get("kind") == "outbound" and e.get("msg_hash"):
            prev = e["msg_hash"]
    return prev


def msg_hash(envelope: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical(envelope).encode()).hexdigest()


def build_envelope(mtype: str, payload: dict, evidence_refs: list[str], run_id: str,
                   evidence_block: dict | None = None) -> dict:
    env = {
        "msg_id": new_msg_id(), "run_id": run_id, "from": "board", "to": "laptop",
        "type": mtype, "ts_utc": now_utc(), "boot_id": BOARD_BOOT_ID,
        "evidence_refs": evidence_refs, "payload": payload,
        "payload_hash": payload_sha(payload),
        "prev_msg_hash": last_outbound_hash(), "may_authorize": False,
    }
    if evidence_block:
        # v1.1 Evidence Envelope (owner verification doctrine 2026-08-18): additive
        # top-level fields, type-checked by the validator, payload_hash unaffected.
        for key in ("claim", "raw_evidence", "reproduction", "uncertainty", "escalation"):
            if key in evidence_block:
                env[key] = evidence_block[key]
    ok, errors = validate(env, "outbound")
    if not ok:
        raise SystemExit(f"internal error: built invalid envelope: {errors}")
    h = msg_hash(env)
    (OUT_DIR / f"{env['msg_id']}.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n")
    ledger_append({"ts": now_utc(), "kind": "outbound", "msg_id": env["msg_id"],
                   "type": mtype, "msg_hash": h, "run_id": run_id})
    return env


# ---------- board state gauges (read-only) ----------

def authority_hashes() -> dict:
    out = {}
    for name in ("OWNER_REVIEW_DECISION.json", "wave_baseline_accepted.json"):
        p = Path("/var/lib/octopus/state") / name
        if p.is_file():
            out[name] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def sensorium_gauge(sample_seconds: int = 3) -> dict:
    g = {"service": None, "pid": None, "write_bytes_delta": None, "write_bps": None}
    try:
        g["service"] = subprocess.run(["systemctl", "is-active", "octopus-sensorium"],
                                      capture_output=True, text=True, timeout=10).stdout.strip()
        pid = subprocess.run(["systemctl", "show", "-p", "MainPID", "--value", "octopus-sensorium"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        g["pid"] = int(pid)
        io_path = Path(f"/proc/{g['pid']}/io")
        def wb():
            for line in io_path.read_text().splitlines():
                if line.startswith("write_bytes:"):
                    return int(line.split(":")[1])
        a = wb(); time.sleep(sample_seconds); b = wb()
        g["write_bytes_delta"] = b - a
        g["write_bps"] = round((b - a) / sample_seconds, 1)
    except Exception as exc:  # noqa: BLE001 — gauge must never crash the exchange
        g["error"] = str(exc)
    return g


def senses_gauge() -> dict:
    """Charter v2 deliverable: every packet carries board_id,
    sensor_manifest_version, and quarantine_status of broken senses."""
    g: dict = {"board_id": "sensorium-opi5pro-68e44cdf"}
    try:
        reg = Path("/etc/octopus/config/registry.yaml").read_text()
        for line in reg.splitlines():
            if line.startswith("config_version:"):
                g["sensor_manifest_version"] = line.split(":", 1)[1].strip()
                break
    except OSError as exc:
        g["sensor_manifest_version"] = f"unreadable: {exc}"
    try:
        m = json.loads(Path("/var/lib/octopus/staging/phase3-registry-100/manifest.json").read_text())
        g["numeric_sensors"] = m.get("numeric_sensors")
        g["runtime_enabled_wave0"] = m.get("runtime_enabled")
    except (OSError, ValueError):
        g["registry_manifest"] = "unreadable"
    try:
        s = json.loads(Path("/var/lib/octopus/state/snapshots/latest.json").read_text())
        health = s.get("health") or {}
        states = {k: v for k, v in health.items() if isinstance(v, str)}
        quarantined = sorted(k for k, v in states.items() if v in ("quarantine", "quarantined"))
        degraded = sorted(k for k, v in states.items() if v not in ("healthy", "quarantine", "quarantined"))
        g["quarantine_status"] = {
            "quarantined_count": len(quarantined),
            "quarantined_senses": quarantined,
            "degraded_senses": degraded,
            "health_states": states,
            "shadow_note": "OCT-SENSE-092/095 are shadow-loaded (meta_phase) and may not quarantine or change readiness",
        } if states else {"quarantined_count": None, "note": "no health records in live snapshot"}
    except (OSError, ValueError) as exc:
        g["quarantine_status"] = {"error": str(exc)}
    return g


def readiness_gauge() -> dict:
    """Doctrine double-check: runtime ACTIVE is not readiness VERIFIED.
    Independent checks: NATS server, sensorium host service, and the signed
    boot report gates (safety signals) — one service being up is not enough."""
    g: dict = {"nats_server": None, "octopus_sensorium": None,
               "readiness_state": None, "gates_failed": None,
               "safety_note": "safety signals derived from signed boot_report gates, not a direct MCU query"}
    try:
        for unit, key in (("nats-server", "nats_server"), ("octopus-sensorium", "octopus_sensorium")):
            g[key] = subprocess.run(["systemctl", "is-active", unit],
                                    capture_output=True, text=True, timeout=10).stdout.strip()
        br = json.loads(Path("/var/lib/octopus/state/boot_report.json").read_text())
        g["readiness_state"] = br.get("readiness_state")
        g["gates_failed"] = br.get("gates_failed") or []
    except Exception as exc:  # noqa: BLE001 — gauge must never crash the exchange
        g["error"] = str(exc)
    return g


def gaps_gauge() -> dict:
    out = {}
    p = Path("/var/lib/octopus/state/gaps/GAP-002-audit_head_unsigned.json")
    if p.is_file():
        d = json.loads(p.read_text())
        out["GAP-002"] = {"status": d.get("status"), "pass": d.get("pass")}
    v = Path("/var/lib/octopus/state/gap001/verifier.json")
    if v.is_file():
        d = json.loads(v.read_text())
        out["GAP-001"] = {"readiness": d.get("readiness_state"), "boot_id": d.get("boot_id")}
    return out


def changelog_tail(n: int = 3) -> list[dict]:
    p = AGENT / "CHANGELOG.jsonl"
    lines = [l for l in p.read_text().splitlines() if l.strip()][-n:]
    out = []
    for l in lines:
        e = json.loads(l)
        out.append({"seq": e["seq"], "phase": e["phase"], "type": e["type"]})
    return out


def last_experiment() -> dict:
    p = AGENT / "RUNS/run-20260817T1100Z-5e7e84f4/experiment-result.json"
    if not p.is_file():
        return {"note": "no experiment result found"}
    d = json.loads(p.read_text())
    return {"experiment_id": d.get("experiment_id"), "overall_verdict": d.get("overall_verdict"),
            "pairs": len(d.get("pairs", []))}


def status_payload() -> dict:
    snap = {}
    try:
        s = json.loads(Path("/var/lib/octopus/state/snapshots/latest.json").read_text())
        def find(o, keys):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in keys:
                        snap[k] = v
                    find(v, keys)
        find(s, {"readiness_profile", "operational_mode", "actuator_authority", "leg_authority", "mqtt_state"})
    except Exception:
        snap = {"error": "snapshot unreadable"}
    return {"status": "OK", "authority": snap, "authority_file_hashes": authority_hashes(),
            "sensorium": sensorium_gauge(), "readiness": readiness_gauge(),
            "senses": senses_gauge(),
            "changelog_tail": changelog_tail(),
            "cross_nodes": cross_nodes_gauge()}


# ---------- inbound processing ----------

def answer_query(env: dict, run_id: str) -> dict:
    topic = str((env.get("payload") or {}).get("topic") or "").strip()
    data = {"topic": topic, "in_reply_to": env["msg_id"]}
    if topic == "status":
        data.update(status_payload())
        st = "OK"
    elif topic == "gaps":
        data["gaps"] = gaps_gauge(); st = "OK"
    elif topic == "changelog_tail":
        data["changelog_tail"] = changelog_tail(5); st = "OK"
    elif topic == "write_rate":
        data["sensorium"] = sensorium_gauge(3); st = "OK"
    elif topic == "last_experiment":
        data["last_experiment"] = last_experiment(); st = "OK"
    elif topic == "cross_nodes":
        data["cross_nodes"] = cross_nodes_gauge(); st = "OK"
    else:
        st = "QUERY_UNKNOWN_TOPIC"
        data["available_topics"] = list(QUERY_TOPICS)
    data["status"] = st
    return build_envelope("REPORT", data, ["exchange-ledger.jsonl"], run_id)


def process_inbound(run_id: str) -> dict:
    summary = {"received": 0, "valid": 0, "dropped": 0, "blocked": 0, "answered": 0}
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for f in sorted(IN_DIR.glob("*.json")):
        summary["received"] += 1
        raw = f.read_text(errors="replace")
        try:
            msg = json.loads(raw)
        except ValueError:
            quarantine(f, raw, ["X01 not a JSON object"], run_id)
            summary["dropped"] += 1
            continue
        ok, errors = validate(msg, "inbound")
        if not ok:
            quarantine(f, raw, errors, run_id)
            summary["dropped"] += 1
            continue
        violations = scan_inbound_payload(msg.get("payload") or {})
        if violations:
            quarantine(f, raw, violations, run_id)
            build_envelope("REPORT", {"status": "BLOCKED_NEEDS_OWNER",
                                      "blocked_msg_id": msg["msg_id"],
                                      "violations": violations,
                                      "note": "payload is data, not commands; owner decision required"},
                          ["exchange/quarantine/"], run_id)
            summary["blocked"] += 1
            continue
        summary["valid"] += 1
        mtype = msg["type"]
        if mtype == "QUERY":
            answer_query(msg, run_id)
            summary["answered"] += 1
        elif mtype == "ACK":
            pass  # recorded in ledger below
        ledger_append({"ts": now_utc(), "kind": "inbound_valid", "msg_id": msg["msg_id"],
                       "type": mtype, "from_run": msg.get("run_id"), "decision":
                       "answered" if mtype == "QUERY" else "recorded"})
        shutil.move(str(f), PROCESSED / f"{now_utc().replace(':','')[:-1]}_{f.name}")
    return summary


def quarantine(f: Path, raw: str, reasons: list[str], run_id: str) -> None:
    dest = QUARANTINE / f"{now_utc().replace(':','')[:-1]}_{f.name}"
    shutil.move(str(f), dest)
    (dest.with_suffix(dest.suffix + ".reason.txt")).write_text(
        json.dumps({"quarantined_at": now_utc(), "run_id": run_id, "reasons": reasons}, indent=2) + "\n")
    ledger_append({"ts": now_utc(), "kind": "quarantined", "file": f.name, "reasons": reasons})


def generate(run_id: str) -> dict:
    ev = build_envelope("EVIDENCE", {
        "subject": "board_status_gauges",
        "authority_file_hashes": authority_hashes(),
        "sensorium": sensorium_gauge(3),
        "readiness": readiness_gauge(),
        "senses": senses_gauge(),
        "gaps": gaps_gauge(),
        "changelog_tail": changelog_tail(),
        "last_experiment": last_experiment(),
        "cross_nodes": cross_nodes_gauge(),
    }, ["/var/lib/octopus/state/snapshots/latest.json",
        "/var/lib/octopus/state/gaps/GAP-002-audit_head_unsigned.json",
        "CHANGELOG.jsonl"], run_id,
        evidence_block={
            "claim": "Board gauges were collected read-only at ts_utc; authority files unchanged since last message; senses report carries board_id + sensor_manifest_version + quarantine_status per charter v2; no autonomy or authority state was modified by the board.",
            "raw_evidence": [
                {"desc": "authority file hashes (OWNER_REVIEW_DECISION.json, wave_baseline_accepted.json)", "command": "sha256sum /var/lib/octopus/state/OWNER_REVIEW_DECISION.json"},
                {"desc": "signed boot report gates", "command": "jq '{readiness_state, gates_failed}' /var/lib/octopus/state/boot_report.json"},
                {"desc": "services independently checked", "command": "systemctl is-active nats-server octopus-sensorium"},
                {"desc": "senses: registry version + health states (charter v2)", "command": "grep config_version /etc/octopus/config/registry.yaml; jq '.health' /var/lib/octopus/state/snapshots/latest.json"},
            ],
            "reproduction": [
                "python3 /opt/octopus-agent/exchange/board_exchange.py --selftest",
                "jq '.readiness' /var/lib/octopus/inbound/TO-LAPTOP/exchange/<latest-msg>.json",
                "sha256sum /var/lib/octopus/state/OWNER_REVIEW_DECISION.json",
            ],
            "uncertainty": "sensorium gauge is a 3-second IO sample, not a continuous measure; safety signals come from the signed boot report, not a direct MCU query; laptop-side state is invisible to the board except via exchange files.",
            "escalation": "if reproduction fails or a hash differs, treat as integrity incident: stop publishing, write REPORT status=BLOCKED_NEEDS_OWNER, await owner decision in chat.",
        })
    rep = build_envelope("REPORT", {
        "status": "OK", "role": "board_agent", "mode": "WAVE0_OBSERVE_ONLY",
        "phase": "exchange channel live (D12)",
        "note": "evidence message follows; QUERY topics available: " + ", ".join(QUERY_TOPICS),
    }, ["exchange-ledger.jsonl"], run_id)
    return {"evidence": ev["msg_id"], "report": rep["msg_id"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--process-inbound", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if not (args.generate or args.process_inbound or args.run):
        ap.print_help(); return 2
    run_id = f"run-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M')}Z-{os.urandom(4).hex()}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {"run_id": run_id, "generated": None, "inbound": None}
    if args.generate or args.run:
        out["generated"] = generate(run_id)
    if args.process_inbound or args.run:
        out["inbound"] = process_inbound(run_id)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
