"""verbatim copy of db.py for shell verification (mount rewrite-sync workaround)."""

import datetime as _dt
import os
import sqlite3
import statistics
from contextlib import contextmanager
from pathlib import Path

import migrations

DB_PATH = Path(os.environ.get("LANGAR_DB", Path(__file__).resolve().parent / "langar.db"))


class AlreadyJudged(Exception):
    def __init__(self, current: str):
        self.current = current
        super().__init__(f"already judged: {current}")


SCHEMA = """
CREATE TABLE IF NOT EXISTS log (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    rmssd REAL, sleep INTEGER, used INTEGER, loc TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS insight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    content TEXT, tag TEXT, recheck TEXT, verdict TEXT DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS reflection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    domain TEXT, question TEXT, answer TEXT
);
CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, val TEXT);
INSERT OR IGNORE INTO config(key, val) VALUES ('halted', '0');
"""


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.executescript(SCHEMA)
        migrations.run_migrations(conn)


def schema_version():
    return get_config("schema_version")


def get_config(key, default=None):
    with _conn() as conn:
        row = conn.execute("SELECT val FROM config WHERE key = ?", (key,)).fetchone()
        return row["val"] if row else default


def set_config(key, val):
    with _conn() as conn:
        conn.execute("INSERT INTO config(key, val) VALUES (?, ?) "
                     "ON CONFLICT(key) DO UPDATE SET val = excluded.val", (key, val))


def is_halted():
    return get_config("halted", "0") == "1"


def add_log(rmssd, sleep, used, loc, note, *, rmssd_quality=None, rmssd_source=None,
            measurement_duration_sec=None, measurement_posture=None):
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO log(rmssd, sleep, used, loc, note, rmssd_quality, rmssd_source, "
            "measurement_duration_sec, measurement_posture) VALUES (?,?,?,?,?,?,?,?,?)",
            (rmssd, sleep, used, loc, note, rmssd_quality, rmssd_source,
             measurement_duration_sec, measurement_posture))
        return cur.lastrowid


def last_log():
    with _conn() as conn:
        return conn.execute("SELECT * FROM log ORDER BY id DESC LIMIT 1").fetchone()


def recent_logs(n=7):
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM log ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return list(reversed(rows))


def logs_on(date_str):
    with _conn() as conn:
        return conn.execute("SELECT * FROM log WHERE substr(ts,1,10) = ? ORDER BY id",
                            (date_str,)).fetchall()


def log_streak():
    with _conn() as conn:
        rows = conn.execute("SELECT DISTINCT substr(ts,1,10) d FROM log").fetchall()
    dates = {r["d"] for r in rows}
    if not dates:
        return 0
    today = _dt.date.today()
    start = today if today.isoformat() in dates else today - _dt.timedelta(days=1)
    if start.isoformat() not in dates:
        return 0
    s = 0
    d = start
    while d.isoformat() in dates:
        s += 1
        d -= _dt.timedelta(days=1)
    return s


_DS_FIELDS = {"mood", "energy", "stress", "soreness", "exercise", "caffeine_time",
              "screen_late", "social", "deep_work_min", "meditation_min",
              "wake_time", "bedtime", "weight", "tags"}


def upsert_daily_state(date_str, **fields):
    clean = {k: v for k, v in fields.items() if k in _DS_FIELDS and v is not None}
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO daily_state(date) VALUES (?)", (date_str,))
        if clean:
            sets = ", ".join(f"{k} = ?" for k in clean)
            conn.execute(f"UPDATE daily_state SET {sets}, updated_at = datetime('now','localtime') "
                         "WHERE date = ?", (*clean.values(), date_str))


def get_daily_state(date_str):
    with _conn() as conn:
        return conn.execute("SELECT * FROM daily_state WHERE date = ?", (date_str,)).fetchone()


def all_daily_state():
    with _conn() as conn:
        return conn.execute("SELECT * FROM daily_state ORDER BY date").fetchall()


def add_insight(content, tag, recheck):
    with _conn() as conn:
        cur = conn.execute("INSERT INTO insight(content, tag, recheck) VALUES (?, ?, ?)",
                           (content, tag, recheck))
        return cur.lastrowid


def insights_due(date_str):
    with _conn() as conn:
        return conn.execute("SELECT * FROM insight WHERE recheck = ? AND verdict = 'pending' "
                            "ORDER BY id", (date_str,)).fetchall()


def record_verdict(insight_id, verdict):
    if verdict not in {"confirmed", "refuted"}:
        raise ValueError("verdict نامعتبر")
    with _conn() as conn:
        row = conn.execute("SELECT verdict FROM insight WHERE id = ?", (insight_id,)).fetchone()
        if row is None:
            raise ValueError("insight پیدا نشد")
        if row["verdict"] != "pending":
            raise AlreadyJudged(row["verdict"])
        conn.execute("UPDATE insight SET verdict = ? WHERE id = ? AND verdict = 'pending'",
                     (verdict, insight_id))


def insight_stats():
    today = _dt.date.today().isoformat()
    with _conn() as conn:
        rows = conn.execute("SELECT tag, verdict, recheck FROM insight").fetchall()
    stats = {"total": len(rows), "by_tag": {"E": 0, "S": 0, "P": 0}, "confirmed": 0,
             "refuted": 0, "pending": 0, "overdue": 0}
    for r in rows:
        if r["tag"] in stats["by_tag"]:
            stats["by_tag"][r["tag"]] += 1
        if r["verdict"] == "confirmed":
            stats["confirmed"] += 1
        elif r["verdict"] == "refuted":
            stats["refuted"] += 1
        else:
            stats["pending"] += 1
            if r["recheck"] and r["recheck"] < today:
                stats["overdue"] += 1
    judged = stats["confirmed"] + stats["refuted"]
    stats["confirm_rate"] = (stats["confirmed"] / judged) if judged else None
    return stats


def all_logs():
    with _conn() as conn:
        return conn.execute("SELECT * FROM log ORDER BY id").fetchall()


def all_insights():
    with _conn() as conn:
        return conn.execute("SELECT * FROM insight ORDER BY id").fetchall()


def add_reflection(domain, question, answer):
    with _conn() as conn:
        cur = conn.execute("INSERT INTO reflection(domain, question, answer) VALUES (?, ?, ?)",
                           (domain, question, answer))
        return cur.lastrowid


def recent_reflections(n=5):
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM reflection ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return list(reversed(rows))


def domain_counts():
    with _conn() as conn:
        rows = conn.execute("SELECT domain, COUNT(*) c FROM reflection GROUP BY domain").fetchall()
    return {r["domain"]: r["c"] for r in rows}


def all_reflections():
    with _conn() as conn:
        return conn.execute("SELECT * FROM reflection ORDER BY id").fetchall()


def _pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    xs2 = [p[0] for p in pairs]
    ys2 = [p[1] for p in pairs]
    try:
        sx = statistics.stdev(xs2)
        sy = statistics.stdev(ys2)
    except statistics.StatisticsError:
        return None
    if sx == 0 or sy == 0:
        return None
    mx = statistics.mean(xs2)
    my = statistics.mean(ys2)
    cov = sum((x - mx) * (y - my) for x, y in pairs) / (len(pairs) - 1)
    return cov / (sx * sy)


def trend(n=7):
    rows = recent_logs(n)
    with_rmssd = [r for r in rows if r["rmssd"] is not None]
    result = {"count": len(rows), "count_rmssd": len(with_rmssd), "mean_rmssd": None,
              "best": None, "worst": None, "corr_sleep": None, "corr_used": None}
    if not with_rmssd:
        return result
    rmssds = [r["rmssd"] for r in with_rmssd]
    result["mean_rmssd"] = statistics.mean(rmssds)
    result["best"] = max(with_rmssd, key=lambda r: r["rmssd"])
    result["worst"] = min(with_rmssd, key=lambda r: r["rmssd"])
    result["corr_sleep"] = _pearson(rmssds, [r["sleep"] for r in with_rmssd])
    result["corr_used"] = _pearson(rmssds, [r["used"] for r in with_rmssd])
    return result


def rmssd_baseline(days=30):
    cutoff = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
    with _conn() as conn:
        rows = conn.execute("SELECT rmssd FROM log WHERE rmssd IS NOT NULL AND substr(ts,1,10) >= ?",
                            (cutoff,)).fetchall()
    vals = [r["rmssd"] for r in rows]
    return statistics.mean(vals) if vals else None


def trend_extended(n=7):
    t = trend(n)
    rows = recent_logs(n)
    t["baseline_30"] = rmssd_baseline(30)
    t["completeness"] = (t["count_rmssd"] / n) if n else 0
    t["low_quality"] = sum(1 for r in rows if r["rmssd_quality"] in ("bad", "questionable"))
    if t["mean_rmssd"] is not None and t["baseline_30"] is not None:
        t["vs_baseline"] = t["mean_rmssd"] - t["baseline_30"]
    else:
        t["vs_baseline"] = None
    return t


def add_habit(title, cue=None, action=None, min_version=None):
    with _conn() as conn:
        cur = conn.execute("INSERT INTO habit(title, cue, action, min_version) VALUES (?, ?, ?, ?)",
                           (title, cue, action, min_version))
        return cur.lastrowid


def list_habits(active_only=True):
    q = "SELECT * FROM habit" + (" WHERE active = 1" if active_only else "") + " ORDER BY id"
    with _conn() as conn:
        return conn.execute(q).fetchall()


def get_habit(habit_id):
    with _conn() as conn:
        return conn.execute("SELECT * FROM habit WHERE id = ?", (habit_id,)).fetchone()


def set_habit_active(habit_id, active):
    with _conn() as conn:
        conn.execute("UPDATE habit SET active = ? WHERE id = ?", (active, habit_id))


def mark_habit(habit_id, date_str, status, note=None):
    with _conn() as conn:
        conn.execute("INSERT INTO habit_log(habit_id, date, status, note) VALUES (?, ?, ?, ?) "
                     "ON CONFLICT(habit_id, date) DO UPDATE SET status = excluded.status, "
                     "note = excluded.note", (habit_id, date_str, status, note))


def habit_streak(habit_id):
    with _conn() as conn:
        rows = conn.execute("SELECT date FROM habit_log WHERE habit_id = ? AND status = 'done'",
                            (habit_id,)).fetchall()
    done = {r["date"] for r in rows}
    if not done:
        return 0
    today = _dt.date.today()
    start = today if today.isoformat() in done else today - _dt.timedelta(days=1)
    if start.isoformat() not in done:
        return 0
    s = 0
    d = start
    while d.isoformat() in done:
        s += 1
        d -= _dt.timedelta(days=1)
    return s


def habit_recent_missed(habit_id, days=7):
    cutoff = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
    with _conn() as conn:
        rows = conn.execute("SELECT date, status FROM habit_log WHERE habit_id = ? AND date >= ?",
                            (habit_id, cutoff)).fetchall()
    done = sum(1 for r in rows if r["status"] == "done")
    return max(0, days - done)


def all_habit_logs():
    with _conn() as conn:
        return conn.execute("SELECT * FROM habit_log ORDER BY id").fetchall()


def add_review(rtype, period_start, period_end, answers_json, summary):
    with _conn() as conn:
        cur = conn.execute("INSERT INTO review(type, period_start, period_end, answers_json, summary) "
                           "VALUES (?, ?, ?, ?, ?)", (rtype, period_start, period_end, answers_json, summary))
        return cur.lastrowid


def recent_reviews(rtype=None, n=5):
    with _conn() as conn:
        if rtype:
            rows = conn.execute("SELECT * FROM review WHERE type = ? ORDER BY id DESC LIMIT ?",
                                (rtype, n)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM review ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    return list(reversed(rows))


def all_reviews():
    with _conn() as conn:
        return conn.execute("SELECT * FROM review ORDER BY id").fetchall()


def add_experiment(title, hypothesis, intervention, design, metric_primary="rmssd",
                   metric_secondary=None, start_date=None, end_date=None):
    start_date = start_date or _dt.date.today().isoformat()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO experiment(title, hypothesis, intervention, design, metric_primary, "
            "metric_secondary, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (title, hypothesis, intervention, design, metric_primary, metric_secondary,
             start_date, end_date))
        return cur.lastrowid


def list_experiments(status="active"):
    with _conn() as conn:
        if status:
            return conn.execute("SELECT * FROM experiment WHERE status = ? ORDER BY id DESC",
                                (status,)).fetchall()
        return conn.execute("SELECT * FROM experiment ORDER BY id DESC").fetchall()


def get_experiment(exp_id):
    with _conn() as conn:
        return conn.execute("SELECT * FROM experiment WHERE id = ?", (exp_id,)).fetchone()


def set_experiment_status(exp_id, status, end_date=None):
    with _conn() as conn:
        if end_date:
            conn.execute("UPDATE experiment SET status = ?, end_date = ? WHERE id = ?",
                         (status, end_date, exp_id))
        else:
            conn.execute("UPDATE experiment SET status = ? WHERE id = ?", (status, exp_id))


def mark_experiment_day(exp_id, date_str, intervention_done, adherence_note=None, outcome_note=None):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO experiment_day(experiment_id, date, intervention_done, adherence_note, "
            "outcome_note) VALUES (?, ?, ?, ?, ?) ON CONFLICT(experiment_id, date) DO UPDATE SET "
            "intervention_done = excluded.intervention_done, adherence_note = excluded.adherence_note, "
            "outcome_note = excluded.outcome_note",
            (exp_id, date_str, intervention_done, adherence_note, outcome_note))


def experiment_report(exp_id):
    exp = get_experiment(exp_id)
    if exp is None:
        return {"ok": False, "reason": "آزمایش پیدا نشد"}
    with _conn() as conn:
        days = conn.execute("SELECT * FROM experiment_day WHERE experiment_id = ?", (exp_id,)).fetchall()
        logs = {r["d"]: r["rmssd"] for r in conn.execute(
            "SELECT substr(ts,1,10) d, rmssd FROM log WHERE rmssd IS NOT NULL").fetchall()}
    inter, base, yes = [], [], 0
    for d in days:
        rv = logs.get(d["date"])
        if d["intervention_done"] == "yes":
            yes += 1
            if rv is not None:
                inter.append(rv)
        elif d["intervention_done"] == "no" and rv is not None:
            base.append(rv)
    rep = {"ok": True, "title": exp["title"], "hypothesis": exp["hypothesis"], "n_days": len(days),
           "adherence": (yes / len(days)) if days else None,
           "baseline_mean": statistics.mean(base) if base else None,
           "intervention_mean": statistics.mean(inter) if inter else None,
           "n_baseline": len(base), "n_intervention": len(inter)}
    rep["delta"] = (rep["intervention_mean"] - rep["baseline_mean"]) if (
        rep["baseline_mean"] is not None and rep["intervention_mean"] is not None) else None
    return rep


def all_experiments():
    with _conn() as conn:
        return conn.execute("SELECT * FROM experiment ORDER BY id").fetchall()


def all_experiment_days():
    with _conn() as conn:
        return conn.execute("SELECT * FROM experiment_day ORDER BY id").fetchall()


def add_measurement_import(**f):
    cols = ["file_name", "source", "detected_columns", "sample_rate", "duration_sec", "rmssd",
            "mean_hr", "beat_count", "quality", "artifact_ratio", "used_in_log_id", "notes"]
    vals = [f.get(c) for c in cols]
    with _conn() as conn:
        cur = conn.execute(f"INSERT INTO measurement_import({', '.join(cols)}) "
                           f"VALUES ({', '.join('?' for _ in cols)})", vals)
        return cur.lastrowid


def wipe_all_data():
    with _conn() as conn:
        for t in ("log", "insight", "reflection", "daily_state", "habit", "habit_log",
                  "review", "experiment", "experiment_day", "measurement_import"):
            conn.execute(f"DELETE FROM {t}")
        conn.execute("DELETE FROM config WHERE key NOT IN ('halted','schema_version')")


def mark_exported():
    set_config("last_export_at", _dt.date.today().isoformat())


def days_since_last_export(marker_key="last_export_at"):
    val = get_config(marker_key)
    if not val:
        return None
    try:
        last = _dt.date.fromisoformat(val[:10])
    except ValueError:
        return None
    return (_dt.date.today() - last).days
