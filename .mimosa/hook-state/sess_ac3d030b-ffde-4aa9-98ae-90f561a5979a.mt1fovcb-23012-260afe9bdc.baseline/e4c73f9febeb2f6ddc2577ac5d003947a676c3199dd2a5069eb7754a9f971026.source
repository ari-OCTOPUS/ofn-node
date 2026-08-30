# -*- coding: utf-8 -*-
"""تست‌های تولید دادهٔ runtime — گیت ماشینی فاز ۸ (قطعیبودن + قالب JS)."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))

from dashboard.gen_runtime_data import generate, _novelty_payload, _economy_payload  # noqa: E402


def test_generate_is_deterministic(tmp_path):
    import dashboard.gen_runtime_data as g
    orig = g.OUT_DIR
    g.OUT_DIR = tmp_path
    try:
        a = generate()
        b = generate()
        assert a == b
        for p in (tmp_path / "novelty-data.js", tmp_path / "economy-data.js"):
            assert p.exists()
            body = p.read_text("utf-8")
            assert body.endswith(";\n")
            assert re.match(r"^window\.[A-Z_]+ = \{", body)
    finally:
        g.OUT_DIR = orig


def test_payloads_grade_measured_and_no_hardcoded_secrets():
    n = _novelty_payload()
    assert n["grade"] == "MEASURED"
    assert n["cohort"]["exact_repeat_records"] == 15
    e = _economy_payload()
    assert e["grade"] == "MEASURED"
    assert e["invariants"]
    blob = json_dump(n) + json_dump(e)
    assert "TOKEN" not in blob.upper().replace("TOKENS", "").replace("TOKEN_", "")


def test_js_parses_if_node_available(tmp_path):
    import dashboard.gen_runtime_data as g
    orig = g.OUT_DIR
    g.OUT_DIR = tmp_path
    try:
        generate()
        for f in ("novelty-data.js", "economy-data.js"):
            try:
                r = subprocess.run(
                    ["node", "-e",
                     'const window = {}; eval(require("fs").readFileSync(process.argv[1], "utf8"));',
                     str(tmp_path / f)],
                    capture_output=True, text=True, timeout=30)
                assert r.returncode == 0, (r.stderr or r.stdout)[-300:]
            except FileNotFoundError:
                pass  # node در دسترس نیست؛ تست قالبِ regex قبلاً رد شده
    finally:
        g.OUT_DIR = orig


def json_dump(o):
    import json
    return json.dumps(o, ensure_ascii=False)
