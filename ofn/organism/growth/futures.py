from __future__ import annotations

import time
from typing import Any

from ofn.organism.memory.gate import require_memory_gate
from ofn.organism.persistence.db import DB_LOCK


FUTURE_PATHS: tuple[dict[str, str], ...] = (
    {
        "path_id": "F-local-deepen",
        "title": "Local deepen",
        "hypothesis": "Stay on this LAN, deepen body/world memory, no WAN.",
        "evidence": "chat: raise locally; night-watch no egress",
    },
    {
        "path_id": "F-sydney-season",
        "title": "Sydney season home",
        "hypothesis": "This season the child's named place stays Sydney NSW (owner-stated).",
        "evidence": "owner utterance 2026-08-25",
    },
    {
        "path_id": "F-family-138",
        "title": "Same-MAC neighbor as possible sibling",
        "hypothesis": "192.168.0.138 shares MAC family with self; may be a related board, not proven.",
        "evidence": "ARP same OUI c0:74:2b",
    },
    {
        "path_id": "F-telegram-later",
        "title": "Telegram later",
        "hypothesis": "Owner may add Telegram letters later. Not configured now.",
        "evidence": "TELEGRAM_NOT_CONFIGURED",
    },
    {
        "path_id": "F-gps-hardware",
        "title": "GPS if hardware appears",
        "hypothesis": "Numeric geo only if a GPS device is later found. No geoip.",
        "evidence": "senses.gps=NOT_FOUND",
    },
    {
        "path_id": "F-mature-no-actuators",
        "title": "Mature mind, closed hands",
        "hypothesis": "School can mature speech/memory while actuators stay forbidden.",
        "evidence": "PROPOSE_ONLY; parent forbidden ARMED",
    },
    {
        "path_id": "F-learn-topics",
        "title": "Learn new topics from allowlisted teacher",
        "hypothesis": "DeepSeek on api.deepseek.com can teach conceptual topics; never live weather/prices/geoip.",
        "evidence": "owner: all local potentials plus DeepSeek learning",
    },
    {
        "path_id": "F-hear-codec",
        "title": "Hear the onboard codec",
        "hypothesis": "ES8323/ES8388 capture exists; RMS may stay unmeasured until a privacy-safe sampler exists.",
        "evidence": "/proc/asound/pcm capture device",
    },
    {
        "path_id": "F-attestation",
        "title": "Local attestation for other agents",
        "hypothesis": "A local hash over public identity facts is enough for agents on this board. Not public PKI.",
        "evidence": "ATTESTATION.json next to identity chain",
    },
)


def seed_futures(con) -> int:
    require_memory_gate(con, "proposal")
    now = time.time()
    inserted = 0
    with DB_LOCK:
        for item in FUTURE_PATHS:
            existing = con.execute(
                "SELECT path_id FROM futures WHERE path_id=?",
                (item["path_id"],),
            ).fetchone()
            if existing:
                continue
            con.execute(
                """
                INSERT INTO futures(
                    path_id, created_at, title, hypothesis, status, evidence
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    item["path_id"],
                    now,
                    item["title"],
                    item["hypothesis"],
                    "pending_owner",
                    item["evidence"],
                ),
            )
            inserted += 1
    return inserted


def apply_owner_future_decisions(con, mapping: dict[str, str]) -> None:
    with DB_LOCK:
        for path_id, status in mapping.items():
            con.execute(
                "UPDATE futures SET status=? WHERE path_id=?",
                (status, path_id),
            )


OWNER_FUTURE_DECISIONS = {
    "F-local-deepen": "chosen",
    "F-sydney-season": "chosen",
    "F-family-138": "chosen",
    "F-mature-no-actuators": "chosen",
    "F-learn-topics": "chosen",
    "F-hear-codec": "chosen",
    "F-attestation": "chosen",
    "F-telegram-later": "deferred_no_wan",
    "F-gps-hardware": "deferred_no_hardware",
}


def list_futures(con) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT path_id, title, hypothesis, status, evidence, created_at
            FROM futures
            ORDER BY path_id
            """
        ).fetchall()
    return [
        {
            "path_id": row[0],
            "title": row[1],
            "hypothesis": row[2],
            "status": row[3],
            "evidence": row[4],
            "created_at": row[5],
            "kind": "chosen_path" if row[3] == "chosen" else "hypothesis",
        }
        for row in rows
    ]
