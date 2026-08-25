from __future__ import annotations

import datetime as dt
import json
import os
import threading
from pathlib import Path
from typing import Any

from ofn.organism.persistence.db import DB_LOCK


PUBLIC_STATUS_PATH = Path("/opt/octopus/lab/state/ORGANISM-PUBLIC.json")
DEFAULT_FIRST_STAGE_LABEL = "NOT_EARNED"
_PUBLIC_STATUS_LOCK = threading.Lock()


def meta_value(con, key: str, default: str | None = None) -> str | None:
    with DB_LOCK:
        row = con.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    return row[0] if row else default


def first_stage_label(con) -> str:
    return meta_value(
        con,
        "first_stage_label",
        DEFAULT_FIRST_STAGE_LABEL,
    ) or DEFAULT_FIRST_STAGE_LABEL


def soak_status() -> dict[str, Any]:
    pids = []
    marker = "/opt/octopus/lab/ofn/organism/runtime/soak.py"
    nul = bytes([0])
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            raw = (proc / "cmdline").read_bytes()
        except (OSError, PermissionError):
            continue
        joined = raw.replace(nul, b" ").decode("utf-8", errors="replace")
        if marker in joined and "sed" not in joined:
            pids.append(int(proc.name))
    return {"running": bool(pids), "pids": sorted(pids)}


def public_letter(health_state: str, alerts) -> str | None:
    if health_state in ("OBSERVING", "STABLE") and not alerts:
        return None
    bits = []
    if health_state not in ("OBSERVING", "STABLE"):
        bits.append("health=" + str(health_state))
    if alerts:
        bits.append("alerts=" + ",".join(str(a) for a in alerts))
    return "board-life-001 " + "; ".join(bits)


def write_public_status(
    con,
    organism_body: dict[str, Any],
    path: Path = PUBLIC_STATUS_PATH,
) -> dict[str, Any]:
    alerts = organism_body.get("alerts") or []
    public = {
        "organism_id": organism_body["organism_id"],
        "health_state": organism_body["health_state"],
        "autonomy_state": organism_body["autonomy_state"],
        "local_cortex": organism_body["local_cortex"],
        "last_event_sequence": organism_body["last_event_sequence"],
        "identity_chain_valid": organism_body["identity_chain_valid"],
        "identity_chain_last_hash": organism_body["identity_chain_last_hash"],
        "first_stage_label": organism_body.get(
            "first_stage_label",
            first_stage_label(con),
        ),
        "alert": alerts if alerts else None,
        "letter": public_letter(organism_body.get("health_state", ""), alerts),
        "updated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "soak": soak_status(),
        "llama_health": (
            "AVAILABLE"
            if organism_body["local_cortex"] == "AVAILABLE"
            else "UNAVAILABLE"
        ),
        "unknowns": organism_body.get("unknowns", []),
        "last_utterance": organism_body.get("last_utterance"),
        "last_utterance_kind": organism_body.get("last_utterance_kind"),
        "given_name": (organism_body.get("development") or {}).get("given_name"),
        "developmental_stage": (organism_body.get("development") or {}).get("stage"),
        "lessons_taught": (organism_body.get("development") or {}).get("lessons_taught"),
        "season_city": (organism_body.get("season") or {}).get("city"),
        "season_source": (organism_body.get("season") or {}).get("source"),
        "school_passed": (organism_body.get("school") or {}).get("all_passed"),
        "external_api": organism_body.get("external_api"),
        "topics_count": organism_body.get("topics_count") or 0,
        "microphone": (
            (organism_body.get("discovery") or {}).get("senses") or {}
        ).get("microphone"),
        "teacher_ready": (organism_body.get("teacher") or {}).get("ready"),
        "world_hosts": [
            {
                "id": item.get("id"),
                "ip": item.get("ip"),
                "status": item.get("status"),
            }
            for item in (organism_body.get("world_hosts") or [])
        ],
        "heartbeat_interval_s": (organism_body.get("growth") or {}).get(
            "heartbeat_interval_s"
        ),
        "last_habit": (organism_body.get("growth") or {}).get("last_habit"),
    }

    with _PUBLIC_STATUS_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                public,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    return public
