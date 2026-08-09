#!/usr/bin/env python3
"""Print the repository-derived baseline: tenants, gates, registry size, tests.

This exists because of CLAUDE.md §8-a. Every number that documents quote about
this node — how many tenants, how many gates are shut, how many sources are in
the painting registry, how many tests are green — has been written into prose
at least once and been wrong within a day. A number that is worth writing down
is worth deriving, so the documents point here instead of stating a figure.

Usage:
    python3 tools/repo_baseline.py            # fast: packs, gates, registry
    python3 tools/repo_baseline.py --tests    # also collects the test count
    python3 tools/repo_baseline.py --json     # machine-readable
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ofn.adapters.packloader import load_dir  # noqa: E402

# Gates that are shut deliberately, not by accident. Named here so the count of
# closed gates is derived per tenant rather than asserted node-wide: `studio`
# carries one the others do not, and a single node-wide number hides that.
DELIBERATELY_SHUT = ("secret_rotation", "partner_precondition", "miner_isolation")


def tenants() -> dict:
    """Tenant -> its declared gates, straight from packs/."""
    specs = load_dir(os.path.join(ROOT, "packs"))
    return {name: sorted(spec.gates) for name, spec in sorted(specs.items())}


def registry_sources() -> int | None:
    """How many sources the painting registry actually holds."""
    path = os.path.join(ROOT, "data", "painting_source_registry.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    sources = data.get("sources", [])
    return len(sources)


def test_count() -> int | None:
    """Ask pytest how many tests it can collect. Slow; opt-in."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        cwd=ROOT, capture_output=True, text=True,
    )
    for line in reversed(proc.stdout.strip().splitlines()):
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].startswith("test"):
            return int(parts[0])
    return None


def baseline(with_tests: bool = False) -> dict:
    packs = tenants()
    shut = {
        name: [g for g in gates if g in DELIBERATELY_SHUT]
        for name, gates in packs.items()
    }
    out = {
        "tenants": sorted(packs),
        "tenant_count": len(packs),
        "gates_by_tenant": packs,
        "shut_gates_by_tenant": shut,
        "painting_registry_sources": registry_sources(),
    }
    if with_tests:
        out["collected_tests"] = test_count()
    return out


def main(argv: list[str]) -> int:
    data = baseline(with_tests="--tests" in argv)
    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"tenants ({data['tenant_count']}): {', '.join(data['tenants'])}")
    for name in data["tenants"]:
        shut = data["shut_gates_by_tenant"][name]
        print(f"  {name:<8} gates={len(data['gates_by_tenant'][name]):<2} "
              f"shut={', '.join(shut) if shut else '-'}")
    print(f"painting registry sources: {data['painting_registry_sources']}")
    if "collected_tests" in data:
        print(f"collected tests: {data['collected_tests']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
