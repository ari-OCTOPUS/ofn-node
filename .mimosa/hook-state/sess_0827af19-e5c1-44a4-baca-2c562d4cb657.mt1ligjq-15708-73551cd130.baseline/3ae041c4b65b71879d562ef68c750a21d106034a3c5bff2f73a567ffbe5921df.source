"""test_consolidate.py — تثبیتِ حافظه اپیزودیک→سِمانتیک (sleep-time compute).

پوشش: no-op بدونِ فلگ (صفر نوشتن)؛ تثبیت با فلگ؛ آرشیو اصل را حفظ می‌کند (هیچ حذف)؛
خروجیِ کران‌دار؛ منطقِ ترتیبِ برجستگی (salience) سالم؛ re-run ِ idempotent؛ fail-soft.
همه زیرِ STATE_DIRِ موقتِ harness — هیچ لمسِ state واقعی.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("consolidate")

import consolidate  # noqa: E402
import opslib        # noqa: E402

FLAG = "CORTEX_CONSOLIDATE"


def _flag_on():
    os.environ[FLAG] = "1"


def _flag_off():
    os.environ.pop(FLAG, None)


def _reset():
    """لاگِ رویداد + آرشیو + سِمانتیک + cursor را پاک کن تا هر تست از صفر شروع شود."""
    for p in (consolidate.EVENTS_LOG, consolidate.ARCHIVE, consolidate.SEMANTIC,
              consolidate.CURSOR):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


def _seed(records):
    """رکوردهای رویدادِ ساختگی را (با ts کنترل‌شده) به لاگِ رویداد append کن."""
    consolidate.EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(consolidate.EVENTS_LOG, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _ev(name, *, ts, agent="worker", status="ok", summary="s", next_action="",
        approval="unknown", trace=""):
    from datetime import datetime
    return {"timestamp": datetime.fromtimestamp(ts).isoformat(timespec="seconds"),
            "ts": ts, "trace_id": trace, "agent_id": agent, "event_name": name,
            "status": status, "summary": summary, "duration_ms": 0,
            "next_action": next_action, "approval_state": approval}


def _count_lines(p):
    if not p.exists():
        return 0
    return len([ln for ln in p.read_text("utf-8").splitlines() if ln.strip()])


# ─────────────────────────────────────────────────────────────────────────────────
def t_a_no_op_without_flag_zero_writes():
    """بدونِ فلگ: no-op مطلق — صفر برمی‌گرداند و هیچ فایلی نمی‌سازد."""
    _reset()
    _flag_off()
    now = time.time()
    _seed([_ev("task.failed", ts=now, summary="boom", trace="t1")])
    r = consolidate.consolidate_once()
    assert r == {"n_in": 0, "n_semantic": 0, "archived": 0, "flag": False, "ts": r["ts"]} \
        or (r["n_in"] == 0 and r["n_semantic"] == 0 and r["archived"] == 0 and r["flag"] is False)
    # صفر نوشتن: نه آرشیو، نه سِمانتیک، نه cursor ساخته شد
    assert not consolidate.ARCHIVE.exists()
    assert not consolidate.SEMANTIC.exists()
    assert not consolidate.CURSOR.exists()


def t_b_consolidates_when_flag_on():
    """با فلگ: همهٔ رویدادهای نو خوانده و آرشیو می‌شوند؛ حداقل یک نوتِ سِمانتیک."""
    _reset()
    _flag_on()
    try:
        now = time.time()
        _seed([
            _ev("incident.opened", ts=now, status="alert", summary="نشتِ ریسک", trace="i1"),
            _ev("task.completed", ts=now, summary="کارِ روتین", trace="c1"),
            _ev("system.heartbeat", ts=now, summary="تپش", agent="heart"),
        ])
        r = consolidate.consolidate_once()
        assert r["flag"] is True
        assert r["n_in"] == 3                       # هر سه رویدادِ نو
        assert r["archived"] == 3                   # همه آرشیو شدند
        assert 1 <= r["n_semantic"] <= 3            # کران‌دار، دستِ‌کم یکی
        assert consolidate.ARCHIVE.exists() and consolidate.SEMANTIC.exists()
        assert consolidate.CURSOR.exists()
    finally:
        _flag_off()


def t_c_archive_preserves_originals_nothing_deleted():
    """آرشیو = کپیِ verbatimِ اصل؛ لاگِ زنده هم دست‌نخورده. هیچ رویدادی حذف نمی‌شود."""
    _reset()
    _flag_on()
    try:
        now = time.time()
        seeded = [
            _ev("task.failed", ts=now - 10, status="failed", summary="A", trace="a"),
            _ev("handoff.created", ts=now - 5, summary="B", trace="b"),
            _ev("task.started", ts=now, summary="C", trace="c"),
        ]
        _seed(seeded)
        r = consolidate.consolidate_once()
        assert r["archived"] == len(seeded)

        # (۱) append-only: هیچ خطِ اصلی از لاگِ زنده حذف نشد (ماژول فقط append می‌کند —
        # یک رویدادِ completionِ خودش را ته می‌افزاید؛ اصل‌ها همه سرِ جای‌شان‌اند)
        live_after = consolidate.EVENTS_LOG.read_text("utf-8")
        for orig in seeded:
            assert json.dumps(orig, ensure_ascii=False) in live_after

        # (۲) هر رویدادِ اصل در آرشیو، بی‌کم‌وکاست، حاضر است
        arch = [json.loads(ln) for ln in
                consolidate.ARCHIVE.read_text("utf-8").splitlines() if ln.strip()]
        assert len(arch) == len(seeded)             # نه کم، نه زیاد
        by_trace = {a["trace_id"]: a for a in arch}
        for orig in seeded:
            got = by_trace[orig["trace_id"]]
            assert got == orig                      # فیلد-به-فیلد یکسان (لاسلس)
    finally:
        _flag_off()


def t_d_bounded_output():
    """خروجیِ سِمانتیک کران‌دار است: با فلوّدِ رویدادِ برجسته، n_semantic ≤ سقف."""
    _reset()
    _flag_on()
    os.environ["CORTEX_CONSOLIDATE_MAX"] = "5"
    import importlib
    importlib.reload(consolidate)                   # سقفِ نو را بخوان
    _flag_on()
    try:
        now = time.time()
        # ۳۰ رویدادِ همه‌برجسته (incident تازه) — بسیار بیشتر از سقفِ ۵
        _seed([_ev("incident.opened", ts=now - i, status="alert",
                   summary=f"inc{i}", trace=f"x{i}") for i in range(30)])
        r = consolidate.consolidate_once()
        assert r["n_in"] == 30
        assert r["archived"] == 30                  # آرشیو کران ندارد (همه حفظ)
        assert r["n_semantic"] == 5                 # سِمانتیک دقیقاً روی سقف بریده شد
        assert _count_lines(consolidate.SEMANTIC) == 5
    finally:
        os.environ.pop("CORTEX_CONSOLIDATE_MAX", None)
        importlib.reload(consolidate)               # knob را به پیش‌فرض برگردان
        _flag_off()


def t_e_salience_ordering_sane():
    """ترتیبِ برجستگی سالم: incidentِ تازه ≫ heartbeatِ کهنه؛ و انتخابِ top-K درست است."""
    now = time.time()
    hot = _ev("incident.opened", ts=now, status="alert",
              summary="داغ", next_action="بررسی", trace="hot")
    cold = _ev("system.heartbeat", ts=now - 240 * 3600, summary="سرد")   # ۱۰ روزِ پیش
    assert consolidate._salience(hot, now) > consolidate._salience(cold, now)
    # مؤلفه‌ها هم منفرداً سالم‌اند
    assert consolidate._recency(hot, now) > consolidate._recency(cold, now)
    assert consolidate._importance(hot) > consolidate._importance(cold)
    assert 0.0 <= consolidate._salience(cold, now) <= consolidate._salience(hot, now) <= 1.0
    # approval.required اهمیت را بالا می‌کشد (منتظرِ انسان = مهم)
    appr = _ev("task.started", ts=now, approval="required")
    assert consolidate._importance(appr) >= 0.85

    # top-K واقعی: با سقفِ ۱، تنها نوتِ نوشته‌شده باید همان رویدادِ داغ باشد
    _reset()
    _flag_on()
    os.environ["CORTEX_CONSOLIDATE_MAX"] = "1"
    import importlib
    importlib.reload(consolidate)
    _flag_on()
    try:
        _seed([cold, hot])                          # سرد اول، داغ دوم
        consolidate.consolidate_once(now=now)
        notes = consolidate.recent_semantic(10)
        assert len(notes) == 1 and notes[0]["trace_id"] == "hot"   # برجسته‌ترین انتخاب شد
    finally:
        os.environ.pop("CORTEX_CONSOLIDATE_MAX", None)
        importlib.reload(consolidate)
        _flag_off()


def t_f_idempotent_rerun():
    """re-run بدونِ رویدادِ نو → صفر، و هیچ خطِ تکراری در آرشیو (cursor idempotent)."""
    _reset()
    _flag_on()
    try:
        now = time.time()
        _seed([_ev("task.failed", ts=now, status="failed", summary="once", trace="o1")])
        r1 = consolidate.consolidate_once()
        assert r1["archived"] == 1
        arch_after_1 = _count_lines(consolidate.ARCHIVE)
        sem_after_1 = _count_lines(consolidate.SEMANTIC)
        # دورِ دوم، بدونِ رویدادِ نو
        r2 = consolidate.consolidate_once()
        assert r2["n_in"] == 0 and r2["archived"] == 0 and r2["n_semantic"] == 0
        assert _count_lines(consolidate.ARCHIVE) == arch_after_1   # تکراری نشد
        assert _count_lines(consolidate.SEMANTIC) == sem_after_1
    finally:
        _flag_off()


def t_g_fail_soft_on_garbage_lines():
    """خطوطِ خرابِ jsonl → skip می‌شوند، crash نه؛ فقط رویدادهای معتبر شمرده می‌شوند."""
    _reset()
    _flag_on()
    try:
        now = time.time()
        consolidate.EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(consolidate.EVENTS_LOG, "a", encoding="utf-8") as f:
            f.write("{این json نیست}\n")            # خطِ خراب
            f.write(json.dumps(_ev("task.failed", ts=now, status="failed",
                                   summary="valid", trace="v1"), ensure_ascii=False) + "\n")
            f.write("\n")                            # خطِ خالی
        r = consolidate.consolidate_once()          # نباید crash کند
        assert r["n_in"] == 1 and r["archived"] == 1   # فقط خطِ معتبر
    finally:
        _flag_off()


def t_h_containment_scrub_in_semantic():
    """لایهٔ سِمانتیک هرگز هویتِ Project-F را echo نمی‌کند (scrub)؛ آرشیو اما verbatim می‌ماند."""
    _reset()
    _flag_on()
    try:
        now = time.time()
        banned = _ev("incident.opened", ts=now, status="alert",
                     summary="onlyfans leak detail", trace="z1")
        _seed([banned])
        consolidate.consolidate_once()
        # نوتِ سِمانتیک redact شده
        note = consolidate.recent_semantic(1)[0]
        assert note["gist"] == "(redacted:containment)"
        # آرشیو verbatim (حفظِ اصل مقدم است؛ داده‌ای گم نمی‌شود)
        arch = consolidate.ARCHIVE.read_text("utf-8")
        assert "onlyfans" in arch
    finally:
        _flag_off()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_consolidate: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)