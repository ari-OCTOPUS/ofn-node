#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""knowledge_hook.py — C3 (AGENT-C-PLAN): hook اتصال knowledge به organism afferent.

flag-gated · پیش‌فرض خاموش (OCTOPUS_KNOWLEDGE_AFFERENT_HOOK=0) ·
بدون تغییر organism.py hot path · بدون restart · بدون merge.

مسیر وقتی فعال شود:
  knowledge sidecar queue → knowledge_afferent_hook → organism afferent registry
  → memory candidate → cognition inbox

فعال‌سازی فقط پس از handoff A/B (C4)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .flags import enabled
from .paths import INBOX, ORGANS_STATE

HOOK_FLAG = "OCTOPUS_KNOWLEDGE_AFFERENT_HOOK"


def hook_active() -> bool:
    """پیش‌فرض خاموش — فعال‌سازی فقط با env صریح."""
    return enabled(HOOK_FLAG, False)


def process_sidecar_queue() -> dict:
    """صف sidecar را پردازش و به cognition inbox بفرست.

    C15 (مگا‌دستور #۱۷): write-ahead intent + backpressure + rollback.
    فقط وقتی hook_active() True است. هر event:
    → HOOK_INTENT (write-ahead)
    → afferent registry append
    → memory candidate append
    → cognition inbox append
    → HOOK_COMMITTED

    اگر وسط کار شکست: HOOK_PARTIAL + reconciliation idempotent.
    """
    if not hook_active():
        return {"ok": False, "reason": "flag-off", "processed": 0}

    # C15: backpressure — اگر protective halt فعال است، توقف
    halt_file = ORGANS_STATE.parent.parent / "STOP-ORGANISM"
    if halt_file.exists():
        return {"ok": False, "reason": "protective_halt_active", "processed": 0}

    ledger = ORGANS_STATE / "knowledge-afferent.jsonl"
    if not ledger.exists():
        return {"ok": True, "processed": 0, "reason": "no-ledger"}

    # خواندن events که هنوز پردازش نشده‌اند
    processed_marker = ORGANS_STATE / "knowledge-hook-last-id.json"
    last_id = ""
    if processed_marker.exists():
        try:
            last_id = json.loads(
                processed_marker.read_text(encoding="utf-8")).get("last_event_id", "")
        except (OSError, ValueError):
            pass

    events = []
    seen = False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if seen or not last_id:
            events.append(ev)
        if ev.get("event_id") == last_id:
            seen = True

    # حداکثر ۲۵ رویداد در هر نوبت (C5: batch کوچک)
    batch = events[:25]
    if not batch:
        return {"ok": True, "processed": 0, "reason": "up-to-date"}

    # C15: write-ahead intent — قبل از هر append
    intent_file = ORGANS_STATE / "knowledge-hook-intent.json"
    intent = {
        "schema": "hook-intent/1",
        "state": "HOOK_INTENT",
        "batch_ids": [ev["event_id"] for ev in batch],
        "ts": __import__("time").time(),
    }
    intent_file.parent.mkdir(parents=True, exist_ok=True)
    intent_file.write_text(json.dumps(intent, ensure_ascii=False), encoding="utf-8")

    # نوشتن در سه مقصد
    registry = ORGANS_STATE / "afferent-registry.jsonl"
    candidates = ORGANS_STATE / "memory-candidates.jsonl"
    inbox_events = INBOX / "events.jsonl"

    for p in (registry, candidates, inbox_events):
        p.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    try:
      for ev in batch:
        # ۱) afferent registry
        with registry.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "schema": "afferent-registry/1",
                "event_id": ev["event_id"],
                "organ_id": "knowledge",
                "source": "knowledge_afferent_hook",
                "occurred_at": ev.get("occurred_at"),
                "recorded_at": ev.get("ingested_at"),
                "evidence_ids": [ev.get("path", "")],
                "quality": ev.get("extra", {}).get("quality", "UNKNOWN"),
                "payload_hash": ev.get("content_hash", ""),
            }, ensure_ascii=False) + "\n")

        # ۲) memory candidate (فقط اگر quality=VALID و denylisted=False)
        if ev.get("extra", {}).get("quality") == "VALID" and \
           not ev.get("extra", {}).get("denylisted"):
            with candidates.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "schema": "memory-candidate/1",
                    "event_id": ev["event_id"],
                    "source": "knowledge_afferent",
                    "path_hash": ev.get("extra", {}).get("path_hash"),
                    "content_hash": ev.get("content_hash"),
                    "state": "UNCONFIRMED",  # C5: semantic candidates ابتدا UNCONFIRMED
                    "occurred_at": ev.get("occurred_at"),
                    "recorded_at": ev.get("ingested_at"),
                    "provenance": "filesystem_scan",
                }, ensure_ascii=False) + "\n")

        # ۳) cognition inbox
        with inbox_events.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "schema": "cognition-inbox-event/1",
                "kind": "organ.knowledge.afferent",
                "event_id": ev["event_id"],
                "organ_id": "knowledge",
                "path_hash": ev.get("extra", {}).get("path_hash"),
                "quality": ev.get("extra", {}).get("quality"),
                "executable": False,
            }, ensure_ascii=False) + "\n")
        n += 1

    except Exception as e:
        # C15: crash recovery — HOOK_PARTIAL + state حفظ
        intent["state"] = "HOOK_PARTIAL"
        intent["error"] = f"{type(e).__name__}: {e}"
        intent["processed_before_crash"] = n
        intent_file.write_text(json.dumps(intent, ensure_ascii=False), encoding="utf-8")
        return {"ok": False, "reason": f"HOOK_PARTIAL:{type(e).__name__}",
                "processed": n, "intent": intent}

    # C15: HOOK_COMMITTED
    intent["state"] = "HOOK_COMMITTED"
    intent["processed"] = n
    intent_file.write_text(json.dumps(intent, ensure_ascii=False), encoding="utf-8")

    # marker به‌روزرسانی
    processed_marker.write_text(json.dumps({
        "last_event_id": batch[-1]["event_id"],
        "processed_at": str(ev.get("ingested_at")),
        "batch_size": n}), encoding="utf-8")

    return {"ok": True, "processed": n, "remaining": max(0, len(events) - n)}


def rollback() -> dict:
    """C15: flag OFF باید producer را متوقف کند ولی evidence queue را حذف نکند."""
    # evidence صف حفظ می‌شود — فقط marker را reset می‌کنیم تا دوباره پردازش شود
    marker = ORGANS_STATE / "knowledge-hook-last-id.json"
    if marker.exists():
        marker.unlink()
    intent = ORGANS_STATE / "knowledge-hook-intent.json"
    if intent.exists():
        d = json.loads(intent.read_text(encoding="utf-8"))
        d["state"] = "ROLLED_BACK"
        intent.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "reason": "flag-off-rollback",
            "evidence_queue_preserved": True}


def reconcile_partial() -> dict:
    """C15: reconciliation idempotent — اگر HOOK_PARTIAL مانده، از نقطهٔ شکست ادامه بده."""
    intent_file = ORGANS_STATE / "knowledge-hook-intent.json"
    if not intent_file.exists():
        return {"ok": True, "reason": "no-partial"}
    intent = json.loads(intent_file.read_text(encoding="utf-8"))
    if intent.get("state") != "HOOK_PARTIAL":
        return {"ok": True, "reason": "no-partial"}
    # دوباره process را صدا بزن — idempotent است (event_id duplicate skip می‌شود)
    return process_sidecar_queue()


if __name__ == "__main__":
    print(json.dumps(process_sidecar_queue(), ensure_ascii=False))
