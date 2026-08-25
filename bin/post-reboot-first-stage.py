#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ofn.organism.identity.ledger import append_identity_event
from ofn.organism.persistence.db import DB_LOCK, connect


LAB = Path("/opt/octopus/lab")
EVIDENCE = LAB / "evidence"
STATE = LAB / "state"
DB_PATH = LAB / "lab-data/organism.db"
PRE_SCAN_PATH = EVIDENCE / "PRE-REBOOT-SCAN.json"
PRE_ASKS_PATH = EVIDENCE / "PRE-REBOOT-ASKS.json"
POST_RECEIPT_PATH = EVIDENCE / "POST-REBOOT-RECALL.json"
HEALTH_RECEIPT_PATH = EVIDENCE / "HEALTH-WRITE.json"
LABEL_RECEIPT_PATH = EVIDENCE / "FIRST-STAGE-LABEL.json"
PUBLIC_PATH = STATE / "ORGANISM-PUBLIC.json"
LABEL_PATH = STATE / "FIRST_STAGE_LABEL"
PENDING_MARKER = EVIDENCE / "FIRST-STAGE-PENDING"
DONE_MARKER = EVIDENCE / "FIRST-STAGE-C-DONE"
ORGANISM_URL = "http://127.0.0.1:8090/api/v1/organism"
EPISODES_URL = "http://127.0.0.1:8090/api/v1/episodes?limit=100"
LLAMA_URL = "http://127.0.0.1:8081/health"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args):
        return None


OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    NoRedirect(),
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def seal_json(path: Path) -> str:
    digest = sha256(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path}\n",
        encoding="utf-8",
    )
    return digest


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def http_json(url: str, timeout: float = 5) -> tuple[int, Any]:
    with OPENER.open(url, timeout=timeout) as response:
        return response.status, json.loads(response.read())


def wait_for(url: str, seconds: int) -> tuple[int | None, Any]:
    deadline = time.monotonic() + seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            return http_json(url)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            time.sleep(1)
    return None, {"error": last_error}


def independent_chain() -> dict[str, Any]:
    process = subprocess.run(
        [
            str(LAB / "bin/verify-identity-chain.py"),
            "--db",
            str(DB_PATH),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if not process.stdout:
        return {
            "valid": False,
            "error": process.stderr or "verifier_no_output",
        }
    return json.loads(process.stdout)


def database_proof(
    source_event_ids: list[str],
    pre_chain_hash: str,
) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        pre_row = con.execute(
            """
            SELECT sequence
            FROM identity_ledger
            WHERE entry_hash=?
            """,
            (pre_chain_hash,),
        ).fetchone()
        last_row = con.execute(
            """
            SELECT sequence, entry_hash
            FROM identity_ledger
            ORDER BY sequence DESC
            LIMIT 1
            """
        ).fetchone()
        recalled = {
            event_id: con.execute(
                """
                SELECT COUNT(*)
                FROM episodes AS ep
                JOIN events AS ev
                  ON ev.event_id=ep.source_event_id
                 AND ev.event_type=ep.event_type
                WHERE ep.source_event_id=?
                """,
                (event_id,),
            ).fetchone()[0]
            for event_id in source_event_ids
        }
    finally:
        con.close()
    return {
        "pre_chain_sequence": pre_row[0] if pre_row else None,
        "current_chain_sequence": last_row[0] if last_row else None,
        "current_chain_hash": last_row[1] if last_row else None,
        "pre_hash_is_ancestor": bool(
            pre_row
            and last_row
            and pre_row[0] <= last_row[0]
        ),
        "episode_counts_by_source_event_id": recalled,
    }


def set_meta(con, key: str, value: str) -> None:
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO meta(k,v) VALUES(?,?)
            ON CONFLICT(k) DO UPDATE SET v=excluded.v
            """,
            (key, value),
        )


def set_owner_label(
    organism: dict[str, Any],
    post_receipt_hash: str,
) -> dict[str, Any]:
    con = connect(DB_PATH)
    try:
        with DB_LOCK:
            previous = con.execute(
                "SELECT v FROM meta WHERE k='first_stage_label'"
            ).fetchone()
        set_meta(con, "first_stage_label", "OWNER_ALIVE_C")
        try:
            ledger = append_identity_event(
                con,
                organism["boot_id"],
                "owner_label_set",
                {
                    "label": "OWNER_ALIVE_C",
                    "post_reboot_receipt_sha256": post_receipt_hash,
                    "claim_scope": "OWNER_LABEL_NOT_SCIENTIFIC_LIFE_CLAIM",
                },
            )
        except Exception:
            set_meta(
                con,
                "first_stage_label",
                previous[0] if previous else "NOT_EARNED",
            )
            raise
    finally:
        con.close()

    STATE.mkdir(parents=True, exist_ok=True)
    temporary = LABEL_PATH.with_suffix(".tmp")
    temporary.write_text(
        "FIRST_STAGE_LABEL=OWNER_ALIVE_C\n",
        encoding="utf-8",
    )
    os.replace(temporary, LABEL_PATH)
    _, refreshed = http_json(ORGANISM_URL)
    receipt = {
        "captured_utc": utc_now(),
        "claim_level": "PROVEN",
        "FIRST_STAGE_LABEL": "OWNER_ALIVE_C",
        "organism_status_label": refreshed.get("first_stage_label"),
        "ledger_entry": ledger,
        "post_reboot_receipt_sha256": post_receipt_hash,
    }
    atomic_json(LABEL_RECEIPT_PATH, receipt)
    seal_json(LABEL_RECEIPT_PATH)
    return receipt


def synthetic_health_write(boot_id: str) -> dict[str, Any]:
    before = independent_chain()
    con = connect(DB_PATH)
    try:
        set_meta(con, "lab_synthetic_health_state", "DEGRADED")
        set_meta(
            con,
            "lab_synthetic_health_reason",
            "FIRST_STAGE_SAFE_SYNTHETIC_PROBE",
        )
    finally:
        con.close()

    degraded_code, degraded = http_json(ORGANISM_URL)
    public_degraded = load_json(PUBLIC_PATH)
    after_degraded = independent_chain()

    con = connect(DB_PATH)
    try:
        set_meta(con, "lab_synthetic_health_state", "CLEARED")
        set_meta(con, "lab_synthetic_health_reason", "CLEARED")
    finally:
        con.close()

    restored = None
    restored_code = None
    for _ in range(4):
        restored_code, restored = http_json(ORGANISM_URL)
        if restored.get("health_state") == "OBSERVING":
            break
        time.sleep(0.2)
    public_restored = load_json(PUBLIC_PATH)
    after_restored = independent_chain()

    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        transitions = []
        for row in con.execute(
            """
            SELECT sequence, payload_json, entry_hash
            FROM identity_ledger
            WHERE sequence > ?
              AND event_type='health_transition'
            ORDER BY sequence
            """,
            (before.get("entries", 0),),
        ):
            transitions.append({
                "sequence": row[0],
                "payload": json.loads(row[1]),
                "entry_hash": row[2],
            })
    finally:
        con.close()

    checks = {
        "degraded_http_200": degraded_code == 200,
        "degraded_state_observed": degraded.get("health_state") == "DEGRADED",
        "public_alert_set": bool(public_degraded.get("alert")),
        "public_state_degraded": (
            public_degraded.get("health_state") == "DEGRADED"
        ),
        "identity_chain_grew": (
            after_degraded.get("entries", 0) > before.get("entries", 0)
        ),
        "degraded_transition_chained": any(
            item["payload"].get("current") == "DEGRADED"
            for item in transitions
        ),
        "restored_http_200": restored_code == 200,
        "restored_to_observing": restored.get("health_state") == "OBSERVING",
        "public_alert_cleared": public_restored.get("alert") is None,
        "chain_valid_after_restore": after_restored.get("valid") is True,
    }
    receipt = {
        "captured_utc": utc_now(),
        "claim_level": "REPRODUCED" if all(checks.values()) else "OBSERVED",
        "scope": "SAFE_SYNTHETIC_DEGRADED_SIGNAL",
        "boot_id": boot_id,
        "checks": checks,
        "transitions": transitions,
        "chain_before": before,
        "chain_after_degraded": after_degraded,
        "chain_after_restore": after_restored,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    atomic_json(HEALTH_RECEIPT_PATH, receipt)
    seal_json(HEALTH_RECEIPT_PATH)
    return receipt


def soak_pids() -> list[int]:
    expected = [
        "python3",
        "/opt/octopus/lab/ofn/organism/runtime/soak.py",
    ]
    pids = []
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            raw = (proc / "cmdline").read_bytes()
        except (OSError, PermissionError):
            continue
        args = [
            part.decode("utf-8", errors="replace")
            for part in raw.split(b"\0")
            if part
        ]
        if args == expected:
            pids.append(int(proc.name))
    return sorted(pids)


def ensure_soak() -> dict[str, Any]:
    existing = soak_pids()
    if existing:
        return {"started": False, "pids": existing}
    log_path = LAB / "receipts/soak.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as log:
        process = subprocess.Popen(
            [
                "/usr/bin/python3",
                str(LAB / "ofn/organism/runtime/soak.py"),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    time.sleep(1)
    if process.poll() is not None:
        return {
            "started": False,
            "pids": [],
            "error": f"soak_exit_{process.returncode}",
        }
    return {"started": True, "pids": [process.pid]}


def run() -> int:
    pre_scan = load_json(PRE_SCAN_PATH)
    pre_asks = load_json(PRE_ASKS_PATH)
    source_event_ids = [
        item["source_event_id"]
        for item in pre_asks["asks"]
    ]

    organism_code, organism = wait_for(ORGANISM_URL, 180)
    llama_code, llama = wait_for(LLAMA_URL, 180)
    episodes_code, episodes = http_json(EPISODES_URL)
    chain = independent_chain()
    database = database_proof(
        source_event_ids,
        pre_asks["pre_reboot_chain_last_hash"],
    )
    current_kernel_boot_id = Path(
        "/proc/sys/kernel/random/boot_id"
    ).read_text().strip()
    endpoint_ids = {
        item["source_event_id"]
        for item in episodes.get("episodes", [])
    }

    checks_a = {
        "kernel_boot_id_changed": (
            current_kernel_boot_id != pre_scan["kernel_boot_id"]
        ),
        "organism_http_200": organism_code == 200,
        "same_organism_id": (
            organism.get("organism_id") == "board-life-001"
        ),
        "identity_chain_computed_true": (
            organism.get("identity_chain_valid") is True
            and chain.get("valid") is True
        ),
        "pre_reboot_chain_hash_is_ancestor": (
            database["pre_hash_is_ancestor"] is True
        ),
        "all_three_recalled_endpoint": all(
            event_id in endpoint_ids
            for event_id in source_event_ids
        ),
        "all_three_recalled_database": all(
            database["episode_counts_by_source_event_id"].get(
                event_id,
                0,
            )
            >= 1
            for event_id in source_event_ids
        ),
    }
    checks_b = {
        "pre_reboot_ask_receipt_proven": (
            pre_asks.get("verdict") == "PROVEN"
        ),
        "three_distinct_source_event_ids": (
            len(set(source_event_ids)) == 3
        ),
        "three_asks_recalled_after_reboot": all(
            checks_a[key]
            for key in (
                "all_three_recalled_endpoint",
                "all_three_recalled_database",
            )
        ),
    }
    a_proven = all(checks_a.values())
    b_proven = all(checks_b.values())
    receipt = {
        "captured_utc": utc_now(),
        "claim_level": (
            "PROVEN" if a_proven and b_proven else "OBSERVED"
        ),
        "pre_kernel_boot_id": pre_scan["kernel_boot_id"],
        "post_kernel_boot_id": current_kernel_boot_id,
        "pre_reboot_chain_last_hash": pre_asks[
            "pre_reboot_chain_last_hash"
        ],
        "post_reboot_chain": chain,
        "llama_http": llama_code,
        "llama_body": llama,
        "organism_http": organism_code,
        "organism_body": organism,
        "episodes_http": episodes_code,
        "source_event_ids": source_event_ids,
        "database_proof": database,
        "A": {
            "level": "PROVEN" if a_proven else "OBSERVED",
            "checks": checks_a,
        },
        "B": {
            "level": "PROVEN" if b_proven else "OBSERVED",
            "checks": checks_b,
        },
        "verdict": "PASS" if a_proven and b_proven else "FAIL",
    }
    atomic_json(POST_RECEIPT_PATH, receipt)
    post_hash = seal_json(POST_RECEIPT_PATH)
    if not (a_proven and b_proven):
        return 1

    label_receipt = set_owner_label(organism, post_hash)
    if (
        label_receipt.get("organism_status_label")
        != "OWNER_ALIVE_C"
    ):
        return 1

    health = synthetic_health_write(organism["boot_id"])
    if health["verdict"] != "PASS":
        return 1
    return 0


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = 1
    error = None
    try:
        result = run()
    except Exception as exc:
        error = {
            "captured_utc": utc_now(),
            "error": f"{type(exc).__name__}: {exc}",
        }
        atomic_json(EVIDENCE / "POST-REBOOT-ERROR.json", error)
        seal_json(EVIDENCE / "POST-REBOOT-ERROR.json")
        result = 1
    finally:
        soak = ensure_soak()
        atomic_json(EVIDENCE / "SOAK-AFTER-REBOOT.json", soak)
        seal_json(EVIDENCE / "SOAK-AFTER-REBOOT.json")
        try:
            http_json(ORGANISM_URL)
        except Exception:
            pass

    if result == 0:
        DONE_MARKER.write_text(
            f"completed_utc={utc_now()}\n",
            encoding="utf-8",
        )
        PENDING_MARKER.unlink(missing_ok=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
