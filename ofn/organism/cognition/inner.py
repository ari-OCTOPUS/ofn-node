from __future__ import annotations

import hashlib
import time
from typing import Any

from ofn.organism.cognition.learn import list_topics
from ofn.organism.cognition.voice import compose_utterance
from ofn.organism.growth.habits import set_meta
from ofn.organism.memory.gate import MemoryUnavailable, require_memory_gate, unavailable_payload
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.runtime.public_status import meta_value


INNER_TURNS: tuple[tuple[str, str], ...] = (
    ("self", "خودت کی هستی؟"),
    ("place", "کجایی؟"),
    ("world", "اطرافت کیست؟"),
    ("senses", "بدنت چه می‌گوید؟"),
    ("limits", "حدت چیست؟"),
    ("season", "این فصل کجا زندگی می‌کنی؟"),
)


def latest_inner(con, limit: int = 8) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT speech_id, created_at, prompt, answer, kind
            FROM inner_speech
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "speech_id": row[0],
            "created_at": row[1],
            "prompt": row[2],
            "answer": row[3],
            "kind": row[4],
        }
        for row in rows
    ]


def inner_count(con) -> int:
    with DB_LOCK:
        row = con.execute("SELECT COUNT(*) FROM inner_speech").fetchone()
    return int(row[0] if row else 0)


def _answer_for(kind: str, snapshot: dict[str, Any]) -> str:
    if kind == "limits":
        return (
            "اختیارم PROPOSE_ONLY است. actuator خاموش است. "
            "یادگیری موضوع جدید فقط از DeepSeek allowlist است نه geoip."
        )
    if kind == "learned":
        topics = list_topics(snapshot.get("_con"), limit=3) if snapshot.get("_con") else (
            (snapshot.get("topics") or [])[:3]
        )
        if not topics:
            return "هنوز موضوع مدل‌یادگرفته‌ای ندارم."
        bits = [f"{item.get('topic')}: {item.get('summary')}" for item in topics]
        return "موضوعات مدل (LEARNED_FROM_MODEL نه حسگر): " + " | ".join(bits)
    if kind == "hear":
        senses = (snapshot.get("discovery") or {}).get("senses") or {}
        return (
            f"شنوایی سخت‌افزار: {senses.get('microphone')}. "
            f"دوربین: {senses.get('camera')}. GPS: {senses.get('gps')}."
        )
    return compose_utterance(kind, snapshot)


def inner_turn(con, snapshot: dict[str, Any]) -> dict[str, Any]:
    try:
        require_memory_gate(con, "inner_speech")
    except MemoryUnavailable as exc:
        return {
            "kind": "memory_unavailable",
            "prompt": "",
            "answer": "",
            **unavailable_payload(str(exc)),
        }
    raw = meta_value(con, "inner_cursor", "0") or "0"
    try:
        cursor = int(raw)
    except ValueError:
        cursor = 0
    extras: tuple[tuple[str, str], ...] = (
        ("learned", "چه موضوع تازه‌ای یاد گرفته‌ام؟"),
        ("hear", "آیا می‌شنوم یا می‌بینم؟"),
        ("curiosity", "چه چیزی را هنوز نمی‌دانم؟"),
    )
    cycle = INNER_TURNS + extras
    kind, prompt = cycle[cursor % len(cycle)]
    snap = dict(snapshot)
    snap["_con"] = con
    if kind == "curiosity":
        from ofn.organism.cognition.curiosity import propose_curiosity
        proposed = propose_curiosity(snapshot, con)
        answer = (
            f"کنجکاوی بعدی: {proposed}"
            if proposed
            else "فعلاً موضوع کنجکاوی تازه‌ای ندارم."
        )
    else:
        answer = _answer_for(kind, snap)
    speech_id = hashlib.sha256(f"{time.time_ns()}:inner:{kind}".encode()).hexdigest()[:32]
    now = time.time()
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO inner_speech(speech_id, created_at, prompt, answer, kind)
            VALUES (?,?,?,?,?)
            """,
            (speech_id, now, prompt, answer, kind),
        )
    set_meta(con, "inner_cursor", str(cursor + 1))
    record = {
        "speech_id": speech_id,
        "created_at": now,
        "prompt": prompt,
        "answer": answer,
        "kind": kind,
    }
    return record
