#!/usr/bin/env python3
"""orchestrator.py — #1: Live Orchestrator. همهٔ قطعات در یک حلقه.
neural → brain → acquisition → hebbian → consolidation → comm → studio.
propose-only، $0، advisory. λ_persist<0."""
from __future__ import annotations
import sys, json, os, time
from dataclasses import dataclass, field, asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_VAULT = _HERE.parent.parent  # F:\backup (Project-F → Projects → backup)
for _p in [str(_HERE / "brain"), str(_HERE / "studio"),
           str(_VAULT / "_ops" / "neural"),
           str(_VAULT / "_ops" / "budget"),   # ۲۰۲۶-۰۸-۰۳: opslib اینجاست
           str(_VAULT / "_ops")]:
    if _p not in sys.path: sys.path.insert(0, _p)

from dual_brain_v3 import DualBrainV3, COMPLIANCE_RULES, ETHICS_RULES, _checks_pass
from content_studio import ContentStudio
from acquisition import AcquisitionBrain, AcquisitionMemory

# ── _ops/neural: وابستگیِ lazy با fallbackِ stdlib (استقلال کامل از vault) ──
# اگر vault کامل mount نباشد، orchestrator با no-opهای هم‌قرارداد بالا می‌آید؛
# advisory-only می‌ماند و tick هیچ قابلیتِ اضافه‌ای «وانمود» نمی‌کند.
try:
    from neural_driver import NeuralDriver
    from hebbian import HebbianAssociator
    from consolidation import ConsolidationCycle
    from sprint import SprintContract, SprintRunner
    from hooks import HookBus
    from circadian import CircadianMap
    NEURAL_AVAILABLE = True
except ImportError:
    NEURAL_AVAILABLE = False

    class NeuralDriver:  # type: ignore[no-redef]
        def evaluate(self, **_kw) -> dict:
            return {"snapshot": {"neural": "unavailable"},
                    "pain": {"level": 0.0}, "reflexes": [], "brain_inputs": {}}

    class HebbianAssociator:  # type: ignore[no-redef]
        def __init__(self, data_path=None):
            self.associations = {}

        def observe(self, _signals) -> None:
            pass

    class ConsolidationCycle:  # type: ignore[no-redef]
        def __init__(self, data_path=None):
            self.cycle_count = 0

        def run(self, _sources) -> None:
            pass

    class SprintContract:  # type: ignore[no-redef]
        def __init__(self, **_kw):
            pass

    class SprintRunner:  # type: ignore[no-redef]
        is_active = False

        def set_hooks(self, _h) -> None:
            pass

        def start(self, _c, start_beat=0) -> None:
            pass

        def tick(self, tokens=0, now_beat=0) -> None:
            pass

        def finish(self, now_beat=0) -> None:
            pass

    class HookBus:  # type: ignore[no-redef]
        def fire(self, _name, _payload=None) -> None:
            pass

    class CircadianMap:  # type: ignore[no-redef]
        pass

# state ارکستر قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = brain/ کنارِ ماژول
# ۲۰۲۶-۰۸-۰۳ fix: lazy resolution — قبلاً module-level constant بود و تست‌ها را به
# ترتیبِ اجرا حساس می‌کرد (PF_BRAIN_DIR باید قبل از import set می‌شد).
def _brain_state_dir() -> Path:
    env = os.environ.get("PF_BRAIN_DIR")
    return Path(env) if env else _HERE / "brain"

LAMBDA_PERSIST = -1.0

# ── مغزِ پیش‌فرض: flag-off = DualBrainV3 (رفتارِ آزموده‌شده)، flag-on = CortexAugmentedBrain
# 2026-07-25 (فاز ۱b): وقتی OCTOPUS_WIRE_PROJECTF_CORTEX=1 است، مغزِ orchestrator
# از CortexAugmentedBrain می‌آید — DualBrainV3 + insight از cortexِ مرکزی (مرزِ #۷).
# importِ cortex_augmented به‌صورتِ lazy تا وابستگیِ circular نباشد و flag-off
# دقیقاً مثلِ قبل بماند.
_CORTEX_FLAG = "OCTOPUS_WIRE_PROJECTF_CORTEX"


def _default_brain():
    """مغزِ پیش‌فرضِ orchestrator. flag-off = DualBrainV3 (رفتارِ آزموده‌شده).
    flag-on = CortexAugmentedBrain (enriched با cortex). هرگز raise نمی‌کند."""
    if os.environ.get(_CORTEX_FLAG, "0") == "1":
        try:
            # cortex_augmented وابسته به brain/ در sys.path است (الان هست).
            from cortex_augmented import CortexAugmentedBrain
            return CortexAugmentedBrain()
        except Exception as _e:  # noqa: BLE001 — fail-soft: برگرد به DualBrainV3
            # در محیطِ زنده لاگ می‌شوند (opslib.alert) ولی در تست بی‌صدا.
            try:
                import opslib  # noqa
                opslib.alert([f"_default_brain: CortexAugmentedBrain در دسترس نیست، "
                              f"fallback به DualBrainV3: {type(_e).__name__}: {_e}"])
            except Exception:  # noqa
                pass
    return DualBrainV3()

# ── compliance از manifest (فیکس بای‌پس 2026-07-20؛ قبلاً همه True هاردکد بود) ──
# قراردادِ ماشین‌خوان. تست‌ها _MANIFEST را swap می‌کنند؛ لودر هر بار از فایل می‌خواند.
_MANIFEST = _HERE / "PROJECT-F-CONTROL-MANIFEST.json"

# نگاشتِ هر قانونِ مغز → لنگرِ متنی‌اش در manifest.hard_rules_locked (پیشوندِ «N:»).
# قانونی که این‌جا نگاشت ندارد = ناشناخته = False (fail-closed).
_RULE_ANCHORS = {
    # compliance
    "faceless": "1:", "feet_only": "1:", "no_explicit": "1:",
    "geo_block_iran": "2:", "inplatform_payment": "3:",
    "over_18": "8:",
    # ethics — لنگر به نزدیک‌ترین قانونِ قفل‌شده (۴=no-ToS، ۵=privacy دوطرفه، ۸=مرز C حاکم)
    "no_dark_pattern": "4:", "no_manipulation": "4:",
    "relationship_80_sales_20": "5:", "no_engagement_optimization": "5:",
    "performer_welfare": "8:", "scope_supreme": "8:",
}


def _load_compliance_checks() -> dict:
    """چک‌های compliance/ethics را از manifest می‌سازد — **fail-closed**.

    هر قانون فقط وقتی True است که: manifest بخواند و parse شود، mutability
    «immutable» اعلام شده باشد، و لنگرِ متنیِ همان قانون در hard_rules_locked
    حاضر باشد. manifest غایب/خراب، ساختار ناآشنا، یا قانونِ بدونِ لنگر → False.
    هیچ مسیرِ خطایی True برنمی‌گرداند."""
    all_rules = list(COMPLIANCE_RULES) + list(ETHICS_RULES)
    failed = {r: False for r in all_rules}
    try:
        raw = json.loads(Path(_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return failed
    if not isinstance(raw, dict):
        return failed
    locked = raw.get("hard_rules_locked")
    mutability = str(raw.get("hard_rules_mutability", ""))
    if not isinstance(locked, list) or not mutability.startswith("immutable"):
        return failed
    prefixes = tuple(str(x).strip()[:2] for x in locked if isinstance(x, str))
    checks = {}
    for rule in all_rules:
        anchor = _RULE_ANCHORS.get(rule)
        checks[rule] = bool(anchor) and anchor in prefixes
    return checks


@dataclass
class TickResult:
    beat: int
    mode: str          # normal | protective | throttled
    pain: float
    snapshot: dict
    brain_inputs: dict | None = None
    thoughts: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    reflexes: list = field(default_factory=list)
    advisory_only: bool = True


class PFOrchestrator:
    """حلقهٔ زندهٔ Project-F. هر tick: snapshot → think → comm.
    protective mode: pain>0.7 → فقط heartbeat."""

    def __init__(self, studio=None, brain=None, acquisition=None,
                 data_dir: str | Path | None = None):
        self.studio = studio or ContentStudio()
        self.brain = brain or _default_brain()
        self.acquisition = acquisition or AcquisitionBrain(
            memory=AcquisitionMemory(data_path=str(_brain_state_dir() / "acq_orch.json")))
        self.neural = NeuralDriver()
        self.hebbian = HebbianAssociator(data_path=str(_brain_state_dir() / "hebb_orch.json"))
        self.consolidation = ConsolidationCycle(data_path=str(_brain_state_dir() / "con_orch.json"))
        self.circadian = CircadianMap()
        self.hooks = HookBus()
        self.sprint_runner = SprintRunner()
        self.sprint_runner.set_hooks(self.hooks)
        self._beat = 0
        self._protective = False
        self._data_dir = Path(data_dir) if data_dir else _brain_state_dir()
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def tick(self, rhythm=None, sensory=None, spectral=None, budget=None,
             post_feedback=None, competitor_data=None,
             visitors=100, subscribers=5, ppv_buyers=1,
             partner_stress=0.3, season="summer") -> TickResult:
        """یک دورِ کامل. همه advisory."""
        self._beat += 1
        self.hooks.fire("pre_sprint", {"beat": self._beat})

        # ۱. Neural snapshot
        neural_result = self.neural.evaluate(
            beat=self._beat, rhythm=rhythm, sensory=sensory,
            spectral=spectral, budget=budget)
        snap = neural_result["snapshot"]
        pain = neural_result["pain"]["level"]
        reflexes = neural_result["reflexes"]
        brain_inputs = neural_result["brain_inputs"]

        # ۲. Protective mode?
        if pain > 0.7:
            self._protective = True
            self.hooks.fire("on_error", {"reason": "protective mode", "pain": pain})
            return TickResult(beat=self._beat, mode="protective", pain=pain,
                              snapshot=snap, reflexes=reflexes)

        # ۳. Throttle check
        throttle = brain_inputs.get("throttle_brain", False)

        # ۴. Acquisition feedback (اگر داده هست)
        if post_feedback:
            for fb in post_feedback:
                self.acquisition.feedback_loop(**fb)

        # ۵. Compliance gate (fail-closed — فیکس بای‌پس 2026-07-20).
        # چک‌ها از manifest واقعی می‌آیند؛ اگر همه پاس نشوند tick بلاک می‌شود و
        # هیچ advisory/پیامی تولید نمی‌شود (حتی «پیشنهاد» هم بیرون نمی‌رود).
        checks = _load_compliance_checks()
        if not _checks_pass(checks):
            self.hooks.fire("on_error", {"reason": "blocked_compliance",
                                         "failed": [r for r, v in checks.items() if not v]})
            return TickResult(beat=self._beat, mode="blocked_compliance", pain=pain,
                              snapshot=snap, brain_inputs=brain_inputs,
                              reflexes=reflexes)

        # ۶. Thinking (اگر throttle نیست)
        thoughts_data = []
        messages_data = []
        if not throttle:
            result = self.brain.think_and_communicate(
                checks=checks, competitor_data=competitor_data,
                visitors=visitors, subscribers=subscribers,
                ppv_buyers=ppv_buyers, partner_stress=partner_stress,
                season=season, drafts_count=self.studio.draft_count)
            thoughts_data = result.get("thoughts", [])
            messages_data = result.get("messages", [])

        # ۶. Hebbian: co-occurring signals
        signals = []
        if rhythm and rhythm.get("mode_color") == "GREEN":
            signals.append("green_mode")
        if spectral and spectral.get("sigma", 0) < 0.8:
            signals.append("stable_sigma")
        if brain_inputs.get("data_confidence", 0) > 0.3:
            signals.append("good_data")
        season_tag = season
        signals.append(season_tag)
        if signals:
            self.hebbian.observe(signals)

        # ۷. Consolidation (هر ۱۰ tick)
        if self._beat % 10 == 0:
            sources = {}
            perf = self.acquisition.memory.tag_performance()
            if perf:
                sources["acquisition"] = perf
            learned = self.brain.thinking._historical if hasattr(self.brain.thinking, '_historical') else []
            if learned:
                sources["doctor_archive"] = [{"outcome": d.get("outcome")} for d in learned if d.get("type") == "price"]
            if sources:
                self.consolidation.run(sources)

        # ۸. Sprint management — TINV-5: beat_seq تزریق می‌شود (نه wall-clock)
        if not self.sprint_runner.is_active:
            self.sprint_runner.start(SprintContract(
                sprint_id=f"tick-{self._beat}", scope="pf-cycle",
                budget_beats=1, budget_tokens=50), start_beat=self._beat)
        self.sprint_runner.tick(tokens=0, now_beat=self._beat)
        self.sprint_runner.finish(now_beat=self._beat)

        self.hooks.fire("post_sprint", {"beat": self._beat, "completed": True})

        # 2026-07-25 (فاز ۱a): انتشارِ یکپارچه به ستونِ فقرات. flag-off = no-op.
        # یک تپِ بی‌نام به bus داخلی + bridge به ارگانیسم (summaryِ content-free).
        # هرگز raise نمی‌کند (fail-soft) — tick نباید بمیرد. spine به‌صورتِ package
        # import می‌شود (relative-importها دارد)، پس ریشهٔ پروژه باید در sys.path باشد.
        try:
            if str(_HERE) not in sys.path:
                sys.path.insert(0, str(_HERE))
            from pf_os import spine as _spine
            _spine.emit("orchestrator.tick.done", "orchestrator",
                        f"tick {self._beat} completed (mode={ 'throttled' if throttle else 'normal' })",
                        bridge_text=f"tick {self._beat} done")
        except Exception:  # noqa: BLE001 — spine هرگز tick را نمی‌کشد
            pass

        mode = "throttled" if throttle else "normal"
        return TickResult(beat=self._beat, mode=mode, pain=pain,
                          snapshot=snap, brain_inputs=brain_inputs,
                          thoughts=thoughts_data, messages=messages_data,
                          reflexes=reflexes)

    @property
    def beat(self) -> int:
        return self._beat

    @property
    def is_protective(self) -> bool:
        return self._protective

    def status(self) -> dict:
        return {"beat": self._beat, "protective": self._protective,
                "drafts": self.studio.draft_count,
                "acquisition_confidence": self.acquisition.memory.learning_confidence(),
                "hebbian_assocs": len(self.hebbian.associations),
                "consolidation_cycles": self.consolidation.cycle_count,
                "lambda_persist": LAMBDA_PERSIST,
                "neural_available": NEURAL_AVAILABLE,
                "compliance_ok": _checks_pass(_load_compliance_checks())}
