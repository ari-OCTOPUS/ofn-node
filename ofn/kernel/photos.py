"""Rules for accepting an image, decided before any bytes are touched.

This module holds the parts of image handling that are decisions rather than
I/O: how big is too big, which formats are allowed, and — the one that
matters most — what a stored file is called.

    a stored path is built from ids this system generated,
    never from anything the sender chose

That is the whole defence. A filename that arrives with an upload is
attacker-controlled text; every traversal bug in this class comes from
treating it as a name instead of as data. Here it is not used at all: the
sender's filename is not a parameter of any function in this file.

The size cap is checked against the *encoded* length, before decoding.
Decoding first and measuring afterwards means a 200 MB payload is already in
memory on a board with 4 GB and three other businesses running on it. Base64
expands by a known ratio, so the encoded length is enough to refuse early.

Kernel purity: no filesystem, no clock, no decoding. `media.py` does those,
using the answers from here.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Mapping

from .errors import FailClosedError

_ID = re.compile(r"^[a-z0-9]([a-z0-9_-]{0,62}[a-z0-9])?$")

# What a phone actually produces, plus the one the web hands back from a
# canvas. Deliberately a fixed set: "whatever the browser said it is" is a
# content-type header, and a content-type header is a claim by the sender.
ALLOWED_MIME: Mapping[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# The cap on one upload. Applies to this route only — the rest of the API has
# a much smaller body limit, and raising that one to fit a photo would raise
# it for every other endpoint too.
MAX_UPLOAD_BYTES = 16 * 1024 * 1024

# Base64 carries 3 bytes in every 4 characters. Used to refuse an oversized
# payload from its length alone, before anything is decoded.
_B64_RATIO = 3 / 4


class Size(enum.Enum):
    """Three sizes because the same photo has three jobs.

    ORIGINAL is kept for this leg specifically: anything that was published
    has to be archivable at the quality it was published at, or afterwards
    nobody can say what actually went out.
    """

    ORIGINAL = "original"
    DISPLAY = "display"      # long edge 1600 — what a preview shows
    THUMB = "thumb"          # long edge 320 — what a contact sheet scrolls


LONG_EDGE = {Size.DISPLAY: 1600, Size.THUMB: 320}


@dataclass(frozen=True)
class Upload:
    """An accepted upload, described. No bytes here."""

    tenant: str
    owner_id: str            # the draft or product this belongs to
    photo_id: str
    mime: str
    declared_bytes: int

    @property
    def extension(self) -> str:
        return ALLOWED_MIME[self.mime]


def decoded_length(b64_len: int) -> int:
    """How many bytes a base64 string of this length will become.

    An estimate, and deliberately one that rounds *up*: it is used to refuse
    things, so erring towards refusing is the safe direction.
    """
    return int(b64_len * _B64_RATIO) + 3


def check_size(b64_text: str, *, max_bytes: int = MAX_UPLOAD_BYTES) -> int:
    """Refuse an oversized upload from its length, before decoding it.

    Returns the estimated decoded size so a caller can record it.
    """
    size = decoded_length(len(b64_text or ""))
    if size > max_bytes:
        raise FailClosedError(
            f"تصویر بزرگ‌تر از حد مجاز است "
            f"({size // 1024 // 1024}MB > {max_bytes // 1024 // 1024}MB)")
    if not b64_text:
        raise FailClosedError("تصویر خالی است")
    return size


def accept(tenant: str, owner_id: str, photo_id: str, *, mime: str,
           b64_text: str, max_bytes: int = MAX_UPLOAD_BYTES) -> Upload:
    """Decide whether this upload may be stored, and under what name.

    Every id is validated here rather than at the call site, because a call
    site that validates is a call site that can forget to.
    """
    for name, value in (("tenant", tenant), ("owner", owner_id),
                        ("photo", photo_id)):
        if not _ID.match(value or ""):
            raise FailClosedError(f"invalid {name} id: {value!r}")
    if mime not in ALLOWED_MIME:
        raise FailClosedError(f"نوع تصویر پشتیبانی نمی‌شود: {mime!r}")
    size = check_size(b64_text, max_bytes=max_bytes)
    return Upload(tenant, owner_id, photo_id, mime, size)


def relative_path(upload: Upload, size: Size) -> str:
    """Where this image lives, relative to the media root.

    Built entirely from validated ids. There is no parameter here that the
    sender controls, which is why there is no traversal check: nothing that
    could traverse ever reaches this function.

    The tenant is the first path component so that one business's media is a
    subtree. That makes "did anything leak between legs" a question about
    directories rather than about every row in a table.
    """
    if size is Size.ORIGINAL:
        leaf = f"{upload.photo_id}.{upload.extension}"
    else:
        # Derived sizes are always jpeg — they are made by a canvas, and a
        # PNG screenshot re-encoded at 1600px is several megabytes for no
        # gain on a board with this much disk.
        leaf = f"{upload.photo_id}.{size.value}.jpg"
    return f"{upload.tenant}/{upload.owner_id}/{leaf}"


def all_paths(upload: Upload) -> Mapping[Size, str]:
    return {s: relative_path(upload, s) for s in Size}


def is_inside(root: str, candidate: str) -> bool:
    """Whether a resolved path is really under the media root.

    A belt to the braces above. `relative_path` cannot produce an escape, so
    this exists for the day somebody adds a second way to build a path and
    does not read this file first.
    """
    root = root.rstrip("/") + "/"
    return candidate.startswith(root) and ".." not in candidate
