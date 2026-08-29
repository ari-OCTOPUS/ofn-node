"""Edge Gateway helpers (readonly diagnostics). Never issues actuator commands."""

from octopus_sensorium.edge_gateway.collect_diagnostics import collect_diagnostics, DIAG_COMMANDS

__all__ = ["collect_diagnostics", "DIAG_COMMANDS"]
