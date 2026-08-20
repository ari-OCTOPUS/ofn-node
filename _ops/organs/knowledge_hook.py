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

    فقط وقتی hook_active() True است. هر event:
    → ثبت در afferent registry (state/afferent-registry.jsonl)
    → memory candidate (state/memory-candidates.jsonl)
    → cognition inbox (cognition_inbox/events.jsonl)
    """
    if not hook_active():
        return {"ok": False, "reason": "flag-off", "processed": 0}

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

    # نوشتن در سه مقصد
    registry = ORGANS_STATE / "afferent-registry.jsonl"
    candidates = ORGANS_STATE / "memory-candidates.jsonl"
    inbox_events = INBOX / "events.jsonl"

    for p in (registry, candidates, inbox_events):
        p.parent.mkdir(parents=True, exist_ok=True)

    n = 0
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

        # ۲) memory candidate (فقط اگر quality=CLEAN و denylisted=False)
        if ev.get("extra", {}).get("quality") == "CLEAN" and \
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

    # marker به‌روزرسانی
    processed_marker.write_text(json.dumps({
        "last_event_id": batch[-1]["event_id"],
        "processed_at": str(ev.get("ingested_at")),
        "batch_size": n}), encoding="utf-8")

    return {"ok": True, "processed": n, "remaining": max(0, len(events) - n)}


if __name__ == "__main__":
    print(json.dumps(process_sidecar_queue(), ensure_ascii=False))
