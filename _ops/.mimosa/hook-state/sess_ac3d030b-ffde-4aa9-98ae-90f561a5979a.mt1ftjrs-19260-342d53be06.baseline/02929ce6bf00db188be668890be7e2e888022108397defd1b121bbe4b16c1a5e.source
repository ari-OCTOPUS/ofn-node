#!/usr/bin/env python3
"""recon.py — موتورِ reconciliation واقعی (فازِ صفر + سخت‌سازیِ auditِ 2026-07-16).

حکمِ نقد: «برابریِ خالص صحت را اثبات نمی‌کند — دو خطای متضاد همدیگر را خنثی می‌کنند.»
سه چیزِ قطعی: (۱) هویتِ ترازِ بانکی opening+flows==closing به سنتِ دقیق؛ (۲) کاملیتِ
تراکنش‌به‌تراکنش id-به-id (missing/extra/mismatch/dup)؛ (۳) لیست+شمارشِ حل‌نشده‌ها.

سخت‌سازیِ audit (#8/#9/#12/#25/#26/#42/#43):
  * مبلغِ ناسالم/غایب **رد است نه ۰** — bad_amounts شمرده و ok را قرمز می‌کند.
  * سطرِ بی‌id/غیرdict → bad_rows و ok قرمز (id==0 معتبر است — چکِ حضور، نه truthiness).
  * دو مجموعهٔ خالی = **vacuous، سبز نیست** (ترکیب با خواننده‌های fail-soft خطرناک بود).
  * لیست‌ها سقف‌دار با پرچمِ صریحِ truncated؛ idها [:40] (ضدِ نشتِ متنِ آزاد در گزارش).
«سبز» فقط وقتی همه‌چیز پاس و unresolved==0 و هیچ bad — net برابر هرگز کافی نیست.
هیچ mutation — فقط محاسبه/گزارش. PocketSmith منبعِ مقایسه است، نه حقیقت. $0 · stdlib.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import money  # noqa: E402

_LIST_CAP = 200
_DUP_CAP = 50


def _cents_strict(x) -> tuple[int, bool]:
    """(مقدار، سالم؟) — فقط int (نه bool/float/رشته). ناسالم → (0, False) و شمرده می‌شود."""
    if isinstance(x, int) and not isinstance(x, bool):
        return x, True
    return 0, False


def balance_check(opening_cents, txn_amounts_cents: list, closing_cents) -> dict:
    """هویتِ ترازِ بانکی: opening + Σamounts == closing. سنتِ دقیق، صفر رواداری.
    opening/closing/مبلغِ ناسالم → ok=False با شمارش (نه ۰ِ بی‌صدا — audit #12)."""
    op, op_ok = _cents_strict(opening_cents)
    cl, cl_ok = _cents_strict(closing_cents)
    total = 0
    bad_amounts = 0
    for a in (txn_amounts_cents or []):
        v, ok = _cents_strict(a)
        if not ok:
            bad_amounts += 1
            continue
        total += v
    computed = op + total
    diff = cl - computed
    ok = op_ok and cl_ok and bad_amounts == 0 and diff == 0
    return {"ok": ok, "opening_cents": op, "flows_cents": total,
            "computed_closing_cents": computed, "stated_closing_cents": cl,
            "diff_cents": diff, "diff_display": money.fmt(diff),
            "bad_amounts": bad_amounts,
            "bad_bounds": (not op_ok) or (not cl_ok)}


def _index(rows, key: str, amount_key: str):
    """(idx, dups, bad_rows, bad_amounts) — id==0 معتبر (چکِ حضور)؛ مبلغِ ناسالم شمرده."""
    idx: dict = {}
    dups: list = []
    bad_rows = bad_amounts = 0
    for r in (rows or []):
        if not isinstance(r, dict) or key not in r or r.get(key) is None:
            bad_rows += 1
            continue
        k = str(r[key])[:40]                       # سقفِ طول — ضدِ نشتِ متنِ آزاد (audit #42)
        if k in idx:
            dups.append(k)
            continue
        if amount_key not in r:
            bad_amounts += 1                       # مبلغِ غایب ≠ صفر (audit #9)
            idx[k] = None
            continue
        v, ok = _cents_strict(r.get(amount_key))
        if not ok:
            bad_amounts += 1
            idx[k] = None
            continue
        idx[k] = v
    return idx, dups, bad_rows, bad_amounts


def completeness(ours: list, theirs: list, key: str = "id",
                 amount_key: str = "amount_cents") -> dict:
    """کاملیتِ تراکنش‌به‌تراکنش. مبلغِ None (ناسالم/غایب) هرگز match نمی‌شود — تطبیقِ
    ۰==۰ روی دو رکوردِ خراب غیرممکن (audit #12)."""
    a, dup_a, badr_a, bada_a = _index(ours, key, amount_key)
    b, dup_b, badr_b, bada_b = _index(theirs, key, amount_key)
    missing_in_ours = sorted(k for k in b if k not in a)
    missing_in_theirs = sorted(k for k in a if k not in b)
    mismatch = sorted(k for k in a
                      if k in b and (a[k] is None or b[k] is None or a[k] != b[k]))
    matched = sum(1 for k in a
                  if k in b and a[k] is not None and a[k] == b[k])
    bad_total = badr_a + badr_b + bada_a + bada_b
    unresolved = (len(missing_in_ours) + len(missing_in_theirs) + len(mismatch)
                  + len(dup_a) + len(dup_b) + bad_total)
    return {"ok": unresolved == 0, "matched": matched, "unresolved": unresolved,
            "missing_in_ours": missing_in_ours[:_LIST_CAP],
            "missing_in_ours_truncated": len(missing_in_ours) > _LIST_CAP,
            "missing_in_theirs": missing_in_theirs[:_LIST_CAP],
            "missing_in_theirs_truncated": len(missing_in_theirs) > _LIST_CAP,
            "amount_mismatch": mismatch[:_LIST_CAP],
            "amount_mismatch_truncated": len(mismatch) > _LIST_CAP,
            "dup_ids_ours": dup_a[:_DUP_CAP], "dup_ids_theirs": dup_b[:_DUP_CAP],
            "bad_rows_ours": badr_a, "bad_rows_theirs": badr_b,
            "bad_amounts_ours": bada_a, "bad_amounts_theirs": bada_b}


def reconcile(ours: list, theirs: list, opening_cents=None,
              closing_cents=None, key: str = "id",
              amount_key: str = "amount_cents") -> dict:
    """گزارشِ کامل. «سبز» فقط: کاملیت پاس + (اگر داده شد) تراز پاس + **غیرِ خالی**.
    دو مجموعهٔ خالی = vacuous و سبز نیست (audit #26 — با خواننده‌های fail-soft که روی
    فایلِ خراب [] می‌دهند، سبزِ پوچ یعنی سبزِ دروغ). net برابر هرگز معیار نیست."""
    comp = completeness(ours, theirs, key=key, amount_key=amount_key)
    bal = None
    if opening_cents is not None and closing_cents is not None:
        bal = balance_check(opening_cents,
                            [r.get(amount_key) for r in (ours or []) if isinstance(r, dict)],
                            closing_cents)
    vacuous = not (ours or []) and not (theirs or [])
    ok = comp["ok"] and (bal is None or bal["ok"]) and not vacuous
    net_ours = sum(v for v, k in (_cents_strict(r.get(amount_key))
                                  for r in (ours or []) if isinstance(r, dict)) if k)
    net_theirs = sum(v for v, k in (_cents_strict(r.get(amount_key))
                                    for r in (theirs or []) if isinstance(r, dict)) if k)
    return {"ok": ok, "vacuous": vacuous, "completeness": comp, "balance": bal,
            "net_ours_cents": net_ours, "net_theirs_cents": net_theirs,
            "net_equal_but_not_proof": net_ours == net_theirs and not comp["ok"]}


if __name__ == "__main__":
    print(json.dumps(reconcile([], []), ensure_ascii=False, indent=2))
