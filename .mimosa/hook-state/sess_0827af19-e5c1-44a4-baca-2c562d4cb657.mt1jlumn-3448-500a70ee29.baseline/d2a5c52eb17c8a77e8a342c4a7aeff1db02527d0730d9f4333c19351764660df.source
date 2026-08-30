#!/usr/bin/env python3
"""pocketsmith_import.py — واردکنندهٔ اکسپورتِ PocketSmith به دفترِ اختاپوس (2026-07-16).

اکسپورتِ .xlsxِ PocketSmith (شرکتِ نقاشیِ ساختمان، نماهای per-person) را با stdlib
(zipfile+xml، بدونِ وابستگی) می‌خواند و به شکلِ entriesِ personal-shared-ledger.v2
درمی‌آورد. propose-only مطلق — فقط فایل می‌خواند/می‌نویسد، صفر حرکتِ مالی.

مرزها: مقادیرِ خام echo نمی‌شوند (فقط شمارش/تراز برمی‌گرداند)؛ دفترِ واقعی + منبع هر دو
gitignore. تاریخِ Excel-serial به YYYY-MM-DD؛ نوع از علامتِ مبلغ (income/expense).
$0 · stdlib · fail-soft.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _excel_date(serial) -> str:
    """Excel serial (epoch 1899-12-30) → YYYY-MM-DD. غیرعدد → همان رشته."""
    try:
        n = float(serial)
        return (_dt.date(1899, 12, 30) + _dt.timedelta(days=int(n))).isoformat()
    except (TypeError, ValueError):
        return str(serial or "")


def _num(x) -> float:
    try:
        return float(str(x).replace(",", "").replace("$", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


def read_xlsx(path: Path) -> list[dict]:
    """sheet1 را به list[dict] (کلید=هدر) درآور — stdlib، بدونِ openpyxl."""
    z = zipfile.ZipFile(path)
    shared = []
    try:
        ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss.findall(f"{_NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{_NS}t")))
    except KeyError:
        pass

    def colnum(ref):
        m = re.match(r"([A-Z]+)", ref or "A")
        c = 0
        for ch in m.group(1):
            c = c * 26 + (ord(ch) - 64)
        return c - 1

    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.iter(f"{_NS}row"):
        cells = {}
        for c in row.findall(f"{_NS}c"):
            v = c.find(f"{_NS}v")
            val = "" if v is None else v.text
            if c.get("t") == "s" and val not in (None, ""):
                try:
                    val = shared[int(val)]
                except (ValueError, IndexError):
                    pass
            cells[colnum(c.get("r"))] = val
        if cells:
            rows.append(cells)
    if not rows:
        return []
    hdr = [rows[0].get(i, "") for i in range(max(rows[0]) + 1)]
    out = []
    for r in rows[1:]:
        out.append({hdr[i]: r.get(i, "") for i in range(len(hdr)) if hdr[i]})
    return out


def to_entries(raw: list[dict], party: str = "joint") -> list[dict]:
    """ردیف‌های PocketSmith → entriesِ ledger.v2. category = Category (نامِ نما) تا مالک
    بعداً دسته‌بندیِ واقعی کند. type از علامتِ Amount؛ account از ستونِ Account/Category."""
    ents = []
    for r in raw:
        amt = _num(r.get("Amount"))
        typ = "income" if amt >= 0 else "expense"
        ents.append({
            "date": _excel_date(r.get("Date")),
            "desc": str(r.get("Merchant") or r.get("Memo") or "")[:120],
            "amount": round(abs(amt), 2),
            "type": typ,
            "party": party,
            "paid_by": party if party in ("armin", "abbas") else "armin",
            "category": str(r.get("Category") or "uncategorized").strip() or "uncategorized",
            "account": str(r.get("Account") or "").strip(),
            "source": "pocketsmith",
            "ext_id": str(r.get("ID") or ""),
        })
    return ents


def import_file(xlsx: Path, party: str = "joint", ledger: Path | None = None) -> dict:
    """xlsx را بخوان و به ledger.json ادغام کن (idempotent روی ext_id). خروجی: خلاصهٔ شمارش/تراز
    — هیچ تراکنشِ منفرد/مبلغِ خام echo نمی‌شود."""
    import opslib  # noqa: WPS433
    lp = ledger or (opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger.json")
    try:
        raw = read_xlsx(xlsx)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"خواندنِ xlsx نشد: {type(e).__name__}"}
    new_ents = to_entries(raw, party=party)
    # ادغامِ idempotent
    doc = {}
    if lp.exists():
        try:
            doc = json.loads(lp.read_text("utf-8"))
        except (OSError, ValueError):
            doc = {}
    if not isinstance(doc, dict):
        doc = {}
    doc.setdefault("_schema", "personal-shared-ledger.v2")
    doc.setdefault("currency", "AUD")
    doc.setdefault("parties", {"armin": "آرمین (مالک)", "abbas": "عباس (همکار)"})
    doc.setdefault("default_split", {"armin": 50, "abbas": 50})
    existing = doc.setdefault("entries", [])
    seen = {e.get("ext_id") for e in existing if isinstance(e, dict) and e.get("ext_id")}
    added = [e for e in new_ents if not (e["ext_id"] and e["ext_id"] in seen)]
    existing.extend(added)
    lp.parent.mkdir(parents=True, exist_ok=True)
    tmp = lp.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
    import os
    os.replace(tmp, lp)
    tin = sum(e["amount"] for e in new_ents if e["type"] == "income")
    tout = sum(e["amount"] for e in new_ents if e["type"] == "expense")
    return {"ok": True, "read": len(new_ents), "added": len(added),
            "skipped_dup": len(new_ents) - len(added),
            "income_total": round(tin, 2), "expense_total": round(tout, 2),
            "net": round(tin - tout, 2), "party": party}


if __name__ == "__main__":
    import opslib  # noqa: WPS433
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    party = sys.argv[2] if len(sys.argv) > 2 else "joint"
    if not src or not src.exists():
        print(json.dumps({"ok": False, "error": "مسیرِ xlsx بده"}, ensure_ascii=False))
    else:
        print(json.dumps(import_file(src, party=party), ensure_ascii=False, indent=2))
