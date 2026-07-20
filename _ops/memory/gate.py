#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate.py — Memory Gate: تنها مسیرِ نوشتنِ مجازِ حافظهٔ مشتق (FSM با قوانینِ trust).

FSM هر candidate: classify → scrub/guard → dedupe → grade(per COMMIT_RULES) → TTL → commit.
verbها: reject | skip | propose | commit.

قیودِ سخت (رفعِ delta-scan Q13 و مرزهای مالک):
  - **مدل/agent هرگز procedural/owner_fact را commit نمی‌کند** — فقط propose (به صفِ پیشنهاد).
    commitِ آن‌ها = فقط source=owner (یا deterministic برای procedural).
  - **self_knowledge همیشه ADVISORY** — خروجیِ خامِ LLM هرگز به‌عنوان authoritative ذخیره/بازخورد
    نمی‌شود (پایانِ حلقهٔ خودتقویت). ارتقا به GRADED فقط با external grade.
  - secret/PII خام رد می‌شود؛ محتوای privacy=owner_only از منبعِ غیرمالک رد می‌شود.
  - هیچ side-effectِ بیرونی. پشتِ فلگِ OCTOPUS_WIRE_MEMORY_GATE (پیش‌فرض خاموش → no-op، صفر DB).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "outcomes") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "outcomes"))
import taxonomy as tax  # noqa: E402

FLAG = "OCTOPUS_WIRE_MEMORY_GATE"
_SALIENCE_BAR = 0.35
_TTL_DAYS = {"self_knowledge": 30, "semantic": 90, "episodic": 30}   # procedural/owner_fact = بی‌انقضا

# secret/PII خام — رد (فقط hash/ref مجاز است، نه رازِ خام)
_SECRET_RX = re.compile(
    r"(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|xox[baprs]-|"
    r"\bpassword\b\s*[:=]|\bseed\b\s*[:=]|\bapi[_-]?key\b\s*[:=]|0x[a-fA-F0-9]{40})", re.I)


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ttl(namespace: str):
    days = _TTL_DAYS.get(namespace)
    if not days:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


class MemoryGate:
    """gateِ نوشتن. store تزریق می‌شود (تست = temp)؛ proposalها به jsonl (owner-only candidates)."""

    def __init__(self, store, proposal_path=None):
        self._store = store
        self._proposal_path = Path(proposal_path) if proposal_path else None

    def submit(self, candidate: dict) -> dict:
        """یک candidate را از FSM بگذران. خروجی: {verb, memory_id?, trust?, reason}."""
        if not flag_on():
            return {"verb": "skip", "reason": "flag-off"}
        if not isinstance(candidate, dict):
            return {"verb": "reject", "reason": "candidate must be dict"}

        # (1) classify
        ns = str(candidate.get("namespace") or "")
        if not tax.is_namespace(ns):
            return {"verb": "reject", "reason": f"unknown namespace {ns!r}"}
        source = str(candidate.get("source") or "unknown")
        content = str(candidate.get("content") or "")
        if not content.strip():
            return {"verb": "reject", "reason": "empty content"}
        privacy = candidate.get("privacy") if tax.is_privacy(candidate.get("privacy")) else "scrubbed"

        # (2) scrub / guard
        if _SECRET_RX.search(content):
            return {"verb": "reject", "reason": "secret/PII pattern — refs/hash only"}
        if privacy == "owner_only" and source != "owner":
            return {"verb": "reject", "reason": "owner_only content from non-owner source"}

        # (3) grade per COMMIT_RULES (dedupe happens at store.insert)
        rule = tax.COMMIT_RULES.get(ns, {})
        trust, verb = self._grade(ns, rule, source, candidate)
        if verb == "reject":
            return {"verb": "reject", "reason": trust}            # trust holds the reason here
        if verb == "propose":
            self._propose(candidate, ns, source, trust)
            return {"verb": "propose", "reason": "owner-only namespace — queued, not committed", "trust": trust}

        # (4) TTL  (5) commit
        rec = {"namespace": ns, "mkey": candidate.get("mkey"), "content": content,
               "trust": trust, "privacy": privacy,
               "provenance": {"source": source, "producer": candidate.get("producer"),
                              "model": candidate.get("model"), "inputs_sha": candidate.get("inputs_sha")},
               "confidence": candidate.get("confidence"), "salience": candidate.get("salience"),
               "valid_from": _utc_now_iso(), "valid_to": _ttl(ns),
               "supersedes": candidate.get("supersedes"), "created_at": _utc_now_iso()}
        try:
            mid = self._store.insert(rec)
        except ValueError as e:
            return {"verb": "reject", "reason": str(e)}
        if mid is None:
            return {"verb": "skip", "reason": "dedupe (active identical exists)"}
        return {"verb": "commit", "memory_id": mid, "trust": trust}

    def _grade(self, ns, rule, source, candidate):
        """(trust, verb). verb ∈ commit|propose|reject. trust در reject حاملِ دلیل است."""
        committer = rule.get("committer")
        if committer in ("owner_only", "owner_or_deterministic"):
            if source == "owner":
                return "OWNER_CONFIRMED", "commit"
            if committer == "owner_or_deterministic" and source == "deterministic":
                return "DETERMINISTIC", "commit"
            # مدل/agent فقط پیشنهاد می‌دهد — هرگز commit
            return "ADVISORY", "propose"
        if committer == "advisory_until_graded":         # self_knowledge — هرگز authoritative
            if candidate.get("external_graded") is True:
                return "GRADED", "commit"
            return "ADVISORY", "commit"
        if committer == "external_grade":                # self_claim
            return ("GRADED" if candidate.get("external_graded") else "ADVISORY"), "commit"
        if committer == "scrub_salience_bar":            # semantic
            sal = candidate.get("salience")
            try:
                sal = float(sal)
            except (TypeError, ValueError):
                sal = 0.0
            if sal >= _SALIENCE_BAR:
                return "GRADED", "commit"
            return "below salience bar", "reject"        # کم‌ارزش → drop (نه اشغالِ store)
        if committer == "auto_scrubbed":                 # episodic
            return "GRADED", "commit"
        return "unknown committer rule", "reject"

    def _propose(self, candidate, ns, source, trust):
        """owner-only candidate را به صفِ پیشنهاد بنویس (append-only)، هرگز commit."""
        if not self._proposal_path:
            return
        try:
            self._proposal_path.parent.mkdir(parents=True, exist_ok=True)
            rec = {"ts": _utc_now_iso(), "namespace": ns, "mkey": candidate.get("mkey"),
                   "source": source, "proposed_trust": trust,
                   "content_preview": str(candidate.get("content"))[:200],
                   "note": "owner-only namespace — needs owner confirmation, NOT committed"}
            with open(self._proposal_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
