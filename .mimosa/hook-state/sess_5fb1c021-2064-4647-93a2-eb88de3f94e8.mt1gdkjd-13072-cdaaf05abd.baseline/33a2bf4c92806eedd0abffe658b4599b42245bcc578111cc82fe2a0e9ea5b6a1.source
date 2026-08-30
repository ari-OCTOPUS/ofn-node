#!/usr/bin/env python3
"""bridge_beat.py — consumer side برای پلِ pf_os ↔ organism.

این یک helper مستقل است که **الگوی canonical _ops/wiring.py::cockpit_requests_beat**
(خط 1184) را وفادارانه کپی می‌کند، ولی برای خواندن saba-bridge.jsonl.

چرا این جدا از wiring.py؟
  - wiring.py ۱۳۳KB است و لینِ قلب (ساختِ heart/fuel) در حال کار روی آن است.
    لمسِ آن = ریسکِ برخورد (LANE-RULES §4).
  - این helper آماده‌ی integration است. وقتی لینِ قلب تمام شد، فقط **یک خط**
    در wiring.py یا organism.py لازم است:
        from pf_os.bridge_beat import saba_bridge_beat
        saba_bridge_beat()  # در main loop
  - پشتِ flag OCTOPUS_WIRE_SABA_BRIDGE (default OFF = بایت‌به‌بایت).

قراردادِ file-pubsub (طبقِ wiring.py:1200-1241):
  - .lock file با PID برای single-consumer (advisory، stale بعد از 120s)
  - .cursor file با byte offset (at-most-once)
  - rotation detection (cursor > size → reset)
  - advance cursor BEFORE execution (at-most-once semantics)

$0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional, Callable

from . import config

STALE_SECONDS = 120
MAX_PER_BEAT = 50  # کپِ خط در هر beat (مثلِ _TG_EXEC_MAX_PER_BEAT)


def _state_dir() -> Path:
    return Path(config.OPS_STATE)


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def saba_bridge_beat(handler: Optional[Callable[[dict], None]] = None,
                     state_dir: Optional[Path] = None) -> dict:
    """خواندنِ saba-bridge.jsonl و dispatch به handler.

    الگوی کپی‌شده از _ops/wiring.py::cockpit_requests_beat (خط 1184-1276) ولی
    تطبیق‌یافته برای saba-bridge.

    args:
      handler: callable که هر record را می‌گیرد. اگر None، فقط شمارش می‌کند.
      state_dir: override برای تست.

    برمی‌گرداند dict با: {"ran": [...], "skipped": [...], "reason": str (اگر skip)}
    """
    # flag check
    if not config.flag(config.WIRE_BRIDGE):
        return {"skipped": "flag-off"}

    sd = Path(state_dir) if state_dir else _state_dir()
    logp = sd / "saba-bridge.jsonl"
    curp = sd / "saba-bridge.cursor"
    lockp = sd / "saba-bridge.lock"

    if not logp.exists():
        return {"skipped": "no-bridge-file"}

    # single-consumer lock (advisory، PID-based)
    pid = os.getpid()
    try:
        if lockp.exists():
            prev = lockp.read_text(encoding="utf-8").strip() or ":"
            prev_pid = prev.split(":", 1)[0]
            if prev_pid and prev_pid != str(pid) and \
               (time.time() - lockp.stat().st_mtime) < STALE_SECONDS:
                return {"skipped": "locked-by-other"}
        lockp.write_text(f"{pid}:{_now_iso()}", encoding="utf-8")
    except OSError:
        pass

    size = logp.stat().st_size

    # first-activation → ffwd بدونِ replayِ backlog
    if not curp.exists():
        try:
            curp.write_text(str(size), encoding="utf-8")
        except OSError:
            pass
        return {"skipped": "first-activation-ffwd", "at": size}

    try:
        off = int(curp.read_text(encoding="utf-8").strip() or 0)
    except (OSError, ValueError):
        off = 0

    # rotation detection
    if off > size:
        off = 0

    try:
        with open(logp, "rb") as f:
            f.seek(off)
            chunk = f.read()
    except OSError:
        return {"skipped": "read-fail"}

    nl = chunk.rfind(b"\n")
    if nl < 0:
        return {"skipped": "no-complete-line"}

    raw_lines = chunk[:nl + 1].decode("utf-8", "replace").splitlines(keepends=True)
    take = raw_lines[:MAX_PER_BEAT]
    consumed = len("".join(take).encode("utf-8"))
    new_off = off + consumed

    # at-most-once: advance cursor BEFORE exec
    try:
        tmp = curp.with_suffix(".cursor.tmp")
        tmp.write_text(str(new_off), encoding="utf-8")
        os.replace(tmp, curp)
    except OSError:
        return {"skipped": "cursor-persist-failed"}

    ran, skipped = [], []
    for line in take:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            skipped.append("parse-error")
            continue
        # PII defense-in-depth: rec از pf_os است که scrub کرده، ولی دوباره چک کن
        text = str(rec.get("text", ""))
        if any(bad in text.lower() for bad in ("ari", "saba", "sydney", "iran")):
            skipped.append(f"pii-reject:{rec.get('kind','?')}")
            continue
        if handler is not None:
            try:
                handler(rec)
                ran.append(rec.get("kind", "?"))
            except Exception as e:  # noqa: BLE001 — handler خطا نباید beat را بکشد
                skipped.append(f"handler-error:{type(e).__name__}")
        else:
            ran.append(rec.get("kind", "?"))

    return {"ran": ran, "skipped": skipped, "advanced_to": new_off}


def default_handler(rec: dict) -> None:
    """handler پیش‌فرض — فقط log می‌کند. organism می‌تواند خودش را تزریق کنه.

    این نمونه‌ی bezpie است: محتوای rec را log نمی‌کند (PII). فقط kind.
    """
    kind = rec.get("kind", "?")
    count = rec.get("count", 0)
    # مثال: می‌توان به cortex/telemetry فرستاد، ولی فعلاً no-op
    _ = (kind, count)  # placeholder — organism خودش تصمیم می‌گیره


def main() -> int:
    """اجرا از CLI برای تست: python -m pf_os.bridge_beat"""
    if not config.flag(config.WIRE_BRIDGE):
        print(f"🔴 {config.WIRE_BRIDGE}=off.")
        return 0
    r = saba_bridge_beat(handler=default_handler)
    print(f"saba_bridge_beat: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
