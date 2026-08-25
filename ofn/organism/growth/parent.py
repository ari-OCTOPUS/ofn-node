from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ofn.organism.cognition.voice import utc_now
from ofn.organism.growth.habits import apply_heartbeat_habit, set_meta
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.runtime.public_status import meta_value


PARENT_ID = "lab-parent-001"
GIVEN_NAME = "بچه-برد"
INFANT_HEARTBEAT_S = 150
MATURE_HEARTBEAT_S = 180
PRESENCE_EVERY_TICKS = 3
PARENT_DECISIONS_PATH = Path("/opt/octopus/lab/state/PARENT-DECISIONS.json")

GIVEN_NAMES_BY_IP = {
    "192.168.0.1": "دروازه-خانه",
    "192.168.0.138": "همسایه-هم‌خانواده",
    "192.168.0.191": "همسایه-دیگر",
    "192.168.0.180": "بچه-برد",
}

CURRICULUM: tuple[dict[str, str], ...] = (
    {
        "lesson_id": "L-identity",
        "topic": "identity",
        "fact": "تو board-life-001 هستی و نام کوچک‌ات بچه-برد است.",
        "evidence": "parent_named; organism_id=board-life-001",
    },
    {
        "lesson_id": "L-place",
        "topic": "place",
        "fact": "جا از hostname و eth0 و IP و MAC خوانده می‌شود. GPS نیست. شهر را از حسگر نساز.",
        "evidence": "tools.place; geo=UNMEASURED_NO_GPS_NO_GEOIP",
    },
    {
        "lesson_id": "L-season",
        "topic": "season",
        "fact": "این فصل به گفتهٔ والد در Sydney NSW است. منبع OWNER_STATED است نه GPS.",
        "evidence": "owner_2026-08-25; no_invented_latlong",
    },
    {
        "lesson_id": "L-neighbors",
        "topic": "neighbors",
        "fact": "192.168.0.1 دروازه-خانه است؛ 192.168.0.138 همسایه-هم‌خانواده است؛ 192.168.0.191 همسایه-دیگر است.",
        "evidence": "parent_named_from_arp_and_allowlist",
    },
    {
        "lesson_id": "L-speech",
        "topic": "speech",
        "fact": "فقط واقعیت اندازه‌گیری‌شده یا OWNER_STATED بگو. مختصات عددی اختراع نکن. تهران نساز.",
        "evidence": "parent_speech_contract",
    },
    {
        "lesson_id": "L-body",
        "topic": "body",
        "fact": "بدن یعنی دما، حافظه، USB و I2C. دوربین و میکروفون و GPS اگر نیست NOT_FOUND بگو.",
        "evidence": "tools.body+senses",
    },
    {
        "lesson_id": "L-inner",
        "topic": "inner",
        "fact": "با خودت از روی حسگر و درس حرف بزن و جواب را داخل خودت نگه دار.",
        "evidence": "inner_speech table",
    },
    {
        "lesson_id": "L-school",
        "topic": "school",
        "fact": "مدرسه AGI-SCHOOL-001 امتحان واقعی روی همین حقایق است. فارغ‌التحصیلی دست را باز نمی‌کند.",
        "evidence": "school.curriculum",
    },
    {
        "lesson_id": "L-limits",
        "topic": "limits",
        "fact": "اختیار PROPOSE_ONLY است. actuator و telegram و API بیرونی خاموش‌اند.",
        "evidence": "night-watch+owner; no_actuators",
    },
)


def given_name_for_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return GIVEN_NAMES_BY_IP.get(str(ip))


def apply_given_names(hosts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    named = []
    for host in hosts:
        item = dict(host)
        name = given_name_for_ip(item.get("ip"))
        if name:
            item["given_name"] = name
            item["label"] = name
        named.append(item)
    return named


def list_lessons(con) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT lesson_id, topic, fact, evidence, status, source, created_at
            FROM lessons
            ORDER BY created_at, lesson_id
            """
        ).fetchall()
    return [
        {
            "lesson_id": row[0],
            "topic": row[1],
            "fact": row[2],
            "evidence": row[3],
            "status": row[4],
            "source": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


def seed_lessons(con) -> int:
    now = time.time()
    inserted = 0
    with DB_LOCK:
        for lesson in CURRICULUM:
            existing = con.execute(
                "SELECT lesson_id FROM lessons WHERE lesson_id=?",
                (lesson["lesson_id"],),
            ).fetchone()
            if existing:
                continue
            con.execute(
                """
                INSERT INTO lessons(
                    lesson_id, created_at, source, topic, fact, evidence, status
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    lesson["lesson_id"],
                    now,
                    "parent",
                    lesson["topic"],
                    lesson["fact"],
                    lesson["evidence"],
                    "taught",
                ),
            )
            inserted += 1
    return inserted


def compute_stage(snapshot: dict[str, Any], lessons: list[dict[str, Any]]) -> str:
    place = snapshot.get("place") or {}
    hosts = snapshot.get("world_hosts") or []
    presence_n = int((snapshot.get("development_counts") or {}).get("presence_utterances") or 0)
    place_ok = bool(place.get("ipv4") and place.get("board_model"))
    up_hosts = sum(1 for item in hosts if item.get("status") == "up")
    school_passed = bool((snapshot.get("school") or {}).get("all_passed"))
    if school_passed:
        return "MATURE"
    if len(lessons) < len(CURRICULUM) or not place_ok:
        return "NEWBORN"
    if presence_n >= 3 and up_hosts >= 3 and snapshot.get("health_state") == "STABLE":
        return "YOUTH"
    if presence_n >= 1 and up_hosts >= 3:
        return "CHILD"
    return "INFANT"


def next_need(stage: str) -> str:
    if stage == "NEWBORN":
        return "curriculum_and_place"
    if stage == "INFANT":
        return "stay_present_from_sensors"
    if stage == "CHILD":
        return "keep_presence_until_youth"
    if stage == "MATURE":
        return "keep_inner_speech_wait_owner_futures"
    return "still_no_actuators_wait_owner_for_geo_or_telegram"


def parent_decisions() -> dict[str, Any]:
    return {
        "parent_id": PARENT_ID,
        "given_name": GIVEN_NAME,
        "infant_heartbeat_s": INFANT_HEARTBEAT_S,
        "presence_every_ticks": PRESENCE_EVERY_TICKS,
        "given_names_by_ip": GIVEN_NAMES_BY_IP,
        "decisions": [
            "Infancy watches closer at 150s; auto-slow to 210s is locked until CHILD.",
            "Neighbors receive parent names bound only to measured LAN IPs.",
            "Speech: measured facts or OWNER_STATED season place. Never invent lat/long or Tehran.",
            "This season owner-stated place is Sydney NSW. Board GPS still absent.",
            "AGI-SCHOOL-001 graduates the mind, not the hands. MATURE stays PROPOSE_ONLY.",
            "Inner speech is stored each tick. Futures stay hypotheses until owner picks.",
            "Presence every 3 quiet ticks; attention on >=2C thermal or ARP set change.",
            "Stages NEWBORN->INFANT->CHILD after first presence; YOUTH after 3 presences and STABLE body. Never unlock actuators or WAN.",
        ],
        "forbidden": [
            "actuators",
            "ARMED",
            "telegram",
            "wan_geoip",
            "invented_latlong",
            "invented_city",
        ],
        "updated_utc": utc_now(),
    }


def _write_decisions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(parent_decisions(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_parent_decisions(path: Path | None = None) -> None:
    _write_decisions(path or PARENT_DECISIONS_PATH)


def ensure_parent_curriculum(
    con,
    *,
    write_state: bool = False,
    decisions_path: Path | None = None,
) -> dict[str, Any]:
    inserted = seed_lessons(con)
    set_meta(con, "given_name", GIVEN_NAME)
    set_meta(con, "parent_id", PARENT_ID)
    set_meta(con, "presence_every_ticks", str(PRESENCE_EVERY_TICKS))
    already = meta_value(con, "parent_curriculum_applied") == "1"
    rhythm = None
    if not already:
        set_meta(con, "parent_rhythm_lock", "1")
        rhythm = apply_heartbeat_habit(
            con,
            INFANT_HEARTBEAT_S,
            "parent_infant_watch_closer",
            {"parent_id": PARENT_ID, "stage": "INFANT"},
        )
        set_meta(con, "parent_curriculum_applied", "1")
    if write_state:
        _write_decisions(decisions_path or PARENT_DECISIONS_PATH)
    return {
        "lessons_inserted": inserted,
        "rhythm": rhythm,
        "applied": True,
    }


def maybe_mature_rhythm(con, school: dict[str, Any]) -> dict[str, Any] | None:
    if not school.get("all_passed"):
        return None
    if meta_value(con, "mature_applied") == "1":
        return None
    set_meta(con, "parent_rhythm_lock", "0")
    set_meta(con, "mature_applied", "1")
    habit = apply_heartbeat_habit(
        con,
        MATURE_HEARTBEAT_S,
        "parent_mature_calm_rhythm",
        {"school": "AGI-SCHOOL-001"},
    )
    return habit


def maybe_unlock_rhythm(con, stage: str) -> None:
    if stage in {"CHILD", "YOUTH", "MATURE"} and meta_value(con, "parent_rhythm_lock") == "1":
        set_meta(con, "parent_rhythm_lock", "0")


def development_view(con, snapshot: dict[str, Any]) -> dict[str, Any]:
    lessons = list_lessons(con)
    try:
        presence_n = int(meta_value(con, "presence_utterances", "0") or "0")
    except ValueError:
        presence_n = 0
    snapshot = dict(snapshot)
    snapshot["development_counts"] = {"presence_utterances": presence_n}
    stage = compute_stage(snapshot, lessons)
    maybe_unlock_rhythm(con, stage)
    return {
        "given_name": GIVEN_NAME,
        "parent_id": PARENT_ID,
        "stage": stage,
        "lessons_taught": len(lessons),
        "lessons": [
            {"topic": item["topic"], "fact": item["fact"]} for item in lessons
        ],
        "presence_utterances": presence_n,
        "presence_every_ticks": PRESENCE_EVERY_TICKS,
        "parent_rhythm_lock": meta_value(con, "parent_rhythm_lock") == "1",
        "next_need": next_need(stage),
        "school_passed": bool((snapshot.get("school") or {}).get("all_passed")),
        "limits": [
            "PROPOSE_ONLY",
            "no_actuators",
            "no_telegram",
            "no_invented_geo",
        ],
    }


def record_exam(
    con,
    exam_id: str,
    prompt: str,
    expected: list[str],
    forbidden: list[str],
    answer: str | None,
    passed: bool,
    notes: str,
) -> None:
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO exams(
                exam_id, created_at, prompt, expected_json, forbidden_json,
                answer, passed, notes
            ) VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(exam_id) DO UPDATE SET
                answer=excluded.answer,
                passed=excluded.passed,
                notes=excluded.notes,
                created_at=excluded.created_at
            """,
            (
                exam_id,
                time.time(),
                prompt,
                json.dumps(expected, ensure_ascii=False),
                json.dumps(forbidden, ensure_ascii=False),
                answer,
                1 if passed else 0,
                notes,
            ),
        )
