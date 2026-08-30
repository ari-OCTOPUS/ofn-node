"""Command-line entry point.

    python -m nbb_cp_kre.cli scan  --vault "F:\\backup" --out "F:\\kre-out"
    python -m nbb_cp_kre.cli run   --vault "F:\\backup" --out "F:\\kre-out" --top-k 40
    python -m nbb_cp_kre.cli report --out "F:\\kre-out"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .app.pipeline import load_result, run_pipeline
from .kernel.guard import ReadOnlyViolation


def _bar(frac: float, msg: str) -> None:
    w = 34
    filled = int(w * max(0.0, min(1.0, frac)))
    sys.stdout.write(f"\r[{'█'*filled}{'·'*(w-filled)}] {frac*100:5.1f}%  {msg[:46]:<46}")
    sys.stdout.flush()
    if frac >= 1.0:
        sys.stdout.write("\n")


def _print_summary(res) -> None:
    s, g = res.scan, res.graph_summary
    print(f"\n{'='*66}\nSCAN\n{'='*66}")
    print(f"  root            : {s.root}")
    print(f"  dirs walked     : {s.n_dirs_walked:,}")
    print(f"  files seen      : {s.n_files_seen:,}")
    print(f"  markdown notes  : {s.n_markdown:,}  ({s.bytes_markdown/1024/1024:.1f} MB)")
    print(f"  elapsed         : {s.elapsed_s}s")
    if s.excluded_hits:
        top = list(s.excluded_hits.items())[:6]
        print(f"  excluded dirs   : " + ", ".join(f"{k}×{v}" for k, v in top))
    for w in s.warnings:
        print(f"  ⚠  {w}")
    print(f"\n  notes per top-level folder (top 12):")
    for k, v in list(s.per_top_folder.items())[:12]:
        print(f"      {k[:44]:<46}{v:>7,}")

    print(f"\n{'='*66}\nLINK GRAPH\n{'='*66}")
    for k in ("n_nodes", "n_edges", "avg_degree", "median_degree",
              "isolated_notes", "isolated_pct", "broken_links", "ambiguous_links"):
        print(f"  {k:<18}: {g[k]}")
    print(f"  resolution        : {g['resolution']}")
    print(f"\n  hubs:")
    for h in g["hubs"][:8]:
        print(f"      {h['degree']:>4}  {h['note'][:56]}")

    if res.bakeoff:
        b = res.bakeoff
        print(f"\n{'='*66}\nREPRESENTATION COMPETITION\n{'='*66}")
        print(f"  {'representation':<26}{'AUC':>10}{'±sd':>8}{'AP':>9}{'sec':>8}")
        print("  " + "-" * 61)
        for sc in b.scores:
            if sc.skipped:
                print(f"  {sc.name:<26}{'skipped':>10}   {sc.skip_reason}")
            else:
                star = " ★" if sc.name == b.winner else ""
                print(f"  {sc.name:<26}{sc.auc_mean:>10.3f}{sc.auc_std:>8.3f}"
                      f"{sc.ap_mean:>9.3f}{sc.seconds:>8.1f}{star}")
        print(f"\n  control AUC {b.control_auc:.3f} → "
              f"{'OK (no leakage)' if b.control_ok else 'FAILED — results void'}")
        if b.winner_beats_baseline_by is not None:
            print(f"  winner beats {b.baseline} by {b.winner_beats_baseline_by:+.3f} AUC")
        for n in b.notes:
            print(f"  ⚠  {n}")

    if res.proposals:
        print(f"\n{'='*66}\nMISSING-LINK PROPOSALS (top 15) — PROPOSED, nothing applied\n{'='*66}")
        for p in res.proposals[:15]:
            print(f"  {p.rank:>3}. {p.score:8.3f}  {p.source[:34]:<36} ⇄  {p.target[:34]}")
    print(f"\nartifacts → {res.out_dir}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nbb_cp_kre", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("scan", "run"):
        p = sub.add_parser(name)
        p.add_argument("--vault", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--max-files", type=int, default=None)
        p.add_argument("--exclude", action="append", default=[])
        p.add_argument("--no-embeds", action="store_true")
        if name == "run":
            p.add_argument("--seeds", type=int, default=5)
            p.add_argument("--test-frac", type=float, default=0.20)
            p.add_argument("--top-k", type=int, default=40)
            p.add_argument("--quick", action="store_true",
                           help="skip the O(n^2)/O(n^3) layout+manifold reps")

    pr = sub.add_parser("report")
    pr.add_argument("--out", required=True)

    a = ap.parse_args(argv)

    if a.cmd == "report":
        d = load_result(a.out)
        if not d:
            print(f"no latest.json in {a.out} — run `run` first")
            return 1
        print(json.dumps(d["graph"], ensure_ascii=False, indent=2))
        return 0

    try:
        res = run_pipeline(
            a.vault, a.out,
            seeds=list(range(a.seeds)) if a.cmd == "run" else None,
            test_frac=getattr(a, "test_frac", 0.20),
            top_k=getattr(a, "top_k", 40),
            max_files=a.max_files,
            extra_excludes=frozenset(a.exclude),
            include_embeds=not a.no_embeds,
            run_competition=(a.cmd == "run"),
            quick=getattr(a, "quick", False),
            progress=_bar,
        )
    except ReadOnlyViolation as exc:
        print(f"\nREAD-ONLY GUARD TRIPPED\n{exc}")
        return 2
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"\n{exc}")
        return 2

    _print_summary(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
