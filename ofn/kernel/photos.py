"""Photo intake. Every rule here answers the same question:

    can a phone, or something pretending to be one, make this node write
    somewhere it should not, or allocate memory it should not?

Two properties carry most of the weight.

**Size is judged before decoding.** Base64 carries three bytes in every four
characters, so the length of the text bounds the size of the image. Decoding
first and measuring afterwards means a 200 MB payload is already resident on
a 4 GB board that is also running three other businesses. The bound rounds
*up*: it is used to refuse, and refusing early is the safe direction.

**Paths are built, never accepted.** Nothing a sender chose reaches the
filesystem — not a filename, not a media type, not an extension. Every
component of a stored path comes from an id this system validated. That is
why there is no traversal check inside `relative_path`: nothing that could
traverse ever reaches it.

Kernel purity: no filesystem, no clock, no decoding. `adapters/media.py` does
those, using the answers from here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .errors import FailClosedError

# Lower case only, and no dots or slashes. Case matters: on a
# case-insensitive filesystem `Piece` and `piece` are one directory, so
# folding would silently merge two pieces rather than rejecting one.
_ID = re.compile(r"^[a-z0-9]([a-z0-9_-]{0,62}[a-z0-9])?$")

# The base64 alphabet, with padding only at the end.
_B64 = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")

_DATA_URL = re.compile(r"^data:([a-z]+/[a-z0-9.+-]+);base64,(.*)$", re.S)

# What a canvas can actually produce. `toDataURL` gives jpeg or falls back to
# png; nothing else is a thing this node will ever be handed by its own shell,
# and anything else is a claim by the sender.
ALLOWED_MEDIA_TYPES = ("image/jpeg", "image/png")

# One upload, on this route only. The rest of the API has a much smaller body
# limit; raising that to fit a photo would raise it for every endpoint.
MAX_DECODED_BYTES = 16 * 1024 * 1024

# The two renditions the browser sends. The archive copy is handled by
# `original_path` — it keeps the bytes exactly as they arrived, which is a
# different promise from these.
ALLOWED_EDGES = (1600, 320)

# More photos than this on one piece is a mistake, not a gallery.
MAX_POSITION = 9

_RATIO = 3 / 4


@dataclass(frozen=True)
class Payload:
    """An upload that has passed inspection. No bytes here."""

    body: str                  # base64, header stripped
    media_type: str
    max_decoded_bytes: int


def _limit(limit: int | None) -> int:
    if limit is None:
        return MAX_DECODED_BYTES
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise FailClosedError(f"invalid size limit: {limit!r}")
    return limit


def inspect(payload: Any, *, limit: int | None = None) -> Payload:
    """Judge an upload from its text alone, before anything is decoded.

    Accepts either a bare base64 string or the `data:` URL a canvas produces.
    The header is matched rather than split on the last comma: splitting would
    let the payload choose where the header ends, and a payload that can move
    that boundary can make the size estimate be computed over something that
    is not the image.
    """
    cap = _limit(limit)
    if not isinstance(payload, str):
        raise FailClosedError(f"payload must be text, got {type(payload).__name__}")
    if not payload:
        raise FailClosedError("payload is empty")

    media_type = "image/jpeg"
    body = payload
    if payload.startswith("data:"):
        m = _DATA_URL.match(payload)
        if m is None:
            # Falling through here would leave the header inside `body`, so
            # the size would be measured over a string that is not the image.
            raise FailClosedError("malformed data URL")
        media_type, body = m.group(1), m.group(2)

    if media_type not in ALLOWED_MEDIA_TYPES:
        raise FailClosedError(f"media type not served here: {media_type}")

    if not body:
        raise FailClosedError("payload is empty")
    if len(body) % 4 != 0:
        raise FailClosedError("payload length is not a multiple of four")
    if not _B64.match(body):
        # Whitespace lands here too, and deliberately: a canvas never wraps
        # its output, so newlines mean the payload did not come from where it
        # claims to — and they make the length estimate meaningless.
        raise FailClosedError("payload is not base64")

    size = int(len(body) * _RATIO)
    if size > cap:
        raise FailClosedError(
            f"image too large ({size // 1024 // 1024}MB > "
            f"{cap // 1024 // 1024}MB)")
    return Payload(body=body, media_type=media_type, max_decoded_bytes=size)


def _check_id(name: str, value: Any) -> str:
    if not isinstance(value, str) or not _ID.match(value):
        raise FailClosedError(f"invalid {name}: {value!r}")
    return value


def _check_position(position: Any) -> int:
    # `True == 1` in Python, so a bool passes an `isinstance(int)` check and
    # silently becomes position 1. Checked before the range, because the
    # range would accept it.
    if isinstance(position, bool) or not isinstance(position, int):
        raise FailClosedError(f"position must be a whole number: {position!r}")
    if not 0 <= position <= MAX_POSITION:
        raise FailClosedError(f"position out of range: {position}")
    return position


def relative_path(tenant: str, piece_id: str, position: int, edge: int) -> str:
    """Where one rendition lives, relative to the media root.

    Built entirely from validated inputs. The sender's filename is not a
    parameter of this function, or of any function in this module.

    The tenant is the first component so one business's media is a subtree,
    which makes "did anything cross between businesses" a question about
    directories rather than about every row in a table.
    """
    _check_id("tenant", tenant)
    _check_id("piece id", piece_id)
    _check_position(position)
    if isinstance(edge, bool) or not isinstance(edge, int) or edge not in ALLOWED_EDGES:
        raise FailClosedError(f"unknown edge: {edge!r}")
    return f"{tenant}/{piece_id}/{position}-{edge}.jpg"


def original_path(tenant: str, piece_id: str, position: int,
                  media_type: str) -> str:
    """Where the untouched upload is archived.

    Separate from `relative_path` because it is a different promise. The
    renditions are always jpeg — a canvas made them. This one keeps whatever
    arrived, because anything published has to be archivable at the quality
    it was published at, or afterwards nobody can say what actually went out.
    """
    _check_id("tenant", tenant)
    _check_id("piece id", piece_id)
    _check_position(position)
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise FailClosedError(f"media type not served here: {media_type}")
    ext = "png" if media_type == "image/png" else "jpg"
    return f"{tenant}/{piece_id}/{position}-original.{ext}"


def piece_prefix(tenant: str, piece_id: str) -> str:
    """Everything belonging to one piece, as a path prefix.

    The trailing slash is the whole point. Without it `piece-1/` is a prefix
    of `piece-10/...`, and a cascade delete takes a piece nobody asked it to
    take.
    """
    _check_id("tenant", tenant)
    _check_id("piece id", piece_id)
    return f"{tenant}/{piece_id}/"


def is_inside(root: str, candidate: str) -> bool:
    """Whether a resolved path is really under the media root.

    A belt to the braces above. `relative_path` cannot produce an escape, so
    this exists for the day somebody adds a second way to build a path and
    does not read this file first.
    """
    root = root.rstrip("/") + "/"
    return candidate.startswith(root) and ".." not in candidate
