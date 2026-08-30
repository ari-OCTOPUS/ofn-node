"""Command line interface for read-only Mining pre-execution tooling."""
from __future__ import annotations

import argparse
from datetime import datetime

from .governance import aggregate_gates, electricity_gate, verdict_queue_gate, wallet_gate
from .registry import load_hardware_registry, validate_hardware_registry
from .verdicts import load_verdicts, default_mining_verdicts
from .report import render_preexec_report, render_coin_scout_report, save_report
from .io import read_yaml
from .models import CoinCandidate


def _load_candidates(path: str) -> list[CoinCandidate]:
    data = read_yaml(path)
    result: list[CoinCandidate] = []
    for raw in data.get("candidates", []):
        launch_date = raw.get("launch_date")
        parsed_date = None
        if launch_date:
            parsed_date = datetime.fromisoformat(str(launch_date)).date()
        result.append(
            CoinCandidate(
                symbol=str(raw.get("symbol", "")).upper(),
                name=str(raw.get("name", raw.get("symbol", ""))),
                algorithm=str(raw.get("algorithm", "")),
                launch_date=parsed_date,
                launch_age_days=raw.get("launch_age_days"),
                network_hashrate_hs=raw.get("network_hashrate_hs"),
                block_reward=raw.get("block_reward"),
                blocks_per_day=raw.get("blocks_per_day"),
                market_cap_usd=raw.get("market_cap_usd"),
                liquidity_notes=str(raw.get("liquidity_notes", "")),
                dev_activity_notes=str(raw.get("dev_activity_notes", "")),
                community_notes=str(raw.get("community_notes", "")),
                quantum_resistance_claim=bool(raw.get("quantum_resistance_claim", False)),
                source_urls=list(raw.get("source_urls", [])),
            )
        )
    return result


def cmd_readiness(args: argparse.Namespace) -> int:
    nodes = load_hardware_registry(args.hardware) if args.hardware else []
    verdicts = load_verdicts(args.verdicts) if args.verdicts else default_mining_verdicts()
    gates = []
    gates.extend(validate_hardware_registry(nodes))
    gates.append(verdict_queue_gate(verdicts))
    gates.append(electricity_gate(nodes))
    gates.append(wallet_gate(args.wallet_zero_access))
    gates.append(aggregate_gates(gates))
    report = render_preexec_report(gates, nodes)
    if args.output:
        save_report(args.output, report)
    print(report)
    return 0


def cmd_scout(args: argparse.Namespace) -> int:
    candidates = _load_candidates(args.candidates)
    report = render_coin_scout_report(candidates)
    if args.output:
        save_report(args.output, report)
    print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mining-preexec", description="Read-only Mining pre-execution MVP")
    sub = parser.add_subparsers(required=True)

    readiness = sub.add_parser("readiness", help="Generate pre-execution readiness report")
    readiness.add_argument("--hardware", help="YAML hardware registry")
    readiness.add_argument("--verdicts", help="YAML verdict queue")
    readiness.add_argument("--wallet-zero-access", action="store_true", help="Confirm wallet zero-agent-access policy")
    readiness.add_argument("--output", help="Write markdown report to path")
    readiness.set_defaults(func=cmd_readiness)

    scout = sub.add_parser("scout", help="Generate draft coin scout report from YAML candidates")
    scout.add_argument("--candidates", required=True, help="YAML coin candidates")
    scout.add_argument("--output", help="Write markdown report to path")
    scout.set_defaults(func=cmd_scout)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
