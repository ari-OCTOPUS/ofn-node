"""test_sync_health_unknown — غیاب حق ندارد خودش را به سبز لاندری کند.

گامِ ۹ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C16).

سنجشِ ۰۸-۰۳: `_ops/legs/sync_health.py` دقیقاً برای پاسخ به «آیا در sync است؟»
ساخته شد و هرگز یک رکورد ثبت نکرد؛ هر دو ظرفش (`_ops/state/sync/` و
`_ops/state/sync-health.json`) روی دیسک غایب‌اند. ولی `snapshot()` روی همان
غیاب `summary={"total":0,"ok":0,"warn":0,"err":0}` می‌داد — یعنی «صفر مشکل»،
که از یک sync ِ سالم قابلِ تفکیک نبود.

سنجهٔ پذیرشِ سند: **سه هدف UNKNOWN؛ فیکسچرِ تک‌رکوردی فقط همان یکی را سبز کند.**
جفتِ دوم عمدی است — بدونش گارد می‌توانست یک UNKNOWN ِ سراسری باشد که همان‌قدر
بی‌اطلاع است که سبزِ قبلی. برای همین این‌جا هر دو جهت سنجیده می‌شود: غیاب سبز
نشود، و حضور UNKNOWN نشود.

ایزوله: هر تست `state_dir` ِ خودش را از `tempfile` می‌گیرد و اول assert می‌کند
که آن مسیر **زیرِ درختِ زنده نیست** (درسِ «ایزوله را برای مسیرِ واقعی بگذار»).
"""
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("sync-health-unknown")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import provenance      # noqa: E402
import sync_health as sh   # noqa: E402

#: درختِ زندهٔ مالک. هیچ مسیرِ تحتِ آزمون حق ندارد زیرِ این بنشیند.
LIVE_TREE = Path(r"F:\backup").resolve()

#: ساعتِ ثابتِ تزریقی — هیچ assert ای ساعتِ دیوار را نمی‌خواند.
NOW = 1_754_200_000.0


def _is_under_live(p: Path) -> bool:
    try:
        Path(p).resolve().relative_to(LIVE_TREE)
        return True
    except ValueError:
        return False


def _fresh_state_dir() -> Path:
    d = Path(tempfile.mkdtemp(prefix="sync-health-state-")).resolve()
    assert not _is_under_live(d), f"فیکسچر داخلِ درختِ زنده ساخته شد: {d}"
    return d


def _write_ledger(state_dir: Path, doc) -> Path:
    p = state_dir / sh.HEALTH_PATH.name
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p


def _ok_record(epoch: float) -> dict:
    return {"last_ok_ts": "2026-08-03T12:00:00", "last_ok_epoch": epoch,
            "fail_count": 0, "last_fail_ts": None, "status": "ok"}


# ─── ۰: ایزوله ───────────────────────────────────────────────────────────────
def t_module_paths_are_isolated_from_the_live_vault():
    """اگر ثابت‌های ماژول به درختِ زنده اشاره کنند، بقیهٔ تست‌ها بی‌معنی‌اند."""
    ops_root = Path(ENV["ops"]).resolve()
    for name in ("SYNC_DIR", "HEALTH_PATH", "SNAPSHOT_PATH"):
        p = Path(getattr(sh, name)).resolve()
        assert not _is_under_live(p), f"{name} داخلِ درختِ زنده است: {p}"
        assert str(p).startswith(str(ops_root)), f"{name} بیرونِ سندباکس: {p}"


# ─── ۱: غیاب ⇒ UNKNOWN (نیمهٔ اولِ سنجهٔ پذیرش) ──────────────────────────────
def t_three_targets_are_unknown_when_the_ledger_is_absent():
    """سنجهٔ پذیرش، نیمهٔ اول: هر سه هدف UNKNOWN، نه یک summary ِ آرام."""
    d = _fresh_state_dir()
    assert len(sh.KNOWN_TARGETS) == 3, f"اهدافِ اعلام‌شده سه‌تا نیستند: {sh.KNOWN_TARGETS}"
    snap = sh.snapshot(state_dir=d, now=NOW)
    assert sorted(snap["sources"]) == sorted(sh.KNOWN_TARGETS), \
        f"فهرستِ اهداف از دفترِ غایب آمده، نه از KNOWN_TARGETS: {sorted(snap['sources'])}"
    for name, rec in snap["sources"].items():
        assert rec["status"] == sh.UNKNOWN, f"«{name}» با غیابِ دفتر {rec['status']} شد"
        assert "never executed" in (rec["reason"] or ""), \
            f"«{name}» نادانستنش را توضیح نمی‌دهد: {rec['reason']!r}"
        assert rec["last_run_ts"] is None, f"«{name}» last_run_ts ساختگی دارد: {rec['last_run_ts']!r}"
    assert snap["summary"] == {"total": 3, "ok": 0, "warn": 0, "err": 0, "unknown": 3}, \
        f"summary غیاب را نمی‌شمارد: {snap['summary']}"
    assert snap["status"] == sh.UNKNOWN, f"وضعیتِ کلیِ دفترِ غایب: {snap['status']}"
    assert snap["mechanism"] == sh.MECHANISM_ABSENT, \
        f"غیابِ مکانیزم اعلام نشد: {snap['mechanism']!r}"
    assert snap["ledger"]["exists"] is False and snap["ledger"]["reason"] == sh.LEDGER_ABSENT, \
        f"بلوکِ دفتر صادق نیست: {snap['ledger']}"


def t_absence_never_renders_as_a_number():
    """صفر یک اندازه‌گیری است. جایی که اندازه‌گیری نیست، عدد هم نباید باشد."""
    d = _fresh_state_dir()
    snap = sh.snapshot(state_dir=d, now=NOW)
    # حلقهٔ روی dict ِ خالی وضعاً پاس می‌شود — اول باید چیزی برای دیدن باشد.
    assert len(snap["sources"]) == 3, f"سه هدف گزارش نشد: {sorted(snap['sources'])}"
    for name, rec in snap["sources"].items():
        assert rec["lag_seconds"] is None, f"«{name}» lag ِ ساختگی دارد: {rec['lag_seconds']!r}"
        assert rec["fail_count"] is None, f"«{name}» fail_count ِ ساختگی دارد: {rec['fail_count']!r}"
        st = rec["provenance"]
        assert st["mode"] == provenance.Mode.UNKNOWN, f"«{name}» تمبرش UNKNOWN نیست: {st['mode']}"
        assert "value" not in st, f"«{name}» تمبرِ UNKNOWN مقدار حمل می‌کند: {st}"
        try:
            provenance.value_of(st)
        except KeyError:
            pass
        else:
            raise AssertionError(f"«{name}» value_of روی UNKNOWN استثنا نداد")


# ─── ۲: حضور ⇒ سبز، فقط همان یکی (نیمهٔ دومِ سنجهٔ پذیرش) ────────────────────
def t_single_record_fixture_greens_only_that_one():
    """سنجهٔ پذیرش، نیمهٔ دوم — همان جفتی که ثابت می‌کند گارد کور نیست.

    اگر این افتاد و بالایی پاس شد، یعنی UNKNOWN ِ سراسری برگردانده می‌شود."""
    d = _fresh_state_dir()
    _write_ledger(d, {"sources": {"cartographer": _ok_record(NOW - 60.0)}})
    snap = sh.snapshot(state_dir=d, now=NOW)
    got = snap["sources"]["cartographer"]
    assert got["status"] == "ok", f"هدفِ رکورددار سبز نشد: {got['status']} ({got['reason']!r})"
    assert got["lag_seconds"] == 60.0, f"lag اشتباه: {got['lag_seconds']}"
    assert got["fail_count"] == 0, f"fail_count رکوردِ سالم: {got['fail_count']!r}"
    for other in ("studio_pf", "lead"):
        rec = snap["sources"][other]
        assert rec["status"] == sh.UNKNOWN, \
            f"«{other}» بی‌رکورد {rec['status']} شد — سبزِ یک هدف به بقیه سرایت کرد"
    assert snap["summary"]["ok"] == 1 and snap["summary"]["unknown"] == 2, \
        f"summary جفتِ سبز/نادانسته را نمی‌شمارد: {snap['summary']}"
    assert snap["status"] == sh.UNKNOWN, \
        "یک هدفِ سبز کلِ سند را سبز کرد در حالی که دو هدف نادانسته‌اند"
    assert snap["mechanism"] is None, "دفترِ رکورددار هنوز «هرگز ساخته نشد» اعلام می‌کند"


def t_recorded_failure_is_err_not_unknown():
    """هدفی که اجرا شد و شکست خورد، خبر است نه غیاب — UNKNOWN بلعیدنش خطاست."""
    d = _fresh_state_dir()
    _write_ledger(d, {"sources": {"lead": {"fail_count": 3,
                                           "last_fail_ts": "2026-08-03T09:00:00",
                                           "status": "fail"}}})
    got = sh.check("lead", now=NOW, state_dir=d)
    assert got["status"] == "err", f"شکستِ ثبت‌شده {got['status']} شد"
    assert got["fail_count"] == 3, f"streak گم شد: {got['fail_count']!r}"
    assert got["reason"] == "no successful sync recorded", f"علت: {got['reason']!r}"
    assert sh.check("studio_pf", now=NOW, state_dir=d)["status"] == sh.UNKNOWN, \
        "هدفِ بی‌رکورد از کنارِ هدفِ شکست‌خورده وضعیت گرفت"


def t_a_record_without_any_run_is_unknown_not_ok():
    """`status: ok` ِ خوداعلام بدونِ هیچ اجرایی، شاهد نیست."""
    d = _fresh_state_dir()
    _write_ledger(d, {"sources": {"lead": {"status": "ok"}, "studio_pf": {}}})
    for name in ("lead", "studio_pf"):
        got = sh.check(name, now=NOW, state_dir=d)
        assert got["status"] == sh.UNKNOWN, f"«{name}» بدونِ اجرا {got['status']} شد"
        assert got["reason"] == sh.TARGET_NEVER_RECORDED, f"«{name}» علت: {got['reason']!r}"


def t_stale_success_is_err_and_warn_band_is_warn():
    """آستانه‌ها هنوز کار می‌کنند — گارد UNKNOWN جای سنجشِ lag را نگرفته."""
    d = _fresh_state_dir()
    cfg = sh._cfg()
    _write_ledger(d, {"sources": {"lead": _ok_record(NOW - cfg["err_lag_seconds"] - 5)}})
    got = sh.check("lead", now=NOW, state_dir=d)
    assert got["status"] == "err", f"lag ِ فراتر از آستانهٔ خطا {got['status']} شد"
    assert got["lag_seconds"] == round(cfg["err_lag_seconds"] + 5, 1), f"lag: {got['lag_seconds']}"

    _write_ledger(d, {"sources": {"lead": _ok_record(NOW - cfg["warn_lag_seconds"] - 5)}})
    got = sh.check("lead", now=NOW, state_dir=d)
    assert got["status"] == "warn", f"lag ِ باندِ هشدار {got['status']} شد"


def t_clock_is_fully_injectable():
    """ساعتِ نیمه‌تزریقی = تستی که فقط بعضی روزها سبز است."""
    d = _fresh_state_dir()
    _write_ledger(d, {"sources": {"lead": _ok_record(NOW - 10.0)}})
    a = sh.check("lead", now=NOW, state_dir=d)["lag_seconds"]
    b = sh.check("lead", now=NOW + 100.0, state_dir=d)["lag_seconds"]
    assert (a, b) == (10.0, 110.0), f"lag به ساعتِ تزریقی گوش نمی‌دهد: {a} / {b}"


# ─── ۳: ناخوانا ⇒ UNKNOWN، نه سبز ────────────────────────────────────────────
def t_corrupt_ledger_is_unknown_not_green():
    """فایلِ خراب دقیقاً همان‌قدر «نمی‌دانم» است که فایلِ غایب."""
    d = _fresh_state_dir()
    (d / sh.HEALTH_PATH.name).write_text("{ this is not json", encoding="utf-8")
    snap = sh.snapshot(state_dir=d, now=NOW)
    assert snap["summary"]["unknown"] == 3, f"دفترِ خراب سبز/صفر شد: {snap['summary']}"
    for name, rec in snap["sources"].items():
        assert rec["status"] == sh.UNKNOWN, f"«{name}» با دفترِ خراب {rec['status']} شد"
        assert (rec["reason"] or "").startswith(sh.LEDGER_UNREADABLE), \
            f"«{name}» ناخوانایی را نام نمی‌برد: {rec['reason']!r}"
    assert snap["status"] == sh.UNKNOWN, f"وضعیتِ کلی: {snap['status']}"


def t_ledger_of_the_wrong_shape_is_unknown():
    """JSON ِ معتبر ولی با شکلِ غلط هم دانش نیست."""
    d = _fresh_state_dir()
    (d / sh.HEALTH_PATH.name).write_text("[]", encoding="utf-8")
    got = sh.check("lead", now=NOW, state_dir=d)
    assert got["status"] == sh.UNKNOWN, f"دفترِ لیستی {got['status']} شد"
    assert "not an object" in (got["reason"] or ""), f"علت: {got['reason']!r}"


# ─── ۴: گزارش‌دادن هیچ‌چیز نمی‌سازد ──────────────────────────────────────────
def t_reporting_creates_no_vessel():
    """ساختنِ دایرکتوری یک اجرا را جعل می‌کند (بندِ ۸ ِ طرح)."""
    d = _fresh_state_dir()
    before = sorted(p.name for p in d.iterdir())
    sh.snapshot(state_dir=d, now=NOW)
    sh.check("studio_pf", now=NOW, state_dir=d)
    after = sorted(p.name for p in d.iterdir())
    assert before == after == [], f"گزارش چیزی ساخت: {before} → {after}"
    assert not (d / "sync").exists(), "SYNC_DIR در مسیرِ گزارش ساخته شد"
    assert not (d / sh.HEALTH_PATH.name).exists(), "دفتر در مسیرِ گزارش ساخته شد"
    assert not (d / (sh.HEALTH_PATH.name + ".lock")).exists(), "قفل در مسیرِ گزارش ساخته شد"


def t_live_vessels_stay_absent():
    """سنجهٔ نهایی: بعد از این سوییت، درختِ زنده هنوز هیچ ظرفِ syncی ندارد."""
    for rel in ("state/sync", "state/sync-health.json", "state/sync-health.json.lock",
                "state/sync-health-snapshot.json"):
        p = LIVE_TREE / "_ops" / rel
        assert not p.exists(), f"ظرفِ زنده ساخته شد: {p}"


# ─── ۵: گزارش دفتر را پاک نمی‌کند ────────────────────────────────────────────
def t_write_snapshot_does_not_clobber_the_ledger():
    """قبلاً گزارش روی همان فایلِ دفتر می‌نشست و `last_ok_epoch` را می‌بلعید —
    یعنی اولین گزارش هر هدفِ سبز را برای همیشه UNKNOWN می‌کرد."""
    assert sh.SNAPSHOT_PATH != sh.HEALTH_PATH, "گزارش و دفتر یک فایل‌اند"
    sh.record_success("cartographer", {"probe": "test"})
    first = sh.check("cartographer")
    assert first["status"] == "ok", f"ثبتِ موفقیت سبز نشد: {first}"
    sh.write_snapshot()
    after = sh.check("cartographer")
    assert after["status"] == "ok", f"گزارش رکورد را پاک کرد: {after['status']} ({after['reason']!r})"
    ledger = json.loads(sh.HEALTH_PATH.read_text("utf-8"))
    assert ledger["sources"]["cartographer"].get("last_ok_epoch"), \
        f"دفتر بعد از گزارش شاهدش را ندارد: {ledger}"
    assert sh.SNAPSHOT_PATH.exists(), "گزارش نوشته نشد"


# ─── ۶: divergence روی اندازه‌گیریِ غایب ─────────────────────────────────────
def t_divergence_with_a_missing_measurement_is_unknown():
    """`None → 0` دو منبعِ نامعلوم را «کاملاً هم‌خوان» اعلام می‌کند."""
    assert not opslib.FREEZE_FLAG.exists(), "سندباکس از قبل FREEZE دارد"
    got = sh.divergence_check("billed", "telemetry", None, 1.0)
    assert got["status"] == sh.UNKNOWN, f"اندازه‌گیریِ غایب {got['status']} شد"
    assert got["divergence"] is None, f"واگراییِ ساختگی: {got['divergence']!r}"
    assert "billed" in (got["reason"] or ""), f"نامِ منبعِ غایب برده نشد: {got['reason']!r}"
    assert not opslib.FREEZE_FLAG.exists(), "غیابِ اندازه‌گیری FREEZE کرد"


def t_unknown_is_never_confusable_with_a_level():
    """رشتهٔ UNKNOWN باید از هر سطحِ سلامتی متمایز بماند — و همان‌ِ provenance باشد."""
    assert sh.UNKNOWN == provenance.Mode.UNKNOWN, \
        f"مفهومِ دومی از UNKNOWN ساخته شد: {sh.UNKNOWN!r}"
    assert sh.UNKNOWN not in ("ok", "warn", "err", "fail"), sh.UNKNOWN


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_sync_health_unknown: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
