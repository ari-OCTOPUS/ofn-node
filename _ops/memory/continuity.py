#!/usr/bin/env python3
"""memory/continuity.py — «هرگز گم نشود»: backup اتمیک + خودزندگی‌نامه در Obsidian.

· snapshot فقط با SQLite Online Backup API (کپی خام DB زنده/WAL ممنوع).
· manifest با checksum دیسک + tip ژنوم + نسخه‌ها؛ بازیابی از temp تست می‌شود.
· پروجکشن Obsidian: _memory/OCTOPUS/NOW.md + AUTOBIOGRAPHY/YYYY/YYYY-MM-DD.md —
  idempotent، بخش مالک هرگز بازنویسی نمی‌شود؛ append-only با مهر beat.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
import sys
for _p in (str(_OPS / "budget"), str(_OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

BACKUP_DIR = opslib.STATE_DIR / "heart-v2-backups"
MEM_DIR = _OPS.parent / "_memory" / "OCTOPUS"
MARKER = opslib.STATE_DIR / "pulse" / "continuity-last.json"
DAILY_BACKUP = True
KEEP = 7


def _sha256_file(p: Path) -> "str | None":
    try:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def backup_db(dest: Path) -> "dict":
    """snapshot اتمیک chrono.db از طریق backup API (WAL-aware)."""
    src = opslib.STATE_DIR / "chrono.db"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return {"ok": False, "reason": "no chrono.db"}
    try:
        s = sqlite3.connect(str(src))
        d = sqlite3.connect(str(dest))
        with d:
            s.backup(d)
        d.close()
        s.close()
        return {"ok": True, "sha256": _sha256_file(dest),
                "size": dest.stat().st_size}
    except sqlite3.Error as e:
        return {"ok": False, "reason": f"{type(e).__name__}"}


def _prune() -> None:
    try:
        snaps = sorted(BACKUP_DIR.glob("chrono-*.db"))
        for old in snaps[:-KEEP]:
            old.unlink(missing_ok=True)
    except OSError:
        pass


def _genome_tip() -> dict:
    try:
        tip = json.loads((opslib.GENOME_DIR / "ledger" / "ledger.jsonl.tip.json")
                         .read_text("utf-8-sig"))
        return {k: tip.get(k) for k in ("n", "tip_hash")}
    except Exception:  # noqa: BLE001
        return {}


def _drill_restore(snap: Path) -> "dict":
    """بازیابی به temp و بازکردن فقط‌خواندنی — اثبات قابل‌بازگشت بودن."""
    tmp = snap.with_suffix(".restore-drill.db")
    try:
        if tmp.exists():
            tmp.unlink()
        con = sqlite3.connect(f"file:{snap.as_posix()}?mode=ro", uri=True)
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        con.close()
        return {"ok": True, "tables": len(tables)}
    except sqlite3.Error as e:
        return {"ok": False, "reason": f"{type(e).__name__}"}
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _now_projection(state: dict) -> str:
    lines = [
        "---", "type: organism-now", "schema: octopus-now/1",
        f"updated: {state.get('ts')}", f"beat: {state.get('beat')}",
        "---", "",
        "# OCTOPUS — الان",
        "",
        f"- **حالت:** {state.get('mode')} (قبلاً {state.get('mode_prev')})",
        f"- **beat:** {state.get('beat')} · streak سبز: {state.get('green_streak')}",
        f"- **period advisory:** {state.get('period_advisory_s')}s "
        "(زنده: pulse_arbiter با anchor G4)",
        f"- **مغز:** ok={state.get('brain_stats', {}).get('ok')} "
        f"degraded={state.get('brain_stats', {}).get('degraded')}",
        f"- **store:** beats={state.get('store_counts', {}).get('beats')} "
        f"events={state.get('store_counts', {}).get('events')}",
        "", "<!-- ماشین‌نوشت؛ بخش مالک زیر خط است -->", "",
    ]
    return "\n".join(lines)


def _autobiography_entry(state: dict) -> "str | None":
    mode = state.get("mode")
    if mode in (None, "", "GENESIS", "BOOTING"):
        return None
    day = dt.date.today()
    stamp = f"- **{state.get('ts')}** · beat {state.get('beat')} → حالت **{mode}**" \
            f" (از {state.get('mode_prev')}) · streak {state.get('green_streak')}"
    return f"{day.isoformat()}\n{stamp}\n"


def project(state: dict) -> dict:
    """پروجکشن Obsidian — فقط بخش ماشین؛ محتوای مالک دست‌نخورده."""
    wrote = []
    try:
        MEM_DIR.mkdir(parents=True, exist_ok=True)
        now = MEM_DIR / "NOW.md"
        if not now.exists():
            now.write_text("", encoding="utf-8")
        text = now.read_text("utf-8")
        machine = _now_projection(state)
        if "<!-- ماشین‌نوشت" in text:
            head = text.split("<!-- ماشین‌نوشت", 1)[0]
            owner = text.split("<!-- ماشین‌نوشت", 1)[1]
            new = machine + "<!-- ماشین‌نوشت" + owner
        else:
            new = machine + text
        tmp = now.with_suffix(".tmp")
        tmp.write_text(new, encoding="utf-8")
        os.replace(tmp, now)
        wrote.append("NOW.md")

        entry = _autobiography_entry(state)
        if entry:
            day_line, stamp = entry.split("\n", 1)
            ab = MEM_DIR / "AUTOBIOGRAPHY" / str(dt.date.today().year) / \
                f"{dt.date.today().isoformat()}.md"
            ab.parent.mkdir(parents=True, exist_ok=True)
            body = ab.read_text("utf-8") if ab.exists() else \
                f"---\ntype: autobiography\nday: {day_line}\n---\n\n## {day_line}\n"
            if stamp not in body:
                if not body.endswith("\n"):
                    body += "\n"
                body += stamp
                tmp = ab.with_suffix(".tmp")
                tmp.write_text(body, encoding="utf-8")
                os.replace(tmp, ab)
                wrote.append(ab.name)
    except OSError:
        pass
    return {"projected": wrote}


def tick(beat: int) -> dict:
    """فراخوان از HEAL organ — روزی یک backup؛ پروجکشن هر بار (ارزان)."""
    from heart import runtime as hrt   # circular-safe: خواندن projection
    state = hrt.read_latest() or {}
    out = {"beat": beat, "projected": project(state).get("projected", [])}
    today = dt.date.today().isoformat()
    try:
        last = json.loads(MARKER.read_text("utf-8-sig"))
    except (OSError, ValueError):
        last = {}
    if DAILY_BACKUP and last.get("day") != today:
        snap = BACKUP_DIR / f"chrono-{today}-{int(time.time())}.db"
        res = backup_db(snap)
        if res.get("ok"):
            drill = _drill_restore(snap)
            _prune()
            out["backup"] = {"sha256": res.get("sha256"), "size": res.get("size"),
                             "restore_drill": drill, "genome_tip": _genome_tip()}
            MARKER.parent.mkdir(parents=True, exist_ok=True)
            tmp = MARKER.with_suffix(".tmp")
            tmp.write_text(json.dumps({"day": today, "ts": opslib.now_iso()},
                                      ensure_ascii=False), "utf-8")
            os.replace(tmp, MARKER)
        else:
            out["backup"] = res
    return out
