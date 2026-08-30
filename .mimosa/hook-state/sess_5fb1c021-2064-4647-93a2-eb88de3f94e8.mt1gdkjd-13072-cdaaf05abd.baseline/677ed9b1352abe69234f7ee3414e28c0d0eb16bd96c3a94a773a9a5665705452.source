"""
REAL experiments (non-synthetic). Each entry returns (conditions, primary)
exactly like demo.mock_experiments, but Condition.run executes a real
evaluation. Names registered here override the synthetic registry in the CLI.
"""
from .adaptive_forgetting import adaptive_forgetting
from .adaptive_forgetting_v2 import adaptive_forgetting_v2
from .attractor_memory import attractor_memory
from .causal_selfmodel import causal_selfmodel
from .comparison_metacog import comparison_metacog
from .comparison_metacog_v2 import comparison_metacog_v2
from .consolidation import consolidation
from .control_signals import control_signals
from .multimetric_memory import multimetric_memory
from .ontology_shift import ontology_shift
from .retrieve_compute import retrieve_compute
from .drake_kernels import drake_kernels
from .geometry_abstraction import geometry_abstraction
from .gridworld_wm import REGISTRY_REAL as _GRIDWORLD
from .homeostasis import homeostasis
from .hybrid_organism import hybrid_organism
from .memory_policy import memory_policy
from .prospective_memory import prospective_memory
from .social_mirror import social_mirror
from .wm_transfer_gain import wm_transfer_gain

REGISTRY_REAL = dict(_GRIDWORLD)
REGISTRY_REAL["drake_kernels"] = drake_kernels
REGISTRY_REAL["geometry_abstraction"] = geometry_abstraction
REGISTRY_REAL["wm_abstraction_v2"] = wm_transfer_gain
REGISTRY_REAL["homeostasis"] = homeostasis
REGISTRY_REAL["consolidation"] = consolidation
REGISTRY_REAL["hybrid_organism"] = hybrid_organism
# wave-2 hypotheses (H-OWN-01/02/05/06/07/08)
REGISTRY_REAL["social_mirror"] = social_mirror
REGISTRY_REAL["comparison_metacog"] = comparison_metacog
REGISTRY_REAL["prospective_memory"] = prospective_memory
REGISTRY_REAL["memory_policy"] = memory_policy
REGISTRY_REAL["causal_selfmodel"] = causal_selfmodel
REGISTRY_REAL["control_signals"] = control_signals
# final corpus experiments (EXP-004/005)
REGISTRY_REAL["adaptive_forgetting"] = adaptive_forgetting
REGISTRY_REAL["retrieve_compute"] = retrieve_compute
# completion wave: geometry substrates + declared v2 follow-ups
REGISTRY_REAL["ontology_shift"] = ontology_shift
REGISTRY_REAL["multimetric_memory"] = multimetric_memory
REGISTRY_REAL["attractor_memory"] = attractor_memory
REGISTRY_REAL["comparison_metacog_v2"] = comparison_metacog_v2
REGISTRY_REAL["adaptive_forgetting_v2"] = adaptive_forgetting_v2

__all__ = ["REGISTRY_REAL"]
