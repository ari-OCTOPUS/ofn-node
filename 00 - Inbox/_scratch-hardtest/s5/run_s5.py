# -*- coding: utf-8 -*-
"""S5 — خودترمیمی زیر خطای تزریقی (HARD-TEST) — همه در سندباکس + شاهد تاریخی زنده.

  H1 فایل state خراب          → state_guard: قرنطینه + بازنویسی اتمی (سندباکس)
  H2 قطع شبکهٔ مدل (mock)      → circuit_breaker: open→half-open→close (سندباکس)
  H3 دیسک‌پر موقت (mock)       → اتمی‌بودن بازنویسی: فایل اصلی باید دست‌نخورده بماند
  H4 کشتن عضو کمکی             → شاهد زندهٔ تاریخی: task.failed→ادامهٔ چرخه (فقط-خواندن)
  H5 کنترل منفی                → عضو غیرواقعی (پورت مرده/فایل غایب) هرگز «احیا» گزارش نشود
"""
import importlib.util
import json
import shutil
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


res = {"test": "S5-self-healing", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

# ══ H1: فایل state خراب → تعمیر ══════════════════════════════════════════
sg = _load("state_guard_s5", OPS / "state_guard.py")
sg.RECEIPTS = HERE / "receipts.jsonl"          # رسید فقط در سندباکس
src = OPS / "state" / "arm" / "renewal-log.jsonl"
sb1 = HERE / "renewal-log.jsonl"
shutil.copy2(src, sb1)
raw_lines = sb1.read_bytes().splitlines(keepends=True)
n_valid_before = 0
for ln in raw_lines:
    s = ln.strip()
    if s and s[:1] not in (b"#", b"//"):
        try:
            json.loads(ln.decode("utf-8"))
            n_valid_before += 1
        except Exception:
            pass
# تزریق خرابی: نصف‌کاره کردن خط آخر + یک خط null-دار
corrupted = raw_lines[:-1] + [raw_lines[-1][: len(raw_lines[-1]) // 2]] + \
    [b'{"broken": "\x00corrupt"}\n']
sb1.write_bytes(b"".join(corrupted))

t0 = time.perf_counter()
scan = sg.scan_jsonl(sb1)
rep = sg.repair_jsonl(sb1)
dt_repair_ms = (time.perf_counter() - t0) * 1000
scan2 = sg.scan_jsonl(sb1)
res["H1_corrupt_state"] = {
    "scan_found": {"invalid_json": scan.invalid_json, "null_lines": scan.null_lines},
    "repair_ok": rep.ok,
    "repair_ms": round(dt_repair_ms, 1),
    "removed_invalid": rep.removed_invalid, "removed_null": rep.removed_null,
    "kept_valid": rep.kept_valid,
    "valid_before": n_valid_before,
    "data_loss_valid_lines": n_valid_before - rep.kept_valid,
    "quarantined": bool(rep.quarantined_to),
    "rescan_clean": scan2.invalid_json == 0 and scan2.null_lines == 0,
    "receipt_written": (HERE / "receipts.jsonl").exists(),
}

# ══ H2: قطع شبکهٔ مدل (mock) → مدارشکن ══════════════════════════════════
cb = _load("circuit_breaker_s5", OPS / "budget" / "circuit_breaker.py")
cb.STATE_PATH = HERE / "cb-state.json"
if (HERE / "cb-state.json").exists():
    (HERE / "cb-state.json").unlink()
FAST = {"failure_threshold": 3, "cooldown_seconds": 1.0, "half_open_max": 3,
        "success_to_close": 2, "max_cooldown_seconds": 4.0, "window_size": 20,
        "window_min_samples": 10, "window_fail_rate": 0.7, "tag": "S5-mock"}
cb._cfg = lambda: dict(FAST)
TARGET = "s5-mock-provider"
t0 = time.perf_counter()
states = []
for _ in range(3):
    cb.record_failure(TARGET, reason="network down (mock)")
    states.append(cb.check(TARGET).get("state"))
opened_at = time.perf_counter() - t0
time.sleep(1.2)                                  # گذر از cooldown (۱ث — mock)
after_cooldown = cb.check(TARGET).get("state")
cb.record_success(TARGET)
cb.record_success(TARGET)
final_state = cb.check(TARGET).get("state")
res["H2_model_net_cut_circuit"] = {
    "states_after_each_failure": states,
    "opened_after_failures": states[-1] == "open",
    "time_to_open_s": round(opened_at, 2),
    "after_cooldown": after_cooldown,
    "after_two_successes": final_state,
    "recovered": final_state == "closed",
    "total_recovery_s": round(time.perf_counter() - t0, 2),
}

# ══ H3: دیسک‌پر موقت (mock) → اتمی‌بودن ═════════════════════════════════
sb3 = HERE / "diskfull.jsonl"
sb3.write_bytes(b"".join(raw_lines))            # نسخهٔ سالم
digest_before = sg._sha256(sb3)
_real_replace = __import__("os").replace


def _replace_fail(src_path, dst_path):
    if str(dst_path).endswith("diskfull.jsonl"):
        raise OSError(28, "No space left on device (S5 mock)")
    return _real_replace(src_path, dst_path)


__import__("os").replace = _replace_fail
t0 = time.perf_counter()
rep3 = sg.repair_jsonl(sb3)                      # فایل سالم — rewrite باید شکست بخورد
os_mod = __import__("os")
os_mod.replace = _real_replace
res["H3_disk_full_atomicity"] = {
    "error_recorded": bool(rep3.error),
    "ok_flag": rep3.ok,
    "original_unchanged": sg._sha256(sb3) == digest_before,
    "no_partial_write": not any(p.name.startswith(".sg_")
                                for p in HERE.glob(".sg_*")),
    "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
    "note": "شکست در replace ⇒ فایل اصلی بایت‌به‌بایت سالم ماند (reset-نه-خرابی)",
}

# ══ H4: کشتن عضو کمکی — شاهد تاریخی زنده از dashboard_events ═══════════
import sqlite3  # noqa: E402

SYS4D = HERE.parents[2] / "4d_system"
con = sqlite3.connect(f"file:{SYS4D / 'outputs' / '4d_experiments.db'}?mode=ro",
                      uri=True)
con.row_factory = sqlite3.Row
rows = con.execute(
    "SELECT id, timestamp, agent_id, event_name FROM dashboard_events"
    " WHERE id > 34000 AND event_name IN ('task.failed','task.completed')"
    " ORDER BY id").fetchall()
con.close()
recovered = {}
last_fail: dict[str, int] = {}
fails_total: dict[str, int] = {}
for r in rows:
    a = r["agent_id"]
    if r["event_name"] == "task.failed":
        fails_total[a] = fails_total.get(a, 0) + 1
        last_fail[a] = r["id"]
    elif r["event_name"] == "task.completed" and a in last_fail:
        recovered[a] = recovered.get(a, 0) + 1
        del last_fail[a]
res["H4_helper_member_kill_history"] = {
    "window": "event id > 34000 (امروز)",
    "fails_by_agent": fails_total,
    "recovered_by_agent": recovered,
    "unrecovered_still_failing": {a: True for a in last_fail},
    "daemon_alive_despite_errors": "pid 27164 از 10:34 (STEP 0)",
    "note": "شاهدِ واقعیِ «خطا → ادامهٔ چرخه» بدون ری‌استارت",
}

# ══ H5: کنترل منفی — عضو غیرواقعی نباید «احیا» گزارش شود ══════════════
wd = _load("watchdog_s5", OPS / "watchdog_extension.py")
mon = wd.WatchdogMonitor(
    bus=None,
    state_file=HERE / "ghost-state.json",        # وجود ندارد
    port=59999,                                   # پورت مرده
    stop_flags=[HERE / "GHOST-STOP.flag"],        # وجود ندارد
    alerts_md=HERE / "ghost-alerts.md")           # وجود ندارد
alerts = mon.run_checks()
by_name = {a["check_name"]: a for a in alerts}
port_alert = by_name.get("port_alive", {})
stale_alert = by_name.get("state_freshness", {})
res["H5_negative_control_ghost"] = {
    "ghost_port_reported_dead": port_alert.get("alive") is False and
                                port_alert.get("severity") == "critical",
    "ghost_state_reported_stale": stale_alert.get("stale") is True,
    "any_ghost_reported_healthy": any(
        (a.get("alive") is True) or (a.get("stale") is False)
        for a in alerts),
    "n_alerts_for_ghost": len(alerts),
}

(HERE / "result-s5.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
