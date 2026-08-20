#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""writer_lease.py — قفل نویسندهٔ واحد OCTOPUS (T37، دستور مالک #۶).

PROPOSAL — این فایل تا تصویب و پذیرش هر دو ایجنت فعال/اجرا نمی‌شود.
قرارداد دستور #۶ §۴:

  lease_path  : _ops/state/locks/octopus-writer.lock
  lease_fields: agent_id, session_id, acquired_at, ttl_seconds, scope

قواعد:
  - acquire فقط با ایجاد اتمیک (O_CREAT|O_EXCL) موفق می‌شود.
  - lease منقضی‌شده صریح takeover می‌شود: نسخهٔ stale با مهر زمان کنار
    می‌رود (تاریخ پاک نمی‌شود) و قفل تازه گرفته می‌شود.
  - lease زندهٔ دیگری ⇒ خروجی HOLD (exit 3): ایجنت دوم فقط read-only.
  - release فقط توسط دارنده یا با --force توسط مالک.

CLI:
  python _ops/writer_lease.py acquire --agent B --session s1 --ttl 900 --scope ledger,evidence,git
  python _ops/writer_lease.py renew   --agent B --session s1
  python _ops/writer_lease.py release --agent B --session s1
  python _ops/writer_lease.py inspect
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
LOCK_PATH = _ROOT / "state" / "locks" / "octopus-writer.lock"
SCHEMA = "octopus-writer-lease/1"


def _now() -> float:
    return time.time()


def _read(path: Path | None = None) -> dict | None:
    # مسیر باید پویا حل شود (نه default-arg) تا override در تست‌ها هم برقرار باشد
    target = path or LOCK_PATH
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _expired(rec: dict) -> bool:
    return _now() - float(rec.get("acquired_at", 0)) > float(rec.get("ttl_seconds", 0))


def inspect() -> int:
    rec = _read()
    if rec is None:
        print(json.dumps({"held": False}))
        return 0
    out = dict(rec)
    out["held"] = True
    out["expired"] = _expired(rec)
    out["age_s"] = round(_now() - float(rec.get("acquired_at", 0)), 1)
    print(json.dumps(out, ensure_ascii=False))
    return 0


def acquire(agent: str, session: str, ttl: int, scope: str) -> int:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = _read()
    if rec is not None and not _expired(rec):
        holder_same = rec.get("agent_id") == agent and rec.get("session_id") == session
        if holder_same:  # renew ضمنی
            return _write_renew(rec, agent, session, ttl)
        print(json.dumps({"status": "HOLD", "held_by": rec.get("agent_id"),
                          "session": rec.get("session_id"),
                          "remaining_s": round(float(rec["acquired_at"]) + float(rec["ttl_seconds"]) - _now(), 1)}))
        return 3
    if rec is not None and _expired(rec):
        stale = LOCK_PATH.with_name(f"{LOCK_PATH.name}.stale.{int(_now())}")
        os.replace(LOCK_PATH, stale)  # تاریخ منقضی کنار می‌رود، حذف نمی‌شود
        print(json.dumps({"status": "STALE_ARCHIVED", "stale_path": str(stale)}))
    payload = {"schema": SCHEMA, "lease_id": uuid.uuid4().hex,
               "agent_id": agent, "session_id": session,
               "acquired_at": round(_now(), 3), "ttl_seconds": ttl,
               "scope": [s.strip() for s in scope.split(",") if s.strip()]}
    fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False))
    print(json.dumps({"status": "ACQUIRED", **payload}, ensure_ascii=False))
    return 0


def _write_renew(rec: dict, agent: str, session: str, ttl: int) -> int:
    rec.update({"renewed_at": round(_now(), 3), "ttl_seconds": ttl,
                "agent_id": agent, "session_id": session})
    tmp = LOCK_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, LOCK_PATH)
    print(json.dumps({"status": "RENEWED"}, ensure_ascii=False))
    return 0


def renew(agent: str, session: str, ttl: int) -> int:
    rec = _read()
    if rec is None or rec.get("agent_id") != agent or rec.get("session_id") != session:
        print(json.dumps({"status": "DENIED", "why": "not-holder"}))
        return 4
    return _write_renew(rec, agent, session, ttl)


def release(agent: str, session: str, force: bool) -> int:
    rec = _read()
    if rec is None:
        print(json.dumps({"status": "NOT_HELD"}))
        return 0
    if not force and (rec.get("agent_id") != agent or rec.get("session_id") != session):
        print(json.dumps({"status": "DENIED", "why": "not-holder"}))
        return 4
    released = LOCK_PATH.with_name(f"{LOCK_PATH.name}.released.{int(_now())}")
    os.replace(LOCK_PATH, released)  # سوابق آزادسازی حفظ می‌شوند
    print(json.dumps({"status": "RELEASED", "archive": str(released)}))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("acquire")
    a.add_argument("--agent", required=True)
    a.add_argument("--session", required=True)
    a.add_argument("--ttl", type=int, default=900)
    a.add_argument("--scope", default="ledger,evidence,budgets,git")
    r = sub.add_parser("renew")
    r.add_argument("--agent", required=True)
    r.add_argument("--session", required=True)
    r.add_argument("--ttl", type=int, default=900)
    q = sub.add_parser("release")
    q.add_argument("--agent", required=True)
    q.add_argument("--session", required=True)
    q.add_argument("--force", action="store_true")
    sub.add_parser("inspect")
    args = ap.parse_args()
    sys.exit({"acquire": lambda: acquire(args.agent, args.session, args.ttl, args.scope),
              "renew": lambda: renew(args.agent, args.session, args.ttl),
              "release": lambda: release(args.agent, args.session, args.force),
              "inspect": inspect}[args.cmd]())
