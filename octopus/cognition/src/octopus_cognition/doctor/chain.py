"""Deterministic hash chaining for Doctor findings and change records.

Existing prediction/reflex/metacontrol ledgers keep their historical formula
(prev + seq + body). New chains use prev || canonical(body) as specified.
Do not append to the anchored audit checkpoint at seq=266.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


GENESIS = "sha256:" + ("0" * 64)


def canonical(body: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(body),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def chain_hash(previous_hash: str, body: Mapping[str, Any]) -> str:
    material = previous_hash.encode("utf-8") + canonical(body)
    return "sha256:" + hashlib.sha256(material).hexdigest()


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()
