#!/usr/bin/env python3
"""تست Neural Integration v2 — ۸ ماژول ($0 آفلاین)."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("neural")
_NEURAL = (harness.SELF_OPS / "neural")
if str(_NEURAL) not in sys.path:
    sys.path.insert(0, str(_NEURAL))

from signal_hub import SignalHub, NeuralSnapshot  # noqa: E402
from reflex import ReflexArc, ReflexAction  # noqa: E402
from circadian import CircadianMap  # noqa: E402
from consolidation import ConsolidationCycle, ConsolidatedInsight, _verify_source  # noqa: E402
from nociceptor import Nociceptor, PainSignal  # noqa: E402
from hebbian import HebbianAssociator, Association  # noqa: E402
from sprint import SprintContract, SprintRunner, SprintResult  # noqa: E402
from hooks import HookBus, VALID_HOOKS  # noqa: E402


# NI-1 SignalHub
def t_signal_hub_snapshot_fields():
    snap = SignalHub().collect(beat=1, rhythm={"mode": "GREEN"},
        sensory={"afferent_ratio": 0.5}, spectral={"sigma": 0.3},
        budget={"pct": 0.1}, pain_level=0.1)
    assert snap.advisory_only is True
    assert "rhythm" in snap.to_dict() and "pain_level" in snap.to_dict()

def t_signal_hub_history():
    hub = SignalHub()
    hub.collect(beat=1); hub.collect(beat=2)
    assert len(hub.history) == 2 and hub.latest.beat == 2

# NI-2 ReflexArc
def t_reflex_sigma_throttle():
    arc = ReflexArc()
    actions = arc.evaluate({"spectral": {"sigma": 1.2}})
    assert any(a.name == "sigma-throttle" and a.triggered for a in actions)

def t_reflex_budget_slow():
    actions = ReflexArc().evaluate({"budget": {"pct": 0.9}})
    assert any(a.name == "budget-slow" for a in actions)

def t_reflex_freeze_pause():
    actions = ReflexArc().evaluate({"rhythm": {"mode_color": "RED"}})
    assert any(a.name == "red-pause" for a in actions)

def t_reflex_no_effect():
    actions = ReflexArc().evaluate({"spectral": {"sigma": 1.5}})
    assert all(not a.is_effect for a in actions)

def t_reflex_all_clear():
    actions = ReflexArc().evaluate({})
    assert actions[0].name == "all-clear" and not actions[0].triggered

# NI-3 Circadian
def t_circadian_peak():
    cm = CircadianMap()
    assert cm.phase(10) == "peak"  # reddit 9-12
    assert cm.readiness(10) == 1.0

def t_circadian_maintenance():
    cm = CircadianMap()
    assert cm.phase(3) == "maintenance"
    assert cm.readiness(3) == 0.3

def t_circadian_best_platform():
    cm = CircadianMap()
    assert cm.best_platform(10) == "reddit"
    assert cm.best_platform(19) == "x"

# NI-4 Consolidation
def t_consolidation_verified_only():
    cyc = ConsolidationCycle(data_path=ENV["ops"] / "con1.json")
    result = cyc.run({
        "acquisition": {"tag-a": 50, "tag-b": 10},
        "doctor_archive": [{"outcome": "approved"}, {"outcome": "rejected"}],
        "school_awareness": {"mean_awareness": 0.3},
        "calibration": [{"verdict": "approved"}],
        "unverified_source": {"junk": "data"},  # → discard
    })
    assert "unverified_source" in result.discarded_sources
    assert "acquisition" in result.verified_sources
    assert len(result.insights) > 0

def t_consolidation_discards_self_report():
    ok = _verify_source("acquisition", {"tag": "no numbers here"})
    assert ok is False

def t_consolidation_accepts_real_data():
    ok = _verify_source("acquisition", {"tag-a": 50})
    assert ok is True

def t_consolidation_persists():
    p = ENV["ops"] / "con2.json"
    c1 = ConsolidationCycle(data_path=p)
    c1.run({"acquisition": {"t": 10}})
    c2 = ConsolidationCycle(data_path=p)
    assert c2.cycle_count >= 1

# NI-5 Nociceptor
def t_nociceptor_healthy():
    p = Nociceptor().measure()
    assert p.pain_level < 0.3 and not p.protective_mode

def t_nociceptor_pain_with_freeze():
    p = Nociceptor().measure(freeze_active=True)
    assert p.pain_level > 0.2

def t_nociceptor_protective():
    p = Nociceptor().measure(budget_pct=1.0, freeze_active=True, error_rate=0.8)
    assert p.protective_mode is True

def t_nociceptor_not_reward():
    from nociceptor import Nociceptor as N
    assert N.LAMBDA_PERSIST == -1.0

# NI-6 Hebbian
def t_hebbian_strength_grows():
    h = HebbianAssociator(data_path=ENV["ops"] / "heb1.json")
    for _ in range(5):
        h.observe(["saturday", "asmr"])
    assert h.strength_of("saturday", "asmr") > 0.3

def t_hebbian_decay():
    h = HebbianAssociator(data_path=ENV["ops"] / "heb2.json")
    for _ in range(5):
        h.observe(["a", "b"])
    s1 = h.strength_of("a", "b")
    for _ in range(20):
        h.decay()
    s2 = h.strength_of("a", "b")
    assert s2 < s1

def t_hebbian_persists():
    p = ENV["ops"] / "heb3.json"
    h1 = HebbianAssociator(data_path=p)
    h1.observe(["x", "y"])
    h2 = HebbianAssociator(data_path=p)
    assert h2.strength_of("x", "y") > 0

# NI-7 SprintContract
def t_sprint_completes():
    runner = SprintRunner()
    c = SprintContract(sprint_id="s1", scope="test", budget_beats=5, budget_tokens=100)
    runner.start(c)
    for i in range(3):
        runner.tick(tokens=10, insight=f"insight {i}")
    result = runner.finish()
    assert result.completed is True
    assert len(result.insights) == 3
    assert result.context_cleared is True

def t_sprint_timeout():
    runner = SprintRunner()
    # TINV-5: انقضا بر حسبِ beat_seq، نه wall-clock
    c = SprintContract(sprint_id="s2", scope="timeout test", budget_beats=10,
                        start_beat=100, deadline_beat=101)  # انقضا در beat 101
    runner.start(c)
    cont = runner.tick(now_beat=101)  # به deadline رسیده → False
    assert cont is False

def t_sprint_budget_exhausted():
    runner = SprintRunner()
    c = SprintContract(sprint_id="s3", scope="budget", budget_beats=100, budget_tokens=20)
    runner.start(c)
    runner.tick(tokens=15)
    cont = runner.tick(tokens=10)  # 25 > 20
    assert cont is False

# NI-8 HookBus
def t_hooks_fire():
    bus = HookBus()
    called = []
    bus.register("pre_sprint", lambda d: called.append("pre"))
    bus.register("post_sprint", lambda d: called.append("post"))
    bus.fire("pre_sprint", {"sprint_id": "x"})
    bus.fire("post_sprint", {})
    assert "pre" in called and "post" in called

def t_hooks_fail_soft():
    bus = HookBus()
    def boom(d): raise RuntimeError("hook exploded")
    bus.register("pre_think", boom)
    bus.fire("pre_think")  # نباید crash
    assert bus.has_errors

def t_hooks_invalid_name():
    bus = HookBus()
    bus.register("invalid_hook", lambda d: None)
    assert bus.has_errors

def t_hooks_with_sprint():
    bus = HookBus()
    called = []
    bus.register("pre_sprint", lambda d: called.append("start"))
    bus.register("post_sprint", lambda d: called.append("end"))
    runner = SprintRunner()
    runner.set_hooks(bus)
    runner.start(SprintContract(sprint_id="h1", scope="hook test"))
    runner.tick()
    runner.finish()
    assert "start" in called and "end" in called


if __name__ == "__main__":
    failed = harness.run([
        # NI-1
        ("[NI-1] snapshot fields + advisory", t_signal_hub_snapshot_fields),
        ("[NI-1] history", t_signal_hub_history),
        # NI-2
        ("[NI-2] σ>1 → throttle", t_reflex_sigma_throttle),
        ("[NI-2] budget>80% → slow", t_reflex_budget_slow),
        ("[NI-2] RED → pause", t_reflex_freeze_pause),
        ("[NI-2] no effect", t_reflex_no_effect),
        ("[NI-2] all clear", t_reflex_all_clear),
        # NI-3
        ("[NI-3] peak hours", t_circadian_peak),
        ("[NI-3] maintenance", t_circadian_maintenance),
        ("[NI-3] best platform", t_circadian_best_platform),
        # NI-4
        ("[NI-4] verified only", t_consolidation_verified_only),
        ("[NI-4] discard self-report", t_consolidation_discards_self_report),
        ("[NI-4] accept real data", t_consolidation_accepts_real_data),
        ("[NI-4] persists", t_consolidation_persists),
        # NI-5
        ("[NI-5] healthy", t_nociceptor_healthy),
        ("[NI-5] freeze → pain", t_nociceptor_pain_with_freeze),
        ("[NI-5] protective mode", t_nociceptor_protective),
        ("[NI-5] λ_persist negative", t_nociceptor_not_reward),
        # NI-6
        ("[NI-6] strength grows", t_hebbian_strength_grows),
        ("[NI-6] decay", t_hebbian_decay),
        ("[NI-6] persists", t_hebbian_persists),
        # NI-7
        ("[NI-7] completes", t_sprint_completes),
        ("[NI-7] timeout", t_sprint_timeout),
        ("[NI-7] budget exhausted", t_sprint_budget_exhausted),
        # NI-8
        ("[NI-8] fire pre/post", t_hooks_fire),
        ("[NI-8] fail-soft", t_hooks_fail_soft),
        ("[NI-8] invalid name", t_hooks_invalid_name),
        ("[NI-8] with sprint", t_hooks_with_sprint),
    ])
    sys.exit(1 if failed else 0)
