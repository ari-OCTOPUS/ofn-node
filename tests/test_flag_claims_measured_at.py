"""FLAG-CLAIMS registry — measured_at is mandatory, not decoration (F-09).

The 2026-09-02 incident: OWNER-GO-LOCKS claimed OFN_WIRE_OUTBOUND=0 while the
live node.env had said =1 since ~Aug 22 — a governance document reporting a
number nobody had ever read. This test makes that class of drift impossible
in the repo-side claim registry: an entry without a timestamped, reproducible
measurement cannot land on main."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "docs" / "runbooks" / "FLAG-CLAIMS.json"

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _load() -> dict:
    return json.loads(CLAIMS.read_text(encoding="utf-8"))


def test_registry_exists_and_nonempty() -> None:
    data = _load()
    assert data["schema"] == "octopus.flag-claims.v1"
    assert len(data["claims"]) >= 5


def test_every_claim_carries_measured_at_and_command() -> None:
    for c in _load()["claims"]:
        assert c.get("name"), c
        assert _ISO.match(c.get("measured_at", "")), \
            f"{c['name']}: measured_at must be ISO-8601 ...Z, got {c.get('measured_at')!r}"
        assert isinstance(c.get("command"), str) and len(c["command"]) >= 10, \
            f"{c['name']}: command must be a reproducible string"
        assert "value" in c and "class" in c, f"{c['name']}: value/class required"


def test_measured_at_is_parseable_and_not_future() -> None:
    now = datetime.now(timezone.utc)
    for c in _load()["claims"]:
        ts = datetime.strptime(c["measured_at"], "%Y-%m-%dT%H:%M:%SZ") \
            .replace(tzinfo=timezone.utc)
        assert ts <= now + __import__("datetime").timedelta(minutes=5), \
            f"{c['name']}: measured_at is in the future"


def test_intent_only_flags_say_so() -> None:
    for c in _load()["claims"]:
        if c["name"] == "OFN_WIRE_OUTBOUND":
            assert c["class"].startswith("intent-only"), \
                "the inert flag must never be presented as a control"
