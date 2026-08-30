#!/usr/bin/env python3
"""cortex/heart_brain.py — مغز مشاور DeepSeek برای Heart v2 (کاملاً advisory).

· بیداری رویدادمحور (kernel)؛ فقط از model_router.ask (درِ واحد موجود) — صفر HTTP جدید.
· خروجی ساختاریافته {assessment, questions, proposals}؛ schema نامعتبر/timeout/ردِ بودجه
  ⇒ DEGRADED بدون proposal اجرایی. proposals همیشه executable=false.
· هیچ متنی جز خلاصهٔ reasoning ذخیره نمی‌شود؛ chain-of-thought خام هرگز نوشته نمی‌شود.
· اعتبار: تحلیل/سؤال/پیشنهاد — اجرا تنها از مسیر decision_arbiter/EffectorGate آینده.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

SINK = opslib.STATE_DIR / "cortex" / "heart-brain" / "advisories.jsonl"
TASK = "heart_brain"
MAX_TOKENS = 700

_SYSTEM = (
    "You are the advisory cognitive layer of OCTOPUS, a homeostatic organism. "
    "Respond ONLY with a JSON object with keys: assessment (string, <=3 sentences), "
    "questions (array of {id, question, reason, blocking}), proposals (array of "
    "{capability, target, arguments, expected_benefit, risks, rollback, confidence, "
    "ttl_s}). Every proposal MUST be low-risk and reversible; you have NO execution "
    "authority. Never request money transfer, identity change, deletion, or "
    "production-wire changes. Be concise and factual; unknowns must be stated as "
    "unknown, never guessed.")


def _packet(kernel_out: dict, observations: list[dict]) -> str:
    """بستهٔ آگاهیِ محدود — فاقد secret/متن خام پیام‌ها."""
    vital = [o for o in observations if o["metric"] in (
        "organism.beat", "organism.sleep_s", "pulse.effective_period_s",
        "pulse.driver", "vitals.stress", "provider.deepseek_ok_age_s",
        "telegram.live", "disk.write_failures_1h")]
    return json.dumps({
        "identity": "OCTOPUS organism on owner laptop",
        "vital_state": {"mode": kernel_out.get("mode"),
                        "beat": kernel_out.get("beat"),
                        "period_s": kernel_out.get("period_advisory_s"),
                        "green_streak": kernel_out.get("green_streak"),
                        "n_missing": kernel_out.get("n_missing"),
                        "n_stale": kernel_out.get("n_stale"),
                        "write_failures_1h": kernel_out.get("write_failures_1h")},
        "observations": [{"metric": o["metric"], "value": o["value"],
                          "quality": o["quality"]} for o in vital],
        "wake_reasons": kernel_out.get("wake_reasons"),
        "instruction": "Assess organism state; ask only decision-relevant "
                       "questions; propose only reversible internal actions.",
    }, ensure_ascii=False)


def _parse_model_json(text: str) -> "dict | None":
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        d = json.loads(text[start:end])
        if not isinstance(d, dict):
            return None
        d.setdefault("assessment", "")
        d.setdefault("questions", [])
        d.setdefault("proposals", [])
        for p in d["proposals"]:
            if isinstance(p, dict):
                p["executable"] = False     # ساختاری: هرگز اجرایی
        return d
    except (ValueError, TypeError):
        return None


def wake(kernel_out: dict, observations: list[dict], *, beat: int) -> dict:
    """یک بیداری. خروجی همیشه dict صادق؛ هرگز raise نمی‌کند. $0-guarded توسط router."""
    rec = {"schema": "heart-brain-advisory/1", "ts": opslib.now_iso(),
           "beat": beat, "wake_reasons": kernel_out.get("wake_reasons"),
           "status": "SKIPPED"}
    if not kernel_out.get("wake_brain"):
        return rec
    try:
        import model_router as mr   # درِ واحد موجود (cortex)
        out = mr.ask(TASK, _packet(kernel_out, observations),
                     system=_SYSTEM, max_tokens=MAX_TOKENS)
        if not (isinstance(out, dict) and out.get("ok")):
            rec["status"] = "DEGRADED"
            rec["reason"] = str(out.get("reason") or "provider-unavailable")[:120]
            return rec
        parsed = _parse_model_json(str(out.get("text") or ""))
        if parsed is None:
            rec["status"] = "DEGRADED"
            rec["reason"] = "model output not parseable JSON"
            return rec
        rec["status"] = "OK"
        rec["model"] = out.get("model")
        rec["assessment"] = str(parsed.get("assessment"))[:600]
        rec["questions"] = parsed.get("questions", [])[:5]
        rec["proposals"] = parsed.get("proposals", [])[:5]
        return rec
    except Exception as e:  # noqa: BLE001 — مغز هرگز ضربان را نمی‌کشد
        rec["status"] = "DEGRADED"
        rec["reason"] = f"{type(e).__name__}"
        return rec


def record(advisory: dict) -> None:
    """رسید فقط-خلاصه (بدون chain-of-thought) — append-only در state."""
    try:
        SINK.parent.mkdir(parents=True, exist_ok=True)
        with SINK.open("a", encoding="utf-8") as f:
            f.write(json.dumps(advisory, ensure_ascii=False) + "\n")
    except OSError:
        pass


def latest(n: int = 3) -> list[dict]:
    try:
        lines = SINK.read_text("utf-8").splitlines()
        return [json.loads(x) for x in lines[-n:]][::-1]
    except (OSError, ValueError):
        return []
