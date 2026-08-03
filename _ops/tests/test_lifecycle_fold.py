"""test_lifecycle_fold — تاشدگی باید در هر دو جهت حرکت کند، وگرنه کور است.

گامِ ۲ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C1).

سنجه‌های پذیرشِ سند:
  · شمارشِ درست روی فیکسچرِ قطعی (عددِ زندهٔ امروز عمداً هاردکد **نمی‌شود** —
    صف در فاصلهٔ همین جلسه از ۱۹ به ۲۰ رسید؛ تستی که عددِ لحظه‌ای را پین کند
    فردا به دلیلِ غلط قرمز می‌شود)
  · تحلیلِ AST: شمارِ صداکنندهٔ تولیدیِ **بیرونیِ** `load_rfc_verdicts` از ۰ به ≥۱
  · جهشِ دوجهته: یک رکورد SUBMITTED→DECIDED ⇒ stalled یکی کم؛ برگردان ⇒ برمی‌گردد
  · ایزوله: صفر بایتِ تغییر در کلِ `_ops/state/` حینِ اجرا

ناوردیِ بارِ اصلی که اینجا قفل می‌شود: **APPLIED بدونِ receipt_id اثر نیست.**
"""
import ast
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("lifecycle-fold")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lifecycle_fold as LF   # noqa: E402
import pending_card_recovery as pcr   # noqa: E402

NOW = 1_785_700_000.0


def _fixture(records, verdicts):
    """یک state_dir ِ کامل و ایزوله. هرگز زیرِ درختِ زنده نیست."""
    root = Path(tempfile.mkdtemp(prefix="lifecycle-fold-"))
    assert str(_OPS).lower() not in str(root).lower(), f"fixture inside live tree: {root}"
    (root / "pulse").mkdir(parents=True)
    (root / "pulse" / "pending-cards.json").write_text(
        json.dumps(records, ensure_ascii=False), encoding="utf-8")
    con = pcr._rfc_con(root)          # نویسندهٔ خودشان، پس اسکیما تضمینی درست است
    try:
        for rid, v in verdicts.items():
            con.execute(
                "INSERT OR REPLACE INTO rfc_decision"
                "(rfc_id,verdict,revision,state,lease_owner,lease_until,receipt_id,"
                "operation_key,updated_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                (rid, v.get("verdict", "approve"), 1, v.get("state", "SUBMITTED"),
                 None, None, v.get("receipt_id", ""), v.get("operation_key"), 0))
        con.commit()
    finally:
        con.close()
    return root


def _cards(n_stalled, n_decided):
    out = {}
    for i in range(n_stalled):
        out[f"rfc:S{i}"] = {"kind": "rfc", "rfc_id": f"S{i}", "delivery": "SENT",
                            "decision": "SUBMITTED", "created_ts": str(int(NOW - 86400 * (i + 1)))}
    for i in range(n_decided):
        out[f"rfc:D{i}"] = {"kind": "rfc", "rfc_id": f"D{i}", "delivery": "SENT",
                            "decision": "DECIDED", "created_ts": str(int(NOW - 3600))}
    return out


def t_counts_on_a_deterministic_fixture():
    root = _fixture(_cards(2, 3), {
        "D0": {"state": "APPLIED", "receipt_id": "rcpt-1"},
        "D1": {"state": "RECONCILE_REQUIRED", "receipt_id": ""},
        "D2": {"state": "RECONCILE_REQUIRED", "receipt_id": ""},
    })
    try:
        f = LF.fold(root, now=NOW)
        assert f["proposed"]["value"] == 5, f["proposed"]
        assert f["delivered"]["value"] == 5, f["delivered"]
        assert f["decided"]["value"] == 3, f["decided"]
        assert f["effected"]["value"] == 1, f["effected"]
        assert f["stalled"]["value"] == 2, f["stalled"]
        assert f["reconcile_required"]["value"] == 2, f["reconcile_required"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_applied_without_receipt_is_not_effected():
    """ناوردیِ بارِ اصلی: یک اثر بدونِ رسید، اثر نیست."""
    root = _fixture(_cards(0, 1), {"D0": {"state": "APPLIED", "receipt_id": ""}})
    try:
        f = LF.fold(root, now=NOW)
        assert f["effected"]["value"] == 0, "APPLIED با رسیدِ تهی نباید EFFECTED شمرده شود"
        assert f["decided"]["value"] == 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_two_way_mutation_stalled_moves_both_directions():
    """تاشدگی‌ای که فقط یک‌طرفه حرکت کند هنوز کور است."""
    root = _fixture(_cards(2, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    store_p = root / "pulse" / "pending-cards.json"
    try:
        assert LF.fold(root, now=NOW)["stalled"]["value"] == 2
        d = json.loads(store_p.read_text("utf-8"))
        d["rfc:S0"]["decision"] = "DECIDED"
        store_p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        assert LF.fold(root, now=NOW)["stalled"]["value"] == 1, "رو به پایین حرکت نکرد"
        d["rfc:S0"]["decision"] = "SUBMITTED"
        store_p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        assert LF.fold(root, now=NOW)["stalled"]["value"] == 2, "رو به بالا برنگشت"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_missing_field_is_unknown_not_zero():
    """کلیدِ غایب ⇒ UNKNOWN — دقیقاً تلهٔ پروبی که فیلدِ اشتباه را می‌خواند."""
    root = _fixture({"rfc:X": {"kind": "rfc", "rfc_id": "X", "delivery": "SENT"}}, {})
    try:
        f = LF.fold(root, now=NOW)
        assert f["by_stage"][LF.Stage.UNKNOWN] == 1, "رکوردِ بی‌decision باید UNKNOWN شود"
        assert f["stalled"]["value"] == 0, "و راکد شمرده نشود"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_absent_store_is_unknown_not_empty():
    root = Path(tempfile.mkdtemp(prefix="lifecycle-fold-empty-"))
    try:
        f = LF.fold(root, now=NOW)
        assert f["readable"] is False
        assert f["proposed"]["mode"] == "UNKNOWN", "ذخیرهٔ غایب نباید صفر رندر شود"
        assert "value" not in f["proposed"], "UNKNOWN نباید کلیدِ value داشته باشد"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_every_number_is_stamped():
    """ناوردیِ ۲: هیچ شمارشِ برهنه‌ای بیرون نمی‌رود."""
    root = _fixture(_cards(1, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    try:
        f = LF.fold(root, now=NOW)
        for key in ("proposed", "delivered", "decided", "effected", "stalled",
                    "reconcile_required", "unknown"):
            s = f[key]
            assert isinstance(s, dict) and "mode" in s and "source" in s, \
                f"{key} تمبر ندارد: {s!r}"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def t_state_dir_is_mandatory():
    """پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده — درسِ ثبت‌شده."""
    try:
        LF.fold(None)
    except ValueError:
        pass
    else:
        raise AssertionError("fold(None) باید استثنا بدهد، نه ذخیرهٔ زنده را بخواند")


def t_module_writes_nothing():
    """با AST، نه با grepِ متن — یک نام در docstring نوشتن نیست."""
    tree = ast.parse((_OPS / "lifecycle_fold.py").read_text("utf-8"))
    called = _calls_in(tree)
    # `replace` و `rename` عمداً در این فهرست **نیستند**: نامِ برهنه‌شان با
    # `str.replace` تصادم دارد و همین تست یک بار روی `str(db).replace("\\","/")`
    # قرمز شد — همان باگِ تصادمِ نامِ برهنه که در `orphan_scan` هم دهان باز کرده
    # بود. جای‌گزینی‌های فایل‌سیستمی جدا و با نامِ کامل سنجیده می‌شوند.
    forbidden = {"write_text", "write_bytes", "mkdir", "dump", "touch", "unlink",
                 "makedirs", "rmtree", "copy", "copy2"}
    bad = called & forbidden
    assert not bad, f"lifecycle_fold این‌ها را صدا می‌زند: {sorted(bad)}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("replace", "rename", "move") \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id in ("os", "shutil", "Path"):
            raise AssertionError(f"جای‌گزینیِ فایل‌سیستمی: {node.func.value.id}.{node.func.attr}")
    # `open` فقط اگر با حالتِ نوشتن باشد ممنوع است
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            mode = ""
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            assert not any(c in mode for c in "wax+"), f"open با حالتِ نوشتن: {mode!r}"


def t_load_rfc_verdicts_now_has_an_external_production_caller():
    """سنجهٔ AST ِ سند: از ۰ صداکنندهٔ بیرونی به ≥۱.

    AST نه grep — grep کامنت را می‌شمارد و `from pkg import mod` را از دست می‌دهد.
    """
    callers = []
    for path in list(_OPS.glob("*.py")) + list((_OPS / "outcomes").glob("*.py")):
        if path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "attr", None) or getattr(fn, "id", None)
                if name == "load_rfc_verdicts":
                    callers.append(path.name)
    external = [c for c in callers if c != "pending_card_recovery.py"]
    assert external, ("load_rfc_verdicts هنوز صفر صداکنندهٔ بیرونی دارد؛ "
                      f"همهٔ صداکننده‌ها داخلی‌اند: {callers}")
    assert "lifecycle_fold.py" in external, external


def t_fold_on_the_live_store_creates_no_files():
    """🔴 ادعا از سنجه بزرگ‌تر بود: fold روی **خودِ** state ِ زنده هم نباید چیزی بسازد.

    تستِ زیر فقط ثابت می‌کرد اجرا روی **فیکسچر** به state ِ زنده دست نمی‌زند — که
    ادعای ضعیف‌تری است. دو لِینِ مستقل کشف کردند مسیرِ ساده به
    `pcr._rfc_con()` می‌رسد که `mkdir` + WAL + `CREATE TABLE` می‌زند، یعنی یک
    سطحِ خواندنی روی دیتابیسِ نزدیکِ پول اتصالِ نوشتنی باز می‌کند.
    """
    live = _OPS / "state"
    doctor = live / "doctor"
    before = {p.name for p in doctor.glob("*")} if doctor.exists() else set()
    LF.fold(live)                     # روی ذخیرهٔ **زنده**، فقط‌خواندنی
    after = {p.name for p in doctor.glob("*")} if doctor.exists() else set()
    new = after - before
    assert not new, f"fold روی ذخیرهٔ زنده فایل ساخت: {sorted(new)}"


def _calls_in(tree):
    """نامِ هر تابعی که واقعاً **صدا زده** می‌شود — با AST، نه با grepِ متن."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            nm = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if nm:
                out.add(nm)
    return out


def t_fold_never_opens_a_writable_connection():
    """گاردِ ساختاری: مسیرِ خواندن نباید سازندهٔ نوشتنی را صدا بزند.

    با AST سنجیده می‌شود، نه با grepِ متن. نسخهٔ اولِ همین assert روی docstringی
    قرمز شد که خودش توضیح می‌داد **چرا** `_rfc_con` صدا زده نمی‌شود — سومین بارِ
    امروز که همین تله دهان باز کرد. یک نام در مستندات فراخوانی نیست.
    """
    src = (_OPS / "lifecycle_fold.py").read_text("utf-8")
    assert "mode=ro" in src, "مسیرِ خواندنی اتصالِ read-only ندارد"
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_read_verdicts"), None)
    assert fn is not None, "_read_verdicts پیدا نشد"
    called = _calls_in(fn)
    assert "connect" in called, "اتصالِ صریحِ read-only باز نمی‌شود"
    # `load_rfc_verdicts` فقط در شاخهٔ fail-soft مجاز است؛ `_rfc_con` هرگز مستقیم.
    assert "_rfc_con" not in called, f"سازندهٔ نوشتنی مستقیم صدا زده می‌شود: {sorted(called)}"


def t_fold_touches_zero_bytes_of_live_state():
    """سنجهٔ ایزولهٔ سند: کلِ `_ops/state/` حینِ اجرا بایت‌به‌بایت دست‌نخورده."""
    live = _OPS / "state"
    def snapshot():
        out = {}
        for p in live.rglob("*"):
            if p.is_file():
                try:
                    st = p.stat()
                    out[str(p)] = (st.st_size, st.st_mtime_ns)
                except OSError:
                    pass
        return out
    before = snapshot()
    root = _fixture(_cards(1, 1), {"D0": {"state": "RECONCILE_REQUIRED"}})
    try:
        LF.fold(root, now=NOW)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    after = snapshot()
    changed = [k for k in before if k in after and before[k] != after[k]]
    added = [k for k in after if k not in before]
    assert not changed, f"فایلِ زنده تغییر کرد: {changed[:5]}"
    assert not added, f"فایلِ تازه در state زنده ساخته شد: {added[:5]}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_lifecycle_fold: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
