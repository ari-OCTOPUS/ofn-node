#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""debate_hook.py — گیت بدایع برای حلقهٔ مناظره، پیش از مصرف بودجه.

پیشفرض خاموش (OCTOPUS_WIRE_NOVELTY_GATE=1 برای فعالسازی). fail-soft:
آرشیو در دسترس نباشد → allow با دلیل (مناظره هرگز بهخاطر گیت نمیمیرد).

هزینه: صفر فراخوانِ پولی — فقط متن/هش/فاصلهٔ محلی.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_SCHEMA = "novelty-gate.v1"
_FLAG = "OCTOPUS_WIRE_NOVELTY_GATE"


def novelty_gate_enabled() -> bool:
    """فلگ گیت بدایع: env صریح برنده؛ وگرنه رأیِ tracked owner-verdicts (همقراردادِ
    life_currency.enabled). fail-soft: هر خطا = خاموش."""
    v = os.environ.get(_FLAG)
    if v is not None:
        return str(v).strip().lower() in ("1", "true", "yes", "on")
    try:
        import owner_verdicts as _ov  # noqa: WPS433 — _ops روی sys.path
        return str(_ov.get(_FLAG) or "0").strip().lower() in ("1", "true", "yes", "on")
    except Exception:  # noqa: BLE001
        return False


def pre_budget_gate(idea: str, topic_id: str, archive_path: Path | None = None) -> dict:
    """حکم گیت روی یک ایده، پیش از هر فراخوان بعدی/اجرای mutation.

    خروجی: {allow: bool, state, nearest_jaccard, reason, schema, grade}.
    allow=False یعنی همان ایده/واریاسیونِ آرشیوشده — بودجه نباید صرفش شود.
    """
    from novelty.archive import NoveltyArchive, evaluate, vector_from_proposal

    if archive_path is None:
        archive_path = Path(__file__).resolve().parent.parent / "state" / "novelty" / "archive.jsonl"
    if not Path(archive_path).exists():
        return {"allow": True, "state": "ARCHIVE_EMPTY",
                "reason": "no archive yet — nothing to compare against",
                "schema": _SCHEMA, "grade": "MEASURED"}
    try:
        arc = NoveltyArchive(archive_path)
        entries = arc.load()
    except Exception:
        return {"allow": True, "state": "ARCHIVE_UNAVAILABLE",
                "reason": "fail-soft: archive read failed", "schema": _SCHEMA,
                "grade": "MEASURED"}
    try:
        res = evaluate({"text": idea, "problem_class": f"debate:{topic_id}"}, entries)
    except Exception:
        return {"allow": True, "state": "EVAL_ERROR",
                "reason": "fail-soft: evaluate failed", "schema": _SCHEMA,
                "grade": "MEASURED"}
    return {"allow": bool(res.get("allow")), "state": res.get("state"),
            "nearest_jaccard": (res.get("nearest") or {}).get("jaccard_char3"),
            "reason": res.get("reason"), "schema": _SCHEMA, "grade": "MEASURED"}
