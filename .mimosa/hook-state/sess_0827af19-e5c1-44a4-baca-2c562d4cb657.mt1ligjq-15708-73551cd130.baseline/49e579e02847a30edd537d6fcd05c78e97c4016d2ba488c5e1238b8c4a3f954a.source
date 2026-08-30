"""test_selfknow_vault_propose.py — ۲۰۲۶-۰۸-۰۵.

تشخیصِ سنتزشدهٔ self_knowledge.py (anatomy/pathology/prescription) به
`vault_updater.propose()` وصل شد — از قبل ساخته و تست شده، صفر صداکننده.
عمداً **فقط propose()، هرگز apply()**: صفر بایت در vault، فقط یک لاگِ محلیِ
جدید (`state/doctor/vault-proposals.jsonl`). شرطِ شلیک دقیقاً روی گذر از
آستانه‌ی سه‌چرخه‌ی پایدار است، نه هر چرخهٔ cached — تا صف اسپم نشود.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("selfknow-vault-propose")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import self_knowledge as sk  # noqa: E402

_SB = Path(ENV["ops"]) / "state"


def _sandbox():
    opslib.STATE_DIR = _SB
    (_SB / "doctor").mkdir(parents=True, exist_ok=True)
    lp = _SB / "doctor" / "vault-proposals.jsonl"
    if lp.exists():
        lp.unlink()   # ایزولاسیونِ بینِ تست‌ها — _SB مشترک است


def _rec(stable_cycles, version=7):
    return {
        "version": version, "stable_cycles": stable_cycles,
        "snapshot_hash": "abc123deadbeef",
        "understanding": {
            "anatomy": "۳ لِگ، ۵ سیمِ روشن",
            "pathology": [{"symptom": "ترس بالا", "root_cause": "لیدِ خشک",
                          "severity": "high"}],
            "prescription": [{"action": "یک لِگ را به لیدِ واقعی وصل کن",
                              "why": "ترس را می‌شکند", "priority": "high"}],
        },
    }


def _log_path():
    return _SB / "doctor" / "vault-proposals.jsonl"


def t_a_flag_off_is_exactly_nothing():
    _sandbox()
    import os
    os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)
    sk._maybe_propose_to_vault(_rec(3))
    assert not _log_path().exists(), "فلگ خاموش نباید هیچ فایلی بسازد"


def t_b_below_threshold_no_propose():
    _sandbox()
    import os
    os.environ[sk._VAULT_PROPOSE_FLAG] = "1"
    try:
        sk._maybe_propose_to_vault(_rec(2))
        assert not _log_path().exists(), "زیرِ آستانه نباید propose کند"
    finally:
        os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)


def t_c_exactly_at_threshold_fires_once():
    _sandbox()
    import os
    os.environ[sk._VAULT_PROPOSE_FLAG] = "1"
    try:
        sk._maybe_propose_to_vault(_rec(sk._VAULT_PROPOSE_STABLE_CYCLES))
        assert _log_path().exists(), "دقیقاً روی آستانه باید propose کند"
        rows = _log_path().read_text(encoding="utf-8").strip().splitlines()
        assert len(rows) == 1, rows
        row = json.loads(rows[0])
        prop = row.get("proposal")
        assert isinstance(prop, dict)
        # ⚠️ نه فقط «کلیدِ status هست» — مقادیرِ **واقعیِ** propose() را می‌سنجیم
        # تا جهشی که فراخوانی را نگه می‌دارد ولی نتیجه‌اش را تقلبی می‌کند
        # (مثلاً `proposal = {"status": "FAKE"}`) هم گرفته شود.
        assert prop.get("status") == "OK", prop
        assert prop.get("commit_mode") == "GATE", prop     # هرگز AUTO — تصمیمِ مالک لازم است
        assert prop.get("target_path") == \
            "07 - Knowledge/شناخت-اختاپوس/DOCTOR-SELF-KNOWLEDGE.md", prop
        assert "stable_cycles=3" in (prop.get("ledger_entry") or {}).get("provenance", ""), prop
    finally:
        os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)


def t_d_past_threshold_does_not_re_fire():
    """۴ چرخهٔ پایدار = یک چرخه بعدِ آستانه؛ نباید دوباره propose کند (ضدِ اسپم)."""
    _sandbox()
    import os
    os.environ[sk._VAULT_PROPOSE_FLAG] = "1"
    try:
        sk._maybe_propose_to_vault(_rec(sk._VAULT_PROPOSE_STABLE_CYCLES + 1))
        assert not _log_path().exists(), "بالاترِ آستانه نباید دوباره propose کند"
    finally:
        os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)


def t_e_propose_never_touches_the_real_vault():
    """propose() خودش هرگز روی دیسک نمی‌نویسد — apply() هرگز صدا زده نمی‌شود.

    ⚠️ گرهِ AST، نه grep روی متن: کامنتِ بالای همین کد صریح می‌گوید
    «هرگز vault_updater_apply.apply()» — یک assert ِ زیررشته‌ای به همان
    کامنت می‌خورد، نه به کد."""
    import ast
    src = Path(sk.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported_names = set()
    called_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(a.name for a in node.names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                called_names.add((node.func.value.id, node.func.attr))
    assert "vault_updater_apply" not in imported_names, \
        "self_knowledge نباید vault_updater_apply را import کند"
    assert ("vault_updater", "propose") in called_names, \
        "propose() باید واقعاً صدا زده شود"
    assert ("vault_updater", "apply") not in called_names, \
        "apply() هرگز نباید از این ماژول صدا زده شود"


def t_f_missing_understanding_is_a_safe_noop():
    _sandbox()
    import os
    os.environ[sk._VAULT_PROPOSE_FLAG] = "1"
    try:
        rec = _rec(sk._VAULT_PROPOSE_STABLE_CYCLES)
        rec["understanding"] = {}
        sk._maybe_propose_to_vault(rec)
        assert not _log_path().exists(), "فهمِ خالی نباید propose بسازد"
    finally:
        os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)


def t_g_a_broken_vault_updater_import_never_crashes_run():
    """fail-soft: اگر import خراب شود، تابع نباید استثنا پرتاب کند."""
    _sandbox()
    import os
    import sys as _s
    os.environ[sk._VAULT_PROPOSE_FLAG] = "1"
    poisoned = object()
    _s.modules["vault_updater"] = poisoned  # noqa: NOQA — عمداً خراب
    try:
        sk._maybe_propose_to_vault(_rec(sk._VAULT_PROPOSE_STABLE_CYCLES))  # نباید استثنا بدهد
    finally:
        _s.modules.pop("vault_updater", None)
        os.environ.pop(sk._VAULT_PROPOSE_FLAG, None)


if __name__ == "__main__":
    for f in (t_a_flag_off_is_exactly_nothing, t_b_below_threshold_no_propose,
              t_c_exactly_at_threshold_fires_once, t_d_past_threshold_does_not_re_fire,
              t_e_propose_never_touches_the_real_vault, t_f_missing_understanding_is_a_safe_noop,
              t_g_a_broken_vault_updater_import_never_crashes_run):
        f()
        print("ok", f.__name__)
    print("PASS test_selfknow_vault_propose")
