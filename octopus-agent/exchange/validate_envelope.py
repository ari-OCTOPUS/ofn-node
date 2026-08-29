#!/usr/bin/env python3
"""Deterministic envelope validator for the board<->laptop exchange (D12).
Dependency-free, clock-free. Returns (ok, [rule-ids]).
Direction: outbound = board->laptop, inbound = laptop->board.
"""
from __future__ import annotations

import hashlib
import json
import re

TYPES = {"EVIDENCE", "PROPOSAL", "REPORT", "QUERY", "ACK"}
REQUIRED = ("msg_id", "run_id", "from", "to", "type", "ts_utc", "boot_id",
            "evidence_refs", "payload", "payload_hash", "prev_msg_hash", "may_authorize")
MSG_ID = re.compile(r"^msg-\d{8}T\d{4,6}Z-[0-9a-f]{8,}$")
TS_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")

CMD_KEYS = {"command", "cmd", "exec", "eval", "script", "shell", "shell_command", "run_command"}
CMD_STARTS = ("systemctl", "sudo ", "reboot", "shutdown", "curl ", "wget ", "rm -rf", "apt ", "pip install")
AUTH_KEYS = {"set_authority", "enable_flag", "restart_service", "authorize", "arm", "enable_actuator"}
CRED_PATTERNS = (re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"), re.compile(r"\.ed25519\.private"),
                 re.compile(r"(?i)\b(api[_-]?key|secret|password)\s*[:=]"))


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_sha(payload) -> str:
    return "sha256:" + hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def validate(msg, direction: str):
    if not isinstance(msg, dict):
        return False, ["X01 not a JSON object"]
    errors = []
    for f in REQUIRED:
        if f not in msg:
            errors.append(f"X02 missing field {f}")
    if errors:
        return False, errors
    if not isinstance(msg.get("msg_id"), str) or not MSG_ID.match(msg["msg_id"]):
        errors.append("X03 msg_id malformed")
    want = ("board", "laptop") if direction == "outbound" else ("laptop", "board")
    if (msg.get("from"), msg.get("to")) != want:
        errors.append("X04 from/to not the expected direction pair")
    if msg.get("type") not in TYPES:
        errors.append("X05 type not allowed")
    if not isinstance(msg.get("ts_utc"), str) or not TS_Z.match(msg.get("ts_utc", "")):
        errors.append("X06 ts_utc not ISO-8601 Z")
    if not str(msg.get("boot_id") or ""):
        errors.append("X07 boot_id missing/empty")
    if not isinstance(msg.get("payload"), dict):
        errors.append("X08 payload not an object")
    else:
        ph = msg.get("payload_hash")
        if not isinstance(ph, str) or ph != payload_sha(msg["payload"]):
            errors.append("X09 payload_hash missing or mismatched")
    if not isinstance(msg.get("evidence_refs"), list):
        errors.append("X02 evidence_refs must be an array")
    pmh = msg.get("prev_msg_hash")
    if pmh is not None and (not isinstance(pmh, str) or not SHA.match(pmh)):
        errors.append("X10 prev_msg_hash not sha256-string or null")
    if msg.get("may_authorize") is not False:
        errors.append("X11 may_authorize must be false")
    # v1.1 Evidence Envelope extension (owner verification doctrine 2026-08-18):
    # additive + optional; type-checked only when present so v1 messages stay valid.
    for f in ("claim", "initiating_owner", "uncertainty", "escalation"):
        if f in msg and not isinstance(msg[f], str):
            errors.append(f"X12 v1.1 field {f} must be a string")
    if "reproduction" in msg:
        r = msg["reproduction"]
        if not isinstance(r, list) or not all(isinstance(x, str) for x in r):
            errors.append("X12 reproduction must be an array of strings")
    if "raw_evidence" in msg:
        rv = msg["raw_evidence"]
        if not isinstance(rv, list) or not all(isinstance(x, dict) for x in rv):
            errors.append("X12 raw_evidence must be an array of objects")
    return (not errors), errors


def scan_inbound_payload(payload) -> list[str]:
    """Deterministic prohibition scan for laptop->board payloads. Returns P-ids."""
    violations: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() in CMD_KEYS:
                    violations.append(f"P01 command-like key '{k}'")
                if str(k).lower() in AUTH_KEYS:
                    violations.append(f"P03 authority-change key '{k}'")
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            s = node.strip()
            if s.startswith(CMD_STARTS):
                violations.append(f"P01 command-like value '{s[:40]}'")
            for pat in CRED_PATTERNS:
                if pat.search(node):
                    violations.append(f"P02 credential content '{node[:40]}'")
                    break

    walk(payload)
    return violations
