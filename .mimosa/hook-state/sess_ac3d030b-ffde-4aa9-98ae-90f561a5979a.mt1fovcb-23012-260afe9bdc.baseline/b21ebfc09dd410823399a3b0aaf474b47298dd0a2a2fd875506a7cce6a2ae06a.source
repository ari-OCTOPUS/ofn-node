"""
Command line for the Research-Spec Compiler.

    python rsc.py validate specs/debate_extraction.yaml
    python rsc.py run      debate_extraction
    python rsc.py list
    python rsc.py scaffold specs/my_new_idea.yaml

(You can also call `python -m spec_compiler.cli ...` from the project root.)
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

# make the project root importable (so `demo.mock_experiments` resolves)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from spec_compiler.model import load_spec, SpecError            # noqa: E402
from spec_compiler.validator import validate, format_report      # noqa: E402
from spec_compiler.harness import run_spec, format_run           # noqa: E402

SPECS_DIR = os.path.join(_ROOT, "specs")
TEMPLATE = os.path.join(_ROOT, "schema", "research_spec.template.yaml")


def _resolve_spec_path(name_or_path: str) -> str:
    if os.path.exists(name_or_path):
        return name_or_path
    for ext in (".yaml", ".yml", ".json"):
        cand = os.path.join(SPECS_DIR, name_or_path + ext)
        if os.path.exists(cand):
            return cand
    raise SpecError(f"could not find spec '{name_or_path}' (looked in {SPECS_DIR})")


def cmd_validate(args) -> int:
    path = _resolve_spec_path(args.spec)
    spec = load_spec(path)
    report = validate(spec)
    print(format_report(report, title=os.path.basename(path)))
    return 0 if report.ok else 1


def _registries():
    """(real, mock). Real experiments override synthetic mocks by name.

    A broken real registry must NEVER silently demote a run to the synthetic
    mock (mocks are tuned to plausible-looking verdicts, so the demotion would
    fabricate a result). Missing package entirely -> loud notice; broken
    import -> hard error."""
    from demo.mock_experiments import REGISTRY as MOCK
    try:
        from experiments import REGISTRY_REAL as REAL
    except ModuleNotFoundError as e:
        if e.name in ("experiments", "experiments.gridworld_wm") \
                and not os.path.isdir(os.path.join(_ROOT, "experiments")):
            print("NOTE: no experiments/ package found - synthetic mocks only.")
            REAL = {}
        else:
            raise SpecError(f"real experiment registry failed to import: {e}")
    except ImportError as e:
        raise SpecError(f"real experiment registry failed to import: {e}")
    return REAL, MOCK


def cmd_run(args) -> int:
    real, mock = _registries()
    name = args.name
    if name not in real and name not in mock:
        avail = sorted(set(real) | set(mock))
        print(f"unknown experiment '{name}'. Available: {', '.join(avail)}")
        return 2
    path = _resolve_spec_path(name)
    spec = load_spec(path)

    # gate: never run a spec that isn't executable
    report = validate(spec)
    if not report.ok:
        print(format_report(report, title=os.path.basename(path)))
        print("\nRefusing to run: fix blocker gates first.")
        return 1

    if name in real:
        conditions, primary = real[name]()
        dataset = (spec.get("metric") or {}).get("dataset", "real data")
        provenance = f"[REAL run — {dataset}]"
    else:
        conditions, primary = mock[name]()
        provenance = "[SYNTHETIC/mock scores]"
    result = run_spec(spec, conditions, primary=primary)
    print(format_run(result, spec, title=name, provenance=provenance))
    return 0


def cmd_list(args) -> int:
    real, mock = _registries()
    print("Specs in specs/:")
    if os.path.isdir(SPECS_DIR):
        for f in sorted(os.listdir(SPECS_DIR)):
            if f.split(".")[-1] in ("yaml", "yml", "json"):
                print(f"  - {f}")
    print("\nRunnable (registered) experiments:")
    for k in sorted(set(real) | set(mock)):
        tag = "REAL" if k in real else "synthetic mock"
        print(f"  - {k}  [{tag}]")
    return 0


def cmd_scaffold(args) -> int:
    dest = args.dest
    if os.path.exists(dest) and not args.force:
        print(f"{dest} exists (use --force to overwrite)")
        return 1
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    shutil.copyfile(TEMPLATE, dest)
    print(f"scaffolded blank spec -> {dest}")
    print("fill it, then: python rsc.py validate " + dest)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rsc", description="Research-Spec Compiler")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="lint a spec against the 5 hard gates")
    v.add_argument("spec", help="path or name in specs/")
    v.set_defaults(func=cmd_validate)

    r = sub.add_parser("run", help="run the (synthetic) experiment + decision rule")
    r.add_argument("name", help="registered experiment name")
    r.set_defaults(func=cmd_run)

    l = sub.add_parser("list", help="list specs and runnable experiments")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("scaffold", help="copy the blank template to a new spec file")
    s.add_argument("dest", help="destination path, e.g. specs/my_idea.yaml")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_scaffold)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SpecError as e:
        print(f"error: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
