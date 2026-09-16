#!/usr/bin/env python3
"""OP-4 چک ۳ — تست sandbox منطق sync_store_watch با MARKER ساختگی (tmp فقط).

قرارداد: هیچ MARKER واقعی روی 138 ساخته نمی‌شود؛ ssh واقعی صدا زده نمی‌شود.
روش: ایمپورت ماژول واقعی drive_loops، سپس monkeypatch روی STATE/DRIVE و
subprocess.run تا فقط مسیرِ کد را در tmp شبیه‌سازی کنیم.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"F:/backup/_ops")
import drive_loops  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="op4-sync-"))
drive_loops.STATE = TMP / "state"
drive_loops.DRIVE = drive_loops.STATE / "drive"
drive_loops.DRIVE.mkdir(parents=True, exist_ok=True)

WATCH = {"schema": "store-watch.v1", "ts_utc": "2026-09-09T00:00:00+00:00",
         "domain": {"dns_ok": True, "page_ok": True},
         "orders": {"ok": True, "total_fetched": 1, "paid_since_sep1": 1,
                    "last_order_id": "TEST-0001", "last_created": "now",
                    "first_real_order": True}}
MARKER = {"order_id": "TEST-0001", "total": "67.50",
          "financial_status": "paid", "created_at": "2026-09-09T00:00:00Z"}


class FakeProc:
    def __init__(self, payload):
        self.returncode = 0
        self.stdout = json.dumps(payload)


def fake_run(cmd, **kw):
    cmd_s = " ".join(cmd)
    if "store-watch.json" in cmd_s:
        return FakeProc(WATCH)
    if "FIRST-ORDER-MARKER.json" in cmd_s:
        return FakeProc(MARKER) if marker_present else subprocess.CompletedProcess([], 1, "", "")
    raise AssertionError("unexpected ssh target: " + cmd_s)


results = {}
local_receipt = drive_loops.STATE / "receipts" / "FIRST-ORDER-RECEIPT.json"

# A: مارکر هست + رسید محلی نیست → رسید باید ساخته شود
marker_present = True
subprocess.run = fake_run
out = drive_loops.sync_store_watch()
results["A_marker_no_receipt"] = {
    "watch_pulled": (drive_loops.STATE / "store-watch.json").exists(),
    "receipt_created": local_receipt.exists(),
    "flag": out.get("first_order_receipt_created"),
    "PASS": local_receipt.exists() and out.get("first_order_receipt_created") is True}

# B: مارکر هست + رسید محلی هست → نباید بازنویسی شود
snap = local_receipt.read_text(encoding="utf-8")
out2 = drive_loops.sync_store_watch()
results["B_receipt_exists"] = {
    "receipt_untouched": local_receipt.read_text(encoding="utf-8") == snap,
    "flag_absent": "first_order_receipt_created" not in out2,
    "PASS": local_receipt.read_text(encoding="utf-8") == snap}

# C: مارکر نیست → هیچ رسید جدیدی نه
marker_present = False
if local_receipt.exists():
    local_receipt.unlink()
out3 = drive_loops.sync_store_watch()
results["C_no_marker"] = {
    "no_receipt": not local_receipt.exists(),
    "watch_still_pulled": (drive_loops.STATE / "store-watch.json").exists(),
    "PASS": not local_receipt.exists()}

# D: محتوای رسید — فیلدهای قراردادی
marker_present = True
drive_loops.sync_store_watch()
r = json.loads(local_receipt.read_text(encoding="utf-8"))
results["D_receipt_contract"] = {
    "fields": sorted(r.keys()),
    "witness_ok": "board138 store_watch FIRST-ORDER-MARKER" in r.get("witness", ""),
    "PASS": r.get("order_id") == "TEST-0001" and r.get("total") == "67.50"
            and r.get("financial_status") == "paid"}

ok = all(v["PASS"] for v in results.values())
print(json.dumps({"tmp": str(TMP), "all_pass": ok, "results": results},
                 ensure_ascii=False, indent=1))
sys.exit(0 if ok else 1)
