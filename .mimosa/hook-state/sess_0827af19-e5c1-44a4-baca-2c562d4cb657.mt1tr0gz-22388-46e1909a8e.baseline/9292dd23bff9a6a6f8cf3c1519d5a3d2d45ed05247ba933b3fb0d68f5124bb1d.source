#!/usr/bin/env python3
"""Offline, hermetic test for M6 (now_moves/module_self_manifest).

Stdlib-only · no network. Builds the manifest against a SYNTHETIC module root
(two tiny .py files) to verify reverse-dependency indexing, entrypoint capture,
resolved wire-flag state, and write-vs-dry — without touching the real tree.
Standalone (exit 0/1) per run_all.py.
"""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="m6_manifest_")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS / "cortex"), str(OPS / "budget"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import module_self_manifest as P                          # noqa: E402


def _mkroot():
    d = Path(tempfile.mkdtemp(prefix="m6_root_"))
    (d / "wiring.py").write_text('"""Fake wiring hub."""\ndef w():\n    pass\n', "utf-8")
    (d / "caller.py").write_text('"""A caller."""\nimport wiring\ndef c():\n    pass\n', "utf-8")
    return d


def test_reverse_deps_and_entrypoints():
    m = P.build_manifest(root=_mkroot())
    mods = m.get("modules", {})
    assert "wiring.py" in mods and "caller.py" in mods, list(mods)
    assert "caller" in mods["wiring.py"]["imported_by"], mods["wiring.py"]
    assert mods["caller.py"]["entrypoints"] == ["c"], mods["caller.py"]
    assert mods["caller.py"]["depends_on"] == ["wiring"], mods["caller.py"]
    print("  ok manifest              -> reverse-deps + entrypoints + depends_on")


def test_flag_on_env():
    os.environ["OCTOPUS_WIRE_ZTEST"] = "1"
    assert P._flag_on("OCTOPUS_WIRE_ZTEST") is True
    os.environ.pop("OCTOPUS_WIRE_ZTEST", None)
    assert P._flag_on("OCTOPUS_WIRE_ZTEST") is False
    print("  ok flag resolution       -> env=1 True, unset+no-file False")


def test_flag_state_dict_present():
    m = P.build_manifest(root=_mkroot())
    assert isinstance(m.get("wire_flag_state"), dict), m.get("wire_flag_state")
    assert "n_flags_armed" in m and "self_awareness_pct" in m, list(m)
    print("  ok globals               -> wire_flag_state dict + counts present")


def test_write_vs_dry():
    root = _mkroot()
    out = Path(tempfile.mkdtemp(prefix="m6_out_")) / "manifest.json"
    m = P.write_manifest(root=root, path=out)
    assert out.exists() and m.get("written") == str(out), m.get("written")
    m2 = P.build_manifest(root=root)
    assert "written" not in m2, "build_manifest alone must not write"
    print("  ok write vs build        -> write_manifest writes; build_manifest doesn't")


def _run():
    tests = [test_reverse_deps_and_entrypoints, test_flag_on_env,
             test_flag_state_dict_present, test_write_vs_dry]
    print("test_module_self_manifest (M6) — offline, hermetic")
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as e:
        print("FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERROR:", type(e).__name__, e); sys.exit(1)
    sys.exit(0)
