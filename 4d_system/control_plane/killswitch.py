"""
control_plane/killswitch.py — v4: pause/resume/kill-switch (flag-gated + تأیید سخت).

هیچ تغییری در خودِ daemon نیست. این ماژول فقط همان قراردادِ فایلیِ موجود را
عمل می‌کند که خودِ daemon تعریف کرده و تلگرام‌بات هم استفاده می‌کند:

  outputs/daemon.pause — مکثِ نرم: فرایند زنده می‌ماند، گامِ خودمختار اجرا نمی‌شود.
  outputs/daemon.stop  — توقفِ تمیز: daemon در اولین tick می‌بیند، حذف می‌کند، می‌ایستد.

گیت‌ها (به ترتیب):
  1. CONTROL_PLANE_KILL_SWITCH_LIVE — default-off؛ خاموش = هیچ عملی.
  2. confirmed=True — تیکِ آگاهانه.
  3. برای stop: تایپِ دقیقِ عبارتِ STOP (تأییدِ سخت — تصمیمِ برگشت‌پذیر ولی جدی).

هر تلاش (حتی ردشده) در outputs/control_plane/killswitch_log.jsonl ثبت می‌شود،
با rollback صریح در هر رکورد.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from control_plane.flags import flag
from control_plane.policy import evaluate
from control_plane.snapshot import DEFAULT_OUT, daemon_status

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_DIR = SYSTEM_ROOT / "outputs" / "control_plane"
AUDIT_FILE = "killswitch_log.jsonl"
STOP_PHRASE = "STOP"
# نشانِ دائمیِ توقفِ مالک (در outputs/). supervisor همین را می‌خوانَد؛ چون daemon
# خودش daemon.stop را مصرف/حذف می‌کند، این نشان kill را دوام می‌بخشد.
OWNER_STOP_FLAG = "owner_intent_stop.flag"


def kill_switch_live() -> bool:
    return flag("CONTROL_PLANE_KILL_SWITCH_LIVE")


def _audit(rec: dict[str, Any], audit_dir: Path | None) -> str:
    d = audit_dir or DEFAULT_AUDIT_DIR
    d.mkdir(parents=True, exist_ok=True)
    p = d / AUDIT_FILE
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(p)


def _base_rec(kind: str, action_type: str, actor: str, confirmed: bool,
              rollback: str) -> dict[str, Any]:
    pol = evaluate(action_type)
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "target": "daemon",
        "actor": actor,
        "confirmed": bool(confirmed),
        "flag_live": kill_switch_live(),
        "policy_action": pol.action_type,
        "policy_level": pol.level,
        "rollback": rollback,
    }


def _finish(rec: dict, ok: bool, reason: str, audit_dir: Path | None) -> dict:
    rec["result"] = {"ok": ok, "reason": reason}
    rec["audit_path"] = _audit(rec, audit_dir)
    return rec


def _stamp() -> str:
    return json.dumps({"by": "control_plane", "at":
                       datetime.now().isoformat(timespec="seconds")},
                      ensure_ascii=False)


def pause_daemon(*, confirmed: bool = False, actor: str = "owner-ui",
                 out: Path | None = None,
                 audit_dir: Path | None = None) -> dict[str, Any]:
    """مکثِ نرم — ساختنِ outputs/daemon.pause (idempotent، برگشت‌پذیر)."""
    out = out or DEFAULT_OUT
    rec = _base_rec("pause", "pause_subsystem", actor, confirmed,
                    rollback="resume_daemon() یا حذفِ outputs/daemon.pause")
    if not kill_switch_live():
        return _finish(rec, False,
                       "CONTROL_PLANE_KILL_SWITCH_LIVE خاموش است (default-off)", audit_dir)
    if not confirmed:
        return _finish(rec, False, "تأییدِ آگاهانه لازم است (تیک را بزن)", audit_dir)
    try:
        (out / "daemon.pause").write_text(_stamp(), encoding="utf-8")
    except OSError as e:
        return _finish(rec, False, f"نوشتنِ فایل ناموفق: {e}", audit_dir)
    return _finish(rec, True, "daemon.pause ساخته شد — گامِ خودمختار در tick بعدی "
                              "اجرا نمی‌شود (فرایند زنده می‌ماند)", audit_dir)


def resume_daemon(*, confirmed: bool = False, actor: str = "owner-ui",
                  out: Path | None = None,
                  audit_dir: Path | None = None) -> dict[str, Any]:
    """ادامه — حذفِ daemon.pause (اگر نبود هم ok: idempotent)."""
    out = out or DEFAULT_OUT
    rec = _base_rec("resume", "pause_subsystem", actor, confirmed,
                    rollback="pause_daemon() دوباره")
    if not kill_switch_live():
        return _finish(rec, False,
                       "CONTROL_PLANE_KILL_SWITCH_LIVE خاموش است (default-off)", audit_dir)
    if not confirmed:
        return _finish(rec, False, "تأییدِ آگاهانه لازم است (تیک را بزن)", audit_dir)
    p = out / "daemon.pause"
    try:
        if p.exists():
            p.unlink()
            return _finish(rec, True, "daemon.pause حذف شد — ادامه از tick بعدی", audit_dir)
        return _finish(rec, True, "مکثی فعال نبود (idempotent)", audit_dir)
    except OSError as e:
        return _finish(rec, False, f"حذفِ فایل ناموفق: {e}", audit_dir)


def stop_daemon(*, confirmed: bool = False, confirm_text: str = "",
                actor: str = "owner-ui", out: Path | None = None,
                audit_dir: Path | None = None) -> dict[str, Any]:
    """توقفِ تمیز — ساختنِ daemon.stop. تأییدِ سخت: باید دقیقاً STOP تایپ شود."""
    out = out or DEFAULT_OUT
    rec = _base_rec("stop", "kill_switch", actor, confirmed,
                    rollback="cancel_stop() قبل از مصرف؛ راه‌اندازیِ دوباره: "
                             "python -m brain.daemon")
    if not kill_switch_live():
        return _finish(rec, False,
                       "CONTROL_PLANE_KILL_SWITCH_LIVE خاموش است (default-off)", audit_dir)
    if not confirmed:
        return _finish(rec, False, "تأییدِ آگاهانه لازم است (تیک را بزن)", audit_dir)
    if confirm_text.strip() != STOP_PHRASE:
        return _finish(rec, False,
                       f"تأییدِ سخت: باید دقیقاً «{STOP_PHRASE}» تایپ شود", audit_dir)
    try:
        # daemon.stop = ماشه‌ی گذرا (daemon خودش آن را مصرف/حذف می‌کند).
        (out / "daemon.stop").write_text(_stamp(), encoding="utf-8")
        # owner_intent_stop.flag = نشانِ دائمی تا kill دوام بیاورد؛ وگرنه بعد از
        # اینکه daemon، daemon.stop را حذف کرد، self-heal دوباره زنده‌اش می‌کرد.
        (out / OWNER_STOP_FLAG).write_text(_stamp(), encoding="utf-8")
    except OSError as e:
        return _finish(rec, False, f"نوشتنِ فایل ناموفق: {e}", audit_dir)
    return _finish(rec, True, "daemon.stop + owner_intent_stop.flag ساخته شد — توقفِ تمیز "
                              "و دائمی؛ self-heal تا cancel_stop دوباره بلندش نمی‌کند", audit_dir)


def cancel_stop(*, confirmed: bool = False, actor: str = "owner-ui",
                out: Path | None = None,
                audit_dir: Path | None = None) -> dict[str, Any]:
    """لغوِ stop قبل از آن‌که daemon مصرفش کند."""
    out = out or DEFAULT_OUT
    rec = _base_rec("cancel_stop", "pause_subsystem", actor, confirmed,
                    rollback="stop_daemon() دوباره (با تأییدِ سخت)")
    if not kill_switch_live():
        return _finish(rec, False,
                       "CONTROL_PLANE_KILL_SWITCH_LIVE خاموش است (default-off)", audit_dir)
    if not confirmed:
        return _finish(rec, False, "تأییدِ آگاهانه لازم است (تیک را بزن)", audit_dir)
    removed = []
    try:
        for fname in ("daemon.stop", OWNER_STOP_FLAG):
            p = out / fname
            if p.exists():
                p.unlink()
                removed.append(fname)
        if removed:
            return _finish(rec, True, f"حذف شد: {', '.join(removed)} — توقف لغو شد "
                                      "(self-heal دوباره می‌تواند daemon را بالا بیاورد)", audit_dir)
        return _finish(rec, True, "stopِ معلقی نبود (idempotent)", audit_dir)
    except OSError as e:
        return _finish(rec, False, f"حذفِ فایل ناموفق: {e}", audit_dir)


def killswitch_status(out: Path | None = None) -> dict[str, Any]:
    """وضعیتِ فعلی برای UI — فقط خواندن."""
    out = out or DEFAULT_OUT
    return {
        "flag_live": kill_switch_live(),
        "daemon": daemon_status(out),
        "stop_phrase": STOP_PHRASE,
    }


def audit_tail(limit: int = 20, audit_dir: Path | None = None) -> list[dict]:
    p = (audit_dir or DEFAULT_AUDIT_DIR) / AUDIT_FILE
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        for line in p.read_text(encoding="utf-8",
                                errors="replace").strip().splitlines()[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        return []
    return out
