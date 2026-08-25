from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ofn.organism.cognition.inner import inner_count, inner_turn, latest_inner
from ofn.organism.cognition.learn import list_topics, maybe_self_learn, topic_count
from ofn.organism.cognition.teacher import external_api_label, teacher_status
from ofn.organism.cognition.voice import compose_utterance, grounding_text, utc_now
from ofn.organism.contracts.events import make_event
from ofn.organism.growth.attention import maybe_presence, notice_attention
from ofn.organism.growth.futures import (
    OWNER_FUTURE_DECISIONS,
    apply_owner_future_decisions,
    list_futures,
    seed_futures,
)
from ofn.organism.growth.habits import growth_view, maybe_adapt_heartbeat
from ofn.organism.growth.parent import (
    apply_given_names,
    development_view,
    ensure_parent_curriculum,
    maybe_mature_rhythm,
)
from ofn.organism.identity.self_model import (
    build_self_model,
    latest_self_model,
    material_self_delta,
    persist_self_model,
)
from ofn.organism.identity.attestation import write_attestation
from ofn.organism.memory.episodic import recall
from ofn.organism.memory.gate import require_memory_gate
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.runtime.telegram_letter import append_local_letter
from ofn.organism.school.curriculum import evaluate_school
from ofn.organism.school.vault import export_vault
from ofn.organism.tools.discover import run_tools
from ofn.organism.world.model import hosts_from_lan, known_hosts, load_lan_state, persist_hosts
from ofn.organism.world.season import attach_season, season_view


LAST_UTTERANCE_PATH = Path("/opt/octopus/lab/state/LAST-UTTERANCE.json")
LIFE_STATE_PATH = Path("/opt/octopus/lab/state/LIFE.json")


def _commit(kernel, event_type: str, payload: dict[str, Any], priority: int = 25) -> dict[str, Any]:
    event = make_event(event_type, payload, priority=priority)
    receipt = kernel.accept(event)
    if receipt.get("status") == "committed":
        kernel.replay_pending(limit=20)
    return {"event": event, "receipt": receipt}


def recent_memory_lines(con, limit: int = 6) -> list[str]:
    lines = []
    for item in recall(con, limit=40):
        if item.get("event_type") == "heartbeat":
            continue
        body = item.get("body") or {}
        summary = body.get("summary") or body.get("text")
        if not summary:
            summary = item.get("event_type")
        lines.append(f"{item.get('event_type')}:{summary}")
        if len(lines) >= limit:
            break
    return lines


def enrich_snapshot(
    con,
    snapshot: dict[str, Any],
    measured: dict[str, Any],
    lan_path: Path | None = None,
    ask_lan: bool = False,
    tools_root: Path | None = None,
) -> dict[str, Any]:
    enriched = dict(snapshot)
    seed_futures(con)
    apply_owner_future_decisions(con, OWNER_FUTURE_DECISIONS)
    sensors = {item["name"]: item for item in measured.get("signals") or []}
    enriched["sensors"] = sensors
    discovery = run_tools(tools_root or Path("/"))
    enriched["discovery"] = discovery
    place = attach_season(discovery.get("place") or {})
    enriched["place"] = place
    enriched["season"] = season_view()
    lan = load_lan_state(lan_path) if lan_path else load_lan_state()
    live_hosts = hosts_from_lan(lan)
    stored = {item["id"]: item for item in known_hosts(con)}
    merged = []
    seen = set()
    for host in live_hosts:
        stored_host = stored.get(host["id"]) or {}
        merged.append({**stored_host, **host})
        seen.add(host["id"])
    for host_id, host in stored.items():
        if host_id not in seen:
            merged.append(host)
    enriched["world_hosts"] = apply_given_names(merged)
    enriched["growth"] = growth_view(con)
    enriched["recent_memories"] = recent_memory_lines(con)
    enriched["futures"] = list_futures(con)
    enriched["inner"] = {
        "count": inner_count(con),
        "recent": latest_inner(con, limit=6),
    }
    enriched["school"] = evaluate_school(con, enriched)
    enriched["development"] = development_view(con, enriched)
    enriched["teacher"] = teacher_status()
    enriched["external_api"] = external_api_label(enriched["teacher"])
    enriched["topics"] = list_topics(con)
    enriched["topics_count"] = topic_count(con)
    enriched["grounding_text"] = grounding_text(enriched)
    enriched["ask_lan"] = ask_lan
    extras = {
        "ask_lan": ask_lan,
        "discovery": discovery,
        "development": enriched["development"],
        "season": enriched["season"],
        "school": enriched["school"],
    }
    enriched["self_model"] = build_self_model(enriched, measured, extras)
    return enriched


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def persist_utterance(con, kind: str, text: str, source_event_id: str | None, grounded: dict[str, Any]) -> dict[str, Any]:
    utterance_id = hashlib.sha256(f"{time.time_ns()}:{kind}".encode()).hexdigest()[:32]
    record = {
        "utterance_id": utterance_id,
        "utc": utc_now(),
        "kind": kind,
        "text": text,
        "source_event_id": source_event_id,
    }
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO utterances(
                utterance_id, created_at, kind, text, source_event_id, grounded_json
            ) VALUES (?,?,?,?,?,?)
            """,
            (
                utterance_id,
                time.time(),
                kind,
                text,
                source_event_id,
                json.dumps(
                    {
                        "health_state": grounded.get("health_state"),
                        "identity_chain_valid": grounded.get("identity_chain_valid"),
                        "world_hosts": [
                            {
                                "id": item.get("id"),
                                "status": item.get("status"),
                            }
                            for item in grounded.get("world_hosts") or []
                        ],
                    },
                    sort_keys=True,
                ),
            ),
        )
    append_local_letter(
        {
            "utc": record["utc"],
            "kind": f"UTTERANCE_{kind.upper()}",
            "detail": kind,
            "telegram": "TELEGRAM_NOT_CONFIGURED",
            "text": text,
        }
    )
    _write_json(LAST_UTTERANCE_PATH, record)
    return record


def latest_utterance(con) -> dict[str, Any] | None:
    with DB_LOCK:
        row = con.execute(
            """
            SELECT utterance_id, created_at, kind, text, source_event_id
            FROM utterances
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    if not row:
        return None
    return {
        "utterance_id": row[0],
        "created_at": row[1],
        "kind": row[2],
        "text": row[3],
        "source_event_id": row[4],
    }


def tick(
    con,
    kernel,
    snapshot: dict[str, Any],
    measured: dict[str, Any],
    *,
    lan_path: Path | None = None,
    ask_lan: bool = False,
    tools_root: Path | None = None,
) -> dict[str, Any]:
    memory_bundle = require_memory_gate(con, "life_cycle.tick")
    snapshot = dict(snapshot)
    snapshot["memory_gate"] = memory_bundle.as_dict()
    parent = ensure_parent_curriculum(con)
    seed_futures(con)
    enriched = enrich_snapshot(
        con,
        snapshot,
        measured,
        lan_path=lan_path,
        ask_lan=ask_lan,
        tools_root=tools_root,
    )
    learned = maybe_self_learn(con, enriched)
    if learned:
        enriched["topics"] = list_topics(con)
        enriched["topics_count"] = topic_count(con)
        enriched["last_learn"] = {
            "status": learned.get("status"),
            "topic": learned.get("topic"),
            "claim_level": learned.get("claim_level") or "LEARNED_FROM_MODEL",
        }
    inner = inner_turn(con, enriched)
    enriched["inner"] = {
        "count": inner_count(con),
        "recent": latest_inner(con, limit=6),
        "last": inner,
    }
    enriched["school"] = evaluate_school(con, enriched)
    mature = maybe_mature_rhythm(con, enriched["school"])
    lan = load_lan_state(lan_path) if lan_path else load_lan_state()
    world_changes = persist_hosts(con, apply_given_names(hosts_from_lan(lan)))
    enriched["development"] = development_view(con, enriched)
    extras = {
        "ask_lan": ask_lan,
        "discovery": enriched.get("discovery") or {},
        "development": enriched["development"],
        "season": enriched.get("season"),
        "school": enriched["school"],
    }
    enriched["self_model"] = build_self_model(enriched, measured, extras)
    previous_self = latest_self_model(con)
    self_changes = material_self_delta(previous_self, enriched["self_model"])
    growth = maybe_adapt_heartbeat(con, enriched.get("health_state") or "", measured)
    if parent.get("rhythm") and growth is None:
        growth = parent["rhythm"]
    if mature and growth is None:
        growth = mature
    elif mature and growth is not None:
        growth = mature
    attention = notice_attention(con, enriched)
    enriched["growth"] = growth_view(con)
    enriched["development"] = development_view(con, enriched)
    enriched["attention"] = attention
    enriched["changes"] = self_changes + world_changes
    if growth:
        enriched["changes"].append(
            f"growth:{growth['from']}->{growth['to']}:{growth['reason']}"
        )
    if attention:
        enriched["changes"].append("attention:" + ";".join(attention["reasons"]))

    if world_changes:
        world_event = _commit(
            kernel,
            "world",
            {"summary": ";".join(world_changes), "changes": world_changes},
        )
    else:
        world_event = None

    self_event = _commit(
        kernel,
        "self_model",
        {
            "summary": ";".join(self_changes) if self_changes else "unchanged",
            "changes": self_changes,
        },
    )
    source_id = None
    if self_event["receipt"].get("status") == "committed":
        source_id = self_event["event"]["event_id"]
        persist_self_model(con, enriched["self_model"], source_id)

    spoke = None
    should_speak = bool(self_changes or world_changes or growth or attention)
    kind = "self"
    if not previous_self:
        kind = "self"
    elif growth:
        kind = "growth"
    elif attention:
        kind = "attention"
    elif world_changes:
        kind = "world"
    elif self_changes:
        kind = "change"
    if should_speak:
        maybe_presence(con, True)
    elif maybe_presence(con, False):
        should_speak = True
        kind = "presence"
    if should_speak:
        text = compose_utterance(kind, enriched)
        utterance_event = _commit(
            kernel,
            "utterance",
            {"summary": text, "kind": kind, "text": text},
            priority=20,
        )
        utterance_id = None
        if utterance_event["receipt"].get("status") == "committed":
            utterance_id = utterance_event["event"]["event_id"]
        spoke = persist_utterance(con, kind, text, utterance_id, enriched)

    _commit(
        kernel,
        "inner",
        {
            "summary": inner["prompt"],
            "prompt": inner["prompt"],
            "kind": inner["kind"],
        },
        priority=22,
    )

    if attention:
        _commit(
            kernel,
            "attention",
            {
                "summary": ";".join(attention["reasons"]),
                "reasons": attention["reasons"],
            },
            priority=18,
        )

    if growth:
        _commit(
            kernel,
            "growth",
            {
                "summary": f"{growth['from']}->{growth['to']}",
                **growth,
            },
            priority=15,
        )

    result = {
        "updated_utc": utc_now(),
        "self_changes": self_changes,
        "world_changes": world_changes,
        "growth": growth,
        "attention": attention,
        "inner": inner,
        "school": enriched.get("school"),
        "last_learn": learned,
        "utterance": spoke,
        "memory_reads_per_cycle": memory_bundle.memory_reads_per_cycle,
        "memory_future_use_total": memory_bundle.memory_future_use_total,
        "memory_gate": memory_bundle.as_dict(),
        "memory_gate_closed": False,
        "snapshot": enrich_snapshot(
            con,
            snapshot,
            measured,
            lan_path=lan_path,
            ask_lan=ask_lan,
            tools_root=tools_root,
        ),
    }
    export_vault(result["snapshot"])
    write_attestation(result["snapshot"])
    _write_json(
        LIFE_STATE_PATH,
        {
            "updated_utc": result["updated_utc"],
            "self_changes": self_changes,
            "world_changes": world_changes,
            "growth": growth,
            "attention": attention,
            "school_passed": (enriched.get("school") or {}).get("all_passed"),
            "season_city": (result["snapshot"].get("season") or {}).get("city"),
            "topics_count": (result["snapshot"].get("topics_count") or 0),
            "external_api": result["snapshot"].get("external_api"),
            "utterance": spoke,
            "health_state": enriched.get("health_state"),
            "developmental_stage": (result["snapshot"].get("development") or {}).get(
                "stage"
            ),
            "given_name": (result["snapshot"].get("development") or {}).get(
                "given_name"
            ),
            "heartbeat_interval_s": result["snapshot"]["growth"]["heartbeat_interval_s"],
        },
    )
    return result
