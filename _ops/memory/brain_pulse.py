"""brain_pulse.py — file-bridge از مغزهای داخلی → چت (لایهٔ ۵ → لایهٔ ۳).

حقیقت معماری (VERIFY روی کد):
  · cortex = پروسهٔ جدا روی :8772؛ حرف چت را مستقیم نمی‌گیرد؛ فقط owner_guidance می‌خواند.
  · business_brain = run_all(beat)؛ از چت بی‌خبر است.
  · خروجی‌های زنده در state/cortex/*.json و identities-latest.json هستند.

این ماژول فقط **می‌خواند** (cite-only). هیچ IPC به :8772، هیچ authorize، هیچ اثر بیرونی.
may_authorize همیشه False. fail-soft.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))

SCHEMA = "brain-pulse.v1"


def _read(rel: str) -> dict | None:
    p = STATE_DIR / rel
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def snapshot() -> dict[str, Any]:
    """شاهد زندهٔ مغزها برای unified_context / Sources / مدل."""
    out: dict[str, Any] = {
        "schema": SCHEMA,
        "bridge": "file-read-only",
        "ipc_to_cortex": False,
        "chat_heard_by_brains": False,
        "note": (
            "مغزها نبض خودشان را دارند؛ چت خروجی‌شان را از فایل می‌خواند "
            "(نه سوکت به :8772). حرفِ تو به cortex فقط از مسیر owner_guidance می‌رسد."
        ),
        "may_authorize": False,
        "four_d_connected": False,
        "warnings": [],
    }

    cx = _read("cortex/cortex-state.json")
    if cx:
        members = cx.get("members") or []
        present_n = sum(1 for m in members if isinstance(m, dict) and m.get("present"))
        thought = cx.get("thought") if isinstance(cx.get("thought"), dict) else {}
        align = cx.get("alignment") if isinstance(cx.get("alignment"), dict) else {}
        out["cortex"] = {
            "live": True,
            "source": "state/cortex/cortex-state.json",
            "cycle": cx.get("cycle"),
            "coherence": cx.get("coherence"),
            "ts": cx.get("ts"),
            "members_present": present_n,
            "members_total": len(members) if isinstance(members, list) else None,
            "aligned": align.get("aligned"),
            "thought_summary": (str(thought.get("summary") or "")[:160] or None),
            "role": "planning/reasoning organ (process :8772)",
        }
    else:
        out["cortex"] = {
            "live": False,
            "source": "state/cortex/cortex-state.json",
            "role": "planning/reasoning organ (process :8772)",
        }
        out["warnings"].append("cortex-state missing/unreadable")

    bb = _read("cortex/business-brain-latest.json")
    if bb:
        props = bb.get("proposals") or []
        titles = []
        for p in props[:3]:
            if isinstance(p, dict) and p.get("title"):
                titles.append(str(p["title"])[:100])
        out["business_brain"] = {
            "live": True,
            "source": "state/cortex/business-brain-latest.json",
            "beat": bb.get("beat"),
            "ts": bb.get("ts"),
            "n_proposals": bb.get("n_proposals") if bb.get("n_proposals") is not None
            else len(props),
            "proposal_titles": titles,
            "projects": [
                {"id": p.get("id"), "status": p.get("status"), "name": p.get("name")}
                for p in (bb.get("projects") or [])[:5]
                if isinstance(p, dict)
            ],
            "role": "business/opportunity brain",
        }
    else:
        out["business_brain"] = {
            "live": False,
            "source": "state/cortex/business-brain-latest.json",
            "role": "business/opportunity brain",
        }
        out["warnings"].append("business-brain-latest missing/unreadable")

    ident = _read("identities-latest.json")
    if ident:
        vals = {}
        for k, v in (ident.get("identities") or {}).items():
            if isinstance(v, dict) and v.get("value") is not None:
                vals[k] = v.get("value")
        out["identities"] = {
            "source": "state/identities-latest.json",
            "ts": ident.get("ts"),
            "values": vals,
        }
    else:
        out["identities"] = None

    sk = _read("doctor/self-knowledge-latest.json")
    if sk:
        und = sk.get("understanding") if isinstance(sk.get("understanding"), dict) else {}
        dd = sk.get("deep_dive") if isinstance(sk.get("deep_dive"), dict) else {}
        sf = dd.get("smallest_fix")
        if isinstance(sf, dict):
            sf = sf.get("description") or sf.get("action") or sf.get("fix")
        out["doctor_self_knowledge"] = {
            "source": "state/doctor/self-knowledge-latest.json",
            "focus": (str(und.get("focus") or und.get("current_focus") or "")[:120] or None),
            "smallest_fix": (str(sf or "").strip()[:160] or None),
        }
    else:
        out["doctor_self_knowledge"] = None

    return out


def as_context_block(*, limit: int = 900) -> str:
    """متن فشرده برای پرامپت مدل."""
    snap = snapshot()
    lines: list[str] = [
        "brain_pulse (file-bridge؛ مغزها حرف چت را مستقیم نمی‌شنوند):",
        f"  bridge={snap.get('bridge')} ipc_to_cortex={snap.get('ipc_to_cortex')} "
        f"chat_heard_by_brains={snap.get('chat_heard_by_brains')}",
    ]
    cx = snap.get("cortex") or {}
    if cx.get("live"):
        lines.append(
            "  cortex: cycle={c} coherence={ch} members={m}/{t} aligned={a}".format(
                c=cx.get("cycle"), ch=cx.get("coherence"),
                m=cx.get("members_present"), t=cx.get("members_total"),
                a=cx.get("aligned"),
            )
        )
        if cx.get("thought_summary"):
            lines.append("  cortex.thought: " + str(cx["thought_summary"])[:140])
    else:
        lines.append("  cortex: UNREADABLE")

    bb = snap.get("business_brain") or {}
    if bb.get("live"):
        lines.append(
            "  business_brain: beat={b} proposals={n}".format(
                b=bb.get("beat"), n=bb.get("n_proposals"))
        )
        for t in bb.get("proposal_titles") or []:
            lines.append("  - " + t)
    else:
        lines.append("  business_brain: UNREADABLE")

    ident = snap.get("identities") or {}
    vals = (ident.get("values") if isinstance(ident, dict) else None) or {}
    if vals:
        bits = " ".join(f"{k}={v}" for k, v in list(vals.items())[:6])
        lines.append("  identities: " + bits[:180])

    sk = snap.get("doctor_self_knowledge") or {}
    if isinstance(sk, dict) and (sk.get("focus") or sk.get("smallest_fix")):
        if sk.get("focus"):
            lines.append("  doctor.focus: " + str(sk["focus"])[:120])
        if sk.get("smallest_fix"):
            lines.append("  doctor.smallest_fix: " + str(sk["smallest_fix"])[:140])

    text = "\n".join(lines)
    return text[:limit]


def for_unified_self_context() -> dict[str, Any]:
    """شکل سازگار با unified_context.self_context + فیلدهای زنده."""
    snap = snapshot()
    org = _read("ORGANISM-STATE.json") or {}
    pa = org.get("pain_assessment") if isinstance(org.get("pain_assessment"), dict) else {}
    return {
        "cortex": snap.get("cortex") or {"live": False},
        "business_brain": snap.get("business_brain") or {"live": False},
        "identities": snap.get("identities"),
        "doctor_self_knowledge": snap.get("doctor_self_knowledge"),
        "four_d_connected": False,
        "bridge": snap.get("bridge"),
        "ipc_to_cortex": False,
        "chat_heard_by_brains": False,
        "note": snap.get("note"),
        "may_authorize": False,
        "runtime": {
            "beat": org.get("beat"),
            "halted": bool(org.get("halted")),
            "pain": pa.get("pain"),
            "protective_skip": bool(org.get("protective_skip")),
        },
        "warnings": snap.get("warnings") or [],
    }
