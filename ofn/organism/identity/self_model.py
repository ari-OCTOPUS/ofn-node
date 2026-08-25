from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from ofn.organism.cognition.policy import learn_external_enabled
from ofn.organism.cognition.voice import utc_now
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.runtime.telegram_letter import telegram_ready


def _signals(measured: dict[str, Any]) -> dict[str, Any]:
    return {item["name"]: item for item in measured.get("signals") or []}


def build_self_model(
    snapshot: dict[str, Any],
    measured: dict[str, Any],
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extras = extras or {}
    return {
        "organism_id": snapshot.get("organism_id"),
        "given_name": (extras.get("development") or {}).get("given_name") or "بچه-برد",
        "developmental_stage": (extras.get("development") or {}).get("stage"),
        "boot_id": snapshot.get("boot_id"),
        "health_state": snapshot.get("health_state"),
        "autonomy_state": snapshot.get("autonomy_state", "PROPOSE_ONLY"),
        "local_cortex": snapshot.get("local_cortex"),
        "identity_chain_valid": snapshot.get("identity_chain_valid"),
        "identity_chain_last_hash": snapshot.get("identity_chain_last_hash"),
        "external_api": snapshot.get("external_api", "DISABLED"),
        "sensors": _signals(measured),
        "place": {
            "hostname": (extras.get("discovery") or {}).get("place", {}).get("hostname"),
            "board_model": (extras.get("discovery") or {}).get("place", {}).get("board_model"),
            "ipv4": (extras.get("discovery") or {}).get("place", {}).get("ipv4"),
            "mac": (extras.get("discovery") or {}).get("place", {}).get("mac"),
            "gateway_ipv4": (extras.get("discovery") or {}).get("place", {}).get("gateway_ipv4"),
            "wlan0_operstate": (extras.get("discovery") or {}).get("place", {}).get(
                "wlan0_operstate"
            ),
            "owner_city": (extras.get("season") or {}).get("city"),
            "owner_region": (extras.get("season") or {}).get("region"),
            "owner_source": (extras.get("season") or {}).get("source"),
        },
        "capabilities": {
            "ask_loopback": True,
            "ask_lan": bool(extras.get("ask_lan")),
            "heartbeat": True,
            "lan_watch": True,
            "memory_episodic": True,
            "growth_heartbeat_interval": True,
            "parent_curriculum": True,
            "attention": True,
            "presence": True,
            "school": True,
            "inner_speech": True,
            "vault": True,
            "external_api": False,
            "learn_external": bool(
                learn_external_enabled()
                and (snapshot.get("teacher") or {}).get("ready")
            ),
            "hear_capture": (
                ((extras.get("discovery") or {}).get("senses") or {}).get(
                    "microphone"
                )
                not in {None, "NOT_FOUND"}
            ),
            "local_attestation": True,
            "telegram": telegram_ready() == "READY",
            "actuators": False,
        },
        "limits": [
            "PROPOSE_ONLY",
            (
                "learn_only_deepseek_allowlisted"
                if snapshot.get("external_api") == "LEARN_ONLY_DEEPSEEK"
                else "no_external_api"
            ),
            "no_actuators",
            "lan_cidr_192.168.0.0/24",
        ],
        "updated_utc": utc_now(),
    }


def model_hash(model: dict[str, Any]) -> str:
    body = json.dumps(model, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def latest_self_model(con) -> dict[str, Any] | None:
    with DB_LOCK:
        row = con.execute(
            "SELECT state_json FROM self_models ORDER BY version DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def persist_self_model(con, model: dict[str, Any], source_event_id: str | None) -> str:
    digest = model_hash(model)
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO self_models(created_at, source_event_id, state_json, state_hash)
            VALUES (?,?,?,?)
            """,
            (time.time(), source_event_id, json.dumps(model, sort_keys=True), digest),
        )
    return digest


def material_self_delta(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[str]:
    if not previous:
        return ["first_self_model"]
    changes = []
    for key in (
        "health_state",
        "local_cortex",
        "identity_chain_valid",
        "autonomy_state",
        "external_api",
        "developmental_stage",
        "given_name",
    ):
        if previous.get(key) != current.get(key):
            changes.append(f"{key}:{previous.get(key)}->{current.get(key)}")
    prev_cap = (previous.get("capabilities") or {}).get("telegram")
    cur_cap = (current.get("capabilities") or {}).get("telegram")
    if prev_cap != cur_cap:
        changes.append(f"telegram:{prev_cap}->{cur_cap}")
    prev_place = previous.get("place") or {}
    cur_place = current.get("place") or {}
    for key in ("ipv4", "gateway_ipv4", "wlan0_operstate", "owner_city"):
        if prev_place.get(key) != cur_place.get(key):
            changes.append(f"{key}:{prev_place.get(key)}->{cur_place.get(key)}")
    return changes
