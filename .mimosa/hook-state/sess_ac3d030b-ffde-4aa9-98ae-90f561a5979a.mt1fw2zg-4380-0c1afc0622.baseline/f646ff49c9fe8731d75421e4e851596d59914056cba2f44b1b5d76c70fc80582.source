#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""connectors -- Privacy-preserving personal connector gateway (EQUIP G9).

This package provides a unified gateway for all personal connectors
(Telegram, GitHub, Hugging Face, Email, Finance, HealthKit, etc.) with:
  - Connector registry with typed manifests
  - Capability-based access control
  - Consent enforcement
  - PII/health/financial data redaction
  - Owner gate for write operations
  - Full audit trail

Modules:
  schema     -- Data types and connector manifest definitions
  registry   -- Connector registry with revocation
  gateway    -- Unified gateway with policy enforcement

Usage:
    from connectors import default_gateway, ConnectorRequest

    gw = default_gateway()
    resp = gw.route(ConnectorRequest(
        request_id="req-001",
        connector_id="telegram",
        action="read",
        target="owner_outer_dm",
    ))
    print(resp.allowed, resp.reason)
"""
from schema import (
    SCHEMA,
    BUILTIN_CONNECTORS,
    ConnectorManifest,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorStatus,
    OwnerGate,
    ReadScope,
    RetentionClass,
    RiskClass,
    WriteScope,
)
from registry import ConnectorRegistry, default_registry
from gateway import ConnectorGateway, default_gateway

__all__ = [
    "SCHEMA",
    "BUILTIN_CONNECTORS",
    "ConnectorManifest",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorStatus",
    "OwnerGate",
    "ReadScope",
    "RetentionClass",
    "RiskClass",
    "WriteScope",
    "ConnectorRegistry",
    "default_registry",
    "ConnectorGateway",
    "default_gateway",
]
