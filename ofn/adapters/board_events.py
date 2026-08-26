"""Version 1 of the durable, signed three-board event contract.

The transport is deliberately outside this module.  An event is a canonical
JSON envelope plus a signature supplied separately to :meth:`ingest`; this
adapter validates and persists inbound work but never sends anything.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Mapping, Sequence

from . import sqlite_base


CONTRACT_VERSION = 1
VERSION = CONTRACT_VERSION
BOARD_EVENT_VERSION = CONTRACT_VERSION
SIGNATURE_ALGORITHM = "HMAC-SHA256"

BOARDS = frozenset(("board-138", "board-180", "board-182"))
EVENT_TYPES = frozenset(
    (
        "LEAD_DISCOVERED",
        "MESSAGE_DRAFT_REQUESTED",
        "MESSAGE_DRAFT_READY",
        "ACK",
        "ERROR",
    )
)
BUSINESS_EVENT_TYPES = frozenset(
    ("LEAD_DISCOVERED", "MESSAGE_DRAFT_REQUESTED", "MESSAGE_DRAFT_READY")
)

RECEIVED = "received"
PROCESSED = "processed"
HELD = "held"
REJECTED = "rejected"
ACKED = "acked"
STATUSES = frozenset((RECEIVED, PROCESSED, HELD, REJECTED, ACKED))

MAX_EVENT_ID_LENGTH = 128
MAX_RUN_ID_LENGTH = 128
MAX_LEAD_ID_LENGTH = 128
MAX_TIMESTAMP_LENGTH = 40
MAX_PAYLOAD_BYTES = 64 * 1024
MAX_PAYLOAD_DEPTH = 32
MAX_ATTEMPTS = 3
MAX_NOTE_LENGTH = 512
MAX_PENDING_LIMIT = 1000
DEFAULT_PENDING_LIMIT = 50
DEFAULT_CLAIM_TIMEOUT_SECONDS = 300

ENVELOPE_FIELDS = (
    "event_id",
    "run_id",
    "source",
    "target",
    "type",
    "lead_id",
    "payload",
    "created_at",
    "expires_at",
    "attempt",
)
_ENVELOPE_FIELD_SET = frozenset(ENVELOPE_FIELDS)


class BoardEventError(ValueError):
    """Base class for event-contract failures."""


class BoardEventValidationError(BoardEventError):
    """The envelope is not a valid version-1 board event."""


class BoardEventExpiredError(BoardEventValidationError):
    """A structurally valid event is no longer fresh enough to ingest."""


class BoardEventSignatureError(BoardEventError):
    """The separately transported HMAC signature is invalid."""


class BoardEventStoreError(RuntimeError):
    """The durable store cannot perform the requested operation."""


# Four digits, a real calendar date, UTC only, and optional sub-second
# precision.  +00:00 is UTC too and is accepted by RFC 3339; other numeric
# offsets are valid RFC 3339 but not UTC and are intentionally rejected.
_RFC3339_UTC = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?P<fraction>\.\d{1,9})?(?P<zone>Z|\+00:00)$"
)


def _text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise BoardEventValidationError(f"{field} must be a string")
    if not value or not value.strip():
        raise BoardEventValidationError(f"{field} must not be empty")
    if value != value.strip():
        raise BoardEventValidationError(
            f"{field} must not have leading or trailing whitespace"
        )
    if len(value) > maximum:
        raise BoardEventValidationError(
            f"{field} exceeds the {maximum}-character limit"
        )
    if any(ord(char) < 0x20 for char in value):
        raise BoardEventValidationError(f"{field} contains a control character")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise BoardEventValidationError(f"{field} is not valid UTF-8 text") from exc
    return value


def _optional_lead_id(value: object, event_type: str) -> str | None:
    if value is None:
        if event_type in BUSINESS_EVENT_TYPES:
            raise BoardEventValidationError(
                f"lead_id is required for {event_type}"
            )
        return None
    return _text(value, "lead_id", MAX_LEAD_ID_LENGTH)


def _json_copy(value: object, *, depth: int = 0, items: list[int] | None = None) -> Any:
    """Return a JSON-only defensive copy, rejecting Python JSON extensions."""

    if items is None:
        items = [0]
    items[0] += 1
    if items[0] > MAX_PAYLOAD_BYTES:
        # A JSON value consumes at least one byte in canonical form.  This
        # early bound prevents enormous container graphs from consuming memory
        # before the exact encoded-byte check below.
        raise BoardEventValidationError(
            f"payload exceeds the {MAX_PAYLOAD_BYTES}-byte limit"
        )
    if depth > MAX_PAYLOAD_DEPTH:
        raise BoardEventValidationError(
            f"payload nesting exceeds {MAX_PAYLOAD_DEPTH} levels"
        )
    if value is None or isinstance(value, (str, bool)):
        return value
    # bool is an int subclass and was deliberately handled first.
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BoardEventValidationError("payload numbers must be finite")
        return value
    if isinstance(value, list):
        return [
            _json_copy(item, depth=depth + 1, items=items) for item in value
        ]
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise BoardEventValidationError("payload object keys must be strings")
            if key in copied:
                raise BoardEventValidationError("payload object keys must be unique")
            copied[key] = _json_copy(
                item, depth=depth + 1, items=items
            )
        return copied
    raise BoardEventValidationError(
        "payload values must use JSON object, array, string, number, boolean, or null"
    )


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise BoardEventValidationError("value is not canonical-JSON encodable") from exc


def _payload(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise BoardEventValidationError("payload must be a JSON object")
    copied = _json_copy(value)
    assert isinstance(copied, dict)  # Mapping above always copies to dict.
    size = len(_canonical_json(copied))
    if size > MAX_PAYLOAD_BYTES:
        raise BoardEventValidationError(
            f"payload exceeds the {MAX_PAYLOAD_BYTES}-byte limit"
        )
    return copied


def _parse_rfc3339_utc(value: object, field: str) -> tuple[str, str]:
    """Validate an RFC 3339 UTC value and return it plus a sortable UTC key."""

    if not isinstance(value, str):
        raise BoardEventValidationError(f"{field} must be a string")
    if not value or len(value) > MAX_TIMESTAMP_LENGTH:
        raise BoardEventValidationError(f"{field} is not an RFC3339 UTC timestamp")
    match = _RFC3339_UTC.fullmatch(value)
    if match is None:
        raise BoardEventValidationError(f"{field} is not an RFC3339 UTC timestamp")
    parts = match.groupdict()
    try:
        # datetime provides strict month/day/hour/minute/second validation and
        # intentionally rejects leap-second 60, which Python cannot represent.
        datetime(
            int(parts["year"]),
            int(parts["month"]),
            int(parts["day"]),
            int(parts["hour"]),
            int(parts["minute"]),
            int(parts["second"]),
            tzinfo=timezone.utc,
        )
    except ValueError as exc:
        raise BoardEventValidationError(
            f"{field} is not an RFC3339 UTC timestamp"
        ) from exc

    fraction = (parts["fraction"] or ".0")[1:].ljust(9, "0")
    # Every accepted input maps to the same fixed-width UTC representation.
    # That makes ordinary TEXT comparisons chronological, including values
    # whose original spellings used different fractional precision or +00:00.
    sort_key = (
        f"{parts['year']}-{parts['month']}-{parts['day']}T"
        f"{parts['hour']}:{parts['minute']}:{parts['second']}.{fraction}Z"
    )
    return value, sort_key


def _now_pair(value: object | None) -> tuple[str, str]:
    if callable(value):
        value = value()
    if value is None:
        value = datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise BoardEventValidationError("now must be timezone-aware UTC")
        if value.utcoffset().total_seconds() != 0:
            raise BoardEventValidationError("now must be UTC")
        utc = value.astimezone(timezone.utc)
        text = utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
        return _parse_rfc3339_utc(text, "now")
    return _parse_rfc3339_utc(value, "now")


def _secret_bytes(secret: object) -> bytes:
    if isinstance(secret, str):
        encoded = secret.encode("utf-8")
    elif isinstance(secret, bytes):
        encoded = secret
    else:
        raise BoardEventValidationError("HMAC secret must be nonempty text or bytes")
    if not encoded:
        raise BoardEventValidationError("HMAC secret must not be empty")
    return encoded


def _positive_int(value: object, field: str, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise BoardEventValidationError(f"{field} must be a positive integer")
    if maximum is not None and value > maximum:
        raise BoardEventValidationError(f"{field} must not exceed {maximum}")
    return value


def _note(value: object) -> str:
    if not isinstance(value, str):
        raise BoardEventValidationError("reason must be a string")
    if len(value) > MAX_NOTE_LENGTH:
        raise BoardEventValidationError(
            f"reason exceeds the {MAX_NOTE_LENGTH}-character limit"
        )
    if any(ord(char) < 0x20 and char not in "\t\n" for char in value):
        raise BoardEventValidationError("reason contains a control character")
    return value


@dataclass(frozen=True)
class BoardEvent:
    """The exact signed version-1 envelope.

    ``signature`` is deliberately not a field.  It is supplied separately to
    :meth:`BoardEventStore.ingest`, so an envelope cannot sign its own HMAC.
    """

    event_id: str
    run_id: str
    source: str
    target: str
    type: str
    lead_id: str | None
    payload: Mapping[str, Any]
    created_at: str
    expires_at: str
    attempt: int

    VERSION: ClassVar[int] = CONTRACT_VERSION
    FIELDS: ClassVar[tuple[str, ...]] = ENVELOPE_FIELDS

    def __post_init__(self) -> None:
        event_id = _text(self.event_id, "event_id", MAX_EVENT_ID_LENGTH)
        run_id = _text(self.run_id, "run_id", MAX_RUN_ID_LENGTH)
        if not isinstance(self.source, str) or self.source not in BOARDS:
            raise BoardEventValidationError("source is not an allowed board")
        if not isinstance(self.target, str) or self.target not in BOARDS:
            raise BoardEventValidationError("target is not an allowed board")
        if self.source == self.target:
            raise BoardEventValidationError("source and target must differ")
        if not isinstance(self.type, str) or self.type not in EVENT_TYPES:
            raise BoardEventValidationError("type is not allowed")
        lead_id = _optional_lead_id(self.lead_id, self.type)
        payload = _payload(self.payload)
        created_at, created_sort = _parse_rfc3339_utc(
            self.created_at, "created_at"
        )
        expires_at, expires_sort = _parse_rfc3339_utc(
            self.expires_at, "expires_at"
        )
        if expires_sort <= created_sort:
            raise BoardEventValidationError("expires_at must be after created_at")
        attempt = _positive_int(self.attempt, "attempt", MAX_ATTEMPTS)

        # Defensively detach mutable caller-owned payloads.  The dataclass is
        # frozen at its public boundary; as_dict() also returns a fresh copy.
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "lead_id", lead_id)
        object.__setattr__(self, "payload", payload)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "attempt", attempt)

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, object],
        *,
        now: object | None = None,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> "BoardEvent":
        """Strictly parse a complete envelope.

        Missing and extension fields both fail.  Pass an injected ``now`` to
        perform the freshness check; the store always does so at ingestion.
        Omitting ``now`` is useful when reading an already-persisted historical
        event, whose immutable envelope remains valid after its delivery TTL.
        """

        if not isinstance(mapping, Mapping):
            raise BoardEventValidationError("event envelope must be an object")
        raw_keys = tuple(mapping.keys())
        if not all(isinstance(key, str) for key in raw_keys):
            raise BoardEventValidationError("event field names must be strings")
        keys = frozenset(raw_keys)
        missing = sorted(_ENVELOPE_FIELD_SET - keys)
        extra = sorted(keys - _ENVELOPE_FIELD_SET)
        if missing or extra:
            details: list[str] = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("extra: " + ", ".join(extra))
            raise BoardEventValidationError("invalid event fields (" + "; ".join(details) + ")")

        configured_max = _positive_int(
            max_attempts, "max_attempts", MAX_ATTEMPTS
        )
        event = cls(**{field: mapping[field] for field in ENVELOPE_FIELDS})
        if event.attempt > configured_max:
            raise BoardEventValidationError(
                f"attempt must not exceed {configured_max}"
            )
        if now is not None:
            event._require_unexpired(now)
        return event

    def _sort_keys(self) -> tuple[str, str]:
        return (
            _parse_rfc3339_utc(self.created_at, "created_at")[1],
            _parse_rfc3339_utc(self.expires_at, "expires_at")[1],
        )

    def _require_unexpired(self, now: object) -> None:
        expires_sort = self._sort_keys()[1]
        now_sort = _now_pair(now)[1]
        # At the exact boundary the event has expired; there is no ambiguous
        # final instant at which two boards may process it differently.
        if expires_sort <= now_sort:
            raise BoardEventExpiredError("event has expired")

    def as_dict(self) -> dict[str, object]:
        """Return only the ten envelope fields, with a defensive payload copy."""

        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "lead_id": self.lead_id,
            "payload": _json_copy(self.payload),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "attempt": self.attempt,
        }

    def canonical_bytes(self) -> bytes:
        """UTF-8 canonical JSON used verbatim as the HMAC message."""

        return _canonical_json(self.as_dict())

    def sign(self, secret: str | bytes) -> str:
        """Return the lowercase hexadecimal HMAC-SHA256 signature."""

        return hmac.new(
            _secret_bytes(secret), self.canonical_bytes(), hashlib.sha256
        ).hexdigest()

    def verify(self, secret: str | bytes, signature: object) -> bool:
        """Constant-time comparison against a separately transported signature.

        The signature is a bare lowercase HMAC-SHA256 hex digest, carried
        outside the envelope.  A non-string, wrong-length, or non-hex value is
        rejected, but the ``compare_digest`` call still runs so a caller cannot
        distinguish "wrong shape" from "wrong secret" by timing.
        """

        expected = self.sign(secret)
        supplied = signature if isinstance(signature, str) else ""
        same = hmac.compare_digest(expected, supplied)
        return (
            same
            and len(supplied) == hashlib.sha256().digest_size * 2
            and all(char in "0123456789abcdef" for char in supplied)
        )


@dataclass(frozen=True)
class BoardEventRecord:
    """A persisted event plus lifecycle metadata (never a signing envelope)."""

    event: BoardEvent
    signature: str
    status: str
    claim_attempts: int
    claimed_at: str | None
    claim_token: str | None
    updated_at: str
    note: str
    ack_event_id: str | None = None

    @property
    def event_id(self) -> str:
        return self.event.event_id

    @property
    def run_id(self) -> str:
        return self.event.run_id

    @property
    def source(self) -> str:
        return self.event.source

    @property
    def target(self) -> str:
        return self.event.target

    @property
    def type(self) -> str:
        return self.event.type

    @property
    def lead_id(self) -> str | None:
        return self.event.lead_id

    @property
    def payload(self) -> Mapping[str, Any]:
        return self.event.payload

    @property
    def created_at(self) -> str:
        return self.event.created_at

    @property
    def expires_at(self) -> str:
        return self.event.expires_at

    @property
    def attempt(self) -> int:
        return self.event.attempt

    @property
    def effective_attempt(self) -> int:
        """Current signed attempt plus local processing attempts after the first."""

        return self.attempt + max(0, self.claim_attempts - 1)

    def as_dict(self) -> dict[str, object]:
        """Return the exact envelope, excluding signature and store metadata."""

        return self.event.as_dict()

    def canonical_bytes(self) -> bytes:
        return self.event.canonical_bytes()


StoredBoardEvent = BoardEventRecord


_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS board_events (
        event_id          TEXT PRIMARY KEY,
        contract_version  INTEGER NOT NULL,
        run_id            TEXT NOT NULL,
        source            TEXT NOT NULL,
        target            TEXT NOT NULL,
        type              TEXT NOT NULL,
        lead_id           TEXT,
        payload           TEXT NOT NULL,
        created_at        TEXT NOT NULL,
        expires_at        TEXT NOT NULL,
        attempt           INTEGER NOT NULL,
        signature         TEXT NOT NULL,
        status            TEXT NOT NULL,
        claim_attempts    INTEGER NOT NULL DEFAULT 0,
        claimed_at        TEXT NOT NULL DEFAULT '',
        claim_sort        TEXT NOT NULL DEFAULT '',
        claim_token       TEXT NOT NULL DEFAULT '',
        created_sort      TEXT NOT NULL,
        expires_sort      TEXT NOT NULL,
        updated_at        TEXT NOT NULL,
        note              TEXT NOT NULL DEFAULT '',
        ack_event_id      TEXT NOT NULL DEFAULT '',
        CHECK (contract_version = 1),
        CHECK (source IN ('board-138', 'board-180', 'board-182')),
        CHECK (target IN ('board-138', 'board-180', 'board-182')),
        CHECK (source <> target),
        CHECK (type IN ('LEAD_DISCOVERED', 'MESSAGE_DRAFT_REQUESTED',
                        'MESSAGE_DRAFT_READY', 'ACK', 'ERROR')),
        CHECK (type NOT IN ('LEAD_DISCOVERED', 'MESSAGE_DRAFT_REQUESTED',
                            'MESSAGE_DRAFT_READY') OR
               (lead_id IS NOT NULL AND length(lead_id) BETWEEN 1 AND 128)),
        CHECK (length(event_id) BETWEEN 1 AND 128),
        CHECK (length(run_id) BETWEEN 1 AND 128),
        CHECK (attempt BETWEEN 1 AND 3),
        CHECK (status IN ('received', 'processed', 'held', 'rejected', 'acked')),
        CHECK (claim_attempts >= 0),
        CHECK (expires_sort > created_sort),
        CHECK (length(signature) = 64)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS board_events_pending
        ON board_events (target, status, created_sort, event_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS board_events_stale_claims
        ON board_events (status, claim_sort)
    """,
)

_MISSING = object()


class BoardEventStore:
    """Durable inbox/state machine for signed three-board events.

    The caller supplies the SQLite path; no sibling database is invented.  The
    connection comes from :mod:`sqlite_base`, so WAL, ``synchronous=FULL``, the
    busy timeout, and foreign-key policy are applied to this existing file.
    Every mutation uses an explicit ``BEGIN IMMEDIATE`` transaction.
    """

    def __init__(
        self,
        path: str,
        secret: str | bytes | object = _MISSING,
        *,
        now: object | None = None,
        max_attempts: int = MAX_ATTEMPTS,
        claim_timeout_seconds: int = DEFAULT_CLAIM_TIMEOUT_SECONDS,
    ) -> None:
        self._path = str(path)
        self._secret: bytes | None = (
            None if secret is _MISSING else _secret_bytes(secret)
        )
        self.max_attempts = _positive_int(
            max_attempts, "max_attempts", MAX_ATTEMPTS
        )
        self.claim_timeout_seconds = _positive_int(
            claim_timeout_seconds, "claim_timeout_seconds"
        )
        self._clock = now
        self._lock = threading.RLock()
        self._closed = False
        self._conn = sqlite_base.connect(self._path)
        try:
            with self._transaction() as conn:
                for statement in _SCHEMA:
                    conn.execute(statement)
        except Exception:
            self._conn.close()
            self._closed = True
            raise

    def __enter__(self) -> "BoardEventStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._conn.close()
                self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise sqlite3.ProgrammingError("BoardEventStore is closed")

    class _Transaction:
        def __init__(self, store: "BoardEventStore") -> None:
            self.store = store

        def __enter__(self) -> sqlite3.Connection:
            self.store._lock.acquire()
            try:
                self.store._ensure_open()
                self.store._conn.execute("BEGIN IMMEDIATE")
            except Exception:
                self.store._lock.release()
                raise
            return self.store._conn

        def __exit__(self, exc_type, exc, traceback) -> bool:
            try:
                if exc_type is None:
                    self.store._conn.execute("COMMIT")
                else:
                    self.store._conn.execute("ROLLBACK")
            finally:
                self.store._lock.release()
            return False

    def _transaction(self) -> "BoardEventStore._Transaction":
        return self._Transaction(self)

    def _now(self, override: object = _MISSING) -> tuple[str, str]:
        source = self._clock if override is _MISSING else override
        return _now_pair(source)

    def _signing_secret(self, override: object = _MISSING) -> bytes:
        if override is not _MISSING:
            supplied = _secret_bytes(override)
            if self._secret is not None and not hmac.compare_digest(
                self._secret, supplied
            ):
                raise BoardEventValidationError(
                    "ingest secret does not match the configured secret"
                )
            return supplied
        if self._secret is None:
            raise BoardEventValidationError(
                "a nonempty HMAC secret is required for ingestion"
            )
        return self._secret

    @staticmethod
    def _validate_board(board: object, field: str = "target") -> str:
        if not isinstance(board, str) or board not in BOARDS:
            raise BoardEventValidationError(f"{field} is not an allowed board")
        return board

    @staticmethod
    def _limit(limit: object) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise BoardEventValidationError("limit must be an integer")
        if limit < 0:
            raise BoardEventValidationError("limit must not be negative")
        return min(limit, MAX_PENDING_LIMIT)

    def ingest(
        self,
        envelope: BoardEvent | Mapping[str, object],
        signature: object,
        *,
        secret: str | bytes | object = _MISSING,
        now: object = _MISSING,
    ) -> bool:
        """Verify and durably insert one event; return ``False`` on replay.

        Signature verification happens before the primary-key conflict check.
        Consequently, replaying an existing ID with a bad signature is still a
        signature failure, while any correctly signed same-ID envelope (same or
        different contents) is an idempotent ``False`` and never overwrites the
        first durable record.
        """

        now_text, now_sort = self._now(now)
        if isinstance(envelope, BoardEvent):
            # Reparse the public projection rather than trusting subclasses or
            # an instance mutated via object.__setattr__ after construction.
            # This keeps ingestion's strict boundary identical for object and
            # mapping callers.
            event = BoardEvent.from_mapping(
                envelope.as_dict(),
                now=now_text,
                max_attempts=self.max_attempts,
            )
        elif isinstance(envelope, Mapping):
            event = BoardEvent.from_mapping(
                envelope,
                now=now_text,
                max_attempts=self.max_attempts,
            )
        else:
            raise BoardEventValidationError("event envelope must be an object")

        signing_secret = self._signing_secret(secret)
        if not event.verify(signing_secret, signature):
            raise BoardEventSignatureError("invalid board event signature")
        if not isinstance(signature, str):  # verify accepted only canonical text.
            raise BoardEventSignatureError("invalid board event signature")
        created_sort, expires_sort = event._sort_keys()
        # Store the payload as canonical JSON too, but never the whole envelope
        # blob; exact fields remain queryable and schema constrained.
        payload_json = _canonical_json(event.payload).decode("utf-8")

        with self._transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO board_events
                    (event_id, contract_version, run_id, source, target, type,
                     lead_id, payload, created_at, expires_at, attempt,
                     signature, status, claim_attempts, claimed_at, claim_sort,
                     claim_token, created_sort, expires_sort, updated_at, note,
                     ack_event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, '', '', '',
                        ?, ?, ?, '', '')
                ON CONFLICT(event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    CONTRACT_VERSION,
                    event.run_id,
                    event.source,
                    event.target,
                    event.type,
                    event.lead_id,
                    payload_json,
                    event.created_at,
                    event.expires_at,
                    event.attempt,
                    signature,
                    RECEIVED,
                    created_sort,
                    expires_sort,
                    now_text,
                ),
            )
            return cursor.rowcount == 1

    def _reject_expired(
        self,
        conn: sqlite3.Connection,
        now_text: str,
        now_sort: str,
        *,
        target: str | None = None,
    ) -> int:
        # Claims are intentionally not auto-rejected here.  Once a consumer has
        # claimed work, recovery or an explicit transition must resolve it;
        # expiring the lease underneath that consumer would make a successful
        # mark_processed race the wall clock.
        sql = (
            "UPDATE board_events SET status = ?, claimed_at = '', claim_sort = '', "
            "claim_token = '', updated_at = ?, note = 'expired' "
            "WHERE status = ? AND claimed_at = '' AND expires_sort <= ?"
        )
        params: list[object] = [REJECTED, now_text, RECEIVED, now_sort]
        if target is not None:
            sql += " AND target = ?"
            params.append(target)
        return conn.execute(sql, params).rowcount

    def _hold_exhausted(
        self,
        conn: sqlite3.Connection,
        now_text: str,
        *,
        target: str | None = None,
    ) -> int:
        # An envelope at attempt N has (max-N+1) local claims available.  This
        # preserves the signed attempt field while making retry bounded.
        sql = (
            "UPDATE board_events SET status = ?, claimed_at = '', claim_sort = '', "
            "claim_token = '', updated_at = ?, note = 'retry limit reached' "
            "WHERE status = ? AND claimed_at = '' "
            "AND claim_attempts >= (? - attempt + 1)"
        )
        params: list[object] = [HELD, now_text, RECEIVED, self.max_attempts]
        if target is not None:
            sql += " AND target = ?"
            params.append(target)
        return conn.execute(sql, params).rowcount

    def claim(
        self,
        target: str | None = None,
        *,
        now: object = _MISSING,
    ) -> BoardEventRecord | None:
        """Atomically claim the oldest received event for ``target``.

        Claiming does not invent a sixth status: the row stays ``received`` and
        gains claim metadata.  A status can therefore only be one of the five
        public states while concurrent consumers are still excluded by the
        guarded update in this transaction.
        """

        if target is not None:
            target = self._validate_board(target)
        now_text, now_sort = self._now(now)
        token = secrets.token_hex(16)
        with self._transaction() as conn:
            self._reject_expired(conn, now_text, now_sort, target=target)
            self._hold_exhausted(conn, now_text, target=target)
            where = (
                "status = ? AND claimed_at = '' AND expires_sort > ? "
                "AND claim_attempts < (? - attempt + 1)"
            )
            params: list[object] = [RECEIVED, now_sort, self.max_attempts]
            if target is not None:
                where += " AND target = ?"
                params.append(target)
            row = conn.execute(
                "SELECT event_id FROM board_events WHERE "
                + where
                + " ORDER BY created_sort ASC, event_id ASC LIMIT 1",
                params,
            ).fetchone()
            if row is None:
                return None
            cursor = conn.execute(
                """
                UPDATE board_events
                   SET claim_attempts = claim_attempts + 1,
                       claimed_at = ?, claim_sort = ?, claim_token = ?,
                       updated_at = ?
                 WHERE event_id = ? AND status = ? AND claimed_at = ''
                       AND expires_sort > ?
                       AND claim_attempts < (? - attempt + 1)
                """,
                (
                    now_text,
                    now_sort,
                    token,
                    now_text,
                    row["event_id"],
                    RECEIVED,
                    now_sort,
                    self.max_attempts,
                ),
            )
            if cursor.rowcount != 1:  # Defensive; BEGIN IMMEDIATE prevents it.
                return None
            claimed = conn.execute(
                "SELECT * FROM board_events WHERE event_id = ?",
                (row["event_id"],),
            ).fetchone()
            return self._row_to_record(claimed)

    def mark_processed(
        self,
        event_id: str,
        *,
        claim_token: str | None = None,
        now: object = _MISSING,
    ) -> bool:
        """Move a currently claimed ``received`` event to ``processed``."""

        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        if claim_token is not None:
            claim_token = _text(claim_token, "claim_token", 128)
        now_text, _ = self._now(now)
        with self._transaction() as conn:
            sql = (
                "UPDATE board_events SET status = ?, claimed_at = '', "
                "claim_sort = '', claim_token = '', updated_at = ?, note = '' "
                "WHERE event_id = ? AND status = ? AND claimed_at <> ''"
            )
            params: list[object] = [PROCESSED, now_text, event_id, RECEIVED]
            if claim_token is not None:
                sql += " AND claim_token = ?"
                params.append(claim_token)
            return conn.execute(sql, params).rowcount == 1

    def hold(
        self,
        event_id: str,
        reason: str = "",
        *,
        now: object = _MISSING,
    ) -> bool:
        """Move ``received`` to ``held`` for an explicit human decision."""

        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        reason = _note(reason)
        now_text, _ = self._now(now)
        with self._transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE board_events
                   SET status = ?, claimed_at = '', claim_sort = '',
                       claim_token = '', updated_at = ?, note = ?
                 WHERE event_id = ? AND status = ?
                """,
                (HELD, now_text, reason, event_id, RECEIVED),
            )
            return cursor.rowcount == 1

    def reject(
        self,
        event_id: str,
        reason: str = "",
        *,
        now: object = _MISSING,
    ) -> bool:
        """Move ``received`` or ``held`` to terminal ``rejected``."""

        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        reason = _note(reason)
        now_text, _ = self._now(now)
        with self._transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE board_events
                   SET status = ?, claimed_at = '', claim_sort = '',
                       claim_token = '', updated_at = ?, note = ?
                 WHERE event_id = ? AND status IN (?, ?)
                """,
                (REJECTED, now_text, reason, event_id, RECEIVED, HELD),
            )
            return cursor.rowcount == 1

    def retry(
        self,
        event_id: str,
        *,
        now: object = _MISSING,
    ) -> bool:
        """Requeue a held event only while its bounded attempt budget remains."""

        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        now_text, now_sort = self._now(now)
        with self._transaction() as conn:
            # Expired held events are terminally rejected rather than requeued.
            expired = conn.execute(
                """
                UPDATE board_events
                   SET status = ?, updated_at = ?, note = 'expired',
                       claimed_at = '', claim_sort = '', claim_token = ''
                 WHERE event_id = ? AND status = ? AND expires_sort <= ?
                """,
                (REJECTED, now_text, event_id, HELD, now_sort),
            )
            if expired.rowcount:
                return False
            cursor = conn.execute(
                """
                UPDATE board_events
                   SET status = ?, updated_at = ?, note = '',
                       claimed_at = '', claim_sort = '', claim_token = ''
                 WHERE event_id = ? AND status = ? AND expires_sort > ?
                       AND claim_attempts < (? - attempt + 1)
                """,
                (
                    RECEIVED,
                    now_text,
                    event_id,
                    HELD,
                    now_sort,
                    self.max_attempts,
                ),
            )
            return cursor.rowcount == 1

    def ack(
        self,
        event_id: str,
        ack_event_id: str | None = None,
        *,
        now: object = _MISSING,
    ) -> bool:
        """Move ``processed`` to terminal ``acked``.

        An ACK is itself a normal, signed, persistable event type.  When
        ``ack_event_id`` is given it must already name a stored ACK row, and the
        association is recorded as lifecycle metadata; it never alters either
        signed envelope.  When omitted, the work item is simply acknowledged
        without a linked ACK record.
        """

        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        if ack_event_id is not None:
            ack_event_id = _text(
                ack_event_id, "ack_event_id", MAX_EVENT_ID_LENGTH
            )
        now_text, _ = self._now(now)
        with self._transaction() as conn:
            if ack_event_id is not None:
                ack_row = conn.execute(
                    "SELECT type FROM board_events WHERE event_id = ?",
                    (ack_event_id,),
                ).fetchone()
                if ack_row is None or ack_row["type"] != "ACK":
                    return False
            cursor = conn.execute(
                """
                UPDATE board_events
                   SET status = ?, updated_at = ?, ack_event_id = ?
                 WHERE event_id = ? AND status = ?
                """,
                (ACKED, now_text, ack_event_id or "", event_id, PROCESSED),
            )
            return cursor.rowcount == 1

    def recover_stale(
        self,
        *,
        timeout_seconds: int | None = None,
        now: object = _MISSING,
        target: str | None = None,
    ) -> int:
        """Recover claims left behind by a crash.

        A stale claim below the bounded attempt cap is made claimable again.
        At the cap it moves to ``held`` rather than looping forever.  No event
        is sent, acknowledged, or processed by recovery.
        """

        if timeout_seconds is None:
            timeout_seconds = self.claim_timeout_seconds
        timeout_seconds = _positive_int(timeout_seconds, "timeout_seconds")
        if target is not None:
            target = self._validate_board(target)
        now_text, now_sort = self._now(now)
        cutoff_sort = _subtract_seconds(now_sort, timeout_seconds)
        with self._transaction() as conn:
            self._reject_expired(conn, now_text, now_sort, target=target)
            expired_where = (
                "status = ? AND claimed_at <> '' AND claim_sort <= ? "
                "AND expires_sort <= ?"
            )
            expired_params: list[object] = [RECEIVED, cutoff_sort, now_sort]
            if target is not None:
                expired_where += " AND target = ?"
                expired_params.append(target)
            expired = conn.execute(
                "UPDATE board_events SET status = ?, claimed_at = '', "
                "claim_sort = '', claim_token = '', updated_at = ?, "
                "note = 'expired during stale claim' WHERE " + expired_where,
                [REJECTED, now_text, *expired_params],
            ).rowcount

            where = (
                "status = ? AND claimed_at <> '' AND claim_sort <= ? "
                "AND expires_sort > ?"
            )
            base_params: list[object] = [RECEIVED, cutoff_sort, now_sort]
            if target is not None:
                where += " AND target = ?"
                base_params.append(target)

            exhausted = conn.execute(
                "UPDATE board_events SET status = ?, claimed_at = '', "
                "claim_sort = '', claim_token = '', updated_at = ?, "
                "note = 'retry limit reached after stale claim' WHERE "
                + where
                + " AND claim_attempts >= (? - attempt + 1)",
                [HELD, now_text, *base_params, self.max_attempts],
            ).rowcount
            requeued = conn.execute(
                "UPDATE board_events SET claimed_at = '', claim_sort = '', "
                "claim_token = '', updated_at = ?, note = 'stale claim recovered' "
                "WHERE "
                + where
                + " AND claim_attempts < (? - attempt + 1)",
                [now_text, *base_params, self.max_attempts],
            ).rowcount
            return expired + exhausted + requeued

    # A short alias keeps the public claim/recover pair obvious while the full
    # name communicates that fresh claims are never touched.
    def recover(
        self,
        *,
        timeout_seconds: int | None = None,
        now: object = _MISSING,
        target: str | None = None,
    ) -> int:
        return self.recover_stale(
            timeout_seconds=timeout_seconds, now=now, target=target
        )

    def get(self, event_id: str) -> BoardEventRecord | None:
        event_id = _text(event_id, "event_id", MAX_EVENT_ID_LENGTH)
        with self._lock:
            self._ensure_open()
            row = self._conn.execute(
                "SELECT * FROM board_events WHERE event_id = ?", (event_id,)
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def pending(
        self,
        target: str | None = None,
        limit: int = DEFAULT_PENDING_LIMIT,
        *,
        now: object = _MISSING,
    ) -> Sequence[BoardEventRecord]:
        """Unclaimed received events, ordered by ``created_at,event_id``."""

        if target is not None:
            target = self._validate_board(target)
        limit = self._limit(limit)
        if limit == 0:
            return []
        now_text, now_sort = self._now(now)
        with self._transaction() as conn:
            self._reject_expired(conn, now_text, now_sort, target=target)
            self._hold_exhausted(conn, now_text, target=target)
            where = "status = ? AND claimed_at = '' AND expires_sort > ?"
            params: list[object] = [RECEIVED, now_sort]
            if target is not None:
                where += " AND target = ?"
                params.append(target)
            rows = conn.execute(
                "SELECT * FROM board_events WHERE "
                + where
                + " ORDER BY created_sort ASC, event_id ASC LIMIT ?",
                [*params, limit],
            ).fetchall()
            return [self._row_to_record(row) for row in rows]

    def counts(
        self,
        target: str | None = None,
        *,
        now: object = _MISSING,
    ) -> Mapping[str, int]:
        """Counts by public status; absent statuses are omitted."""

        if target is not None:
            target = self._validate_board(target)
        now_text, now_sort = self._now(now)
        with self._transaction() as conn:
            self._reject_expired(conn, now_text, now_sort, target=target)
            sql = "SELECT status, COUNT(*) AS n FROM board_events"
            params: list[object] = []
            if target is not None:
                sql += " WHERE target = ?"
                params.append(target)
            sql += " GROUP BY status"
            rows = conn.execute(sql, params).fetchall()
            return {row["status"]: int(row["n"]) for row in rows}

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> BoardEventRecord:
        payload = json.loads(row["payload"])
        event = BoardEvent.from_mapping(
            {
                "event_id": row["event_id"],
                "run_id": row["run_id"],
                "source": row["source"],
                "target": row["target"],
                "type": row["type"],
                "lead_id": row["lead_id"],
                "payload": payload,
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
                "attempt": int(row["attempt"]),
            }
        )
        return BoardEventRecord(
            event=event,
            signature=row["signature"],
            status=row["status"],
            claim_attempts=int(row["claim_attempts"]),
            claimed_at=row["claimed_at"] or None,
            claim_token=row["claim_token"] or None,
            updated_at=row["updated_at"],
            note=row["note"],
            ack_event_id=row["ack_event_id"] or None,
        )


def _subtract_seconds(sort_key: str, seconds: int) -> str:
    """Subtract whole seconds from this module's fixed-width UTC sort key."""

    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{9})Z", sort_key
    )
    if match is None:  # Internal invariant, kept loud if schema/code drifts.
        raise BoardEventStoreError("invalid internal claim timestamp")
    base = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    shifted = base - timedelta(seconds=seconds)
    return shifted.strftime("%Y-%m-%dT%H:%M:%S") + "." + match.group(2) + "Z"


__all__ = [
    "ACKED",
    "BOARD_EVENT_VERSION",
    "BOARDS",
    "BUSINESS_EVENT_TYPES",
    "BoardEvent",
    "BoardEventError",
    "BoardEventExpiredError",
    "BoardEventRecord",
    "BoardEventSignatureError",
    "BoardEventStore",
    "BoardEventStoreError",
    "BoardEventValidationError",
    "CONTRACT_VERSION",
    "ENVELOPE_FIELDS",
    "EVENT_TYPES",
    "HELD",
    "MAX_ATTEMPTS",
    "MAX_EVENT_ID_LENGTH",
    "MAX_LEAD_ID_LENGTH",
    "MAX_PAYLOAD_BYTES",
    "MAX_PAYLOAD_DEPTH",
    "MAX_RUN_ID_LENGTH",
    "PROCESSED",
    "RECEIVED",
    "REJECTED",
    "SIGNATURE_ALGORITHM",
    "STATUSES",
    "StoredBoardEvent",
    "VERSION",
]
