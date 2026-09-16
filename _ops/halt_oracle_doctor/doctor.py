"""doctor — halt-oracle coverage doctor (READ-ONLY, OFFLINE).

What it answers, per consumer: is the canonical halt oracle actually consulted ON
the path that produces the effect? It emits three machine-readable artifacts:

  receipts/<phase>-coverage-<ts>.json   octopus.halt-coverage-receipt.v1
  receipts/mismatches-<ts>.jsonl        octopus.halt-doctor.v1   (append-only, one row per mismatch)
  receipts/<phase>-result-<ts>.json     octopus.halt-doctor-result.v1

Hard boundaries (from the owner card): no write outside `receipts/`, no create/delete/
arm of any HALT file, no service/timer/systemd/env/budget change, no live-node access,
no network. `mutations_performed` is emitted as 0 on every receipt and the doc-side
canary in the tests asserts it.

Usage:
    python -m _ops.halt_oracle_doctor.doctor \
        --repo F:/ofn-node \
        --declared-home /home/ari \
        --documented-oracle F:/ofn-node/HALT \
        --phase PRE
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import baseline, canon, coverage, resolver, safety_check

PKG = Path(__file__).resolve().parent
DEFAULT_RECEIPTS = PKG / "receipts"
DEFAULT_REPO = Path("F:/ofn-node")
# Declared, never inherited from the environment: the board's service units use
# `User=ari` / `WorkingDirectory=/home/ari/ofn`, which is where this literal comes from.
DEFAULT_DECLARED_HOME = "/home/ari"
# The path AGENTS.md GOV-V7 names as the kill switch. Declared as a parameter
# (not parsed out of prose) so a mismatch is visible rather than smoothed over.
DEFAULT_DOCUMENTED_ORACLE = "F:/ofn-node/HALT"

COVERAGE_SCHEMA = "octopus.halt-coverage-receipt.v1"
MISMATCH_SCHEMA = "octopus.halt-doctor.v1"
RESULT_SCHEMA = "octopus.halt-doctor-result.v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _guard_write(target: Path, receipts_dir: Path) -> None:
    """Runtime write-scope guard: refuse anything outside receipts/."""
    t = target.resolve()
    r = receipts_dir.resolve()
    if r != t and r not in t.parents:
        raise safety_check.FailClosedError(
            f"refusing to write outside receipts/: {t} (allowed root {r})"
        )


def _emit(path: Path, payload: object, receipts_dir: Path) -> str:
    _guard_write(path, receipts_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canon.canonical(payload) if isinstance(payload, dict) else str(payload)
    path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8", newline="\n")
    return canon.digest(payload) if isinstance(payload, dict) else ""


def _append_jsonl(path: Path, rows: list[dict], receipts_dir: Path) -> None:
    _guard_write(path, receipts_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(canon.canonical(r) + "\n")


def _mismatches(canonical: dict, documented: str, cov_rows) -> list[dict]:
    out: list[dict] = []

    resolved = canonical.get("resolved_path")
    if canonical.get("found") and resolved:
        # Normalise for comparison only; the raw strings are kept in the receipt.
        norm = lambda s: str(s).replace("\\", "/").rstrip("/").lower()
        if norm(resolved) != norm(documented):
            out.append({
                "kind": "path_divergence",
                "severity": "high",
                "reason": f"documented oracle {documented!r} != the oracle the code computes {resolved!r}",
                "paths_involved": [documented, resolved],
                "consumers": [],
                "owner_action_required": True,
            })

    for row in cov_rows:
        if row.coverage != "WIRED":
            out.append({
                "kind": "coverage_gap",
                "severity": "high" if row.effect_id == "E-A-telegram-send" else "high",
                "reason": (f"{row.consumer_id} ({row.label}) is path-{row.path_correctness} but "
                           f"coverage-{row.coverage}: the canonical oracle does not stop this effect"),
                "paths_involved": [row.file, row.egress],
                "consumers": [f"{row.file}:{row.function}"],
                "owner_action_required": True,
            })
    return out


def _require_posix_absolute(value: str, flag: str) -> None:
    """Refuse a path that a POSIX->Windows shell may have silently rewritten.

    Observed 2026-09-17: Git-Bash translates a POSIX argument before handing it to a
    native Python - `--declared-home /home/ari` arrived as
    `C:/Program Files/Git/home/ari`, which would have produced a plausible-looking but
    WRONG canonical oracle path. A silently wrong answer is the exact failure mode this
    tool exists to find, so it refuses instead of computing one.
    """
    looks_mangled = (":" in value) or value.startswith("\\\\") or "Program Files" in value
    if looks_mangled or not value.startswith("/"):
        raise safety_check.FailClosedError(
            f"{flag}={value!r} is not an absolute POSIX path - it looks shell-rewritten. "
            f"Re-run with MSYS_NO_PATHCONV=1 (Git-Bash) or pass the literal POSIX path."
        )


def run(repo: Path, declared_home: str, documented_oracle: str,
        receipts_dir: Path, phase: str) -> dict:
    ts = _now_iso()
    stamp = ts.replace(":", "").replace("-", "")

    _require_posix_absolute(declared_home, "--declared-home")

    # 0. fail-closed self-certification BEFORE any analysis
    certification = safety_check.certify(PKG, predicate_import=True, repo=repo)
    canon_failures = canon.self_test()
    if canon_failures:
        raise safety_check.FailClosedError(
            "canonicalization self-test failed: " + "; ".join(canon_failures)
        )

    # 1. what the code computes as the canonical oracle, for a DECLARED home
    canonical = resolver.resolve_canonical_oracle(repo, declared_home)

    # 2. every halt-reading site, with its path source
    sites, parse_failures = resolver.discover_sites(repo)
    site_rows = [s.as_dict() for s in sites]
    consumers_of_oracle = sorted({
        f"{r['file']}:{r['line']}" for r in site_rows if r["path_source"] == "resolved"
    })

    # 3. local proxy state of the oracle path. This is NOT node observation and says so.
    local_proxy = None
    local_candidate = repo / "HALT-ALL"
    try:
        from ofn.kernel.halt import is_halted as _real_predicate  # allowlisted (R2)
        local_proxy = resolver.classify_file(local_candidate, _real_predicate)
        local_proxy["predicate_source"] = "ofn.kernel.halt.is_halted (real predicate)"
    except Exception as exc:  # noqa: BLE001
        local_proxy = {"path": str(local_candidate), "state": "not_classified",
                       "reason": f"predicate unavailable: {type(exc).__name__}"}
    local_proxy["observed_on"] = "local checkout proxy — NOT the live node"

    # 4. coverage per approved consumer
    cov_rows = coverage.analyse_all(repo)
    cov_dicts = [r.as_dict() for r in cov_rows]
    summary = coverage.summarise(cov_rows)

    # The two extra `is_halted` sites found by the site scan: kernel start-gate
    # primitives that RECEIVE a value and do not read the file. Reported here so
    # the three-approved-consumer scope above stays exact and auditable.
    primitives = coverage.analyse_kernel_primitives(repo)

    # Content manifest of every file this analysis read. HEAD pinning alone was NOT
    # enough: 4 of 11 scanned files were uncommitted or never tracked, so the receipt
    # records digests and the POST rule becomes content-level (see baseline.py).
    analysed_files = sorted(
        {s['file'] for s in site_rows}
        | {c['file'] for c in cov_dicts}
        | {pr['file'] for pr in primitives}
        | {'ofn/budget/opslib.py'}
    )
    manifest = baseline.source_manifest(repo, analysed_files)

    mismatches = _mismatches(canonical, documented_oracle, cov_rows)

    # 5. receipts
    coverage_receipt = {
        "schema": COVERAGE_SCHEMA,
        "phase": phase,
        "captured_at_utc": ts,
        "runtime_identity": {
            "repo": str(repo),
            "commit": _git_head(repo),
            "source": "git rev-parse HEAD (read-only)",
        },
        "declared_home": declared_home,
        "documented_oracle": documented_oracle,
        "canonical_oracle": canonical,
        "oracle_path_state": local_proxy,
        "consumers": [
            {
                "effect_id": r["effect_id"],
                "consumer": f"{r['file']}:{r['function']}",
                "coverage": r["coverage"],
                "evidence": r["evidence"],
                "oracle_reference": r["oracle_reference"],
            }
            for r in cov_dicts
        ],
        "out_of_scope_consumers": {
            "checked": True,
            "scanned_sites": len(site_rows),
            "resolved_path_sites": len(consumers_of_oracle),
            "any_label_changed": False,
            "note": "the doctor reports coverage only for the three approved OD-4 consumers",
            "kernel_start_primitives": [
                {"primitive_id": p["primitive_id"], "site": f"{p['file']}:{p['function']}",
                 "coverage": p["coverage"], "reads_halt_file": p["reads_halt_file"],
                 "production_callers": p["production_callers"], "in_od4_scope": p["in_od4_scope"]}
                for p in primitives
            ],
        },
        "summary": summary,
        "source_manifest": manifest,
        "mutations_performed": 0,
        "node_observation": "NOT_PERFORMED — no live-node access (owner boundary)",
        "generated_by": "halt_oracle_doctor (offline, read-only)",
    }

    result = {
        "schema": RESULT_SCHEMA,
        "phase": phase,
        "generated_at_utc": ts,
        "certification": certification,
        "canonical_rule": canon.RULE_ID,
        "canon_self_test": "PASS",
        "canonical_oracle": canonical,
        "halt_sites": site_rows,
        "parse_failures": parse_failures,
        "kernel_start_primitives": primitives,
        "coverage": cov_dicts,
        "summary": summary,
        "source_manifest": manifest,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "mutations_performed": 0,
    }

    cov_path = receipts_dir / f"{phase}-coverage-{stamp}.json"
    res_path = receipts_dir / f"{phase}-result-{stamp}.json"
    mis_path = receipts_dir / f"mismatches-{stamp}.jsonl"

    _emit(cov_path, coverage_receipt, receipts_dir)
    _emit(res_path, result, receipts_dir)
    _append_jsonl(mis_path, [
        {"schema": MISMATCH_SCHEMA, "observed_at_utc": ts, "half": "A_static",
         "canonical_oracle": canonical.get("resolved_path"),
         "documented_oracle": documented_oracle,
         "mismatch": m, "verdict": "DOC_ONLY", "mutations_performed": 0}
        for m in mismatches
    ], receipts_dir)

    result["artifacts"] = {
        "coverage_receipt": str(cov_path),
        "result": str(res_path),
        "mismatches": str(mis_path),
    }
    return result


def _git_head(repo: Path) -> str | None:
    """Read .git/HEAD and the ref it points at, without running git (no subprocess)."""
    try:
        git = repo / ".git"
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head.split("ref:", 1)[1].strip()
            ref_file = git / ref
            if ref_file.exists():
                return ref_file.read_text(encoding="utf-8").strip()
            packed = git / "packed-refs"
            if packed.exists():
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(ref) and not line.startswith("#"):
                        return line.split()[0]
            return None
        return head
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="halt-oracle coverage doctor (read-only, offline)")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--declared-home", default=DEFAULT_DECLARED_HOME)
    ap.add_argument("--documented-oracle", default=DEFAULT_DOCUMENTED_ORACLE)
    ap.add_argument("--receipts", default=str(DEFAULT_RECEIPTS))
    ap.add_argument("--phase", default="PRE", choices=["PRE", "POST"])
    ap.add_argument("--json", action="store_true", help="print the full result JSON")
    args = ap.parse_args(argv)

    try:
        result = run(Path(args.repo), args.declared_home, args.documented_oracle,
                     Path(args.receipts), args.phase)
    except safety_check.FailClosedError as exc:
        print(f"BLOCKED_BY_SAFETY: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(canon.canonical(result))
    else:
        print(f"halt-oracle doctor — phase {result['phase']}")
        print(f"  certification : {result['certification']['certified']} "
              f"(static violations: {result['certification']['static_violations']})")
        print(f"  canonical rule: {result['canonical_rule']}  self-test PASS")
        co = result["canonical_oracle"]
        print(f"  oracle (code) : {co.get('resolved_path')}")
        print(f"  oracle (docs) : {args.documented_oracle}")
        s = result["summary"]
        print(f"  consumers     : {s['consumers_total']} total, {s['path_correct']} path-correct, "
              f"{s['covered_by_canonical_oracle']} covered by the oracle")
        for row in result["coverage"]:
            print(f"    - {row['consumer_id']:6} {row['label']:32} "
                  f"path={row['path_correctness']:6} coverage={row['coverage']}")
            print(f"      evidence: {row['evidence']}")
        print(f"  halt sites    : {len(result['halt_sites'])} (parse failures: {len(result['parse_failures'])})")
        for pr in result["kernel_start_primitives"]:
            print(f"    - {pr['primitive_id']:6} {pr['file']}:{pr['line'] if 'line' in pr else pr['function']}"
                  f"  coverage={pr['coverage']:12} reads_file={pr['reads_halt_file']}"
                  f"  callers={len(pr['production_callers'])}")
        print(f"  mismatches    : {result['mismatch_count']}")
        print(f"  source files  : {result['source_manifest']['file_count']} digests (content-level baseline)")
        print(f"  mutations     : {result['mutations_performed']}")
        print(f"  artifacts     : {result['artifacts']['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
