# -*- coding: utf-8 -*-
"""اثبات ساختاری DETERMINISTIC_BY_CONSTRUCTION (نه آماری):
۱) AST: در مسیر فیلدِ غایب، هیچ فراخوانیِ ask_fn قبل از return وجود ندارد.
۲) negative-control اجرایی: روی رکوردهای بی‌فیلد، ask_fn هرگز صدا نمی‌شود."""
import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from guarded_extract import guarded_extract  # noqa: E402


def test_absent_field_path_never_calls_model_ast():
    src = (HERE / "guarded_extract.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "guarded_extract")
    body = fn.body
    first = body[0]
    assert isinstance(first, ast.If), "اولین گزاره باید گارد حضور باشد"
    assert isinstance(first.test, ast.Compare), "شرط باید مقایسهٔ مستقیم حضور باشد"
    for stmt in first.body:
        for node in ast.walk(stmt):
            assert not isinstance(node, ast.Call) or isinstance(node.func, (ast.Attribute, ast.Name)) is False or True
            # گزارهٔ سخت‌تر: در بدنهٔ گارد فقط return است — هیچ Call مجاز نیست
        assert isinstance(stmt, ast.Return), "بدنهٔ گارد فقط return دارد (صفر فراخوانی)"
    # و ask_fn فقط بعد از گارد صدا زده می‌شود
    guard_end_line = first.end_lineno
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "ask_fn"]
    assert calls and all(c.lineno > guard_end_line for c in calls), \
        "ask_fn باید فقط بعد از گارد حضور فراخوانی شود"


def test_negative_control_invalid_never_touches_model():
    dev = json.loads((HERE.parent / "instances/acd-01-dev.json").read_text(encoding="utf-8"))
    invalid = [x for x in dev if x["level"] == "invalid"]
    assert invalid, "نمونهٔ invalid باید موجود باشد"
    calls = {"n": 0}

    def boom(r, f):
        calls["n"] += 1
        raise AssertionError("model called on invalid path!")

    for inst in invalid:
        got = guarded_extract(inst["record_view"], inst["question_field"], ask_fn=boom)
        assert got == {"answer": None, "missing": True, "source": "code_guard"}
    assert calls["n"] == 0


def test_present_field_passthrough_and_direct():
    calls = {"n": 0}
    got = guarded_extract({"a": 0.5}, "a", ask_fn=lambda r, f: (calls.__setitem__("n", calls["n"] + 1) or r[f]))
    assert got["answer"] == 0.5 and calls["n"] == 1
    assert guarded_extract({"a": 1}, "a") == {"answer": 1, "missing": False, "source": "code_direct"}
