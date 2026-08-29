"""OpenTelemetry kernel hooks. No OTLP export, no new port, OCT-SENSE-055 stays not_enabled."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Span, Tracer

OTEL_EXPORT = False
OTEL_ENDPOINT = None
SENSOR_055_STATUS = "not_enabled"
KERNEL_STATUS = "in_process_noop"

_provider: TracerProvider | None = None


def init_otel() -> Tracer:
    global _provider
    if _provider is None:
        _provider = TracerProvider()
        trace.set_tracer_provider(_provider)
    return trace.get_tracer("octopus.sensorium.kernel")


def tracer() -> Tracer:
    return init_otel()


def start_span(name: str) -> Span:
    return tracer().start_span(name)
