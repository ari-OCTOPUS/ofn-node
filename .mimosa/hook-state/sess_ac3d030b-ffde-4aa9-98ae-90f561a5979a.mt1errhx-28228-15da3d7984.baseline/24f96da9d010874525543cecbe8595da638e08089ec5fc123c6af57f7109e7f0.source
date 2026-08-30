#!/usr/bin/env python3
"""تست M-1 · fusion_sim — پایداری، γ، refractory ($0 آفلاین).

خطوطِ قرمز: ChronoUnit جای pacemaker نگیرد · FusionGate وارد *_gate نشود · γ/σ هدفِ
reward نشود. این sim تحقیقاتی است، جدا از production.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(r"F:\backup\_ops\tests")))

import harness  # noqa: E402
ENV = harness.setup("fusion-sim")
from fusion_sim import (FusionField, FusionGate, ChronoUnit,  # noqa: E402
                        laplacian_matrix, stability_matrix, simulate_fusion_world)


def t_fusionfield_stable_no_explosion():
    """‖φ‖ منفجر نشود (پایداریِ A=−L(G))."""
    # گرافِ مثلث (همبند) → L(G) نیمه‌معین‌مثبت → −L(G) پایدار
    edges = [(0, 1), (1, 2), (0, 2)]
    A = stability_matrix(edges, 3)
    ff = FusionField(A=A, dt=0.01)
    max_norm = 0.0
    for _ in range(200):
        ff.step()
        max_norm = max(max_norm, ff.norm)
    assert max_norm < 1e4, f"φ منفجر شد: norm={max_norm}"


def t_fusionfield_laplacian_is_psd():
    """L(G) نیمه‌معین‌مثبت (eigenvalues ≥ ۰). پلِ کانونی."""
    edges = [(0, 1), (1, 2)]
    L = laplacian_matrix(edges, 3)
    try:
        import numpy as np
        eigvals = sorted(np.linalg.eigvalsh(np.asarray(L, dtype=float)))
        assert all(e >= -1e-9 for e in eigvals), f"L(G) PSD نیست: {eigvals}"
        assert abs(eigvals[0]) < 1e-9   # λ₁ ≈ ۰ برای همبند
    except ImportError:
        pass   # pure-python fallback: diagonal فقط


def t_stability_matrix_is_negative_laplacian():
    """A = −L(G) → پایدار (eigenvalues ≤ ۰)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    A = stability_matrix(edges, 3)
    try:
        import numpy as np
        eigvals = np.linalg.eigvalsh(np.asarray(A, dtype=float))
        assert all(e <= 1e-9 for e in eigvals), f"A پایدار نیست: {eigvals}"
    except ImportError:
        pass


def t_chronounit_gamma_high_stretches_time():
    """γ>1 → زمانِ ذهنی > فیزیکی (claim C1/C3: کش‌دار)."""
    c = ChronoUnit(gamma=2.0)
    assert c.subjective_time(10.0) == 20.0


def t_chronounit_gamma_low_compresses_time():
    """γ<1 → زمانِ ذهنی < فیزیکی (برق‌آسا)."""
    c = ChronoUnit(gamma=0.5)
    assert c.subjective_time(10.0) == 5.0


def t_chronounit_refractory_works():
    """refractory: بعد از fire، فایرِ فوری رد می‌شود."""
    c = ChronoUnit(refractory_ms=100.0)
    c.try_fire(physical_t=1.0, threshold=1.0)   # قطعی fire
    # فوراً بعد (۱ms بعد): باید رد شود چون refractory ۱۰۰ms
    assert c.try_fire(physical_t=1.001, threshold=1.0) is False


def t_fusiongate_prob_in_range():
    """FusionGate.prob ∈ [0,1] و با فاصله کم می‌شود."""
    g = FusionGate(lam0=1.0, alpha=1.0)
    p_near = g.prob(dt=1.0, distance=0.0)
    p_far = g.prob(dt=1.0, distance=5.0)
    assert 0 <= p_near <= 1 and 0 <= p_far <= 1
    assert p_near > p_far   # نزدیک‌تر = احتمالِ بیشتر


def t_simulate_fusion_world_returns_fields():
    """simulate_fusion_world تمامِ فیلدها را برمی‌گرداند."""
    result = simulate_fusion_world(edges=[(0, 1), (1, 2)], n_nodes=3, n_steps=50)
    for key in ("physical_time", "subjective_time", "fires", "final_norm",
                "max_norm", "stable", "gamma", "n_nodes"):
        assert key in result, f"missing {key}"


def t_simulate_stable_graph():
    """گرافِ همبندِ پایدار → stable=True (منفجر نشود)."""
    result = simulate_fusion_world(edges=[(0, 1), (1, 2), (2, 0)],
                                   n_nodes=3, n_steps=100, dt=0.01)
    assert result["stable"] is True, f"باید پایدار باشد: max_norm={result['max_norm']}"


def t_no_production_gate_dependency():
    """fusion_sim هیچ وابستگی به *_gate یا chrono production ندارد."""
    import fusion_sim
    src = open(fusion_sim.__file__, encoding="utf-8").read()
    # نباید import کند از *_gate یا chrono
    assert "import chrono" not in src and "from chrono" not in src
    assert "organ_gate" not in src and "money_gate" not in src
    assert "capability_gate" not in src and "budget_gate" not in src


if __name__ == "__main__":
    failed = harness.run([
        ("[M-1] FusionField پایدار (منفجر نشود)", t_fusionfield_stable_no_explosion),
        ("[M-1] L(G) نیمه‌معین‌مثبت (پلِ کانونی)", t_fusionfield_laplacian_is_psd),
        ("[M-1] A=−L(G) پایدار", t_stability_matrix_is_negative_laplacian),
        ("[M-1] ChronoUnit γ>1 → زمان کش‌دار", t_chronounit_gamma_high_stretches_time),
        ("[M-1] ChronoUnit γ<1 → برق‌آسا", t_chronounit_gamma_low_compresses_time),
        ("[M-1] ChronoUnit refractory کار می‌کند", t_chronounit_refractory_works),
        ("[M-1] FusionGate.prob ∈ [0,1]", t_fusiongate_prob_in_range),
        ("[M-1] simulate_fusion_world فیلدها برمی‌گرداند", t_simulate_fusion_world_returns_fields),
        ("[M-1] گرافِ همبند → stable", t_simulate_stable_graph),
        ("[M-1] هیچ وابستگی به *_gate/chrono production", t_no_production_gate_dependency),
    ])
    sys.exit(1 if failed else 0)
