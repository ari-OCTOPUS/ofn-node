"""Typed effect-free boundary. Serialized validation claims are never accepted."""
from dataclasses import fields
import math
import re
from shadow_homeostasis.observation import Observation, parse_dt
from shadow_homeostasis.canonical import finite_number

OBS_FIELDS = {f.name for f in fields(Observation) if f.init}
CASE_FIELDS = {"case_id", "label", "observations", "sent_at", "ttl_s", "topology",
               "business_legs", "memory_updates", "prediction_trials", "note", "expected_sources"}


def observation_from_dict(raw):
    if not isinstance(raw, dict) or set(raw) - OBS_FIELDS:
        raise ValueError("unsupported observation fields; input cannot supply validation status")
    for name in ("observation_id", "source_id", "metric", "unit", "provenance_path", "quality"):
        if not isinstance(raw.get(name), str) or len(raw[name]) > 1024:
            raise ValueError("invalid observation string: " + name)
    for name in ("boot_id", "source_hash", "node_id"):
        if raw.get(name) is not None and not isinstance(raw[name], str):
            raise ValueError("invalid identity type")
    if not isinstance(raw.get("quality_reasons", []), list) or not all(
            isinstance(r, str) for r in raw.get("quality_reasons", [])):
        raise ValueError("invalid quality reasons")
    if type(raw.get("value")) not in (int, float, str, bool, type(None)):
        raise ValueError("invalid observation value type")
    # Times stay raw until trust can emit a specific failure reason.
    return Observation(**raw)


def envelope(case, evaluation_time):
    if not isinstance(case, dict) or set(case) - CASE_FIELDS:
        raise ValueError("unknown case fields")
    if not isinstance(case.get("case_id"), str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}", case["case_id"]):
        raise ValueError("case_id contract")
    if case.get("label") not in ("SIMULATED", "REDACTED_SNAPSHOT"):
        raise ValueError("explicit provenance label required")
    observations = case.get("observations")
    if not isinstance(observations, list) or len(observations) > 128:
        raise ValueError("bounded observations required")
    sent, dt = parse_dt(case.get("sent_at")), parse_dt(evaluation_time)
    ttl = case.get("ttl_s")
    if sent is None or dt is None or not finite_number(ttl) or ttl < 0:
        raise ValueError("envelope clock/TTL contract")
    for key in ("business_legs", "memory_updates", "prediction_trials", "expected_sources"):
        if not isinstance(case.get(key, []), list) or len(case.get(key, [])) > 256:
            raise ValueError("bounded list required: " + key)
    if not all(isinstance(source, str) and source for source in case.get("expected_sources", [])):
        raise ValueError("expected source identity contract")
    if case.get("topology") is not None and not isinstance(case["topology"], dict):
        raise ValueError("topology object required")
    age = (dt - sent).total_seconds()
    status = "FUTURE" if age < 0 else "EXPIRED" if age > ttl else "CURRENT"
    return {"case_id": case["case_id"], "label": case["label"], "status": status,
            "age_s": age, "ttl_s": ttl, "source_authentication": "UNVERIFIED",
            "executable": False}
