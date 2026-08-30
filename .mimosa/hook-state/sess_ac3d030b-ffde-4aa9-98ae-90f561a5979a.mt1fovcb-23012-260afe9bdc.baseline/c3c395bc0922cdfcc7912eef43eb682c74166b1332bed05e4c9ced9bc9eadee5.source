#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_journal_recovery.py — C2-D: durable_journal ← doctor + بازیابیِ resume-not-restart بوت.

پوشش:
  1. doctor سه قدمش را journal می‌کند (propose/sandbox/submit) — دیگر یتیم نیست
  2. مرگِ وسطِ sandbox (start بدونِ ok) → incomplete_runs آن را می‌بیند
  3. boot_recovery: گزارشِ advisory + resume_point — **هیچ قدمی re-run نمی‌شود**
  4. chrono: EXECUTINGِ رهاشده → RECONCILE_REQUIRED در بوت — هرگز settled/re-run
  5. جاروی knob=0 → خاموش؛ journal/chrono غایب → skip بی‌صدا (fail-soft)
  6. رگِ تازه: EXECUTINGِ کهنه دیگر برای همیشه در برزخ نمی‌ماند (اولین callerِ C6)
$0 آفلاین؛ صفر شبکه؛ state موقت.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("journal-recovery")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import durable_journal as dj  # noqa: E402
import journal_recovery as jr  # noqa: E402
import opslib  # noqa: E402
from doctor import Doctor  # noqa: E402  (doctor/__init__ export؟ در نبودش از doctor.doctor)

_STATE = Path(str(opslib.STATE_DIR))
_JPATH = _STATE / "journal" / "run-journal.jsonl"


def _entries():
    import json
    if not _JPATH.exists():
        return []
    out = []
    for ln in _JPATH.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    return out


def _wipe_journal():
    if _JPATH.exists():
        _JPATH.unlink()


def _mk_doctor():
    return Doctor(state_dir=_STATE)


# ── ۱: دکتر قدم‌ها را journal می‌کند ────────────────────────────────────────────
def t_doctor_steps_journaled():
    _wipe_journal()
    doc = _mk_doctor()
    rfc = doc.propose_rfc({"bottleneck": "test-bn"}, fix="a genuinely long test fix line",
                          expected_lift="none", rollback="revert")
    doc.run_sandbox(rfc)
    ents = _entries()
    steps = [(e.get("run_id"), e.get("step"), e.get("status")) for e in ents]
    rid = f"rfc-{rfc.rfc_id}"
    assert (rid, "propose", "ok") in steps, f"propose باید ثبت شود: {steps}"
    assert (rid, "sandbox", "start") in steps and (rid, "sandbox", "ok") in steps, \
        f"sandbox start+ok: {steps}"


# ── ۲: مرگِ وسطِ قدم دیده می‌شود ────────────────────────────────────────────────
def t_died_mid_step_visible():
    _wipe_journal()
    dj.record("rfc-DEAD1", "propose", "ok", path=_JPATH)
    dj.record("rfc-DEAD1", "sandbox", "start", path=_JPATH)   # مرگ همین‌جا
    inc = dj.incomplete_runs(within_h=24, path=_JPATH)
    pairs = [(r.get("run_id"), r.get("step")) for r in inc]
    assert ("rfc-DEAD1", "sandbox") in pairs, f"باید مرگِ وسطِ sandbox دیده شود: {inc}"
    assert dj.resume_point("rfc-DEAD1", path=_JPATH) == "propose", "resume از آخرین ok"


# ── ۳: boot_recovery advisory است — هیچ re-run ──────────────────────────────────
def t_boot_recovery_advisory_no_rerun():
    _wipe_journal()
    dj.record("rfc-DEAD2", "sandbox", "start", path=_JPATH)
    calls = {"n": 0}
    res = jr.boot_recovery(state_dir=_STATE)
    j = res["journal"]
    ids = [i["run_id"] for i in j.get("incomplete", [])]
    assert "rfc-DEAD2" in ids, f"گزارش باید مرده را بیاورد: {j}"
    assert calls["n"] == 0, "هیچ قدمی نباید اجرا شود (advisory)"
    ents = _entries()
    assert any(e.get("run_id") == "boot-recovery" for e in ents), "خودِ اسکن journal می‌شود"


# ── ۴+۶: EXECUTINGِ رهاشده → RECONCILE_REQUIRED (نه settled، نه re-run) ────────
def t_stale_executing_to_reconcile():
    import chrono as ch
    dbp = _STATE / "chrono-test.db"
    if dbp.exists():
        dbp.unlink()
    db = ch.ChronoDB(path=dbp)
    old_ms = int(time.time() * 1000) - 8 * 3600_000   # ۸ ساعت پیش
    db._con.execute(
        "INSERT INTO gated_effect(effect_id, kind, payload_ref, status, "
        "execution_id, execution_started_at, created_ts) VALUES(?,?,?,?,?,?,?)",
        ("fx-lost", "send", "ref", "EXECUTING", "exec-1", old_ms, old_ms))
    db._con.commit()
    db._con.close()
    res = jr.boot_recovery(state_dir=_STATE, chrono_db_path=dbp)
    c = res["chrono"]
    assert c.get("reconciled_now") == 1 and "fx-lost" in c.get("reconciled_ids", []), f"{c}"
    import sqlite3
    con = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
    st = con.execute("SELECT status FROM gated_effect WHERE effect_id='fx-lost'").fetchone()[0]
    n_settled = con.execute(
        "SELECT COUNT(*) FROM gated_effect WHERE status='settled'").fetchone()[0]
    con.close()
    assert st == "RECONCILE_REQUIRED", f"باید آشتیِ انسانی بخواهد نه terminal جعلی: {st}"
    assert n_settled == 0, "هرگز settled/re-run"


# ── ۵: knob خاموش + غایب‌ها fail-soft ───────────────────────────────────────────
def t_fail_soft_paths():
    os.environ[jr.EXEC_H_ENV] = "0"
    res = jr.boot_recovery(state_dir=_STATE)
    assert res["chrono"].get("skipped") == "knob-off"
    os.environ.pop(jr.EXEC_H_ENV, None)
    res2 = jr.boot_recovery(state_dir=_STATE / "does-not-exist",
                            chrono_db_path=_STATE / "nope" / "x.db")
    assert isinstance(res2, dict), "هرگز raise"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] دکتر قدم‌ها را journal می‌کند", t_doctor_steps_journaled),
        ("[۲] مرگِ وسطِ قدم دیده می‌شود", t_died_mid_step_visible),
        ("[۳] بازیابی advisory — صفر re-run", t_boot_recovery_advisory_no_rerun),
        ("[۴/۶] EXECUTINGِ رهاشده → RECONCILE_REQUIRED", t_stale_executing_to_reconcile),
        ("[۵] fail-soft کامل", t_fail_soft_paths),
    ])
    sys.exit(1 if failed else 0)
