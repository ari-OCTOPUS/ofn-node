"""repair_api — داروخانهٔ بورد: API لوکالِ خوددرمانی با لیست‌سفید (2026-09-03).

فرمول مالک: «هر بیماری پیدا می‌کند شفا بده؛ تجهیزات بده در آینده خودش درست
کند؛ API در اختیارش باشد.» این همان ابزارهایی است که ایجنت مقیم در
۲۰۲۶-۰۳-۰۹ با دست اجرا کرد، حالا به‌صورت سرویس روی خودِ بورد — تا ارگانیسم
(دکتر → پیشنهاد → فراخوانی این API) فردا خودش مداوا کند.

قواعد آهنین:
  · فقط loopback (127.0.0.1) — هیچ سطح بیرونی
  · dry_run پیش‌فرض TRUE؛ اجرای واقعی فقط با "dry_run": false
  · هر اقدام: بازرسی پیش‌شرط + رسید در state/repair-log.jsonl + فرمان rollback
  · حالت conservation (غیبت مالک) = ردِ همهٔ اقدامات اجرایی
  · فقط-تعمیر: هیچ restart خام، هیچ حذف بی‌بازگشت، هیچ پرچم/ارسال
  · fail-closed: action ناشناس = رد با رسید
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.repair-api.v1"
HOST, PORT = "127.0.0.1", 8797
LOG = opslib.STATE_DIR / "repair-log.jsonl"
MESH = Path.home() / "octopus-mesh"
REPO = Path.home() / "ofn"

# اقدامات مجاز — همان درمان‌های اثبات‌شدهٔ 2026-09-03
ACTIONS = ("mesh_archive_expired", "mesh_drain", "git_pull_ff",
           "doctor_summary", "timesync_status")


def _log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry.setdefault("at", opslib.now_iso())
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _conservation_on() -> bool:
    try:
        import owner_absence
        return bool(owner_absence.conservation_active())
    except Exception:  # noqa: BLE001 — خرابی زیرسیستم = بدترین فرض
        return True


def _expiry_ts(path: Path) -> int:
    try:
        import datetime as dt
        d = json.loads(path.read_text(encoding="utf-8"))
        e = d.get("expires_at")
        return int(dt.datetime.fromisoformat(
            e.replace("Z", "+00:00")).timestamp()) if e else 0
    except (OSError, ValueError, AttributeError):
        return 0


def plan(action: str, payload: dict) -> dict:
    """محاسبهٔ اقدام (بدون اجرا) — خروجی هم برای dry_run هم برای رسید."""
    base = {"schema": SCHEMA, "action": action,
            "at": opslib.now_iso(), "actor": payload.get("actor", "unknown")}
    if action not in ACTIONS:
        return {**base, "ok": False, "error": "unknown-action",
                "allowed": ACTIONS}
    if action in ("mesh_archive_expired", "mesh_drain", "git_pull_ff") \
            and _conservation_on():
        return {**base, "ok": False, "error": "conservation-on",
                "detail": "owner absent — no repairs during conservation"}
    if action == "mesh_archive_expired":
        q = payload.get("queue", "outbox")
        d = MESH / q
        now = int(time.time())
        expired = [p.name for p in d.glob("*.json")
                   if not p.name.endswith(".state.json")
                   and 0 < _expiry_ts(p) < now]
        return {**base, "ok": True, "queue": q, "expired": expired,
                "archive_dir": f"{q}-expired-{time.strftime('%Y%m%d')}",
                "rollback": f"mv {q}-expired-*/* {q}/"}
    if action == "mesh_drain":
        return {**base, "ok": True, "cmd": "python3 bin/octomesh_process.py",
                "cwd": str(MESH), "rollback": "idempotent retry tool"}
    if action == "git_pull_ff":
        return {**base, "ok": True, "cmd": "git pull --ff-only origin main",
                "cwd": str(REPO), "rollback": "git reset --hard ORIG_HEAD"}
    if action == "doctor_summary":
        p = opslib.STATE_DIR / "doctor" / "report.json"
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            return {**base, "ok": True, "verdict": r.get("verdict"),
                    "banner": r.get("banner"),
                    "unhealthy": [m["name"] for m in r.get("measurements", [])
                                  if m.get("verdict") == "unhealthy"]}
        except (OSError, ValueError):
            return {**base, "ok": False, "error": "report-absent"}
    if action == "timesync_status":
        out = subprocess.run(["timedatectl"], capture_output=True,
                             text=True, timeout=15).stdout
        synced = "System clock synchronized: yes" in out
        return {**base, "ok": True, "synchronized": synced}
    return {**base, "ok": False, "error": "unreachable"}


def execute(action: str, payload: dict) -> dict:
    """اجرای واقعی — فقط بعد از planِ ok؛ هر قدم fail-soft با رسید."""
    p = plan(action, payload)
    _log({"phase": "plan", **{k: p[k] for k in p if k != "schema"}})
    if not p.get("ok"):
        return p
    if action == "mesh_archive_expired":
        d = MESH / p["queue"]
        arch = MESH / p["archive_dir"]
        arch.mkdir(exist_ok=True)
        moved = 0
        for name in p["expired"]:
            src = d / name
            if src.exists():
                src.rename(arch / name)
                moved += 1
        p["moved"] = moved
    elif action in ("mesh_drain", "git_pull_ff"):
        r = subprocess.run(p["cmd"].split(), cwd=p["cwd"],
                           capture_output=True, text=True, timeout=300)
        p["rc"] = r.returncode
        p["tail"] = (r.stdout or r.stderr)[-200:]
    # doctor_summary / timesync_status فقط-خواندنی‌اند؛ plan خودش اجراست
    _log({"phase": "done", **{k: p[k] for k in p if k != "schema"}})
    return p


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 — stdlib contract
        try:
            body = json.loads(self.rfile.read(
                int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            body = {}
        action = str(body.get("action", ""))
        dry = body.get("dry_run", True)
        if self.path != "/v1/repair" or not action:
            res = {"ok": False, "error": "use POST /v1/repair {action}"}
        elif dry:
            res = plan(action, body)
            _log({"phase": "dry-run", "action": action, "ok": res.get("ok")})
        else:
            res = execute(action, body)
        data = json.dumps(res, ensure_ascii=False).encode("utf-8")
        self.send_response(res.get("ok") and 200 or 400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a) -> None:  # silence — رسیدها در repair-log است
        pass


def main() -> int:
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(json.dumps({"schema": SCHEMA, "listening": f"{HOST}:{PORT}",
                      "actions": ACTIONS, "dry_run_default": True}))
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
