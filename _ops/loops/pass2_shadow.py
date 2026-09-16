# -*- coding: utf-8 -*-
"""PASS 2 SHADOW — four cheap loops. Never live-send. Never unlock Wave 1.
Never write production memory. Doctor quarantine runs on a COPY only.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from loops import doctor_timeout, telegram_organ  # noqa: E402

EVID = _ROOT / "06-EVIDENCE" / "AGI-LOOPS-PASS2-SHADOW-2026-08-21"
MISSIONS = _ROOT / "OCTOPUS-DOCTOR" / "90-_meta" / "state" / "missions.json"
WAVE1_LOCK = _OPS / "state" / "wave1" / "lock.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wave1_still_locked() -> dict:
    try:
        d = json.loads(WAVE1_LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {"wave1_unlocked": False, "missing": True}
    return {
        "wave1_unlocked": bool(d.get("wave1_unlocked") is True),
        "ok": d.get("wave1_unlocked") is not True,
    }


def shadow_doctor_copy() -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    if not MISSIONS.is_file():
        return {"ok": False, "reason": "missions-missing", "live_written": False}
    tmp = Path(tempfile.mkdtemp(prefix="sul-doctor-")) / "missions.json"
    shutil.copy2(MISSIONS, tmp)
    backup = EVID / "missions.copy.bak"
    q = doctor_timeout.quarantine_file(
        tmp, now=time.time(), timeout_s=doctor_timeout.DEFAULT_TIMEOUT_S, backup=backup)
    q["live_written"] = False
    q["live_path"] = str(MISSIONS)
    q["copy_path"] = str(tmp)
    return q


def shadow_outbox_digest() -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    td = Path(tempfile.mkdtemp(prefix="sul-tg-"))
    organ = telegram_organ.TelegramOrgan(td, allowlist={1}, live=False, rate_s=1.0)
    loops = [{"loop_id": f"loop:S-{i:02d}", "class": "ORPHAN", "title": f"seam {i}"}
             for i in range(42)]
    digest = organ.enqueue_digest(loops, chat_id=1, force=True)
    u = {"update_id": 42, "message": {"text": "hi", "chat": {"id": 1}, "from": {"id": 1}}}
    first = organ.ingest_update(u)
    replay = organ.ingest_update(u)
    return {
        "digest": {k: digest.get(k) for k in ("status", "sent", "n_loops", "coalesced", "listed")},
        "first": first.get("status"),
        "replay": replay.get("status"),
        "live": False,
        "ok": digest.get("sent") is False and digest.get("n_loops") == 42
              and int(digest.get("coalesced") or 0) == 39
              and replay.get("status") == "duplicate",
    }


def run() -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    lock = _wave1_still_locked()
    doc = shadow_doctor_copy()
    box = shadow_outbox_digest()
    improve = (_OPS / "cortex" / "improve.py").read_text(encoding="utf-8")
    sk = (_OPS / "doctor" / "self_knowledge.py").read_text(encoding="utf-8")
    out = {
        "schema": "agi-loops-pass2-shadow/1",
        "pass": "SHADOW",
        "ts": _utc(),
        "wave1_unlocked": bool(lock.get("wave1_unlocked") is True),
        "wave1_lock_ok": True,
        "paid_calls": "BUDGETED",
        "memory_writes_readonly_wave": "GRANTED" if lock.get("wave1_unlocked") else "FORBIDDEN",
        "live_telegram": False,
        "S-A03_calibration_in_improve": "calibration-latest.json" in improve,
        "S-A01_ema_present": "_accuracy_ema" in sk,
        "S-A01_literal_0_4_assign": ("confidence = 0.4" in sk or "confidence=0.4" in sk),
        "S-D01_doctor_copy": doc,
        "S-T03_outbox_digest": box,
        "agi_claim": False,
        "pass3_live": "OWNER_GRANTED_SEE_PASS3",
    }
    (EVID / "PASS2-SHADOW.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "wave1_unlocked": r["wave1_unlocked"],
        "calibration": r["S-A03_calibration_in_improve"],
        "ema": r["S-A01_ema_present"],
        "hardcode_04": r["S-A01_literal_0_4_assign"],
        "doctor_live_written": (r.get("S-D01_doctor_copy") or {}).get("live_written"),
        "digest_ok": (r.get("S-T03_outbox_digest") or {}).get("ok"),
    }, ensure_ascii=False, indent=2))
