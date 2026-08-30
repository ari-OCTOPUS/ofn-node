#!/usr/bin/env python3
"""deposits_export.py — پیش‌نویسِ CSV واریزی‌ها برای قلبِ پول (فاز ۱ نقشهٔ reconcile، رأی مالک 2026-07-17).

نقش: انبارِ تراکنش‌ها (personal/txn-store.json) را می‌خواند، فقط واریزی‌ها
(amount_cents > 0) را برمی‌دارد، و یک CSV با فرمتِ قفل‌شدهٔ reconcile
(`date,amount_aud,lead_id,source` — رأی 2026-07-07) به‌عنوانِ **پیش‌نویس** در
drafts می‌نویسد. lead_id عمداً خالی است — طبقِ اصلِ استقلالِ دو جریان (رأی #۱۰)
فقط مالک می‌داند کدام واریزی مالِ کدام فاکتور است؛ مالک پرش می‌کند و فایل را
خودش به _ops/reconcile می‌بَرد (انسان-در-حلقه).

ستون‌های اضافه (desc/account/owner) بعد از ۴ ستونِ قرارداد می‌آیند — DictReaderِ
reconcile با نام می‌خواند پس بی‌ضررند و برای شناساییِ ردیف به مالک کمک می‌کنند.
$0 · فقط‌خواندنی از انبار · هیچ لجر/پول/شبکه. خروجی: شمارش (هرگز ردیفِ خام echo نمی‌شود).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

HEADER = ("date", "amount_aud", "lead_id", "source",
          "desc", "account", "owner")   # ۴تای اول = قراردادِ reconcile (قفل)


def _store_rows(store_path: Path | None = None) -> list[dict]:
    """انبار (txn-store.json) را مستقیم بخوان — fail-soft به [] (قراردادِ txn_store.save)."""
    import json
    import txn_store
    p = Path(store_path) if store_path else txn_store.default_store_path()
    try:
        data = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return []
    rows = data.get("txns") if isinstance(data, dict) else data
    return rows if isinstance(rows, list) else []


def draft_path(out_dir: Path | None = None) -> Path:
    if out_dir is None:
        import txn_store
        acc = txn_store.default_store_path().parent.parent   # …/Accounting
        out_dir = acc / "drafts" / "reconcile-draft"
    return out_dir / "deposits-draft.csv"


def export(min_aud: float = 0.01, since: str = "", out_dir: Path | None = None,
           store_path: Path | None = None) -> dict:
    """واریزی‌ها → CSV پیش‌نویس. خروجی: شمارش + مسیر (هرگز محتوا).

    since: اگر داده شود (YYYY-MM-DD)، فقط واریزی‌های از آن تاریخ به بعد —
    برای این‌که مالک با ۲۸۸ ردیفِ تاریخی غرق نشود؛ پیش‌فرض: همه."""
    rows = _store_rows(store_path)
    deps = []
    for r in rows:
        try:
            cents = int(r.get("amount_cents") or 0)
        except (TypeError, ValueError):
            continue
        if cents <= 0 or (cents / 100.0) < min_aud:
            continue
        d = str(r.get("date") or "")
        if since and d < since:
            continue
        deps.append({"date": d, "amount_aud": f"{cents / 100.0:.2f}",
                     "lead_id": "",                       # فقط مالک پر می‌کند
                     "source": str(r.get("source") or "txn-store"),
                     "desc": str(r.get("desc") or "")[:80],
                     "account": str(r.get("account") or "")[:40],
                     "owner": str(r.get("owner") or "")[:20]})
    deps.sort(key=lambda x: x["date"], reverse=True)
    p = draft_path(out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(HEADER))
        w.writeheader()
        w.writerows(deps)
    import os
    os.replace(tmp, p)
    return {"ok": True, "deposits": len(deps), "path": str(p)}


if __name__ == "__main__":
    since = sys.argv[1] if len(sys.argv) > 1 else ""
    r = export(since=since)
    print(f"{'✅' if r['ok'] else '❌'} {r['deposits']} واریزی → {r['path']}")
