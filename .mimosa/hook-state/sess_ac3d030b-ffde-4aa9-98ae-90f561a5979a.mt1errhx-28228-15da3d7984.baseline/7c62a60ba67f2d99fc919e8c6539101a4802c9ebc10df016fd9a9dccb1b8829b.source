"""VERDICT_QUEUE helpers."""
from __future__ import annotations

from .io import read_yaml
from .models import VerdictItem, DecisionStatus


def load_verdicts(path: str) -> list[VerdictItem]:
    data = read_yaml(path)
    items = data.get("verdicts", [])
    result: list[VerdictItem] = []
    for item in items:
        result.append(
            VerdictItem(
                id=str(item["id"]),
                decision=str(item.get("decision", "")),
                status=DecisionStatus(str(item.get("status", "open")).lower()),
                answer=item.get("answer"),
                evidence=item.get("evidence"),
            )
        )
    return result


def default_mining_verdicts() -> list[VerdictItem]:
    return [
        VerdictItem("MIN-V1", "How many rigs/Orange Pi are usable?"),
        VerdictItem("MIN-V2", "Is electricity <$0.05/kWh or solar?"),
        VerdictItem("MIN-V3", "Is zero mining active right now?"),
        VerdictItem("MIN-V4", "Is Hardware Registry filled?"),
        VerdictItem("MIN-V5", "Does wallet access remain zero for agents?"),
        VerdictItem("MIN-V6", "Is coin scouting report-only?"),
    ]
