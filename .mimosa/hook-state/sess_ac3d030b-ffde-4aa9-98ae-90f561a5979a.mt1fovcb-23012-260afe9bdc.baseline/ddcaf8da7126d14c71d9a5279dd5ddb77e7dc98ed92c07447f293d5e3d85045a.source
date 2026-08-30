"""session_memory.py — فاز S: session memory سبک (موقت، درون-فرایند + آخرین N روی دیسک).

سه نوع حافظه (مگاپرامت):
  1. session memory: مکالمهٔ فعلی — موقت، مجاز
  2. episodic candidate: خلاصهٔ رویداد — فقط candidate/proposal، may_authorize=false
  3. semantic/core: حقیقت پایدار — write خودکار ممنوع (نیازمند رأی مالک)

این ماژول فقط #1 (session) را نگه می‌دارد و #2 را به‌صورت candidate پیشنهاد می‌دهد.
هیچ semantic write نمی‌کند. may_authorize همیشه false. fail-soft مطلق.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))

SESSION_SCHEMA = "session-memory.v1"
# آخرین N نوبت روی دیسک (درون-فرایند cache کامل‌تر است؛ دیسک برای restart)
SESSION_MAX_TURNS = 12
SESSION_FILE = STATE_DIR / "session" / "session-memory.jsonl"

# درون-فرایند (کامل‌تر از دیسک — فقط برای همین process)
_SESSION: list[dict[str, Any]] = []


def remember(turn_id: str, role: str, intent: str, text: str) -> dict[str, Any]:
    """یک نوبت به session اضافه کن (موقت). fail-soft."""
    if not turn_id or not text:
        return {"ok": False, "reason": "missing turn_id/text"}
    rec = {
        "schema": SESSION_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "turn_id": str(turn_id)[:128],
        "role": "owner" if role == "owner" else "collaborator",
        "intent": str(intent or "chat")[:100],
        # فقط خلاصهٔ کوتاه/هش — نه متن کامل (privacy-light)
        "text_preview": str(text)[:120],
        "may_authorize": False,
    }
    _SESSION.append(rec)
    if len(_SESSION) > SESSION_MAX_TURNS * 2:
        del _SESSION[: len(_SESSION) - SESSION_MAX_TURNS * 2]
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with SESSION_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass  # session هرگز نباید مکالمه را بکشد
    return {"ok": True, "turn_id": turn_id}


def recent(limit: int = 6) -> list[dict[str, Any]]:
    """آخرین نوبت‌های session (برای context؛ از درون-فرایند)."""
    return list(_SESSION[-max(0, min(int(limit), 12)):])


def as_context_block(limit: int = 6) -> str:
    """بلوک متنی سبک برای تزریق به مدل — «مکالمهٔ اخیر»."""
    turns = recent(limit)
    if not turns:
        return ""
    lines = []
    for t in turns:
        who = "مالک" if t.get("role") == "owner" else "اختاپوس"
        lines.append(f"{who}: {t.get('text_preview', '')}")
    return "مکالمهٔ اخیر (session):\n" + "\n".join(lines)


def propose_remember(query: str) -> dict[str, Any]:
    """«یادت بماند» → episodic candidate (نه commit). may_authorize=false."""
    return {
        "schema": "memory-proposal.v1",
        "proposal": "MEMORY_CANDIDATE",
        "text": str(query or "")[:300],
        "may_authorize": False,
        "status": "candidate_not_committed",
        "note": "semantic write خودکار ممنوع است؛ نیازمند رأی مالک + مسیر memory governance.",
    }


def clear() -> None:
    """پاک‌کردن session (موقت). فقط همین process."""
    _SESSION.clear()
    try:
        if SESSION_FILE.is_file():
            SESSION_FILE.unlink()
    except OSError:
        pass


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear()
        print("session cleared")
    else:
        print(json.dumps(recent(), ensure_ascii=False, indent=2))
