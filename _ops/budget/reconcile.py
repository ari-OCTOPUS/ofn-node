#!/usr/bin/env python3
"""reconcile.py — تطبیقِ پولِ نشسته با attribution، فقط از CSVِ انسانی‌دراپ‌شده (offline).

هیچ bank API، هیچ scrape، هیچ شبکه. ورودی: `_ops/reconcile/*.csv` با ستون‌های
  date, amount_aud, lead_id, source  (قفل‌شدهٔ verdict آری).

قاعدهٔ محافظه‌کارِ fail-closed (ضدِ گیم): تطبیق فقط وقتی CONFIRMED می‌شود که هر چهار برقرار باشند —
  lead_id موجود · attribution در وضعیتِ CLAIMED · مبلغ match (exact یا جمعِ ردیف‌ها) ·
  تاریخِ پرداخت در پنجرهٔ ۷ روز.

v2: پرداختِ جزئی — اگر چند ردیف CSV برای یک lead_id وجود داشته باشد، جمع مبالغ با
claim_amount تطبیق داده می‌شود. این اجازه می‌دهد بیعانه + مابقی (یا هر پرداختِ مرحله‌ای)
به‌درستی CONFIRMED شود. هر ردیفِ تکی هم کار می‌کند (backward-compat).

هر تطبیقِ ناقص/مبهم/خارج‌ازپنجره/بی‌lead_id/دابل → CONFIRMED نمی‌شود؛ UNMATCHED علامت می‌خورد و
در گزارش می‌آید. پولِ تأییدنشده هرگز fitness را تکان نمی‌دهد. CONFIRMED را فقط همین job می‌نویسد.
"""
from __future__ import annotations

import csv
import datetime
import sys
from collections import OrderedDict
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

    # ── v2: group rows by lead_id for partial payment support ──────────
    # Multiple CSV rows for the same lead_id → sum their amounts.
    # This allows deposit + balance (or staged payments) to match total.
    grouped: dict[str, list[dict]] = OrderedDict()
    for row in rows:
        lead = row["lead_id"]
        if lead:
            grouped.setdefault(lead, []).append(row)
        else:
            # no lead_id — immediate unmatched
            unmatched.append({**row, "reason": "no-lead_id"})

    for lead, lead_rows in grouped.items():
        rec = latest.get(lead) if lead else None

        # ── pre-checks (per lead, not per row) ─────────────────────────
        if rec is None:
            for r in lead_rows:
                unmatched.append({**r, "reason": "unknown-lead_id"})
            continue
        if rec.get("state") in attribution.CONFIRMED_STATES or lead in seen:
            for r in lead_rows:
                double.append({**r, "reason": "double-claim"})
                if write:
                    opslib.alert([f"reconcile double-claim: {lead} ({r['_file']}:{r['_line']}) — قبلاً CONFIRMED، نادیده"])
            continue
        if rec.get("state") == "CONFLICT":
            for r in lead_rows:
                unmatched.append({**r, "reason": "in-conflict"})
            continue
        if rec.get("state") != "CLAIMED":
            for r in lead_rows:
                unmatched.append({**r, "reason": f"not-claimed(state={rec.get('state')})"})
            continue

        # ── sum amounts for this lead_id ────────────────────────────────
        total_csv = 0.0
        bad_rows: list[dict] = []
        for r in lead_rows:
            try:
                total_csv += float(r["amount_aud"])
            except ValueError:
                bad_rows.append(r)
        for r in bad_rows:
            unmatched.append({**r, "reason": "bad-amount"})

        if not lead_rows or all(r in bad_rows for r in lead_rows):
            continue  # all rows for this lead were bad

        # ── amount match (sum vs claim) ────────────────────────────────
        claim_amt = float(rec.get("amount_aud") or 0)
        base_date = rec.get("claim_date") or rec.get("decision_date") or ""
        if abs(claim_amt - total_csv) > AMOUNT_TOL:
            if len(lead_rows) == 1:
                reason = f"amount-mismatch(claim={claim_amt},csv={total_csv})"
            else:
                reason = f"amount-mismatch(claim={claim_amt},csv_sum={total_csv} from {len(lead_rows)} rows)"
            for r in lead_rows:
                if r not in bad_rows:
                    unmatched.append({**r, "reason": reason})
            continue

        # ── window check (all payments must be within window) ───────────
        out_of_window_rows: list[dict] = []
        for r in lead_rows:
            if not _within_window(base_date, r["date"], attribution.ATTR_WINDOW_DAYS):
                out_of_window_rows.append(r)
        if out_of_window_rows:
            for r in out_of_window_rows:
                unmatched.append({**r, "reason": "out-of-window(>7d یا پیش از تصمیم)"})
            for r in lead_rows:
                if r not in bad_rows and r not in out_of_window_rows:
                    unmatched.append({**r, "reason": "cohort-partial-out-of-window"})
            continue

        # ── all checks passed → CONFIRM ────────────────────────────────
        cell = rec.get("cell", "unknown")
        if write:
            proof = {
                "date": ",".join(r["date"] for r in lead_rows if r not in bad_rows),
                "source": ",".join(r["source"] for r in lead_rows if r not in bad_rows),
                "lead_id": lead,
                "file": ",".join(f"{r['_file']}:{r['_line']}" for r in lead_rows if r not in bad_rows),
                "n_rows": len(lead_rows) - len(bad_rows),
                "csv_total": total_csv,
            }
            attribution.confirm(lead, cell, total_csv, proof)
        seen.add(lead)
        confirmed.append({
            "attribution_id": lead, "cell": cell, "amount_aud": total_csv,
            "n_payments": len(lead_rows) - len(bad_rows),
        })

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
