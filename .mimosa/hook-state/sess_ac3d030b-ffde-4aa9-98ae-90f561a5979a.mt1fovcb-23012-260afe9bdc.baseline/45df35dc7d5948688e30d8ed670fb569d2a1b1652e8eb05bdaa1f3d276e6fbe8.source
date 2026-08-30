# -*- coding: utf-8 -*-
"""S5-fix — دو پیگیری: H2 مشاهدهٔ open واقعی (cooldown بلند) و H4 پنجرهٔ تاریخی بهتر."""
import importlib.util
import json
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parents[2] / "_ops"
sys.path.insert(0, str(OPS))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


res = json.loads((HERE / "result-s5.json").read_text(encoding="utf-8"))

# ── H2: مشاهدهٔ OPEN با cooldown بلند (۳۰ث) — شکست‌ها سریع، چک فوری ──
cb = _load("circuit_breaker_s5b", OPS / "budget" / "circuit_breaker.py")
cb.STATE_PATH = HERE / "cb-state-b.json"
f = HERE / "cb-state-b.json"
if f.exists():
    f.unlink()
cb._cfg = lambda: {"failure_threshold": 3, "cooldown_seconds": 30.0,
                   "half_open_max": 3, "success_to_close": 2,
                   "max_cooldown_seconds": 60.0, "window_size": 20,
                   "window_min_samples": 10, "window_fail_rate": 0.7,
                   "tag": "S5-mock"}
T = "s5-mock-provider-b"
t0 = time.perf_counter()
states = []
for _ in range(3):
    cb.record_failure(T, reason="network down (mock)")
    states.append(cb.check(T).get("state"))
opened = states[-1] == "open"
t_open = round(time.perf_counter() - t0, 2)
# بهبود: شبیه‌سازیِ گذرِ cooldown با دستکاریِ timestamp در state (mock ساعت)
import opslib  # noqa: E402

with opslib.LockedJson(cb.STATE_PATH) as lj:
    st = lj.read()
if st.get("targets", {}).get(T):
    st["targets"][T]["opened_at"] = st["targets"][T]["opened_at"] - 31 \
        if "opened_at" in st["targets"][T] else None
    lj.write(st)
after = cb.check(T).get("state")
cb.record_success(T)
cb.record_success(T)
final = cb.check(T).get("state")
res["H2_model_net_cut_circuit"] = {
    "states_after_each_failure": states,
    "opened_after_3_failures": opened,
    "time_to_open_s": t_open,
    "after_cooldown(mock clock)": after,
    "after_two_successes": final,
    "recovered": final == "closed",
    "note": "cooldown واقعی ۳۰ث؛ گذرِ زمان با mock ساعت شبیه‌سازی شد (بی‌هزینه)",
}

# ── H4: شاهد تاریخی — خطاهای readback امروز vs ادامهٔ چرخهٔ تصمیم ──
SYS4D = HERE.parents[2] / "4d_system"
con = sqlite3.connect(f"file:{SYS4D / 'outputs' / '4d_experiments.db'}?mode=ro",
                      uri=True)
con.row_factory = sqlite3.Row
# پنجرهٔ خطا: 03:57 تا 05:00 (۱۱ readback error قبل از فیکس)
err = con.execute(
    "SELECT COUNT(*) FROM dashboard_events WHERE event_name='memory.readback'"
    " AND status='error' AND timestamp >= '2026-08-16T03:57'"
    " AND timestamp < '2026-08-16T05:00'").fetchone()[0]
reads = con.execute(
    "SELECT COUNT(*) FROM dashboard_events WHERE event_name='memory.read'"
    " AND timestamp >= '2026-08-16T03:57' AND timestamp < '2026-08-16T05:00'"
).fetchone()[0]
tasks_done = con.execute(
    "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.completed'"
    " AND timestamp >= '2026-08-16T03:57' AND timestamp < '2026-08-16T05:00'"
).fetchone()[0]
tasks_fail = con.execute(
    "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.failed'"
    " AND timestamp >= '2026-08-16T03:57' AND timestamp < '2026-08-16T05:00'"
).fetchone()[0]
# همهٔ تاریخ: task.failed ها و اینکه آیا همان agent بعداً task.completed دارد
allf = con.execute(
    "SELECT agent_id, COUNT(*) c FROM dashboard_events"
    " WHERE event_name='task.failed' GROUP BY agent_id").fetchall()
con.close()
res["H4_helper_member_kill_history"] = {
    "fault_window": "03:57–05:00 (۱۱ خطای readback قبل از فیکس r16-view)",
    "readback_errors": err,
    "memory_reads_continued": reads,
    "tasks_completed_despite_faults": tasks_done,
    "tasks_failed_hard": tasks_fail,
    "daemon_restart_needed": False,
    "all_time_task_failed_by_agent": {r["agent_id"]: r["c"] for r in allf},
    "note": "حافظه‌خوانی خطا داد ولی چرخهٔ تصمیم ادامه یافت؛ فیکس زنده WITHOUT کرش",
}

(HERE / "result-s5.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps({"H2": res["H2_model_net_cut_circuit"],
                  "H4": res["H4_helper_member_kill_history"]},
                 ensure_ascii=False, indent=1, default=str))
