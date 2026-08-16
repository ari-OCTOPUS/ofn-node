"""lead_painting.py — اسکلت پای lead_painting (روی OFN؛ رأی NBB-V5). فقط ثبت — رفتار خاص بعداً."""
from __future__ import annotations

from nbb_cp.adapters.legs.base import LegAdapter


class LeadPaintingLeg(LegAdapter):
    leg_id = "lead_painting"
    budget_cap_aud = 0.0
