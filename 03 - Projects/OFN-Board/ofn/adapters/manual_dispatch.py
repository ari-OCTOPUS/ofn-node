"""Manual dispatch contracts (operations launch O1).

A manual packet is what the HUMAN actually sends: the exact text, target,
and channels, derived from the outbox payload at approval time. The
completion receipt is the independent record that the human did send it —
it carries a hash of the packet and an optional external reference digest,
never the raw content or any credential.

These are adapter-layer types (not kernel): they carry no business names
and no I/O; they are pure data shapes with a hash helper.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ManualPacket:
    """The exact bytes a human is about to send outside the node."""

    idem_key: str
    tenant: str
    kind: str
    text: str
    target: str = ""           # phone/email/channel, or "" if none
    channels: tuple[str, ...] = ()
    meta: Mapping[str, object] = ()

    def sha256(self) -> str:
        """Hash of the exact packet content — the receipt's witness."""
        canonical = json.dumps(
            {"text": self.text, "target": self.target,
             "channels": list(self.channels), "meta": dict(self.meta)},
            ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CompletionReceipt:
    """The independent record that a human completed a manual delivery."""

    idem_key: str
    tenant: str
    completed_at: str
    completed_by: str
    channel: str
    packet_sha256: str
    external_ref_digest: str = ""   # optional hash, never raw proof
