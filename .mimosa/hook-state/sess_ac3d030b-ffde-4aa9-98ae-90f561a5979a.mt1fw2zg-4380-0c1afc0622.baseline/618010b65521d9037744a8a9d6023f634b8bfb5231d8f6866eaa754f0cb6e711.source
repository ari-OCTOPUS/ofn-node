"""
test_langar.py — تست‌های هسته‌ی LANGAR (بدونِ وابستگی به تلگرام).

اجرا (در پوشه‌ی langar):
    python tests/test_langar.py
خروجی: یا «ALL TESTS PASSED» یا اولین assertِ خطاخورده.

این تست‌ها db, migrations, hrv, coach, muse را پوشش می‌دهند —
یعنی همه‌ی منطقِ غیرِ‌تلگرامیِ سیستم. روی یک دیتابیسِ موقت اجرا می‌شوند
و به داده‌ی واقعیِ تو دست نمی‌زنند.
"""

import os
import sys
import tempfile
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# دیتابیسِ موقت قبل از import db
_tmp = tempfile.mkdtemp()
os.environ["LANGAR_DB"] = os.path.join(_tmp, "test.db")

import db          # noqa: E402
import hrv         # noqa: E402
import coach       # noqa: E402
import muse        # noqa: E402
import migrations  # noqa: E402

TODAY = dt.date.today().isoformat()

# راه‌اندازیِ دیتابیسِ موقت یک‌بار، قبل از همه‌ی تست‌ها
db.init_db()


def test_migrations_idempotent():
    db.init_db()
    db.init_db()
    assert db.schema_version() == migrations.SCHEMA_VERSION


def test_log_and_trend():
    db.add_log(50, 5, 0, "home", None)
    db.add_log(40, 2, 1, "work", None)
    db.add_log(60, 5, 0, "home", None)
    t = db.trend(7)
    assert t["count_rmssd"] >= 3 and t["mean_rmssd"] is not None
    te = db.trend_extended(7)
    assert "baseline_30" in te and "completeness" in te


def test_add_log_advanced_columns():
    lid = db.add_log(45, 4, 0, "home", None,
                     rmssd_quality="good", rmssd_source="manual",
                     measurement_duration_sec=300, measurement_posture="seated")
    row = db.last_log()
    assert row["id"] == lid and row["rmssd_quality"] == "good"


def test_write_once_verdict():
    iid = db.add_insight("x", "S", TODAY)
    db.record_verdict(iid, "confirmed")
    try:
        db.record_verdict(iid, "refuted")
        raise AssertionError("باید AlreadyJudged می‌داد")
    except db.AlreadyJudged:
        pass


def test_daily_state_partial_edit():
    db.upsert_daily_state(TODAY, mood=4, energy=3)
    db.upsert_daily_state(TODAY, stress=2)
    ds = db.get_daily_state(TODAY)
    assert ds["mood"] == 4 and ds["stress"] == 2


def test_streak():
    import sqlite3
    c = sqlite3.connect(os.environ["LANGAR_DB"])
    for i in range(3):
        d = (dt.date.today() - dt.timedelta(days=i)).isoformat()
        c.execute("INSERT INTO log(ts,rmssd) VALUES(?,?)", (d + " 08:00:00", 45))
    c.commit(); c.close()
    assert db.log_streak() >= 3


def test_insight_stats():
    s = db.insight_stats()
    assert "by_tag" in s and "confirm_rate" in s


def test_habits():
    hid = db.add_habit("Morning RMSSD", cue="After waking", min_version="60s")
    db.mark_habit(hid, TODAY, "done")
    assert db.habit_streak(hid) >= 1
    assert db.get_habit(hid)["title"] == "Morning RMSSD"


def test_experiment_report():
    eid = db.add_experiment("caffeine", "late caffeine lowers rmssd",
                            "no caffeine after 14", "ab")
    today = dt.date.today()
    for off, iv in [(0, "yes"), (1, "yes"), (2, "no"), (3, "no")]:
        db.mark_experiment_day(eid, (today - dt.timedelta(days=off)).isoformat(), iv)
    rep = db.experiment_report(eid)
    assert rep["ok"] and rep["n_days"] == 4


def test_hrv_rmssd():
    r = hrv.compute_rmssd([800, 810, 790, 805])
    assert r["ok"] and r["rmssd"] > 0
    assert hrv.compute_rmssd([800])["ok"] is False


def test_coach_rules():
    assert coach.recommend({"n_logs": 1})[0].startswith("داده")
    r = coach.recommend({"n_logs": 9, "rmssd_below_baseline": True, "sleep_low": True})
    assert any("خواب" in x for x in r)


def test_muse_rr_path():
    res = muse.compute_from_csv("timestamp,RR\n0,800\n1,810\n2,790\n3,805\n4,795\n")
    assert res["ok"] and res["source"] == "muse_rr"


def test_wipe_all_data():
    db.add_log(50, 5, 0, "home", None)
    db.wipe_all_data()
    assert db.all_logs() == []
    assert db.schema_version() == migrations.SCHEMA_VERSION


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
    print(f"\nALL TESTS PASSED ✅  ({len(tests)} تست)")


if __name__ == "__main__":
    main()
