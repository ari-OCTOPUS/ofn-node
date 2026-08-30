"""test_adapters_obsidian.py — telegram/webapp/obsidian verification.

no network، no real telegram.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "intel_spine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ["OCTOPUS_INTERACTION_LOG"] = "1"

import intel_spine
import telegram_adapter
import webapp_adapter
import obsidian_sync

_TMP = Path(tempfile.mkdtemp())
intel_spine._STATE = _TMP / "intel_spine_test"

results = {"pass": 0, "fail": 0, "details": []}

def check(name, cond):
    if cond:
        results["pass"] += 1
        results["details"].append(f"  ✅ {name}")
    else:
        results["fail"] += 1
        results["details"].append(f"  ❌ {name}")

def main():
    # ─── Telegram adapter ───
    update = {"message": {"text": "/now", "chat": {"id": 12345}, "from": {"id": 9999999999}}}
    eid = telegram_adapter.log_incoming(update)
    check("telegram log_incoming", eid is not None)

    # PII نباید raw باشد
    events = intel_spine.read_recent("events", 5)
    import json
    raw_found = any("9999999999" in json.dumps(e) for e in events) if events else False
    check("telegram no raw chat_id in events", not raw_found)

    eid2 = telegram_adapter.log_outgoing(12345, "status: ok", stream="center-status")
    check("telegram log_outgoing", eid2 is not None)

    eid3 = telegram_adapter.log_callback("ok:diff:doctor-pulse", from_id=9999999999, chat_id=12345)
    check("telegram log_callback", eid3 is not None)

    # /stop باید allow + is_stop=True
    stop_update = {"message": {"text": "/stop", "chat": {"id": 12345}, "from": {"id": 9999999999}}}
    eid4 = telegram_adapter.log_incoming(stop_update)
    check("telegram /stop logged", eid4 is not None)

    # ─── WebApp adapter ───
    wid = webapp_adapter.log_request("GET", "/api/state", status_code=200, actor="owner", is_mutating=False)
    check("webapp log_request read-only", wid is not None)

    wid2 = webapp_adapter.log_request("POST", "/save", status_code=200, actor="owner", is_mutating=True)
    check("webapp log_request mutating", wid2 is not None)

    # ─── Obsidian sync ───
    vault = _TMP / "vault"

    # truth note
    ok = obsidian_sync.sync_truth_note(vault, {"head": "abc123", "tick": "ok", "paid_calls": 527})
    check("obsidian truth note created", ok)
    truth_path = vault / "Octopus" / "CURRENT-TRUTH.md"
    check("obsidian truth note exists", truth_path.exists())

    # memory model note
    ok2 = obsidian_sync.sync_memory_model_note(vault)
    check("obsidian memory note created", ok2)
    mem_path = vault / "Octopus" / "Memory" / "Memory-Model.md"
    check("obsidian memory note exists", mem_path.exists())

    # idempotent update (no duplicate)
    obsidian_sync.sync_truth_note(vault, {"head": "new123"})
    content = truth_path.read_text("utf-8")
    marker_count = content.count(obsidian_sync.START_MARKER)
    check("obsidian idempotent (one marker block)", marker_count == 1)
    check("obsidian updated content", "new123" in content)

    # manual content preserved
    manual_note = vault / "Octopus" / "manual.md"
    manual_note.parent.mkdir(parents=True, exist_ok=True)
    manual_note.write_text("# My Manual Note\n\nThis is hand-written by owner.\n", "utf-8")
    obsidian_sync.safe_update_note(manual_note, "auto content here", "test")
    manual_content = manual_note.read_text("utf-8")
    check("obsidian manual preserved + appended", "hand-written by owner" in manual_content and "auto content here" in manual_content)

    # no raw PII in obsidian
    check("obsidian no chat_id", "9999999999" not in truth_path.read_text("utf-8"))

    print("test_adapters_obsidian — telegram + webapp + obsidian")
    for d in results["details"]:
        print(d)
    print(f"\nPass: {results['pass']}, Fail: {results['fail']}")
    return results["fail"] == 0

if __name__ == "__main__":
    ok = main()
    shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(0 if ok else 1)
