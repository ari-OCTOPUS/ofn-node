"""observatory — Evidence-Grounded Perception Layer (EQUIP G3).

Modules:
  - observation_v1: deterministic body parser (existing, L3 from ADR-041)
  - envelope: standardized ObservationEnvelope with content/instruction separation
  - evidence_parser: parser pipeline bridging envelope to observation_v1
  - allowlist_loader: runtime allowlist checker from observatory-allowlist.yaml
  - fetch_guard: L1 single-exit-door with SSRF protection and audit
"""
from .observation_v1 import PARSE_DRIFT, parse_body, SCHEMA  # noqa: F401
from .envelope import (  # noqa: F401
    ObservationEnvelope, create_envelope, content_hash,
    validate_content_type, validate_retention, validate_body_size,
    ENVELOPE_SCHEMA, PARSER_VERSION,
)
from .evidence_parser import parse_envelope, parse_with_body  # noqa: F401
from .allowlist_loader import ObservatoryAllowlist  # noqa: F401
from .fetch_guard import FetchGuard  # noqa: F401
