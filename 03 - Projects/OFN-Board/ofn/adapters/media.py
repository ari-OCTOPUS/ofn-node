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
import time

from ..kernel.errors import FailClosedError
from ..kernel.photos import (
    Payload, is_inside, original_path, piece_prefix, relative_path,
)


class MediaStore:
    """Files under one root, one subtree per business."""

    # Owner-only. For this leg the files are pictures of a person on a disk
    # that is not encrypted, so the cheapest useful control is that no other
    # account on the board can read them. It does not survive theft of the
    # board — nothing here does — but it is one fewer way to lose them.
    DIR_MODE = 0o700

    def __init__(self, root: str) -> None:
        self._root = os.path.abspath(root)
        os.makedirs(self._root, mode=self.DIR_MODE, exist_ok=True)
        try:
            os.chmod(self._root, self.DIR_MODE)   # an existing tree, too
        except OSError:
            pass

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
        os.makedirs(os.path.dirname(full), mode=self.DIR_MODE,
                    exist_ok=True)
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
        # Before the rename, not after: the file must never exist at the
        # final name in a readable mode, not even for the instant between
        # the two calls.
        os.chmod(tmp, 0o600)
        os.replace(tmp, full)
        return rel

    def sweep_stale_parts(self, max_age_s: int = 3600) -> int:
        """Remove .part files older than max_age_s (finding 36).

        A crash between writing the temp file and renaming it leaves a
        `.part` behind forever — the backup skips it, so it just sits there.
        This removes stale ones, bounded to the photos root by construction
        (the walk never leaves this.root). Returns how many were removed.
        """
        removed = 0
        now = time.time()
        for here, _, names in os.walk(self._root):
            for name in names:
                if not name.endswith(".part"):
                    continue
                path = os.path.join(here, name)
                try:
                    age = now - os.path.getmtime(path)
                    if age > max_age_s:
                        os.remove(path)
                        removed += 1
                except OSError:
                    continue
        return removed

    def write_rendition(self, tenant: str, piece_id: str, position: int,
                        edge: int, payload: Payload) -> str:
        """One of the two browser-made sizes. Always jpeg."""
        return self._put(relative_path(tenant, piece_id, position, edge),
                         payload)

    def write_original(self, tenant: str, piece_id: str, position: int,
                       payload: Payload) -> str:
        """The upload exactly as it arrived.

        Kept because this is her archive, not only a control panel. The
        renditions are what a screen shows and what a platform gets; the
        original is the work.
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

    def purge_from_backups(self, backup_root: str, tenant: str,
                           piece_id: str) -> int:
        """Remove a piece's files from every backup copy as well.

        Without this, "delete" means "in fourteen days" — the nightly backup
        keeps fourteen generations, so a photo she removed is still on the
        disk in fourteen places. For a control panel that would be a
        reasonable trade. For somebody's archive of their own body it is the
        wrong default, and it is the kind of wrong that is only discovered by
        someone who trusted the button.

        Backups themselves are not otherwise touched: only this subtree, only
        in each generation's `media` mirror.
        """
        removed = 0
        if not os.path.isdir(backup_root):
            return 0
        prefix = piece_prefix(tenant, piece_id).rstrip("/")
        for generation in sorted(os.listdir(backup_root)):
            target = os.path.join(backup_root, generation, "media", prefix)
            # Confined to the backup root by construction, and checked
            # anyway: this is a recursive delete driven by an id.
            full = os.path.abspath(target)
            if not is_inside(os.path.abspath(backup_root), full):
                raise FailClosedError(f"refusing to delete outside backups: {target}")
            if os.path.isdir(full):
                removed += sum(len(f) for _, _, f in os.walk(full))
                shutil.rmtree(full)
        return removed

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
