#!/usr/bin/env python3
"""Offline-first vLLM KV block-size planning harness.

Default behavior only writes local WAVE0 planning artifacts.  This script has
no implementation that starts vLLM or sends inference/network requests.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ofn.adapters.vllm_metrics import (  # noqa: E402
    PrometheusParseError,
    discover_vllm_metrics,
)
from ofn.benchmarks.result_store import ResultStore  # noqa: E402
from ofn.benchmarks.vllm_block_size import (  # noqa: E402
    FINAL_STATUSES,
    CanaryLaunchAuthorization,
    PlanningError,
    SafetyValidationError,
    backend_plan,
    collect_local_preflight,
    validate_canary_launch_authorization,
)
from ofn.benchmarks.workload_manifest import (  # noqa: E402
    build_workload_manifest,
    write_workload_manifest,
)


NEW_FILE_PATHS = (
    "ofn/benchmarks/__init__.py",
    "ofn/benchmarks/vllm_block_size.py",
    "ofn/benchmarks/workload_manifest.py",
    "ofn/benchmarks/result_store.py",
    "ofn/adapters/vllm_metrics.py",
    "scripts/benchmark_vllm_block_size.py",
    "ofn/organism/tests/test_vllm_block_size_estimator.py",
    "ofn/organism/tests/test_vllm_block_size_planning.py",
    "ofn/organism/tests/test_vllm_workload_manifest.py",
    "ofn/organism/tests/test_vllm_metrics.py",
    "ofn/organism/tests/test_vllm_result_store.py",
    "ofn/organism/tests/test_vllm_block_size_cli.py",
    "docs/adr/ADR-VLLM-KV-BLOCK-SIZE.md",
    "artifacts/vllm-block-size/preflight.json",
    "artifacts/vllm-block-size/workload-manifest.json",
    "artifacts/vllm-block-size/results.csv",
    "artifacts/vllm-block-size/pareto-report.md",
    "artifacts/vllm-block-size/recommendation.md",
    "artifacts/vllm-block-size/rollback.md",
)


def _parse_supported_sizes(raw: str | None) -> tuple[int, ...] | None:
    if raw is None:
        return None
    try:
        values = tuple(int(item.strip()) for item in raw.split(",") if item.strip())
    except ValueError as exc:
        raise ValueError(
            "supported block sizes must be comma-separated integers"
        ) from exc
    if not values:
        raise ValueError("supported block sizes must not be empty")
    return values


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build offline WAVE0 plans for vLLM logical KV block-size "
            "experiments. Default mode performs no network or process action."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "validate-canary"),
        default="plan",
        help="plan is the default offline dry-run",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/vllm-block-size",
        help="local artifact directory",
    )
    parser.add_argument("--seed", type=int, default=20_260_825)
    parser.add_argument("--samples-per-concurrency", type=int, default=4)
    parser.add_argument("--backend")
    parser.add_argument("--vllm-version")
    parser.add_argument(
        "--supported-block-sizes",
        help="observed same-version capability values; never guessed",
    )
    parser.add_argument(
        "--capability-source",
        help="non-sensitive reference to same-version help/log evidence",
    )
    parser.add_argument(
        "--enable-diagnostic-size-one",
        action="store_true",
        help="keep supported size 1 in a separate diagnostic-only lane",
    )
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--owner-approval-reference")
    parser.add_argument("--owner-thermal-limit-c", type=float)
    parser.add_argument(
        "--canary-endpoint",
        help="required for validation; never contacted or persisted",
    )
    parser.add_argument(
        "--production-endpoint",
        action="append",
        default=[],
        help="origin(s) that must be rejected; never persisted",
    )
    parser.add_argument(
        "--metrics-file",
        help="local Prometheus fixture/snapshot; no network scrape is performed",
    )
    parser.add_argument(
        "--execute-canary",
        action="store_true",
        help=(
            "reserved hard gate; WAVE0 observer harness refuses live execution "
            "even after validation"
        ),
    )
    return parser


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rollback_command() -> str:
    quoted = " ".join(f"'{path}'" for path in NEW_FILE_PATHS)
    return f"rm -f -- {quoted}"


def _render_pareto_report(status: str) -> str:
    return f"""# vLLM KV Block-Size Pareto Report

- final_status: `{status}`
- empirical_result_rows: `0`
- pareto_frontier: `not computed`

No GPU benchmark was run. `results.csv` contains only its redacted schema
header, so there is no empirical TTFT, E2E, throughput, APC, preemption,
fragmentation, queue, or memory winner.

Theoretical tail-fragmentation estimates cannot select a block size. Candidate
selection requires at least three independent repetitions, separate cold/warm
cache phases, complete metrics, safety gates, and non-overlapping confidence
evidence.
"""


def _render_recommendation(preflight: dict[str, object]) -> str:
    status = str(preflight["status"])
    if status not in FINAL_STATUSES:
        raise AssertionError("invalid recommendation status")
    return f"""# vLLM KV Block-Size Recommendation

- final_status: `{status}`
- selected_profile: `none`
- selected_block_size: `unknown`
- baseline_block_size: `unknown (platform auto was not resolved)`
- model/revision: `unknown`
- GPU/backend: `no compatible local CUDA/ROCm evidence; backend unknown`
- workloads: `W1-W5 planned; W4 awaits an owner-supplied anonymized histogram`
- confidence: `none — no GPU measurements`
- TTFT delta: `not measured`
- throughput delta: `not measured`
- cache-hit delta: `not measured`
- fragmentation delta: `theoretical only; not decision evidence`
- preemption delta: `not measured`
- known limitations: `no local vLLM/GPU, version-resolved capabilities, resolved cache config, or Prometheus run data`
- rollback command: `{_rollback_command()}`

There is no empirical winner. Do not infer a preferred block size from the
estimator, do not alter a running process dynamically, and do not deploy.
"""


def _render_rollback() -> str:
    listed = "\n".join(f"- `{path}`" for path in NEW_FILE_PATHS)
    return f"""# Rollback — vLLM KV Block-Size Harness

No rollback was executed. Review the repository state first, then remove only
the files introduced by this harness:

{listed}

Scoped command (documentation only; not executed):

```bash
{_rollback_command()}
rmdir --ignore-fail-on-non-empty \
  artifacts/vllm-block-size scripts ofn/benchmarks
```

Do not reset the branch, clean untracked files, or touch existing prefix-cache
work, services, systemd, endpoints, state, logs, or unrelated dirty files.
"""


def _add_candidate_plan(
    preflight: dict[str, object], args: argparse.Namespace
) -> None:
    supported = _parse_supported_sizes(args.supported_block_sizes)
    if args.backend is None and supported is None:
        return
    if args.backend is None:
        raise PlanningError("backend is required with supported candidates")
    plan = backend_plan(
        backend=args.backend,
        supported=supported,
        vllm_version=args.vllm_version,
        capability_source=args.capability_source,
        enable_diagnostic_size_one=args.enable_diagnostic_size_one,
    )
    preflight["block_size_plan"] = {
        "baseline_auto": plan.baseline_auto,
        "candidates": list(plan.candidates),
        "diagnostic_candidates": list(plan.diagnostic_candidates),
        "backend": plan.backend,
        "vllm_version": plan.vllm_version,
        "capability_source_supplied": plan.capability_source is not None,
    }


def _validate_canary(args: argparse.Namespace) -> None:
    metrics_available = False
    if args.metrics_file:
        metrics_text = Path(args.metrics_file).read_text(encoding="utf-8")
        discovery = discover_vllm_metrics(
            metrics_text,
            vllm_version=args.vllm_version,
            strict=True,
        )
        metrics_available = discovery.required_metrics_available
    validate_canary_launch_authorization(
        CanaryLaunchAuthorization(
            owner_approved=args.owner_approved,
            owner_approval_reference=args.owner_approval_reference,
            owner_thermal_limit_c=args.owner_thermal_limit_c,
            metrics_available=metrics_available,
            candidate_endpoint=args.canary_endpoint or "",
            production_endpoints=tuple(args.production_endpoint),
        )
    )
    if not args.vllm_version:
        raise PlanningError("same-version vLLM evidence is required")
    if (
        not args.backend
        or not args.supported_block_sizes
        or not args.capability_source
    ):
        raise PlanningError(
            "backend, supported candidates, and capability source are required"
        )
    if args.execute_canary:
        raise SafetyValidationError(
            "live canary execution is disabled in WAVE0_OBSERVE_ONLY"
        )


def _write_plan_artifacts(
    output_dir: Path, preflight: dict[str, object], args: argparse.Namespace
) -> None:
    _write_json(output_dir / "preflight.json", preflight)
    manifest = build_workload_manifest(
        seed=args.seed,
        samples_per_concurrency=args.samples_per_concurrency,
    )
    write_workload_manifest(output_dir / "workload-manifest.json", manifest)
    ResultStore(output_dir / "results.csv").ensure_header()
    status = str(preflight["status"])
    (output_dir / "pareto-report.md").write_text(
        _render_pareto_report(status),
        encoding="utf-8",
    )
    (output_dir / "recommendation.md").write_text(
        _render_recommendation(preflight),
        encoding="utf-8",
    )
    (output_dir / "rollback.md").write_text(
        _render_rollback(),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        preflight = collect_local_preflight()
        _add_candidate_plan(preflight, args)
        if args.mode == "validate-canary":
            _validate_canary(args)
        elif args.execute_canary:
            raise SafetyValidationError(
                "--execute-canary requires validate-canary mode and remains disabled"
            )
        output_dir = Path(args.output_dir)
        _write_plan_artifacts(output_dir, preflight, args)
    except (
        OSError,
        PlanningError,
        PrometheusParseError,
        SafetyValidationError,
        ValueError,
    ) as exc:
        print(f"status=BLOCKED_SAFETY reason={type(exc).__name__}", file=sys.stderr)
        return 2
    print(f"status={preflight['status']}")
    print(f"offline_plan_written={Path(args.output_dir)}")
    print("canary_launched=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
