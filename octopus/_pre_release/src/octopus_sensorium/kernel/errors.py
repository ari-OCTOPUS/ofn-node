"""Kernel errors. Pipeline failures stay fail-closed."""

from __future__ import annotations

from octopus_sensorium.pipeline import PipelineError
from octopus_sensorium.sensors.base import SensorError
from octopus_sensorium.state_machine import IllegalTransition


class KernelError(Exception):
    pass


class PluginLifecycleError(KernelError):
    pass


class UnknownPluginError(KernelError):
    pass


class ReadinessSourceError(KernelError):
    pass


__all__ = [
    "IllegalTransition",
    "KernelError",
    "PipelineError",
    "PluginLifecycleError",
    "ReadinessSourceError",
    "SensorError",
    "UnknownPluginError",
]
