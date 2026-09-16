"""Thin adapters around real Octopus system-under-test modules."""

from .collab_adapter import run as run_collaborator
from .kill_seam_adapter import evaluate as evaluate_kill_seam
from .model_router_adapter import RouterObservation, RouterScenario, run as run_model_router

__all__ = (
    "RouterObservation", "RouterScenario", "evaluate_kill_seam",
    "run_collaborator", "run_model_router",
)
