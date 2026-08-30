"""EPI_METRIC contract — schema v1 for the off-loop epistemics layer.

SCAFFOLD (greenfield). Off-loop, read-only, advisory. Emitted to a SEPARATE
stream (see emit.py), never to the money ledger. Not wired into the organism
loop — that is Phase 5, behind OCTOPUS_WIRE_EPISTEMICS, only after Phase 1-3.

Guardrails baked in:
- Every metric carries `confidence` and `sample_size`.
- `authoritative=False` until sample_size >= MIN_SAMPLES[name] (small-sample
  estimators like MI/perplexity are high-variance and misleading otherwise).
- `self_reference` (SOG) is a FUNCTIONAL verdict only — never a transcendence
  or phenomenal-consciousness claim.
- `method` (S=>L) is CONDITIONAL only — never an unconditional/metaphysical claim.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = 1
RECORD_TYPE = "EPI_METRIC"

# access-only معرفتی (بک‌لاگِ ۲۰۲۷ #۳، رأی مالک): هر متریک می‌تواند برچسبِ سه‌گانهٔ
# تریاژ بگیرد (Block 1995 / C2PA / Butlin 2023). گاردِ سخت: هیچ رشتهٔ معرفتی هرگز
# ادعای phenomenal/qualia/sentience نمی‌کند — فقط access-consciousness.
EPISTEMIC_LABELS = frozenset({"fact", "emerging", "hype"})
_PHENOMENAL_BANNED = ("phenomenal", "qualia", "sentient", "sentience",
                      "conscious experience", "subjective experience", "feels")
# ذکرِ سلبی (disclaimer) مجاز است: لایهٔ epistemics عمداً خودش را با «not a phenomenal
# claim / never …» سلب‌مسئولیت می‌کند. فقط ادعای *مثبت* را می‌بندیم.
_NEGATIONS = ("not", "never", "no ", "n't", "non-", "without", "excluded", "disclaim",
              "هرگز", "نه ", "بدون", "غیرِ", "غیر ")


def assert_access_only(*texts: str) -> None:
    """اگر رشتهٔ معرفتی ادعای *مثبتِ* phenomenal/qualia/sentience کند raise می‌کند.
    «conscious» تنها مجاز است (access-consciousness)؛ ذکرِ سلبیِ phenomenal هم مجاز است."""
    for t in texts:
        low = str(t or "").lower()
        hit = next((w for w in _PHENOMENAL_BANNED if w in low), None)
        if hit and not any(neg in low for neg in _NEGATIONS):
            raise ValueError(
                f"access-only violation: ادعای مثبتِ '{hit}' — فقط access-consciousness، نه phenomenal/qualia")

# metric names
IDENTIFIABILITY = "identifiability"   # N_eff (effective number of internal states)
CHANNEL = "channel"                   # DPI / mutual information I(H; H_hat)
LEVELS = "levels"                     # L_G (graph Laplacian spectrum)
SELF_REFERENCE = "self_reference"     # SOG (functional self-modeling verdict)
METHOD = "method"                     # S=>L (conditional proposition only)

# minimum samples before a metric is treated as authoritative. TODO(GLM): calibrate.
MIN_SAMPLES = {
    IDENTIFIABILITY: 200,
    CHANNEL: 500,     # plug-in MI estimator is positively biased on small n
    LEVELS: 8,        # need a non-trivial graph
    SELF_REFERENCE: 100,
    METHOD: 1,        # conditional proposition, not sample-driven
}


def _confidence(name: str, sample_size: int) -> float:
    need = MIN_SAMPLES.get(name, 1)
    if need <= 0:
        return 1.0
    return max(0.0, min(1.0, sample_size / need))


@dataclass
class EpiMetric:
    metric: str
    value: Any
    sample_size: int
    notes: str = ""
    epistemic_label: str = ""          # "" | fact | emerging | hype (access-only، بک‌لاگ #۳)
    ts: float = field(default_factory=time.time)
    schema: int = SCHEMA_VERSION
    type: str = RECORD_TYPE
    confidence: float = 0.0
    authoritative: bool = False

    def __post_init__(self) -> None:
        self.confidence = round(_confidence(self.metric, self.sample_size), 4)
        self.authoritative = self.sample_size >= MIN_SAMPLES.get(self.metric, 1)
        if self.epistemic_label and self.epistemic_label not in EPISTEMIC_LABELS:
            raise ValueError(
                f"epistemic_label نامعتبر: {self.epistemic_label!r} — یکی از {sorted(EPISTEMIC_LABELS)}")
        assert_access_only(self.notes, self.epistemic_label)   # گاردِ ضدِ phenomenal

    def to_record(self) -> dict:
        return asdict(self)


def make_metric(metric: str, value: Any, sample_size: int, notes: str = "",
                epistemic_label: str = "") -> dict:
    """Stamp a metric with confidence/authoritative + optional access-only triage label.
    epistemic_label ∈ {fact|emerging|hype}؛ notes/label نمی‌توانند ادعای phenomenal کنند."""
    return EpiMetric(metric=metric, value=value, sample_size=sample_size,
                     notes=notes, epistemic_label=epistemic_label).to_record()
