#!/usr/bin/env python3
"""owner_guidance.py — Task 3b (2026-07-24): حلقهٔ owner→brain با directiveهای **bounded**.

قرارداد (مرزِ سخت):
  · مالک از تلگرام «/brain guide <متن>» می‌زند → approval_channel (in-process ارگانیسم،
    owner-gated) این ماژول را صدا می‌زند و یک خط به artifactِ append-only
    `state/cortex/owner-guidance.jsonl` می‌نویسد.
  · cortex (پروسهٔ جدا، 8772) در ابتدای هر cycle فقط `effective()` را **می‌خواند** —
    هیچ‌وقت خودش TelegramApprovalChannel نمی‌سازد (ضدِ 409؛ قانونِ process-locality).
  · directiveها bounded و بسته‌اند — هیچ متنِ آزادی «اجرا» نمی‌شود (DATA نه دستور):
      focus: <متن ≤200>        → فقط hint متنی برای think (steering، نه فرمان)
      think_every_n: N          → کادنسِ فکر، فقط در بازهٔ [1,100]
      pause: think              → فکرِ LLM موقتاً خاموش (deterministic summary می‌ماند)
      resume: think             → لغوِ pause
    متنِ بدونِ کلید = focus (رایج‌ترین حالت).
  · درونِ mandateِ $0: هیچ spend/effector — فقط فایلِ state. fail-soft همه‌جا.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

_FILE_NAME = "owner-guidance.jsonl"
_MAX_RAW = 300
_MAX_FOCUS = 200
_THINK_LO, _THINK_HI = 1, 100
_PAUSABLE = frozenset({"think"})
_MAX_TAIL_LINES = 200   # سقفِ fold — فایل append-only است، فقط دُم مهم است


def _gpath(state_dir=None) -> Path:
    sd = Path(state_dir) if state_dir else opslib.STATE_DIR
    return sd / "cortex" / _FILE_NAME


def parse(text: str) -> tuple[dict | None, str | None]:
    """متنِ مالک → directiveِ bounded یا خطا. خالص/تست‌پذیر؛ هیچ I/O.

    خروجی: (directive, None) یا (None, error). directive فقط کلیدهای بسته دارد:
    focus / think_every_n / paused. مقدارِ خارج از کران = خطا (نه clamp بی‌صدا —
    مالک باید بداند چه چیزی پذیرفته شد)."""
    t = str(text or "").strip()
    if not t:
        return None, "متنِ خالی"
    out: dict = {}
    for line in t.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("focus:"):
            v = line.split(":", 1)[1].strip()
            if not v:
                return None, "focus خالی"
            out["focus"] = v[:_MAX_FOCUS]
        elif low.startswith("think_every_n:"):
            v = line.split(":", 1)[1].strip()
            try:
                n = int(v)
            except ValueError:
                return None, f"think_every_n عددِ صحیح نیست: {v[:20]}"
            if not (_THINK_LO <= n <= _THINK_HI):
                return None, f"think_every_n خارج از بازهٔ [{_THINK_LO},{_THINK_HI}]: {n}"
            out["think_every_n"] = n
        elif low.startswith("pause:"):
            v = line.split(":", 1)[1].strip().lower()
            if v not in _PAUSABLE:
                return None, f"pause فقط برای {sorted(_PAUSABLE)} مجاز است"
            out["paused"] = True
        elif low.startswith("resume:"):
            v = line.split(":", 1)[1].strip().lower()
            if v not in _PAUSABLE:
                return None, f"resume فقط برای {sorted(_PAUSABLE)} مجاز است"
            out["paused"] = False
        elif ":" in line and low.split(":", 1)[0].strip() in (
                "period", "period_s", "rate", "bpm", "cap", "budget", "spend"):
            # مرزِ سخت: steeringِ مغز هرگز نرخ/پول را فرمان نمی‌دهد (ADR-001 هم‌راستا)
            return None, f"کلیدِ «{low.split(':', 1)[0].strip()}» در steeringِ مغز مجاز نیست"
        else:
            # متنِ بدونِ کلیدِ شناخته = focus (رایج‌ترین حالتِ مالک)
            out["focus"] = (out.get("focus", "") + " " + line).strip()[:_MAX_FOCUS]
    if not out:
        return None, "هیچ directive معتبری پیدا نشد"
    return out, None


def append(text: str, state_dir=None, by: str = "owner") -> dict:
    """اعتبارسنجی + append اتمیک به jsonl. خروجی: {ok, directive|error}."""
    directive, err = parse(text)
    if err:
        return {"ok": False, "error": err}
    rec = {"ts": opslib.now_iso(), "by": str(by)[:40],
           "raw": str(text or "")[:_MAX_RAW], "directive": directive}
    p = _gpath(state_dir)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        return {"ok": False, "error": f"write-failed:{type(e).__name__}"}
    return {"ok": True, "directive": directive}


def effective(state_dir=None) -> dict:
    """foldِ last-wins روی دُمِ فایل → directiveِ مؤثرِ فعلی. fail-soft → {}.
    cortex این را در ابتدای هر cycle می‌خواند (فقط‌خواندنی، $0)."""
    p = _gpath(state_dir)
    try:
        if not p.exists():
            return {}
        lines = p.read_text("utf-8").splitlines()[-_MAX_TAIL_LINES:]
    except OSError:
        return {}
    out: dict = {}
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        d = rec.get("directive")
        if isinstance(d, dict):
            for k in ("focus", "think_every_n", "paused"):
                if k in d:
                    out[k] = d[k]
            out["_ts"] = rec.get("ts")
    # کران‌ها را در خواندن هم دوباره enforce کن (فایلِ دست‌کاری‌شده → امن)
    if "think_every_n" in out:
        try:
            n = int(out["think_every_n"])
            if not (_THINK_LO <= n <= _THINK_HI):
                out.pop("think_every_n", None)
            else:
                out["think_every_n"] = n
        except (TypeError, ValueError):
            out.pop("think_every_n", None)
    if "focus" in out:
        out["focus"] = str(out["focus"])[:_MAX_FOCUS]
    return out


if __name__ == "__main__":
    print(json.dumps(effective(), ensure_ascii=False, indent=2))
