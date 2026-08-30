# -*- coding: utf-8 -*-
"""تستهای آزمایشگاه (sandbox) — گیت ماشینی فاز ۳. همهٔ تستها fail-closed را میسنجند."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab"))

from lab.runner import SandboxRunner, _scan  # noqa: E402


def _runner():
    return SandboxRunner(workspace_root=Path(__file__).resolve().parent / "_tmp_lab_ws")


def test_valid_candidate_runs_and_writes_inside_workspace():
    src = 'from pathlib import Path\np = Path("out.txt")\np.write_text("ok", encoding="utf-8")\nprint("DONE")\n'
    r = _runner().run(src, name="ok1", timeout_s=10)
    assert r["ok"] is True and r["blocked"] is False
    assert r["exit_code"] == 0
    assert "DONE" in r["stdout_tail"]
    assert "out.txt" in r["files_created"]


def test_socket_import_blocked():
    src = "import socket\nprint(1)\n"
    r = _runner().run(src, name="net", timeout_s=5)
    assert r["blocked"] is True and r["ok"] is False
    kinds = [e["pattern"] for e in r["security_events"]]
    assert any("socket" in k for k in kinds)


def test_subprocess_and_os_system_blocked():
    for src in ("import subprocess\nsubprocess.run(['calc'])\n",
                "import os\nos.system('calc')\n"):
        r = _runner().run(src, name="proc", timeout_s=5)
        assert r["blocked"] is True


def test_absolute_path_write_blocked():
    src = 'from pathlib import Path\nPath("C:/Windows/Temp/evil.txt").write_text("x")\n'
    r = _runner().run(src, name="abs", timeout_s=5)
    assert r["blocked"] is True
    assert any(e["kind"] == "absolute-path-literal" for e in r["security_events"])


def test_env_access_blocked_fail_closed():
    src = "import os\nprint(os.environ.get('SOME_TOKEN'))\n"
    r = _runner().run(src, name="env", timeout_s=5)
    assert r["blocked"] is True
    assert any(e["pattern"] == "os.environ" for e in r["security_events"])


def test_infinite_loop_killed_by_timeout():
    src = "while True:\n    pass\n"
    t0 = time.time()
    r = _runner().run(src, name="loop", timeout_s=2)
    assert r["timeout"] is True
    assert time.time() - t0 < 10
    assert "killed" in r["stderr_tail"] or r["exit_code"] is not None


def test_scan_detects_drive_literal_and_tilde():
    assert _scan('p = Path("E:/x")')[0]["kind"] == "absolute-path-literal"
    assert _scan('p = Path("~/x")')[0]["kind"] == "absolute-path-literal"


def test_verdict_is_honest_about_isolation():
    v = SandboxRunner._verdict()
    assert v["level"] == "policy_workspace_env_timeout"
    assert v["os_namespace_isolation"] is False


def test_runner_never_raises():
    r = SandboxRunner(workspace_root=Path(__file__).resolve().parent / "_tmp_lab_ws2") \
        .run(None, name="bad", timeout_s=1)  # type: ignore[arg-type]
    assert isinstance(r, dict) and "schema" in r and "ok" in r
