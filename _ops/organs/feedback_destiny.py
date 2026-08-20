#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feedback_destiny.py — C19 (مگا‌دستور #۱۷): Knowledge feedback destiny.

State machine: PROPOSED → SEEN → ACCEPTED | REJECTED | EXPIRED | SUPERSEDED
Proposal بدون پاسخ پس از TTL → EXPIRED (نه تکرار notification).
Digest داخلی برای consumer A/B — نه Telegram direct."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

DEFAULT_TTL_S = 7 * 24 * 3600  # یک هفته


@dataclass
class KnowledgeProposal:
    proposal_id: str
    event_id: str
    evidence_hash: str
    proposed_action: str
    owner_impact: str
    confidence: float
    created_at: float
    state: str = "PROPOSED"
    seen_at: float | None = None
    resolved_at: float | None = None
    resolution_reason: str = ""


class FeedbackDestiny:
    """مدیریت چرخهٔ عمر proposalهای knowledge — بدون Telegram send."""

    def __init__(self, state_path: Path | None = None):
        self.state_path = state_path
        self._proposals: dict[str, KnowledgeProposal] = {}
        if state_path and state_path.exists():
            try:
                for line in state_path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        d = json.loads(line)
                        self._proposals[d["proposal_id"]] = KnowledgeProposal(**d)
            except (OSError, ValueError, TypeError):
                pass

    def propose(self, event_id: str, evidence_hash: str, action: str,
                impact: str, confidence: float) -> KnowledgeProposal | None:
        """proposal فقط با evidence جدید + duplicate check."""
        # duplicate: same event_id already proposed
        for p in self._proposals.values():
            if p.event_id == event_id and p.state in ("PROPOSED", "SEEN"):
                return None  # duplicate — don't create
        pid = f"kp-{hashlib.sha256(f'{event_id}|{action}'.encode()).hexdigest()[:10]}"
        if pid in self._proposals:
            return None
        p = KnowledgeProposal(
            proposal_id=pid, event_id=event_id, evidence_hash=evidence_hash,
            proposed_action=action, owner_impact=impact, confidence=confidence,
            created_at=time.time())
        self._proposals[pid] = p
        self._save()
        return p

    def mark_seen(self, proposal_id: str) -> bool:
        p = self._proposals.get(proposal_id)
        if p and p.state == "PROPOSED":
            p.state = "SEEN"
            p.seen_at = time.time()
            self._save()
            return True
        return False

    def resolve(self, proposal_id: str, resolution: str, reason: str = "") -> bool:
        p = self._proposals.get(proposal_id)
        if p and p.state in ("PROPOSED", "SEEN"):
            if resolution in ("ACCEPTED", "REJECTED", "SUPERSEDED"):
                p.state = resolution
                p.resolved_at = time.time()
                p.resolution_reason = reason
                self._save()
                return True
        return False

    def expire_stale(self, ttl_s: float = DEFAULT_TTL_S) -> int:
        """proposals بی‌پاسخ پس از TTL → EXPIRED (نه notification جدید)."""
        now = time.time()
        expired = 0
        for p in self._proposals.values():
            if p.state in ("PROPOSED", "SEEN") and (now - p.created_at) > ttl_s:
                p.state = "EXPIRED"
                p.resolved_at = now
                p.resolution_reason = f"ttl_expired_{int(ttl_s)}s"
                expired += 1
        if expired:
            self._save()
        return expired

    def digest(self) -> dict:
        """digest داخلی برای consumer A/B — نه Telegram."""
        by_state: dict[str, int] = {}
        for p in self._proposals.values():
            by_state[p.state] = by_state.get(p.state, 0) + 1
        high_value = [vars(p) for p in self._proposals.values()
                      if p.confidence >= 0.7 and p.state == "PROPOSED"]
        return {
            "digest_id": f"kd-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}",
            "total": len(self._proposals),
            "by_state": by_state,
            "new_high_value_candidates": high_value[:10],
            "conflicts": [vars(p) for p in self._proposals.values()
                          if "conflict" in p.proposed_action.lower()],
            "stale_or_invalid": [vars(p) for p in self._proposals.values()
                                 if p.state == "EXPIRED"],
            "proposals_created": by_state.get("PROPOSED", 0) + by_state.get("SEEN", 0),
            "proposals_expired": by_state.get("EXPIRED", 0),
        }

    def _save(self) -> None:
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with self.state_path.open("w", encoding="utf-8") as f:
                for p in self._proposals.values():
                    f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
