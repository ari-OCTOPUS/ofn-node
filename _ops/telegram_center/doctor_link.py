#!/usr/bin/env python3
"""doctor_link.py — پلِ دکترِ اختاپوس (OCTOPUS-DOCTOR) به مرکزِ تلگرامِ زنده.

دکتر در حالتِ outbox کارت‌هایش را فقط در
`OCTOPUS-DOCTOR/90-_meta/state/tg-outbox.jsonl` صف می‌کند و هیچ اتصالِ دومی به
تلگرام باز نمی‌کند (دزدیِ getUpdates از pollerِ زنده = کوریِ بی‌صدا). این ماژول
همان «پروسهٔ زندهٔ موجود» است که قراردادِ outbox به آن تکیه دارد:

  · beat(center)          — کارت‌های صف‌شدهٔ نو را با clientِ خودِ مرکز می‌فرستد
  · handle_callback(...)  — رأیِ سه‌تکهٔ دکتر (ok|no:gate:mission) را جدا می‌کند و
                            با subprocess به `doctor/cli.py votes` می‌دهد؛ وگرنه
                            fallbackِ ok/no:<id> مرکز آن را به‌عنوانِ approval ِ
                            بی‌ربط ثبت می‌کرد و دکتر هرگز رأی را نمی‌دید.

مرزِ عمدی: این فایل **هیچ** ماژولی از OCTOPUS-DOCTOR را import نمی‌کند — outbox
JSONِ خالص است و رأی از راهِ subprocess می‌رود. نامِ importیِ `doctor` ملکِ
`_ops/doctor` است (wiring.py:222) و نام‌های عمومیِ آن پکیج (router/scanner/...)
نباید واردِ sys.path ِ پروسهٔ زندهٔ مرکز شوند.

گیت: OCTOPUS_WIRE_DOCTOR_TG (پیش‌فرض خاموش = no-op بایت‌به‌بایت).
امنیت: dedup با کلیدِ mission:gate + cursorِ بایتی (restart-safe)؛ سقفِ روزانه؛
fail-soft (هرگز beat یا dispatch را نمی‌کشد). صدا زدن: Center.beat() و
Center._handle_callback().
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_DOCTOR_TG"
DOCTOR_ROOT = opslib.ORG_ROOT / "OCTOPUS-DOCTOR"
OUTBOX = DOCTOR_ROOT / "90-_meta" / "state" / "tg-outbox.jsonl"
CLI = DOCTOR_ROOT / "doctor" / "cli.py"
CURSOR = opslib.STATE_DIR / "telegram" / "doctor-link-cursor.json"
# سقفِ ابتکاری — کارتِ رأی نادر است؛ سقف فقط پادزهرِ حلقهٔ خراب است، نه throttleِ رأی.
MAX_PER_DAY = 20
MAX_PER_BEAT = 3
_SENT_CAP = 300
_GATES = ("intent", "diff", "test")


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _load_cursor() -> dict:
    try:
        if CURSOR.exists():
            d = json.loads(CURSOR.read_text("utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save_cursor(c: dict) -> None:
    try:
        CURSOR.parent.mkdir(parents=True, exist_ok=True)
        tmp = CURSOR.with_suffix(".tmp")
        tmp.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, CURSOR)
    except Exception:  # noqa: BLE001
        pass


def _read_past(path: Path, pos: int) -> "tuple[list[str], int]":
    """بایت‌های پس از pos (همان الگوی event_bridge). فایل نبود → ([], 0)."""
    if not path.exists():
        return [], 0
    try:
        size = path.stat().st_size
        if size < pos:            # truncate/بازنویسی → از صفر
            pos = 0
        if pos >= size:
            return [], size
        with path.open("rb") as f:
            f.seek(pos)
            chunk = f.read(size - pos).decode("utf-8", errors="replace")
        return chunk.splitlines(), size
    except Exception:  # noqa: BLE001
        return [], pos


def _day_ok(cur: dict, now: float) -> bool:
    if now - cur.get("day_window_start", 0.0) >= 86400.0:
        cur["day_window_start"] = now
        cur["day_count"] = 0
    return cur.get("day_count", 0) < MAX_PER_DAY


def _keyboard(payload: dict):
    kb = ((payload.get("reply_markup") or {}).get("inline_keyboard"))
    return kb if isinstance(kb, list) and kb else None


def _topic_id():
    v = str(os.environ.get("OCTOPUS_DOCTOR_TOPIC_ID", "")).strip()
    if v:
        try:
            return int(v)
        except ValueError:
            return None
    return None


def beat(center=None) -> dict:
    """یک تیک: رکوردهای نوی outbox → sendMessage با clientِ مرکز. خروجی = آمار."""
    out = {"sent": 0, "skipped": 0}
    if not flag_on():
        out["reason"] = "flag-off"
        return out
    client = getattr(center, "_client", None)
    if client is None:
        out["reason"] = "no-client"
        return out
    cur = _load_cursor()
    now = time.time()
    sent_keys = cur.get("sent_keys")
    if not isinstance(sent_keys, dict):
        sent_keys = {}

    lines, new_pos = _read_past(OUTBOX, cur.get("outbox_pos", 0))
    cur["outbox_pos"] = new_pos
    burst = 0
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        payload = rec.get("payload") or {}
        text = str(payload.get("text") or "")
        key = f"{rec.get('mission_id')}:{rec.get('gate')}"
        if not text or key in sent_keys:
            out["skipped"] += 1
            continue
        if burst >= MAX_PER_BEAT or not _day_ok(cur, now):
            out["skipped"] += 1
            continue
        mid = None
        try:
            mid = client.send("🩺 " + text, topic_id=_topic_id(),
                              keyboard=_keyboard(payload))
        except Exception:  # noqa: BLE001 — ارسال هرگز beat را نمی‌کشد
            mid = None
        if mid is not None:
            out["sent"] += 1
            burst += 1
            cur["day_count"] = cur.get("day_count", 0) + 1
            sent_keys[key] = {"ts": now, "message_id": mid}
        else:
            out["skipped"] += 1
    if len(sent_keys) > _SENT_CAP:
        for k, _ in sorted(sent_keys.items(),
                           key=lambda kv: float((kv[1] or {}).get("ts", 0)))[:len(sent_keys) - _SENT_CAP]:
            sent_keys.pop(k, None)
    cur["sent_keys"] = sent_keys
    _save_cursor(cur)
    return out


def _feed_votes(cbq: dict) -> bool:
    """رأیِ خام → doctor/cli.py votes (stdin JSON). subprocess تا sys.path ِ مرکز
    با نام‌های عمومیِ پکیجِ دکتر آلوده نشود."""
    if not CLI.exists():
        return False
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(CLI), "votes"],
            input=json.dumps([cbq], ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8",
            timeout=30, cwd=str(DOCTOR_ROOT))
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def is_doctor_callback(data: str) -> bool:
    parts = str(data or "").split(":")
    return len(parts) == 3 and parts[0] in ("ok", "no") and parts[1] in _GATES


def handle_callback(center, cbq: dict, feeder=None) -> bool:
    """True = این callback مالِ دکتر بود و مصرف شد (موفق یا ناموفق — در هر دو حالت
    نباید به fallbackِ ok/no:<id> برسد وگرنه approvalِ بی‌ربط ثبت می‌شود)."""
    if not flag_on():
        return False
    data = str((cbq or {}).get("data") or "")
    if not is_doctor_callback(data):
        return False
    ok = (feeder or _feed_votes)(cbq)
    toast = ("🩺 رأی ثبت شد" if ok
             else "🩺 رأی نرسید — doctor/cli.py votes شکست خورد")
    try:
        if center is not None and hasattr(center, "_answer"):
            center._answer(cbq, toast)
    except Exception:  # noqa: BLE001
        pass
    return True
