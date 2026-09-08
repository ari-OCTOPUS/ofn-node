#!/usr/bin/env python3
"""pin-fx-daily.py — پینِ روزانهٔ FX از RBA F11.1 (رویهٔ رأی مالک FX-1، خودکارسازی:
رأی «همرو اجازه داری» 2026-09-08).

fail-closed و idempotent:
  exit 0  = پینِ امروز نوشته و گیت سبز (یا از قبل همین نرخِ امروز پین بوده)
  exit 2  = ردیفِ امروز هنوز منتشر نشده (RBA ~16:30 AEST) — دوباره بعداً
  exit 3  = خطا (شبکه/پارس/گیت) — هیچ تغییری روی فایلِ زنده نمی‌ماند (rollback خودکار)

هیچ تاریخی جعل نمی‌شود؛ anchor همیشه «<روزِ داده>T06:00:00Z» (نرخِ 4pm AEST).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

OPS = Path(r"F:/backup/_ops")
PIN_PATH = OPS / "cortex" / "pricing_pinned.json"
WEDGE = OPS / "state" / "wedge"
LANE = Path(r"F:/backup/09-LANES/FAULT-LLMLEARN-20260908")
URL = "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv"
ROW_RE = re.compile(r"^(\d{2}-[A-Za-z]{3}-\d{4}),([01]\.\d{3,5})")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}


def _parse_row_date(s: str) -> date:
    d, mon, y = s.split("-")
    return date(int(y), MONTHS[mon[:3].title()], int(d))


def main() -> int:
    today = date.today()
    stamp = today.strftime("%Y%m%d")
    WEDGE.mkdir(parents=True, exist_ok=True)
    csv_path = WEDGE / f"rba-f111-fetch-{stamp}.csv"

    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (octopus-fx-pin)"})
    with urllib.request.urlopen(req, timeout=45) as r:
        csv_path.write_bytes(r.read())
    rows = [m.groups() for line in csv_path.read_text("utf-8", "replace").splitlines()
            if (m := ROW_RE.match(line.strip()))]
    if not rows:
        print("EXIT3: no data rows parsed")
        return 3
    row_date_s, aud_usd = rows[-1]
    row_date = _parse_row_date(row_date_s)
    rate = round(1.0 / float(aud_usd), 5)
    receipt_id = hashlib.sha256(csv_path.read_bytes()).hexdigest()[:16]

    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    rec = pin.get("fx_record") or {}
    already = (str(rec.get("fx_source_id", "")).endswith(row_date_s)
               and abs(float(rec.get("fx_rate_usd_to_aud", -1)) - rate) < 1e-9)
    if already and row_date == today:
        print(f"EXIT0: today's pin already in place ({row_date_s}, {rate})")
        return 0
    if row_date != today:
        print(f"EXIT2: latest RBA row is {row_date_s}, today is {today.isoformat()} — not published yet")
        return 2

    bak = PIN_PATH.with_suffix(f".json.bak-fxpin-{stamp}")
    shutil.copy2(PIN_PATH, bak)
    old = PIN_PATH.read_bytes()
    try:
        pin["fx_usd_to_aud"] = rate
        pin["fx_record"] = {
            "fx_source_id": f"RBA_EXCHANGE_RATES_DAILY_{row_date_s}_F11.1",
            "fx_timestamp_utc": f"{row_date.isoformat()}T06:00:00Z",
            "fx_rate_usd_to_aud": rate,
            "FX_SOURCE_VALUE": f"AUD_USD = {aud_usd}",
            "FX_CONVERSION_METHOD": "reciprocal_of_RBA_AUD_USD",
            "owner_pin_id": f"FX-PIN-{stamp}-01",
            "receipt_id": receipt_id,
            "standing_authorization": "Owner ballot FX-1 2026-09-07 + «همرو اجازه داری» 2026-09-08; see 09-LANES/FAULT-LLMLEARN-20260908/RUNBOOK-FX-DAILY.md",
        }
        PIN_PATH.write_text(json.dumps(pin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        sys.path[:0] = [str(OPS / "budget"), str(OPS / "cortex"), str(OPS)]
        import env_loader
        env_loader.load_env()
        import cost_receipt
        ok, why = cost_receipt.fx_pinned_fresh()
        if not ok:
            PIN_PATH.write_bytes(old)
            print(f"EXIT3: gate still closed after pin ({why}) — rolled back")
            return 3

        receipt = {"schema": "fx-pin-daily.v1", "ts": datetime.now().isoformat(timespec="seconds"),
                   "date": row_date.isoformat(), "aud_usd": float(aud_usd), "fx_usd_to_aud": rate,
                   "anchor": f"{row_date.isoformat()}T06:00:00Z", "receipt_id": receipt_id,
                   "owner_pin_id": f"FX-PIN-{stamp}-01", "backup": bak.name,
                   "csv_witness": str(csv_path), "gate": "fresh"}
        (LANE / f"FX-PIN-{stamp}-RECEIPT.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"EXIT0: pinned {row_date_s} rate={rate} anchor=06:00Z gate=fresh receipt={receipt_id}")
        return 0
    except Exception as e:  # noqa: BLE001 — هر خطا: بازگشتِ فایلِ زنده
        PIN_PATH.write_bytes(old)
        print(f"EXIT3: {type(e).__name__}: {e} — rolled back")
        return 3


if __name__ == "__main__":
    sys.exit(main())
