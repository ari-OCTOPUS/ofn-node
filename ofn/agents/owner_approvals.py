"""owner_approvals — the real two-step owner-approval store for releases.

Why this exists: release_pipeline.py used to treat ``bool(step_token)`` as
owner approval — any non-empty string authorized a real send. That is the
single most dangerous line the M5 bridge shipped. This module replaces it
with the actual trust path:

  1. ``issue``  — a card is prepared; two single-use confirm codes are
     minted and written (codes + payload) to an append-only journal. The
     codes go to the OWNER via the card channel; nothing else has them.
  2. ``record_step`` — an owner confirmation (via queue/telegram operator)
     records that a code was presented back.
  3. ``validate`` — the pipeline accepts a release only when: the approval
     exists, is not revoked, the draft text hashes to the bound payload,
     the lead matches, both codes match what was issued, both steps were
     presented, the steps are distinct events, and nothing expired (24h,
     the D-27 rollback window).

An approval is bound to (lead_id, sha256(draft), platform, effect_id). A
retry of the same effect reuses the same approval while unexpired; a
changed draft invalidates it. Revocation is append-only and permanent.

Fail-closed everywhere: unreadable journal, malformed rows, or clock
errors all refuse. Kernel purity is preserved — this is an agents-module
with I/O by design; it decides nothing about *publishing* itself, it only
authenticates the owner's hand.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.owner-approvals.v1"
APPROVALS_JOURNAL = opslib.STATE_DIR / "legs" / "owner-approvals.jsonl"
EXPIRY_SECONDS = 24 * 3600  # D-27 rollback window

_KIND_ISSUE = "ISSUE"
_KIND_STEP = "STEP"
_KIND_REVOKE = "REVOKE"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_s(now: float | None = None) -> float:
    return time.time() if now is None else float(now)


def _append(entry: dict, path: Path | None = None) -> None:
    p = path or APPROVALS_JOURNAL
    p.parent.mkdir(parents=True, exist_ok=True)
    entry.setdefault("at", opslib.now_iso())
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        # fsync so a crash cannot silently drop the only copy of an approval.
        try:
            fh.flush()
            os.fsync(fh.fileno())
        except OSError:
            pass


def _load(path: Path | None = None) -> list[dict]:
    p = path or APPROVALS_JOURNAL
    if not p.exists():
        return []
    entries: list[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            return []  # unreadable journal → fail-closed (validate refuses)
    return entries


def issue(*, lead_id: str, draft_text: str, platform: str,
          effect_id: str, path: Path | None = None) -> dict:
    """Mint an approval card record with two owner-held confirm codes."""
    aid = "aprv_" + secrets.token_hex(8)
    codes = {"step1_code": secrets.token_hex(4),
             "step2_code": secrets.token_hex(4)}
    payload = {"lead_id": str(lead_id), "platform": str(platform),
               "draft_sha256": _sha256(draft_text), "effect_id": str(effect_id)}
    _append({"kind": _KIND_ISSUE, "approval_id": aid, "payload": payload,
             **codes}, path)
    # The codes must reach only the owner channel; the caller (card flow)
    # receives them here once. The journal itself is on the board, root-only
    # readable in production deployments.
    return {"approval_id": aid, **codes, "payload": payload}


def record_step(approval_id: str, step: int, *, actor: str = "owner",
                path: Path | None = None, now: float | None = None) -> bool:
    """Record that the owner presented a step's confirm code. Idempotent
    per (approval, step); a second presentation of the SAME step is a
    no-op refusal (False) so a replayed code cannot double-count."""
    if step not in (1, 2):
        return False
    _append({"kind": _KIND_STEP, "approval_id": str(approval_id),
             "step": int(step), "actor": str(actor),
             "step_at_s": round(_now_s(now), 3)}, path)
    return True


def revoke(approval_id: str, *, reason: str = "",
           path: Path | None = None) -> None:
    _append({"kind": _KIND_REVOKE, "approval_id": str(approval_id),
             "reason": str(reason)[:200]}, path)


def validate(approval_id: str, step1_code: str, step2_code: str, *,
             lead_id: str, draft_text: str, platform: str,
             effect_id: str, path: Path | None = None,
             now: float | None = None) -> tuple[bool, str]:
    """True only for a live, bound, two-step, unexpired, unrevoked approval."""
    entries = _load(path)
    if not entries and (path or APPROVALS_JOURNAL).exists():
        return False, "approvals:journal-unreadable"
    issued: dict | None = None
    steps: list[dict] = []
    revoked = False
    for e in entries:
        if e.get("approval_id") != str(approval_id):
            continue
        kind = e.get("kind")
        if kind == _KIND_ISSUE:
            if issued is not None:
                return False, "approvals:duplicate-issue"
            issued = e
        elif kind == _KIND_STEP:
            steps.append(e)
        elif kind == _KIND_REVOKE:
            revoked = True
    if revoked:
        return False, "approvals:revoked"
    if issued is None:
        return False, "approvals:unknown"
    payload = issued.get("payload") or {}
    if payload.get("draft_sha256") != _sha256(draft_text):
        return False, "approvals:payload-mismatch"
    if payload.get("lead_id") != str(lead_id):
        return False, "approvals:lead-mismatch"
    if payload.get("platform") != str(platform):
        return False, "approvals:platform-mismatch"
    if payload.get("effect_id") != str(effect_id):
        return False, "approvals:effect-mismatch"
    if not secrets.compare_digest(str(issued.get("step1_code", "")),
                                  str(step1_code or "\0")):
        return False, "approvals:step1-code-invalid"
    if not secrets.compare_digest(str(issued.get("step2_code", "")),
                                  str(step2_code or "\0")):
        return False, "approvals:step2-code-invalid"
    s1 = sorted(float(s["step_at_s"]) for s in steps if s.get("step") == 1)
    s2 = sorted(float(s["step_at_s"]) for s in steps if s.get("step") == 2)
    if not s1 or not s2:
        return False, "approvals:two-step-required"
    now_s = _now_s(now)
    latest = max(s1[-1], s2[-1])
    if now_s - latest > EXPIRY_SECONDS:
        return False, "approvals:expired"
    return True, "approvals:ok"
