#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""admission.py — تنها مسیرِ پذیرشِ نوشتن در حافظهٔ کانونی (CL01-P2).

REUSE (نه ساخت موازی): MemoryGate (FSM) + MemoryStore (درجه‌بندی‌شده)
+ ContradictionRadar (پیش از ADMITTED). این ماژول فقط قراردادِ ورودی را
اجرا می‌کند و رسید می‌نویسد:

  fail-closed:   متادیتای اجباری ناقص ⇒ REJECTED (هرگز سکوت).
  idempotency:   idempotency_key ⇒ mkey؛ تکرار ⇒ IDEMPOTENT_SKIP.
  untrusted:     source خارج از TRUSTED_SOURCES بدون evidence_ref ⇒ REJECTED.
  quarantine:    تناقض یا خطای رادار ⇒ رکورد PENDING می‌ماند + قراردادِ قرنطینه.
  receipt:       هر تصمیم (هر نوع) یک ردیف append-only در admission-receipts.jsonl.

canonical یعنی admission_state=ADMITTED — چیز دیگری canonical نیست.
خام (raw ingest) هرگز از این ماژول عبور نمی‌کند و نباید عبور کند.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_META = ("trace_id", "parent_id", "timestamp", "actor", "source",
                 "schema_version", "idempotency_key", "confidence")
TRUSTED_SOURCES = frozenset({"owner", "deterministic"})
SCHEMA = "memory-admission.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


class Admission:
    """یک نمونه = یک مسیر پذیرش برای یک store/گیت مشخص."""

    def __init__(self, store, gate, radar=None, *, state_dir=None):
        self.store = store
        self.gate = gate
        self.radar = radar
        root = Path(state_dir) if state_dir else Path(str(getattr(store, "path", "memory.db"))).parent
        self.receipt_path = root / "admission-receipts.jsonl"
        self.quarantine_path = root / "quarantine.jsonl"

    # ── receipt ────────────────────────────────────────────────────────────
    def _receipt(self, decision: str, candidate: dict, extra: dict | None = None) -> dict:
        row = {"schema": SCHEMA, "decision": decision, "ts": _now(),
               "trace_id": candidate.get("trace_id"),
               "idempotency_key": candidate.get("idempotency_key"),
               "source": candidate.get("source"), "actor": candidate.get("actor"),
               "content_sha256": _sha(str(candidate.get("content", "")))}
        if extra:
            row.update(extra)
        _append(self.receipt_path, row)
        return row

    # ── مسیر اصلی ──────────────────────────────────────────────────────────
    def admit(self, candidate: dict) -> dict:
        candidate = dict(candidate or {})

        # (1) fail-closed روی متادیتای اجباری
        missing = [k for k in REQUIRED_META if not candidate.get(k)]
        if missing:
            return {"decision": "REJECTED", "reason": f"missing metadata: {','.join(missing)}",
                    "receipt": self._receipt("REJECTED", candidate, {"reason": "metadata-missing"})}

        # (2) منبع غیرقابل‌اعتماد بدون evidence ⇒ رد (خروجی LLM بی‌شاهد هرگز canonical نمی‌شود)
        if candidate["source"] not in TRUSTED_SOURCES and not candidate.get("evidence_ref"):
            return {"decision": "REJECTED", "reason": "untrusted source lacks evidence_ref",
                    "receipt": self._receipt("REJECTED", candidate, {"reason": "no-evidence"})}

        # (3) idempotency — mkey را از idempotency_key می‌سازیم (dedupe در store.insert)
        candidate.setdefault("namespace", "general")
        candidate["mkey"] = candidate["idempotency_key"]
        prior = None
        try:
            prior = self.store.get(candidate["namespace"], candidate["mkey"])
        except Exception:
            prior = None  # getِ ناموفق جلوی ادامه را نمی‌گیرد؛ gate نهایتاً dedupe می‌زند
        if prior is not None and str(prior.get("admission_state", "")).upper() != "RETRACTED":
            return {"decision": "IDEMPOTENT_SKIP", "memory_id": prior.get("id") or prior.get("memory_id"),
                    "reason": "idempotency_key already present",
                    "receipt": self._receipt("IDEMPOTENT_SKIP", candidate, {"reason": "duplicate"})}

        # (4) عبور از گیت FSM — همیشه دو-فازی: PENDING وارد می‌شود
        candidate["admission_state"] = "PENDING"
        res = self.gate.submit(candidate)
        verb = str(res.get("verb") or "")
        if verb == "reject":
            return {"decision": "REJECTED", "reason": res.get("reason"),
                    "receipt": self._receipt("REJECTED", candidate, {"reason": res.get("reason")})}
        if verb == "skip":
            return {"decision": "IDEMPOTENT_SKIP", "reason": res.get("reason"),
                    "receipt": self._receipt("IDEMPOTENT_SKIP", candidate, {"reason": res.get("reason")})}
        mid = res.get("memory_id")
        if verb == "quarantine" or not mid:
            # گیت خودش تناقض دیده (checker داخلی) یا propose شده — canonical نیست
            decision = "QUARANTINED" if verb == "quarantine" else "PROPOSED_NOT_CANONICAL"
            if verb == "quarantine":
                _append(self.quarantine_path, {"schema": SCHEMA, "ts": _now(),
                                               "memory_id": mid, "trace_id": candidate.get("trace_id"),
                                               "flags": [str(f)[:200] for f in (res.get("flags") or [])[:3]]})
            return {"decision": decision, "memory_id": mid, "reason": res.get("reason"),
                    "receipt": self._receipt(decision, candidate, {"reason": res.get("reason")})}

        # (5) رادار — خطای رادار هم قرنطینه است (fail-closed)؛ خودِ رکوردِ
        # تازه (mid) از نتایج کنار گذاشته می‌شود تا self-match تناقض نخواند.
        flags: list = []
        if self.radar is not None:
            try:
                flags = self.radar.check_against_store(content=str(candidate.get("content", ""))) or []
            except TypeError:
                flags = self.radar.check_against_store(str(candidate.get("content", ""))) or []
            except Exception as exc:  # noqa: BLE001 — خطای رادار ⇒ قرنطینه
                flags = [{"radar_error": type(exc).__name__}]
        flags = [f for f in flags
                 if not (isinstance(f, dict)
                         and str(f.get("contradicting_memory_id") or f.get("memory_id") or "") == str(mid))]
        if flags:
            _append(self.quarantine_path, {"schema": SCHEMA, "ts": _now(), "memory_id": mid,
                                           "trace_id": candidate.get("trace_id"),
                                           "flags": [str(f)[:200] for f in flags[:3]]})
            return {"decision": "QUARANTINED", "memory_id": mid, "reason": "contradiction-detected",
                    "flags": flags[:3],
                    "receipt": self._receipt("QUARANTINED", candidate, {"reason": "contradiction"})}

        # (6) پاک بودن ⇒ ارتقا به ADMITTED (تنها تعریف canonical)
        ok = self.gate.promote(mid)
        state = self.store.admission_state(mid) if hasattr(self.store, "admission_state") else None
        decision = "ADMITTED" if ok else "ADMIT_FAILED"
        return {"decision": decision, "memory_id": mid, "admission_state": state,
                "receipt": self._receipt(decision, candidate, {"memory_id": mid})}
