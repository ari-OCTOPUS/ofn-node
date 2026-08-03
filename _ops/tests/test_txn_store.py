#!/usr/bin/env python3
"""تستِ انبارِ تجمیعیِ تراکنش (txn_store) — 2026-07-16.

اثبات:
  (الف) load_all منابعِ ساختگی (xlsx + csv در tmp) را به سنتِ صحیح می‌خواند:
        $250.00 → 25000 · "(420.00)" → -42000 · Excel-serial → ISO.
  (ب) dedupِ content-hash: همان تراکنش دوبار (دو فایل) → یک ردیف.
  (پ) reconcile_report tie-out سبز (جمعِ مستقلِ دوباره برابر می‌شود).
  (ت) هر تراکنش کاملِ schema است (id/date/amount_cents/owner/ptype/review/…).
  (ث) save اتمیک می‌نویسد و دوباره خوانده می‌شود.
$0 آفلاین، stdlib، منابعِ ساختگی در tmp (هیچ دادهٔ واقعی لمس نمی‌شود).
"""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("txn-store")

_LEGS = harness.SELF_OPS / "legs"
if str(_LEGS) not in sys.path:
    sys.path.insert(0, str(_LEGS))
import txn_store as ts   # noqa: E402
import opslib            # noqa: E402


def _make_xlsx(path: Path, rows: list[list]):
    """xlsxِ حداقلی (sharedStrings + sheet1) بدونِ openpyxl — همان الگوی test_pocketsmith_import."""
    strings, sidx = [], {}

    def sref(v):
        if v not in sidx:
            sidx[v] = len(strings)
            strings.append(v)
        return sidx[v]

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


def _seed_sources():
    """منابعِ ساختگی را دقیقاً در مسیرهایی که txn_store می‌خواند بساز (نسبت به ORG_ROOTِ tmp)."""
    src = ts._sources()
    src["xlsx"].parent.mkdir(parents=True, exist_ok=True)
    src["csv_dir"].mkdir(parents=True, exist_ok=True)
    # xlsx: یک ورود ($250 credit) + یک خروج (پرانتزی = -420)
    _make_xlsx(src["xlsx"], [
        ["Date", "Merchant", "Amount", "Transaction Type", "Category", "Account", "ID"],
        ["45999", "MERCHANT_A", "$250.00", "credit", "wages", "acctX", "x1"],   # 2025-12-08
        ["46000", "MERCHANT_B", "(420.00)", "debit", "supplies", "acctX", "x2"],
    ])
    # CSV یک: یک ردیفِ یکتا + یک ردیفِ *دقیقاً یکسان* با ردیفِ اول xlsx (برای dedupِ بین‌منبعی)
    csv1 = src["csv_dir"] / "Armin.csv"
    csv1.write_text(
        "Date,Merchant,Amount,Transaction Type,Category,Account,ID\n"
        "2026-01-15,MERCHANT_C,1000.00,credit,income,acctY,c1\n"
        "2025-12-08,MERCHANT_A,$250.00,credit,wages,acctX,dup\n",   # == ردیفِ x1 → dedup
        "utf-8")
    return src


def t_a_load_to_cents():
    _seed_sources()
    txns = ts.load_all()
    by_desc = {t["desc"]: t for t in txns}
    assert by_desc["MERCHANT_A"]["amount_cents"] == 25000, by_desc["MERCHANT_A"]
    assert by_desc["MERCHANT_B"]["amount_cents"] == -42000, by_desc["MERCHANT_B"]
    assert by_desc["MERCHANT_C"]["amount_cents"] == 100000, by_desc["MERCHANT_C"]
    # Excel-serial → ISO
    assert by_desc["MERCHANT_A"]["date"] == "2025-12-08", by_desc["MERCHANT_A"]["date"]
    # منشأ: A از xlsx (اولین بار)، C از csv
    assert by_desc["MERCHANT_A"]["source"] == "pocketsmith", by_desc["MERCHANT_A"]["source"]
    assert by_desc["MERCHANT_C"]["source"].startswith("csv:"), by_desc["MERCHANT_C"]["source"]


def t_b_dedup_cross_source():
    txns = ts.load_all()
    # سه ردیفِ منطقی: A، B، C — نه چهار (ردیفِ dupِ CSV باید با x1 ادغام شود)
    assert len(txns) == 3, [t["desc"] for t in txns]
    ids = [t["id"] for t in txns]
    assert len(ids) == len(set(ids)), "شناسه‌ها باید یکتا باشند"


def t_c_reconcile_tie_out():
    txns = ts.load_all()
    rep = ts.reconcile_report(txns)
    assert rep["tie_out_ok"] is True, rep
    # netِ کل = 25000 - 42000 + 100000 = 83000 (تجمیعی، برای اثباتِ تراز)
    assert rep["total_net_cents"] == 83000, rep["total_net_cents"]
    assert rep["total_rows"] == 3, rep
    # جمعِ netهای per-source == کلِ net (مسیرِ مستقل)
    assert sum(d["net_cents"] for d in rep["per_source"].values()) == rep["total_net_cents"]


def t_d_schema_fields():
    t = ts.load_all()[0]
    for k in ("id", "date", "amount_cents", "desc", "source", "account",
              "owner", "ptype", "category", "review", "note"):
        assert k in t, f"فیلدِ {k} در schema نیست"
    assert t["owner"] == "unknown" and t["ptype"] == "unknown" and t["review"] == "pending"
    assert isinstance(t["amount_cents"], int), "مبلغ باید عددِ صحیحِ سنت باشد (نه float)"


def t_e_save_atomic_roundtrip():
    txns = ts.load_all()
    out = opslib.STATE_DIR / "txn-store.json"
    ts.save(txns, out)
    doc = json.loads(out.read_text("utf-8"))
    assert doc["_schema"] == "txn-store.v1" and doc["count"] == len(txns)
    assert len(doc["txns"]) == len(txns)
    # مسیرِ پیش‌فرض هم درست به personal/txn-store.json اشاره کند (gitignore)
    assert ts.default_store_path().name == "txn-store.json"
    assert ts.default_store_path().parent.name == "personal"


if __name__ == "__main__":
    for f in (t_a_load_to_cents, t_b_dedup_cross_source, t_c_reconcile_tie_out,
              t_d_schema_fields, t_e_save_atomic_roundtrip):
        f()
        print("ok", f.__name__)
    print("PASS test_txn_store")
