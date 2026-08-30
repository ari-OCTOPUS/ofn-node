# ADR-033 Evidence-Control Plane — registry, events, quarantine, promotion.
# 2026-08-23 laptop-debug: re-export connector_* for import surface parity with agents/octopus_evidence.
SCHEMA = "evidence-control-plane.v1"
POLICY_VERSION = "ADR-033-v1"

from .connector_evidence import (
    SCHEMA as CONNECTOR_EVIDENCE_SCHEMA,
    VALID_SOURCE_TYPES,
    normalize_record,
    validate_batch,
    compute_evidence_id,
    is_valid_evidence_id,
    is_valid_source_type,
)
from .connector_gap_loader import (
    load_registry,
    connector_status,
    mark_oauth_gaps,
    resolve_registry_path,
)

# Keep plane SCHEMA as ADR-033; connector schema available as CONNECTOR_EVIDENCE_SCHEMA.
__all__ = [
    "SCHEMA",
    "POLICY_VERSION",
    "CONNECTOR_EVIDENCE_SCHEMA",
    "VALID_SOURCE_TYPES",
    "normalize_record",
    "validate_batch",
    "compute_evidence_id",
    "is_valid_evidence_id",
    "is_valid_source_type",
    "load_registry",
    "connector_status",
    "mark_oauth_gaps",
    "resolve_registry_path",
]
