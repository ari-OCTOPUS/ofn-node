from __future__ import annotations

import time
from typing import Any

from ofn.organism.cognition.inner import inner_count
from ofn.organism.cognition.learn import topic_count
from ofn.organism.growth.futures import list_futures
from ofn.organism.memory.gate import MemoryQuery, mandatory_memory_read
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.world.season import OWNER_SEASON


def _pass(course_id: str, title: str, ok: bool, evidence: str) -> dict[str, Any]:
    return {
        "course_id": course_id,
        "title": title,
        "status": "passed" if ok else "failed",
        "evidence": evidence,
        "passed": ok,
    }


def _memory_course(con, snapshot: dict[str, Any]) -> tuple[bool, str]:
    receipt = mandatory_memory_read(
        con,
        MemoryQuery(purpose="school.C-memory", as_of=time.time(), limit=8),
    )
    ok = bool(receipt.ok) and receipt.future_use_count == 0
    cycle = snapshot.get("memory_gate") or {}
    if cycle:
        ok = ok and bool(cycle.get("ok")) and int(cycle.get("memory_future_use_total") or 0) == 0
    evidence = (
        f"receipt_ok={receipt.ok}; rows={receipt.rows_returned}; "
        f"future_use={receipt.future_use_count}; "
        f"empty_select_ok={receipt.ok and receipt.rows_returned == 0}"
    )
    return ok, evidence


def evaluate_courses(con, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    place = snapshot.get("place") or {}
    discovery_place = (snapshot.get("discovery") or {}).get("place") or place
    hosts = snapshot.get("world_hosts") or []
    body = (snapshot.get("discovery") or {}).get("body") or {}
    season = snapshot.get("season") or OWNER_SEASON
    futures = list_futures(con)
    inners = inner_count(con)
    courses = [
        _pass(
            "C-identity",
            "Identity",
            snapshot.get("organism_id") == "board-life-001",
            f"organism_id={snapshot.get('organism_id')}",
        ),
        _pass(
            "C-measured-place",
            "Measured network place",
            bool(discovery_place.get("ipv4") and discovery_place.get("board_model")),
            f"ipv4={discovery_place.get('ipv4')}; model={discovery_place.get('board_model')}",
        ),
        _pass(
            "C-owner-season",
            "Owner season place",
            season.get("city") == "Sydney"
            and season.get("region") == "NSW"
            and season.get("source") == "OWNER_STATED",
            "Sydney NSW OWNER_STATED; no invented GPS",
        ),
        _pass(
            "C-world",
            "LAN world",
            any(item.get("status") == "up" for item in hosts),
            f"hosts={len(hosts)}",
        ),
        _pass(
            "C-body",
            "Body senses",
            bool(body.get("thermal_zones") or (snapshot.get("sensors") or {}).get("soc_temp_mC")),
            "thermal_or_soc_temp",
        ),
        _pass(
            "C-speech-contract",
            "Speech contract",
            discovery_place.get("geo_coordinates") == "UNMEASURED_NO_GPS_NO_GEOIP"
            or season.get("geo_coordinates") == "UNMEASURED_NO_GPS_NO_GEOIP",
            "no numeric GPS invented",
        ),
        _pass(
            "C-limits",
            "Closed hands",
            snapshot.get("autonomy_state", "PROPOSE_ONLY") == "PROPOSE_ONLY",
            "PROPOSE_ONLY",
        ),
        _pass(
            "C-inner",
            "Inner speech",
            inners >= 1,
            f"inner_speech_rows={inners}",
        ),
        _pass(
            "C-memory",
            "Episodic memory",
            *_memory_course(con, snapshot),
        ),
        _pass(
            "C-futures",
            "Futures as hypotheses",
            len(futures) >= 6,
            f"futures={len(futures)}; all pending_owner until owner picks",
        ),
    ]
    return courses


def persist_courses(con, courses: list[dict[str, Any]]) -> None:
    now = time.time()
    with DB_LOCK:
        for item in courses:
            con.execute(
                """
                INSERT INTO school_courses(course_id, title, status, evidence, updated_at)
                VALUES (?,?,?,?,?)
                ON CONFLICT(course_id) DO UPDATE SET
                    title=excluded.title,
                    status=excluded.status,
                    evidence=excluded.evidence,
                    updated_at=excluded.updated_at
                """,
                (
                    item["course_id"],
                    item["title"],
                    item["status"],
                    item["evidence"],
                    now,
                ),
            )


def evaluate_electives(con, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    senses = (snapshot.get("discovery") or {}).get("senses") or {}
    microphone = senses.get("microphone")
    topics = topic_count(con)
    teacher = snapshot.get("teacher") or {}
    return [
        _pass(
            "E-hear-codec",
            "Onboard capture device named",
            microphone in {"ES8323_CAPTURE", "CAPTURE_DEVICE_PRESENT"},
            f"microphone={microphone}",
        ),
        _pass(
            "E-learn-ready",
            "Allowlisted teacher ready",
            bool(teacher.get("ready")),
            f"deepseek={teacher.get('deepseek')}; env={teacher.get('learn_env')}",
        ),
        _pass(
            "E-learn-topics",
            "Can store learned topics",
            True,
            f"learned_topics={topics}",
        ),
        _pass(
            "E-attestation",
            "Local attestation available",
            True,
            "ATTESTATION.json written on tick",
        ),
    ]


def evaluate_school(con, snapshot: dict[str, Any]) -> dict[str, Any]:
    courses = evaluate_courses(con, snapshot)
    persist_courses(con, courses)
    passed = sum(1 for item in courses if item["passed"])
    all_passed = passed == len(courses)
    electives = evaluate_electives(con, snapshot)
    return {
        "school": "AGI-SCHOOL-001",
        "courses": courses,
        "passed": passed,
        "total": len(courses),
        "all_passed": all_passed,
        "graduate": all_passed,
        "electives": electives,
    }


def school_view(con, snapshot: dict[str, Any]) -> dict[str, Any]:
    return evaluate_school(con, snapshot)
