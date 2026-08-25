#!/usr/bin/env python3
"""15-minute homogeneous soak after GET_PURE + LAN token deploy. No llama restart."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ofn.organism.cognition import active_inference as ai
from ofn.organism.runtime.lan_auth import TOKEN_HEADER, load_lan_token
from ofn.organism.science import wbe_allometry as wbe

LAB = Path("/opt/octopus/lab")
DB = LAB / "lab-data/organism.db"
ART = LAB / "artifacts/completion-phase3"
RECEIPTS = ART / "receipts"
TOKEN_FILE = Path("/etc/octopus/lan-token")
SOAK_LIVE = LAB / "evidence/SOAK-RESULTS.json"
DURATION_S = 15 * 60
MIN_HEARTBEATS = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(LAB), *args], text=True).strip()


def unit_show(unit: str) -> dict:
    raw = subprocess.check_output(
        [
            "systemctl",
            "show",
            unit,
            "-p",
            "MainPID,ActiveState,NRestarts,ExecMainStartTimestamp",
            "--no-pager",
        ],
        text=True,
    )
    out = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def tcp_ok(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def disk() -> dict:
    st = os.statvfs("/")
    avail = st.f_bavail * st.f_frsize
    return {
        "avail_bytes": avail,
        "avail_gib": round(avail / 1024**3, 3),
        "used_pct": round(100.0 * (1.0 - (st.f_bavail / st.f_blocks)), 2),
    }


def mem_avail_kib() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1])
    return -1


def temp_mc() -> int:
    return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip())


def ro() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    return con


def db_snap() -> dict:
    con = ro()
    try:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

        def count(table: str) -> int:
            return 0 if table not in names else con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        ident = con.execute(
            "SELECT sequence, entry_hash FROM identity_ledger ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        events = con.execute("SELECT MAX(node_seq), COUNT(*) FROM events").fetchone()
        version = con.execute("SELECT v FROM meta WHERE k='schema_migration_version'").fetchone()
        return {
            "schema": None if not version else version[0],
            "identity_head": {"sequence": ident[0], "entry_hash": ident[1]} if ident else {},
            "events_max": events[0],
            "events": events[1],
            "episodes": count("episodes"),
            "outbox": count("outbox"),
            "identity": count("identity_ledger"),
            "memory_read_receipts": count("memory_read_receipts"),
            "decision_evidence": count("decision_evidence"),
            "heartbeat_events": con.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='heartbeat'"
            ).fetchone()[0],
            "wan_fetches": count("wan_fetches"),
            "quick_check": con.execute("PRAGMA quick_check").fetchone()[0],
        }
    finally:
        con.close()


def identity_valid() -> bool:
    raw = subprocess.check_output(
        ["python3", str(LAB / "bin/verify-identity-chain.py"), "--db", str(DB)],
        text=True,
    )
    return bool(json.loads(raw)["valid"])


def token_headers() -> dict[str, str]:
    return {TOKEN_HEADER: load_lan_token()}


def http_json(url: str, headers: dict | None = None, timeout: float = 5) -> tuple[int, dict | None]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            body = json.loads(raw.decode()) if raw else None
            return int(resp.status), body
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode())
        except Exception:
            body = None
        return int(exc.code), body
    except Exception:
        return 0, None


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def purity_probe(attempts: int = 3) -> dict:
    public = LAB / "state/ORGANISM-PUBLIC.json"
    attest = LAB / "state/ATTESTATION.json"
    last = {}
    for _ in range(attempts):
        before = db_snap()
        hashes_before = {"public": file_hash(public), "attestation": file_hash(attest)}
        statuses = []
        for _repeat in range(3):
            status, _ = http_json("http://127.0.0.1:8090/api/v1/organism", token_headers())
            statuses.append(status)
            status2, _ = http_json("http://127.0.0.1:8090/api/v1/utterance", token_headers())
            statuses.append(status2)
        after = db_snap()
        hashes_after = {"public": file_hash(public), "attestation": file_hash(attest)}
        keys = (
            "events",
            "events_max",
            "episodes",
            "outbox",
            "identity",
            "identity_head",
            "memory_read_receipts",
            "decision_evidence",
        )
        cognitive = {k: before[k] for k in keys}
        cognitive_after = {k: after[k] for k in keys}
        delta = 0 if cognitive == cognitive_after and hashes_before == hashes_after else 1
        last = {
            "http_statuses": statuses,
            "GET_STATE_DELTA": delta,
            "before": cognitive,
            "after": cognitive_after,
            "file_hashes_changed": hashes_before != hashes_after,
        }
        if delta == 0:
            return last
        time.sleep(2)
    return last


def watcher_running() -> bool:
    path = RECEIPTS / "watcher.heartbeat.json"
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    age = time.time() - path.stat().st_mtime
    return bool(payload.get("running")) and age < 45


def ensure_token() -> None:
    if TOKEN_FILE.is_file() and (TOKEN_FILE.stat().st_mode & 0o777) == 0o600:
        if len(TOKEN_FILE.read_bytes().strip()) >= 32:
            return
    subprocess.check_call(
        ["bash", "-c", "umask 077; head -c 32 /dev/urandom | base64 -w0 > /etc/octopus/lan-token; chmod 0600 /etc/octopus/lan-token"]
    )


def close_mixed_soak() -> dict:
    soak_unit = unit_show("octopus-soak-lab")
    live = {}
    if SOAK_LIVE.is_file():
        live = json.loads(SOAK_LIVE.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = LAB / f"evidence/SOAK-RESULTS-MIXED-VERSION-{stamp}.json"
    if SOAK_LIVE.is_file():
        shutil.copy2(SOAK_LIVE, archive)
    stop = run(["systemctl", "stop", "octopus-soak-lab"])
    snap = db_snap()
    payload = {
        "SOAK_TYPE": "MIXED_VERSION",
        "OLD_SKIN_INCLUDED": True,
        "NEW_SKIN_INCLUDED": True,
        "VALID_FOR_CONTINUITY": True,
        "VALID_FOR_HOMOGENEOUS_RELEASE": False,
        "closed_at": utc_now(),
        "archive": str(archive),
        "last_sample": live.get("last"),
        "abort": live.get("abort"),
        "samples": live.get("samples"),
        "identity_head": snap["identity_head"],
        "soak_pid_at_close": int(soak_unit.get("MainPID") or 0),
        "stop_rc": stop.returncode,
    }
    write_json(RECEIPTS / "14_mixed_soak_closeout.json", payload)
    return payload


def write_dropins() -> None:
    org = Path("/etc/systemd/system/octopus-organism-lab.service.d")
    org.mkdir(parents=True, exist_ok=True)
    (org / "phase3-compat.conf").write_text(
        "[Service]\n"
        "Environment=OCTOPUS_GET_PURE=1\n"
        "Environment=OCTOPUS_REQUIRE_LAN_TOKEN=1\n"
        "Environment=OCTOPUS_LEARN_EXTERNAL=0\n"
        "Environment=OCTOPUS_LAN_TOKEN_FILE=/etc/octopus/lan-token\n",
        encoding="utf-8",
    )
    soak = Path("/etc/systemd/system/octopus-soak-lab.service.d")
    soak.mkdir(parents=True, exist_ok=True)
    (soak / "phase31-token.conf").write_text(
        "[Service]\n"
        "Environment=OCTOPUS_REQUIRE_LAN_TOKEN=1\n"
        "Environment=OCTOPUS_LAN_TOKEN_FILE=/etc/octopus/lan-token\n"
        "Environment=PYTHONPATH=/opt/octopus/lab\n",
        encoding="utf-8",
    )
    run(["systemctl", "daemon-reload"])


def restart_organism(prev_identity: int, prev_heartbeats: int) -> dict:
    old = unit_show("octopus-organism-lab")
    t0 = time.time()
    stop = run(["systemctl", "restart", "octopus-organism-lab"])
    deadline = time.time() + 90
    ok = False
    new = {}
    while time.time() < deadline:
        new = unit_show("octopus-organism-lab")
        health, _body = http_json("http://127.0.0.1:8090/health")
        try:
            ident_now = db_snap()["identity"]
            hb_now = db_snap()["heartbeat_events"]
        except Exception:
            ident_now = prev_identity
            hb_now = prev_heartbeats
        if (
            new.get("ActiveState") == "active"
            and int(new.get("MainPID") or 0) not in {0, int(old.get("MainPID") or 0)}
            and health == 200
            and ident_now > prev_identity
            and hb_now > prev_heartbeats
        ):
            ok = True
            break
        time.sleep(1)
    return {
        "ok": ok,
        "stop_rc": stop.returncode,
        "downtime_s": round(time.time() - t0, 3),
        "old_pid": int(old.get("MainPID") or 0),
        "new_pid": int(new.get("MainPID") or 0),
        "nrestarts": new.get("NRestarts"),
    }


def main() -> int:
    os.environ["OCTOPUS_REQUIRE_LAN_TOKEN"] = "1"
    os.environ["OCTOPUS_LAN_TOKEN_FILE"] = str(TOKEN_FILE)
    os.environ["PYTHONPATH"] = str(LAB)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ensure_token()
    mixed = close_mixed_soak()
    write_dropins()
    prev = db_snap()
    restarted = restart_organism(prev["identity"], prev["heartbeat_events"])
    if not restarted["ok"]:
        print("ORGANISM_RESTART_FAILED", json.dumps(restarted))
        return 2
    time.sleep(2)
    unauth_status, unauth_body = http_json("http://192.168.0.180:8090/api/v1/organism")
    auth_status, auth_body = http_json(
        "http://192.168.0.180:8090/api/v1/organism",
        token_headers(),
    )
    loop_health, _ = http_json("http://127.0.0.1:8090/health")
    eval_status, eval_body = http_json(
        "http://127.0.0.1:8090/api/v1/eval",
        token_headers(),
    )
    purity = purity_probe()
    llama = unit_show("octopus-llama-lab")
    start_snap = db_snap()
    start = {
        "recorded_at": utc_now(),
        "source_hash": git("rev-parse", "HEAD"),
        "pid": restarted["new_pid"],
        "old_pid": restarted["old_pid"],
        "schema_version": start_snap["schema"],
        "identity_head": start_snap["identity_head"],
        "event_head": start_snap["events_max"],
        "database_counts": start_snap,
        "disk": disk(),
        "ram_avail_kib": mem_avail_kib(),
        "temperature_mC": temp_mc(),
        "organism_nrestarts": restarted["nrestarts"],
        "llama_pid": int(llama.get("MainPID") or 0),
        "unauthenticated_lan_status": unauth_status,
        "authenticated_lan_status": auth_status,
        "loopback_health_status": loop_health,
        "eval_get_status": eval_status,
        "GET_STATE_DELTA": purity["GET_STATE_DELTA"],
        "purity": purity,
        "UNAUTHENTICATED_LAN_ACCEPTED": unauth_status == 200,
        "IDENTITY_CHAIN_VALID": identity_valid(),
        "mixed_soak_closeout": str(RECEIPTS / "14_mixed_soak_closeout.json"),
        "downtime_s": restarted["downtime_s"],
        "OCTOPUS_GET_PURE": "1",
        "OCTOPUS_REQUIRE_LAN_TOKEN": "1",
        "OCTOPUS_LEARN_EXTERNAL": "0",
        "WAVE0_OBSERVE_ONLY": True,
        "PROPOSE_ONLY": True,
        "token_in_auth_body": False if not isinstance(auth_body, dict) else TOKEN_HEADER.lower() in json.dumps(auth_body).lower(),
    }
    write_json(RECEIPTS / "15_fresh_soak_15min_start.json", start)
    if unauth_status == 200 or auth_status != 200 or loop_health != 200 or purity["GET_STATE_DELTA"] != 0:
        print("SECURITY_VERIFY_FAILED", json.dumps({k: start[k] for k in ("unauthenticated_lan_status", "authenticated_lan_status", "loopback_health_status", "GET_STATE_DELTA")}))
        return 2

    watcher = subprocess.Popen(
        [sys.executable, str(LAB / "bin/checkpoint-watcher.py")],
        cwd=str(LAB),
        env={**os.environ, "PYTHONPATH": str(LAB)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    soak_start = run(["systemctl", "start", "octopus-soak-lab"])
    if soak_start.returncode != 0:
        watcher.terminate()
        print("SOAK_START_FAILED", soak_start.stderr)
        return 2

    t0 = time.time()
    samples = []
    abort = None
    health_states = []
    ram_min = mem_avail_kib()
    temp_max = temp_mc()
    auth_failures = 0
    unauth_accepted = False
    while time.time() - t0 < DURATION_S:
        snap = db_snap()
        soak = json.loads(SOAK_LIVE.read_text()) if SOAK_LIVE.is_file() else {}
        life = json.loads((LAB / "state/LIFE.json").read_text()) if (LAB / "state/LIFE.json").is_file() else {}
        org = unit_show("octopus-organism-lab")
        ram = mem_avail_kib()
        temp = temp_mc()
        ram_min = min(ram_min, ram) if ram > 0 else ram_min
        temp_max = max(temp_max, temp)
        dsk = disk()
        hb_new = snap["heartbeat_events"] - start_snap["heartbeat_events"]
        health = life.get("health_state")
        if health and (not health_states or health_states[-1] != health):
            health_states.append(health)
        unauth_now, _ = http_json("http://192.168.0.180:8090/api/v1/organism")
        if unauth_now == 200:
            unauth_accepted = True
            abort = "unauthenticated_LAN_request_accepted"
        mid = {
            "t": utc_now(),
            "elapsed_s": int(time.time() - t0),
            "pid": int(org.get("MainPID") or 0),
            "nrestarts": int(org.get("NRestarts") or 0),
            "health": health,
            "heartbeat_events_new": hb_new,
            "memory_read_receipts": snap["memory_read_receipts"],
            "decision_evidence": snap["decision_evidence"],
            "events": snap["events"],
            "identity": snap["identity"],
            "wan_fetches": snap["wan_fetches"],
            "soak_abort": soak.get("abort"),
            "watcher_running": watcher_running(),
            "unauth_lan": unauth_now,
            "ram_avail_kib": ram,
            "temp_mC": temp,
            "disk": dsk,
            "identity_valid": identity_valid(),
            "quick_check": snap["quick_check"],
        }
        samples.append(mid)
        write_json(RECEIPTS / "15min_observe.json", {"samples": samples[-8:]})
        reasons = []
        if int(ai.EXECUTABLE) + int(wbe.EXECUTABLE) > 0:
            reasons.append("executable_total")
        if not mid["identity_valid"]:
            reasons.append("identity_chain_valid")
        if snap["quick_check"] != "ok":
            reasons.append("sqlite_integrity")
        if snap["wan_fetches"] > start_snap["wan_fetches"]:
            reasons.append("wan_fetches")
        if mid["nrestarts"] > int(restarted["nrestarts"] or 0):
            reasons.append("service_restart_count")
        if not mid["watcher_running"]:
            reasons.append("checkpoint_watcher_running")
        if dsk["avail_bytes"] < 5 * 1024**3 or dsk["used_pct"] >= 92:
            reasons.append("disk")
        if ram >= 0 and ram < 350 * 1024:
            reasons.append("ram")
        if temp > 0 and (115000 - temp) < 10000:
            reasons.append("thermal")
        if snap["events_max"] < start_snap["events_max"]:
            reasons.append("event_sequence_regression")
        if snap["identity_head"]["sequence"] < start_snap["identity_head"]["sequence"]:
            reasons.append("identity_rewound")
        if soak.get("abort"):
            reasons.append("soak_abort")
        if int(org.get("MainPID") or 0) != restarted["new_pid"]:
            reasons.append("pid_changed")
        if llama.get("MainPID") != unit_show("octopus-llama-lab").get("MainPID"):
            reasons.append("llama_restarted")
        if unauth_now not in {401, 429}:
            if unauth_now == 200:
                reasons.append("unauthenticated_LAN_request_accepted")
            auth_failures += 1
        if reasons:
            abort = ",".join(reasons)
            break
        time.sleep(15)

    purity_end = purity_probe()
    end_snap = db_snap()
    hb_obs = end_snap["heartbeat_events"] - start_snap["heartbeat_events"]
    elapsed = int(time.time() - t0)
    if abort is None and hb_obs < MIN_HEARTBEATS:
        abort = "minimum_heartbeats_not_reached"
    closeout = {
        "recorded_at": utc_now(),
        "elapsed_s": elapsed,
        "SOAK_DURATION_MINUTES": round(elapsed / 60, 2),
        "HEARTBEATS_EXPECTED": "3_TO_4",
        "HEARTBEATS_OBSERVED": hb_obs,
        "MINIMUM_HEARTBEATS_REACHED": hb_obs >= MIN_HEARTBEATS,
        "health_transitions": health_states,
        "MEMORY_RECEIPTS_ADDED": end_snap["memory_read_receipts"] - start_snap["memory_read_receipts"],
        "DECISION_EVIDENCE_ADDED": end_snap["decision_evidence"] - start_snap["decision_evidence"],
        "events_added": end_snap["events"] - start_snap["events"],
        "identity_added": end_snap["identity"] - start_snap["identity"],
        "db_size_bytes": DB.stat().st_size,
        "wal_size_bytes": (DB.with_suffix(".db-wal").stat().st_size if DB.with_suffix(".db-wal").exists() else 0),
        "minimum_ram_kib": ram_min,
        "maximum_temperature_mC": temp_max,
        "authentication_failures_non_401": auth_failures,
        "GET_STATE_DELTA": purity_end["GET_STATE_DELTA"],
        "UNAUTHENTICATED_LAN_ACCEPTED": unauth_accepted,
        "IDENTITY_CHAIN_VALID": identity_valid(),
        "SERVICE_RESTARTS": int(unit_show("octopus-organism-lab").get("NRestarts") or 0),
        "WAN_FETCHES": end_snap["wan_fetches"] - start_snap["wan_fetches"],
        "EXECUTABLE_TOTAL": int(ai.EXECUTABLE) + int(wbe.EXECUTABLE),
        "abort": abort,
        "samples": samples,
        "watcher_pid": watcher.pid,
        "LONG_TERM_STABILITY_PROVEN": False,
        "SHORT_HOMOGENEOUS_SOAK_PASS": abort is None,
    }
    write_json(RECEIPTS / "16_fresh_soak_15min_closeout.json", closeout)
    watcher.terminate()
    report = ART / "26_fresh_soak_15min_report.md"
    report.write_text(
        "\n".join(
            [
                "# 15-minute homogeneous soak report",
                "",
                f"SOAK_DURATION_MINUTES: {closeout['SOAK_DURATION_MINUTES']}",
                f"HEARTBEATS_EXPECTED: {closeout['HEARTBEATS_EXPECTED']}",
                f"HEARTBEATS_OBSERVED: {closeout['HEARTBEATS_OBSERVED']}",
                f"MEMORY_RECEIPTS_ADDED: {closeout['MEMORY_RECEIPTS_ADDED']}",
                f"DECISION_EVIDENCE_ADDED: {closeout['DECISION_EVIDENCE_ADDED']}",
                f"GET_STATE_DELTA: {closeout['GET_STATE_DELTA']}",
                f"UNAUTHENTICATED_LAN_ACCEPTED: {closeout['UNAUTHENTICATED_LAN_ACCEPTED']}",
                f"IDENTITY_CHAIN_VALID: {closeout['IDENTITY_CHAIN_VALID']}",
                f"SERVICE_RESTARTS: {closeout['SERVICE_RESTARTS']}",
                f"WAN_FETCHES: {closeout['WAN_FETCHES']}",
                f"EXECUTABLE_TOTAL: {closeout['EXECUTABLE_TOTAL']}",
                f"FINAL_STATUS: {'SHORT_HOMOGENEOUS_SOAK_PASS' if abort is None else abort}",
                "",
                "This is a smoke test, not long-term stability proof.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({k: closeout[k] for k in (
        "SOAK_DURATION_MINUTES",
        "HEARTBEATS_EXPECTED",
        "HEARTBEATS_OBSERVED",
        "MEMORY_RECEIPTS_ADDED",
        "DECISION_EVIDENCE_ADDED",
        "GET_STATE_DELTA",
        "UNAUTHENTICATED_LAN_ACCEPTED",
        "IDENTITY_CHAIN_VALID",
        "SERVICE_RESTARTS",
        "WAN_FETCHES",
        "EXECUTABLE_TOTAL",
        "SHORT_HOMOGENEOUS_SOAK_PASS",
        "abort",
    )}, indent=2))
    return 0 if abort is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
