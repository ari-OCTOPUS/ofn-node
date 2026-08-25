from __future__ import annotations

import hashlib
import time
from typing import Any

from ofn.organism.cognition.policy import topic_allowed
from ofn.organism.cognition.teacher import complete_deep, complete_flash
from ofn.organism.memory.gate import MemoryUnavailable, require_memory_gate, unavailable_payload
from ofn.organism.persistence.db import DB_LOCK


def list_topics(con, limit: int = 20) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT topic_id, created_at, topic, summary, source, claim_level
            FROM learned_topics
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "topic_id": row[0],
            "created_at": row[1],
            "topic": row[2],
            "summary": row[3],
            "source": row[4],
            "claim_level": row[5],
        }
        for row in rows
    ]


def topic_count(con) -> int:
    with DB_LOCK:
        row = con.execute("SELECT COUNT(*) FROM learned_topics").fetchone()
    return int(row[0] if row else 0)


def already_learned(con, topic: str) -> dict[str, Any] | None:
    with DB_LOCK:
        row = con.execute(
            """
            SELECT topic_id, summary, source, claim_level
            FROM learned_topics
            WHERE topic=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (topic,),
        ).fetchone()
    if not row:
        return None
    return {
        "topic_id": row[0],
        "summary": row[1],
        "source": row[2],
        "claim_level": row[3],
        "topic": topic,
    }


def persist_topic(
    con,
    topic: str,
    summary: str,
    source: str,
    response_hash: str,
    evidence: str,
) -> dict[str, Any]:
    topic_id = hashlib.sha256(f"{time.time_ns()}:{topic}".encode()).hexdigest()[:32]
    now = time.time()
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO learned_topics(
                topic_id, created_at, topic, summary, source, claim_level,
                evidence, response_hash
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                topic_id,
                now,
                topic,
                summary,
                source,
                "LEARNED_FROM_MODEL",
                evidence,
                response_hash,
            ),
        )
    return {
        "topic_id": topic_id,
        "topic": topic,
        "summary": summary,
        "source": source,
        "claim_level": "LEARNED_FROM_MODEL",
        "created_at": now,
    }


def learn_topic(con, topic: str, *, track: str = "flash") -> dict[str, Any]:
    allowed, reason = topic_allowed(topic)
    if not allowed:
        return {"status": "DENIED", "reason": reason, "topic": topic, "answer": None}
    existing = already_learned(con, topic)
    if existing:
        return {
            "status": "RECALL",
            "topic": topic,
            "answer": existing["summary"],
            "claim_level": "LEARNED_FROM_MODEL",
            "source": existing["source"],
        }
    prompt = (
        f"موضوع برای یادگیری مفهومی (نه واقعیت زنده اینترنت):\n{topic}\n"
        "در چند جمله کوتاه بگو چیست. بگو این دانش مدل است نه حسگر."
    )
    result = complete_flash(prompt) if track == "flash" else complete_deep(prompt)
    if result.get("status") != "OK" or not result.get("answer"):
        return {
            "status": result.get("status") or "DEGRADED",
            "reason": result.get("error"),
            "topic": topic,
            "answer": None,
            "track": result.get("track"),
        }
    summary = str(result["answer"]).strip()
    stored = persist_topic(
        con,
        topic,
        summary,
        f"deepseek_{result.get('track')}",
        str(result.get("response_hash") or ""),
        f"model={result.get('model')}",
    )
    return {
        "status": "LEARNED",
        **stored,
        "answer": summary,
        "latency_ms": result.get("latency_ms"),
    }


def format_learned_answer(result: dict[str, Any]) -> str:
    summary = (result.get("answer") or "").strip()
    topic = result.get("topic") or ""
    prefix = "[LEARNED_FROM_MODEL]"
    if topic:
        return f"{prefix} {topic}: {summary}".strip()
    return f"{prefix} {summary}".strip()


def maybe_self_learn(
    con,
    snapshot: dict[str, Any],
    *,
    cooldown_s: float = 180.0,
) -> dict[str, Any] | None:
    from ofn.organism.cognition.curiosity import propose_curiosity
    from ofn.organism.cognition.policy import learn_external_enabled
    from ofn.organism.growth.habits import set_meta
    from ofn.organism.runtime.public_status import meta_value

    if not learn_external_enabled():
        return None
    try:
        require_memory_gate(con, "learning")
    except MemoryUnavailable as exc:
        return unavailable_payload(str(exc))
    now = time.time()
    try:
        last = float(meta_value(con, "last_learn_at", "0") or 0)
    except (TypeError, ValueError):
        last = 0.0
    if now - last < cooldown_s:
        return None
    topic = propose_curiosity(snapshot, con)
    if not topic:
        return None
    result = learn_topic(con, topic, track="flash")
    set_meta(con, "last_learn_at", str(now))
    return result
