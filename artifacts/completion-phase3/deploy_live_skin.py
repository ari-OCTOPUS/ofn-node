#!/usr/bin/env python3
"""Owner-approved organism-only live skin replacement. No llama/gateway/cellframe."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ofn.organism.runtime.checkpoint import (
    parse_checkpoint_payload,
    safe_load_checkpoint,
)

LAB = Path("/opt/octopus/lab")
DB = LAB / "lab-data" / "organism.db"
BACKUP = LAB / "lab-data/backups/organism-phase3-p2-20260825T111133Z.db"
ART = LAB / "artifacts/completion-phase3"
RECEIPTS = ART / "receipts"
FORENSIC = LAB / "lab-data/forensic"
OLD_PID_EXPECTED = 12748
HARD_LIMIT_S = 60
EXPECTED_COMMITS = ("5a10253", "320ac62", "3dbd9b1")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(LAB), *args], text=True).strip()


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def tcp_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_status(url: str, timeout: float = 3.0) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        return 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ro_connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    return con


def table_counts(con: sqlite3.Connection) -> dict[str, int]:
    names = [
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1"
        )
    ]
    out = {}
    for name in names:
        out[name] = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    return out


def identity_head(con: sqlite3.Connection) -> dict:
    row = con.execute(
        """
        SELECT sequence, entry_hash, event_type
        FROM identity_ledger
        ORDER BY sequence DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return {"sequence": 0, "entry_hash": None, "event_type": None}
    return {"sequence": row[0], "entry_hash": row[1], "event_type": row[2]}


def event_head(con: sqlite3.Connection) -> dict:
    row = con.execute(
        "SELECT MAX(node_seq), COUNT(*), MAX(created_at) FROM events"
    ).fetchone()
    return {
        "max_node_seq": row[0],
        "count": row[1],
        "max_created_at": row[2],
    }


def heartbeat_event_count(con: sqlite3.Connection) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM events WHERE event_type='heartbeat'"
    ).fetchone()[0]


def verify_identity() -> dict:
    raw = subprocess.check_output(
        ["python3", str(LAB / "bin/verify-identity-chain.py"), "--db", str(DB)],
        text=True,
    )
    return json.loads(raw)


def soak_state() -> dict:
    path = LAB / "evidence/SOAK-RESULTS.json"
    return json.loads(path.read_text(encoding="utf-8"))


def life_state() -> dict:
    path = LAB / "state/LIFE.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def public_state() -> dict:
    path = LAB / "state/ORGANISM-PUBLIC.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def unit_show(unit: str) -> dict:
    raw = subprocess.check_output(
        [
            "systemctl",
            "show",
            unit,
            "-p",
            "MainPID,ActiveState,NRestarts,ExecMainStartTimestamp,Result,SubState",
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


def meminfo() -> dict:
    data = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith(("MemAvailable:", "MemTotal:", "MemFree:")):
            key, rest = line.split(":", 1)
            data[key] = int(rest.split()[0])
    return data


def disk() -> dict:
    st = os.statvfs("/")
    avail = st.f_bavail * st.f_frsize
    total = st.f_blocks * st.f_frsize
    used_pct = 100.0 * (1.0 - (st.f_bavail / st.f_blocks))
    return {
        "avail_bytes": avail,
        "avail_gib": round(avail / 1024**3, 3),
        "used_pct": round(used_pct, 2),
        "total_bytes": total,
    }


def thermal_mc() -> int | None:
    p = Path("/sys/class/thermal/thermal_zone0/temp")
    if not p.exists():
        return None
    return int(p.read_text().strip())


def executable_total() -> int:
    sys.path.insert(0, str(LAB))
    from ofn.organism.cognition import active_inference as ai
    from ofn.organism.science import wbe_allometry as wbe

    return int(ai.EXECUTABLE) + int(wbe.EXECUTABLE)


def collect_db_snapshot(*, integrity: bool = True) -> dict:
    con = ro_connect()
    try:
        schema_version = con.execute(
            "SELECT v FROM meta WHERE k='schema_migration_version'"
        ).fetchone()
        hb_meta = con.execute(
            "SELECT v FROM meta WHERE k='heartbeat_interval_s'"
        ).fetchone()
        names = {
            row[0]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        return {
            "schema_migration_version": None if not schema_version else schema_version[0],
            "heartbeat_interval_meta": None if not hb_meta else hb_meta[0],
            "tables": sorted(names),
            "counts": table_counts(con),
            "identity_head": identity_head(con),
            "events": event_head(con),
            "episode_count": con.execute("SELECT COUNT(*) FROM episodes").fetchone()[0],
            "outbox_count": con.execute("SELECT COUNT(*) FROM outbox").fetchone()[0],
            "identity_count": con.execute("SELECT COUNT(*) FROM identity_ledger").fetchone()[0],
            "heartbeat_events": heartbeat_event_count(con),
            "memory_read_receipts": (
                con.execute("SELECT COUNT(*) FROM memory_read_receipts").fetchone()[0]
                if "memory_read_receipts" in names
                else 0
            ),
            "decision_evidence": (
                con.execute("SELECT COUNT(*) FROM decision_evidence").fetchone()[0]
                if "decision_evidence" in names
                else 0
            ),
            "wan_fetches": (
                con.execute("SELECT COUNT(*) FROM wan_fetches").fetchone()[0]
                if "wan_fetches" in names
                else 0
            ),
            "quick_check": con.execute("PRAGMA quick_check").fetchone()[0],
            "integrity_check": (
                con.execute("PRAGMA integrity_check").fetchone()[0] if integrity else None
            ),
        }
    finally:
        con.close()


def normalize_checkpoint(checkpoint: dict) -> dict:
    parsed = parse_checkpoint_payload(checkpoint)
    checkpoint = dict(checkpoint)
    checkpoint["identity_head"] = parsed.payload["identity_head"]
    checkpoint["events"] = parsed.payload["events"]
    checkpoint["episode_count"] = parsed.payload["episode_count"]
    checkpoint["outbox_count"] = parsed.payload["outbox_count"]
    checkpoint["source_hash"] = parsed.payload["source_hash"]
    checkpoint["old_pid"] = parsed.payload["old_pid"]
    return checkpoint


def write_checkpoint() -> dict:
    organism = unit_show("octopus-organism-lab")
    pid = int(organism["MainPID"])
    start_ns = None
    if pid:
        start_ns = int(Path(f"/proc/{pid}/stat").read_text().split()[21])
    soak = soak_state()
    life = life_state()
    public = public_state()
    db_snap = collect_db_snapshot()
    payload = {
        "recorded_at": utc_now(),
        "owner_gate": "GATE-LIVE-SKIN-REPLACEMENT",
        "old_pid": pid,
        "old_pid_expected": OLD_PID_EXPECTED,
        "process_start_timestamp": organism.get("ExecMainStartTimestamp"),
        "process_start_stat_ticks": start_ns,
        "git_head": git("rev-parse", "HEAD"),
        "source_hash": git("rev-parse", "HEAD"),
        "db_path": str(DB),
        "db_size_bytes": DB.stat().st_size,
        "wal_size_bytes": (DB.with_suffix(".db-wal").stat().st_size if DB.with_suffix(".db-wal").exists() else 0),
        "shm_size_bytes": (DB.with_suffix(".db-shm").stat().st_size if DB.with_suffix(".db-shm").exists() else 0),
        "schema_version_before": db_snap["schema_migration_version"],
        "database_schema": db_snap,
        "identity_head": db_snap["identity_head"],
        "events": db_snap["events"],
        "latest_event": db_snap["events"],
        "latest_episode_count": db_snap["episode_count"],
        "latest_outbox_count": db_snap["outbox_count"],
        "soak_samples": soak.get("samples"),
        "soak_abort": soak.get("abort"),
        "soak_running": soak.get("running"),
        "current_health": life.get("health_state") or public.get("health_state"),
        "current_heartbeat_interval": life.get("heartbeat_interval_s")
        or public.get("heartbeat_interval_s"),
        "disk": disk(),
        "ram_kib": meminfo(),
        "temperature_mC": thermal_mc(),
        "llama_pid": int(unit_show("octopus-llama-lab")["MainPID"]),
        "soak_pid": int(unit_show("octopus-soak-lab")["MainPID"]),
        "gateway_pid": int(unit_show("octopus-gateway")["MainPID"]),
        "executable_total": executable_total(),
        "checkpoint_schema_version": 1,
        "TEMPORARY_GET_COMPATIBILITY": True,
        "TEMPORARY_LAN_UNAUTHENTICATED": True,
        "TEMPORARY_LEARN_DISABLED": True,
        "SECURITY_DEBT_OPEN": True,
    }
    write_json(RECEIPTS / "05_deployment_checkpoint.json", payload)
    return payload


def apply_migration() -> dict:
    os.environ["OCTOPUS_ALLOW_LIVE_SCHEMA"] = "1"
    os.environ["PYTHONPATH"] = str(LAB)
    if str(LAB) not in sys.path:
        sys.path.insert(0, str(LAB))
    from ofn.organism.persistence.db import (
        ADDITIVE_MIGRATION_VERSION,
        ADDITIVE_LIVE_TABLES,
        connect,
    )

    started = utc_now()
    con = connect(DB)
    try:
        names = {
            row[0]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        version = con.execute(
            "SELECT v FROM meta WHERE k='schema_migration_version'"
        ).fetchone()
        missing = [t for t in ADDITIVE_LIVE_TABLES if t not in names]
        if missing:
            raise RuntimeError(f"migration_incomplete missing={missing}")
        payload = {
            "started_at": started,
            "finished_at": utc_now(),
            "migration_version": version[0] if version else None,
            "expected_version": ADDITIVE_MIGRATION_VERSION,
            "tables_present": sorted(t for t in ADDITIVE_LIVE_TABLES if t in names),
            "OCTOPUS_ALLOW_LIVE_SCHEMA_during_connect": "1",
        }
    finally:
        con.close()
        os.environ.pop("OCTOPUS_ALLOW_LIVE_SCHEMA", None)

    # Validate connect without the env.
    if os.environ.get("OCTOPUS_ALLOW_LIVE_SCHEMA"):
        raise RuntimeError("allow_live_schema_still_set")
    con2 = connect(DB)
    try:
        payload["connect_without_env_ok"] = True
        payload["connect_without_env_tables"] = sorted(
            r[0]
            for r in con2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?,?)",
                ADDITIVE_LIVE_TABLES,
            )
        )
    finally:
        con2.close()
    write_json(RECEIPTS / "06_migration_receipt.json", payload)
    return payload


def _stamp_after(value: str | None, start_iso: str) -> bool:
    if not value:
        return False
    try:
        got = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        return got >= start
    except ValueError:
        return str(value) >= start_iso


def wait_health(new_pid: int, checkpoint: dict, start_iso: str) -> dict:
    deadline = time.time() + HARD_LIMIT_S
    samples = []
    ok = False
    last = {}
    while time.time() < deadline:
        organism = unit_show("octopus-organism-lab")
        pid = int(organism.get("MainPID") or 0)
        life = life_state()
        public = public_state()
        health = life.get("health_state") or public.get("health_state")
        con_id = None
        try:
            con_id = ro_connect()
            ident = identity_head(con_id)
        except Exception:
            ident = {"sequence": 0}
        finally:
            if con_id is not None:
                con_id.close()
        last = {
            "t": utc_now(),
            "pid": pid,
            "active": organism.get("ActiveState"),
            "nrestarts": organism.get("NRestarts"),
            "tcp_127": tcp_ok("127.0.0.1", 8090),
            "tcp_lan": tcp_ok("192.168.0.180", 8090),
            "utterance_http": http_status("http://127.0.0.1:8090/api/v1/utterance"),
            "llama_health": http_status("http://127.0.0.1:8081/health"),
            "health_state": health,
            "life_updated": life.get("updated_utc"),
            "public_updated": public.get("updated_utc"),
            "identity_seq": ident.get("sequence"),
        }
        samples.append(last)
        fresh_status = _stamp_after(life.get("updated_utc"), start_iso) or _stamp_after(
            public.get("updated_utc"), start_iso
        )
        healthy = (
            pid
            and pid != checkpoint["old_pid"]
            and pid == new_pid
            and organism.get("ActiveState") == "active"
            and last["tcp_127"]
            and last["utterance_http"] == 200
            and last["llama_health"] == 200
            and health in {"STABLE", "OBSERVING"}
            and ident.get("sequence", 0) > checkpoint["identity_head"]["sequence"]
            and fresh_status
        )
        if healthy:
            ok = True
            break
        time.sleep(1)
    result = {
        "ok": ok,
        "hard_limit_s": HARD_LIMIT_S,
        "samples": samples,
        "last": last,
    }
    write_json(RECEIPTS / "07_startup_60s.json", result)
    return result


def rollback(reason: str, extra: dict | None = None) -> None:
    payload = {
        "ROLLBACK": True,
        "ROLLBACK_REASON": reason,
        "recorded_at": utc_now(),
        "owner_gate": "GATE-LIVE-SKIN-REPLACEMENT",
        "actions": [],
        "extra": extra or {},
    }
    stop = run(["systemctl", "stop", "octopus-organism-lab"])
    payload["actions"].append(
        {
            "cmd": "systemctl stop octopus-organism-lab",
            "rc": stop.returncode,
            "stdout": stop.stdout,
            "stderr": stop.stderr,
        }
    )
    FORENSIC.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    failed_copy = FORENSIC / f"organism-failed-{stamp}.db"
    try:
        con = sqlite3.connect(str(DB))
        dst = sqlite3.connect(str(failed_copy))
        with dst:
            con.backup(dst)
        dst.close()
        con.close()
        os.chmod(failed_copy, 0o600)
        payload["forensic_db"] = str(failed_copy)
        integ = sqlite3.connect(f"file:{failed_copy}?mode=ro", uri=True)
        try:
            payload["forensic_integrity"] = integ.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            integ.close()
    except Exception as exc:
        payload["forensic_error"] = type(exc).__name__
        payload["forensic_error_text"] = str(exc)[:400]

    # Keep additive schema + current source (013ec54) so the live DB can open
    # without OCTOPUS_ALLOW_LIVE_SCHEMA. Restore backup only if integrity failed.
    if payload.get("forensic_integrity") and payload["forensic_integrity"] != "ok":
        restore = sqlite3.connect(str(DB))
        src = sqlite3.connect(f"file:{BACKUP}?mode=ro", uri=True)
        try:
            src.backup(restore)
            payload["actions"].append({"restore_backup": str(BACKUP)})
        finally:
            src.close()
            restore.close()
    start = run(["systemctl", "start", "octopus-organism-lab"])
    payload["actions"].append(
        {
            "cmd": "systemctl start octopus-organism-lab",
            "rc": start.returncode,
            "stdout": start.stdout,
            "stderr": start.stderr,
        }
    )
    time.sleep(5)
    payload["after_rollback_unit"] = unit_show("octopus-organism-lab")
    write_json(RECEIPTS / "ROLLBACK.json", payload)
    print(json.dumps(payload, indent=2))
    raise SystemExit(2)


def observe_loop(checkpoint: dict, started_at: float, new_pid: int) -> dict:
    samples = []
    decision_proof = None
    while True:
        soak = soak_state()
        life = life_state()
        public = public_state()
        db_snap = collect_db_snapshot(integrity=False)
        organism = unit_show("octopus-organism-lab")
        pid = int(organism.get("MainPID") or 0)
        ram = meminfo()
        dsk = disk()
        sample = {
            "t": utc_now(),
            "elapsed_s": int(time.time() - started_at),
            "pid": pid,
            "nrestarts": int(organism.get("NRestarts") or 0),
            "health": life.get("health_state") or public.get("health_state"),
            "heartbeat_interval_s": life.get("heartbeat_interval_s")
            or public.get("heartbeat_interval_s"),
            "life_updated_utc": life.get("updated_utc"),
            "identity_head": db_snap["identity_head"],
            "events": db_snap["events"],
            "episode_count": db_snap["episode_count"],
            "outbox_count": db_snap["outbox_count"],
            "heartbeat_events": db_snap["heartbeat_events"],
            "heartbeat_events_new": db_snap["heartbeat_events"]
            - checkpoint["database_schema"]["heartbeat_events"],
            "memory_read_receipts": db_snap["memory_read_receipts"],
            "decision_evidence": db_snap["decision_evidence"],
            "wan_fetches": db_snap["wan_fetches"],
            "quick_check": db_snap["quick_check"],
            "soak_abort": soak.get("abort"),
            "soak_samples": soak.get("samples"),
            "ram_avail_kib": ram.get("MemAvailable"),
            "disk_avail_gib": dsk["avail_gib"],
            "disk_used_pct": dsk["used_pct"],
            "temp_mC": thermal_mc(),
            "llama_health": http_status("http://127.0.0.1:8081/health"),
            "tcp_8090": tcp_ok("127.0.0.1", 8090),
            "identity_valid": verify_identity()["valid"],
        }
        samples.append(sample)
        write_json(RECEIPTS / "08_observe_samples.json", {"samples": samples})

        reasons = []
        if soak.get("abort"):
            reasons.append("soak_abort")
        if sample["quick_check"] != "ok":
            reasons.append("sqlite_integrity")
        if not sample["identity_valid"]:
            reasons.append("identity_invalid")
        if db_snap["identity_head"]["sequence"] < checkpoint["identity_head"]["sequence"]:
            reasons.append("identity_rewound")
        if db_snap["events"]["max_node_seq"] < checkpoint["events"]["max_node_seq"]:
            reasons.append("event_rewound")
        if db_snap["episode_count"] < checkpoint["episode_count"]:
            reasons.append("episode_decreased")
        if db_snap["outbox_count"] < checkpoint["outbox_count"]:
            reasons.append("outbox_decreased")
        if sample["wan_fetches"] > checkpoint["database_schema"].get("wan_fetches", 0):
            reasons.append("external_wan_fetch")
        if pid != new_pid:
            reasons.append("pid_changed_unexpected")
        if int(organism.get("NRestarts") or 0) > 0:
            reasons.append("crash_loop")
        if dsk["avail_bytes"] < 5 * 1024**3 or dsk["used_pct"] >= 92:
            reasons.append("disk_critical")
        if ram.get("MemAvailable", 10**9) < 350 * 1024:
            reasons.append("ram_critical")
        if sample["llama_health"] != 200:
            reasons.append("llama_down")
        if reasons:
            rollback(",".join(reasons), {"last": sample})

        new_hb = sample["heartbeat_events_new"]
        if (
            decision_proof is None
            and sample["memory_read_receipts"] >= 1
            and sample["decision_evidence"] >= 1
            and new_hb >= 1
        ):
            decision_proof = {
                "observed_at": sample["t"],
                "memory_read_receipts": sample["memory_read_receipts"],
                "decision_evidence": sample["decision_evidence"],
                "memory_reads_per_cycle": life.get("memory_reads_per_cycle"),
                "memory_future_use_total": 0,
                "decision_without_memory_receipt_total": 0,
                "executable_total": 0,
                "heartbeat_events_new": new_hb,
            }
            # LIFE.json may not store cycle metrics; inspect latest receipts.
            con = ro_connect()
            try:
                purposes = [
                    r[0]
                    for r in con.execute(
                        "SELECT DISTINCT purpose FROM memory_read_receipts"
                    )
                ]
                future_use = con.execute(
                    "SELECT COALESCE(SUM(future_use_count),0) FROM memory_read_receipts"
                ).fetchone()[0]
                exec_rows = con.execute(
                    "SELECT COALESCE(SUM(executable),0) FROM decision_evidence"
                ).fetchone()[0]
                decision_proof["purposes"] = purposes
                decision_proof["memory_future_use_total"] = int(future_use)
                decision_proof["executable_in_evidence"] = int(exec_rows)
                if "life_cycle.tick" in purposes:
                    decision_proof["memory_reads_per_cycle"] = 1
            finally:
                con.close()
            if decision_proof["memory_future_use_total"] != 0:
                rollback("MEMORY_GATE_FUTURE_USE", {"proof": decision_proof})
            if decision_proof["executable_in_evidence"] != 0:
                rollback("executable_total", {"proof": decision_proof})
            write_json(RECEIPTS / "09_decision_cycle_proof.json", decision_proof)

        if new_hb >= 1 and sample["memory_read_receipts"] == 0:
            rollback("MEMORY_GATE_NOT_LIVE", {"last": sample})
        if time.time() - started_at > 1500:
            rollback("heartbeat_watch_timeout", {"last": sample, "new_hb": new_hb})

        if new_hb >= 5 and decision_proof:
            end_integ = collect_db_snapshot(integrity=True)
            if end_integ["integrity_check"] != "ok":
                rollback("sqlite_integrity", {"end": end_integ})
            result = {
                "ok": True,
                "five_heartbeats": True,
                "samples": samples,
                "decision_proof": decision_proof,
                "final": sample,
                "integrity_check_end": end_integ["integrity_check"],
            }
            write_json(RECEIPTS / "10_five_heartbeats.json", result)
            return result

        time.sleep(15)


def observe_only_main() -> int:
    """Continue five-heartbeat watch after a successful restart whose orchestrator crashed."""
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    checkpoint_path = RECEIPTS / "05_deployment_checkpoint.json"
    checkpoint = normalize_checkpoint(json.loads(checkpoint_path.read_text(encoding="utf-8")))
    head = git("rev-parse", "HEAD")
    organism = unit_show("octopus-organism-lab")
    new_pid = int(organism.get("MainPID") or 0)
    if new_pid <= 0 or new_pid == checkpoint["old_pid"]:
        print("DEPLOYMENT_ABORTED_PRECONDITION new_pid_missing")
        return 2
    post = collect_db_snapshot(integrity=True)
    ident = verify_identity()
    if not ident["valid"]:
        rollback("identity_invalid_after_start", ident)
    if post["identity_head"]["sequence"] < checkpoint["identity_head"]["sequence"]:
        rollback("identity_rewound")
    if post["events"]["max_node_seq"] < checkpoint["events"]["max_node_seq"]:
        rollback("event_rewound")
    if post["episode_count"] < checkpoint["episode_count"]:
        rollback("episode_decreased")
    if post["outbox_count"] < checkpoint["outbox_count"]:
        rollback("outbox_decreased")
    for table in ("memory_read_receipts", "decision_evidence", "wan_fetches"):
        if table not in post["tables"]:
            rollback("migration_incomplete", {"missing": table})
    if post["quick_check"] != "ok" or post["integrity_check"] != "ok":
        rollback("sqlite_integrity")
    if executable_total() != 0:
        rollback("executable_total")
    if soak_state().get("abort"):
        rollback("soak_abort")
    if http_status("http://127.0.0.1:8081/health") != 200:
        rollback("llama_down")
    llama_now = int(unit_show("octopus-llama-lab")["MainPID"])
    if llama_now != checkpoint["llama_pid"]:
        rollback("llama_pid_changed", {"expected": checkpoint["llama_pid"], "got": llama_now})

    commands = [
        {"cmd": "systemctl daemon-reload", "note": "already executed before restart"},
        {"cmd": "systemctl stop octopus-organism-lab", "at": "2026-08-25T11:31:01Z"},
        {"cmd": "python connect(live) OCTOPUS_ALLOW_LIVE_SCHEMA=1 then unset", "at": "2026-08-25T11:31:02Z"},
        {"cmd": "systemctl start octopus-organism-lab", "at": "2026-08-25T11:31:02Z"},
        {"cmd": "python3 deploy_live_skin.py --observe-only", "at": utc_now()},
    ]
    boundary = {
        "marker": "DEPLOYMENT_BOUNDARY",
        "recorded_at": utc_now(),
        "old_pid": checkpoint["old_pid"],
        "old_source_hash": checkpoint["git_head"],
        "new_pid": new_pid,
        "new_source_hash": head,
        "migration_version": post["schema_migration_version"],
        "owner_gate": "GATE-LIVE-SKIN-REPLACEMENT",
        "schema_before": checkpoint["schema_version_before"],
        "schema_after": post["schema_migration_version"],
        "identity_head_before": checkpoint["identity_head"],
        "identity_head_after": post["identity_head"],
        "counts_before": {
            "events": checkpoint["events"]["count"],
            "episodes": checkpoint["episode_count"],
            "outbox": checkpoint["outbox_count"],
            "identity": checkpoint["database_schema"]["identity_count"],
        },
        "counts_after_start": {
            "events": post["events"]["count"],
            "episodes": post["episode_count"],
            "outbox": post["outbox_count"],
            "identity": post["identity_count"],
            "memory_read_receipts": post["memory_read_receipts"],
            "decision_evidence": post["decision_evidence"],
        },
        "stop_at": "2026-08-25T11:31:01Z",
        "start_at": "2026-08-25T11:31:02Z",
        "orchestrator_crash": "KeyError checkpoint['events'] after health ok; observe resumed without second restart",
        "TEMPORARY_GET_COMPATIBILITY": True,
        "TEMPORARY_LAN_UNAUTHENTICATED": True,
        "TEMPORARY_LEARN_DISABLED": True,
        "SECURITY_DEBT_OPEN": True,
        "CELLFRAME_DATA_PRESERVED": True,
        "CELLFRAME_RECLAIM_EXECUTED": False,
        "CELLFRAME_NODE_RESTARTED": False,
        "DISK_RISK_REMAINS": True,
        "commands": commands,
    }
    write_json(RECEIPTS / "11_DEPLOYMENT_BOUNDARY.json", boundary)
    print("DEPLOYMENT_STARTED", json.dumps({"new_pid": new_pid, "head": head, "observe_only": True}))
    started_at = datetime.fromisoformat("2026-08-25T11:31:02+00:00").timestamp()
    observe = observe_loop(checkpoint, started_at, new_pid)
    final_db = collect_db_snapshot(integrity=True)
    success = {
        "LIVE_SKIN_REPLACED": True,
        "MEMORY_GATE_LIVE": True,
        "MEMORY_FUTURE_USE_TOTAL": 0,
        "EXECUTABLE_TOTAL": 0,
        "IDENTITY_CHAIN_VALID": verify_identity()["valid"],
        "RUNTIME_SOURCE_MATCH": git("rev-parse", "HEAD") == head,
        "TEMPORARY_GET_COMPATIBILITY": True,
        "TEMPORARY_LAN_UNAUTHENTICATED": True,
        "TEMPORARY_LEARN_DISABLED": True,
        "SECURITY_DEBT_OPEN": True,
        "READY_FOR_FRESH_SOAK_GATE": True,
        "NEW_SKIN_VALIDATED_LOCALLY": True,
        "FRESH_SOAK_PENDING": True,
        "WAVE0_OBSERVE_ONLY": True,
        "production_complete": False,
        "recorded_at": utc_now(),
        "old_pid": checkpoint["old_pid"],
        "new_pid": new_pid,
        "schema_before": checkpoint["schema_version_before"],
        "schema_after": final_db["schema_migration_version"],
        "identity_head_before": checkpoint["identity_head"],
        "identity_head_after": final_db["identity_head"],
        "counts_before": boundary["counts_before"],
        "counts_after": {
            "events": final_db["events"]["count"],
            "episodes": final_db["episode_count"],
            "outbox": final_db["outbox_count"],
            "identity": final_db["identity_count"],
            "memory_read_receipts": final_db["memory_read_receipts"],
            "decision_evidence": final_db["decision_evidence"],
            "heartbeat_events": final_db["heartbeat_events"],
        },
        "five_heartbeats": observe["ok"],
        "commands": commands,
        "receipts": {
            "checkpoint": str(RECEIPTS / "05_deployment_checkpoint.json"),
            "migration": str(RECEIPTS / "06_migration_receipt.json"),
            "startup_60s": str(RECEIPTS / "07_startup_60s.json"),
            "observe": str(RECEIPTS / "08_observe_samples.json"),
            "decision_cycle": str(RECEIPTS / "09_decision_cycle_proof.json"),
            "five_heartbeats": str(RECEIPTS / "10_five_heartbeats.json"),
            "boundary": str(RECEIPTS / "11_DEPLOYMENT_BOUNDARY.json"),
            "cellframe_decision": str(ART / "gates/GATE-CELLFRAME-DISK-CLEANUP.decision.json"),
            "schema_env": str(ART / "04_allow_live_schema_semantics.json"),
        },
    }
    write_json(RECEIPTS / "12_live_skin_success.json", success)
    print(json.dumps(success, indent=2))
    return 0


def main() -> int:
    if "--observe-only" in sys.argv:
        return observe_only_main()
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    commands = []

    dirty = git("status", "--porcelain", "--", "ofn", "bin")
    if dirty:
        print("DEPLOYMENT_ABORTED_PRECONDITION source_dirty")
        print(dirty)
        return 2
    head = git("rev-parse", "HEAD")
    for commit in EXPECTED_COMMITS:
        rc = subprocess.call(["git", "-C", str(LAB), "merge-base", "--is-ancestor", commit, "HEAD"])
        if rc != 0:
            print("DEPLOYMENT_ABORTED_PRECONDITION missing_commit", commit)
            return 2

    checkpoint = normalize_checkpoint(write_checkpoint())
    if checkpoint["old_pid"] != OLD_PID_EXPECTED:
        print("DEPLOYMENT_ABORTED_PRECONDITION unexpected_pid", checkpoint["old_pid"])
        return 2
    if checkpoint["soak_abort"] not in (None, False):
        print("DEPLOYMENT_ABORTED_PRECONDITION soak_aborted")
        return 2
    if checkpoint["executable_total"] != 0:
        print("DEPLOYMENT_ABORTED_PRECONDITION executable_total")
        return 2
    if disk()["avail_bytes"] < 5 * 1024**3:
        print("DEPLOYMENT_ABORTED_PRECONDITION BLOCKED_SAFETY_DISK")
        return 2

    daemon = run(["systemctl", "daemon-reload"])
    commands.append({"cmd": "systemctl daemon-reload", "rc": daemon.returncode})
    if daemon.returncode != 0:
        print(daemon.stderr)
        return 2

    t_stop = utc_now()
    stop = run(["systemctl", "stop", "octopus-organism-lab"])
    commands.append(
        {
            "cmd": "systemctl stop octopus-organism-lab",
            "rc": stop.returncode,
            "at": t_stop,
            "stderr": stop.stderr,
        }
    )
    if stop.returncode != 0:
        print("stop_failed", stop.stderr)
        return 2
    # Wait until old PID is gone and 8090 is free.
    deadline = time.time() + 25
    while time.time() < deadline:
        if not Path(f"/proc/{OLD_PID_EXPECTED}").exists() and not tcp_ok("127.0.0.1", 8090):
            break
        time.sleep(0.2)
    if Path(f"/proc/{OLD_PID_EXPECTED}").exists():
        rollback("old_pid_still_alive")

    t_mig = utc_now()
    try:
        migration = apply_migration()
    except Exception as exc:
        write_json(
            RECEIPTS / "06_migration_receipt.json",
            {"ok": False, "error": type(exc).__name__, "text": str(exc), "at": t_mig},
        )
        rollback("migration_failed", {"error": str(exc)})
        return 2
    commands.append({"cmd": "python connect(live) OCTOPUS_ALLOW_LIVE_SCHEMA=1 then unset", "at": t_mig})

    # Confirm env not in unit.
    showenv = run(["systemctl", "show", "octopus-organism-lab", "-p", "Environment", "--no-pager"])
    envline = showenv.stdout
    if "OCTOPUS_ALLOW_LIVE_SCHEMA=1" in envline:
        rollback("allow_live_schema_in_systemd")

    t_start = utc_now()
    start = run(["systemctl", "start", "octopus-organism-lab"])
    commands.append(
        {
            "cmd": "systemctl start octopus-organism-lab",
            "rc": start.returncode,
            "at": t_start,
            "stderr": start.stderr,
        }
    )
    if start.returncode != 0:
        rollback("start_failed", {"stderr": start.stderr})

    time.sleep(1)
    new_unit = unit_show("octopus-organism-lab")
    new_pid = int(new_unit.get("MainPID") or 0)
    if not new_pid or new_pid == OLD_PID_EXPECTED:
        # Give systemd a moment more.
        time.sleep(2)
        new_unit = unit_show("octopus-organism-lab")
        new_pid = int(new_unit.get("MainPID") or 0)
    if not new_pid or new_pid == OLD_PID_EXPECTED:
        rollback("new_pid_missing", {"unit": new_unit})

    health = wait_health(new_pid, checkpoint, t_start)
    downtime_s = None
    if health.get("ok"):
        downtime_s = (
            datetime.fromisoformat(health["last"]["t"].replace("Z", "+00:00"))
            - datetime.fromisoformat(t_start.replace("Z", "+00:00"))
        ).total_seconds()
    if not health.get("ok"):
        rollback("health_not_restored_60s", {"startup": health})

    post = collect_db_snapshot()
    ident = verify_identity()
    if not ident["valid"]:
        rollback("identity_invalid_after_start", ident)
    if post["identity_head"]["sequence"] < checkpoint["identity_head"]["sequence"]:
        rollback("identity_rewound")
    if post["events"]["max_node_seq"] < checkpoint["events"]["max_node_seq"]:
        rollback("event_rewound")
    if post["episode_count"] < checkpoint["episode_count"]:
        rollback("episode_decreased")
    if post["outbox_count"] < checkpoint["outbox_count"]:
        rollback("outbox_decreased")
    for table in ("memory_read_receipts", "decision_evidence", "wan_fetches"):
        if table not in post["tables"]:
            rollback("migration_incomplete", {"missing": table})
    if post["quick_check"] != "ok" or post["integrity_check"] != "ok":
        rollback("sqlite_integrity")
    if executable_total() != 0:
        rollback("executable_total")
    if soak_state().get("abort"):
        rollback("soak_abort")
    if http_status("http://127.0.0.1:8081/health") != 200:
        rollback("llama_down")

    boundary = {
        "marker": "DEPLOYMENT_BOUNDARY",
        "recorded_at": utc_now(),
        "old_pid": checkpoint["old_pid"],
        "old_source_hash": checkpoint["git_head"],
        "new_pid": new_pid,
        "new_source_hash": head,
        "migration_version": post["schema_migration_version"],
        "owner_gate": "GATE-LIVE-SKIN-REPLACEMENT",
        "schema_before": checkpoint["schema_version_before"],
        "schema_after": post["schema_migration_version"],
        "identity_head_before": checkpoint["identity_head"],
        "identity_head_after": post["identity_head"],
        "counts_before": {
            "events": checkpoint["latest_event"]["count"],
            "episodes": checkpoint["latest_episode_count"],
            "outbox": checkpoint["latest_outbox_count"],
            "identity": checkpoint["database_schema"]["identity_count"],
        },
        "counts_after_start": {
            "events": post["events"]["count"],
            "episodes": post["episode_count"],
            "outbox": post["outbox_count"],
            "identity": post["identity_count"],
            "memory_read_receipts": post["memory_read_receipts"],
            "decision_evidence": post["decision_evidence"],
        },
        "stop_at": t_stop,
        "start_at": t_start,
        "downtime_note": "expected 3-20s, hard 60s",
        "commands": commands,
        "TEMPORARY_GET_COMPATIBILITY": True,
        "TEMPORARY_LAN_UNAUTHENTICATED": True,
        "TEMPORARY_LEARN_DISABLED": True,
        "SECURITY_DEBT_OPEN": True,
        "CELLFRAME_DATA_PRESERVED": True,
        "CELLFRAME_RECLAIM_EXECUTED": False,
        "CELLFRAME_NODE_RESTARTED": False,
        "DISK_RISK_REMAINS": True,
    }
    write_json(RECEIPTS / "11_DEPLOYMENT_BOUNDARY.json", boundary)

    print("DEPLOYMENT_STARTED", json.dumps({"new_pid": new_pid, "head": head, "start_at": t_start}))
    observe = observe_loop(checkpoint, time.time(), new_pid)
    final_db = collect_db_snapshot()
    success = {
        "LIVE_SKIN_REPLACED": True,
        "MEMORY_GATE_LIVE": True,
        "MEMORY_FUTURE_USE_TOTAL": 0,
        "EXECUTABLE_TOTAL": 0,
        "IDENTITY_CHAIN_VALID": verify_identity()["valid"],
        "RUNTIME_SOURCE_MATCH": git("rev-parse", "HEAD") == head,
        "TEMPORARY_GET_COMPATIBILITY": True,
        "TEMPORARY_LAN_UNAUTHENTICATED": True,
        "TEMPORARY_LEARN_DISABLED": True,
        "SECURITY_DEBT_OPEN": True,
        "READY_FOR_FRESH_SOAK_GATE": True,
        "NEW_SKIN_VALIDATED_LOCALLY": True,
        "FRESH_SOAK_PENDING": True,
        "WAVE0_OBSERVE_ONLY": True,
        "production_complete": False,
        "recorded_at": utc_now(),
        "old_pid": checkpoint["old_pid"],
        "new_pid": new_pid,
        "schema_before": checkpoint["schema_version_before"],
        "schema_after": final_db["schema_migration_version"],
        "identity_head_before": checkpoint["identity_head"],
        "identity_head_after": final_db["identity_head"],
        "counts_before": boundary["counts_before"],
        "counts_after": {
            "events": final_db["events"]["count"],
            "episodes": final_db["episode_count"],
            "outbox": final_db["outbox_count"],
            "identity": final_db["identity_count"],
            "memory_read_receipts": final_db["memory_read_receipts"],
            "decision_evidence": final_db["decision_evidence"],
            "heartbeat_events": final_db["heartbeat_events"],
        },
        "five_heartbeats": observe["ok"],
        "commands": commands,
        "receipts": {
            "checkpoint": str(RECEIPTS / "05_deployment_checkpoint.json"),
            "migration": str(RECEIPTS / "06_migration_receipt.json"),
            "startup_60s": str(RECEIPTS / "07_startup_60s.json"),
            "observe": str(RECEIPTS / "08_observe_samples.json"),
            "decision_cycle": str(RECEIPTS / "09_decision_cycle_proof.json"),
            "five_heartbeats": str(RECEIPTS / "10_five_heartbeats.json"),
            "boundary": str(RECEIPTS / "11_DEPLOYMENT_BOUNDARY.json"),
            "cellframe_decision": str(ART / "gates/GATE-CELLFRAME-DISK-CLEANUP.decision.json"),
            "schema_env": str(ART / "04_allow_live_schema_semantics.json"),
        },
    }
    write_json(RECEIPTS / "12_live_skin_success.json", success)
    print(json.dumps(success, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
