#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lockedjson_write — سخت‌سازیِ مسیرِ نوشتنِ LockedJson (VQ-STATE-WRITE-001).

اپیزودِ ۰۷-۳۰ («tmp تازه، فایلِ اصلی کهنه، WinError 5») نشان داد `write()`
هیچ retry و هیچ رسیدِ شکستی ندارد: یک PermissionError ِ گذرا از AV/reader
کافی است تا self-model/ORGANISM-STATE برای ساعت‌ها کهنه بماند و هیچ‌کس نفهمد.

سنجه‌ها رفتاری‌اند (درسِ ۰۷-۳۰: گاردِ رشته‌ای/فراخوانی‌شمار کافی نیست):
  · شکستِ گذرا → retry ِ محدود و موفقیتِ واقعی روی دیسک.
  · شکستِ پایدار → استثنا بالا می‌آید (هرگز موفقیتِ ساکت)، نسخهٔ قبلی سالم
    می‌ماند، و رسیدِ شکست در `state/write-failures.jsonl` می‌نشیند.
  · خطای خودِ رسید هرگز خطای اصلی را نمی‌پوشاند.
  · snapshot ِ unified_control رسیدِ تازه را به‌عنوان blocker بالا می‌آورد —
    رسیدِ بی‌مصرف‌کننده ثبت نیست، زینت است.
"""
import json
import os
import time
from pathlib import Path

import harness

ENV = harness.setup("lockedjson-write")

import opslib  # noqa: E402

NOW = time.time()
STATE = Path(ENV["ops"]) / "state"


def _receipts() -> list:
    p = STATE / "write-failures.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _clear_receipts() -> None:
    p = STATE / "write-failures.jsonl"
    if p.exists():
        p.write_text("", "utf-8")


def t_roundtrip_write_read():
    p = STATE / "rt.json"
    with opslib.LockedJson(p) as lj:
        lj.write({"a": 1})
    with opslib.LockedJson(p) as lj:
        assert lj.read() == {"a": 1}


def t_transient_replace_failure_is_retried_to_success():
    _clear_receipts()
    p = STATE / "transient.json"
    orig = os.replace
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise PermissionError(13, "locked by a reader")
        return orig(src, dst)

    opslib.os.replace = flaky
    try:
        with opslib.LockedJson(p) as lj:
            lj.write({"v": 2})
    finally:
        opslib.os.replace = orig
    assert json.loads(p.read_text("utf-8")) == {"v": 2}, "روی دیسک ننشست"
    assert calls["n"] == 3, f"retry ِ محدود انتظار می‌رفت؛ calls={calls['n']}"
    assert _receipts() == [], "موفقیتِ retry نباید رسیدِ شکست بسازد"


def t_bounded_failure_raises_keeps_previous_and_writes_receipt():
    _clear_receipts()
    p = STATE / "stubborn.json"
    with opslib.LockedJson(p) as lj:
        lj.write({"old": True})
    orig = os.replace

    def always_denied(src, dst):
        raise PermissionError(13, "handle held open")

    opslib.os.replace = always_denied
    raised = False
    try:
        with opslib.LockedJson(p) as lj:
            lj.write({"new": True})
    except PermissionError:
        raised = True
    finally:
        opslib.os.replace = orig
    assert raised, "شکستِ پایدارِ نوشتن، ساکت بلعیده شد — success claim ممنوع"
    assert json.loads(p.read_text("utf-8")) == {"old": True}, "نسخهٔ قبلی باید سالم بماند"
    rows = _receipts()
    assert len(rows) == 1, f"دقیقاً یک رسیدِ شکست انتظار می‌رفت؛ {len(rows)}"
    r = rows[0]
    assert r.get("error") == "PermissionError", r
    assert str(p.name) in str(r.get("path", "")), r
    assert p.with_suffix(p.suffix + ".tmp").exists(), "tmp ِ تازه باید برای forensics بماند"


def t_receipt_failure_never_masks_the_original_error():
    _clear_receipts()
    p = STATE / "mask.json"
    orig_replace, orig_append = os.replace, opslib.append_jsonl

    def always_denied(src, dst):
        raise PermissionError(13, "denied")

    def broken_append(path, rec):
        raise OSError("receipt disk full")

    opslib.os.replace = always_denied
    opslib.append_jsonl = broken_append
    got = None
    try:
        with opslib.LockedJson(p) as lj:
            lj.write({"x": 1})
    except Exception as e:  # noqa: BLE001
        got = e
    finally:
        opslib.os.replace = orig_replace
        opslib.append_jsonl = orig_append
    assert isinstance(got, PermissionError), f"خطای اصلی پوشانده شد: {type(got).__name__}"


def t_receipt_is_bounded_and_content_free():
    _clear_receipts()
    p = STATE / "shape.json"
    orig = os.replace

    def always_denied(src, dst):
        raise PermissionError(13, "x" * 5000)

    opslib.os.replace = always_denied
    try:
        with opslib.LockedJson(p) as lj:
            lj.write({"secret_looking_payload": "must-not-appear"})
    except PermissionError:
        pass
    finally:
        opslib.os.replace = orig
    r = _receipts()[-1]
    assert set(r) <= {"ts", "epoch", "path", "error", "detail"}, r
    assert len(str(r.get("detail", ""))) <= 220, "detail باید bounded باشد"
    blob = json.dumps(r)
    assert "must-not-appear" not in blob, "payload هرگز واردِ رسید نمی‌شود"


def t_snapshot_surfaces_recent_write_failures_as_blocker():
    from unified_control import snapshot as sn
    old_state = sn.STATE
    sn.STATE = STATE
    try:
        wf = STATE / "write-failures.jsonl"
        wf.write_text(json.dumps({"epoch": NOW - 60, "path": "x", "error": "PermissionError"}) + "\n", "utf-8")
        snap = sn.build(now=NOW)
        assert any(b.startswith("state-write-failures") for b in snap["blockers"]), snap["blockers"]
        wf.write_text(json.dumps({"epoch": NOW - 90000, "path": "x", "error": "PermissionError"}) + "\n", "utf-8")
        snap = sn.build(now=NOW)
        assert not any(b.startswith("state-write-failures") for b in snap["blockers"]), \
            "رسیدِ کهنه (>۲۴h) نباید blocker بماند"
    finally:
        sn.STATE = old_state
        try:
            (STATE / "write-failures.jsonl").unlink()
        except OSError:
            pass


CHECKS = [(f.__name__, f) for f in (
    t_roundtrip_write_read,
    t_transient_replace_failure_is_retried_to_success,
    t_bounded_failure_raises_keeps_previous_and_writes_receipt,
    t_receipt_failure_never_masks_the_original_error,
    t_receipt_is_bounded_and_content_free,
    t_snapshot_surfaces_recent_write_failures_as_blocker,
)]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    total = len(CHECKS)
    print(("✅" if not failed else "❌") + f" test_lockedjson_write: {total - failed}/{total}")
    raise SystemExit(1 if failed else 0)
