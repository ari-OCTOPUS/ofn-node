#!/usr/bin/env python3
"""test_octopus_logger_wire.py — WP2 · ORPH-OCTOPUS-LOG (2026-07-14).

اثبات می‌کند که oct_log حالا SELF-WIRING است، پشتِ فلگِ پیش‌فرض‌خاموشِ
`OCTOPUS_WIRE_STRUCTLOG`:

  * فلگ خاموش (پیش‌فرض) → octo_log هیچ چیزی روی دیسک نمی‌نویسد (بایت‌به‌بایت
    مثلِ قبل: فقط stream). فایلِ کاکپیت ساخته هم نمی‌شود.
  * فلگ روشن → octo_log هر رویداد را به همان مسیرِ JSONLِ کاکپیت
    (`_ops/state/octopus-log.jsonl`) append می‌کند، و رکورد:
        - JSONِ معتبرِ تک‌خطی است،
        - از validate_event پاک عبور می‌کند (schema v1)،
        - توسطِ خوانندهٔ واقعیِ کاکپیت (CockpitReadModel.tail_structured_log) دیده می‌شود.
  * fail-soft: مسیرِ نانوشتنی هرگز caller را نمی‌کشد.

صفر نوشتن روی مسیرِ زنده: STRUCTLOG_PATH + فلگِ env به یک tmp مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_octopus_logger_wire.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import octopus_logger as ol  # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="structlog-test-"))


def _reset_sink(path: pathlib.Path) -> None:
    """مسیرِ سینک را به tmp ببر و کشِ ماژول را باطل کن."""
    ol.STRUCTLOG_PATH = str(path)
    ol._FILE_SINK = None  # کشِ path-aware را دور بزن


def _set_flag(on: bool) -> None:
    if on:
        os.environ[ol.STRUCTLOG_FLAG] = "1"
    else:
        os.environ.pop(ol.STRUCTLOG_FLAG, None)


def test_flag_off_writes_nothing() -> None:
    """پیش‌فرض خاموش: هیچ فایلی نوشته یا ساخته نمی‌شود (بایت‌به‌بایتِ قبل)."""
    d = _tmp()
    target = d / "state" / "octopus-log.jsonl"
    _reset_sink(target)
    _set_flag(False)

    ctx = ol.OctoContext(organ="doctor", agent_id="rfc-miner")
    for _ in range(5):
        ol.octo_log(ctx, "doctor.rfc.drafted", "خاموش — نباید بنویسد",
                    status="started", confidence=0.7)
    ol.octo_log_warn(ctx, "doctor.rfc.submitted", "هنوز خاموش", status="blocked")

    assert not target.exists(), "فلگ خاموش نباید فایل بسازد یا بنویسد"


def test_flag_on_appends_wellformed_record() -> None:
    """روشن: رکوردِ well-formed که schema v1 و خوانندهٔ کاکپیت قبولش دارند."""
    d = _tmp()
    target = d / "state" / "octopus-log.jsonl"
    _reset_sink(target)
    _set_flag(True)
    try:
        ctx = ol.OctoContext(organ="doctor", agent_id="rfc-miner", tags=["audit"])
        ol.octo_log(ctx, "doctor.rfc.drafted", "bottleneck: budget conflict",
                    status="started", confidence=0.8,
                    p={"bottleneck": "freeze_halt"})
        child = ctx.child(agent_id="sandbox")
        ol.octo_log(child, "doctor.rfc.sandboxed", "RFC passed sandbox",
                    status="success", duration_ms=3420)

        assert target.exists(), "فلگ روشن باید فایل را بسازد و بنویسد"
        raw = target.read_text(encoding="utf-8").splitlines()
        assert len(raw) == 2, f"باید ۲ خط باشد، شد {len(raw)}"

        for ln in raw:
            ev = json.loads(ln)  # JSONِ تک‌خطیِ معتبر
            assert ev["v"] == ol.SCHEMA_VERSION
            assert ev["organ"] == "doctor"
            assert ol.validate_event(ev) == [], f"schema v1 نقض: {ev}"

        ev0 = json.loads(raw[0])
        assert ev0["event"] == "doctor.rfc.drafted"
        assert ev0["status"] == "started"
        assert ev0["p"]["bottleneck"] == "freeze_halt"
        # trace propagation: child همان trace، span/parent متفاوت
        ev1 = json.loads(raw[1])
        assert ev1["trace"] == ev0["trace"]
        assert ev1["parent"] == ev0["span"]
    finally:
        _set_flag(False)


def test_cockpit_reader_sees_records() -> None:
    """خوانندهٔ واقعیِ کاکپیت (نه ماک) خطوط را از همان مسیر tail می‌کند."""
    import cockpit_readmodel as crm  # noqa: E402
    d = _tmp()
    state_dir = d / "state"
    target = state_dir / "octopus-log.jsonl"
    _reset_sink(target)
    _set_flag(True)
    try:
        ctx = ol.OctoContext(organ="cortex")
        ol.octo_log(ctx, "system.heartbeat", "tick complete",
                    status="success", p={"beat_seq": 1234})

        reader = crm.CockpitReadModel(state_dir=str(state_dir))
        lines = reader.tail_structured_log(n=20)
        assert lines, "کاکپیت باید حداقل یک خط ببیند"
        ev = json.loads(lines[-1])
        assert ev["event"] == "system.heartbeat"
        assert ev["p"]["beat_seq"] == 1234
    finally:
        _set_flag(False)


def test_flag_on_is_fail_soft() -> None:
    """مسیرِ ناممکن (فایل به‌جای دایرکتوریِ والد) → هیچ استثنایی به caller نمی‌رسد."""
    d = _tmp()
    blocker = d / "blocker"
    blocker.write_text("i am a file, not a dir", encoding="utf-8")
    # والدِ target یک فایل است → makedirs/open شکست می‌خورد، ولی باید بلعیده شود
    target = blocker / "state" / "octopus-log.jsonl"
    _reset_sink(target)
    _set_flag(True)
    try:
        ctx = ol.OctoContext(organ="doctor")
        ol.octo_log(ctx, "doctor.rfc.drafted", "نباید کرش کند", status="started")
        # اگر به اینجا رسیدیم، fail-soft کار کرد
        assert True
    finally:
        _set_flag(False)


def test_rotation_bound() -> None:
    """نوشتنِ کران‌دار: از سقف که رد شد، فایلِ قبلی به .bak می‌رود (رشدِ نامحدود نه)."""
    d = _tmp()
    target = d / "state" / "octopus-log.jsonl"
    _reset_sink(target)
    _set_flag(True)
    try:
        sink = ol._file_sink()
        sink._max = 200  # سقفِ کوچک برای تستِ چرخش
        ctx = ol.OctoContext(organ="doctor")
        for i in range(30):
            ol.octo_log(ctx, "doctor.tick", "x" * 40, status="success",
                        p={"i": i})
        assert (d / "state" / "octopus-log.jsonl.bak").exists(), \
            "بعد از عبور از سقف باید .bak ساخته شود"
        # فایلِ فعال از دو-برابرِ سقف کوچکتر بماند (کران واقعی)
        assert target.stat().st_size < 400
    finally:
        _set_flag(False)


if __name__ == "__main__":
    _set_flag(False)  # شروعِ تمیز
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_octopus_logger_wire: {len(_tests)}/{len(_tests)} سبز")
