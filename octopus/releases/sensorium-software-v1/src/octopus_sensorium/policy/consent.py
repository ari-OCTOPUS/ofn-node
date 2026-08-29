"""Consent is required for personal/health classification. Wave 0 sensors are internal host telemetry."""

from __future__ import annotations


def consent_required(classification: str, contains_pii: bool) -> bool:
    return classification in {"personal", "health"} or contains_pii
