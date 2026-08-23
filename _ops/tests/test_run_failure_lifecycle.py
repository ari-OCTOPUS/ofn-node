#!/usr/bin/env python3
"""test_run_failure_lifecycle.py — runهای شکست‌خورده باید واقعاً FAILED شوند.

چرا این فایل هست (2026-08-23):
    `event_stream.fail_run()` وجود داشت، تست داشت، و **صفر صداکنندهٔ تولیدی**.
    یعنی: `start_run()` run می‌ساخت، `complete_run()` فقط در مسیرِ موفق صدا
    می‌شد، و هر استثنایی که از میانهٔ `collaborator.handle` بیرون می‌زد run را
    برای همیشه غیرترمینال رها می‌کرد — `_state_from_events` تا ابد "ACTIVE".
    مالک یک گفتگوی شکست‌خورده را در تایم‌لاین «هنوز در جریان» می‌دید.

    مصداقِ واقعیِ مسیرِ بی‌پوشش: `_model_enhance()` در handle داخلِ try نیست
    (برخلافِ تقریباً هر بلوکِ دیگر). اگر آداپتورِ مدل **استثنا پرتاب کند** (نه
    اینکه ok=False برگرداند) استثنا از handle بیرون می‌زند.

    درسِ مربوط: `feedback-tested-module-zero-callers`.

دو نکتهٔ روشِ تست (هر دو در نسخهٔ اولِ همین فایل اشتباه بودند و تست را
دروغ‌سبز/دروغ‌قرمز می‌کردند):
  ۱. harness عمداً `OCTOPUS_WIRE_COLLAB=0` می‌گذارد («Suites that need them
     re-arm explicitly» — harness.py). بدونِ re-arm، `handle()` در همان خطِ
     اولِ `_is_enabled()` برمی‌گردد و هیچ runی ساخته نمی‌شود.
  ۲. شناساییِ run با «جدیدترین فایل» غلط است: فیکسچرهای این فایل هم با
     `run_` شروع می‌شوند. باید قبل/بعد snapshot گرفت.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("run-failure-lifecycle")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "cognitive"))

import run_store as rs  # noqa: E402
import event_stream as es  # noqa: E402

sys.path.insert(0, str(_OPS / "owner_console"))
import collaborator  # noqa: E402


def _fresh_store():
    rs.STATE_DIR = Path(ENV["ops"]) / "state"
    rs.RUNS_DIR = rs.STATE_DIR / "cognitive" / "runs"


def _existing_runs() -> set:
    if not rs.RUNS_DIR.is_dir():
        return set()
    return {p.stem for p in rs.RUNS_DIR.glob("*.jsonl")}


def _run_created_by(fn):
    """fn را اجرا کن و شناسهٔ runِ **تازه‌ساخته‌شده** را برگردان.

    snapshot قبل/بعد — نه «جدیدترین فایل»، چون فیکسچرهای این فایل هم
    `run_*` نام دارند و mtime روی FAT/NTFS دانه‌درشت است.
    """
    before = _existing_runs()
    exc = None
    try:
        fn()
    except BaseException as e:  # noqa: BLE001 — صداکننده تصمیم می‌گیرد
        exc = e
    new = _existing_runs() - before
    assert len(new) == 1, f"انتظار دقیقاً یک runِ نو، دیده شد {sorted(new)}"
    return new.pop(), exc


class _ArmCollab:
    """re-arm ِ فلگِ collab فقط برای طولِ یک تست (harness عمداً خاموشش می‌کند)."""

    def __init__(self, use_model: bool = False):
        self.use_model = use_model
        self._prev = {}

    def __enter__(self):
        for k, v in (("OCTOPUS_WIRE_COLLAB", "1"),
                     ("OCTOPUS_COLLAB_USE_MODEL", "1" if self.use_model else "0")):
            self._prev[k] = os.environ.get(k)
            os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, v in self._prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


# ---------------------------------------------------------------- fail_run itself

def t_fail_run_makes_run_terminal_failed():
    _fresh_store()
    rs.create_run("fixture_fail_direct")
    es.fail_run("fixture_fail_direct", "model timeout")
    run = rs.get_run("fixture_fail_direct")
    assert run["state"] == "FAILED", f"انتظار FAILED، دیده شد {run['state']}"


def t_failed_run_is_not_active():
    """رگرسیونِ اصلی: runِ شکست‌خورده نباید ACTIVE بماند."""
    _fresh_store()
    rs.create_run("fixture_fail_notactive")
    rs.append_event("fixture_fail_notactive", "INTENT_DETECTED")
    es.fail_run("fixture_fail_notactive", "boom")
    assert rs.get_run("fixture_fail_notactive")["state"] != "ACTIVE"


# ---------------------------------------------------------------- wiring

def t_exception_in_handle_marks_run_failed():
    """قلبِ این batch: استثنا از میانهٔ handle ⇒ run ترمینالِ FAILED."""
    _fresh_store()
    orig = collaborator._model_enhance

    def _boom(base_reply, owner_text):
        raise RuntimeError("simulated adapter blowup")

    collaborator._model_enhance = _boom
    try:
        with _ArmCollab(use_model=True):
            rid, exc = _run_created_by(lambda: collaborator.handle("سلام"))
        assert isinstance(exc, RuntimeError), (
            f"استثنا باید به صداکننده برسد، نه بلعیده شود (دیده شد {exc!r})")
        run = rs.get_run(rid)
        assert run["state"] == "FAILED", (
            f"run باید FAILED باشد، دیده شد {run['state']} — fail_run سیم نشده")
        kinds = [e.get("event_type") for e in rs.list_events(rid)]
        assert "RUN_FAILED" in kinds, f"RUN_FAILED ثبت نشد: {kinds}"
    finally:
        collaborator._model_enhance = orig


def t_failure_reason_carries_no_owner_text():
    """ناوردیِ redaction: نامِ نوعِ استثنا ثبت می‌شود، نه متنش/ورودیِ مالک."""
    _fresh_store()
    orig = collaborator._model_enhance
    secret = "رمزعبورِ محرمانهٔ مالک"

    def _boom(base_reply, owner_text):
        raise RuntimeError(secret)

    collaborator._model_enhance = _boom
    try:
        with _ArmCollab(use_model=True):
            rid, _ = _run_created_by(lambda: collaborator.handle(secret))
        blob = str(rs.list_events(rid))
        assert secret not in blob, "متنِ مالک/استثنا به لاگِ run نشت کرد!"
        assert "unhandled:RuntimeError" in blob, f"نوعِ استثنا ثبت نشد: {blob[:300]}"
    finally:
        collaborator._model_enhance = orig


def t_successful_run_still_completes():
    """گاردِ رگرسیون: مسیرِ موفق نباید FAILED شود و نباید دوباره ترمینال شود."""
    _fresh_store()
    with _ArmCollab(use_model=False):
        rid, exc = _run_created_by(lambda: collaborator.handle("سلام"))
    assert exc is None, f"مسیرِ موفق استثنا داد: {exc!r}"
    kinds = [e.get("event_type") for e in rs.list_events(rid)]
    assert "RUN_COMPLETED" in kinds, f"مسیرِ موفق کامل نشد: {kinds}"
    assert "RUN_FAILED" not in kinds, f"runِ موفق FAILED هم شد: {kinds}"
    assert rs.get_run(rid)["state"] == "COMPLETED"


def t_model_failure_marks_event_failed_but_run_completed():
    """شکستِ تماسِ مدل (بدونِ استثنا) ⇒ MODEL_FINISHED=FAILED ولی run=COMPLETED."""
    _fresh_store()
    orig = collaborator._model_enhance

    def _fellback(base_reply, owner_text):
        out = dict(base_reply)
        out["model_source"] = "model-fallback-stub"
        out["data"] = {"warning": "model_call_failed:quota_exhausted"}
        return out

    collaborator._model_enhance = _fellback
    try:
        with _ArmCollab(use_model=True):
            rid, exc = _run_created_by(lambda: collaborator.handle("سلام"))
        assert exc is None, f"fallback نباید استثنا بدهد: {exc!r}"
        events = rs.list_events(rid)
        mf = [e for e in events if e.get("event_type") == "MODEL_FINISHED"]
        assert mf, f"MODEL_FINISHED ثبت نشد: {[e.get('event_type') for e in events]}"
        assert mf[0]["status"] == "FAILED", (
            f"شکستِ مدل باید status=FAILED بدهد، دیده شد {mf[0]['status']}")
        assert mf[0]["payload"].get("failure_reason") == "quota_exhausted"
        assert rs.get_run(rid)["state"] == "COMPLETED", "runِ دارای جواب نباید FAILED شود"
    finally:
        collaborator._model_enhance = orig


def t_sanitize_reason_strips_prose():
    f = collaborator._sanitize_reason
    assert f("model_call_failed:quota") == "quota"
    assert " " not in f("model_call_failed:رمزِ مالک leaked here")
    assert len(f("x" * 500)) <= 60
    assert f(None) == "unknown"
    assert f("") == "unknown"


if __name__ == "__main__":
    failed = harness.run([
        ("fail_run marks terminal FAILED", t_fail_run_makes_run_terminal_failed),
        ("failed run is not ACTIVE", t_failed_run_is_not_active),
        ("exception in handle -> run FAILED", t_exception_in_handle_marks_run_failed),
        ("failure reason carries no owner text", t_failure_reason_carries_no_owner_text),
        ("successful run still completes", t_successful_run_still_completes),
        ("model failure -> event FAILED, run COMPLETED", t_model_failure_marks_event_failed_but_run_completed),
        ("_sanitize_reason strips prose", t_sanitize_reason_strips_prose),
    ])
    sys.exit(1 if failed else 0)
