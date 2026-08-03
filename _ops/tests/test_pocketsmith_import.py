#!/usr/bin/env python3
"""تستِ واردکنندهٔ PocketSmith (2026-07-16): xlsx (stdlib) → ledger.v2، idempotent، بدونِ leak.

اثبات:
  (الف) خواندنِ xlsxِ ساختگی (zipfile+xml دستی) → entries با تاریخِ درست + type از علامت.
  (ب) ادغام در ledger.json + idempotent روی ext_id (اجرای دوم چیزی اضافه نمی‌کند).
  (پ) تراز پس از import با personal_ledger درست حساب می‌شود.
  (ت) خروجیِ import فقط شمارش/تراز است، نه تراکنشِ خام.
$0 آفلاین، stdlib، xlsxِ ساختگی در tmp.
"""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("pocketsmith-import")

_LEGS = harness.SELF_OPS / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import pocketsmith_import as imp  # noqa: E402
import personal_ledger as pl     # noqa: E402
import opslib                    # noqa: E402


def _make_xlsx(path: Path, rows: list[list]):
    """یک xlsxِ حداقلی بساز (sharedStrings + sheet1) — بدونِ openpyxl."""
    strings, sidx = [], {}
    def sref(v):
        if v not in sidx:
            sidx[v] = len(strings); strings.append(v)
        return sidx[v]
    # همهٔ سلول‌ها را رشته کن (ساده)
    cells_xml = []
    for ri, row in enumerate(rows, 1):
        cs = []
        for ci, v in enumerate(row):
            col = chr(65 + ci)
            cs.append(f'<c r="{col}{ri}" t="s"><v>{sref(str(v))}</v></c>')
        cells_xml.append(f'<row r="{ri}">{"".join(cs)}</row>')
    NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    sheet = f'<worksheet {NS}><sheetData>{"".join(cells_xml)}</sheetData></worksheet>'
    ss = (f'<sst {NS} count="{len(strings)}" uniqueCount="{len(strings)}">'
          + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
    wb = f'<workbook {NS}><sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", ss)
        z.writestr("xl/workbook.xml", wb)


def t_a_read_and_import():
    xp = opslib.STATE_DIR / "ps.xlsx"
    xp.parent.mkdir(parents=True, exist_ok=True)
    _make_xlsx(xp, [
        ["Date", "Merchant", "Amount", "Transaction Type", "Category", "Account", "ID"],
        ["45999", "M1", "100", "credit", "AbbasNew", "acc", "id-1"],   # income
        ["46000", "M2", "-30", "debit", "AbbasNew", "acc", "id-2"],    # expense
    ])
    lp = opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger.json"
    r = imp.import_file(xp, party="abbas", ledger=lp)
    assert r["ok"] and r["read"] == 2 and r["added"] == 2, r
    assert r["income_total"] == 100.0 and r["expense_total"] == 30.0 and r["net"] == 70.0, r
    # تاریخِ Excel→ISO
    ents = json.loads(lp.read_text("utf-8"))["entries"]
    assert ents[0]["date"] == "2025-12-08", ents[0]["date"]      # 45999
    assert ents[0]["type"] == "income" and ents[1]["type"] == "expense"
    # idempotent
    r2 = imp.import_file(xp, party="abbas", ledger=lp)
    assert r2["added"] == 0 and r2["skipped_dup"] == 2, r2


def t_b_balance_after_import():
    lp = opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger.json"
    b = pl.personal_status(lp)["balance"]
    assert b["entity_ato"]["net_before_tax"] == 70.0, b["entity_ato"]
    assert b["per_party"]["abbas"]["cashflow"] == 70.0, b["per_party"]["abbas"]


def t_c_import_output_no_raw_txn():
    xp = opslib.STATE_DIR / "ps2.xlsx"
    _make_xlsx(xp, [["Date", "Merchant", "Amount", "ID"], ["46000", "SECRET-MERCHANT", "-999", "id-x"]])
    lp = opslib.STATE_DIR / "ledger-b.json"
    r = imp.import_file(xp, party="abbas", ledger=lp)
    assert "SECRET-MERCHANT" not in json.dumps(r, ensure_ascii=False), "خروجیِ import نباید نامِ فروشنده را echo کند"
    assert "999" not in str(r.get("read"))   # فقط شمارش/تراز، نه تراکنشِ خام در فیلدهای متا


if __name__ == "__main__":
    for f in (t_a_read_and_import, t_b_balance_after_import, t_c_import_output_no_raw_txn):
        f()
        print("ok", f.__name__)
    print("PASS test_pocketsmith_import")
