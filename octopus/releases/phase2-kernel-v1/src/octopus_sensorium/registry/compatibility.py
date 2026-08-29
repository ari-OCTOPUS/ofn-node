"""Compatibility notes. Live signed registry is authoritative until a v2 bundle expands it."""

LIVE_NUMERIC_IDS = {51, 52, 53, 54, 55, 56, 92, 95}
REGISTRY_100_STATUS = "APPLIED"
REGISTRY_100_REQUIRES = "offline_v2_signing_bundle"
STAGING_PATH = "/var/lib/octopus/staging/phase3-registry-100"
LIVE_REGISTRY_HASH = "sha256:19f25383d2611000e3272ad9ad5d55e2e645cb5db757a9419f4e7b6d5f1251c5"
