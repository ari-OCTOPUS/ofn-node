from core.models import State
from tests.helpers import build


def test_start_then_status_then_stop(tmp_path):
    mgr, safety, runner = build(tmp_path)
    r = mgr.start("demo")
    assert r.state == State.RUNNING and r.detail == "روشن شد"
    assert mgr.status("demo").state == State.RUNNING
    r2 = mgr.stop("demo")
    assert r2.state == State.STOPPED
    assert mgr.status("demo").state == State.STOPPED


def test_disabled_project_refused(tmp_path):
    mgr, safety, runner = build(tmp_path, enabled=False)
    r = mgr.start("demo")
    assert r.state == State.STOPPED
    assert "غیرفعال" in r.detail


def test_halt_blocks_start(tmp_path):
    mgr, safety, runner = build(tmp_path)
    safety.halt("تست")
    r = mgr.start("demo")
    assert r.state == State.STOPPED
    assert "قفل ایمنی" in r.detail
    safety.resume()
    assert mgr.start("demo").state == State.RUNNING


def test_unknown_project(tmp_path):
    mgr, safety, runner = build(tmp_path)
    assert mgr.status("nope").state == State.UNKNOWN


def test_test_pass_and_fail(tmp_path):
    mgr, safety, runner = build(tmp_path)
    runner.run_result = (0, "همه سبز")
    ok, out = mgr.test("demo")
    assert ok is True
    runner.run_result = (1, "خطا")
    ok2, out2 = mgr.test("demo")
    assert ok2 is False


def test_double_start_is_idempotent(tmp_path):
    mgr, safety, runner = build(tmp_path)
    mgr.start("demo")
    r = mgr.start("demo")
    assert r.state == State.RUNNING
    assert "از قبل" in r.detail
