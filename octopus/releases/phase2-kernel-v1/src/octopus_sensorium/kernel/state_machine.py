"""Re-export of the agent state machine. READY remains a verifier gate, not a title."""

from octopus_sensorium.state_machine import AgentState, IllegalTransition, StateMachine

__all__ = ["AgentState", "IllegalTransition", "StateMachine"]
