"""Time-boxed, self-chaining research loop.

Each iteration:  research(prompt) -> conclude -> write a report -> emit the NEXT
prompt, and feed that prompt into the next iteration. The loop runs on the
WALL CLOCK (the laptop's time) until `--minutes` have elapsed (default 60), then
stops and writes a SUMMARY.

Safety (this loop can spend money, so it is fenced):
  * every LLM call's cost is metered to the ledger;
  * the loop STOPS early if cumulative cost would exceed --max-cost;
  * ONE Guardian is created before the loop and re-checked each iteration (so it
    can actually HALT on genome tampering mid-run);
  * a failing iteration (API/parse error) is logged and the loop keeps going;
  * nothing is applied -- output is report files + ledger notes only.

With no ANTHROPIC_API_KEY it runs an offline stub, so the same code path works
for a 20-second dry run or a real hour.

Usage:
  python research_loop.py "your seed question" --minutes 60 --max-cost 1.0
  ANTHROPIC_API_KEY=sk-...  python research_loop.py "..." --minutes 60
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for sub in ("ledger", "common", "agents"):
    sys.path.insert(0, str(ROOT / sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402
from guardian import Guardian       # noqa: E402

RESEARCH_SYSTEM = (
    "You are a rigorous research agent. Given a QUESTION, reason carefully, stay "
    "honest about uncertainty, and return ONLY a JSON object with keys: research "
    "(3-6 key findings as one string), conclusion (1-3 sentences), report_md (a "
    "short markdown report), next_prompt (the single most valuable follow-up "
    "question to investigate next). No prose outside the JSON."
)

_ANGLES = ["the biggest open risk", "the cheapest safe approach", "what to measure",
           "the most likely failure mode", "a one-week experiment to test it",
           "what a skeptical expert would object to"]


def _extract_json(text: str) -> dict:
    s = text.strip()
    i, j = s.find("{"), s.rfind("}")
    if i == -1 or j == -1:
        raise ValueError("no JSON in reply")
    return json.loads(s[i:j + 1])


def _stub(prompt: str, n: int) -> dict:
    angle = _ANGLES[(n - 1) % len(_ANGLES)]
    return {
        "research": f"(offline stub) iteration {n} examining {angle}.",
        "conclusion": f"(stub) provisional take on {angle}; connect a key for real analysis.",
        "report_md": f"### Iteration {n} — {angle}\n\n(offline stub output)",
        "next_prompt": f"Investigate {angle} next. (follow-up {n + 1})",
    }


def _format_report(n: int, ts: str, prompt: str, d: dict) -> str:
    return (f"# Research report — iteration {n}\n_{ts}_\n\n"
            f"## Question\n{prompt}\n\n"
            f"## Research\n{d.get('research', '')}\n\n"
            f"## Conclusion\n{d.get('conclusion', '')}\n\n"
            f"## Report\n{d.get('report_md', '')}\n\n"
            f"## Next prompt\n{d.get('next_prompt', '')}\n")


def research(prompt: str, n: int, client) -> tuple[dict, float]:
    if client is None:
        return _stub(prompt, n), 0.0
    out = client.complete("generate", RESEARCH_SYSTEM,
                          f"QUESTION: {prompt}\nReturn ONLY the JSON.", max_tokens=1200)
    try:
        return _extract_json(out["text"]), out["cost_usd"]
    except Exception:
        d = _stub(prompt, n)
        d["conclusion"] = "(model reply unparseable; kept chain alive)"
        return d, out["cost_usd"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("seed", nargs="?",
                    default="How should a solo, local-first agent vault implement safe "
                            "off-site backup and monthly restore drills?")
    ap.add_argument("--minutes", type=float, default=60.0)
    ap.add_argument("--max-cost", type=float, default=None)
    ap.add_argument("--interval", type=float, default=5.0, help="min seconds between iterations")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    genome = Genome.load(ROOT / "genome")
    ledger = Ledger(ROOT / "ledger" / "ledger.jsonl")
    guard = Guardian(genome, ledger)            # ONE instance -> baseline fixed at start
    max_cost = args.max_cost if args.max_cost is not None else float(genome.budget.get("daily_ops", 1.0))

    client = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        from llm import LLMClient
        client = LLMClient(genome, ledger=ledger)

    out_dir = Path(args.out) if args.out else \
        ROOT / "reports" / f"research-{time.strftime('%Y%m%d-%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    duration = args.minutes * 60.0
    start = time.monotonic()
    ledger.append("NOTE", {"research_loop": "start", "seed": args.seed,
                           "minutes": args.minutes, "max_cost": max_cost,
                           "brain": "real" if client else "stub"}, actor="research")
    print(f"research loop: up to {args.minutes:g} min, cap ${max_cost:g}, "
          f"{'REAL' if client else 'stub'} brain -> {out_dir.name}")

    chain = [args.seed]
    prompt = args.seed
    total_cost = 0.0
    n = 0
    while time.monotonic() - start < duration:
        if guard.tick()["halt"]:
            print("guardian HALT -> stopping"); break
        n += 1
        ts = datetime.now(timezone.utc).isoformat()
        try:
            data, cost = research(prompt, n, client)
        except Exception as exc:                 # never let one bad iteration kill the hour
            ledger.append("NOTE", {"research_error": str(exc)[:200], "iter": n}, actor="research")
            data, cost = _stub(prompt, n), 0.0
            data["conclusion"] = f"(iteration error: {str(exc)[:80]})"
        total_cost += cost
        (out_dir / f"report_{n:02d}.md").write_text(
            _format_report(n, ts, prompt, data), encoding="utf-8")
        nxt = (data.get("next_prompt") or f"Continue: {prompt}").strip()
        ledger.append("NOTE", {"research_iter": n, "cost_usd": round(cost, 6),
                               "report": f"report_{n:02d}.md",
                               "next_prompt": nxt[:120]}, actor="research")
        elapsed = int(time.monotonic() - start)
        print(f"[{n}] {elapsed}s  cost=${total_cost:.4f}  next: {nxt[:56]}")

        if total_cost > max_cost:
            print(f"budget cap ${max_cost:g} reached -> stopping"); break
        chain.append(nxt)
        prompt = nxt
        remaining = duration - (time.monotonic() - start)
        if remaining <= 0:
            break
        time.sleep(min(args.interval, max(0.0, remaining)))

    secs = int(time.monotonic() - start)
    summary = ["# Research loop — summary", "",
               f"- iterations: {n}", f"- elapsed: {secs}s (cap {args.minutes:g} min)",
               f"- total LLM cost: ${total_cost:.4f} (cap ${max_cost:g})",
               f"- brain: {'real model' if client else 'offline stub'}",
               "", "## Prompt chain"]
    summary += [f"{i}. {p}" for i, p in enumerate(chain, 1)]
    (out_dir / "SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")
    ledger.append("NOTE", {"research_loop": "done", "iterations": n,
                           "elapsed_s": secs, "total_cost_usd": round(total_cost, 6)},
                  actor="research")
    print(f"done: {n} iterations in {secs}s, ${total_cost:.4f}. summary -> {out_dir / 'SUMMARY.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
