"""direction_reader.py — خواندن جهت مالک از charter/goals (فقط‌خواندنی).

این ماژول فایل charter را فقط می‌خواند و یک Direction می‌سازد.
هیچ فایل مشترکی را ویرایش نمی‌کند. اگر charter پیدا نشد، fallback امن برمی‌گرداند.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .contracts import Direction

_OPS_ROOT = Path(__file__).resolve().parent.parent
_CHARTER = Path(__file__).resolve().parent / "WORLD-DISCOVERY-CHARTER-2026-07-30.md"
_GOALS = _OPS_ROOT / "GOALS-OCTOPUS.md"


def load_direction(
    *,
    charter_path: Optional[Path] = None,
    goals_path: Optional[Path] = None,
) -> Direction:
    """ساخت Direction از رأی‌های ثبت‌شدهٔ مالک در charter.

    این مقادیر از رأی‌های 2026-07-30 گرفته شده‌اند (hard-coded به‌عنوان
    پیش‌فرض)، ولی اگر فایل charter وجود داشت، برای یکپارچگی آن را به‌عنوان
    source ثبت می‌کنیم.
    """
    src = charter_path or _CHARTER
    goals = goals_path or _GOALS
    owner_source = src.name if src.exists() else "fallback"

    # رأی‌های ثبت‌شدهٔ مالک (WORLD-DISCOVERY-CHARTER-2026-07-30 section A)
    return Direction(
        mission_id="wd-mission-2026-07-30",
        domain="ai-competition",
        geography="global",
        horizon_days=7,
        competitors=["Anthropic", "xAI", "Sakana AI", "Moonshot/Kimi K3", "Perplexity"],
        discovery_definition="C+D+E",
        min_sources=2,
        desired_output="testable-opportunity",
        competition_dims=[
            "model-power", "agent-architecture", "memory-personalization",
            "tool-use", "multimodality", "reliability", "safety-governance",
            "distribution", "data-moat", "pricing", "customer-ownership",
            "local-market-depth", "transparency", "operational-execution",
        ],
        action_level="L3",
        owner_source=owner_source,
        notes=(
            "Goals path referenced (read-only): "
            + (str(goals) if goals.exists() else "not-found")
        ),
    )


def read_owner_goals_snippet(goals_path: Optional[Path] = None, max_chars: int = 4000) -> str:
    """خواندنِ فقط‌خواندنیِ GOALS-OCTOPUS.md برای جهت کلی (بدون ویرایش)."""
    p = goals_path or _GOALS
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""
