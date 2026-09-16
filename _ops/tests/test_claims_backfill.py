#!/usr/bin/env python3
"""test_claims_backfill.py — فاز ۱+۲ نقشهٔ reconcile: خروجی‌سازِ واریزی + backfillِ ادعا +
**خطِ لولهٔ کامل**: claim → depositsِ CSV → reconcile.run → CONFIRMED → confirmed_revenue.

قراردادها:
- deposits_export: فقط amount_cents>0، فرمتِ قفلِ reconcile (۴ ستونِ اول)، lead_id خالی.
- claims_backfill: DRY پیش‌فرض (صفر نوشتن)؛ write → PROPOSAL+CLAIMED؛ idempotent با ref؛
  ردیفِ خراب fail-closed (بقیه زنده).
- e2e: واریزیِ هم‌مبلغ در پنجرهٔ ۷روزه → reconcile تأیید می‌کند و درآمدِ سلول دیده می‌شود.
صفر شبکه؛ همهٔ نوشتن‌ها داخلِ harness (GENOME_DIR/OPS_DIR ریدایرکت).
"""
import csv
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("claims-backfill")

sys.path.insert(0, str(_HERE.parent / "legs"))

import opslib             # noqa: E402
import attribution        # noqa: E402
import claims_backfill    # noqa: E402
import deposits_export    # noqa: E402
import reconcile          # noqa: E402

TMP = opslib.STATE_DIR / "test-claims-backfill"


def _mk_store(rows) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / "txn-store.json"
    p.write_text(json.dumps({"_schema": "txn-store.v1", "txns": rows},
                            ensure_ascii=False), "utf-8")
    return p


def _mk_claims_csv(rows) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / "claims-backfill.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cell", "ref", "amount_aud",
                                          "claim_date", "note"])
        w.writeheader()
        w.writerows(rows)
    return p


def t_a_deposits_export_only_positive_locked_format():
    store = _mk_store([
        {"date": "2026-07-10", "amount_cents": 48000, "desc": "دپوزیت", "source": "bank",
         "account": "A", "owner": "armin"},
        {"date": "2026-07-11", "amount_cents": -2000, "desc": "خرید", "source": "bank"},
        {"date": "2026-07-12", "amount_cents": 25000, "desc": "تسویه", "source": "ps"},
    ])
    r = deposits_export.export(out_dir=TMP / "out", store_path=store)
    assert r["ok"] and r["deposits"] == 2, r
    with open(r["path"], "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [c for c in rows[0]][:4] == ["date", "amount_aud", "lead_id", "source"], \
        "۴ ستونِ اول باید دقیقاً قراردادِ reconcile باشد"
    assert rows[0]["amount_aud"] == "250.00" and rows[0]["lead_id"] == "", \
        "جدیدترین اول، مبلغ ۲رقم، lead_id خالی (فقط مالک پر می‌کند)"


def t_b_backfill_dry_writes_nothing():
    p = _mk_claims_csv([
        {"cell": "lead.doer", "ref": "INV-T1", "amount_aud": "480.00",
         "claim_date": "2026-07-10", "note": "تست"},
        {"cell": "", "ref": "BAD", "amount_aud": "10", "claim_date": "2026-07-10"},
    ])
    r = claims_backfill.run(csv_path=p, write=False)
    assert r["total"] == 1 and r["new"] == 1 and r["written"] == 0
    assert r["errors"], "ردیفِ بی‌cell باید خطا بدهد"
    assert attribution.fold() == {} or not any(
        v.get("ref") == "INV-T1" for v in attribution.fold().values()), \
        "DRY نباید چیزی در لجر بنویسد"


def t_c_backfill_write_then_idempotent():
    p = _mk_claims_csv([
        {"cell": "lead.doer", "ref": "INV-T2", "amount_aud": "480.00",
         "claim_date": "2026-07-10", "note": "نقاشی"},
    ])
    r = claims_backfill.run(csv_path=p, write=True)
    assert r["written"] == 1 and not r["errors"], r
    fold = attribution.fold()
    rec = next(v for v in fold.values() if v.get("ref") == "INV-T2")
    assert rec["state"] == "CLAIMED" and abs(rec["amount_aud"] - 480.0) < 0.005
    r2 = claims_backfill.run(csv_path=p, write=True)
    assert r2["new"] == 0 and r2["written"] == 0 and r2["skipped_existing"] == 1, \
        "اجرای دوباره باید idempotent باشد"


def t_d_full_pipeline_claim_csv_reconcile_confirmed():
    """خطِ لولهٔ کامل: backfillِ claim → CSV واریزیِ هم‌مبلغ در پنجره → CONFIRMED."""
    p = _mk_claims_csv([
        {"cell": "ziman", "ref": "INV-T3", "amount_aud": "250.00",
         "claim_date": "2026-07-10", "note": "قاب"},
    ])
    r = claims_backfill.run(csv_path=p, write=True)
    assert r["written"] == 1, r
    fold = attribution.fold()
    aid = next(k for k, v in fold.items() if v.get("ref") == "INV-T3")
    rec_dir = TMP / "reconcile"
    rec_dir.mkdir(parents=True, exist_ok=True)
    with open(rec_dir / "deposits.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(reconcile.COLUMNS))
        w.writeheader()
        w.writerow({"date": "2026-07-13", "amount_aud": "250.00",
                    "lead_id": aid, "source": "bank"})
    report = reconcile.run(reconcile_dir=rec_dir, write=True)
    confirmed = report.get("confirmed") or report.get("matched") or []
    assert confirmed, f"باید تأیید می‌شد: {report}"
    fold2 = attribution.fold()
    # وضعیتِ نهایی بعدِ reconcile: CONFIRMED و سپس ATTRIBUTED (تقسیمِ شریک) — هر دو یعنی پول تأیید شد
    assert fold2[aid]["state"] in ("CONFIRMED", "ATTRIBUTED"), fold2[aid]
    rev = attribution.confirmed_revenue()
    by_cell = rev.get("by_cell") or {}
    assert abs(float(by_cell.get("ziman", 0)) - 250.0) < 0.005, \
        f"درآمدِ تأییدشدهٔ سلول باید دیده شود: {by_cell}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_claims_backfill: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
