"""steering.py — خواندنِ نیّتِ سادهٔ مالک از GOALS-ZIMAN.md (+ حالتِ steering.json).

مثلِ الگوی GOALS-OCTOPUS: هر خطِ «- » یک بولت است، زیرِ سه بخشِ DIRECTIVES/PRIORITIES/
GUARDRAILS. fail-soft (فایلِ نبود/خراب → خالی). stdlib-only، read-only، $0.

این ماژول هیچ‌چیز اجرا نمی‌کند؛ فقط نیّت را به ساختار تبدیل می‌کند تا مدلِ خود و (بعداً)
ماتریس از آن اولویت بسازند. هیچ اکشنِ بیرونی، هیچ خرج.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_MAX_BULLETS = 40  # سقفِ محافظه‌کار برای هر بخش (ضدِ فایلِ غول‌آسا)

# نگاشتِ سرفصل → کلید (تشخیصِ بخش، بی‌حساسیت به حروف و متنِ اضافه بعدِ سرفصل)
_SECTION_HINTS = (
    ("directives", "directive"),
    ("priorities", "priorit"),
    ("guardrails", "guardrail"),
)


def find_goals(start: Optional[Path] = None) -> Optional[Path]:
    """GOALS-ZIMAN.md را با بالا رفتن از مسیرِ جاری می‌یابد."""
    here = Path(start).resolve() if start else Path(__file__).resolve()
    rel = Path("00-Control") / "FOUNDATIONS" / "GOALS-ZIMAN.md"
    for base in [here, *here.parents]:
        cand = base / rel
        if cand.exists():
            return cand
    return None


def _section_key(header_line: str) -> Optional[str]:
    low = header_line.lower()
    for key, hint in _SECTION_HINTS:
        if hint in low:
            return key
    return None


def parse_goals(text: str) -> dict[str, list[str]]:
    """متنِ GOALS-ZIMAN.md → {directives, priorities, guardrails}.

    فقط بولت‌های «- » که *بعد از* یک سرفصلِ شناخته‌شده می‌آیند شمرده می‌شوند؛
    خطوطِ blockquote (>)، کامنت‌های HTML، و متنِ پیش از سرفصل نادیده گرفته می‌شوند.
    """
    out: dict[str, list[str]] = {"directives": [], "priorities": [], "guardrails": []}
    current: Optional[str] = None
    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("#"):                 # سرفصل
            current = _section_key(line)
            continue
        if current is None:
            continue
        m = re.match(r"^\s*-\s+(.*\S)\s*$", line)          # بولتِ «- ...»
        if not m:
            continue
        bullet = m.group(1).strip()
        if bullet.startswith("<!--"):                     # کامنتِ HTML
            continue
        if len(out[current]) < _MAX_BULLETS:
            out[current].append(bullet)
    return out


def load_steering_state(base_dir: Optional[Path] = None) -> dict[str, Any]:
    """حالتِ تپ‌های مالک از state/ziman/steering.json (اگر باشد). fail-soft به پیش‌فرضِ امن."""
    default = {"focus": None, "paused": False, "boosts": [], "mutes": [],
               "updated_iso": None, "source": "default"}
    base = Path(base_dir) if base_dir else Path(".")
    path = base / "state" / "ziman" / "steering.json"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        # فقط کلیدهای شناخته‌شده را می‌پذیریم (ضدِ ورودیِ ناخواسته)
        for k in ("focus", "paused", "boosts", "mutes", "updated_iso", "source"):
            if k in d:
                default[k] = d[k]
        default["paused"] = bool(default["paused"])
    except Exception:  # noqa: BLE001 — نبود/خراب = پیش‌فرضِ امن
        pass
    return default


def load_steering(goals_path: Optional[Path] = None,
                  base_dir: Optional[Path] = None) -> dict[str, Any]:
    """نیّتِ کاملِ مالک: بولت‌های GOALS-ZIMAN.md + حالتِ تپ. fail-soft سراسری."""
    path = Path(goals_path) if goals_path else find_goals()
    found = bool(path and Path(path).exists())
    goals = {"directives": [], "priorities": [], "guardrails": []}
    if found:
        try:
            goals = parse_goals(Path(path).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            found = False
    state = load_steering_state(base_dir)
    return {
        "directives": goals["directives"],
        "priorities": goals["priorities"],
        "guardrails": goals["guardrails"],
        "focus": state["focus"],
        "paused": state["paused"],
        "boosts": state["boosts"],
        "mutes": state["mutes"],
        "source": state["source"],
        "goals_found": found,
    }
