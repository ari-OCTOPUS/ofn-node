"""OCTOPUS connector evidence + CONNECTOR-GAP stubs.

Runtime SoT code also mirrored under:
  F:\\backup\\_ops\\evidence_plane\\connector_evidence.py
  F:\\backup\\_ops\\evidence_plane\\connector_gap_loader.py
"""
from .connector_evidence import (
    SCHEMA,
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

__all__ = [
    "SCHEMA",
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
