"""دو شورای فاز یک (سایه): Architecture + Epistemic — فقط deliberation.

اعضای این نسخه دترمینیستیک‌اند (stubs سند) — اعضای مدلِ واقعی پس از گیت‌های
Go/No-Go سند وصل می‌شوند. هیچ tool/شبکه/subprocess در این بسته نیست.
"""
from __future__ import annotations

from councils.base import BaseCouncil, CouncilMember


def _stub_arch_opinion(ctx: dict) -> dict:
    return {"opinion": "طرح با مرز اعتمادِ فعلی سازگار است؛ نیازمند پیوستِ "
            "شواهدِ مرز (DA-4/DA-5).",
            "evidence": ["council-mesh-v0.1 §معماری هدف", "DA-4 قرارداد عمل"],
            "confidence": 0.6, "verdict": "ok",
            "reproducible": True, "policy_violation": False, "falsifiable": True}


def _stub_epi_opinion(ctx: dict) -> dict:
    return {"opinion": "ادعای شناختی باید با ClaimGraph و falsifier ثبت شود، "
            "نه متن آزاد.",
            "evidence": ["ADR-037 evidence level C"],
            "confidence": 0.55, "verdict": "ok",
            "reproducible": True, "policy_violation": False, "falsifiable": True}


class ArchitectureCouncil(BaseCouncil):
    name = "architecture"

    def __init__(self):
        super().__init__(members=[
            CouncilMember("arch-1", family="architecture-docs", opinion_fn=_stub_arch_opinion),
            CouncilMember("arch-2", family="live-tree", opinion_fn=_stub_arch_opinion),
        ])


class EpistemicCouncil(BaseCouncil):
    name = "epistemic"

    def __init__(self):
        super().__init__(members=[
            CouncilMember("epi-1", family="hypothesis-engine", opinion_fn=_stub_epi_opinion),
            CouncilMember("epi-2", family="observatory", opinion_fn=_stub_epi_opinion),
        ])
