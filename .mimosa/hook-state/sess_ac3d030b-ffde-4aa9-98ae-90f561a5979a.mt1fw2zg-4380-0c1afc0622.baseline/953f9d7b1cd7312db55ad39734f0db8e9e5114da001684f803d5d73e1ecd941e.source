import os, sys, tempfile, datetime as dt
os.environ["LANGAR_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
import db, hrv, coach, muse, migrations
db.init_db()  # setup once before all tests
TODAY = dt.date.today().isoformat()

def test_migrations_idempotent():
    db.init_db(); db.init_db()
    assert db.schema_version() == migrations.SCHEMA_VERSION

def test_log_and_trend():
    db.add_log(50,5,0,"home",None); db.add_log(40,2,1,"work",None); db.add_log(60,5,0,"home",None)
    assert db.trend(7)["count_rmssd"] >= 3
    assert "baseline_30" in db.trend_extended(7)

def test_add_log_advanced_columns():
    lid = db.add_log(45,4,0,"home",None, rmssd_quality="good", rmssd_source="manual",
                     measurement_duration_sec=300, measurement_posture="seated")
    assert db.last_log()["rmssd_quality"] == "good"

def test_write_once_verdict():
    iid = db.add_insight("x","S",TODAY); db.record_verdict(iid,"confirmed")
    try:
        db.record_verdict(iid,"refuted"); raise AssertionError("expected AlreadyJudged")
    except db.AlreadyJudged: pass

def test_daily_state_partial_edit():
    db.upsert_daily_state(TODAY, mood=4, energy=3); db.upsert_daily_state(TODAY, stress=2)
    ds = db.get_daily_state(TODAY); assert ds["mood"]==4 and ds["stress"]==2

def test_streak():
    import sqlite3
    c = sqlite3.connect(os.environ["LANGAR_DB"])
    for i in range(3):
        c.execute("INSERT INTO log(ts,rmssd) VALUES(?,?)",
                  ((dt.date.today()-dt.timedelta(days=i)).isoformat()+" 08:00:00",45))
    c.commit(); c.close()
    assert db.log_streak() >= 3

def test_insight_stats():
    s = db.insight_stats(); assert "by_tag" in s and "confirm_rate" in s

def test_habits():
    hid = db.add_habit("Morning RMSSD", cue="After waking", min_version="60s")
    db.mark_habit(hid, TODAY, "done")
    assert db.habit_streak(hid) >= 1 and db.get_habit(hid)["title"]=="Morning RMSSD"

def test_experiment_report():
    eid = db.add_experiment("caffeine","late caffeine","no caffeine after 14","ab")
    for off,iv in [(0,"yes"),(1,"yes"),(2,"no"),(3,"no")]:
        db.mark_experiment_day(eid,(dt.date.today()-dt.timedelta(days=off)).isoformat(),iv)
    rep = db.experiment_report(eid); assert rep["ok"] and rep["n_days"]==4

def test_hrv_rmssd():
    assert hrv.compute_rmssd([800,810,790,805])["ok"]
    assert hrv.compute_rmssd([800])["ok"] is False

def test_coach_rules():
    assert coach.recommend({"n_logs":1})[0].startswith("داده")
    assert any("خواب" in x for x in coach.recommend({"n_logs":9,"rmssd_below_baseline":True,"sleep_low":True}))

def test_muse_rr_path():
    res = muse.compute_from_csv("timestamp,RR\n0,800\n1,810\n2,790\n3,805\n4,795\n")
    assert res["ok"] and res["source"]=="muse_rr"

def test_wipe_all_data():
    db.add_log(50,5,0,"home",None); db.wipe_all_data()
    assert db.all_logs()==[] and db.schema_version()==migrations.SCHEMA_VERSION

tests = [v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
for t in tests:
    t(); print("  ✓", t.__name__)
print(f"\nALL TESTS PASSED ✅ ({len(tests)})")
