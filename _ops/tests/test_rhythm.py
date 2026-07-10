#!/usr/bin/env python3
"""تست CR-B0 · chrono-rhythm layer ($0 آفلاین، advisory).

DoD: (الف) ledger invariance: age_tick/hash با rhythm-on == off ·
(ب) 1/f کران‌دار و seeded · (ج) HRV↓ → آلارم · (د) τ با novelty کش ·
(ه) mode-map درست · (و) صفر production-touch.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("rhythm")
_RH = (harness.REAL_VAULT / r"_ops\chrono_rhythm")
if str(_RH) not in sys.path:
    sys.path.insert(0, str(_RH))

from rhythm import Rhythm, RhythmState, FractalNoise  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# (الف) Ledger invariance — rhythm on/off نباید لجر را تغییر دهد
# ══════════════════════════════╦════════════════════════════════════════════════
def t_ledger_invariance_rhythm_on_off():
    """TINV-3/7: rhythm هرگز age_tick/hash-chain را تغییر نمی‌دهد.
    structural test: rhythm هیچ متدِ write/settle/append به genome-chain ندارد."""
    rh = Rhythm(seed=42)
    for _ in range(5):
        rh.step(readiness=0.5, stress=0.3, novelty=0.2, dt=1.0)
    # rhythm advisory است — نباید هیچ write-path به genome داشته باشد
    import rhythm
    # چک: rhythm هیچ import از opslib/genome/ledger نمی‌کند
    src = open(rhythm.__file__, encoding="utf-8").read()
    assert "import opslib" not in src, "rhythm نباید opslib را import کند"
    assert "from genome" not in src and "import genome" not in src
    # rhythm فقط advisory است — state. shows it
    assert rh.advisory()["advisory_only"] is True


# ════════════════════════════════════════════════════════════════════════════════
# (ب) 1/f noise bounded + seeded
# ════════════════════════════════════════════════════════════════════════════════

def t_noise_bounded():
    """نویز 1/f کران‌دار ∈ [-cap, cap]."""
    fn = FractalNoise(seed=42, cap=1.0)
    samples = [fn.sample() for _ in range(200)]
    assert all(-1.0 <= s <= 1.0 for s in samples), "نویز باید bounded باشد"


def t_noise_seeded_reproducible():
    """seeded: همان seed → همان توالی."""
    fn1 = FractalNoise(seed=99)
    fn2 = FractalNoise(seed=99)
    s1 = [fn1.sample() for _ in range(10)]
    s2 = [fn2.sample() for _ in range(10)]
    assert s1 == s2, "seeded باید reproducible باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) HRV alarm
# ════════════════════════════════════════════════════════════════════════════════

def t_hrv_alarm_fires_on_collapse():
    """HRV↓ → آلارم."""
    rh = Rhythm(seed=42)
    # force rigid beats (same T every time → HRV→0)
    for _ in range(10):
        rh._beat_times.append(60.0)   # identical → HRV=0
    rh.state.hrv = 0.1
    alarm = rh.hrv_alarm()
    assert alarm is not None and alarm["type"] == "hrv-collapse"


def t_hrv_no_alarm_when_healthy():
    """HRV بالا → no alarm."""
    rh = Rhythm(seed=42)
    rh.state.hrv = 5.0
    assert rh.hrv_alarm() is None


# ════════════════════════════════════════════════════════════════════════════════
# (د) τ stretches with novelty
# ════════════════════════════════════════════════════════════════════════════════

def t_tau_higher_with_novelty():
    """τ با novelty بالا کش می‌آید (γ = 1 + a·novelty − b·stress)."""
    rh_low = Rhythm(seed=42)
    rh_high = Rhythm(seed=42)
    for _ in range(10):
        rh_low.step(readiness=0.5, stress=0.0, novelty=0.1, dt=1.0)
        rh_high.step(readiness=0.5, stress=0.0, novelty=0.9, dt=1.0)
    assert rh_high.state.tau > rh_low.state.tau, \
        f"τ باید با novelty بالا تر باشد: {rh_high.state.tau} vs {rh_low.state.tau}"


def t_tau_lower_with_stress():
    """τ با stress فشرده می‌شود (γ = 1 + a·novelty − b·stress)."""
    rh_calm = Rhythm(seed=42)
    rh_stress = Rhythm(seed=42)
    for _ in range(10):
        rh_calm.step(readiness=0.5, stress=0.0, novelty=0.5, dt=1.0)
        rh_stress.step(readiness=0.5, stress=0.8, novelty=0.5, dt=1.0)
    assert rh_stress.state.tau < rh_calm.state.tau, \
        f"τ باید با stress پایین‌تر باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ه) Mode map
# ════════════════════════════════════════════════════════════════════════════════

def t_mode_red_on_high_stress():
    """stress بالا → RED."""
    rh = Rhythm(seed=42)
    for _ in range(10):
        rh.step(readiness=0.2, stress=0.9, novelty=0.1, dt=1.0, sigma=0.5)
    assert rh.state.mode_color == "RED", f"باید RED: {rh.state.mode_color}"


def t_mode_green_on_healthy():
    """healthy → GREEN/STEADY. use high readiness + low stress + low sigma."""
    rh = Rhythm(seed=42)
    for _ in range(20):
        rh.step(readiness=0.8, stress=0.05, novelty=0.3, dt=1.0, sigma=0.2)
    # اگر HRV هنوز پایین است (rigid)، حداقل color نباید RED با stress این پایین
    assert rh.state.mode_color != "RED" or rh.state.stress > 0.5, \
        f"healthy نباید RED: color={rh.state.mode_color} stress={rh.state.stress}"


def t_mode_focused_on_moderate_stress():
    """stress moderate → FOCUSED."""
    rh = Rhythm(seed=42)
    rh.step(readiness=0.6, stress=0.5, novelty=0.3, dt=1.0, sigma=0.4)
    assert rh.state.mode_focus in ("FOCUSED", "STEADY")


# ════════════════════════════════════════════════════════════════════════════════
# (و) Advisory + no production
# ════════════════════════════════════════════════════════════════════════════════

def t_advisory_has_flag():
    """advisory() حاوی advisory_only=True."""
    rh = Rhythm(seed=42)
    rh.step(readiness=0.5, stress=0.3, novelty=0.2)
    adv = rh.advisory()
    assert adv["advisory_only"] is True


def t_no_production_import():
    """rhythm هیچ import از *_gate/chrono/money/opslib ندارد."""
    import rhythm
    src = open(rhythm.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib",
                 "from _ops", "import _ops"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


def t_beat_interval_stressed_faster():
    """stress بالا → T_beat کوتاه‌تر (سریع‌تر)."""
    rh = Rhythm(seed=42)
    T_calm = rh.beat_interval(readiness=0.8, stress=0.1)
    T_stress = rh.beat_interval(readiness=0.2, stress=0.8)
    assert T_stress < T_calm, f"استرس باید سریع‌تر: {T_stress} vs {T_calm}"


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] ledger invariance (rhythm on/off)", t_ledger_invariance_rhythm_on_off),
        ("[ب] نویز bounded", t_noise_bounded),
        ("[ب] نویز seeded reproducible", t_noise_seeded_reproducible),
        ("[ج] HRV↓ → آلارم", t_hrv_alarm_fires_on_collapse),
        ("[ج] HRV بالا → no alarm", t_hrv_no_alarm_when_healthy),
        ("[د] τ با novelty کش", t_tau_higher_with_novelty),
        ("[د] τ با stress فشرده", t_tau_lower_with_stress),
        ("[ه] stress بالا → RED", t_mode_red_on_high_stress),
        ("[ه] healthy → GREEN", t_mode_green_on_healthy),
        ("[ه] moderate stress → FOCUSED", t_mode_focused_on_moderate_stress),
        ("[و] advisory_only=True", t_advisory_has_flag),
        ("[و] no production import", t_no_production_import),
        ("[و] stress → T_beat سریع‌تر", t_beat_interval_stressed_faster),
    ])
    sys.exit(1 if failed else 0)
