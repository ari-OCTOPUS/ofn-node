# -*- coding: utf-8 -*-
"""PASS 3 LIVE — owner-granted 2026-08-21. One coalesced digest. Respect 429.

Does not auto-approve anything. Does not git add -A. Does not delete STOP files
(moves them). Paid calls: none in this module.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "telegram_center") not in sys.path:
    sys.path.insert(0, str(_OPS / "telegram_center"))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))

EVID = _ROOT / "06-EVIDENCE" / "AGI-LOOPS-PASS3-LIVE-2026-08-21"
LOCK = _OPS / "state" / "wave1" / "lock.json"
GRANT = _ROOT / "02-DECISIONS" / "OWNER-GRANT-UNLOCK-AGI-LOCKS-2026-08-21.md"
MISSIONS = _ROOT / "OCTOPUS-DOCTOR" / "90-_meta" / "state" / "missions.json"
ARCHIVE_STOPS = _ROOT / "_Archive" / "Stops" / "2026-08-21-owner-grant"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def move_stop(name: str) -> dict:
    src = _OPS / name
    ARCHIVE_STOPS.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        cleared = _OPS / f"{name}.cleared-20260821"
        return {"name": name, "was_present": False, "dest": None,
                "already_cleared": cleared.is_file()}
    dest = ARCHIVE_STOPS / f"{name}.cleared-20260821"
    if dest.exists():
        dest = ARCHIVE_STOPS / f"{name}.cleared-20260821-{os.getpid()}"
    shutil.move(str(src), str(dest))
    return {"name": name, "was_present": True, "dest": str(dest.as_posix()),
            "live_present": src.is_file()}


def write_lock() -> dict:
    rec = {
        "schema": "wave1-lock/1",
        "wave1_unlocked": True,
        "verifier_pass": True,
        "updated": _utc(),
        "activation": "owner-grant-2026-08-21-full",
        "prompt_injection": False,
        "memory_writes": True,
        "organism_hook": True,
        "paid_calls": "budgeted",
        "grant": str(GRANT.as_posix()),
        "note": (
            "Owner explicit full Wave 1 unlock. Wave0 governor report stays a "
            "historical WAVE0_PASS artifact; production authority is this lock."
        ),
    }
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def merge_doctor_pulse() -> dict:
    if not MISSIONS.is_file():
        return {"ok": False, "reason": "missions-missing"}
    EVID.mkdir(parents=True, exist_ok=True)
    bak = EVID / "missions.json.pre-merge.bak"
    shutil.copy2(MISSIONS, bak)
    raw = json.loads(MISSIONS.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return {"ok": False, "reason": "not_list"}
    n_merged = 0
    out = []
    for m in raw:
        row = dict(m)
        if row.get("mission_id") == "doctor-pulse" and row.get("state") in (
                "proposed", "running", "awaiting-merge"):
            notes = list(row.get("notes") or [])
            notes.append(
                f"merged {_utc()} owner-grant: _ops/tools/doctor_pulse.py already on disk"
            )
            row["notes"] = notes
            row["state"] = "merged"
            row["merged_at"] = _utc()
            n_merged += 1
        out.append(row)
    tmp = MISSIONS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, MISSIONS)
    tool = (_OPS / "tools" / "doctor_pulse.py").is_file()
    return {"ok": True, "n_merged": n_merged, "tool_exists": tool,
            "backup": str(bak.as_posix()), "live_path": str(MISSIONS.as_posix())}


def _load_root_env() -> dict:
    """Load token/chat ids from vault .env into os.environ. Never logs values."""
    p = _ROOT / ".env"
    if not p.is_file():
        return {"loaded": False, "n_set": 0}
    allow = {
        "TG_CENTER_BOT_TOKEN", "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_OWNER_CHAT_ID", "TG_CENTER_CHAT_ID",
    }
    n = 0
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return {"loaded": False, "n_set": 0}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k = k.strip()
        if k not in allow:
            continue
        if os.environ.get(k):
            continue
        os.environ[k] = v.strip().strip('"').strip("'")
        n += 1
    return {"loaded": True, "n_set": n}


def send_owner_digest() -> dict:
    env_load = _load_root_env()
    import approval_store as aps  # noqa: WPS433
    from loops import families, telegram_organ  # noqa: E402
    from telegram_center.tg_api import TgClient  # noqa: WPS433

    pending = aps.load_pending()
    summary = aps.summary()
    fam_lines = []
    for fam in families.FAMILIES:
        fam_lines.append(f"{fam['family_id']} {fam['name']}")
    loops = (
        [{"loop_id": r["family_id"], "class": "FAMILY", "title": r["name"]}
         for r in families.FAMILIES]
        + [{"loop_id": "LOOP-APPROVAL-QUEUE", "class": "DECISION",
            "title": f"pending={summary.get('pending', 0)}"}]
    )
    td = EVID / "telegram-organ"
    organ = telegram_organ.TelegramOrgan(td, allowlist=set(), live=False)
    digest = organ.enqueue_digest(loops, chat_id=1, force=True)
    text = (
        "🐙 <b>owner grant digest</b> (یک پیام، coalesced)\n"
        f"Wave 1: UNLOCKED · memory_writes=yes · organism_hook=yes\n"
        f"صف تأیید: pending={summary.get('pending')} "
        f"approved={summary.get('approved')} rejected={summary.get('rejected')}\n"
        "سکوت = approval نیست. برای هر کارت جدا approve/reject/defer بزن.\n"
        f"خانواده‌ها: {len(families.FAMILIES)} · کشف: {len(families.DISCOVERY)}\n"
        "STOP-TG-HEARTBEAT منتقل شد. heartbeat دیگر با این فایل بسته نیست "
        "(probe-invalid هنوز نباید ۱:۱ اسپم شود — bridge هویت بدون beat است).\n"
        "BotFather Menu Button را خودت بزن: /setmenubutton → Web App → "
        "https://&lt;tunnel&gt;/miniapp\n"
    )
    if pending:
        shown = pending[:5]
        text += "نمونه pending (content-free):\n"
        for p in shown:
            text += f"- {p.get('id') or '?'} · {p.get('type') or ''} · {p.get('risk') or ''}\n"
        extra = len(pending) - len(shown)
        if extra > 0:
            text += f"- … و {extra} مورد دیگر\n"
    client = TgClient()
    wired = bool(client.wired())
    owner = client.owner_chat_id
    mid = None
    err = None
    if wired and owner is not None:
        try:
            mid = client.send(text, chat_id=owner, stream="owner-grant-digest")
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
    return {
        "wired": wired,
        "owner_present": owner is not None,
        "env_load": env_load,
        "message_id": mid,
        "error": err,
        "pending_n": len(pending),
        "summary": summary,
        "outbox_digest": {k: digest.get(k) for k in ("n_loops", "coalesced", "sent", "status")},
        "paid_calls": 0,
    }


def write_authority(lock: dict) -> None:
    path = _OPS / "state" / "waves" / "WAVE1-AUTHORITY.json"
    try:
        prev = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError:
        prev = {}
    prev["owner_grant_2026_08_21"] = {
        "ts": _utc(),
        "wave1_unlocked": True,
        "memory_writes": True,
        "organism_hook": True,
        "source": "AskQuestion owner form",
        "lock": lock,
        "precedence_now": (
            "Explicit owner grant flips production lock.json. "
            "wave0_governor source still reports historical WAVE0_PASS with "
            "wave1_unlocked=False so Wave 0 freeze stays bit-stable."
        ),
    }
    prev["authoritative_state"] = {
        "wave1_unlocked": True,
        "production_memory_read": True,
        "memory_write": True,
        "authority": "owner-grant-2026-08-21",
    }
    path.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")


def run() -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    if not GRANT.is_file():
        raise SystemExit("owner grant card missing")
    stops = [move_stop("STOP-TG-HEARTBEAT"), move_stop("STOP-CODE-AUTONOMY")]
    lock = write_lock()
    write_authority(lock)
    doctor = merge_doctor_pulse()
    digest = send_owner_digest()
    out = {
        "schema": "agi-loops-pass3-live/1",
        "pass": "LIVE",
        "ts": _utc(),
        "agi_claim": False,
        "grant": str(GRANT.as_posix()),
        "wave1_unlocked": True,
        "memory_writes": True,
        "organism_hook": True,
        "paid_calls": 0,
        "stops": stops,
        "doctor": doctor,
        "digest": digest,
        "botfather": "OWNER_MANUAL",
        "miniapp_routes_10": "NOT_GRANTED",
    }
    (EVID / "PASS3-LIVE.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    d = r.get("digest") or {}
    print(json.dumps({
        "wave1_unlocked": r["wave1_unlocked"],
        "stops": [{k: x.get(k) for k in ("name", "was_present", "live_present")}
                  for x in r["stops"]],
        "doctor_merged": (r.get("doctor") or {}).get("n_merged"),
        "digest_wired": d.get("wired"),
        "digest_message_id": d.get("message_id"),
        "pending_n": d.get("pending_n"),
        "paid_calls": r["paid_calls"],
    }, ensure_ascii=False, indent=2))
