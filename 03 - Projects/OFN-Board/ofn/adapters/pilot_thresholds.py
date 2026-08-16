"""Owner-writable pilot thresholds and payment-rail choices.

The approved pilot criterion lives in docs/operations/PILOT-14DAY.md.
Defaults here match that document so the report never invents a new KPI.
Owner overrides are stored under state_dir (0700) as JSON — not secrets,
not PII — and are read back by tools/pilot_report.py.

Payment methods start unset. Unset means "not measured"; the UI must not
pretend a rail exists.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping


# Documented defaults from PILOT-14DAY.md — not invented here.
DEFAULT_THRESHOLDS = {
    "min_production_listings": 3,
    "min_linked_production_inquiries": 1,
    "min_qualifying_production_payments": 1,
}

PAYMENT_METHODS = ("unset", "payid", "bank_transfer", "cash", "stripe", "other")
BUSINESSES = ("lead", "ziman", "studio")


@dataclass(frozen=True)
class PilotConfig:
    thresholds: Mapping[str, int]
    payment_methods: Mapping[str, str]
    source: str  # "defaults" | "owner"


def _path(state_dir: str) -> str:
    return os.path.join(state_dir, "pilot_config.json")


def ensure_private_dir(state_dir: str) -> None:
    """Owner-private directory before first write (CLAUDE §۷-الف)."""
    os.makedirs(state_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(state_dir, 0o700)
    except OSError:
        pass


def load(state_dir: str) -> PilotConfig:
    path = _path(state_dir)
    if not os.path.isfile(path):
        return PilotConfig(
            thresholds=dict(DEFAULT_THRESHOLDS),
            payment_methods={b: "unset" for b in BUSINESSES},
            source="defaults",
        )
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return PilotConfig(
            thresholds=dict(DEFAULT_THRESHOLDS),
            payment_methods={b: "unset" for b in BUSINESSES},
            source="defaults",
        )
    th = dict(DEFAULT_THRESHOLDS)
    for key in DEFAULT_THRESHOLDS:
        try:
            val = int((raw.get("thresholds") or {}).get(key, th[key]))
            if val > 0:
                th[key] = val
        except (TypeError, ValueError):
            pass
    pays = {b: "unset" for b in BUSINESSES}
    for b in BUSINESSES:
        m = str((raw.get("payment_methods") or {}).get(b, "unset")).strip()
        if m in PAYMENT_METHODS:
            pays[b] = m
    return PilotConfig(thresholds=th, payment_methods=pays, source="owner")


def save(state_dir: str, body: Mapping[str, Any]) -> PilotConfig:
    current = load(state_dir)
    th = dict(current.thresholds)
    incoming_th = body.get("thresholds") or {}
    if isinstance(incoming_th, Mapping):
        for key in DEFAULT_THRESHOLDS:
            if key not in incoming_th:
                continue
            try:
                val = int(incoming_th[key])
            except (TypeError, ValueError):
                raise ValueError(f"threshold {key} must be a positive integer")
            if val <= 0 or val > 10_000:
                raise ValueError(f"threshold {key} out of range")
            th[key] = val
    pays = dict(current.payment_methods)
    incoming_pay = body.get("payment_methods") or {}
    if isinstance(incoming_pay, Mapping):
        for b in BUSINESSES:
            if b not in incoming_pay:
                continue
            m = str(incoming_pay[b] or "").strip()
            if m not in PAYMENT_METHODS:
                raise ValueError(f"payment method for {b} invalid")
            pays[b] = m
    ensure_private_dir(state_dir)
    path = _path(state_dir)
    payload = {
        "thresholds": th,
        "payment_methods": pays,
        "updated_by": "owner",
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return PilotConfig(thresholds=th, payment_methods=pays, source="owner")


def as_dict(cfg: PilotConfig) -> dict[str, Any]:
    unset = [b for b, m in cfg.payment_methods.items() if m == "unset"]
    return {
        "ok": True,
        "thresholds": dict(cfg.thresholds),
        "payment_methods": dict(cfg.payment_methods),
        "source": cfg.source,
        "defaults": dict(DEFAULT_THRESHOLDS),
        "payment_methods_unset": unset,
        "ready_for_measured_pilot": len(unset) == 0,
    }
