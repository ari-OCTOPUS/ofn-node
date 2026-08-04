"""Writing image bytes to disk, and the one place that is allowed to.

Everything that decides — what is too big, which media types, what a file is
called — lives in `kernel/photos.py`. This module only carries out those
decisions, so the rules can be tested without a filesystem and there is
exactly one function in the project that turns a request into a file.

Two properties are enforced here rather than assumed:

    the decoded size is checked again, after decoding
    the resolved path is checked to be inside the media root

Both are already guaranteed upstream. They are re-checked because they are
the two failures that cannot be undone by a later fix: bytes on disk that
should not be there, and bytes on disk somewhere they should not be.
"""

from __future__ import annotations

import base64
import binascii
import os
import shutil

from ..kernel.errors import FailClosedError
from ..kernel.photos import (
    Payload, is_inside, original_path, piece_prefix, relative_path,
)


class MediaStore:
    """Files under one root, one subtree per business."""

    def __init__(self, root: str) -> None:
        self._root = os.path.abspath(root)
        os.makedirs(self._root, exist_ok=True)

    @property
    def root(self) -> str:
        return self._root

    def absolute(self, relative: str) -> str:
        full = os.path.abspath(os.path.join(self._root, relative))
        if not is_inside(self._root, full):
            # Unreachable through `relative_path`, which builds from
            # validated ids only. Kept because "unreachable" is a property of
            # today's call sites, not of the function.
            raise FailClosedError(f"path escapes the media root: {relative!r}")
        return full

    def _put(self, rel: str, payload: Payload) -> str:
        full = self.absolute(rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        try:
            raw = base64.b64decode(payload.body, validate=True)
        except (binascii.Error, ValueError):
            raise FailClosedError("تصویر خراب است — base64 معتبر نیست") from None
        if len(raw) > payload.max_decoded_bytes:
            # The bound rounds up, so real bytes exceeding it means the text
            # was not what was measured.
            raise FailClosedError("اندازهٔ تصویر با آنچه سنجیده شد نمی‌خواند")

        # Written to a temporary name and renamed, so a power cut leaves
        # either nothing or a whole file. A half-written JPEG with a database
        # row pointing at it is worse than a missing one — it looks like data.
        tmp = full + ".part"
        with open(tmp, "wb") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, full)
        return rel

    def write_rendition(self, tenant: str, piece_id: str, position: int,
                        edge: int, payload: Payload) -> str:
        """One of the two browser-made sizes. Always jpeg."""
        return self._put(relative_path(tenant, piece_id, position, edge),
                         payload)

    def write_original(self, tenant: str, piece_id: str, position: int,
                       payload: Payload) -> str:
        """The archive copy, in whatever arrived.

        Anything published has to be archivable at the quality it was
        published at, or afterwards nobody can say what actually went out.
        """
        return self._put(
            original_path(tenant, piece_id, position, payload.media_type),
            payload)

    def exists(self, relative: str) -> bool:
        return os.path.isfile(self.absolute(relative))

    def size_on_disk(self, relative: str) -> int:
        return os.path.getsize(self.absolute(relative))

    def read(self, relative: str) -> bytes:
        with open(self.absolute(relative), "rb") as fh:
            return fh.read()

    def remove_piece(self, tenant: str, piece_id: str) -> int:
        """Delete every rendition belonging to one piece.

        The cascade half of a cascade delete. A database row removed without
        this leaves files nothing references and nothing will ever clean up —
        and for the studio leg those files are pictures of a person.

        Deletes the directory named by `piece_prefix`, not everything whose
        path starts with the piece id: `piece-1` must not take `piece-10`.
        """
        target = self.absolute(piece_prefix(tenant, piece_id).rstrip("/"))
        if not os.path.isdir(target):
            return 0
        count = sum(len(files) for _, _, files in os.walk(target))
        shutil.rmtree(target)
        return count

    def tenant_bytes(self, tenant: str) -> int:
        """Total bytes under one business. Used by the backup report."""
        base = self.absolute(tenant)
        if not os.path.isdir(base):
            return 0
        total = 0
        for here, _, files in os.walk(base):
            for name in files:
                total += os.path.getsize(os.path.join(here, name))
        return total
