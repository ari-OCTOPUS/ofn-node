#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""receipts — append-only jsonl evidence with per-line sha256.

Every line is a self-verifying record: the line carries `line_sha256` computed
over the canonical JSON of everything except that field, so any tampering with
content or ordering is detectable by `ReceiptLog.verify()`. Receipts are the
contract's `receipts` flow-step for this lane: append-only, replayable.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path

__all__ = [
    "ReceiptLog", "canonical_json", "sha256_file", "sha256_text",
    "sha256_canonical_text_file",
]


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path | str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def sha256_canonical_text_file(path: Path | str) -> str:
    """SHA-256 of file bytes after CRLF→LF.

    Text-pin helper. ``.gitattributes eol=lf`` is the preferred checkout
    pin; this helper is the second witness if a runner still converts.
    Does not claim working-tree bytes are immutable.
    """
    data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ReceiptLog:
    """Append-only receipt journal. No update/delete API exists by design."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    # ------------------------------------------------------------------ write
    def write(self, kind: str, **fields) -> str:
        record = {"ts": _utcnow(), "kind": kind, **fields}
        record["line_sha256"] = sha256_text(canonical_json(record))
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(canonical_json(record) + "\n")
        return record["line_sha256"]

    def write_manifest(self, kind: str, manifest: dict[str, str]) -> str:
        """Manifest of {path: sha256}; ordering made deterministic by sorting."""
        payload = {p: manifest[p] for p in sorted(manifest)}
        digest = sha256_text(canonical_json(payload))
        return self.write(kind, manifest=payload, manifest_sha256=digest)

    # ------------------------------------------------------------------ verify
    def verify(self) -> dict:
        """Recompute every line's sha256. One bad line → valid=False overall."""
        lines, bad = 0, []
        with open(self.path, encoding="utf-8") as fh:
            for no, raw in enumerate(fh, 1):
                raw = raw.strip()
                if not raw:
                    continue
                lines += 1
                try:
                    rec = json.loads(raw)
                    claimed = rec.pop("line_sha256", None)
                    if claimed != sha256_text(canonical_json(rec)):
                        bad.append(no)
                except (ValueError, TypeError):
                    bad.append(no)
        return {"lines": lines, "bad_lines": bad, "valid": not bad}

    # ------------------------------------------------------------------ read
    def read_all(self) -> list[dict]:
        out = []
        with open(self.path, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if raw:
                    out.append(json.loads(raw))
        return out
