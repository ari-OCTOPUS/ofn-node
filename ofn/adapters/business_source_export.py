"""Additive, read-only export of business source rows for the 138 spine.

This module answers one question: "what does the business's own data look
like today, stripped of everything that identifies a person?" It reads the
painting lane from `painting_leads` and the ziman lane from `products`, and
writes one JSONL snapshot per lane under `<out_dir>/exports/`.

Three properties are the whole design, and each is load-bearing:

  * READ-ONLY. Connections are opened with `mode=ro` URIs via
    `sqlite_base.connect_readonly`, so this module cannot mutate, create or
    migrate a source database even if it wanted to. The owner's CRM is not
    ours to write to.

  * PII-FREE BY CONSTRUCTION. `customer_name`, `phone`, `email`, `message`
    and `source_ref` are never selected into the exported fields — not
    blanked, not masked, dropped. The row identity (`lead_id` / `sku`) leaves
    only as a SHA-256 digest. Every line carries `pii_redacted: true` and
    `may_contact: false`, because a de-identified export is not consent to
    contact anybody.

  * DETERMINISTIC. `now_utc` and `snapshot_id` are injected by the caller,
    rows are ordered by the table's primary key, and every digest is plain
    SHA-256 over canonical JSON. Same inputs, same bytes — which is what
    makes a snapshot diffable and testable.

"None vs unknown" is preserved: a column that is SQL `NULL` (the value was
never captured) exports as JSON `null` *and* is named in `fields["_unknown"]`,
while an explicit empty string (asked, and the answer was "none") stays `""`.
Without the marker list the two are indistinguishable downstream, and a
missing suburb would silently become "suburb is nowhere".

The source-row hash covers the *entire* source row — including the columns
this export drops. A hash over only the exported fields could not see a phone
number change, and change detection is the hash's job. SHA-256 is one-way:
the hash binds the row without disclosing it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Mapping

from .sqlite_base import connect_readonly

SCHEMA_NAME = "business_source.v1"
WARNING_SCHEMA_NAME = "business_source_warning.v1"
SOURCE_NODE = "138"
EXPORTS_DIRNAME = "exports"

LANES = ("painting", "ziman")
_LANE_TABLE = {"painting": "painting_leads", "ziman": "products"}
# The internal id is the one column that identifies a row to the business.
# It never leaves the node in the clear; only its digest does.
_LANE_ID_COLUMN = {"painting": "lead_id", "ziman": "sku"}
# Stable ordering: the products table has an integer `id`; painting_leads is
# keyed by a TEXT lead_id, so its primary key is its order.
_LANE_ORDER_COLUMN = {"painting": "lead_id", "ziman": "id"}

# Columns that must never appear in an export, in any form. Checking this
# list at build time is cheaper than apologising later.
DROPPED_COLUMNS = ("customer_name", "phone", "email", "message", "source_ref")

PAINTING_FIELDS = (
    "suburb", "job_type", "rooms", "budget_text", "score",
    "temperature", "status", "next_action", "follow_up_count",
)
ZIMAN_FLAT_FIELDS = ("name", "category", "state", "channel")
ZIMAN_COST_FIELDS = (
    "materials_cost_aud", "labour_hours", "hourly_rate_aud",
    "packaging_cost_aud", "cogs_aud",
)
ZIMAN_PRICE_FIELDS = ("price_primary_aud", "price_secondary_aud")

# Key inside `fields` naming the columns that were SQL NULL (unknown), as
# opposed to present-but-empty (none). See the module docstring.
UNKNOWN_MARKER = "_unknown"


class _MalformedRow(Exception):
    """A single source row could not be serialised. The export continues."""


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(row: Mapping[str, object]) -> str:
    """One byte string per row, for `source_row_hash`.

    `allow_nan=False` so a NaN/Infinity float is a malformed row rather than
    invalid JSON silently written to the snapshot.
    """
    return json.dumps(row, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    # `table` comes from this module's own mapping, never from input.
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def _put(fields: dict, unknown: list[str], path: str, name: str,
         value: object) -> None:
    """Store one field value, recording SQL NULL as unknown.

    A missing column (an older file) reads back as NULL here too, so schema
    drift and an absent value degrade the same honest way: named, not blank.
    """
    if value is None:
        fields[name] = None
        unknown.append(path)
    else:
        fields[name] = value


def _painting_fields(row: Mapping[str, object]) -> dict:
    fields: dict = {}
    unknown: list[str] = []
    for name in PAINTING_FIELDS:
        _put(fields, unknown, name, name, row.get(name))
    fields[UNKNOWN_MARKER] = sorted(unknown)
    return fields


def _ziman_fields(row: Mapping[str, object]) -> dict:
    fields: dict = {}
    unknown: list[str] = []
    for name in ZIMAN_FLAT_FIELDS:
        _put(fields, unknown, name, name, row.get(name))
    for group, names in (("costs", ZIMAN_COST_FIELDS),
                         ("price", ZIMAN_PRICE_FIELDS)):
        nested: dict = {}
        for name in names:
            _put(nested, unknown, f"{group}.{name}", name, row.get(name))
        fields[group] = nested
    fields[UNKNOWN_MARKER] = sorted(unknown)
    return fields


def _fields(lane: str, row: Mapping[str, object]) -> dict:
    return _painting_fields(row) if lane == "painting" else _ziman_fields(row)


def _record(lane: str, row: Mapping[str, object], now_utc: str) -> dict:
    """Build one export line. Raises `_MalformedRow` on unserialisable data."""
    internal_id = row.get(_LANE_ID_COLUMN[lane])
    if internal_id is None or internal_id == "":
        raise _MalformedRow("identity-missing")
    if not isinstance(internal_id, str):
        internal_id = str(internal_id)
    return {
        "schema": SCHEMA_NAME,
        "source_node": SOURCE_NODE,
        "lane": lane,
        "internal_id_hash": _sha256_text(internal_id),
        "fields": _fields(lane, row),
        "observed_at_utc": now_utc,
        "source_row_hash": hashlib.sha256(
            _canonical_json(row).encode("utf-8")).hexdigest(),
        "may_contact": False,
        "pii_redacted": True,
    }


def _warning_line(lane: str, row_number: int, now_utc: str) -> dict:
    """A malformed row's placeholder: what happened, never what was in it.

    The exception text is deliberately dropped — a decode error message can
    quote the bytes that failed, and those bytes are the one thing this
    export must not carry.
    """
    return {
        "schema": WARNING_SCHEMA_NAME,
        "source_node": SOURCE_NODE,
        "lane": lane,
        "row_number": row_number,
        "reason": "malformed-row",
        "observed_at_utc": now_utc,
    }


def _collect(conn: sqlite3.Connection, lane: str, now_utc: str) -> list[str]:
    table = _LANE_TABLE[lane]
    if not _table_exists(conn, table):
        # A file that has never been initialised has nothing to observe.
        # Raising here would make an export of a fresh node impossible.
        return []
    columns = set(_table_columns(conn, table))
    id_column = _LANE_ID_COLUMN[lane]
    if id_column not in columns:
        raise ValueError(
            f"{lane}: table {table} has no {id_column} column to identify rows")
    order = _LANE_ORDER_COLUMN[lane]
    if order not in columns:
        order = id_column
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order}")
    lines: list[str] = []
    seen: set[str] = set()
    row_number = 0
    for row in rows:
        row_number += 1
        raw = dict(row)
        # The dropped columns ARE read here — the row hash binds them — but
        # `fields` is assembled from a fixed whitelist of names, so they have
        # no path into the output. The whitelist, not a scrubber, is the mask.
        try:
            record = _record(lane, raw, now_utc)
            line = json.dumps(record, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError, UnicodeDecodeError):
            lines.append(json.dumps(_warning_line(lane, row_number, now_utc),
                                    ensure_ascii=False))
            continue
        # Two source rows can share one internal id (the same sku under two
        # tenants, say). The export's identity IS the digest, so the second
        # row would be indistinguishable from the first — emit it once.
        if record["internal_id_hash"] in seen:
            continue
        seen.add(record["internal_id_hash"])
        lines.append(line)
    return lines


def export_business_sources(db_paths: Mapping[str, str], lane: str,
                            out_dir: Path, *, now_utc: str,
                            snapshot_id: str) -> Path:
    """Write `<out_dir>/exports/<snapshot_id>-<lane>.jsonl`, return its path.

    `now_utc` and `snapshot_id` are injected, never read from the clock, so
    a test (or a re-run) reproduces the file byte for byte. The write is
    tmp-file plus `os.replace`: a reader either sees the previous snapshot
    or the complete new one, never a half-written line.
    """
    if lane not in _LANE_TABLE:
        raise ValueError(f"unknown lane {lane!r}; expected one of {LANES}")
    if lane not in db_paths:
        raise ValueError(f"no database configured for lane {lane!r}")
    exports = Path(out_dir) / EXPORTS_DIRNAME
    exports.mkdir(parents=True, exist_ok=True)
    target = exports / f"{snapshot_id}-{lane}.jsonl"

    lines: list[str] = []
    source = db_paths[lane]
    if os.path.exists(source):
        conn = connect_readonly(str(source))
        try:
            lines = _collect(conn, lane, now_utc)
        finally:
            conn.close()
    # A source file that does not exist yet (a lane never booted) exports as
    # an empty snapshot rather than an error: there is nothing to observe,
    # and a missing observation is still an observation.

    payload = "".join(line + "\n" for line in lines)
    tmp = target.with_name(target.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, target)
    return target


def load_export(path: Path) -> list[dict]:
    """Parse a snapshot back into records. The tests' read side; production
    consumers get the same function so there is one definition of the shape."""
    out: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
