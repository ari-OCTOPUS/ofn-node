#!/usr/bin/env python3
"""Independent reader for the Telegram shadow closure artifact."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "_ops" / "state" / "loops" / "TELEGRAM-SHADOW-RESULT.json"
TEST = ROOT / "_ops" / "tests" / "test_telegram_durable_loop.py"
SOURCES = [
    ROOT / "_ops" / "telegram_center" / "durable_loop.py",
    ROOT / "_ops" / "telegram_center" / "tg_api.py",
    ROOT / "_ops" / "telegram_center" / "center.py",
    TEST,
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    checks = []
    try:
        data = json.loads(REPORT.read_text("utf-8"))
    except Exception:
        data = {}
    events = list(data.get("events") or [])
    checks.extend([
        {"name": "shadow_report_pass", "ok": data.get("pass") is True},
        {"name": "nonempty_sample_ge_5", "ok": len(events) >= 5},
        {"name": "all_events_closed", "ok": bool(events) and all(e.get("state") == "CLOSED" for e in events)},
        {"name": "all_readbacks_verified", "ok": bool(events) and all(e.get("readback_verified") is True for e in events)},
        {"name": "all_duplicates_suppressed", "ok": bool(events) and all(e.get("duplicate_suppressed") is True for e in events)},
        {"name": "unique_event_ids", "ok": len({e.get("event_id") for e in events}) == len(events)},
        {"name": "unique_task_ids", "ok": len({e.get("task_id") for e in events}) == len(events)},
        {"name": "nonempty_task_run_ids", "ok": all(e.get("task_id") and e.get("run_id") for e in events)},
        {"name": "zero_duplicate_effects", "ok": data.get("duplicate_effects") == 0},
        {"name": "zero_fabricated_task_ids", "ok": data.get("fabricated_task_ids") == 0},
        {"name": "zero_raw_payload_persisted", "ok": data.get("raw_payload_persisted") is False},
        {"name": "uncertain_send_quarantined", "ok": (data.get("crash_recovery") or {}).get("first_state") == "NEEDS_RECONCILIATION"},
        {"name": "restart_no_resend", "ok": (data.get("crash_recovery") or {}).get("transport_attempts") == 1},
        {"name": "source_files_present", "ok": all(p.is_file() for p in SOURCES)},
    ])
    proc = subprocess.run([sys.executable, "-X", "utf8", str(TEST)], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)
    checks.append({"name": "independent_test_rerun", "ok": proc.returncode == 0,
                   "summary": next((ln for ln in reversed(proc.stdout.splitlines()) if ln.strip()), "")})
    failed = [c["name"] for c in checks if not c["ok"]]
    verdict = {
        "schema": "telegram-loop-verifier/1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent_identity": "independent-reader-process",
        "scope": "fixture-shadow-only",
        "confirmed": not failed,
        "failed_checks": failed,
        "critical_regressions": 0 if not failed else 1,
        "checks": checks,
        "production_confirmed": False,
        "production_blockers": [
            "durable flag is not enabled in live process",
            "no live process restart performed",
            "no five-event owner canary with Telegram delivery/readback",
        ],
        "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in SOURCES if p.is_file()},
        "report_hash": sha(REPORT) if REPORT.is_file() else None,
        "limitations": ["fake transport", "no external Telegram call", "no paid call"],
    }
    target = ROOT / "_ops" / "state" / "loops" / "LOOP-VERIFIER.json"
    target.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"confirmed": verdict["confirmed"], "failed_checks": failed,
                      "test_exit": proc.returncode}, ensure_ascii=False))
    return 0 if verdict["confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
