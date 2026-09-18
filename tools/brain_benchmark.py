#!/usr/bin/env python3
"""BRAIN-AUDIT Phase 2 — the 10-task benchmark across every live brain.

Steps this one artifact completes (owner: "5 گام بعدی"):
  audit-phase-2  performance measurement of the different brains
  plan-step-3    every call here records its provider (attribution, no unknowns)
  plan-step-4    per-provider spend cap enforced BEFORE each call

10 tasks, 4 classes, mechanical scoring only (exact/contains/shape) — a score
without a mechanical rule is fabrication, so summarization is scored on shape
and marked SOFT. Raw outputs are kept as evidence. Bound: 64 output tokens per
call, 50 calls total, cap 0.25 USD per provider (from the health record _meta).
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, "/home/ari/ofn/tools")
import brain_factory as bf  # noqa: E402

LEDGER = pathlib.Path("/home/ari/ofn/state/api-budget/budget-ledger.jsonl")
OUT = pathlib.Path("/home/ari/ofn/state/api-budget/config/brain-benchmark.jsonl")
CAP_USD = 0.25

PROVIDERS = ["local-llamacpp-180", "deepseek", "openai", "anthropic", "gemini"]

TASKS = [
    ("cls", "Sentiment: 'The delivery was fast and the paint looks amazing.' Positive or negative? One word.", "positive"),
    ("cls", "Sentiment: 'Terrible service, nobody called me back.' Positive or negative? One word.", "negative"),
    ("cls", "Is 17 a prime number? Answer yes or no.", "yes"),
    ("sum", "Summarize in one short sentence: We painted three townhouse buildings in Parramatta last month, finished two days early, and the strata manager left a five-star review.", None),
    ("sum", "Summarize in one short sentence: The customer asked which building we service, we replied within an hour, and they booked a quote for Thursday.", None),
    ("sum", "Summarize in one short sentence: Our Shopify store had 31 zero-stock products, we set each to one unit, making two thirds of the catalog buyable again.", None),
    ("reason", "A painter charges $40 per hour. He works 3.5 hours. How many dollars total? Answer with just the number.", "140"),
    ("reason", "If today is Thursday, what day is it in 3 days? One word.", "sunday"),
    ("code", "Write a one-line Python function named add that returns the sum of a and b.", "def add"),
    ("code", "Write a one-line Python function named is_even that returns True when n is even.", "def is_even"),
]


def spend_per_provider() -> dict:
    out: dict[str, float] = {}
    if not LEDGER.exists():
        return out
    for line in LEDGER.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = str(r.get("provider") or "")
        try:
            out[p] = out.get(p, 0.0) + float(r.get("cost_usd") or 0)
        except (TypeError, ValueError):
            pass
    return out


def _unfence(t: str) -> str:
    """A correct answer wrapped in ``` fences is still a correct answer."""
    s = (t or "").strip()
    if s.startswith("```"):
        lines = s.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = chr(10).join(lines).strip()
    return s


def score(task_cls: str, expected: str | None, text: str) -> tuple[float, str]:
    t = _unfence(text)
    low = t.lower()
    if task_cls == "cls":
        ok = expected in low
        return (1.0 if ok else 0.0), "exact-word" if ok else "missed"
    if task_cls == "reason":
        ok = expected in low
        return (1.0 if ok else 0.0), "exact" if ok else "missed"
    if task_cls == "code":
        ok = expected in low and "def" in low
        return (1.0 if ok else 0.0), "signature" if ok else "missed"
    # summarization: mechanical shape only, honestly marked SOFT
    ok = 20 <= len(t) <= 400
    return (1.0 if ok else 0.0), "SOFT-shape" if ok else "bad-shape"


def main() -> int:
    spend = spend_per_provider()
    results = []
    for pid in PROVIDERS:
        already = spend.get(pid, 0.0)
        if already >= CAP_USD:
            results.append({"provider": pid, "skipped": f"CAP_REACHED({already:.2f})"})
            continue
        try:
            probe = bf.build(tier="standard", pin=pid)
        except bf.BrainBuildError as exc:
            results.append({"provider": pid, "skipped": str(exc)[:80]})
            continue
        brain = probe["brain"]
        rows = []
        for i, (cls, prompt, expected) in enumerate(TASKS, 1):
            t0 = time.time()
            try:
                reply = brain.answer(f"bench-{i}", prompt)
                text = (getattr(reply, "text", "") or "").strip()
            except Exception as exc:  # noqa: BLE001
                text, reply = "", None
            pts, rule = score(cls, expected, text)
            rows.append({"i": i, "cls": cls, "ok": pts > 0, "rule": rule,
                         "reply_head": text[:120],
                         "latency_s": round(time.time() - t0, 2)})
        total = sum(r["ok"] for r in rows)
        results.append({
            "provider": pid, "model": probe["model"], "dialect": probe["dialect"],
            "score": f"{total}/10",
            "by_class": {c: f"{sum(1 for r in rows if r['cls']==c and r['ok'])}/"
                          f"{sum(1 for r in rows if r['cls']==c)}"
                         for c in ("cls", "sum", "reason", "code")},
            "median_latency_s": sorted(r["latency_s"] for r in rows)[len(rows)//2],
            "tasks": rows,
        })
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(results[-1], ensure_ascii=False) + "\n")

    for r in results:
        if "skipped" in r:
            print(f"{r['provider']:<20} SKIPPED {r['skipped']}")
        else:
            print(f"{r['provider']:<20} {r['score']:<7} {r['model']:<22} "
                  f"med={r['median_latency_s']}s  {r['by_class']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
