"""Offline OCTOPUS evolution-island evidence, outside Core.

This module is stdlib-only: it has no network, subprocess, dynamic execution,
live integration, or deployment path. Passing technical lab checks NEVER
authorizes deployment. It offers evidence recording and proposals, not control.

Receipts form an UNSIGNED, LOCAL, single-writer hash chain. They do not prove
identity, external nonrepudiation, independence, or the truth of the payload or
timestamp. In particular, another component in the same admin domain is not
independent. A writer with filesystem access can replace the entire chain.
Trusted head/count anchors detect a changed chain or suffix truncation only
while the anchors themselves remain trustworthy; rewriting both defeats that
check. Keep anchors outside the mutable ledger when that assurance is needed.
Canonical hashes cover JSON values, not whitespace or original JSON spelling.

Vitality values are toy resource proxies, NOT real health measurements. They
are observe-only, do not control motion, and confer no authority.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
import threading

__all__ = [
    "ReceiptLedger",
    "verify_ledger",
    "make_proposal",
    "observe_vitality",
]

_SCHEMA_VERSION = 1
_GENESIS_HASH = "0" * 64
_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "index",
        "event_time",
        "record_time",
        "previous_hash",
        "payload",
        "event_type",
        "hash",
    }
)
_EVIDENCE_KEYS = frozenset({"integrity_ok", "tests_ok", "evidence_count"})


def _json_value(value):
    """Reject coercions (tuple, non-string key, custom type) and nonfinite JSON."""
    kind = type(value)
    if value is None or kind in (str, bool, int):
        return
    if kind is float:
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return
    if kind is list:
        for item in value:
            _json_value(item)
        return
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _json_value(item)
        return
    raise ValueError("payload must contain only JSON values")


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def _digest(unsigned_receipt):
    return hashlib.sha256(_canonical(unsigned_receipt).encode("utf-8")).hexdigest()


def _is_hash(value):
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _nonnegative_integer(value):
    return type(value) is int and value >= 0


def _finite_nonnegative(value):
    # bool is a subclass of int; it must not masquerade as a count or signal.
    # Avoid converting arbitrary-size integers to float just to check finiteness.
    return (
        type(value) in (int, float)
        and value >= 0
        and (type(value) is int or math.isfinite(value))
    )


def _validate_event(event_type, payload, event_time):
    if type(event_type) is not str or not event_type.strip():
        raise ValueError("event_type must be a nonempty string")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if not _nonnegative_integer(event_time):
        raise ValueError("event_time must be a nonnegative logical integer")
    try:
        _json_value(payload)
    except RecursionError as error:
        raise ValueError("payload is cyclic or too deeply nested") from error


class ReceiptLedger:
    """Create a NEW JSONL ledger with exclusive ``'x'`` creation.

    ``append(event_type, payload, event_time)`` snapshots a JSON-object payload,
    records an actual UTC timestamp, hashes the canonical unsigned receipt, and
    writes and flushes one newline-terminated record. Indexes are zero-based;
    the genesis previous_hash is 64 zeroes. ``event_time`` is a caller-supplied
    nonnegative logical integer (e.g. generation), never inferred from a clock.
    Equal or nonmonotonic event times are permitted; index establishes ordering.

    The API never seeks, rewrites, resumes, or opens an existing ledger. Appends
    from this instance are serialized, but this is not a multi-process writer or
    an OS-enforced immutable store. A write failure closes the instance because
    a partial record may have reached disk. Flush is not a power-loss guarantee.
    Use a context manager or ``close()``. Returned receipts are detached copies.
    """

    def __init__(self, path):
        self._lock = threading.Lock()
        self._count = 0
        self._head = None
        self._closed = False
        self._file = open(os.fspath(path), "x", encoding="utf-8", newline="\n")

    @property
    def count(self):
        """Number of successfully appended receipts."""
        with self._lock:
            return self._count

    @property
    def head(self):
        """Last receipt hash, or None before the first append."""
        with self._lock:
            return self._head

    @property
    def closed(self):
        with self._lock:
            return self._closed

    def append(self, event_type, payload, event_time):
        with self._lock:
            if self._closed:
                raise ValueError("ledger is closed")
            _validate_event(event_type, payload, event_time)
            try:
                # Snapshot caller-owned nested values before hashing or writing.
                payload_copy = json.loads(_canonical(payload))
                receipt = {
                    "schema_version": _SCHEMA_VERSION,
                    "index": self._count,
                    "event_time": event_time,
                    "record_time": datetime.now(timezone.utc).isoformat(
                        timespec="microseconds"
                    ),
                    "previous_hash": self._head or _GENESIS_HASH,
                    "payload": payload_copy,
                    "event_type": event_type,
                }
                receipt["hash"] = _digest(receipt)
                line = _canonical(receipt) + "\n"
                # Check Unicode encoding before any bytes are written.
                line.encode("utf-8")
            except (TypeError, ValueError, RecursionError, UnicodeError) as error:
                raise ValueError("receipt cannot be encoded as canonical JSON") from error
            try:
                written = self._file.write(line)
                if written != len(line):
                    raise OSError("incomplete ledger write")
                self._file.flush()
            except (OSError, ValueError):
                self._closed = True
                try:
                    self._file.close()
                except (OSError, ValueError):
                    pass
                raise
            self._count += 1
            self._head = receipt["hash"]
            return receipt

    def close(self):
        """Close idempotently; no later append is permitted."""
        with self._lock:
            if not self._closed:
                self._closed = True
                self._file.close()

    def __enter__(self):
        if self.closed:
            raise ValueError("ledger is closed")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def _validate_record(receipt, index, previous_hash):
    if type(receipt) is not dict or set(receipt) != _RECEIPT_KEYS:
        raise ValueError("unknown, missing, or malformed receipt fields")
    if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
        raise ValueError("unknown schema_version")
    if not _nonnegative_integer(receipt["index"]) or receipt["index"] != index:
        raise ValueError("index/order mismatch")
    _validate_event(receipt["event_type"], receipt["payload"], receipt["event_time"])
    if not _is_hash(receipt["previous_hash"]) or receipt["previous_hash"] != previous_hash:
        raise ValueError("previous_hash mismatch")
    if not _is_hash(receipt["hash"]):
        raise ValueError("malformed hash")
    stamp = receipt["record_time"]
    if type(stamp) is not str:
        raise ValueError("record_time must be a UTC ISO timestamp")
    try:
        parsed = datetime.fromisoformat(stamp)
        if (
            parsed.utcoffset() != timedelta(0)
            or parsed.isoformat(timespec="microseconds") != stamp
        ):
            raise ValueError("not canonical UTC")
    except (TypeError, ValueError) as error:
        raise ValueError("record_time must be a canonical UTC ISO timestamp") from error
    unsigned = {key: value for key, value in receipt.items() if key != "hash"}
    if _digest(unsigned) != receipt["hash"]:
        raise ValueError("receipt hash mismatch")


def verify_ledger(path, expected_head=None, expected_count=None):
    """Verify schema and canonical chain, optionally against trusted anchors.

    Returns exactly ``{valid, count, head, errors}``. On failure, count/head
    describe only the fully verified prefix; errors is a list of explanations.
    Missing/unreadable files, empty files, blank/malformed/unterminated records,
    duplicate JSON keys, unknown schema/fields, and invalid anchors fail closed.
    Head is None when no record has verified. An empty ledger is NEVER valid,
    even with expected_count=0.

    Without an external expected_head or expected_count, a nonempty valid
    prefix cannot be distinguished from a ledger whose suffix was removed.
    Rehashing the entire ledger also passes without a trusted head anchor.
    A count anchor alone does not detect a same-length full rewrite.
    """
    errors = []
    count = 0
    head = None
    if expected_head is not None and not _is_hash(expected_head):
        errors.append("expected_head must be a lowercase SHA256 hex digest")
    if expected_count is not None and not _nonnegative_integer(expected_count):
        errors.append("expected_count must be a nonnegative integer")
    if errors:
        return {"valid": False, "count": count, "head": head, "errors": errors}
    try:
        with open(os.fspath(path), "r", encoding="utf-8", newline="") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    if not line.endswith("\n"):
                        raise ValueError("unterminated JSONL record")
                    receipt = json.loads(
                        line, object_pairs_hook=_unique_object,
                        parse_constant=_reject_constant,
                    )
                    _validate_record(receipt, count, head or _GENESIS_HASH)
                except (
                    TypeError, ValueError, RecursionError, UnicodeError, OverflowError
                ) as error:
                    errors.append("line {}: {}".format(line_number, error))
                    break
                count += 1
                head = receipt["hash"]
    except (OSError, TypeError, ValueError, UnicodeError) as error:
        errors.append("cannot read ledger: {}".format(error))
    if count == 0:
        errors.append("ledger has no verified records")
    if expected_count is not None and count != expected_count:
        errors.append("expected_count mismatch")
    if expected_head is not None and head != expected_head:
        errors.append("expected_head mismatch")
    return {"valid": not errors, "count": count, "head": head, "errors": errors}


def _proposal_authority():
    return {
        "production_authorized": False,
        "action": "NONE",
        "authority": "A0_PROPOSE_ONLY",
    }


def make_proposal(evidence: dict) -> dict:
    """Assess a technical lab claim without granting ANY deployment authority.

    The closed input schema is integrity_ok, tests_ok, evidence_count. Both
    flags must be literal bools. Count must be an explicit finite nonnegative
    built-in int/float, not a bool. Unknown fields (including owner-approval
    strings, purported signatures, and requested authority) fail closed.

    technical_lab_status:
      PASS: both flags True and count > 0.
      FAIL: valid evidence schema with at least one flag False.
      INSUFFICIENT_EVIDENCE: valid flags True but count is zero.
      UNKNOWN: missing, malformed, or unknown evidence/schema.

    A valid zero count is deliberately insufficient to claim a technical pass.
    This function checks supplied evidence fields; it does not independently
    run tests, authenticate people, or establish independence. There is no
    execute flag, signature verifier, approval shortcut, or production path.
    """
    result = _proposal_authority()
    reasons = []
    count = None
    if type(evidence) is not dict:
        reasons.append("evidence_must_be_dict")
    else:
        if set(evidence) - _EVIDENCE_KEYS:
            reasons.append("unknown_evidence_fields")
        if _EVIDENCE_KEYS - set(evidence):
            reasons.append("missing_evidence_fields")
        if type(evidence.get("integrity_ok")) is not bool:
            reasons.append("integrity_ok_must_be_bool")
        if type(evidence.get("tests_ok")) is not bool:
            reasons.append("tests_ok_must_be_bool")
        if not _finite_nonnegative(evidence.get("evidence_count")):
            reasons.append("evidence_count_must_be_finite_nonnegative_number")
        else:
            count = evidence["evidence_count"]
    if reasons:
        status = "UNKNOWN"
    elif evidence["integrity_ok"] is not True or evidence["tests_ok"] is not True:
        status = "FAIL"
        if evidence["integrity_ok"] is False:
            reasons.append("integrity_check_failed")
        if evidence["tests_ok"] is False:
            reasons.append("tests_failed")
    elif count == 0:
        status = "INSUFFICIENT_EVIDENCE"
        reasons.append("no_evidence")
    else:
        status = "PASS"
    result.update(
        technical_lab_status=status, evidence_count=count, reasons=reasons
    )
    return result


def observe_vitality(path_len, collision_rate, turn_effort) -> dict:
    """Observe toy resource proxies; never control motion or grant authority.

    Accept finite nonnegative built-in int/float scalars (not bools);
    collision_rate must additionally be in [0, 1]. Path length and turn effort
    are unbounded nonnegative toy quantities, not real health measurements.

    energy_reserve = clamp(1 - .12*path_len - .35*turn_effort
                           - .4*collision_rate, 0, 1)
    GREEN >= .65; YELLOW >= .4; RED >= .2; BLACK otherwise.
    Invalid input yields BLACK, zero energy, and input_valid=False.
    """
    valid = (
        _finite_nonnegative(path_len)
        and _finite_nonnegative(collision_rate)
        and _finite_nonnegative(turn_effort)
        and collision_rate <= 1
    )
    energy = 0.0
    if valid:
        # Saturating each nonnegative penalty at 1 leaves the clamped result
        # unchanged and avoids float overflow for arbitrary-size Python ints.
        energy = max(
            0.0,
            min(
                1.0,
                1.0
                - 0.12 * min(path_len, 1.0 / 0.12)
                - 0.35 * min(turn_effort, 1.0 / 0.35)
                - 0.4 * collision_rate,
            ),
        )
    if energy >= 0.65:
        status = "GREEN"
    elif energy >= 0.4:
        status = "YELLOW"
    elif energy >= 0.2:
        status = "RED"
    else:
        status = "BLACK"
    result = _proposal_authority()
    result.update(
        energy_reserve=energy,
        status=status,
        input_valid=bool(valid),
        observe_only=True,
        controls_motion=False,
        value_kind="TOY_RESOURCE_PROXY",
    )
    return result
