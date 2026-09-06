"""prev_hash chain — second witness that a JSONL ledger was not rewritten.

The store's seq cursor proves order of *accepted* appends. It does not
prove a middle line was not replaced with another valid-looking record
that kept the same seq. A hash chain does: each record binds to the
digest of the previous canonical body.

This module does not claim filesystem immutability. It claims detectable
rewrite: a walk that re-hashes every body and checks claimed prev_hash
against the prior record_hash will refuse a spliced ledger. A rewrite of
the entire suffix produces a *different* tip — that is a new chain, not
the same one.

Not wired into the run store. Linking a record is not send_authorized,
quote_sent, or campaign_envelope_ready.

HALT stops STARTS. This chain has no halt parameter: in-flight appends
must still be chained so recovery does not need the owner.

Kernel purity: hashlib + re + typing. No json, no clock, no I/O. The
adapter feeds already-canonical bytes; this module returns hex digests.
"""

from __future__ import annotations

import hashlib
import re
from typing import List, Optional, Sequence, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name

GENESIS = "0" * 64
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A hash chain never authorizes a send. Structurally False."""
    return False


def halt_blocks_chain() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight linking."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A chain detects splice; it is not chattr +i."""
    return False


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if is_forbidden_effect_name(value) or value.strip().lower() in _SEALED:
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"{what} names a sealed send/ready alias: {value!r}")


def require_hex(digest: object, *, what: str = "digest") -> str:
    """64 lowercase hex chars. Uppercase, unknown, and non-str fail closed.

    UNKNOWN is not a match. A malformed digest is not treated as GENESIS.
    """
    if not isinstance(digest, str) or not digest.strip():
        raise FailClosedError(f"{what} required: {digest!r}")
    _refuse_sealed(digest, what=what)
    if not SHA256_HEX_RE.match(digest):
        raise FailClosedError(
            f"{what} must be 64 lowercase hex chars: {digest!r}")
    return digest


def record_hash(prev_hash: str, body: bytes) -> str:
    """SHA-256 of ``prev_hash || LF || body``. Kernel formats; it does not I/O.

    ``prev_hash`` is included so two identical bodies under different
    predecessors cannot share a digest. Empty body is not a record —
    the store skips blank lines; this module refuses them.
    """
    prev = require_hex(prev_hash, what="prev_hash")
    if isinstance(body, bool) or not isinstance(body, (bytes, bytearray)):
        raise FailClosedError(f"body must be bytes: {body!r}")
    raw = bytes(body)
    if not raw:
        raise FailClosedError("body must be non-empty bytes")
    return hashlib.sha256(prev.encode("ascii") + b"\n" + raw).hexdigest()


def refuse_sealed_chain_label(label: object) -> None:
    """A chain link is bytes + hex. A send/ready name is not a link label."""
    if not isinstance(label, str):
        raise FailClosedError(f"chain label must be a string: {label!r}")
    _refuse_sealed(label, what="chain label")


class HashChain:
    """Append-only prev_hash cursor. Replay does not write.

    Two independent claims:

      * first accept cites GENESIS (or the current tip, which starts there)
      * every later accept must cite the prior record_hash — a splice
        of a middle body with a sequential-looking seq still fails
        because the suffix still names the old digest
    """

    def __init__(self) -> None:
        self._tip = GENESIS
        self._accepted: List[str] = []

    @property
    def tip(self) -> str:
        return self._tip

    def accept(self, body: bytes, *, claimed_prev: Optional[str] = None) -> str:
        if claimed_prev is not None:
            claimed = require_hex(claimed_prev, what="claimed_prev")
            if claimed != self._tip:
                raise FailClosedError(
                    f"prev_hash break: expected {self._tip}, got {claimed!r}")
        digest = record_hash(self._tip, body)
        self._accepted.append(digest)
        self._tip = digest
        return digest

    def peek_would_accept(
        self, body: object, *, claimed_prev: Optional[object] = None,
    ) -> bool:
        """True only when ``accept`` would succeed. Does not write.

        Invalid input is False, not an exception — peek is a read.
        """
        if claimed_prev is not None:
            if not isinstance(claimed_prev, str) or not SHA256_HEX_RE.match(
                    claimed_prev):
                return False
            if claimed_prev != self._tip:
                return False
        if isinstance(body, bool) or not isinstance(body, (bytes, bytearray)):
            return False
        if not bytes(body):
            return False
        return True

    def __len__(self) -> int:
        return len(self._accepted)

    def replay(self) -> Tuple[str, ...]:
        """Read-only snapshot in append order. Has no write path."""
        return tuple(self._accepted)


def verify_links(links: Sequence[Tuple[object, object]]) -> str:
    """Walk ``(claimed_prev, body)`` pairs from GENESIS. Return the final tip.

    An empty walk returns GENESIS — absence of records is not a forged
    chain. A first link that does not cite GENESIS fails closed. Each
    later claimed_prev must equal ``record_hash`` of the prior link.

    Does not mutate any HashChain. Does not claim the file is immutable.
    """
    if not isinstance(links, (list, tuple)):
        raise FailClosedError(f"links must be a sequence: {links!r}")
    expected = GENESIS
    for index, item in enumerate(links):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise FailClosedError(
                f"link {index} must be (prev_hash, body): {item!r}")
        claimed_prev, body = item
        claimed = require_hex(claimed_prev, what="claimed_prev")
        if claimed != expected:
            raise FailClosedError(
                f"prev_hash break at link {index}: expected {expected}, "
                f"got {claimed!r}")
        expected = record_hash(claimed, body)
    return expected
