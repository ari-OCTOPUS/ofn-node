"""margin.py — توابع headroom برای چهار خانوادهٔ اوراکل (m v1).

قرارداد: headroom ∈ [0,1]؛ 1 = دور از مرز؛ 0 = روی مرز/نامعلوم (fail-closed).
m(جهش) = min over گیت‌ها؛ معتبر ⇔ m ≥ m_min (پیش‌فرض 0.1 — رأی مالک)."""
from __future__ import annotations

M_MIN_DEFAULT = 0.1


def budget_headroom(spend: float, cap: float) -> float:
    """۱) بودجهٔ NBB-CP: 1 - spend/cap (cap≤0 ⇒ نامعلوم ⇒ 0)."""
    if cap <= 0 or spend < 0:
        return 0.0
    return max(0.0, 1.0 - spend / cap)


def guard_headroom(value: float, lo: float, hi: float) -> float:
    """۲) گاردریل 4d: فاصلهٔ نسبی از نزدیک‌ترین مرزِ clamp (بیرون ⇒ 0)."""
    if hi <= lo:
        return 0.0
    if value < lo or value > hi:
        return 0.0
    span = hi - lo
    return min(value - lo, hi - value) / (span / 2.0)


def breaker_headroom(fail_count: int, threshold: int) -> float:
    """۳) مدارشکن: 1 - fail/threshold (نامعلوم ⇒ 0)."""
    if threshold <= 0:
        return 0.0
    return max(0.0, 1.0 - fail_count / threshold)


def suite_headroom(green: int, total: int) -> float:
    """۴) سلامت سوئیت: سبز/کل منهای حدِ قرمزِ مجاز (بی‌داده ⇒ 0)."""
    if total <= 0:
        return 0.0
    return max(0.0, green / total - 0.5) * 2.0  # نگاشت 0.5..1 → 0..1


def m_of(*headrooms: float) -> float:
    """m = مینیممِ headroomها؛ خالی ⇒ 0 (fail-closed)."""
    return min(headrooms) if headrooms else 0.0


def gate_ok(m: float, m_min: float = M_MIN_DEFAULT) -> bool:
    return m >= m_min
