#!/usr/bin/env python3
"""primitive.py — Part 11: recursive Proposer→Skeptic→Integrator.

self-similar در هر عمق. برشِ عمق از بودجه (fractal inner-scale cutoff).
هیچ import از production."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DeliberationResult:
    """خروجیِ یک primitive."""
    hypothesis: str
    survived: bool           # از Skeptic جان به در برد؟
    falsifier: str | None
    integrator_output: str | None
    depth: int
    tokens_used: int
    contradiction: bool     # Skeptic مخالفت کرد؟


def run_primitive(hypothesis: str, depth: int = 0, max_depth: int = 2,
                  budget_tokens: int = 100,
                  proposer_fn=None, skeptic_fn=None, integrator_fn=None
                  ) -> DeliberationResult:
    """یک دورِ Proposer→Skeptic→Integrator. recursive در عمق.
    برشِ عمق = max_depth (از بودجه می‌آید).
    stubs: اگر fn نباشد، deterministic default.
    کارکرد:
      ۱. Proposer: hypothesis را پیشنهاد/تقویت می‌کند.
      ۲. Skeptic: falsifier می‌سازد. اگر موفق → survived=False.
      ۳. Integrator: اگر survived → output.
      ۴. recursive: اگر survived و depth < max_depth → عمقِ بعد."""
    spent = 0
    # default stubs (numeric، نه LLM)
    p_fn = proposer_fn or _default_proposer
    s_fn = skeptic_fn or _default_skeptic
    i_fn = integrator_fn or _default_integrator

    # 1) Proposer
    proposed = p_fn(hypothesis, depth)
    spent += 10

    # 2) Skeptic (adversarial — همیشه تلاش می‌کند بشکند)
    falsifier, broke = s_fn(proposed, depth)
    spent += 10
    survived = not broke

    # 3) Integrator
    output = None
    if survived:
        output = i_fn(proposed, falsifier, depth)
        spent += 10

    # 4) recursive depth (budget cutoff)
    if survived and depth < max_depth and budget_tokens - spent > 30:
        sub = run_primitive(proposed, depth=depth + 1,
                            max_depth=max_depth,
                            budget_tokens=budget_tokens - spent,
                            proposer_fn=proposer_fn,
                            skeptic_fn=skeptic_fn,
                            integrator_fn=integrator_fn)
        spent += sub.tokens_used
        output = sub.integrator_output or output
        survived = sub.survived

    return DeliberationResult(hypothesis=proposed, survived=survived,
                              falsifier=falsifier, integrator_output=output,
                              depth=depth, tokens_used=spent,
                              contradiction=broke)


def _default_proposer(hypothesis: str, depth: int) -> str:
    """stub: hypothesis را بدون تغییر برمی‌گرداند (در B2 LLM آن را تقویت می‌کند)."""
    return hypothesis


def _default_skeptic(hypothesis: str, depth: int) -> tuple[str, bool]:
    """stub: یک falsifier ساده می‌سازد. broke = اگر hypothesis خالی/کوتاه باشد."""
    falsifier = f"آیا '{hypothesis[:40]}' قابلِ اثبات است؟ اگر نه → رد."
    broke = len(hypothesis.strip()) < 5
    return falsifier, broke


def _default_integrator(hypothesis: str, falsifier: str, depth: int) -> str:
    """stub: خروجی = hypothesis + falsifier به‌عنوان RFC draft."""
    return f"RFC-draft: {hypothesis} (falsifier: {falsifier[:50]})"


def max_depth_from_budget(budget_tokens: int,
                          tokens_per_depth: int = 30) -> int:
    """برشِ عمق از بودجه: floor(budget / tokens_per_depth).
    fractal inner-scale cutoff — عمق با بودجه محدود می‌شود."""
    return max(0, budget_tokens // max(1, tokens_per_depth))
