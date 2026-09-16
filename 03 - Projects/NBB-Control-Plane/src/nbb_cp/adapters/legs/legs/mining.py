"""mining.py — اسکلت پای mining (روی OFN؛ رأی NBB-V5). فقط ثبت — رفتار خاص بعداً."""
from __future__ import annotations

from nbb_cp.adapters.legs.base import LegAdapter


class MiningLeg(LegAdapter):
    leg_id = "mining"
    budget_cap_aud = 0.0
