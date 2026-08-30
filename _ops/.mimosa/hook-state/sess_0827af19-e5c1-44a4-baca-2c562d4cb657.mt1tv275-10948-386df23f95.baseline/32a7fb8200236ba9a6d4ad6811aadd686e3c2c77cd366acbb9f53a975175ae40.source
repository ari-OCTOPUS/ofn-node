#!/usr/bin/env python3
"""claims_backfill.py — ثبتِ ادعاهای گذشته در لجرِ انتساب (فاز ۲ نقشهٔ reconcile، رأی مالک 2026-07-17).

مسئله: لجرِ انتساب خالی است (صفر lead) — پس CSV واریزی‌ها چیزی برای تطبیق ندارد.
راه: مالک فایلِ سادهٔ claims-backfill.csv را پر می‌کند (هر ردیف = یک فاکتور/طلبِ واقعی)،
این ابزار برای هر ردیف propose (mintِ LEAD-id) + claim (CLAIMED) می‌زند.

قراردادِ فایل (utf-8-sig، comma):
    cell,ref,amount_aud,claim_date,note
    lead.doer,INV-2026-014,480.00,2026-07-15,نقاشی راه‌پله
- cell: سلولِ بیزنسی (مثل lead.doer / ziman) — همان که در fitness دیده می‌شود.
- ref: شناسهٔ یکتای فاکتور/کوت (کلیدِ idempotency — ردیفِ تکراری دوباره ثبت نمی‌شود).
- amount_aud: مبلغِ طلب (AUD) — واریزی باید دقیقاً (یا جمعِ چند واریزی) همین باشد.
- claim_date: تاریخِ فاکتور (ISO) — پنجرهٔ تطبیق ۰..۷ روز بعدِ همین تاریخ است؛ برای
  backfill باید با تاریخِ واریزیِ واقعی هماهنگ باشد وگرنه UNMATCHED می‌شود.

ایمنی (پول = فقط با انسان):
- پیش‌فرض DRY: هیچ نوشتنی؛ فقط گزارشِ نقشه. نوشتنِ واقعی فقط با آرگومانِ صریح --write.
- idempotent: ref ِ موجود در لجر → skip (اجرای دوباره امن است).
- این ابزار فقط PROPOSAL/CLAIMED می‌سازد؛ CONFIRMED فقط از reconcile می‌آید (رأی #۱۰).
- خروجی: شمارش + ref (هرگز echo ِ مبلغ‌ها به‌صورتِ جدولِ خام در لاگ‌های ماندگار).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

COLUMNS = ("cell", "ref", "amount_aud", "claim_date")   # note اختیاری


def default_csv_path() -> Path:
    import txn_store
    return (txn_store.default_store_path().parent.parent
            / "drafts" / "reconcile-draft" / "claims-backfill.csv")


def _existing_refs() -> set[str]:
    """refهای ثبت‌شده در fold لجر (برای idempotency). خطا → set خالی (fail-soft به DRY)."""
    try:
        import attribution
        rows = attribution.fold()
        vals = rows.values() if isinstance(rows, dict) else rows
        return {str(r.get("ref") or "").strip() for r in vals if r.get("ref")}
    except Exception:  # noqa: BLE001
        return set()


def load_rows(csv_path: Path | None = None) -> tuple[list[dict], list[str]]:
    """ردیف‌های معتبر + خطاهای اعتبارسنجی (شمارهٔ ردیف + دلیل، بدونِ echo ِ مبلغ)."""
    p = Path(csv_path) if csv_path else default_csv_path()
    rows, errors = [], []
    if not p.exists():
        return [], [f"فایل نیست: {p}"]
    import datetime
    with open(p, "r", encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            ref = str(row.get("ref") or "").strip()
            cell = str(row.get("cell") or "").strip()
            if not ref or not cell:
                errors.append(f"ردیف {i}: cell/ref خالی")
                continue
            try:
                amt = round(float(row.get("amount_aud") or ""), 2)
                assert amt > 0
            except (TypeError, ValueError, AssertionError):
                errors.append(f"ردیف {i} ({ref}): amount_aud نامعتبر")
                continue
            day = str(row.get("claim_date") or "").strip()
            try:
                datetime.date.fromisoformat(day)
            except ValueError:
                errors.append(f"ردیف {i} ({ref}): claim_date باید ISO باشد")
                continue
            rows.append({"cell": cell, "ref": ref, "amount_aud": amt, "day": day,
                         "note": str(row.get("note") or "").strip()[:80]})
    return rows, errors


def run(csv_path: Path | None = None, write: bool = False) -> dict:
    """DRY پیش‌فرض. write=True فقط از دستِ مالک (پول = انسان-در-حلقه)."""
    rows, errors = load_rows(csv_path)
    seen = _existing_refs()
    plan = [r for r in rows if r["ref"] not in seen]
    skipped = len(rows) - len(plan)
    out = {"ok": not errors, "total": len(rows), "new": len(plan),
           "skipped_existing": skipped, "errors": errors, "written": 0,
           "refs": [r["ref"] for r in plan][:20]}
    if not write or not plan:
        return out
    import attribution
    written = []
    for r in plan:
        try:
            rec = attribution.propose(r["cell"], r["amount_aud"], lead=r["note"],
                                      day=r["day"])
            aid = rec.get("attribution_id") or (rec.get("payload") or {}).get("attribution_id")
            if not aid:
                errors.append(f"{r['ref']}: propose بدونِ id")
                continue
            attribution.claim(aid, r["ref"], r["amount_aud"], day=r["day"])
            written.append(r["ref"])
        except Exception as e:  # noqa: BLE001 — fail-closed: ردیفِ خراب بقیه را نمی‌کشد
            errors.append(f"{r['ref']}: {type(e).__name__}")
    out.update({"written": len(written), "errors": errors, "ok": not errors})
    return out


if __name__ == "__main__":
    write = "--write" in sys.argv
    r = run(write=write)
    mode = "WRITE" if write else "DRY (بدونِ نوشتن — برای ثبت: --write)"
    print(f"[{mode}] total={r['total']} new={r['new']} "
          f"skipped={r['skipped_existing']} written={r['written']}")
    for e in r["errors"][:10]:
        print("  ⚠", e)
