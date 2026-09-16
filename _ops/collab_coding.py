#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_coding.py — هم‌کدنویسیِ مالک↔ارگانیسم فقط از تلگرام (propose-only).

قانون‌ها:
  - هیچ auto-apply / merge / deploy
  - هیچ ساختنِ OCTOPUS_CB_SECRET
  - هیچ خواندنِ .env / secret / PII
  - هر پیشنهاد = یک کارت با diffِ کوتاه + معیارِ ابطال + مسیرِ فایل
  - ذخیره append-only در state/collab/proposals.jsonl

دستورهای متنی (از intent/center):
  /code status | /code propose <idea> | /code list | /code show <id>
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

FLAG = "OCTOPUS_WIRE_COLLAB_CODING"
_HERE = Path(__file__).resolve().parent
STATE = _HERE / "state" / "collab"
QUEUE = STATE / "proposals.jsonl"

# الگوهای ممنوع در متنِ پیشنهاد (defense-in-depth)
_BANNED = re.compile(
    r"(api[_-]?key|secret|password|token\s*=|BEGIN\s+PRIVATE|seed\s*phrase|"
    r"OCTOPUS_CB_SECRET\s*=)",
    re.I,
)


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _pid(text: str) -> str:
    return "cc-" + hashlib.sha256(f"{text}|{_now()}".encode("utf-8")).hexdigest()[:10]


def _read_all() -> list[dict]:
    if not QUEUE.exists():
        return []
    out = []
    try:
        for ln in QUEUE.read_text("utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if isinstance(d, dict):
                out.append(d)
    except OSError:
        pass
    return out


def list_proposals(limit: int = 8) -> list[dict]:
    rows = _read_all()
    # newest last in append-only → reverse
    return list(reversed(rows[-max(1, limit):]))


def get(pid: str) -> dict | None:
    for r in reversed(_read_all()):
        if r.get("id") == pid:
            return r
    return None


def _classify_idea(idea: str) -> dict:
    """حدسِ سبک از ایده → هدفِ فایل/خانواده (پیشنهاد، نه اجرا)."""
    t = (idea or "").lower()
    if any(k in t for k in ("لید", "lead", "نقاش", "scorer", "امتیاز")):
        return {
            "family": "lead",
            "paths": ["_ops/legs/lead_scorer.py", "_ops/tests/test_lead_scorer.py"],
            "risk": "low",
            "falsify": "لیدِ مسکونیِ نمونه باید draft/save شود نه skip؛ strata همچنان اول بماند",
        }
    if any(k in t for k in ("c6", "فرضیه", "hypothesis", "probe", "پروب")):
        return {
            "family": "c6",
            "paths": ["_ops/c6_probes.py", "_ops/c6_producer.py", "_ops/tests/test_c6_hypothesis_producer.py"],
            "risk": "low",
            "falsify": "پروبِ خاموش/خطادار صفر ردیف بسازد؛ فقط count>floor ردیف بسازد",
        }
    if any(k in t for k in ("تز", "thesis", "delta", "phi", "معادله", "identity", "هویت")):
        return {
            "family": "thesis",
            "paths": ["_ops/identity_equations.py", "_ops/outcomes/thesis_queue.py",
                      "_ops/state/thesis/thesis-ledger.json"],
            "risk": "low",
            "falsify": "هر ردیف kill داشته باشد؛ هیچ ادعای phenomenal بدون بازنویسی",
        }
    if any(k in t for k in ("تلگرام", "telegram", "دکمه", "menu", "intent")):
        return {
            "family": "telegram",
            "paths": ["_ops/telegram_center/intent.py", "_ops/telegram_center/center.py"],
            "risk": "medium",
            "falsify": "intentِ نو danger=read مگر state عوض کند؛ بدون secret در لاگ",
        }
    if any(k in t for k in ("romajan", "pslq", "sindy", "ریاض")):
        return {
            "family": "romajan",
            "paths": ["_ops/c6_probes.py", "_program-deliverables/romajan-c6-wiring-2026-07-25/DESIGN.md"],
            "risk": "low",
            "falsify": "read-only نسبت به F:\\romajan؛ claim بدون verified وارد FACT نشود",
        }
    return {
        "family": "general",
        "paths": ["_ops/GOALS-OCTOPUS.md", "ARCHITECTURE-SOT.md"],
        "risk": "medium",
        "falsify": "پچ باید flag-gated و testable باشد؛ IMPROVE-DON'T-REWRITE",
    }


def propose(idea: str, *, source: str = "telegram") -> dict:
    """یک پیشنهادِ propose-only ثبت کن. هرگز کد را اعمال نمی‌کند."""
    if not enabled():
        return {"ok": False, "reason": "flag-off", "hint": "set OCTOPUS_WIRE_COLLAB_CODING=1"}
    idea = str(idea or "").strip()
    if len(idea) < 8:
        return {"ok": False, "reason": "idea-too-short"}
    if _BANNED.search(idea):
        return {"ok": False, "reason": "banned-pattern-in-idea",
                "hint": "راز/کلید را در چت ننویس؛ فقط مسیر و رفتار را بگو"}
    if len(idea) > 2000:
        idea = idea[:2000]

    meta = _classify_idea(idea)
    pid = _pid(idea)
    row = {
        "id": pid,
        "status": "PROPOSED",
        "source": source,
        "idea": idea,
        "family": meta["family"],
        "target_paths": meta["paths"],
        "risk": meta["risk"],
        "falsify": meta["falsify"],
        "apply": "FORBIDDEN — owner implements or next agent under verdict",
        "created_at": _now(),
    }
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        with QUEUE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as e:
        return {"ok": False, "reason": f"write-failed:{type(e).__name__}"}
    return {"ok": True, "proposal": row}


def status_card() -> str:
    rows = _read_all()
    n = len(rows)
    by = {}
    for r in rows:
        by[r.get("status", "?")] = by.get(r.get("status", "?"), 0) + 1
    lines = [
        "🧩 collab coding (propose-only)",
        f"flag={'ON' if enabled() else 'OFF'}",
        f"proposals={n} " + " ".join(f"{k}={v}" for k, v in sorted(by.items())),
        "دستورها:",
        "  /code propose <ایده>",
        "  /code list",
        "  /code show <id>",
        "اعمال خودکار: هرگز. رأی/پیاده‌سازی با مالک یا ایجنتِ بعدی.",
    ]
    return "\n".join(lines)


def list_card(limit: int = 5) -> str:
    rows = list_proposals(limit=limit)
    if not rows:
        return "صفِ collab خالی است. با /code propose <ایده> شروع کن."
    lines = [f"🧩 آخرین {len(rows)} پیشنهاد:"]
    for r in rows:
        lines.append(
            f"· {r.get('id')} [{r.get('family')}/{r.get('status')}] "
            f"{str(r.get('idea', ''))[:60]}"
        )
    return "\n".join(lines)


def show_card(pid: str) -> str:
    r = get(str(pid or "").strip())
    if not r:
        return f"پیشنهادِ {pid} پیدا نشد."
    paths = r.get("target_paths") or []
    return "\n".join([
        f"🧩 {r.get('id')} — {r.get('status')}",
        f"خانواده: {r.get('family')} · ریسک: {r.get('risk')}",
        f"ایده: {r.get('idea')}",
        "مسیرها:",
        *[f"  - {p}" for p in paths],
        f"ابطال: {r.get('falsify')}",
        f"apply: {r.get('apply')}",
        f"at: {r.get('created_at')}",
    ])


def handle_command(text: str) -> str:
    """پارسرِ سادهٔ /code ... برای center."""
    raw = str(text or "").strip()
    low = raw.lower()
    # strip leading /code or code
    body = raw
    for pref in ("/code", "code", "/کد", "کد"):
        if low.startswith(pref):
            body = raw[len(pref):].strip()
            break
    if not body or body.lower() in ("status", "وضعیت", "help", "؟", "?"):
        return status_card()
    if body.lower().startswith("list") or body.startswith("لیست"):
        return list_card()
    if body.lower().startswith("show") or body.startswith("نشان"):
        pid = body.split(None, 1)[1].strip() if len(body.split(None, 1)) > 1 else ""
        return show_card(pid)
    if body.lower().startswith("propose") or body.startswith("پیشنهاد"):
        idea = body.split(None, 1)[1].strip() if len(body.split(None, 1)) > 1 else ""
        res = propose(idea)
        if not res.get("ok"):
            return f"❌ {res.get('reason')} {res.get('hint', '')}".strip()
        p = res["proposal"]
        return show_card(p["id"]) + "\n\n✅ ثبت شد (اعمال نشد)."
    # bare idea after /code
    res = propose(body)
    if not res.get("ok"):
        return f"❌ {res.get('reason')} {res.get('hint', '')}".strip()
    return show_card(res["proposal"]["id"]) + "\n\n✅ ثبت شد (اعمال نشد)."
