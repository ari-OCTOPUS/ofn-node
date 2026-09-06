"""Isolated WAVE0 shadow slice: Trust → Homeostasis → World Model → Metacontrol.

Not imported by organism.py. executable is always False.
"""
from .observation import Observation, Quality
from .registry import MetricRegistry, default_registry
from .trust import eligibility, validate_observation
from .homeostasis import assess as assess_homeostasis
from .world_model import build_world_state
from .metacontrol import decide as metacontrol_decide
from .pipeline import run_shadow_pipeline

__all__ = [
    "Observation", "Quality", "MetricRegistry", "default_registry",
    "validate_observation", "eligibility",
    "assess_homeostasis", "build_world_state", "metacontrol_decide",
    "run_shadow_pipeline",
]
PACKAGE = "shadow_homeostasis"
VERSION = "0.1.0"
EXECUTABLE_POLICY = False
