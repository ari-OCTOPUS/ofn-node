"""Bounded, read-only projections for the M1 owner cockpit.

The adapter deliberately knows only files and injected, zero-argument read
callbacks.  It never constructs a store, invokes a model, starts a process, or
writes state.  Input is reduced to small allowlisted metadata projections
before it can enter a response.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "2.0"
RESOURCES = ("status", "nodes", "legs", "queue", "audit", "version")
NODE_IDS = ("138", "180", "182")
LEG_IDS = (
    "DEMAND",
    "QUALIFICATION",
    "OFFER",
    "CONVERSION",
    "DELIVERY",
    "CASH",
    "RETENTION",
    "FINANCE",
)

HEARTBEAT_FRESHNESS_SECONDS = 180
TELEMETRY_FRESHNESS_SECONDS = 300
LEASE_FRESHNESS_SECONDS = 900

MAX_FILE_BYTES = 128 * 1024
MAX_JSONL_BYTES = 1024 * 1024
MAX_JSONL_LINE_BYTES = 64 * 1024
MAX_JSONL_LINES = 2_000
MAX_DIRECTORY_ENTRIES = 2_048
MAX_FILES = 2_048
MAX_ROWS = 2_000
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_WORK = 20_000
MAX_WARNINGS = 100
MAX_QUERY_BYTES = 2_048
MAX_QUERY_VALUE_BYTES = 1_024
MAX_SEARCH_CHARS = 80


class TruthState(str, Enum):
    LIVE_VERIFIED = "LIVE_VERIFIED"
    REPO_VERIFIED = "REPO_VERIFIED"
    DOCUMENTED = "DOCUMENTED"
    STALE = "STALE"
    HYPOTHESIS = "HYPOTHESIS"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


LIVE_VERIFIED = TruthState.LIVE_VERIFIED.value
REPO_VERIFIED = TruthState.REPO_VERIFIED.value
DOCUMENTED = TruthState.DOCUMENTED.value
STALE = TruthState.STALE.value
HYPOTHESIS = TruthState.HYPOTHESIS.value
CONTRADICTED = TruthState.CONTRADICTED.value
UNKNOWN = TruthState.UNKNOWN.value
TRUTH_STATES = tuple(state.value for state in TruthState)


_BAD_QUERY_CODES = frozenset(
    {
        "unknown_resource",
        "unknown_query",
        "duplicate_query",
        "malformed_query",
        "query_too_long",
        "invalid_cursor",
    }
)


class BadQuery(ValueError):
    """A safe, HTTP-400-equivalent query error.

    ``code`` is deliberately selected from a small fixed vocabulary.  The
    exception never includes the rejected value, cursor, path, or parser error.
    """

    status_code = 400

    def __init__(self, code: str = "malformed_query") -> None:
        if code not in _BAD_QUERY_CODES:
            code = "malformed_query"
        self.code = code
        super().__init__(code)


BadQueryError = BadQuery
QueryError = BadQuery


class _SourceProblem(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(status)


class _BudgetExceeded(Exception):
    pass


_STATUS_SEVERITY = {
    "ok": 0,
    "stale": 1,
    "truncated": 2,
    "missing": 3,
    "malformed": 4,
    "oversized": 5,
    "blocked": 6,
    "failed": 7,
}
_TRUTH_SEVERITY = {
    LIVE_VERIFIED: 0,
    REPO_VERIFIED: 1,
    DOCUMENTED: 2,
    HYPOTHESIS: 3,
    STALE: 4,
    CONTRADICTED: 5,
    UNKNOWN: 6,
}

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SAFE_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+/@:-]{0,127}$")
_HASH_RE = re.compile(r"^[0-9a-fA-F]{8,128}$")
_IPV4_RE = re.compile(
    r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])"
)
_EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")

_ALLOWED_ROOTS = frozenset(
    {
        "VERSION",
        "SESSION_BRIDGE_VERSION",
        "AGENT_RUNTIME_DISCOVERY.json",
        "OWNER_PAUSE",
        "config",
        "state",
        "inbox",
        "outbox",
        "processing",
        "processed",
        "rejected",
        "receipts",
        "audit",
        "calibration",
    }
)
_QUEUE_DIRECTORIES = ("inbox", "outbox", "processing", "processed", "rejected")
_QUEUE_STATES = frozenset(
    {
        "inbox",
        "outbox",
        "processing",
        "processed",
        "rejected",
        "pending",
        "queued",
        "claimed",
        "leased",
        "retryable",
        "failed",
        "completed",
        "completed_no_reply",
        "expired",
        "held",
        "sent",
    }
)
_QUEUE_PRECEDENCE = {
    "inbox": 1,
    "outbox": 2,
    "processing": 3,
    "processed": 4,
    "rejected": 5,
}
_AUDIT_CATEGORIES = frozenset(
    {"mesh_audit", "receipt", "incident", "calibration", "ofn_ledger"}
)

_NODE_ROLES = {
    "138": ("commander-router-ledger-owner", "command-reconciliation-execution"),
    "180": ("quality-brain", "cognitive-quality-proposal"),
    "182": ("lab-witness", "independent-witness"),
}

_LEG_METRICS = {
    "DEMAND": (
        ("inbound_count", "count"),
        ("open_lead_count", "count"),
    ),
    "QUALIFICATION": (("qualified_count", "count"),),
    "OFFER": (
        ("quote_count", "count"),
        ("quoted_amount_minor", "money"),
    ),
    "CONVERSION": (
        ("booking_count", "count"),
        ("booked_amount_minor", "money"),
        ("follow_ups_due", "count"),
    ),
    "DELIVERY": (("completed_count", "count"),),
    "CASH": (
        ("invoice_count", "count"),
        ("invoiced_amount_minor", "money"),
        ("verified_cash_minor", "verified_cash"),
    ),
    "RETENTION": (
        ("retained_count", "count"),
        ("complaint_count", "count"),
        ("opt_out_count", "count"),
    ),
    "FINANCE": (
        ("sale_count", "count"),
        ("sale_amount_minor", "money"),
        ("contribution_margin_minor", "verified_margin"),
    ),
}

_VERSION_FIELDS = frozenset(
    {
        "service",
        "version",
        "release",
        "revision",
        "commit",
        "build",
        "built_at",
        "branch",
    }
)

_CALLBACK_ALIASES = {
    "status": "status",
    "owner_status": "status",
    "metrics": "metrics",
    "owner_metrics": "metrics",
    "observability": "observability",
    "owner_observability": "observability",
    "core_snapshot": "core_snapshot",
    "owner_core_snapshot": "core_snapshot",
    "risks": "risks",
    "owner_risks": "risks",
    "ledger": "ledger",
    "ledger_summary": "ledger",
    "owner_ledger_summary": "ledger",
    "businesses": "businesses",
    "owner_businesses": "businesses",
    "workboard": "workboard",
    "owner_workboard": "workboard",
    "growth_workbench": "growth_workbench",
    "owner_growth_workbench": "growth_workbench",
    "telegram": "telegram",
    "owner_telegram_summary": "telegram",
    "legs": "legs",
    "money": "money",
    "owner_money": "money",
    "owner_queue_metadata": "owner_queue_metadata",
}

_QUERY_ALIASES = {
    "queue": {"status": "state", "type": "message_type", "q": "search"},
    "audit": {"type": "kind", "q": "search"},
}
_QUERY_FIELDS = {
    "status": frozenset(),
    "nodes": frozenset(),
    "legs": frozenset(),
    "version": frozenset(),
    "queue": frozenset(
        {
            "limit",
            "cursor",
            "state",
            "queue",
            "node",
            "message_type",
            "scope",
            "search",
            "status",
            "type",
            "q",
        }
    ),
    "audit": frozenset(
        {
            "limit",
            "cursor",
            "category",
            "kind",
            "status",
            "node",
            "source",
            "from",
            "to",
            "search",
            "type",
            "q",
        }
    ),
}

_CURSOR_DOMAIN = b"ofn.cockpit-v2.cursor.v1\x00"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_time(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    if value.microsecond:
        rendered = value.isoformat(timespec="microseconds")
        rendered = rendered.replace("+00:00", "Z")
        head, _, fraction = rendered.partition(".")
        fraction = fraction[:-1].rstrip("0")
        return head + ("." + fraction if fraction else "") + "Z"
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            return None
        try:
            result = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    elif isinstance(value, str):
        text = value.strip()
        if not text or len(text) > 64 or _CONTROL_RE.search(text):
            return None
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            result = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    try:
        return result.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        return None


def _timestamp(value: Any) -> str | None:
    parsed = _as_datetime(value)
    return _canonical_time(parsed) if parsed is not None else None


def _clock_value(clock: Callable[[], Any]) -> datetime:
    try:
        parsed = _as_datetime(clock())
    except Exception as exc:  # the message must not inherit callback details
        raise RuntimeError("cockpit clock unavailable") from exc
    if parsed is None:
        raise RuntimeError("cockpit clock unavailable")
    return parsed


def _safe_token(value: Any, *, maximum: int = 128) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text != value or not text or len(text) > maximum:
        return None
    if not _SAFE_TOKEN_RE.fullmatch(text):
        return None
    if ".." in text or _IPV4_RE.search(text) or _EMAIL_RE.search(text):
        return None
    return text


def _safe_version_value(value: Any) -> str | int | bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if -(10**12) <= value <= 10**12:
            return value
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text != value or not text or len(text) > 128:
        return None
    lowered = text.casefold()
    if (
        text.startswith(("/", "~", "\\"))
        or "\\" in text
        or "/home/" in lowered
        or "/root/" in lowered
        or ".ssh" in lowered
        or "private_key" in lowered
        or "identity_file" in lowered
        or _IPV4_RE.search(text)
        or _EMAIL_RE.search(text)
        or _CONTROL_RE.search(text)
    ):
        return None
    if not _SAFE_VERSION_RE.fullmatch(text):
        return None
    return text


def _safe_hash(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if not _HASH_RE.fullmatch(value):
        return None
    return value.lower()


def _integer(value: Any, *, minimum: int = 0, maximum: int = 10**15) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < minimum or value > maximum:
        return None
    return value


def _number(
    value: Any, *, minimum: float = -(10**15), maximum: float = 10**15
) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < minimum or numeric > maximum:
        return None
    return value


def _node_id(value: Any) -> str | None:
    text = str(value) if isinstance(value, int) and not isinstance(value, bool) else value
    return text if text in NODE_IDS else None


def _fact(value: Any = None, truth: str = UNKNOWN) -> dict[str, Any]:
    return {"value": value, "truth": truth}


def _money_fact(
    amount_minor: int | None = None,
    currency: str | None = None,
    truth: str = UNKNOWN,
) -> dict[str, Any]:
    return {"amount_minor": amount_minor, "currency": currency, "truth": truth}


def _metric(value: Any, unit: str, currency: str | None, truth: str) -> dict[str, Any]:
    return {"value": value, "unit": unit, "currency": currency, "truth": truth}


def _freshness(
    observed_at: str | None,
    now: datetime,
    seconds: int,
) -> tuple[str, str | None, int | None]:
    observed = _as_datetime(observed_at)
    if observed is None:
        return UNKNOWN, None, None
    expiry = observed + timedelta(seconds=seconds)
    if observed > now + timedelta(minutes=5):
        return CONTRADICTED, _canonical_time(expiry), None
    age = max(0, int((now - observed).total_seconds()))
    if now > expiry:
        return STALE, _canonical_time(expiry), age
    return LIVE_VERIFIED, _canonical_time(expiry), age


def _query_filter_digest(resource: str, normalized: Mapping[str, Any]) -> str:
    filters = {
        key: value
        for key, value in normalized.items()
        if key not in {"limit", "cursor"}
    }
    return _sha256(_canonical_json({"resource": resource, "filters": filters}))


def _encode_cursor(resource: str, filter_digest: str, key: Sequence[str]) -> str:
    payload = {
        "v": 1,
        "resource": resource,
        "filter": filter_digest,
        "key": list(key),
    }
    body = _canonical_json(payload)
    signature = hashlib.sha256(_CURSOR_DOMAIN + body).hexdigest()[:24]
    token = _canonical_json({"payload": payload, "signature": signature})
    return base64.urlsafe_b64encode(token).decode("ascii").rstrip("=")


def _decode_cursor(
    token: str,
    resource: str,
    filter_digest: str,
) -> tuple[str, ...]:
    if not isinstance(token, str) or not token or len(token) > MAX_QUERY_VALUE_BYTES:
        raise BadQuery("invalid_cursor")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
        raise BadQuery("invalid_cursor")
    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        if len(raw) > 768:
            raise ValueError
        wrapper = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise BadQuery("invalid_cursor") from None
    if not isinstance(wrapper, dict) or set(wrapper) != {"payload", "signature"}:
        raise BadQuery("invalid_cursor")
    payload = wrapper.get("payload")
    signature = wrapper.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        raise BadQuery("invalid_cursor")
    if set(payload) != {"v", "resource", "filter", "key"}:
        raise BadQuery("invalid_cursor")
    body = _canonical_json(payload)
    expected = hashlib.sha256(_CURSOR_DOMAIN + body).hexdigest()[:24]
    if not hmac.compare_digest(signature, expected):
        raise BadQuery("invalid_cursor")
    key = payload.get("key")
    if (
        payload.get("v") != 1
        or payload.get("resource") != resource
        or payload.get("filter") != filter_digest
        or not isinstance(key, list)
        or len(key) != 4
        or not all(isinstance(part, str) and len(part) <= 160 for part in key)
    ):
        raise BadQuery("invalid_cursor")
    return tuple(key)


def _single_query_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            raise BadQuery("duplicate_query")
        value = value[0]
    elif isinstance(value, (set, frozenset, dict)):
        raise BadQuery("malformed_query")
    if isinstance(value, bool) or value is None or isinstance(value, bytes):
        raise BadQuery("malformed_query")
    if isinstance(value, int):
        value = str(value)
    if not isinstance(value, str):
        raise BadQuery("malformed_query")
    if _CONTROL_RE.search(value):
        raise BadQuery("malformed_query")
    if len(value.encode("utf-8")) > MAX_QUERY_VALUE_BYTES:
        raise BadQuery("query_too_long")
    return value


def normalize_query(
    resource: str,
    query: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and canonicalize one resource query.

    List-valued entries (as returned by ``parse_qs``) are accepted only when
    they contain exactly one value.  Aliases normalize to one semantic key, so
    ``status=x&state=x`` is still rejected as a duplicate.
    """

    if resource not in RESOURCES:
        raise BadQuery("unknown_resource")
    if query is None:
        query = {}
    if not isinstance(query, Mapping):
        raise BadQuery("malformed_query")
    if len(query) > 16:
        raise BadQuery("query_too_long")

    allowed = _QUERY_FIELDS[resource]
    aliases = _QUERY_ALIASES.get(resource, {})
    out: dict[str, Any] = {}
    total_bytes = 0
    for raw_key, raw_value in query.items():
        if not isinstance(raw_key, str) or not raw_key or len(raw_key) > 64:
            raise BadQuery("malformed_query")
        if raw_key not in allowed:
            raise BadQuery("unknown_query")
        value = _single_query_value(raw_value)
        total_bytes += len(raw_key.encode("utf-8")) + len(value.encode("utf-8"))
        if total_bytes > MAX_QUERY_BYTES:
            raise BadQuery("query_too_long")
        key = aliases.get(raw_key, raw_key)
        if key in out:
            raise BadQuery("duplicate_query")
        out[key] = value

    if resource not in {"queue", "audit"}:
        if out:
            raise BadQuery("unknown_query")
        return {}

    limit_text = out.get("limit", "50")
    if not isinstance(limit_text, str) or not re.fullmatch(r"[0-9]{1,3}", limit_text):
        raise BadQuery("malformed_query")
    limit = int(limit_text)
    if not 1 <= limit <= 100:
        raise BadQuery("malformed_query")
    normalized: dict[str, Any] = {"limit": limit}

    cursor = out.get("cursor")
    if cursor is not None:
        if not cursor or len(cursor) > MAX_QUERY_VALUE_BYTES:
            raise BadQuery("invalid_cursor")
        normalized["cursor"] = cursor

    if resource == "queue":
        if "state" in out:
            state = out["state"].casefold()
            if state not in _QUEUE_STATES:
                raise BadQuery("malformed_query")
            normalized["state"] = state
        if "queue" in out:
            queue_name = out["queue"].casefold()
            if queue_name not in _QUEUE_DIRECTORIES:
                raise BadQuery("malformed_query")
            normalized["queue"] = queue_name
        if "node" in out:
            node = _node_id(out["node"])
            if node is None:
                raise BadQuery("malformed_query")
            normalized["node"] = node
        for key in ("message_type", "scope"):
            if key in out:
                token = _safe_token(out[key], maximum=64)
                if token is None:
                    raise BadQuery("malformed_query")
                normalized[key] = token
    else:
        if "category" in out:
            category = out["category"].casefold()
            if category not in _AUDIT_CATEGORIES:
                raise BadQuery("malformed_query")
            normalized["category"] = category
        for key in ("kind", "status", "source"):
            if key in out:
                token = _safe_token(out[key], maximum=64)
                if token is None:
                    raise BadQuery("malformed_query")
                normalized[key] = token
        if "node" in out:
            node = _node_id(out["node"])
            if node is None:
                raise BadQuery("malformed_query")
            normalized["node"] = node
        for key in ("from", "to"):
            if key in out:
                stamp = _timestamp(out[key])
                if stamp is None:
                    raise BadQuery("malformed_query")
                normalized[key] = stamp
        if "from" in normalized and "to" in normalized:
            if _as_datetime(normalized["from"]) > _as_datetime(normalized["to"]):
                raise BadQuery("malformed_query")

    if "search" in out:
        search = out["search"]
        if (
            not search
            or len(search) > MAX_SEARCH_CHARS
            or search != search.strip()
            or _CONTROL_RE.search(search)
        ):
            raise BadQuery("malformed_query")
        normalized["search"] = search
    return normalized


def semantic_etag(
    envelope: Mapping[str, Any],
    resource: str,
    normalized_query: Mapping[str, Any] | None = None,
) -> str:
    """Return a deterministic weak ETag for semantic response content.

    Request generation time is intentionally excluded.  Source observation
    times and ``stale_after`` remain because a changed observation or freshness
    boundary is meaningful response state.
    """

    if resource not in RESOURCES:
        raise BadQuery("unknown_resource")
    if not isinstance(envelope, Mapping):
        raise TypeError("envelope must be a mapping")
    semantic = {key: value for key, value in envelope.items() if key != "generated_at"}
    payload = {
        "resource": resource,
        "query": dict(normalized_query or {}),
        "envelope": semantic,
    }
    digest = _sha256(_canonical_json(payload))
    return f'W/"{digest}"'


class _Budget:
    def __init__(self) -> None:
        self.bytes = 0
        self.files = 0
        self.rows = 0
        self.work = 0

    def spend(
        self,
        *,
        bytes_count: int = 0,
        files: int = 0,
        rows: int = 0,
        work: int = 0,
    ) -> None:
        if min(bytes_count, files, rows, work) < 0:
            raise _BudgetExceeded
        self.bytes += bytes_count
        self.files += files
        self.rows += rows
        self.work += work
        if (
            self.bytes > MAX_TOTAL_BYTES
            or self.files > MAX_FILES
            or self.rows > MAX_ROWS
            or self.work > MAX_WORK
        ):
            raise _BudgetExceeded


class _Context:
    def __init__(self, now: datetime) -> None:
        self.now = now
        self.budget = _Budget()
        self.sources: dict[str, dict[str, Any]] = {}
        self.usable_sources: set[str] = set()
        self.warnings: set[str] = set()
        self.expiries: set[str] = set()
        self.callback_cache: dict[str, Any] = {}
        self.incomplete = False

    def warn(self, code: str) -> None:
        safe = _safe_token(code, maximum=128)
        if safe is not None and len(self.warnings) < MAX_WARNINGS:
            self.warnings.add(safe)

    def source(
        self,
        source_id: str,
        status: str,
        truth: str,
        observed_at: str | None = None,
        *,
        usable: bool = False,
    ) -> None:
        if source_id not in self.sources:
            self.sources[source_id] = {
                "id": source_id,
                "status": status,
                "truth": truth,
                "observed_at": observed_at,
            }
        else:
            current = self.sources[source_id]
            if _STATUS_SEVERITY.get(status, 99) > _STATUS_SEVERITY.get(
                current["status"], 99
            ):
                current["status"] = status
            if _TRUTH_SEVERITY.get(truth, 99) > _TRUTH_SEVERITY.get(
                current["truth"], 99
            ):
                current["truth"] = truth
            if current["observed_at"] is None and observed_at is not None:
                current["observed_at"] = observed_at
        if usable:
            self.usable_sources.add(source_id)
        if status != "ok":
            self.warn(f"{source_id}_{status}")
        if status in {"missing", "malformed", "oversized", "blocked", "failed", "truncated"}:
            self.incomplete = True

    def expiry(self, value: str | None) -> None:
        if value is not None:
            self.expiries.add(value)

    def envelope(self, data: Any, status: str) -> dict[str, Any]:
        stale_after = None
        if self.expiries:
            stale_after = min(self.expiries, key=lambda item: _as_datetime(item))
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _canonical_time(self.now),
            "status": status,
            "data": data,
            "sources": [self.sources[key] for key in sorted(self.sources)],
            "warnings": sorted(self.warnings),
            "stale_after": stale_after,
        }


class CockpitV2ReadModel:
    """Pure bounded read model for the M1 cockpit resources."""

    def __init__(
        self,
        clock: Callable[[], Any],
        mesh_root: Path,
        ofn_callbacks: Mapping[str, Callable[[], Any]] | None = None,
        version_metadata: Mapping[str, Any] | None = None,
        *,
        callbacks: Mapping[str, Callable[[], Any]] | None = None,
        version: Mapping[str, Any] | None = None,
    ) -> None:
        if not callable(clock):
            raise TypeError("clock must be callable")
        if not isinstance(mesh_root, Path):
            mesh_root = Path(mesh_root)
        if ofn_callbacks is not None and callbacks is not None:
            raise TypeError("callbacks supplied twice")
        if version_metadata is not None and version is not None:
            raise TypeError("version metadata supplied twice")
        supplied_callbacks = ofn_callbacks if ofn_callbacks is not None else callbacks
        supplied_version = version_metadata if version_metadata is not None else version
        if supplied_callbacks is None:
            supplied_callbacks = {}
        if supplied_version is None:
            supplied_version = {}
        if not isinstance(supplied_callbacks, Mapping):
            raise TypeError("ofn_callbacks must be a mapping")
        if not isinstance(supplied_version, Mapping):
            raise TypeError("version_metadata must be a mapping")

        normalized_callbacks: dict[str, Callable[[], Any]] = {}
        for name, callback in supplied_callbacks.items():
            canonical = _CALLBACK_ALIASES.get(name) if isinstance(name, str) else None
            if canonical is None or canonical in normalized_callbacks or not callable(callback):
                continue
            normalized_callbacks[canonical] = callback

        self._clock = clock
        self._mesh_root = mesh_root
        try:
            self._resolved_root = mesh_root.resolve(strict=False)
        except OSError:
            self._resolved_root = mesh_root.absolute()
        self._callbacks = normalized_callbacks
        self._version_metadata = dict(supplied_version)

    def __call__(
        self, resource: str, query: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        return self.read(resource, query)

    def normalize_query(
        self, resource: str, query: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        return normalize_query(resource, query)

    def read(
        self, resource: str, query: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        normalized = normalize_query(resource, query)
        now = _clock_value(self._clock)
        ctx = _Context(now)
        handler = {
            "status": self._read_status,
            "nodes": self._read_nodes,
            "legs": self._read_legs,
            "queue": self._read_queue,
            "audit": self._read_audit,
            "version": self._read_version,
        }[resource]
        return handler(ctx, normalized)

    # ---- bounded filesystem primitives ---------------------------------

    def _resolve(self, relative: str) -> Path:
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute()
            or not pure.parts
            or pure.parts[0] not in _ALLOWED_ROOTS
            or any(part in {"", ".", ".."} for part in pure.parts)
        ):
            raise _SourceProblem("blocked")
        candidate = self._resolved_root.joinpath(*pure.parts)
        try:
            resolved = candidate.resolve(strict=False)
            if os.path.commonpath((str(self._resolved_root), str(resolved))) != str(
                self._resolved_root
            ):
                raise _SourceProblem("blocked")
        except (OSError, ValueError):
            raise _SourceProblem("blocked") from None
        return resolved

    def _mesh_root_source(self, ctx: _Context) -> bool:
        try:
            if self._mesh_root.is_symlink():
                original = self._mesh_root.resolve(strict=False)
                if original != self._resolved_root:
                    raise _SourceProblem("blocked")
            if not self._resolved_root.exists():
                ctx.source("mesh_root", "missing", UNKNOWN)
                return False
            if not self._resolved_root.is_dir():
                ctx.source("mesh_root", "malformed", UNKNOWN)
                return False
        except OSError:
            ctx.source("mesh_root", "failed", UNKNOWN)
            return False
        ctx.source("mesh_root", "ok", LIVE_VERIFIED, usable=True)
        return True

    def _read_bytes_path(
        self,
        path: Path,
        ctx: _Context,
        source_id: str,
        *,
        maximum: int,
    ) -> bytes | None:
        try:
            resolved = path.resolve(strict=False)
            if os.path.commonpath((str(self._resolved_root), str(resolved))) != str(
                self._resolved_root
            ):
                raise _SourceProblem("blocked")
            stat = resolved.stat()
            if not resolved.is_file():
                raise _SourceProblem("malformed")
            if stat.st_size > maximum:
                raise _SourceProblem("oversized")
            ctx.budget.spend(files=1, work=1)
            with resolved.open("rb") as handle:
                raw = handle.read(maximum + 1)
            if len(raw) > maximum:
                raise _SourceProblem("oversized")
            ctx.budget.spend(bytes_count=len(raw))
            return raw
        except _BudgetExceeded:
            ctx.source(source_id, "truncated", UNKNOWN, usable=True)
            return None
        except _SourceProblem as problem:
            ctx.source(source_id, problem.status, UNKNOWN, usable=True)
            return None
        except (OSError, PermissionError):
            ctx.source(source_id, "failed", UNKNOWN, usable=True)
            return None

    def _load_json_path(
        self,
        path: Path,
        ctx: _Context,
        source_id: str,
        *,
        maximum: int = MAX_FILE_BYTES,
    ) -> tuple[Any | None, str | None]:
        raw = self._read_bytes_path(path, ctx, source_id, maximum=maximum)
        if raw is None:
            return None, None
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None, None
        ctx.source(source_id, "ok", REPO_VERIFIED, usable=True)
        return value, _sha256(raw)

    def _load_json(
        self,
        relative: str,
        ctx: _Context,
        source_id: str,
        *,
        required: bool,
        maximum: int = MAX_FILE_BYTES,
    ) -> tuple[Any | None, str | None]:
        try:
            path = self._resolve(relative)
            if not path.exists():
                if required:
                    ctx.source(source_id, "missing", UNKNOWN)
                return None, None
        except _SourceProblem as problem:
            ctx.source(source_id, problem.status, UNKNOWN)
            return None, None
        except OSError:
            ctx.source(source_id, "failed", UNKNOWN)
            return None, None
        return self._load_json_path(path, ctx, source_id, maximum=maximum)

    def _load_text(
        self,
        relative: str,
        ctx: _Context,
        source_id: str,
        *,
        required: bool,
    ) -> str | None:
        try:
            path = self._resolve(relative)
            if not path.exists():
                if required:
                    ctx.source(source_id, "missing", UNKNOWN)
                return None
        except _SourceProblem as problem:
            ctx.source(source_id, problem.status, UNKNOWN)
            return None
        except OSError:
            ctx.source(source_id, "failed", UNKNOWN)
            return None
        raw = self._read_bytes_path(path, ctx, source_id, maximum=4_096)
        if raw is None:
            return None
        try:
            text = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None
        safe = _safe_version_value(text)
        if not isinstance(safe, str):
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None
        ctx.source(source_id, "ok", REPO_VERIFIED, usable=True)
        return safe

    def _scan_directory(
        self,
        relative: str,
        ctx: _Context,
        source_id: str,
        *,
        required: bool = True,
    ) -> tuple[list[Path], bool]:
        try:
            directory = self._resolve(relative)
            if not directory.exists():
                if required:
                    ctx.source(source_id, "missing", UNKNOWN)
                return [], False
            if not directory.is_dir():
                ctx.source(source_id, "malformed", UNKNOWN)
                return [], False
            ctx.source(source_id, "ok", REPO_VERIFIED, usable=True)
            entries: list[Path] = []
            with os.scandir(directory) as iterator:
                for index, entry in enumerate(iterator):
                    ctx.budget.spend(work=1)
                    if index >= MAX_DIRECTORY_ENTRIES:
                        ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                        break
                    if entry.is_symlink():
                        ctx.source(source_id, "blocked", UNKNOWN, usable=True)
                        continue
                    try:
                        if entry.is_file(follow_symlinks=False):
                            entries.append(Path(entry.path))
                    except OSError:
                        ctx.source(source_id, "failed", UNKNOWN, usable=True)
            entries.sort(key=lambda item: item.name)
            return entries, True
        except _BudgetExceeded:
            ctx.source(source_id, "truncated", UNKNOWN, usable=True)
            return [], True
        except _SourceProblem as problem:
            ctx.source(source_id, problem.status, UNKNOWN)
            return [], False
        except (OSError, PermissionError):
            ctx.source(source_id, "failed", UNKNOWN)
            return [], False

    def _marker_state(self, ctx: _Context) -> tuple[bool | None, str]:
        parent_ok = False
        try:
            state_dir = self._resolve("state")
            parent_ok = state_dir.exists() and state_dir.is_dir()
        except (OSError, _SourceProblem):
            parent_ok = False
        for relative in ("state/OWNER_PAUSE", "OWNER_PAUSE"):
            try:
                path = self._resolve(relative)
                if path.exists():
                    if path.is_symlink() or not path.is_file():
                        ctx.source("mesh_pause_marker", "blocked", UNKNOWN)
                        return None, UNKNOWN
                    ctx.source(
                        "mesh_pause_marker", "ok", LIVE_VERIFIED, usable=True
                    )
                    return True, LIVE_VERIFIED
            except _SourceProblem as problem:
                ctx.source("mesh_pause_marker", problem.status, UNKNOWN)
                return None, UNKNOWN
            except OSError:
                ctx.source("mesh_pause_marker", "failed", UNKNOWN)
                return None, UNKNOWN
        if parent_ok:
            ctx.source("mesh_pause_marker", "ok", LIVE_VERIFIED, usable=True)
            return False, LIVE_VERIFIED
        ctx.source("mesh_pause_marker", "missing", UNKNOWN)
        return None, UNKNOWN

    # ---- injected callback primitive -----------------------------------

    def _callback(
        self,
        name: str,
        ctx: _Context,
        *,
        expected: bool,
    ) -> Any | None:
        if name in ctx.callback_cache:
            return ctx.callback_cache[name]
        callback = self._callbacks.get(name)
        source_id = f"ofn_{name}"
        if callback is None:
            if expected:
                ctx.source(source_id, "missing", UNKNOWN)
            ctx.callback_cache[name] = None
            return None
        try:
            value = callback()
        except Exception:
            ctx.source(source_id, "failed", UNKNOWN)
            ctx.callback_cache[name] = None
            return None
        if not isinstance(value, (Mapping, list, tuple)):
            ctx.source(source_id, "malformed", UNKNOWN)
            ctx.callback_cache[name] = None
            return None

        observed_at = None
        if isinstance(value, Mapping):
            for key in ("observed_at", "generated_at", "as_of"):
                if key in value:
                    observed_at = _timestamp(value.get(key))
                    break
        truth = LIVE_VERIFIED
        status = "ok"
        if observed_at is not None:
            truth, expiry, _ = _freshness(
                observed_at, ctx.now, TELEMETRY_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
            if truth == STALE:
                status = "stale"
            elif truth == CONTRADICTED:
                status = "malformed"
        ctx.source(source_id, status, truth, observed_at, usable=True)
        ctx.callback_cache[name] = value
        return value

    # ---- queue ----------------------------------------------------------

    @staticmethod
    def _filename_timestamp(name: str) -> str | None:
        prefix = name.split("__", 1)[0]
        prefix = prefix.replace("-", ":", 2) if "T" not in prefix else prefix
        return _timestamp(prefix)

    @staticmethod
    def _message_id_from_filename(name: str) -> str | None:
        base = name
        if base.endswith(".json"):
            base = base[:-5]
        if "__" in base:
            base = base.rsplit("__", 1)[1]
        return _safe_token(base, maximum=128)

    @staticmethod
    def _is_message_file(name: str) -> bool:
        lowered = name.casefold()
        return (
            lowered.endswith(".json")
            and not lowered.endswith(".state.json")
            and not lowered.startswith(".")
            and ".tmp" not in lowered
            and ".part" not in lowered
            and not lowered.endswith("~")
        )

    def _lease_map(self, ctx: _Context) -> tuple[dict[str, dict[str, Any]], bool]:
        files, readable = self._scan_directory(
            "receipts", ctx, "mesh_queue_leases", required=True
        )
        leases: dict[str, dict[str, Any]] = {}
        for path in files:
            if not path.name.endswith(".claim.json"):
                continue
            value, _ = self._load_json_path(path, ctx, "mesh_queue_leases")
            if not isinstance(value, Mapping):
                if value is not None:
                    ctx.source("mesh_queue_leases", "malformed", UNKNOWN, usable=True)
                continue
            message_id = _safe_token(value.get("message_id"), maximum=128)
            claimed_at = _timestamp(value.get("claimed_at"))
            expires_at = _timestamp(value.get("lease_expires_at"))
            status = _safe_token(value.get("status"), maximum=64)
            claimed_by = _node_id(value.get("claimed_by_node"))
            if message_id is None or claimed_at is None:
                ctx.source("mesh_queue_leases", "malformed", UNKNOWN, usable=True)
                continue
            if expires_at is None:
                claimed = _as_datetime(claimed_at)
                if claimed is not None:
                    expires_at = _canonical_time(
                        claimed + timedelta(seconds=LEASE_FRESHNESS_SECONDS)
                    )
            row = {
                "claimed_at": claimed_at,
                "lease_expires_at": expires_at,
                "status": status,
                "claimed_by_node": claimed_by,
            }
            previous = leases.get(message_id)
            if previous is None or (claimed_at, status or "") > (
                previous["claimed_at"],
                previous["status"] or "",
            ):
                leases[message_id] = row
        return leases, readable

    def _queue_state(
        self,
        base_path: Path,
        ctx: _Context,
        source_id: str,
    ) -> dict[str, Any] | None:
        companion = base_path.with_name(base_path.name + ".state.json")
        try:
            if not companion.exists():
                return None
        except OSError:
            ctx.source(source_id, "failed", UNKNOWN, usable=True)
            return None
        value, _ = self._load_json_path(companion, ctx, source_id)
        if not isinstance(value, Mapping):
            if value is not None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None
        state = _safe_token(value.get("status"), maximum=64)
        attempts = _integer(value.get("attempts"), maximum=1_000_000)
        updated_at = _timestamp(value.get("updated_at"))
        if state is None and attempts is None and updated_at is None:
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None
        return {"state": state, "attempts": attempts, "updated_at": updated_at}

    def _project_queue_row(
        self,
        value: Mapping[str, Any],
        path: Path,
        queue_name: str,
        ctx: _Context,
        source_id: str,
        leases: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any] | None:
        message_id = _safe_token(value.get("message_id"), maximum=128)
        if message_id is None:
            message_id = self._message_id_from_filename(path.name)
        if message_id is None:
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None
        created_at = _timestamp(value.get("created_at"))
        if created_at is None:
            created_at = self._filename_timestamp(path.name)
        expires_at = _timestamp(value.get("expires_at"))
        message_type = _safe_token(value.get("message_type"), maximum=64)
        scope = _safe_token(value.get("scope"), maximum=64)
        run_id = _safe_token(value.get("run_id"), maximum=128)
        sender = _node_id(value.get("sender_node"))
        recipient = _node_id(value.get("recipient_node"))
        state = queue_name
        attempts = None
        state_updated_at = None
        if queue_name == "outbox":
            companion = self._queue_state(path, ctx, source_id)
            if companion is not None:
                candidate_state = companion["state"]
                if candidate_state in _QUEUE_STATES:
                    state = candidate_state
                attempts = companion["attempts"]
                state_updated_at = companion["updated_at"]

        lease = leases.get(message_id)
        lease_expires_at = None
        lease_state = None
        truth = REPO_VERIFIED
        if lease is not None:
            lease_expires_at = lease.get("lease_expires_at")
            lease_dt = _as_datetime(lease_expires_at)
            if lease_dt is None:
                lease_state = "unknown"
                truth = UNKNOWN
            elif ctx.now > lease_dt:
                lease_state = "expired"
                truth = STALE
            else:
                lease_state = "active"
                ctx.expiry(lease_expires_at)
            if attempts is None and state in {"retryable", "failed"}:
                attempts = 1

        return {
            "id": message_id,
            "queue": queue_name,
            "state": state,
            "message_type": message_type,
            "scope": scope,
            "sender_node": sender,
            "recipient_node": recipient,
            "run_id": run_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "attempts": attempts,
            "state_updated_at": state_updated_at,
            "lease_expires_at": lease_expires_at,
            "lease_state": lease_state,
            "truth": truth,
        }

    @staticmethod
    def _queue_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
        return (
            row.get("created_at") or "",
            row.get("id") or "",
            row.get("queue") or "",
            row.get("state") or "",
        )

    def _collect_queue(
        self, ctx: _Context
    ) -> tuple[list[dict[str, Any]], bool, bool]:
        leases, leases_readable = self._lease_map(ctx)
        candidates: dict[str, dict[str, Any]] = {}
        readable_count = 0
        complete = leases_readable
        for queue_name in _QUEUE_DIRECTORIES:
            source_id = f"mesh_queue_{queue_name}"
            files, readable = self._scan_directory(
                queue_name, ctx, source_id, required=True
            )
            if readable:
                readable_count += 1
            else:
                complete = False
            for path in files:
                if not self._is_message_file(path.name):
                    continue
                value, _ = self._load_json_path(path, ctx, source_id)
                if not isinstance(value, Mapping):
                    if value is not None:
                        ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                    complete = False
                    continue
                row = self._project_queue_row(
                    value, path, queue_name, ctx, source_id, leases
                )
                if row is None:
                    complete = False
                    continue
                try:
                    ctx.budget.spend(rows=1, work=1)
                except _BudgetExceeded:
                    ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                    complete = False
                    break
                previous = candidates.get(row["id"])
                if previous is None:
                    candidates[row["id"]] = row
                else:
                    prior_choice = (
                        _QUEUE_PRECEDENCE.get(previous["queue"], 0),
                        self._queue_sort_key(previous),
                    )
                    new_choice = (
                        _QUEUE_PRECEDENCE.get(row["queue"], 0),
                        self._queue_sort_key(row),
                    )
                    if new_choice > prior_choice:
                        candidates[row["id"]] = row
        rows = sorted(candidates.values(), key=self._queue_sort_key, reverse=True)
        return rows, readable_count > 0, complete and not ctx.incomplete

    @staticmethod
    def _owner_queue_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
        return (row.get("created_at") or "", row.get("id") or "")

    @staticmethod
    def _project_owner_queue_row(
        value: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        native_id = _safe_token(value.get("native_id"), maximum=128)
        tenant = _safe_token(value.get("tenant"), maximum=64)
        idempotency_key = _safe_token(
            value.get("idempotency_key"), maximum=128
        )
        state = _safe_token(value.get("state"), maximum=64)
        risk = _safe_token(value.get("risk"), maximum=32)
        created_at = _timestamp(value.get("created_at"))

        if native_id is None or tenant is None:
            return None
        prefix = f"{tenant}:"
        if not native_id.startswith(prefix) or len(native_id) <= len(prefix):
            return None
        if (
            idempotency_key is not None
            and native_id != f"{tenant}:{idempotency_key}"
        ):
            return None

        truth = LIVE_VERIFIED
        if None in (idempotency_key, state, risk, created_at):
            truth = UNKNOWN
        return {
            "id": f"business:{native_id}",
            "source_kind": "business_outbox",
            "native_id": native_id,
            "idempotency_key": idempotency_key,
            "tenant": tenant,
            "state": state,
            "risk": risk,
            "created_at": created_at,
            "truth": truth,
        }

    def _collect_owner_queue(
        self, ctx: _Context
    ) -> tuple[list[dict[str, Any]] | None, bool]:
        value = self._callback(
            "owner_queue_metadata", ctx, expected=True
        )
        if value is None:
            return None, False
        source_id = "ofn_owner_queue_metadata"
        if not isinstance(value, (list, tuple)):
            ctx.source(source_id, "malformed", UNKNOWN, usable=True)
            return None, False

        candidates: dict[str, dict[str, Any]] = {}
        had_input = bool(value)
        for index, raw in enumerate(value):
            if index >= MAX_ROWS:
                ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                break
            try:
                ctx.budget.spend(rows=1, work=1)
            except _BudgetExceeded:
                ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                break
            if not isinstance(raw, Mapping):
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            row = self._project_owner_queue_row(raw)
            if row is None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            previous = candidates.get(row["native_id"])
            if previous is not None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                continue
            candidates[row["native_id"]] = row

        if had_input and not candidates:
            return None, False
        rows = sorted(
            candidates.values(), key=self._owner_queue_sort_key, reverse=True
        )
        return rows, True

    @staticmethod
    def _filter_queue(
        rows: Sequence[dict[str, Any]], normalized: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        result = []
        search = normalized.get("search")
        search_folded = search.casefold() if isinstance(search, str) else None
        for row in rows:
            if "state" in normalized and row["state"] != normalized["state"]:
                continue
            if "queue" in normalized and row["queue"] != normalized["queue"]:
                continue
            if "node" in normalized and normalized["node"] not in {
                row["sender_node"],
                row["recipient_node"],
            }:
                continue
            if (
                "message_type" in normalized
                and row["message_type"] != normalized["message_type"]
            ):
                continue
            if "scope" in normalized and row["scope"] != normalized["scope"]:
                continue
            if search_folded is not None:
                haystack = " ".join(
                    str(row[key])
                    for key in ("id", "state", "queue", "message_type", "scope", "run_id")
                    if row[key] is not None
                ).casefold()
                if search_folded not in haystack:
                    continue
            result.append(row)
        return result

    def _paginate(
        self,
        rows: Sequence[dict[str, Any]],
        resource: str,
        normalized: Mapping[str, Any],
        key_function: Callable[[Mapping[str, Any]], tuple[str, str, str, str]],
    ) -> tuple[list[dict[str, Any]], str | None]:
        filter_digest = _query_filter_digest(resource, normalized)
        cursor_key = None
        if "cursor" in normalized:
            cursor_key = _decode_cursor(
                normalized["cursor"], resource, filter_digest
            )
        eligible = rows
        if cursor_key is not None:
            eligible = [row for row in rows if key_function(row) < cursor_key]
        limit = normalized["limit"]
        page = list(eligible[:limit])
        next_cursor = None
        if len(eligible) > limit and page:
            next_cursor = _encode_cursor(
                resource, filter_digest, key_function(page[-1])
            )
        return page, next_cursor

    def _read_queue(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._mesh_root_source(ctx)
        rows, available, complete = self._collect_queue(ctx)
        owner_items, owner_available = self._collect_owner_queue(ctx)
        filtered = self._filter_queue(rows, normalized)
        page, next_cursor = self._paginate(
            filtered, "queue", normalized, self._queue_sort_key
        )
        total = len(filtered) if complete else None
        data = {
            "items": page,
            "owner_items": owner_items,
            "limit": normalized["limit"],
            "next_cursor": next_cursor,
            "total": total,
        }
        if not available and not owner_available:
            status = "unavailable"
        elif (
            ctx.warnings or not complete or not available or not owner_available
        ):
            status = "degraded"
        else:
            status = "ok"
        return ctx.envelope(data, status)

    # ---- nodes ----------------------------------------------------------

    @staticmethod
    def _empty_telemetry() -> dict[str, Any]:
        return {
            "cpu_percent": None,
            "memory_total_bytes": None,
            "memory_available_bytes": None,
            "disk_total_bytes": None,
            "disk_free_bytes": None,
            "temperature_c": None,
            "truth": UNKNOWN,
        }

    @staticmethod
    def _node_template(node: str) -> dict[str, Any]:
        role, semantic_role = _NODE_ROLES[node]
        return {
            "id": node,
            "role": role,
            "semantic_role": semantic_role,
            "may_authorize": False,
            "metadata_truth": DOCUMENTED,
            "state": _fact(None, UNKNOWN),
            "heartbeat": {
                "observed_at": None,
                "age_seconds": None,
                "truth": UNKNOWN,
            },
            "telemetry": CockpitV2ReadModel._empty_telemetry(),
            "queue_depth": _fact(None, UNKNOWN),
            "restart_count": _fact(None, UNKNOWN),
            "config_hash": _fact(None, UNKNOWN),
            "policy_hash": _fact(None, UNKNOWN),
        }

    def _apply_node_record(
        self,
        row: dict[str, Any],
        record: Mapping[str, Any],
        ctx: _Context,
        *,
        default_timestamp: Any = None,
    ) -> None:
        observed_at = None
        for key in ("heartbeat_at", "observed_at", "ts_iso", "timestamp", "ts"):
            if key in record:
                observed_at = _timestamp(record.get(key))
                if observed_at is not None:
                    break
        if observed_at is None:
            observed_at = _timestamp(default_timestamp)
        if observed_at is not None:
            truth, expiry, age = _freshness(
                observed_at, ctx.now, HEARTBEAT_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
            row["heartbeat"] = {
                "observed_at": observed_at,
                "age_seconds": age,
                "truth": truth,
            }
            if truth == LIVE_VERIFIED:
                row["state"] = _fact("live", LIVE_VERIFIED)
            elif truth == STALE:
                row["state"] = _fact("stale", STALE)
            elif truth == CONTRADICTED:
                row["state"] = _fact(None, CONTRADICTED)
        explicit_state = _safe_token(
            record.get("state", record.get("status")), maximum=32
        )
        if explicit_state is not None and row["heartbeat"]["truth"] == UNKNOWN:
            row["state"] = _fact(explicit_state.casefold(), REPO_VERIFIED)

        restart_count = _integer(record.get("restart_count"), maximum=10**9)
        if restart_count is not None:
            row["restart_count"] = _fact(restart_count, REPO_VERIFIED)
        queue_depth = _integer(record.get("queue_depth"), maximum=10**9)
        if queue_depth is not None:
            row["queue_depth"] = _fact(queue_depth, REPO_VERIFIED)
        for target, keys in (
            ("config_hash", ("config_hash", "config_sha256")),
            ("policy_hash", ("policy_hash", "policy_sha256")),
        ):
            for key in keys:
                digest = _safe_hash(record.get(key))
                if digest is not None:
                    row[target] = _fact(digest, REPO_VERIFIED)
                    break

        telemetry_source = record.get("telemetry")
        if not isinstance(telemetry_source, Mapping):
            telemetry_source = record
        telemetry_at = None
        for key in ("telemetry_at", "observed_at", "ts_iso", "timestamp"):
            if key in telemetry_source:
                telemetry_at = _timestamp(telemetry_source.get(key))
                if telemetry_at is not None:
                    break
        telemetry_truth = REPO_VERIFIED
        if telemetry_at is not None:
            telemetry_truth, expiry, _ = _freshness(
                telemetry_at, ctx.now, TELEMETRY_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
        telemetry = self._empty_telemetry()
        telemetry["cpu_percent"] = _number(
            telemetry_source.get("cpu_percent"), minimum=0, maximum=100
        )
        telemetry["memory_total_bytes"] = _integer(
            telemetry_source.get("memory_total_bytes", telemetry_source.get("mem_total_b"))
        )
        telemetry["memory_available_bytes"] = _integer(
            telemetry_source.get(
                "memory_available_bytes", telemetry_source.get("mem_available_b")
            )
        )
        telemetry["disk_total_bytes"] = _integer(
            telemetry_source.get("disk_total_bytes", telemetry_source.get("disk_total_b"))
        )
        telemetry["disk_free_bytes"] = _integer(
            telemetry_source.get("disk_free_bytes", telemetry_source.get("disk_free_b"))
        )
        telemetry["temperature_c"] = _number(
            telemetry_source.get(
                "temperature_c", telemetry_source.get("thermal_hottest_c")
            ),
            minimum=-100,
            maximum=250,
        )
        if any(telemetry[key] is not None for key in telemetry if key != "truth"):
            telemetry["truth"] = telemetry_truth
            row["telemetry"] = telemetry

    def _apply_local_metrics(
        self, row: dict[str, Any], metrics: Mapping[str, Any], ctx: _Context
    ) -> None:
        if metrics.get("ok") is False:
            ctx.warn("ofn_metrics_unavailable")
            return
        telemetry = self._empty_telemetry()
        mem = metrics.get("mem")
        if isinstance(mem, Mapping):
            total = _integer(mem.get("total_b"))
            available = _integer(mem.get("available_b"))
            if total is not None and total > 0 and available is not None and available <= total:
                telemetry["memory_total_bytes"] = total
                telemetry["memory_available_bytes"] = available
        disk = metrics.get("disk")
        if isinstance(disk, Mapping):
            total = _integer(disk.get("total_b"))
            free = _integer(disk.get("free_b"))
            if total is not None and total > 0 and free is not None and free <= total:
                telemetry["disk_total_bytes"] = total
                telemetry["disk_free_bytes"] = free
        temperature = _number(
            metrics.get("thermal_hottest_c"), minimum=-100, maximum=250
        )
        if temperature is not None:
            telemetry["temperature_c"] = temperature
        cpu = _number(metrics.get("cpu_percent"), minimum=0, maximum=100)
        if cpu is not None:
            telemetry["cpu_percent"] = cpu
        if any(telemetry[key] is not None for key in telemetry if key != "truth"):
            telemetry["truth"] = LIVE_VERIFIED
            row["telemetry"] = telemetry

    def _collect_nodes(
        self, ctx: _Context, *, include_queue: bool
    ) -> tuple[list[dict[str, Any]], bool]:
        rows = {node: self._node_template(node) for node in NODE_IDS}
        available = False

        nodes_config, _ = self._load_json(
            "config/nodes.json", ctx, "mesh_nodes_config", required=True
        )
        if isinstance(nodes_config, Mapping):
            configured = nodes_config.get("nodes")
            if isinstance(configured, Mapping):
                available = True
                for node in NODE_IDS:
                    raw = configured.get(node)
                    if not isinstance(raw, Mapping):
                        continue
                    role = _safe_token(raw.get("role"), maximum=64)
                    may_authorize = raw.get("may_authorize")
                    if role is not None:
                        rows[node]["role"] = role
                    if isinstance(may_authorize, bool):
                        rows[node]["may_authorize"] = may_authorize
                    safe_projection = {
                        "node_id": node,
                        "role": rows[node]["role"],
                        "may_authorize": rows[node]["may_authorize"],
                    }
                    rows[node]["config_hash"] = _fact(
                        _sha256(_canonical_json(safe_projection)), REPO_VERIFIED
                    )
                    rows[node]["metadata_truth"] = REPO_VERIFIED
            else:
                ctx.source("mesh_nodes_config", "malformed", UNKNOWN, usable=True)

        _, policy_digest = self._load_json(
            "config/autonomy_policy.json",
            ctx,
            "mesh_autonomy_policy",
            required=True,
        )
        if policy_digest is not None:
            available = True
            for row in rows.values():
                row["policy_hash"] = _fact(policy_digest, REPO_VERIFIED)

        consolidated, _ = self._load_json(
            "state/status/nodes.json",
            ctx,
            "mesh_node_status",
            required=False,
        )
        if isinstance(consolidated, Mapping):
            values = consolidated.get("nodes", consolidated)
            if isinstance(values, Mapping):
                available = True
                for node in NODE_IDS:
                    record = values.get(node)
                    if isinstance(record, Mapping):
                        self._apply_node_record(rows[node], record, ctx)

        heartbeat_files, heartbeat_readable = self._scan_directory(
            "state/heartbeats", ctx, "mesh_heartbeats", required=True
        )
        available = available or heartbeat_readable
        for path in heartbeat_files:
            value, _ = self._load_json_path(path, ctx, "mesh_heartbeats")
            if not isinstance(value, Mapping):
                if value is not None:
                    ctx.source("mesh_heartbeats", "malformed", UNKNOWN, usable=True)
                continue
            stem = path.name[:-5] if path.name.endswith(".json") else path.name
            node = _node_id(value.get("node_id"))
            if node is None:
                node = _node_id(stem.removeprefix("node-"))
            if node is None and value.get("worker") == "octopus-heartbeat":
                node = "138"
            if node is None:
                continue
            candidate_at = None
            for key in ("heartbeat_at", "observed_at", "ts_iso", "timestamp", "ts"):
                candidate_at = _timestamp(value.get(key))
                if candidate_at is not None:
                    break
            current_at = rows[node]["heartbeat"]["observed_at"]
            if current_at is None or (
                candidate_at is not None and candidate_at > current_at
            ):
                self._apply_node_record(rows[node], value, ctx)

        status_files, status_readable = self._scan_directory(
            "state/status", ctx, "mesh_node_metadata", required=True
        )
        available = available or status_readable
        for path in status_files:
            stem = path.name[:-5] if path.name.endswith(".json") else path.name
            node = _node_id(stem.removeprefix("node-"))
            if node is None:
                continue
            value, _ = self._load_json_path(path, ctx, "mesh_node_metadata")
            if isinstance(value, Mapping):
                self._apply_node_record(rows[node], value, ctx)
            elif value is not None:
                ctx.source("mesh_node_metadata", "malformed", UNKNOWN, usable=True)

        telemetry_files, telemetry_readable = self._scan_directory(
            "state/telemetry", ctx, "mesh_node_telemetry", required=False
        )
        available = available or telemetry_readable
        for path in telemetry_files:
            stem = path.name[:-5] if path.name.endswith(".json") else path.name
            value, _ = self._load_json_path(path, ctx, "mesh_node_telemetry")
            if not isinstance(value, Mapping):
                continue
            node = _node_id(value.get("node_id")) or _node_id(
                stem.removeprefix("node-")
            )
            if node is not None:
                self._apply_node_record(rows[node], {"telemetry": value}, ctx)

        metrics = self._callback("metrics", ctx, expected=True)
        if isinstance(metrics, Mapping):
            available = True
            self._apply_local_metrics(rows["138"], metrics, ctx)

        if include_queue:
            queue_rows, queue_available, queue_complete = self._collect_queue(ctx)
            available = available or queue_available
            if queue_available and queue_complete:
                counts = {node: 0 for node in NODE_IDS}
                for item in queue_rows:
                    node = item["recipient_node"]
                    if node in counts and item["state"] not in {"processed", "rejected", "completed", "completed_no_reply"}:
                        counts[node] += 1
                for node in NODE_IDS:
                    rows[node]["queue_depth"] = _fact(counts[node], LIVE_VERIFIED)

        return [rows[node] for node in NODE_IDS], available

    def _read_nodes(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        root_available = self._mesh_root_source(ctx)
        rows, available = self._collect_nodes(ctx, include_queue=True)
        live_complete = all(
            row["heartbeat"]["truth"] == LIVE_VERIFIED for row in rows
        )
        telemetry_complete = all(
            row["telemetry"]["truth"] == LIVE_VERIFIED for row in rows
        )
        if not root_available and not available:
            status = "unavailable"
        elif ctx.warnings or not live_complete or not telemetry_complete:
            status = "degraded"
        else:
            status = "ok"
        return ctx.envelope({"nodes": rows}, status)

    # ---- legs and money -------------------------------------------------

    @staticmethod
    def _leg_template(leg: str) -> dict[str, Any]:
        metrics = {
            name: _metric(
                None,
                "minor_currency" if kind != "count" else "count",
                None,
                UNKNOWN,
            )
            for name, kind in _LEG_METRICS[leg]
        }
        return {
            "id": leg,
            "health": _fact(None, UNKNOWN),
            "policy": {
                "active": None,
                "version": None,
                "hash": None,
                "truth": UNKNOWN,
            },
            "connector_count": _fact(None, UNKNOWN),
            "events_today": _fact(None, UNKNOWN),
            "blocker_count": _fact(None, UNKNOWN),
            "open_exceptions": _fact(None, UNKNOWN),
            "last_witness_at": _fact(None, UNKNOWN),
            "metrics": metrics,
        }

    @staticmethod
    def _currency(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        currency = value.strip().upper()
        if re.fullmatch(r"[A-Z]{3}", currency):
            return currency
        return None

    def _verified_money(
        self,
        container: Mapping[str, Any] | None,
        key: str,
        ctx: _Context,
        *,
        margin: bool,
    ) -> dict[str, Any]:
        if not isinstance(container, Mapping):
            return _money_fact()
        raw = container.get(key)
        if not isinstance(raw, Mapping):
            return _money_fact()
        amount = _integer(
            raw.get("amount_minor", raw.get("value_minor", raw.get("amount_cents"))),
            maximum=10**15,
        )
        currency = self._currency(raw.get("currency"))
        proof = raw.get("proof")
        proof_verified = isinstance(proof, Mapping) and proof.get("verified") is True
        proof_kind = (
            _safe_token(proof.get("kind"), maximum=64)
            if isinstance(proof, Mapping)
            else None
        )
        if margin:
            verified = raw.get("components_verified") is True or (
                proof_verified and proof_kind in {"margin_components", "finance_receipts"}
            )
        else:
            verified = raw.get("receipt_verified") is True or (
                proof_verified
                and proof_kind
                in {"payment_receipt", "settlement_receipt", "production_receipt"}
            )
        if amount is None or currency is None or not verified:
            return _money_fact()
        truth = LIVE_VERIFIED
        observed_at = _timestamp(raw.get("observed_at", raw.get("verified_at")))
        if observed_at is not None:
            truth, expiry, _ = _freshness(
                observed_at, ctx.now, TELEMETRY_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
        return _money_fact(amount, currency, truth)

    def _money(self, ctx: _Context) -> tuple[dict[str, Any], bool]:
        callback = self._callback("money", ctx, expected=True)
        if not isinstance(callback, Mapping):
            return {
                "verified_cash": _money_fact(),
                "contribution_margin": _money_fact(),
            }, False
        cash = self._verified_money(callback, "verified_cash", ctx, margin=False)
        margin = self._verified_money(
            callback, "contribution_margin", ctx, margin=True
        )
        return {"verified_cash": cash, "contribution_margin": margin}, True

    def _apply_leg_callback(
        self,
        row: dict[str, Any],
        value: Mapping[str, Any],
        ctx: _Context,
    ) -> None:
        observed_at = _timestamp(value.get("observed_at"))
        truth = LIVE_VERIFIED
        if observed_at is not None:
            truth, expiry, _ = _freshness(
                observed_at, ctx.now, TELEMETRY_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
        health = _safe_token(value.get("health"), maximum=32)
        if health is not None and health.casefold() in {
            "healthy",
            "degraded",
            "blocked",
            "paused",
            "unknown",
        }:
            row["health"] = _fact(health.casefold(), truth)
        for field in (
            "connector_count",
            "events_today",
            "blocker_count",
            "open_exceptions",
        ):
            number = _integer(value.get(field), maximum=10**9)
            if number is not None:
                row[field] = _fact(number, truth)
        witness = _timestamp(value.get("last_witness_at"))
        if witness is not None:
            witness_truth, expiry, _ = _freshness(
                witness, ctx.now, TELEMETRY_FRESHNESS_SECONDS
            )
            ctx.expiry(expiry)
            row["last_witness_at"] = _fact(witness, witness_truth)

        metrics_source = value.get("metrics")
        if not isinstance(metrics_source, Mapping):
            metrics_source = value
        kinds = dict(_LEG_METRICS[row["id"]])
        for name, kind in kinds.items():
            if kind in {"verified_cash", "verified_margin"}:
                continue
            raw = metrics_source.get(name)
            currency = None
            candidate = raw
            if isinstance(raw, Mapping):
                candidate = raw.get("value", raw.get("amount_minor"))
                currency = self._currency(raw.get("currency"))
            number = _integer(candidate, maximum=10**15)
            if number is None:
                continue
            if kind == "money" and currency is None:
                continue
            row["metrics"][name] = _metric(
                number,
                "count" if kind == "count" else "minor_currency",
                currency,
                truth,
            )

    def _leg_policies(
        self, rows: Mapping[str, dict[str, Any]], ctx: _Context
    ) -> bool:
        all_files: list[Path] = []
        any_readable = False
        for relative in ("config/legs", "config/policies"):
            files, readable = self._scan_directory(
                relative, ctx, "mesh_leg_policies", required=False
            )
            any_readable = any_readable or readable
            all_files.extend(files)
        if not any_readable:
            ctx.source("mesh_leg_policies", "missing", UNKNOWN)
            return False
        for path in all_files:
            if not path.name.casefold().endswith(".json"):
                continue
            stem = path.name[:-5].upper().replace("-", "_")
            value, digest = self._load_json_path(path, ctx, "mesh_leg_policies")
            if not isinstance(value, Mapping):
                continue
            leg = str(value.get("leg_id", stem)).upper().replace("-", "_")
            if leg not in rows:
                continue
            active = value.get("active") if isinstance(value.get("active"), bool) else None
            version = value.get("policy_version")
            if not isinstance(version, (str, int)) or isinstance(version, bool):
                version = None
            if isinstance(version, str):
                version = _safe_token(version, maximum=64)
            rows[leg]["policy"] = {
                "active": active,
                "version": version,
                "hash": digest,
                "truth": REPO_VERIFIED,
            }
        return True

    def _legacy_leg_aggregates(
        self, rows: Mapping[str, dict[str, Any]], ctx: _Context
    ) -> bool:
        used = False
        observability = self._callback("observability", ctx, expected=False)
        if isinstance(observability, Mapping):
            tenants = observability.get("tenants")
            if isinstance(tenants, Mapping):
                values = []
                valid = True
                for tenant in tenants.values():
                    if not isinstance(tenant, Mapping):
                        valid = False
                        break
                    count = _integer(tenant.get("inbox_processed"), maximum=10**9)
                    if count is None:
                        valid = False
                        break
                    values.append(count)
                if valid:
                    rows["DEMAND"]["metrics"]["inbound_count"] = _metric(
                        sum(values), "count", None, LIVE_VERIFIED
                    )
                    used = True
        workboard = self._callback("workboard", ctx, expected=False)
        if isinstance(workboard, Mapping):
            lead = workboard.get("lead")
            if isinstance(lead, Mapping):
                open_count = _integer(lead.get("open"), maximum=10**9)
                followups = _integer(lead.get("follow_ups_due"), maximum=10**9)
                if open_count is not None:
                    rows["DEMAND"]["metrics"]["open_lead_count"] = _metric(
                        open_count, "count", None, LIVE_VERIFIED
                    )
                    used = True
                if followups is not None:
                    rows["CONVERSION"]["metrics"]["follow_ups_due"] = _metric(
                        followups, "count", None, LIVE_VERIFIED
                    )
                    used = True
                # booked_revenue_cents is intentionally not copied to Cash.
        growth = self._callback("growth_workbench", ctx, expected=False)
        if isinstance(growth, Mapping):
            ziman = growth.get("ziman")
            if isinstance(ziman, Mapping):
                sold = _integer(ziman.get("sold"), maximum=10**9)
                if sold is not None:
                    rows["FINANCE"]["metrics"]["sale_count"] = _metric(
                        sold, "count", None, LIVE_VERIFIED
                    )
                    used = True
        return used

    def _read_legs(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        root_available = self._mesh_root_source(ctx)
        rows = {leg: self._leg_template(leg) for leg in LEG_IDS}
        policy_available = self._leg_policies(rows, ctx)
        callback = self._callback("legs", ctx, expected=True)
        callback_available = False
        if isinstance(callback, Mapping):
            values = callback.get("legs", callback)
            if isinstance(values, Mapping):
                iterable = values.items()
            elif isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
                iterable = []
                for entry in values:
                    if isinstance(entry, Mapping):
                        iterable.append((entry.get("id", entry.get("leg_id")), entry))
            else:
                iterable = []
            for raw_leg, value in iterable:
                leg = str(raw_leg).upper().replace("-", "_")
                if leg in rows and isinstance(value, Mapping):
                    self._apply_leg_callback(rows[leg], value, ctx)
                    callback_available = True
        legacy_available = self._legacy_leg_aggregates(rows, ctx)
        money, money_source_available = self._money(ctx)
        cash = money["verified_cash"]
        margin = money["contribution_margin"]
        if cash["amount_minor"] is not None:
            rows["CASH"]["metrics"]["verified_cash_minor"] = _metric(
                cash["amount_minor"], "minor_currency", cash["currency"], cash["truth"]
            )
        if margin["amount_minor"] is not None:
            rows["FINANCE"]["metrics"]["contribution_margin_minor"] = _metric(
                margin["amount_minor"],
                "minor_currency",
                margin["currency"],
                margin["truth"],
            )

        output = [rows[leg] for leg in LEG_IDS]
        facts_complete = all(
            row["health"]["truth"] != UNKNOWN and row["policy"]["truth"] != UNKNOWN
            for row in output
        )
        available = (
            root_available
            or policy_available
            or callback_available
            or legacy_available
            or money_source_available
        )
        if not available:
            status = "unavailable"
        elif ctx.warnings or not facts_complete:
            status = "degraded"
        else:
            status = "ok"
        return ctx.envelope({"legs": output}, status)

    # ---- audit ----------------------------------------------------------

    @staticmethod
    def _audit_id(projected: Mapping[str, Any]) -> str:
        return "event-" + _sha256(_canonical_json(projected))[:20]

    def _project_audit_mapping(
        self,
        value: Mapping[str, Any],
        category: str,
        truth: str,
    ) -> dict[str, Any] | None:
        if category == "mesh_audit":
            occurred_at = _timestamp(value.get("ts", value.get("created_at")))
            kind = _safe_token(value.get("type", value.get("event")), maximum=64)
            status = _safe_token(value.get("status"), maximum=64)
            source = "mesh"
            node = _node_id(value.get("sender", value.get("source")))
            event_id = _safe_token(value.get("message_id"), maximum=128)
            sequence = _integer(value.get("seq"), maximum=10**15)
            severity = None
        elif category == "receipt":
            occurred_at = _timestamp(
                value.get("claimed_at", value.get("created_at"))
            )
            kind = _safe_token(value.get("message_type"), maximum=64)
            if kind is None:
                kind = "lease_receipt" if "claimed_at" in value else "receipt"
            status = _safe_token(value.get("status"), maximum=64)
            source = "mesh"
            node = _node_id(
                value.get("claimed_by_node", value.get("sender_node"))
            )
            event_id = _safe_token(value.get("message_id"), maximum=128)
            sequence = None
            severity = None
        elif category == "incident":
            occurred_at = _timestamp(value.get("created_at"))
            kind = _safe_token(value.get("type"), maximum=64)
            resolved = value.get("resolved")
            status = "resolved" if resolved is True else "open" if resolved is False else None
            source = "mesh"
            node = _node_id(value.get("source"))
            event_id = _safe_token(value.get("incident_id"), maximum=128)
            sequence = None
            severity = _safe_token(value.get("severity"), maximum=32)
        elif category == "calibration":
            occurred_at = _timestamp(
                value.get("resolved_at", value.get("submitted_at"))
            )
            kind = _safe_token(value.get("kind"), maximum=64) or "calibration"
            if value.get("correction_needed") is True:
                status = "correction_needed"
            else:
                status = _safe_token(value.get("outcome"), maximum=64)
            source = "mesh"
            node = _node_id(value.get("agent"))
            event_id = _safe_token(
                value.get("cycle_id", value.get("task_id")), maximum=128
            )
            sequence = None
            severity = None
        else:
            occurred_at = _timestamp(value.get("ts", value.get("created_at")))
            kind = _safe_token(value.get("kind", value.get("type")), maximum=64)
            status = _safe_token(value.get("status"), maximum=64)
            source = "ofn"
            node = "138"
            event_id = _safe_token(value.get("id", value.get("event_id")), maximum=128)
            sequence = _integer(value.get("seq"), maximum=10**15)
            severity = None

        if kind is None and event_id is None and occurred_at is None and sequence is None:
            return None
        seed = {
            "category": category,
            "occurred_at": occurred_at,
            "kind": kind,
            "status": status,
            "source": source,
            "node_id": node,
            "sequence": sequence,
            "severity": severity,
        }
        if event_id is None:
            event_id = self._audit_id(seed)
        return {
            "id": event_id,
            "occurred_at": occurred_at,
            "category": category,
            "kind": kind,
            "status": status,
            "source": source,
            "node_id": node,
            "sequence": sequence,
            "severity": severity,
            "truth": truth,
        }

    def _read_jsonl(
        self,
        relative: str,
        ctx: _Context,
        source_id: str,
        category: str,
        *,
        required: bool,
    ) -> tuple[list[dict[str, Any]], list[int], bool, bool]:
        try:
            path = self._resolve(relative)
            if not path.exists():
                if required:
                    ctx.source(source_id, "missing", UNKNOWN)
                return [], [], False, False
            stat = path.stat()
            if not path.is_file():
                ctx.source(source_id, "malformed", UNKNOWN)
                return [], [], False, False
            if stat.st_size > MAX_JSONL_BYTES:
                ctx.source(source_id, "oversized", UNKNOWN)
                return [], [], False, False
            ctx.budget.spend(files=1, work=1)
            rows: list[dict[str, Any]] = []
            sequences: list[int] = []
            complete = True
            consumed = 0
            with path.open("rb") as handle:
                for index in range(MAX_JSONL_LINES + 1):
                    line = handle.readline(MAX_JSONL_LINE_BYTES + 1)
                    if not line:
                        break
                    consumed += len(line)
                    ctx.budget.spend(bytes_count=len(line), work=1)
                    if index >= MAX_JSONL_LINES:
                        ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                        complete = False
                        break
                    if len(line) > MAX_JSONL_LINE_BYTES and not line.endswith(b"\n"):
                        complete = False
                        ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                        while line and not line.endswith(b"\n"):
                            line = handle.readline(MAX_JSONL_LINE_BYTES + 1)
                            consumed += len(line)
                            ctx.budget.spend(bytes_count=len(line), work=1)
                        continue
                    if not line.strip():
                        continue
                    try:
                        value = json.loads(line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                        ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                        complete = False
                        continue
                    if not isinstance(value, Mapping):
                        ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                        complete = False
                        continue
                    projected = self._project_audit_mapping(
                        value, category, REPO_VERIFIED
                    )
                    if projected is None:
                        ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                        complete = False
                        continue
                    ctx.budget.spend(rows=1)
                    rows.append(projected)
                    if category == "mesh_audit" and projected["sequence"] is not None:
                        sequences.append(projected["sequence"])
            if consumed > MAX_JSONL_BYTES:
                ctx.source(source_id, "oversized", UNKNOWN, usable=True)
                complete = False
            ctx.source(source_id, "ok", REPO_VERIFIED, usable=True)
            return rows, sequences, True, complete
        except _BudgetExceeded:
            ctx.source(source_id, "truncated", UNKNOWN, usable=True)
            return [], [], True, False
        except _SourceProblem as problem:
            ctx.source(source_id, problem.status, UNKNOWN)
            return [], [], False, False
        except (OSError, PermissionError):
            ctx.source(source_id, "failed", UNKNOWN)
            return [], [], False, False

    def _audit_directory(
        self,
        relative: str,
        ctx: _Context,
        source_id: str,
        category: str,
        *,
        suffix: str = ".json",
    ) -> tuple[list[dict[str, Any]], bool, bool]:
        files, readable = self._scan_directory(
            relative, ctx, source_id, required=True
        )
        rows: list[dict[str, Any]] = []
        complete = readable
        for path in files:
            if not path.name.endswith(suffix):
                continue
            value, _ = self._load_json_path(path, ctx, source_id)
            if not isinstance(value, Mapping):
                if value is not None:
                    ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                complete = False
                continue
            row = self._project_audit_mapping(value, category, REPO_VERIFIED)
            if row is None:
                ctx.source(source_id, "malformed", UNKNOWN, usable=True)
                complete = False
                continue
            try:
                ctx.budget.spend(rows=1)
            except _BudgetExceeded:
                ctx.source(source_id, "truncated", UNKNOWN, usable=True)
                complete = False
                break
            rows.append(row)
        return rows, readable, complete

    def _calibration_rows(
        self, ctx: _Context
    ) -> tuple[list[dict[str, Any]], bool, bool]:
        files, readable = self._scan_directory(
            "calibration", ctx, "mesh_calibration", required=True
        )
        rows: list[dict[str, Any]] = []
        complete = readable
        for path in files:
            if path.name.endswith(".jsonl"):
                relative = f"calibration/{path.name}"
                part, _, part_readable, part_complete = self._read_jsonl(
                    relative,
                    ctx,
                    "mesh_calibration",
                    "calibration",
                    required=False,
                )
                rows.extend(part)
                readable = readable or part_readable
                complete = complete and part_complete
        return rows, readable, complete

    def _ofn_ledger(
        self, ctx: _Context
    ) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
        value = self._callback("ledger", ctx, expected=True)
        default_chain = {"verified": None, "event_count": None, "truth": UNKNOWN}
        if value is None:
            return [], default_chain, False
        rows: list[dict[str, Any]] = []
        chain = dict(default_chain)
        events: Any = value
        if isinstance(value, Mapping):
            verification = value.get("verification")
            verified = None
            if isinstance(verification, Mapping) and isinstance(
                verification.get("ok"), bool
            ):
                verified = verification["ok"]
            businesses = value.get("businesses")
            if verified is None and isinstance(businesses, Sequence):
                checks = []
                for business in businesses:
                    if not isinstance(business, Mapping):
                        continue
                    check = business.get("verification")
                    if isinstance(check, Mapping) and isinstance(check.get("ok"), bool):
                        checks.append(check["ok"])
                if checks:
                    verified = all(checks)
            count = _integer(value.get("event_count"), maximum=10**15)
            if verified is not None or count is not None:
                chain = {
                    "verified": verified,
                    "event_count": count,
                    "truth": LIVE_VERIFIED,
                }
            events = value.get("events", [])
        if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
            for event in events[:MAX_ROWS]:
                if not isinstance(event, Mapping):
                    ctx.source("ofn_ledger", "malformed", UNKNOWN, usable=True)
                    continue
                row = self._project_audit_mapping(
                    event, "ofn_ledger", LIVE_VERIFIED
                )
                if row is not None:
                    rows.append(row)
        return rows, chain, True

    @staticmethod
    def _sequence_summary(
        sequences: Sequence[int], *, readable: bool, complete: bool
    ) -> dict[str, Any]:
        if not readable:
            return {
                "first": None,
                "last": None,
                "contiguous": None,
                "gaps": None,
                "duplicates": None,
                "out_of_order": None,
                "records_checked": 0,
                "truth": UNKNOWN,
            }
        if not sequences:
            return {
                "first": None,
                "last": None,
                "contiguous": True if complete else None,
                "gaps": 0 if complete else None,
                "duplicates": 0 if complete else None,
                "out_of_order": 0 if complete else None,
                "records_checked": 0,
                "truth": REPO_VERIFIED if complete else UNKNOWN,
            }
        unique = sorted(set(sequences))
        duplicates = len(sequences) - len(unique)
        gaps = sum(max(0, right - left - 1) for left, right in zip(unique, unique[1:]))
        out_of_order = sum(
            1 for left, right in zip(sequences, sequences[1:]) if right <= left
        )
        return {
            "first": unique[0],
            "last": unique[-1],
            "contiguous": (
                duplicates == 0 and gaps == 0 and out_of_order == 0
                if complete
                else None
            ),
            "gaps": gaps,
            "duplicates": duplicates,
            "out_of_order": out_of_order,
            "records_checked": len(sequences),
            "truth": REPO_VERIFIED if complete else UNKNOWN,
        }

    @staticmethod
    def _audit_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
        return (
            row.get("occurred_at") or "",
            row.get("id") or "",
            row.get("category") or "",
            row.get("kind") or "",
        )

    @staticmethod
    def _filter_audit(
        rows: Sequence[dict[str, Any]], normalized: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        search = normalized.get("search")
        search_folded = search.casefold() if isinstance(search, str) else None
        lower = _as_datetime(normalized.get("from")) if "from" in normalized else None
        upper = _as_datetime(normalized.get("to")) if "to" in normalized else None
        for row in rows:
            if "category" in normalized and row["category"] != normalized["category"]:
                continue
            if "kind" in normalized and row["kind"] != normalized["kind"]:
                continue
            if "status" in normalized and row["status"] != normalized["status"]:
                continue
            if "node" in normalized and row["node_id"] != normalized["node"]:
                continue
            if "source" in normalized and row["source"] != normalized["source"]:
                continue
            occurred = _as_datetime(row["occurred_at"])
            if lower is not None and (occurred is None or occurred < lower):
                continue
            if upper is not None and (occurred is None or occurred > upper):
                continue
            if search_folded is not None:
                haystack = " ".join(
                    str(row[key])
                    for key in ("id", "category", "kind", "status", "source", "node_id")
                    if row[key] is not None
                ).casefold()
                if search_folded not in haystack:
                    continue
            result.append(row)
        return result

    def _read_audit(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        self._mesh_root_source(ctx)
        rows: list[dict[str, Any]] = []
        audit_rows, sequences, audit_readable, audit_complete = self._read_jsonl(
            "audit/audit.jsonl",
            ctx,
            "mesh_audit_log",
            "mesh_audit",
            required=True,
        )
        rows.extend(audit_rows)
        receipt_rows, receipts_readable, receipts_complete = self._audit_directory(
            "receipts", ctx, "mesh_receipts", "receipt"
        )
        rows.extend(receipt_rows)
        control_rows, control_readable, control_complete = self._audit_directory(
            "receipts/control", ctx, "mesh_control_receipts", "receipt"
        )
        rows.extend(control_rows)
        incident_rows, incidents_readable, incidents_complete = self._audit_directory(
            "state/incidents", ctx, "mesh_incidents", "incident"
        )
        rows.extend(incident_rows)
        calibration_rows, calibration_readable, calibration_complete = self._calibration_rows(
            ctx
        )
        rows.extend(calibration_rows)
        ledger_rows, hash_chain, ledger_available = self._ofn_ledger(ctx)
        rows.extend(ledger_rows)

        deduplicated: dict[tuple[str, str, str | None], dict[str, Any]] = {}
        for row in rows:
            key = (row["category"], row["id"], row["occurred_at"])
            deduplicated[key] = row
        ordered = sorted(
            deduplicated.values(), key=self._audit_sort_key, reverse=True
        )
        filtered = self._filter_audit(ordered, normalized)
        page, next_cursor = self._paginate(
            filtered, "audit", normalized, self._audit_sort_key
        )
        complete = all(
            (
                audit_complete,
                receipts_complete,
                control_complete,
                incidents_complete,
                calibration_complete,
            )
        ) and not ctx.incomplete
        any_available = any(
            (
                audit_readable,
                receipts_readable,
                control_readable,
                incidents_readable,
                calibration_readable,
                ledger_available,
            )
        )
        data = {
            "items": page,
            "limit": normalized["limit"],
            "next_cursor": next_cursor,
            "total": len(filtered) if complete else None,
            "sequence": self._sequence_summary(
                sequences, readable=audit_readable, complete=audit_complete
            ),
            "hash_chain": hash_chain,
        }
        if not any_available:
            status = "unavailable"
        elif ctx.warnings or not complete:
            status = "degraded"
        else:
            status = "ok"
        return ctx.envelope(data, status)

    # ---- status ---------------------------------------------------------

    def _incident_count(self, ctx: _Context) -> tuple[int | None, bool]:
        rows, readable, complete = self._audit_directory(
            "state/incidents", ctx, "mesh_incidents", "incident"
        )
        if not readable or not complete:
            return None, readable
        return sum(1 for row in rows if row["status"] == "open"), True

    def _approval_count(self, ctx: _Context) -> tuple[int | None, bool]:
        files, readable = self._scan_directory(
            "state/approvals", ctx, "mesh_approvals", required=True
        )
        if not readable:
            return None, False
        pending = 0
        complete = True
        for path in files:
            if not path.name.endswith(".json"):
                continue
            value, _ = self._load_json_path(path, ctx, "mesh_approvals")
            if not isinstance(value, Mapping):
                complete = False
                continue
            status = _safe_token(value.get("status"), maximum=64)
            settled = value.get("settled")
            expires_at = _as_datetime(value.get("expires_at"))
            if status in {"pending", "open", "requested"} or settled is False:
                if expires_at is None or expires_at >= ctx.now:
                    pending += 1
            elif status in {"approved", "denied", "expired", "settled"} or settled is True:
                continue
            else:
                # A command receipt is not silently called a pending approval.
                complete = False
        if not complete:
            ctx.warn("mesh_approvals_unclassified")
            return None, True
        return pending, True

    def _cycle_count(self, queue_rows: Sequence[Mapping[str, Any]], ctx: _Context) -> tuple[int | None, bool]:
        files, readable = self._scan_directory(
            "state/runs", ctx, "mesh_runs", required=True
        )
        run_ids = {
            row["run_id"]
            for row in queue_rows
            if row.get("run_id") is not None
            and row.get("state")
            not in {"processed", "rejected", "completed", "completed_no_reply"}
        }
        complete = readable
        for path in files:
            if not path.name.endswith(".json"):
                continue
            value, _ = self._load_json_path(path, ctx, "mesh_runs")
            if not isinstance(value, Mapping):
                complete = False
                continue
            status = _safe_token(value.get("status", value.get("state")), maximum=64)
            run_id = _safe_token(value.get("run_id"), maximum=128)
            if status in {"active", "running", "queued", "reconciling"} and run_id:
                run_ids.add(run_id)
        if not readable and not queue_rows:
            return None, False
        if not complete:
            return None, True
        return len(run_ids), True

    def _status_disk(self, metrics: Any, ctx: _Context) -> dict[str, Any]:
        unknown = {
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "truth": UNKNOWN,
        }
        if not isinstance(metrics, Mapping) or metrics.get("ok") is False:
            return unknown
        disk = metrics.get("disk")
        if not isinstance(disk, Mapping):
            return unknown
        total = _integer(disk.get("total_b"))
        used = _integer(disk.get("used_b"))
        free = _integer(disk.get("free_b"))
        if (
            total is None
            or total <= 0
            or used is None
            or free is None
            or used + free > total
        ):
            return unknown
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "truth": LIVE_VERIFIED,
        }

    def _read_status(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        root_available = self._mesh_root_source(ctx)
        mesh_version = self._load_text(
            "VERSION", ctx, "mesh_version_marker", required=True
        )
        latest, _ = self._load_json(
            "state/status/latest.json",
            ctx,
            "mesh_runtime_state",
            required=True,
        )
        latest_truth = UNKNOWN
        if isinstance(latest, Mapping):
            observed = _timestamp(latest.get("as_of", latest.get("observed_at")))
            if observed is not None:
                latest_truth, expiry, _ = _freshness(
                    observed, ctx.now, TELEMETRY_FRESHNESS_SECONDS
                )
                ctx.expiry(expiry)
                if latest_truth == STALE:
                    ctx.source(
                        "mesh_runtime_state", "stale", STALE, observed, usable=True
                    )
                elif latest_truth == CONTRADICTED:
                    ctx.source(
                        "mesh_runtime_state", "malformed", CONTRADICTED, observed, usable=True
                    )
            else:
                latest_truth = REPO_VERIFIED

        pause_value, pause_truth = self._marker_state(ctx)
        safe_hold_value = None
        safe_hold_truth = UNKNOWN
        telegram_mode = None
        telegram_truth = UNKNOWN
        policy_converged = None
        policy_truth = UNKNOWN
        explicit_mode = None
        explicit_mode_truth = UNKNOWN
        if isinstance(latest, Mapping):
            mode_candidate = _safe_token(
                latest.get("runtime_mode", latest.get("mode")), maximum=32
            )
            if mode_candidate is not None:
                explicit_mode = mode_candidate.upper()
                explicit_mode_truth = latest_truth
            budget = latest.get("budget")
            if isinstance(budget, Mapping):
                level = _safe_token(budget.get("level"), maximum=32)
                if level is not None:
                    safe_hold_value = level.upper() == "SAFE_HOLD"
                    safe_hold_truth = latest_truth
            policy = latest.get("policy")
            if isinstance(policy, Mapping) and isinstance(policy.get("converged"), bool):
                policy_converged = policy["converged"]
                policy_truth = latest_truth
            elif isinstance(latest.get("policy_converged"), bool):
                policy_converged = latest["policy_converged"]
                policy_truth = latest_truth

        telegram_config, _ = self._load_json(
            "config/telegram_policy.json",
            ctx,
            "mesh_telegram_policy",
            required=True,
        )
        if isinstance(telegram_config, Mapping):
            candidate = _safe_token(telegram_config.get("mode"), maximum=32)
            if candidate is not None:
                telegram_mode = candidate
                telegram_truth = REPO_VERIFIED
        telegram_callback = self._callback("telegram", ctx, expected=False)
        if isinstance(telegram_callback, Mapping):
            candidate = _safe_token(telegram_callback.get("mode"), maximum=32)
            if candidate is not None:
                telegram_mode = candidate
                telegram_truth = LIVE_VERIFIED

        status_callback = self._callback("status", ctx, expected=True)
        core_callback = self._callback("core_snapshot", ctx, expected=True)
        ofn_killed = None
        ofn_killed_truth = UNKNOWN
        for callback in (core_callback, status_callback):
            if not isinstance(callback, Mapping):
                continue
            if isinstance(callback.get("killed"), bool):
                ofn_killed = callback["killed"]
                ofn_killed_truth = LIVE_VERIFIED
            boot = callback.get("boot")
            if explicit_mode is None and isinstance(boot, Mapping):
                candidate = _safe_token(boot.get("mode"), maximum=32)
                if candidate is not None:
                    explicit_mode = candidate.upper()
                    explicit_mode_truth = LIVE_VERIFIED

        runtime_mode = explicit_mode
        runtime_truth = explicit_mode_truth
        if ofn_killed is True:
            if explicit_mode not in {None, "STOPPED", "KILLED"}:
                runtime_truth = CONTRADICTED
                ctx.warn("runtime_state_conflict")
            runtime_mode = "STOPPED"
            if runtime_truth != CONTRADICTED:
                runtime_truth = LIVE_VERIFIED
        elif pause_value is True:
            if explicit_mode not in {None, "PAUSED", "HOLD", "SAFE_HOLD"}:
                runtime_truth = CONTRADICTED
                ctx.warn("runtime_state_conflict")
            runtime_mode = "PAUSED"
            if runtime_truth != CONTRADICTED:
                runtime_truth = pause_truth
        elif safe_hold_value is True:
            runtime_mode = "SAFE_HOLD"
            runtime_truth = safe_hold_truth

        nodes, node_available = self._collect_nodes(ctx, include_queue=False)
        live = sum(1 for row in nodes if row["heartbeat"]["truth"] == LIVE_VERIFIED)
        stale = sum(1 for row in nodes if row["heartbeat"]["truth"] == STALE)
        unknown_nodes = 3 - live - stale
        heartbeat_source_available = any(
            row["heartbeat"]["truth"] != UNKNOWN for row in nodes
        )
        nodes_truth = LIVE_VERIFIED if heartbeat_source_available else UNKNOWN

        queue_rows, queue_available, queue_complete = self._collect_queue(ctx)
        queue_depth = None
        queue_truth = UNKNOWN
        if queue_available and queue_complete:
            queue_depth = sum(
                1
                for row in queue_rows
                if row["state"]
                not in {"processed", "rejected", "completed", "completed_no_reply"}
            )
            queue_truth = LIVE_VERIFIED
        cycle_count, cycle_available = self._cycle_count(queue_rows, ctx)
        incident_count, incident_available = self._incident_count(ctx)
        approval_count, approval_available = self._approval_count(ctx)

        metrics = self._callback("metrics", ctx, expected=True)
        disk = self._status_disk(metrics, ctx)
        money, money_available = self._money(ctx)

        data = {
            "runtime": {
                "mode": _fact(runtime_mode, runtime_truth),
                "mesh_version": _fact(
                    mesh_version, REPO_VERIFIED if mesh_version is not None else UNKNOWN
                ),
                "owner_pause": _fact(pause_value, pause_truth),
                "safe_hold": _fact(safe_hold_value, safe_hold_truth),
                "ofn_killed": _fact(ofn_killed, ofn_killed_truth),
                "telegram_mode": _fact(telegram_mode, telegram_truth),
            },
            "nodes": {
                "total": 3,
                "live": live if heartbeat_source_available else None,
                "stale": stale if heartbeat_source_available else None,
                "unknown": unknown_nodes,
                "truth": nodes_truth,
            },
            "work": {
                "queue_depth": _fact(queue_depth, queue_truth),
                "active_cycles": _fact(
                    cycle_count,
                    LIVE_VERIFIED if cycle_count is not None else UNKNOWN,
                ),
            },
            "governance": {
                "open_incidents": _fact(
                    incident_count,
                    LIVE_VERIFIED if incident_count is not None else UNKNOWN,
                ),
                "pending_approvals": _fact(
                    approval_count,
                    LIVE_VERIFIED if approval_count is not None else UNKNOWN,
                ),
                "policy_converged": _fact(policy_converged, policy_truth),
            },
            "disk": disk,
            "money": money,
        }
        critical_truths = (
            runtime_truth,
            nodes_truth,
            queue_truth,
            disk["truth"],
            money["verified_cash"]["truth"],
            money["contribution_margin"]["truth"],
        )
        available = any(
            (
                root_available,
                mesh_version is not None,
                isinstance(latest, Mapping),
                status_callback is not None,
                core_callback is not None,
                node_available,
                queue_available,
                cycle_available,
                incident_available,
                approval_available,
                metrics is not None,
                money_available,
            )
        )
        if not available:
            response_status = "unavailable"
        elif ctx.warnings or any(truth in {UNKNOWN, STALE, CONTRADICTED} for truth in critical_truths):
            response_status = "degraded"
        else:
            response_status = "ok"
        return ctx.envelope(data, response_status)

    # ---- version --------------------------------------------------------

    def _read_version(
        self, ctx: _Context, normalized: Mapping[str, Any]
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        filtered = False
        for key in sorted(self._version_metadata):
            if not isinstance(key, str) or key not in _VERSION_FIELDS:
                filtered = True
                continue
            value = self._version_metadata[key]
            if key == "built_at":
                safe: Any = _timestamp(value)
            elif key in {"commit", "revision"}:
                safe = _safe_hash(value) or _safe_version_value(value)
            else:
                safe = _safe_version_value(value)
            if safe is None:
                filtered = True
                continue
            metadata[key] = safe
        if filtered:
            ctx.warn("version_metadata_filtered")
        ctx.source("version_metadata", "ok", REPO_VERIFIED, usable=True)
        status = "degraded" if filtered else "ok"
        return ctx.envelope({"metadata": metadata}, status)


__all__ = [
    "BadQuery",
    "BadQueryError",
    "CockpitV2ReadModel",
    "CONTRADICTED",
    "DOCUMENTED",
    "HEARTBEAT_FRESHNESS_SECONDS",
    "HYPOTHESIS",
    "LEG_IDS",
    "LEASE_FRESHNESS_SECONDS",
    "LIVE_VERIFIED",
    "NODE_IDS",
    "QueryError",
    "REPO_VERIFIED",
    "RESOURCES",
    "SCHEMA_VERSION",
    "STALE",
    "TELEMETRY_FRESHNESS_SECONDS",
    "TRUTH_STATES",
    "TruthState",
    "UNKNOWN",
    "normalize_query",
    "semantic_etag",
]
