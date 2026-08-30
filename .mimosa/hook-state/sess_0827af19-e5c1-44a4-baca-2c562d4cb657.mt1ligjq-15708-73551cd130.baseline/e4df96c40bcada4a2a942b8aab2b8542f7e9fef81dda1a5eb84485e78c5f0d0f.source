"""Markdown report rendering."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import GateResult, HardwareNode, CoinCandidate
from .scout import score_candidate


def render_gate_table(gates: list[GateResult]) -> str:
    lines = ["| Gate | Pass | Risk | Message |", "|---|---:|---|---|"]
    for g in gates:
        lines.append(f"| {g.name} | {'✅' if g.passed else '❌'} | {g.risk.value} | {g.message} |")
    return "\n".join(lines)


def render_preexec_report(gates: list[GateResult], nodes: list[HardwareNode]) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    text = [
        "# Mining Pre-Execution Readiness Report",
        "",
        f"Generated: `{ts}`",
        "",
        "> Scope: INFORM-only. This report does not approve mining, SSH, deploy, wallet access, or financial execution.",
        "",
        "## Gate Summary",
        render_gate_table(gates),
        "",
        "## Hardware Snapshot",
        "| Node | Type | Status | Power | $/kWh | Role |",
        "|---|---|---|---|---:|---|",
    ]
    if nodes:
        for n in nodes:
            cost = "" if n.electricity_cost_usd_kwh is None else f"{n.electricity_cost_usd_kwh:.4f}"
            text.append(
                f"| {n.node_id} | {n.device_type} | {n.status.value} | {n.power_source.value} | {cost} | {n.role} |"
            )
    else:
        text.append("| — | — | no registry | — | — | — |")
    text += [
        "",
        "## Required Human Actions",
        "- Close all VERDICT_QUEUE items.",
        "- Confirm wallet zero-access policy remains immutable.",
        "- Verify electricity source/cost before any experiment.",
        "- Fill hardware registry with real node statuses.",
        "- Run one-node benchmark only after human approval.",
    ]
    return "\n".join(text) + "\n"


def render_coin_scout_report(candidates: list[CoinCandidate]) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Mining Coin Scout Draft Report",
        "",
        f"Generated: `{ts}`",
        "",
        "> Scope: draft only. Coin scouting is report-only until human verdict.",
        "",
        "| Symbol | Algorithm | ARM | Score | Risk | Notes |",
        "|---|---|---:|---:|---|---|",
    ]
    for c in candidates:
        s = score_candidate(c)
        notes = "; ".join(s["reasons"][:3]).replace("|", "/")
        lines.append(
            f"| {s['symbol']} | {s['algorithm']} | {'✅' if s['arm_viable'] else '❌'} | {s['score']} | {s['risk']} | {notes} |"
        )
    return "\n".join(lines) + "\n"


def save_report(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
