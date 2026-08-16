#!/usr/bin/env python3
"""test_sog_floor_guards — continuous-A: DARE با |ρ|≥۱ دیگر نمی‌ترکد.

قبل (اندازه‌گیری 2026-08-16): ۵ مسیر ZeroDivisionError
  p_closed(±1, λ=0) · p_iter(se2=0,λ=0) · solve_floors(ρ=1) · e_shadow(ρ=1).
core.model (TCB) همان ترکیدگی را دارد — این تست آن را characterization می‌کند، فیکس نمی‌کند.
نقطهٔ canonical باید بیت‌به‌بیت همان بماند.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402
ENV = harness.setup("sog-floor-guards")  # قبل از import opslib-خورها

sys.path.insert(0, str(_HERE.parent))
from heart import sog_math as sm  # noqa: E402

CANON_P = 0.0032518381359193053
_DEGENERATE = (
    ("p_closed rho=+1 lam=0", lambda: sm.p_closed(1.0, 0.0, 0.01, 0.0025)),
    ("p_closed rho=-1 lam=0", lambda: sm.p_closed(-1.0, 0.0, 0.01, 0.0025)),
    ("p_iter se2=0 lam=0", lambda: sm.p_iter(0.5, 0.0, 0.0, 0.0025, iters=10)),
    ("solve_floors rho=1", lambda: sm.solve_floors(1.0, 0.5, 0.1, 0.05, 0.1)["P"]),
    ("e_shadow rho=1", lambda: sm.e_shadow(sm.solve_floors(1.0, 0.5, 0.1, 0.05, 0.1))),
)


def t_canonical_p_unchanged():
    p = sm.p_closed(0.5, 0.5, 0.01, 0.0025)
    assert math.isfinite(p) and abs(p - CANON_P) < 1e-18, p


def t_five_degenerates_do_not_raise():
    for name, fn in _DEGENERATE:
        try:
            v = fn()
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"{name} هنوز می‌ترکد: {type(e).__name__}: {e}") from e
        assert v != v or (isinstance(v, float) and not math.isfinite(v)), (
            f"{name} باید nan/non-finite باشد، شد {v!r}")


def t_solve_floors_marks_degenerate():
    fl = sm.solve_floors(1.0, 0.5, 0.1, 0.05, 0.1)
    assert fl.get("ok") is False and fl.get("reason") == "degenerate-params", fl


def t_canonical_solve_still_ok():
    fl = sm.solve_floors(**sm.CANONICAL)
    assert fl.get("ok") is True
    assert abs(sm.delta_self(fl) - 0.122520) < 5e-4


def t_tcb_core_still_raises_rho_eq_one_lam_zero():
    """characterization: 4d_system/core داخل TCB است — فیکس = امضای مجدد."""
    root = _HERE.parent.parent
    sys.path.insert(0, str(root / "4d_system"))
    from core.model import P_closed  # noqa: WPS433
    try:
        P_closed(1.0, 0.0, 0.01, 0.0025)
    except ZeroDivisionError:
        return
    raise AssertionError("TCB core الان گارد دارد — این characterization را به‌روز کن")


if __name__ == "__main__":
    failed = harness.run([
        ("canonical P بیت‌پایدار", t_canonical_p_unchanged),
        ("۵ منحط بدون استثنا", t_five_degenerates_do_not_raise),
        ("solve_floors ok=False روی ρ=1", t_solve_floors_marks_degenerate),
        ("canonical هنوز ok", t_canonical_solve_still_ok),
        ("TCB core هنوز می‌ترکد (رأی)", t_tcb_core_still_raises_rho_eq_one_lam_zero),
    ])
    sys.exit(1 if failed else 0)
