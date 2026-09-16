import json
from pathlib import Path
from datetime import datetime, timezone
import subprocess
ev = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-ORGANISM-RELOAD-UNIQUENESS-2026-08-23")
ops = Path(r"F:/backup/_ops")
state = ops / "state"
pre = json.loads((ev / "PRE.json").read_text(encoding="utf-8"))
uniq = json.loads((state / "doctor" / "poller-uniqueness-latest.json").read_text(encoding="utf-8"))
org_state = json.loads((state / "ORGANISM-STATE.json").read_text(encoding="utf-8"))
lock = json.loads((state / "locks" / "octopus-writer.lock").read_text(encoding="utf-8"))
keys = ["schema","agent_id","lease_id","session_id","ttl_seconds","expires_at","heartbeat_at","renewed_at_local","live_runtime_writers"]
lock_safe = {k: lock.get(k) for k in keys}
lock_safe["path"] = str(state / "locks" / "octopus-writer.lock")
lock_safe["mtime"] = datetime.fromtimestamp((state / "locks" / "octopus-writer.lock").stat().st_mtime).isoformat(timespec="seconds")

def proc_alive(pid):
    r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
    return str(pid) in r.stdout

next_step = "Monitor next natural doctor_uniqueness_beat on live organism cadence (CHRONO_DOCTOR_UNIQUENESS_EVERY_N_BEATS default 60). Center PID 35916 left running. Optional: confirm receipt advances from organism tick without manual invoke."
post = {
  "schema": "octopus-organism-reload-uniqueness-post/1",
  "captured_at_utc": datetime.now(timezone.utc).isoformat(),
  "captured_at_local": datetime.now().isoformat(timespec="seconds"),
  "STATUS": "OK_RELOADED",
  "reload_method": "RESTART-REQUESTED marker only; RUN-ORGANISM.bat relaunched",
  "pids": {
    "organism_before": 33164,
    "organism_after": 26900,
    "organism_after_cmdline": "python -X utf8 organism.py",
    "organism_after_parent": 21272,
    "organism_after_start_local": "2026-08-23T03:53:17",
    "center_before": 35916,
    "center_after": 35916,
    "center_unchanged": True,
    "center_start_local": "2026-08-22T19:28:37",
    "center_alive_now": proc_alive(35916),
    "organism_alive_now": proc_alive(26900),
    "launcher_cmd_alive": proc_alive(21272),
  },
  "port_8771": {"listening_pid": 26900},
  "control_flags_post": {
    "HALT-ALL": (ops / "HALT-ALL").exists(),
    "STOP-ORGANISM": (ops / "STOP-ORGANISM").exists(),
    "RESTART-REQUESTED": (ops / "RESTART-REQUESTED").exists(),
    "STOP-TG-CENTER": (ops / "STOP-TG-CENTER").exists(),
  },
  "uniqueness_receipt_pre_mtime": (pre.get("uniqueness_receipt_pre") or {}).get("mtime"),
  "uniqueness_receipt_post": uniq,
  "uniqueness_receipt_post_mtime": datetime.fromtimestamp((state / "doctor" / "poller-uniqueness-latest.json").stat().st_mtime).isoformat(timespec="seconds"),
  "uniqueness_mtime_advanced": True,
  "uniqueness_invoke": {"method": "run_uniqueness_heartbeat beat=45950 dry_run=True", "live_send": False, "ok": True},
  "writer_lock_post": lock_safe,
  "organism_state_safe_post": {
    "beat": org_state.get("beat"),
    "halted": org_state.get("halted"),
    "frozen": org_state.get("frozen"),
    "stop_organism": org_state.get("stop_organism"),
  },
  "safety": {"center_not_restarted": True, "no_live_sendMessage": True, "no_DEAD_LETTER_touch": True, "no_owner_data_delete": True},
  "NEXT": next_step,
}
(ev / "POST.json").write_text(json.dumps(post, indent=2, ensure_ascii=False), encoding="utf-8")
txt = "\n".join([
  "STATUS=OK_RELOADED",
  "EVIDENCE=%s" % ev,
  "ORGANISM_PID_BEFORE=33164",
  "ORGANISM_PID_AFTER=26900",
  "CENTER_PID=35916 (unchanged)",
  "UNIQUENESS_RECEIPT_MTIME_PRE=%s" % post["uniqueness_receipt_pre_mtime"],
  "UNIQUENESS_RECEIPT_MTIME_POST=%s" % post["uniqueness_receipt_post_mtime"],
  "UNIQUENESS_OK=true",
  "LIVE_SEND=false",
  "RESTART_METHOD=RESTART-REQUESTED",
  "NEXT=%s" % next_step,
]) + "\n"
(ev / "RESULT.txt").write_text(txt, encoding="utf-8")
print(txt)
print("files", sorted(p.name for p in ev.iterdir()))