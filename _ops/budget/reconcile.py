#!/usr/bin/env python3
"""reconcile.py — تطبیقِ پولِ نشسته با attribution، فقط از CSVِ انسانی‌دراپ‌شده (offline).

هیچ bank API، هیچ scrape، هیچ شبکه. ورودی: `_ops/reconcile/*.csv` با ستون‌های
  date, amount_aud, lead_id, source  (قفل‌شدهٔ verdict آری).

قاعدهٔ محافظه‌کارِ fail-closed (ضدِ گیم): تطبیق فقط وقتی CONFIRMED می‌شود که هر چهار برقرار باشند —
  lead_id موجود · attribution در وضعیتِ CLAIMED · مبلغ دقیقاً match · تاریخِ پرداخت در پنجرهٔ ۷ روز.
هر تطبیقِ ناقص/مبهم/خارج‌ازپنجره/بی‌lead_id/دابل → CONFIRMED نمی‌شود؛ UNMATCHED علامت می‌خورد و
در گزارش می‌آید. پولِ تأییدنشده هرگز fitness را تکان نمی‌دهد. CONFIRMED را فقط همین job می‌نویسد.
"""
from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib       # noqa: E402
import attribution  # noqa: E402

RECONCILE_DIR = opslib.OPS / "reconcile"
COLUMNS = ("date", "amount_aud", "lead_id", "source")
AMOUNT_TOL = 0.005   # نیم‌سنت = عملاً exact


def _read_rows(reconcile_dir=None) -> list[dict]:
    d = Path(reconcile_dir) if reconcile_dir else RECONCILE_DIR
    rows: list[dict] = []
    if not d.exists():
        return rows
    for csvf in sorted(d.glob("*.csv")):
        try:
            with open(csvf, "r", encoding="utf-8-sig", newline="") as fh:
                for i, r in enumerate(csv.DictReader(fh), start=2):
                    rows.append({"_file": csvf.name, "_line": i,
                                 "date": (r.get("date") or "").strip(),
                                 "amount_aud": (r.get("amount_aud") or "").strip(),
                                 "lead_id": (r.get("lead_id") or "").strip(),
                                 "source": (r.get("source") or "").strip()})
        except OSError as e:
            opslib.alert([f"reconcile: cannot read {csvf.name}: {e}"])
    return rows


def _within_window(base_date: str, pay_date: str, days: int) -> bool:
    try:
        d0 = datetime.date.fromisoformat(base_date)
        d1 = datetime.date.fromisoformat(pay_date)
    except (ValueError, TypeError):
        return False
    return 0 <= (d1 - d0).days <= days


def run(reconcile_dir=None, write: bool = True) -> dict:
    latest = attribution.fold()
    rows = _read_rows(reconcile_dir)
    confirmed: list[dict] = []
    unmatched: list[dict] = []
    double: list[dict] = []
    seen = set()   # dedup درون همین ران

    for row in rows:
        lead = row["lead_id"]
        rec = latest.get(lead) if lead else None
        try:
            amt = float(row["amount_aud"])
        except ValueError:
            amt = None

        if not lead:
            reason = "no-lead_id"
        elif amt is None:
            reason = "bad-amount"
        elif rec is None:
            reason = "unknown-lead_id"
        elif rec.get("state") in attribution.CONFIRMED_STATES or lead in seen:
            # دابل‌کلیمِ یک دلار → گزارش + alert؛ CONFIRMEDِ اصلی سرِ جایش می‌ماند (هرگز override/اعتبارِ دوباره)
            double.append({**row, "reason": "double-claim"})
            if write:
                opslib.alert([f"reconcile double-claim: {lead} ({row['_file']}:{row['_line']}) — قبلاً CONFIRMED، نادیده"])
            continue
        elif rec.get("state") == "CONFLICT":
            reason = "in-conflict"
        elif rec.get("state") != "CLAIMED":
            reason = f"not-claimed(state={rec.get('state')})"
        else:
            claim_amt = float(rec.get("amount_aud") or 0)
            base_date = rec.get("claim_date") or rec.get("decision_date") or ""
            if abs(claim_amt - amt) > AMOUNT_TOL:
                reason = f"amount-mismatch(claim={claim_amt},csv={amt})"
            elif not _within_window(base_date, row["date"], attribution.ATTR_WINDOW_DAYS):
                reason = "out-of-window(>7d یا پیش از تصمیم)"
            else:
                cell = rec.get("cell", "unknown")
                if write:
                    attribution.confirm(lead, cell, amt, {
                        "date": row["date"], "source": row["source"], "lead_id": lead,
                        "file": row["_file"], "line": row["_line"]})
                seen.add(lead)
                confirmed.append({"attribution_id": lead, "cell": cell, "amount_aud": amt})
                continue
        unmatched.append({**row, "reason": reason})

    rev = attribution.confirmed_revenue()
    report = {
        "ts": opslib.now_iso(), "rows_read": len(rows),
        "confirmed": confirmed, "unmatched": unmatched, "double_claims": double,
        "attribution_coverage": rev["attribution_coverage"],
        "revenue_by_cell": rev["by_cell"],
        "note": "فقط CONFIRMEDِ match‌خورده به fitness می‌رود؛ UNMATCHED/CONFLICT هرگز",
    }
    if write:
        with opslib.LockedJson(opslib.STATE_DIR / "reconcile-latest.json") as lj:
            lj.write(report)
    return report


if __name__ == "__main__":
    import json
    print(json.dumps(run(write="--dry" not in sys.argv), ensure_ascii=False, indent=2))
