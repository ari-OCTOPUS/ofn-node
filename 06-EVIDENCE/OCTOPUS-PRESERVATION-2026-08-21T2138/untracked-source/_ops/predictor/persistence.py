"""persistence.py — سایه‌ی S6 (HARDTEST): روان‌ساز نمایی، نه جایگزینی p_base.

مدل ثبت‌شده METAPHOR ماند. این ماژول فقط اندازه‌گیری مسیر پایداری است.
روزهای گذار را جدا گزارش کن وگرنه METAPHORِ بهتر جای قبلی می‌نشیند.
"""
from __future__ import annotations


def brier(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        raise ValueError("empty pairs")
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def exponential_smoother(
    ys: list[float],
    *,
    alpha: float,
    p0: float,
) -> list[float]:
    """p_t از y_{t-1}؛ p0 برای اولین گام. alpha∈[0,1]."""
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be in [0,1]")
    p = float(p0)
    out: list[float] = []
    for y in ys:
        out.append(p)
        p = alpha * float(y) + (1.0 - alpha) * p
    return out


def transition_indices(ys: list[float]) -> list[int]:
    """شاخص‌هایی که y با گام قبل فرق دارد (t≥1)."""
    out = []
    for i in range(1, len(ys)):
        if ys[i] != ys[i - 1]:
            out.append(i)
    return out
