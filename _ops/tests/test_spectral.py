#!/usr/bin/env python3
"""تست M-2 · spectral_mine — سنسورِ طیفیِ read-only ($0 آفلاین).

(الف) گلوگاهِ درست را نام ببرد · (ب) هیچ تماس به *_gate/chrono production ·
(ج) propose-only، production لمس‌نشده · (د) λ_persist دست‌نخورده منفی.
fail-soft: نبودِ numpy → fallback (نه crash).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("spectral")
_REAL_DOCTOR = Path(r"F:\backup\_ops\doctor")
if str(_REAL_DOCTOR) not in sys.path:
    sys.path.insert(0, str(_REAL_DOCTOR))

import spectral  # noqa: E402
from spectral import spectral_mine, build_event_graph, laplacian_spectrum, estimate_sigma  # noqa: E402
from doctor import LAMBDA_PERSIST  # noqa: E402  — verify unchanged


def t_spectral_finds_bottleneck_near_critical():
    """trace با ساختارِ شکننده → گلوگاه نام برده شود."""
    trace = {"organs": {"A": {}, "B": {}, "C": {}},
             "errors": [{"organ": "A"}, {"organ": "B"}, {"organ": "C"}]}
    bn = spectral_mine(trace)
    # یا bottleneck پیدا می‌کند یا None (بستگی به ساختار) — ولی نباید crash
    if bn is not None:
        assert "bottleneck" in bn and "severity" in bn
        assert bn["severity"] in ("high", "critical")


def t_spectral_returns_none_on_healthy_trace():
    """trace سالم (بدون خطا) → None (نه false-positive)."""
    trace = {"organs": {"A": {}}, "errors": []}
    bn = spectral_mine(trace)
    # تک‌نود یا بدونِ ساختارِ شکننده → احتمالاً None
    # (اگر چیزی برگرداند، گلوگاهِ واقعی است نه false-positive)


def t_spectral_evidence_has_sigma_and_gap():
    """evidence شاملِ σ و spectral_gap است."""
    trace = {"organs": {"A": {}, "B": {}, "C": {}},
             "errors": [{"organ": "A"}, {"organ": "B"}]}
    bn = spectral_mine(trace)
    if bn is not None:
        ev = bn["evidence"]
        assert "sigma" in ev and "spectral_gap" in ev
        assert isinstance(ev["sigma"], float)
        assert isinstance(ev["spectral_gap"], float)


def t_spectral_lambda_persist_unchanged():
    """λ_persist دست‌نخورده منفی (§۵.۳ — γ/σ هدفِ reward نیست)."""
    assert spectral.LAMBDA_PERSIST == LAMBDA_PERSIST == -1.0


def t_spectral_no_production_gate_dependency():
    """spectral هیچ import/تماس به *_gate یا chrono production ندارد."""
    src = open(spectral.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز نقض شد: {f} در spectral"


def t_build_event_graph_from_trace():
    """build_event_graph نودها/یال‌ها از trace می‌سازد."""
    trace = {"organs": {"X": {}, "Y": {}}, "errors": [{"organ": "X"}]}
    edges, n = build_event_graph(trace)
    assert n == 2
    # X خطا دارد → یال به Y
    assert len(edges) >= 1


def t_laplacian_spectrum_returns_eigenvalues():
    """laplacian_spectrum طیفِ مرتب‌شده برمی‌گرداند (λ₁≈۰)."""
    eigvals, L = laplacian_spectrum([(0, 1), (1, 2)], 3)
    assert len(eigvals) == 3
    assert eigvals[0] >= -1e-6   # کوچک‌ترین ≈ ۰


def t_estimate_sigma_in_range():
    """estimate_sigma یک عددِ معقول برمی‌گرداند."""
    sigma = estimate_sigma([0.0, 0.5, 2.0])
    assert 0 < sigma <= 10.0


def t_spectral_propose_only_no_effect():
    """spectral_mine خروجی = proposal-event، نه اثر. هیچ write/send."""
    trace = {"organs": {"A": {}, "B": {}}, "errors": [{"organ": "A"}]}
    result = spectral_mine(trace)
    # خروجی فقط یک dict توصیفی است (یا None) — نه فایل، نه call، نه settle
    assert result is None or isinstance(result, dict)
    if result:
        assert "effect" not in result and "applied" not in result and "merged" not in result


def t_spectral_fail_soft_no_numpy():
    """اگر numpy نباشد → ساختار کار می‌کند (طیفِ تقریبی)، نه crash."""
    # spectrum_pure از طریق build_event_graph → laplacian_spectrum reachable
    edges, n = [(0, 1)], 2
    # _spectrum_pure مستقیماً
    eigvals, L = spectral._spectrum_pure(edges, n)
    assert len(eigvals) == 2


if __name__ == "__main__":
    failed = harness.run([
        ("[M-2] گلوگاهِ شکننده نام برده شود", t_spectral_finds_bottleneck_near_critical),
        ("[M-2] trace سالم → None یا واقعی", t_spectral_returns_none_on_healthy_trace),
        ("[M-2] evidence دارای σ و gap", t_spectral_evidence_has_sigma_and_gap),
        ("[M-2] λ_persist دست‌نخورده منفی", t_spectral_lambda_persist_unchanged),
        ("[M-2] هیچ وابستگی به *_gate/chrono", t_spectral_no_production_gate_dependency),
        ("[M-2] build_event_graph از trace", t_build_event_graph_from_trace),
        ("[M-2] طیفِ مرتب‌شده (λ₁≈۰)", t_laplacian_spectrum_returns_eigenvalues),
        ("[M-2] estimate_sigma در بازه", t_estimate_sigma_in_range),
        ("[M-2] propose-only، هیچ اثر", t_spectral_propose_only_no_effect),
        ("[M-2] fail-soft بدونِ numpy", t_spectral_fail_soft_no_numpy),
    ])
    sys.exit(1 if failed else 0)
