#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_fourd_wired.py — فاز ۷ دستورالعمل ۲۰۲۶-۰۸-۱۶: W1 اتصالِ 4d_system (read-only).

قیودِ اثبات‌شده:
  · بدونِ فلگ: صفر I/O — هیچ فایلی باز نمی‌شود (fail-closed)
  · با فلگ: نمای‌های مجاز خوانده می‌شوند؛ نامِ خارجِ اجازه‌نامه رد می‌شود
  · فقط-خواندنِ ساختاری: AST — open فقط حالتِ خواندن؛ write/remove/shutil ممنوع
  · wiring.py مرحلهٔ W1 را دارد و W2-W5 را ندارد (رأیِ مالک مانده)
"""
import ast
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("fourd-w1")

import fourd_access as fa   # noqa: E402


def test_flag_off_is_zero_io(monkeypatch):
    monkeypatch.setenv(fa.FLAG, "0")
    snap = fa.snapshot()
    assert snap["enabled"] is False and snap["views"] == {}
    r = fa.read_view("organism_state")
    assert r["reason"] == "flag-off" and "data" not in r


def test_flag_on_reads_allowed_views(monkeypatch):
    # فایل‌های state ایزولهٔ harness را بساز تا خواندن واقعی اثبات شود
    import opslib
    st = Path(opslib.STATE_DIR)
    (st / "ORGANISM-STATE.json").write_text(
        json.dumps({"beat": 7, "arbiter": {"color": "GREEN"}}), "utf-8")
    (st / "cardiac-budget.json").write_text(
        json.dumps({"daily_cap": 2000, "spent": 500}), "utf-8")
    monkeypatch.setenv(fa.FLAG, "1")
    snap = fa.snapshot()
    assert snap["enabled"] is True and snap["read_only"] is True
    assert snap["views"]["organism_state"]["beat"] == 7
    assert snap["views"]["cardiac_budget"]["daily_cap"] == 2000
    # فایلِ غایبِ مجاز = «unreadable» صادقانه، نه دروغ
    assert snap["views"]["heartstate"].get("error") == "unreadable"


def test_not_in_allowlist_denied(monkeypatch):
    monkeypatch.setenv(fa.FLAG, "1")
    r = fa.read_view("OCTOPUS-flags.cmd")        # حاملِ secret — خارجِ اجازه‌نامه
    assert r["error"] == "not-in-allowlist"
    r2 = fa.read_view("../.env")                  # traversal — خارجِ اجازه‌نامه
    assert r2["error"] == "not-in-allowlist"
    r3 = fa.read_view("OWNER-PROFILE.json")       # دادهٔ دستهٔ ویژه
    assert r3["error"] == "not-in-allowlist"


def test_structurally_read_only():
    """AST: ماژول هیچ عملیاتِ نوشتن ندارد — تضمینِ ساختاری، نه قولِ متن."""
    src = (_HERE.parent / "fourd_access.py").read_text("utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else \
                (f.attr if isinstance(f, ast.Attribute) else "")
            assert name not in ("write_text", "write_bytes", "remove", "unlink",
                                "mkdir", "rename", "replace"), \
                f"write-like call: {name}"
            if name == "open":
                modes = [a.value for a in node.args[1:]
                         if isinstance(a, ast.Constant)] + \
                        [kw.value for kw in node.keywords
                         if kw.arg == "mode" and isinstance(kw.value, ast.Constant)]
                for m in modes:
                    assert "w" not in str(m) and "a" not in str(m), \
                        f"open with write mode: {m}"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names]
            assert not any(m.startswith("shutil") for m in mods), "shutil ممنوع"
    # ماژول واقعاً هم تابعِ نوشتن ندارد
    public = [x for x in dir(fa) if not x.startswith("_")]
    assert not any(("write" in x or "save" in x or "delete" in x) for x in public)


def test_wiring_has_w1_and_not_w2_w5():
    src = (_HERE.parent / "wiring.py").read_text("utf-8")
    assert "FOURD_DATA_ACCESS" in src or "fourd_access" in src   # W1 stage-marker
    for later_stage_flag in ("FOURD_PROPOSE", "NBB_EVAL_FOURD"):
        assert later_stage_flag not in src, \
            f"{later_stage_flag} بدونِ رأیِ مالک وصل شده نباید"


def test_owner_verdict_registered_w1_only():
    text = (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")
    assert "FOURD_DATA_ACCESS" in text
    assert "FOURD_PROPOSE" not in text and "NBB_EVAL_FOURD" not in text


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
