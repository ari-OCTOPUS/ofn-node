"""O11 — dry-run sender (prepared, NOT enabled).

This module can BUILD a dry-run diff of what a publish WOULD do, but it
cannot publish: `send()` is structurally absent — the only exit is the
outbox, and even there nothing drains. Real outbound requires:
  - secrets rotated and `secret_rotation` officially open
  - `partner_precondition` recorded and the studio gate opened
  - the exact transport WIRE turned on
  - `require_release_context()` immediately before transport
  - one tenant, one platform, one item cap
  - dry-run diff + second confirmation

Until every one of those holds, `dry_run_diff()` is the ONLY method that
exists here, and it mutates nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PublishIntent:
    """What a future sender would publish — the diff input."""

    tenant: str
    platform: str
    idempotency_key: str
    caption: str
    media_refs: tuple[str, ...] = ()
    adult_label: bool = False


def dry_run_diff(intent: PublishIntent,
                 release: Mapping[str, object] | None = None) -> dict:
    """The exact bytes a publish WOULD send, as a diff for human review.

    Nothing is transmitted, nothing is queued, nothing is mutated. The
    output is the payload + the release context snapshot, so the human can
    confirm "this exact text to this platform under these gates".

    Returns ok=False if the release context is missing or not green — a
    sender must never even propose a publish without it.
    """
    if release is None:
        return {"ok": False, "error": "release context required",
                "rule": "release:context-missing"}
    if not release.get("ok"):
        return {"ok": False, "error": release.get("reason", "release blocked"),
                "rule": release.get("rule", "release:blocked")}
    return {
        "ok": True,
        "mode": "dry-run",
        "diff": {
            "tenant": intent.tenant,
            "platform": intent.platform,
            "idempotency_key": intent.idempotency_key,
            "caption": intent.caption,
            "media_refs": list(intent.media_refs),
            "adult_label": intent.adult_label,
            "payload_json": json.dumps(
                {"caption": intent.caption,
                 "media_refs": list(intent.media_refs),
                 "adult_label": intent.adult_label},
                ensure_ascii=False, sort_keys=True),
        },
        "release_snapshot": {k: release.get(k)
                             for k in ("rule", "risk", "ok")},
    }
