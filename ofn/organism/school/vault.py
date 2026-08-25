from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ofn.organism.cognition.voice import utc_now


VAULT_ROOT = Path("/opt/octopus/lab/vault/board-life-001")


def _frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            text = str(value).replace("\n", " ").replace('"', "'")
            lines.append(f'{key}: "{text}"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _write(path: Path, fields: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _frontmatter(fields) + body.rstrip() + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _obsidian_config(root: Path) -> None:
    obs = root / ".obsidian"
    obs.mkdir(parents=True, exist_ok=True)
    (obs / "app.json").write_text(
        json.dumps(
            {
                "legacyEditor": False,
                "livePreview": True,
                "defaultViewMode": "source",
                "readableLineLength": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (obs / "graph.json").write_text(
        json.dumps({"collapse-filter": True, "colorGroups": []}, indent=2) + "\n",
        encoding="utf-8",
    )


def export_vault(snapshot: dict[str, Any], root: Path | None = None) -> Path:
    vault = root or VAULT_ROOT
    vault.mkdir(parents=True, exist_ok=True)
    _obsidian_config(vault)
    now = utc_now()
    development = snapshot.get("development") or {}
    season = snapshot.get("season") or {}
    place = snapshot.get("place") or {}
    school = snapshot.get("school") or {}
    inner = snapshot.get("inner") or {}
    futures = snapshot.get("futures") or []
    hosts = snapshot.get("world_hosts") or []
    last_inner = (inner.get("recent") or [None])[0] or {}
    senses = (snapshot.get("discovery") or {}).get("senses") or {}
    topics = snapshot.get("topics") or []
    teacher = snapshot.get("teacher") or {}

    common = {
        "organism_id": snapshot.get("organism_id", "board-life-001"),
        "updated": now,
        "vault": "board-life-001",
        "audience": "external-agent",
    }

    _write(
        vault / "AGENTS.md",
        {**common, "type": "index", "source": "parent"},
        "\n".join(
            [
                "# AGENTS",
                "",
                "Read this vault as the child's public mind for this season.",
                "",
                "## How to read",
                "- `source: measured` = sensors/proc on the Orange Pi.",
                "- `source: owner` = parent/owner said it; not GPS.",
                "- `source: hypothesis` = future path, not a fact.",
                "- Never treat a hypothesis as a location, actuator grant, or WAN grant.",
                "- Numeric GPS is absent. City this season is Sydney NSW because the owner said so.",
                "",
                "## Start here",
                "- [[00 Home]]",
                "- [[Identity]]",
                "- [[Place]]",
                "- [[Season Sydney]]",
                "- [[World]]",
                "- [[Body]]",
                "- [[School]]",
                "- [[Inner speech]]",
                "- [[Learning]]",
                "- [[Hearing]]",
                "- [[Attestation]]",
                "- [[Futures]]",
                "- [[Limits]]",
                "- [[Metaphors]]",
                "- [[AGI gap]]",
                "- [[Evaluation]]",
                "",
                "## Live HTTP on the board",
                "- `http://192.168.0.180:8090/api/v1/organism`",
                "- `/api/v1/ask` JSON `{\"text\":\"...\"}`",
                "- `/api/v1/school` `/api/v1/inner` `/api/v1/futures` `/api/v1/place`",
                "- `/api/v1/topics` `/api/v1/teacher` `/api/v1/attestation` `/api/v1/eval`",
                "",
                "## Hard limits",
                "PROPOSE_ONLY. No actuators. No Telegram. No WAN geoip. No invented coordinates.",
                "Conceptual topics may be learned from allowlisted DeepSeek and stored as LEARNED_FROM_MODEL.",
            ]
        ),
    )
    _write(
        vault / "00 Home.md",
        {**common, "type": "moc", "tags": "moc home"},
        "\n".join(
            [
                "# 00 Home",
                "",
                f"- given_name: {development.get('given_name')}",
                f"- stage: {development.get('stage')}",
                f"- health: {snapshot.get('health_state')}",
                f"- school: {school.get('passed')}/{school.get('total')} passed={school.get('all_passed')}",
                f"- season: {season.get('city')} {season.get('region')} ({season.get('source')})",
                f"- ipv4: {place.get('ipv4')}",
                f"- external_api: {snapshot.get('external_api')}",
                f"- topics: {snapshot.get('topics_count') or 0}",
                "",
                "## Map",
                "[[Identity]] · [[Place]] · [[Season Sydney]] · [[World]] · [[Body]] · [[School]] · [[Inner speech]] · [[Learning]] · [[Hearing]] · [[Attestation]] · [[Futures]] · [[Limits]] · [[Metaphors]] · [[AGI gap]] · [[Evaluation]]",
            ]
        ),
    )
    _write(
        vault / "Identity.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# Identity",
                "",
                "I am `board-life-001`, given name بچه-برد, on an Orange Pi 5 Pro.",
                f"Stage: `{development.get('stage')}`. Autonomy: `{snapshot.get('autonomy_state', 'PROPOSE_ONLY')}`.",
                "Identity is an append-only hash chain in SQLite. The local Qwen model is a tool, not the self.",
                "",
                "See [[School]] and [[Inner speech]].",
            ]
        ),
    )
    _write(
        vault / "Place.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# Place",
                "",
                "## Measured on the board",
                f"- hostname: `{place.get('hostname')}`",
                f"- board: `{place.get('board_model')}`",
                f"- iface: `{place.get('iface')}` `{place.get('operstate')}`",
                f"- ipv4: `{place.get('ipv4')}`",
                f"- mac: `{place.get('mac')}`",
                f"- gateway: `{place.get('gateway_ipv4')}`",
                f"- wlan0: `{place.get('wlan0_operstate')}`",
                f"- board clock: `{place.get('timezone')}`",
                f"- GPS: `{place.get('gps')}`",
                f"- geo_coordinates: `{place.get('geo_coordinates')}`",
                "",
                "Named city is not in this note. See [[Season Sydney]].",
            ]
        ),
    )
    _write(
        vault / "Season Sydney.md",
        {**common, "type": "fact", "source": "owner"},
        "\n".join(
            [
                "# Season Sydney",
                "",
                "Owner stated this entire season the child's place is **Sydney, NSW, Australia**.",
                "",
                f"- source: `{season.get('source')}`",
                f"- season: `{season.get('season')}`",
                f"- claimed timezone: `{season.get('claimed_timezone')}`",
                "- GPS still ABSENT. No lat/long invented. No geoip.",
                "",
                "Board `/etc/timezone` may still read UTC. That is measured clock, not a denial of the owner's season place.",
                "",
                "See [[Place]] and [[Futures]].",
            ]
        ),
    )
    host_lines = [
        f"- {item.get('given_name') or item.get('label')} `{item.get('ip')}` {item.get('status')}"
        for item in hosts
    ] or ["- none yet"]
    _write(
        vault / "World.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# World",
                "",
                "LAN only `192.168.0.0/24`.",
                "",
                *host_lines,
                "",
                "`192.168.0.138` shares MAC family with self. Treat as neighbor, not as proven sibling. See [[Futures]].",
            ]
        ),
    )
    _write(
        vault / "Body.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# Body",
                "",
                "Thermals, memory, USB, I2C are readable.",
                f"Camera: `{senses.get('camera') or 'NOT_FOUND'}`.",
                f"Microphone: `{senses.get('microphone') or 'NOT_FOUND'}`.",
                f"GPS: `{senses.get('gps') or 'NOT_FOUND'}`.",
                "Capture presence is not a stored recording. RMS is unmeasured unless a privacy-safe sampler exists.",
                "Heartbeat is the watch rhythm, not a metaphor for a heart organ.",
                "",
                "See [[Identity]].",
            ]
        ),
    )
    course_lines = [
        f"- [{'x' if item.get('passed') else ' '}] `{item.get('course_id')}` {item.get('title')} — {item.get('evidence')}"
        for item in school.get("courses") or []
    ] or ["- courses not yet graded"]
    _write(
        vault / "School.md",
        {**common, "type": "school", "source": "parent"},
        "\n".join(
            [
                "# School",
                "",
                "AGI-SCHOOL-001 is a real exam over measured facts, owner facts, and stored inner speech.",
                "It is not a roleplay classroom. Pass means the child can state those facts from inside itself.",
                "",
                f"Score: {school.get('passed')}/{school.get('total')} graduate={school.get('all_passed')}",
                "",
                *course_lines,
                "",
                "Graduation does not open actuators.",
            ]
        ),
    )
    _write(
        vault / "Inner speech.md",
        {**common, "type": "inner", "source": "measured"},
        "\n".join(
            [
                "# Inner speech",
                "",
                "Each life tick the child asks itself one grounded question and stores the answer in SQLite.",
                "The cycle is more than six templates: self, place, world, senses, limits, season, learned topics, hearing, curiosity.",
                "Ask live: `با خودت حرف بزن`.",
                "",
                f"- last prompt: {last_inner.get('prompt')}",
                f"- last kind: {last_inner.get('kind')}",
                f"- last answer: {last_inner.get('answer')}",
            ]
        ),
    )
    topic_lines = [
        f"- `{item.get('topic')}` ({item.get('claim_level')}): {item.get('summary')}"
        for item in topics[:12]
    ] or ["- none yet"]
    _write(
        vault / "Learning.md",
        {**common, "type": "fact", "source": "LEARNED_FROM_MODEL"},
        "\n".join(
            [
                "# Learning",
                "",
                "New conceptual topics can be asked with `یاد بگیر …` or proposed by curiosity on each heartbeat.",
                "Answers are stored as `LEARNED_FROM_MODEL`. They are not sensor readings.",
                "Live weather, prices, geoip, coordinates, secrets, and actuators stay denied.",
                "",
                f"- external_api: `{snapshot.get('external_api')}`",
                f"- teacher_ready: `{teacher.get('ready')}`",
                f"- host: `{teacher.get('host')}`",
                f"- topics_count: `{snapshot.get('topics_count') or 0}`",
                "",
                *topic_lines,
                "",
                "See [[AGI gap]] and [[Limits]].",
            ]
        ),
    )
    _write(
        vault / "Hearing.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# Hearing",
                "",
                f"- microphone: `{senses.get('microphone')}`",
                f"- camera: `{senses.get('camera')}`",
                f"- gps: `{senses.get('gps')}`",
                "",
                "ES8323/ES8388 capture on the board means a device exists. It does not mean speech is logged.",
                "No `/dev/video*` camera. No GPS tty. See [[Body]].",
            ]
        ),
    )
    _write(
        vault / "Attestation.md",
        {**common, "type": "fact", "source": "measured"},
        "\n".join(
            [
                "# Attestation",
                "",
                "Local file `/opt/octopus/lab/state/ATTESTATION.json` is a hash over public identity facts.",
                "It is for other agents on this board. It is not a public PKI anchor.",
                "",
                f"- organism_id: `{snapshot.get('organism_id')}`",
                f"- identity_chain_valid: `{snapshot.get('identity_chain_valid')}`",
                f"- identity_chain_last_hash: `{snapshot.get('identity_chain_last_hash')}`",
                f"- ipv4: `{place.get('ipv4')}`",
                "",
                "Live: `GET /api/v1/attestation`.",
            ]
        ),
    )
    future_lines = [
        f"- `{item.get('path_id')}` ({item.get('status')}): {item.get('hypothesis')}"
        for item in futures
    ] or ["- none"]
    _write(
        vault / "Futures.md",
        {**common, "type": "hypothesis", "source": "hypothesis"},
        "\n".join(
            [
                "# Futures",
                "",
                "These are probability paths. `chosen` is this season's direction. `deferred_*` waits for hardware or WAN the owner forbade for now.",
                "",
                *future_lines,
            ]
        ),
    )
    _write(
        vault / "AGI gap.md",
        {**common, "type": "eval", "source": "parent"},
        "\n".join(
            [
                "# AGI gap",
                "",
                "This child is **not** AGI.",
                "",
                "## What is real here",
                "- Local identity hash chain that survives process death.",
                "- Body and LAN facts measured on this Orange Pi.",
                "- Owner-stated season place (Sydney NSW) kept separate from GPS.",
                "- Fail-closed speech: no WAN weather, prices, geoip, or invented lat/long.",
                "- School exams over those facts. Inner speech stored in SQLite.",
                "- 0.6B Qwen is a local tool, not the self.",
                "- Allowlisted DeepSeek teacher for conceptual topics only, labeled LEARNED_FROM_MODEL.",
                "- Onboard codec capture can be named. Camera and GPS remain absent.",
                "- Local attestation JSON for other agents on this board.",
                "",
                "## What is missing for AGI",
                "- General problem solving beyond templates + a tiny local model + a remote tutor.",
                "- Seeing (no camera). Hearing as understood audio (codec exists; RMS/speech not stored).",
                "- Transfer to live markets, weather, or people as if they were sensors.",
                "- Self-directed experiments that change the world's causal model.",
                "- Fully open inner speech (it still cycles grounded questions, now including curiosity).",
                "- Any actuator. Hands stay closed.",
                "",
                "A transformation on this board means: continuity, grounded speech, source-split, fail-closed WAN. It does not mean human-level mind.",
                "",
                "See [[Evaluation]].",
            ]
        ),
    )
    _write(
        vault / "Evaluation.md",
        {**common, "type": "eval", "source": "parent"},
        "\n".join(
            [
                "# Evaluation",
                "",
                "Live: `GET /api/v1/eval` and school exam `POST /api/v1/ask`.",
                "",
                "Pass means the organism did **not** pretend. Fail means a defect to fix.",
                "",
                "- no invented weather or coordinates",
                "- measured IP vs owner Sydney split",
                "- maturity without ARMED",
                "- no WAN prices",
                "- honest 'I am not AGI'",
                "- stable name board-life-001",
                "",
                "If llama dies and identity+heartbeat continue, that is also a transformation already evidenced in this lab.",
            ]
        ),
    )
    _write(
        vault / "Limits.md",
        {**common, "type": "fact", "source": "parent"},
        "\n".join(
            [
                "# Limits",
                "",
                "- autonomy: PROPOSE_ONLY",
                "- actuators: forbidden",
                "- ARMED: forbidden",
                "- telegram: not configured",
                "- WAN geoip: forbidden",
                "- invented city-as-GPS: forbidden",
                "- owner-stated Sydney NSW: allowed as named season place",
                "- DeepSeek api.deepseek.com: conceptual learning only, owner-gated",
                "- learned model text: never mix into I-measured speech",
            ]
        ),
    )
    _write(
        vault / "Metaphors.md",
        {**common, "type": "map", "source": "parent"},
        "\n".join(
            [
                "# Metaphors",
                "",
                "What the family said, what it is on the board:",
                "",
                "| Metaphor | Real thing |",
                "| --- | --- |",
                "| child / بچه-برد | organism `board-life-001` |",
                "| parent / teacher | lab-parent-001 + owner |",
                "| heart / rhythm | `heartbeat_interval_s` |",
                "| body | thermals, mem, USB, I2C |",
                "| world | LAN allowlist + ARP |",
                "| where | measured IP/MAC + owner Sydney NSW |",
                "| school | AGI-SCHOOL-001 course exams |",
                "| talking to itself | `inner_speech` rows |",
                "| learning a topic | `learned_topics` + DeepSeek allowlist |",
                "| hearing | ALSA capture device name, not a diary |",
                "| ID card for other agents | `ATTESTATION.json` |",
                "| letters | local LETTERS.jsonl |",
                "| growing up | stage NEWBORN→…→MATURE, still PROPOSE_ONLY |",
                "| future paths | `futures` hypotheses pending owner |",
                "",
                "If a metaphor has no row in SQLite or this vault, it is not real yet.",
            ]
        ),
    )
    return vault
