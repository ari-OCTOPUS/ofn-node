"""Lock: isolated pytest collection must resolve `import opslib`.

Full-suite collect can look green because an earlier test inserts
`ofn/budget` onto sys.path. CI must fail if that pollution is the only
reason `tools/experiments_output.py` imports.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "ofn" / "budget" / "opslib.py"
SHIM = ROOT / "budget" / "opslib.py"


def test_live_opslib_body_still_the_r0_pin() -> None:
    assert LIVE.is_file(), "do not replace the live board shim with a stub body"
    assert SHIM.is_file(), "tools/ insert <repo>/budget; that path must exist"


def test_bare_import_via_tools_budget_path() -> None:
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; from pathlib import Path; "
         "sys.path.insert(0, str(Path(r'%s') / 'budget')); "
         "import opslib; print(opslib.now_iso()); "
         "assert opslib.STATE_DIR" % ROOT],
        cwd=str(ROOT), capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_experiments_output_collects_in_isolation() -> None:
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "pytest",
         "tests/test_experiments_output.py", "--collect-only", "-q"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,
    )
    # #region agent log
    try:
        import json, time
        open(r"F:\backup\debug-11f994.log", "a", encoding="utf-8").write(
            json.dumps({"sessionId": "11f994", "runId": "post-fix",
                        "hypothesisId": "D",
                        "location": "tests/test_opslib_import_boundary.py",
                        "message": "isolated_collect",
                        "data": {"exit": proc.returncode,
                                 "out_tail": (proc.stdout or "")[-240:],
                                 "err_tail": (proc.stderr or "")[-240:]},
                        "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass
    # #endregion
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "error" not in (proc.stdout + proc.stderr).lower()
    assert "collected" in (proc.stdout + proc.stderr)


def test_experiments_output_import_does_not_need_prior_tests() -> None:
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; from pathlib import Path; r=Path(r'%s'); "
         "sys.path.insert(0, str(r)); sys.path.insert(0, str(r/'tools')); "
         "import experiments_output; print(experiments_output.SCHEMA)" % ROOT],
        cwd=str(ROOT), capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "octopus.experiments-output.v1" in proc.stdout
