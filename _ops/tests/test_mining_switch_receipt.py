"""test_mining_switch_receipt — رسیدِ سوییچِ کوین (D-015)."""
import os
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("switch-receipt")

_OPS = harness.REAL_VAULT / "_ops"
_LEGS = _OPS / "legs"
for _p in (str(_OPS), str(_LEGS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mining_switch_receipt as msr  # noqa: E402

# مسیرِ موقت برای فایلِ JSONL — هرگز در ولتِ زنده نمی‌نویسد
_TMP_JSONL = Path(tempfile.mktemp(suffix=".jsonl", prefix="test-sr-"))


def _cleanup():
    _TMP_JSONL.unlink(missing_ok=True)


def _set_env():
    os.environ["OCTOPUS_MINING_SWITCH_RECEIPT_FILE"] = str(_TMP_JSONL)


def _clr_env():
    os.environ.pop("OCTOPUS_MINING_SWITCH_RECEIPT_FILE", None)


# ─── ۱: record_switch ────────────────────────────────────────────────────
def t_record_switch_appends_a_row():
    """record_switch یک ردیفِ JSON به فایل اضافه می‌کند."""
    try:
        _set_env()
        row = msr.record_switch(node_id="OPI-01", from_coin="VRSC",
                                to_coin="SAL", algo="verushash", now=1700000000.0)
        assert row["node"] == "OPI-01"
        assert row["from"] == "VRSC"
        assert row["to"] == "SAL"
        assert row["algo"] == "verushash"
        assert "ts" in row
        # فایل باید وجود داشته باشد و JSONL معتبر باشد
        lines = _TMP_JSONL.read_text("utf-8").strip().splitlines()
        assert len(lines) == 1
    finally:
        _clr_env()
        _cleanup()


def t_record_switch_returns_dict():
    """خروجی همیشه dict است."""
    try:
        _set_env()
        row = msr.record_switch(node_id="N1", from_coin="A", to_coin="B")
        assert isinstance(row, dict)
        assert "ts" in row and "node" in row
    finally:
        _clr_env()
        _cleanup()


# ─── ۲: recent_switches ────────────────────────────────────────────────
def t_recent_switches_returns_last_n():
    """آخرین n رسید (برعکسِ زمانی)."""
    try:
        _set_env()
        for i in range(5):
            msr.record_switch(node_id=f"N{i}", from_coin="X", to_coin="Y",
                              now=1700000000.0 + i * 100)
        recent = msr.recent_switches(n=3)
        assert len(recent) == 3
        # اولین عنصر = آخرین نوشته (N4)
        assert recent[0]["node"] == "N4"
        assert recent[1]["node"] == "N3"
        assert recent[2]["node"] == "N2"
    finally:
        _clr_env()
        _cleanup()


def t_recent_switches_fail_soft_on_missing_file():
    """فایلِ ناموجود → []."""
    _clr_env()
    result = msr.recent_switches()
    assert result == []


# ─── ۳: append مستقیم (نه overwrite) ─────────────────────────────────────
def t_multiple_records_all_persist():
    """چند record پشت سر هم همه ذخیره می‌شوند (append)."""
    try:
        _set_env()
        msr.record_switch(node_id="A", from_coin="X", to_coin="Y", now=100.0)
        msr.record_switch(node_id="B", from_coin="X", to_coin="Z", now=200.0)
        msr.record_switch(node_id="C", from_coin="Z", to_coin="W", now=300.0)
        lines = _TMP_JSONL.read_text("utf-8").strip().splitlines()
        assert len(lines) == 3, f"expected 3 lines, got {len(lines)}"
    finally:
        _clr_env()
        _cleanup()


# ─── ۴: receipt_text ────────────────────────────────────────────────────
def t_receipt_text_mentions_nodes_and_coins():
    """متنِ رسید حاوی نامِ نود و کوین‌هاست."""
    txt = msr.receipt_text("OPI-02", "Verus", "Salvium")
    assert "OPI-02" in txt
    assert "Verus" in txt
    assert "Salvium" in txt


def t_receipt_text_says_registered_not_executed():
    """متنِ رسید فقط «ثبت شد» می‌گوید، نه «اجرا شد»."""
    txt = msr.receipt_text("N1", "A", "B")
    assert "ثبت شد" in txt
    assert "اجرا شد" not in txt


def t_receipt_text_mentions_d015():
    """متنِ رسید به D-015 ارجاع می‌دهد."""
    txt = msr.receipt_text("N1", "A", "B")
    assert "D-015" in txt


# ─── ۵: تستِ صداقتِ مسیرِ زنده ────────────────────────────────────────────
def t_no_ssh_no_network_imports():
    """ماژول SSH/requests/socket وارد نمی‌کند."""
    import ast
    tree = ast.parse(Path(msr.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "subprocess",
                             "paramiko", "fabric"}), imported


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_mining_switch_receipt: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
