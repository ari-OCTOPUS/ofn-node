"""Planner exists for later waves. WAVE0 services must not import this module."""

from collections.abc import Sequence

from octopus_cognition.world_model.contracts import Action, PredictedState, State, WorldModel


class Planner:
    def __init__(self, world_model: WorldModel) -> None:
        self._world_model = world_model

    def simulate(self, state: State, plan: Sequence[Action]) -> list[PredictedState]:
        return self._world_model.rollout(state, plan)
