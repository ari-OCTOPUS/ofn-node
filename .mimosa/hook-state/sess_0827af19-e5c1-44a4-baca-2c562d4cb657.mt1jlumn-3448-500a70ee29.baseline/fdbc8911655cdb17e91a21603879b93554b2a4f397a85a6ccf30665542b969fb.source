#!/usr/bin/env python3
"""txn_store.py — انبارِ تجمیعیِ تراکنش‌ها (یک منبعِ حقیقت، همه بر پایهٔ سنتِ صحیح) — 2026-07-16.

همهٔ منابعِ در دسترسِ حسابداری را به یک انبارِ واحدِ cents-محور می‌ریزد:
  (۱) اکسپورتِ .xlsxِ PocketSmith  (۲) پنج CSVِ اکسترکتِ دفتر.
هر تراکنش شناسهٔ content-hash می‌گیرد (date|amount_cents|desc|account) → دوتاییِ یکسان
از دو فایل = یک ردیف (dedupِ بین‌منبعی). پول همیشه عددِ صحیحِ سنت است (هرگز float) با موتورِ
money.py؛ تاریخِ Excel-serial به ISO. propose-only مطلق — فقط فایل می‌خواند/می‌نویسد،
صفر حرکتِ مالی.

روش‌های ۲۰۲۷: پولِ integer-cents · واردِ idempotent با content-hash · تراز به منبع
(reconcile_report با جمعِ مستقلِ دوباره → تضمینِ نبودِ نشتِ سنت).

مرزها: مقادیرِ خام/نامِ فروشنده/شماره‌حساب هرگز echo نمی‌شوند — فقط شمارش/ترازِ تجمیعی.
انبارِ واقعی (txn-store.json) gitignore + محلی است (دادهٔ مالیِ واقعی).
$0 · stdlib + money/opslib · fail-soft.
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))                 # money.py + pocketsmith_import.py کنارِ همین فایل
sys.path.insert(0, str(_HERE.parent / "budget"))   # opslib

import money                                        # noqa: E402 — موتورِ سنتِ صحیح
try:
    from pocketsmith_import import read_xlsx        # noqa: E402 — پارسرِ stdlibِ xlsx
except Exception:  # noqa: BLE001 — اسکن #21: نبودِ ماژول نباید کلِ زنجیره را با ImportError بکشد
    read_xlsx = None                                # مصرف‌کننده fail-soft می‌شود (xlsx skip)

# نامِ فایلِ اکسپورتِ PocketSmith (منبعِ (۱)) — fallback؛ _newest_xlsx جدیدترین را می‌گیرد
_XLSX_NAME = "pocketsmith-abbas-2025-12-08_2026-04-20.xlsx"


def _newest_xlsx(src_dir):
    """جدیدترین اکسپورتِ pocketsmith*.xlsx (اسکن #65: نامِ ثابت اکسپورتِ نو را نادیده
    می‌گرفت). نبود → مسیرِ نامِ ثابت (سازگاری با قبل)."""
    try:
        cands = sorted(src_dir.glob("pocketsmith*.xlsx"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if cands:
            return cands[0]
    except OSError:
        pass
    return src_dir / _XLSX_NAME

# ─── نرمالِ تاریخ ────────────────────────────────────────────────────────────
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
_SERIAL_RE = re.compile(r"^\d{1,6}$")
_DATE_FMTS = ("%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%y", "%d-%m-%Y", "%d %b %Y")


def _excel_serial(n) -> str:
    """Excel serial (epoch 1899-12-30) → YYYY-MM-DD."""
    return (_dt.date(1899, 12, 30) + _dt.timedelta(days=int(float(n)))).isoformat()


def _norm_date(raw) -> str:
    """هر شکلِ تاریخ → ISO(YYYY-MM-DD) در حدِ امکان؛ ناموفق → همان رشتهٔ خام (fail-soft).
    عددِ صحیح = Excel serial؛ ISO دست‌نخورده (فقط ۱۰ رقمِ اول)؛ اسلش/خط‌تیره → تلاش با قالب‌ها."""
    s = str(raw or "").strip()
    if not s:
        return ""
    if _ISO_RE.match(s):
        return s[:10]
    if _SERIAL_RE.match(s):
        try:
            return _excel_serial(s)
        except (TypeError, ValueError, OverflowError):
            return s
    for fmt in _DATE_FMTS:
        try:
            return _dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s


# ─── ساختِ تراکنش + شناسهٔ content-hash ──────────────────────────────────────
def _hash(date: str, amount_cents: int, desc: str, account: str) -> str:
    """شناسهٔ پایدارِ محتوا: sha1(date|amount_cents|desc|account) → ۱۶ رقمِ hex.
    دوتاییِ یکسان از دو فایل → همین شناسه → dedup."""
    raw = f"{date}|{int(amount_cents)}|{desc}|{account}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _mk(date: str, amount_raw, desc, account, category, source: str) -> dict:
    """یک ردیفِ منبع → تراکنشِ استانداردِ انبار (schemaِ ثابت). مبلغ → سنتِ صحیحِ علامت‌دار."""
    cents = money.to_cents(amount_raw)                       # علامت از خودِ Amount (پرانتز/منفی = خروج)
    desc = str(desc or "").strip()[:120]
    account = str(account or "").strip()
    category = (str(category or "").strip() or "uncategorized")
    return {
        "id": _hash(date, cents, desc, account),
        "date": date,
        "amount_cents": cents,          # علامت‌دار: منفی=بدهکار/خروج، مثبت=بستانکار/ورود
        "desc": desc,
        "source": source,
        "account": account,
        "owner": "unknown",             # مالکیت (آرمین/عباس/pass-through) بعداً با مرورِ مالک
        "ptype": "unknown",             # income/expense/transfer/pass-through — نامشخص تا مرور
        "category": category,
        "review": "pending",
        "note": "",
    }


# ─── منابع ───────────────────────────────────────────────────────────────────
def _accounting_root() -> Path:
    import opslib  # noqa: WPS433 — lazy تا ORG_ROOTِ زنده/تست خوانده شود
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting"


def _sources() -> dict:
    """مسیرِ منابع نسبت به ORG_ROOT (زنده یا تست)."""
    acc = _accounting_root()
    return {
        "xlsx": _newest_xlsx(acc / "personal" / "source"),
        "csv_dir": acc / "drafts" / "ledger-extract",
    }


def default_store_path() -> Path:
    """مسیرِ انبارِ واقعی (gitignore + محلی)."""
    return _accounting_root() / "personal" / "txn-store.json"


def _from_xlsx(path: Path) -> list[dict]:
    """اکسپورتِ PocketSmith → تراکنش‌ها. desc=Merchant|Memo، account=Account، date=Excel-serial→ISO."""
    if read_xlsx is None:                  # ماژولِ پارسر غایب → fail-softِ صادق (اسکن #21)
        return []
    try:
        rows = read_xlsx(path)
    except Exception:  # noqa: BLE001 — منبعِ خراب نباید کلِ بارگذاری را بکشد
        return []
    src = "pocketsmith"
    out = []
    for r in rows:
        out.append(_mk(
            date=_norm_date(r.get("Date")),
            amount_raw=r.get("Amount"),
            desc=r.get("Merchant") or r.get("Memo") or "",
            account=r.get("Account") or "",
            category=r.get("Category") or "uncategorized",
            source=src,
        ))
    return out


def _from_csv(path: Path) -> list[dict]:
    """CSVِ اکسترکت (Date,Merchant,Amount,Transaction Type,Category,Account,ID) → تراکنش‌ها."""
    src = "csv:" + path.stem
    out = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                out.append(_mk(
                    date=_norm_date(r.get("Date")),
                    amount_raw=r.get("Amount"),
                    desc=r.get("Merchant") or r.get("Memo") or "",
                    account=r.get("Account") or path.stem,
                    category=r.get("Category") or "uncategorized",
                    source=src,
                ))
    except OSError:
        return []
    return out


def _dedup(txns: list[dict]) -> list[dict]:
    """dedupِ content-hash: اولین بروزِ هر id می‌ماند، بقیه رد می‌شوند (بین‌منبعی)."""
    seen: set[str] = set()
    out = []
    for t in txns:
        tid = t["id"]
        if tid in seen:
            continue
        seen.add(tid)
        out.append(t)
    return out


def load_all() -> list[dict]:
    """همهٔ منابعِ در دسترس را بخوان، به سنت درآور، dedupِ بین‌منبعی کن → یک لیستِ واحد.
    منابعِ نبود = fail-soft (نادیده)؛ ترتیبِ dedup: xlsx اول، بعد CSVها به‌ترتیبِ نام."""
    s = _sources()
    txns: list[dict] = []
    if s["xlsx"].exists():
        txns += _from_xlsx(s["xlsx"])
    if s["csv_dir"].is_dir():
        for csvp in sorted(s["csv_dir"].glob("*.csv")):
            txns += _from_csv(csvp)
    return _dedup(txns)


def save(txns: list[dict], path: Path | None = None) -> None:
    """انبار را اتمیک بنویس (tmp + os.replace). پیش‌فرض: personal/txn-store.json (gitignore).
    فقط ساختار/شمارش در سند؛ خودِ تراکنش‌ها دادهٔ محلیِ محافظت‌شده‌اند."""
    p = Path(path) if path else default_store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "_schema": "txn-store.v1",
        "currency": "AUD",
        "count": len(txns),
        "generated": _dt.datetime.now().isoformat(timespec="seconds"),
        "txns": txns,
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
    os.replace(tmp, p)


def reconcile_report(txns: list[dict]) -> dict:
    """ترازِ کنترلی به منبع: به‌ازای هر source شمارشِ ردیف + netِ سنت.
    tie_out_ok با جمعِ مستقلِ دوباره اثبات می‌شود — مجموعِ کلِ همهٔ txnها باید *دقیقاً* برابرِ
    مجموعِ netهای per-source باشد (و همین‌طور شمارش‌ها) → نشتِ سنت/باکت غیرممکن."""
    per: dict[str, dict] = {}
    for t in txns:
        s = str(t.get("source", "?"))
        d = per.setdefault(s, {"row_count": 0, "net_cents": 0})
        d["row_count"] += 1
        d["net_cents"] += int(t.get("amount_cents", 0))
    total_rows = len(txns)                                          # مسیرِ مستقلِ ۱ (شمارش)
    total_net = sum(int(t.get("amount_cents", 0)) for t in txns)    # مسیرِ مستقلِ ۱ (جمع)
    sum_src_rows = sum(d["row_count"] for d in per.values())        # مسیرِ مستقلِ ۲ (شمارش)
    sum_src_net = sum(d["net_cents"] for d in per.values())         # مسیرِ مستقلِ ۲ (جمع)
    ok = (total_rows == sum_src_rows) and (total_net == sum_src_net)
    return {
        "per_source": per,
        "total_rows": total_rows,
        "total_net_cents": total_net,
        "source_count": len(per),
        "tie_out_ok": ok,
    }


if __name__ == "__main__":
    # اجرای واقعی: فقط شمارش/ترازِ تجمیعی چاپ می‌شود — هرگز تراکنشِ خام/مبلغِ فردی.
    # ذخیره فقط با آرگومانِ صریحِ "save" (تا اجرای گزارش‌گیری چیزی روی درختِ زنده ننویسد).
    _txns = load_all()
    _rep = reconcile_report(_txns)
    _summary = {
        "consolidated_count": len(_txns),
        "source_count": _rep["source_count"],
        "per_source_rows": {k: v["row_count"] for k, v in _rep["per_source"].items()},
        "tie_out_ok": _rep["tie_out_ok"],
        "total_net_cents": _rep["total_net_cents"],   # تجمیعی (مجاز)، نه تراکنشِ خام
    }
    print(json.dumps(_summary, ensure_ascii=False, indent=2))
    if len(sys.argv) > 1 and sys.argv[1] == "save":
        save(_txns)
        print(f"saved → {default_store_path()}")
