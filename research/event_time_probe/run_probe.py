#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_probe.py — اجرای PRE-REG-EVENT-TIME-PROBE-2026-08-20 (امضاشدهٔ Ed25519).

پیش‌شرط‌ها (همه fail-closed):
  - امضای payload معتبر با کلید لنگر
  - پین FX تازه (≤24h) — با authority همین payload امضاشده
  - دقیقاً یک فراخوان · سقف AU$0.01 · بدون retry
خروجی: رسید کامل (server_created، skew، معنای timestamp) + رویداد spine
با event_time_source=provider_server_created (از کد T52 در همین پروسه).
متن پاسخ بعد از hash دور ریخته می‌شود."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "_ops"))
sys.path.insert(0, str(_ROOT / "_ops" / "cortex"))
sys.path.insert(0, str(_ROOT / "_ops" / "owner-signing"))

PAYLOAD = _ROOT / "02-DECISIONS/PAYLOAD-EVENT-TIME-PROBE-2026-08-20.json"
SIG = Path(str(PAYLOAD) + ".sig")
PUB = _ROOT / "_ops/owner-signing/octopus-owner-ed25519-public.pem"
OUT = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-2026-08-20.json"
RUN_ID_PATH = _ROOT / "06-EVIDENCE/EVENT-TIME-PROBE-RUN-ID.txt"


def _die(why: str) -> None:
    OUT.write_text(json.dumps({"status": "BLOCKED", "why": why,
                               "ts": datetime.now(timezone.utc).isoformat()},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"status": "BLOCKED", "why": why}))
    sys.exit(3)


def main() -> None:
    # ۱) امضا + لنگر
    from check_anchor import check
    ok, _, _ = check()
    if not ok:
        _die("trust-anchor-mismatch")
    v = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-rawin",
                        "-inkey", str(PUB), "-in", str(PAYLOAD), "-sigfile", str(SIG)],
                       capture_output=True, text=True)
    if v.returncode != 0 or "Verified" not in v.stdout:
        _die("payload-signature-invalid")
    card = json.loads(PAYLOAD.read_text(encoding="utf-8"))

    # ۲) FX تازه
    from cost_receipt import fx_pinned_fresh
    okfx, whyfx = fx_pinned_fresh()
    if not okfx:
        _die(f"fx-stale:{whyfx}")

    # ۳) run_id immutable
    if RUN_ID_PATH.exists():
        run_id = RUN_ID_PATH.read_text(encoding="utf-8").strip()
    else:
        run_id = str(uuid.uuid4())
        RUN_ID_PATH.write_text(run_id, encoding="utf-8")
    import os
    os.environ["OCTOPUS_RUN_ID"] = run_id

    # ۴) یک فراخوان (کد T50/T52 فعال در همین پروسه)
    import model_router as mr
    t0 = time.time()
    out = mr.ask(task=card["task_id"],
                 prompt="Reply with exactly one word: ok",
                 max_tokens=5, tier="primary", temperature=0.0)
    t_done = time.time()
    sc = out.get("server_created")
    receipt = {
        "schema": "event-time-probe/1",
        "status": "OK" if out.get("ok") else "CALL_FAILED",
        "task_id": card["task_id"], "run_id": run_id,
        "calls": 1, "cap_aud": card["hard_stop_aud"],
        "local_request_ts": datetime.fromtimestamp(t0, timezone.utc).isoformat(timespec="milliseconds"),
        "local_receipt_ts": datetime.fromtimestamp(t_done, timezone.utc).isoformat(timespec="milliseconds"),
        "server_created": sc,
        "server_created_iso": (datetime.fromtimestamp(int(sc), tz=timezone.utc).isoformat(timespec="seconds")
                               if sc is not None else None),
        "text_sha256": hashlib.sha256(str(out.get("text") or "").encode()).hexdigest()[:16],
        "output_discarded": True,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    if sc is not None:
        sc_ts = int(sc)
        receipt["skew_vs_request_s"] = round(sc_ts - t0, 3)
        receipt["skew_vs_receipt_s"] = round(sc_ts - t_done, 3)
        # معنای فیلد: created به کدام لحظه نزدیک‌تر است؟ (حدس نمی‌زنیم — می‌سنجیم)
        receipt["created_semantics_probe"] = (
            "closer_to_request" if abs(sc_ts - t0) < abs(sc_ts - t_done) else "closer_to_receipt")
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
