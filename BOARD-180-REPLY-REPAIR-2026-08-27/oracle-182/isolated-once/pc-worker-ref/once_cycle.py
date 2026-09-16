# Isolated reference — NOT 182 production. Do not claim c3f085a8.
# Bug class: --once is parsed then main() returns without cycle()
# (prod copy returns after --selftest/--crash-test only; --once never calls cycle).
from __future__ import annotations

import argparse
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/root/octopus-mesh")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--crash-test", action="store_true")
    return ap.parse_args(argv)


class Worker:
    def __init__(self, inbox: list[Any]):
        self.inbox = list(inbox)
        self.claimed: list[Any] = []
        self.cycle_calls = 0

    def cycle(self, max_n: int | None = None, one_claim: bool = False) -> dict:
        self.cycle_calls += 1
        n = 0
        for item in self.inbox:
            if one_claim and n >= 1:
                break
            if max_n is not None and n >= max_n:
                break
            self.claimed.append(item)
            n += 1
        return {"claimed": n, "inbox": len(self.inbox)}


def _crash_and_soak(_root: str, _cycles: int) -> int:
    # prod: soak/fork path — --once must NOT land here as a silent return.
    return 0


def main_buggy(argv: list[str], inbox: list[Any]) -> tuple[int, Worker]:
    """Mirrors prod: --once is a no-op; never cycle()."""
    args = parse_args(argv)
    w = Worker(inbox)
    if args.selftest:
        return 0, w
    if args.crash_test:
        return _crash_and_soak(args.root, args.cycles), w
    return 0, w


def main_fixed(argv: list[str], inbox: list[Any], max_n: int = 1) -> tuple[int, Worker]:
    """--once runs one bounded cycle (max-N / one-claim). No inbox stampede."""
    args = parse_args(argv)
    w = Worker(inbox)
    if args.selftest:
        return 0, w
    if args.crash_test:
        return _crash_and_soak(args.root, args.cycles), w
    if args.once:
        w.cycle(max_n=max_n, one_claim=True)
        return 0, w
    return 0, w
