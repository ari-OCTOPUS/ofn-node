"""Writing image bytes to disk, and the one place that is allowed to.

Everything that decides — what is too big, which formats, what a file is
called — lives in `kernel/photos.py`. This module only carries out those
decisions, so that the rules can be tested without a filesystem and so there
is exactly one function in the project that turns a request into a file.

Two properties are enforced here rather than assumed:

    the decoded size is checked again after decoding
    the resolved path is checked to be inside the media root

Both are already guaranteed by the kernel. They are re-checked because they
are the two failures that cannot be undone by a later fix: bytes on disk that
should not be there, and bytes on disk somewhere they should not be.
"""

from __future__ import annotations

import base64
import binascii
import os
import shutil

from ..kernel.errors import FailClosedError
from ..kernel.photos import Size, Upload, all_paths, is_inside


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
            # Unreachable through `relative_path`, which builds from validated
            # ids only. Kept because "unreachable" is a property of today's
            # call sites, not of the function.
            raise FailClosedError(f"path escapes the media root: {relative!r}")
        return full

    def write(self, upload: Upload, size: Size, b64_text: str) -> str:
        """Decode and store one rendition. Returns the relative path.

        The write is to a temporary name in the same directory and then
        renamed, so a power cut leaves either nothing or a whole file. A
        half-written JPEG that still has a database row pointing at it is
        worse than a missing one: it looks like data.
        """
        rel = all_paths(upload)[size]
        full = self.absolute(rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)

        try:
            raw = base64.b64decode(b64_text, validate=True)
        except (binascii.Error, ValueError):
            raise FailClosedError("تصویر خراب است — base64 معتبر نیست") from None
        if len(raw) > upload.declared_bytes:
            # The estimate rounds up, so real bytes exceeding it means the
            # text was not what was measured.
            raise FailClosedError("اندازهٔ تصویر با آنچه اعلام شد نمی‌خواند")

        tmp = full + ".part"
        with open(tmp, "wb") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, full)
        return rel

    def exists(self, relative: str) -> bool:
        return os.path.isfile(self.absolute(relative))

    def size_on_disk(self, relative: str) -> int:
        return os.path.getsize(self.absolute(relative))

    def read(self, relative: str) -> bytes:
        with open(self.absolute(relative), "rb") as fh:
            return fh.read()

    def remove_owner(self, tenant: str, owner_id: str) -> int:
        """Delete every rendition belonging to one draft or product.

        The cascade half of a cascade delete. A database row removed without
        this leaves files that nothing references and nothing will ever
        clean up — and for this leg those files are pictures of a person.
        """
        target = self.absolute(f"{tenant}/{owner_id}")
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
