#!/usr/bin/env python3
"""تستِ صداقتِ خودِ ارگانیسم (تری‌اسکن 2026-07-17): A1 state-clobber + A3 version-sensor.

A1: مسیرِ خطا/STOP دیگر بلوک‌های غنی را دور نمی‌ریزد (merge_prev) — beat «یخ» می‌زند
    در حالی که ts جلو می‌رود (سیگنالِ «آخرین‌دانسته»).
A3: سایدکارِ نسخهٔ کد نوشته می‌شود و «کدِ زنده کهنه‌تر از دیسک» تشخیص داده می‌شود.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("organism-honesty")
_OPS = (harness.SELF_OPS)
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "live")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import organism  # noqa: E402

_SANDBOX = Path(ENV["ops"]) / "state"


def _sandbox_state():
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    organism.STATE_FILE = _SANDBOX / "ORGANISM-STATE.json"
    return organism.STATE_FILE


# ── A1: state-clobber ──────────────────────────────────────────────────────────
def t_merge_prev_preserves_rich_blocks():
    """مسیرِ STOP/خطا: بلوک‌های غنیِ tickِ قبل حفظ می‌شوند، نه دور ریخته."""
    sp = _sandbox_state()
    # یک tickِ سالمِ غنی (wholesale)
    organism._write_state({"beat": 7000, "heart": {"beat": 7000, "period": 900},
                           "ziman": {"leg_id": "z", "beat": 7000}, "proposal_router": {"delivered": 3}})
    rich = json.loads(sp.read_text("utf-8"))
    assert rich["heart"]["beat"] == 7000 and "ziman" in rich
    # مسیرِ STOP با merge_prev
    organism._write_state({"exited": "STOP"}, merge_prev=True)
    after = json.loads(sp.read_text("utf-8"))
    assert after["exited"] == "STOP", "markerِ نو باید برنده باشد"
    assert after["heart"]["beat"] == 7000, "بلوکِ heart باید حفظ شود"
    assert "ziman" in after and "proposal_router" in after, "بلوک‌های غنی حفظ شوند"
    assert after["beat"] == 7000, "beat یخ می‌زند (از prev)"


def t_no_merge_is_wholesale():
    """بدونِ merge_prev: جایگزینیِ کامل (رفتارِ tickِ سالم، بایت‌به‌بایت مثلِ قبل)."""
    sp = _sandbox_state()
    organism._write_state({"beat": 100, "heart": {"beat": 100}})
    organism._write_state({"month": "2026-07"})   # tickِ سالمِ نو
    after = json.loads(sp.read_text("utf-8"))
    assert "heart" not in after, "tickِ سالم باید wholesale جایگزین کند (نه merge)"
    assert after["month"] == "2026-07"


def t_error_path_preserves_and_marks():
    """مسیرِ خطا: last_error + حفظِ بلوک‌ها."""
    sp = _sandbox_state()
    organism._write_state({"beat": 50, "school": {"awareness": 0.5}})
    organism._write_state({"last_error": "ValueError: x"}, merge_prev=True)
    after = json.loads(sp.read_text("utf-8"))
    assert after["last_error"].startswith("ValueError") and after["school"]["awareness"] == 0.5


# ── A3: version-sensor ─────────────────────────────────────────────────────────
def t_code_sidecar_written():
    """سایدکارِ نسخه با (mtime,size) ماژول‌ها نوشته می‌شود."""
    organism.CODE_SIDECAR = _SANDBOX / "ORGANISM-STATE.code"
    organism._write_code_sidecar()
    sc = json.loads(organism.CODE_SIDECAR.read_text("utf-8"))
    assert "modules" in sc and "organism.py" in sc["modules"]
    m = sc["modules"]["organism.py"]
    assert m is not None and "mtime" in m and "size" in m


def t_freshness_detects_stale():
    """server._code_freshness: سایدکارِ کهنه (mtime قدیمی) → stale."""
    import server
    sc = _SANDBOX / "ORGANISM-STATE.code"
    real = _OPS / "organism.py"
    sc.write_text(json.dumps({"booted": "t",
        "modules": {"organism.py": {"mtime": 1.0, "size": 1}}}), "utf-8")
    server._CODE_SIDECAR = sc
    server._KEY_MODULES = {"organism.py": real}   # دیسک mtime امروز > 1.0
    cf = server._code_freshness()
    assert cf["live"] is False and "organism.py" in cf["stale"]


def t_freshness_live_when_matches():
    """اگر سایدکار mtimeِ فعلیِ دیسک را داشته باشد → live=True."""
    import server
    sc = _SANDBOX / "ORGANISM-STATE.code"
    real = _OPS / "organism.py"
    cur = real.stat().st_mtime
    sc.write_text(json.dumps({"booted": "t",
        "modules": {"organism.py": {"mtime": round(cur, 3), "size": real.stat().st_size}}}), "utf-8")
    server._CODE_SIDECAR = sc
    server._KEY_MODULES = {"organism.py": real}
    cf = server._code_freshness()
    assert cf["live"] is True and cf["stale"] == []


def t_freshness_none_when_no_sidecar():
    """بدونِ سایدکار → live=None (نامعلوم؛ سرور به هیوریستیکِ قدیم برمی‌گردد)."""
    import server
    server._CODE_SIDECAR = _SANDBOX / "does-not-exist.code"
    assert server._code_freshness()["live"] is None


def t_freshness_nondict_sidecar_failsoft():
    """بازبینی: سایدکارِ JSONِ غیر-object (list/null) → live=None بدونِ crash (fail-soft)."""
    import server
    sc = _SANDBOX / "ORGANISM-STATE.code"
    for bad in ("[1,2,3]", "null", "42", "\"x\""):
        sc.write_text(bad, "utf-8")
        server._CODE_SIDECAR = sc
        assert server._code_freshness()["live"] is None, bad


# ── بازبینی: markerهای گذرا در merge حمل نمی‌شوند ──────────────────────────────
def t_merge_prev_drops_transient_markers():
    """exited/last_error از prev حمل نمی‌شوند — وگرنه STOPِ اجرای قبل روی اجرای نو می‌ماند."""
    sp = _sandbox_state()
    organism._write_state({"exited": "STOP", "beat": 9, "heart": {"beat": 9}})
    organism._write_state({"last_error": "X: y"}, merge_prev=True)   # خطا قبل از اولین tickِ سالم
    after = json.loads(sp.read_text("utf-8"))
    assert "exited" not in after, "STOPِ اجرای قبل نباید حمل شود"
    assert after["last_error"].startswith("X"), "markerِ نو باید باشد"
    assert after["heart"]["beat"] == 9, "بلوکِ غنی همچنان حفظ می‌شود"


if __name__ == "__main__":
    failed = harness.run([
        ("[A1] merge_prev بلوک‌ها را حفظ می‌کند", t_merge_prev_preserves_rich_blocks),
        ("[A1] بدونِ merge = wholesale", t_no_merge_is_wholesale),
        ("[A1] مسیرِ خطا حفظ + mark", t_error_path_preserves_and_marks),
        ("[A3] سایدکارِ نسخه نوشته می‌شود", t_code_sidecar_written),
        ("[A3] کدِ کهنه تشخیص داده می‌شود", t_freshness_detects_stale),
        ("[A3] تطابق → live", t_freshness_live_when_matches),
        ("[A3] بی‌سایدکار → None", t_freshness_none_when_no_sidecar),
        ("[A3] سایدکارِ غیر-object fail-soft", t_freshness_nondict_sidecar_failsoft),
        ("[A1] markerهای گذرا حمل نمی‌شوند", t_merge_prev_drops_transient_markers),
    ])
    sys.exit(1 if failed else 0)
