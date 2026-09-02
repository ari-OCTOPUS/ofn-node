#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""telegram_glass — the read-only Telegram command surface (Article-10 lane 4).

Owner directive 2026-08-22 / Final Plan stage 4: Telegram is a read-only
command bus, never an actuator. This module answers six owner commands
(/status /self /doctor /money /queue /receipts) from honest local sources
and embeds a receipt (run_id, ts, node_id, sources) in every answer.

House rules encoded here:

  * may_authorize is False ALWAYS — there is no send path, no token read,
    no network call in this lane; bot wiring stays with the owner's runtime.
  * a claim the module cannot verify from a named source is answered
    UNKNOWN — never guessed, never defaulted to green;
  * a malformed source fails closed (FailClosedError) instead of producing
    a plausible-looking answer;
  * the 7-stage loop is reported with only the stages that actually
    occurred marked. MODEL_STARTED and PROPOSAL_CREATED never occur here
    (no model call, no proposal), and EXECUTION_RECEIPT is "done" exactly
    when the answer carries a receipt — which is always, so "Done"
    without a receipt cannot be expressed.

Router purity: route() is a pure function of (command, snapshot) plus
injected run_id/ts. Builders do local, read-only file/git reads only.
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping

from ofn.kernel.errors import FailClosedError
from ofn.kernel import self_model as _sm

__all__ = ["SCHEMA_ID", "COMMANDS", "LOOP_STAGES", "NODE_IDS", "UNKNOWN",
           "DEFAULT_NODE_ID", "FailClosedError", "route", "receipt_of",
           "render_text", "build_status_snapshot", "build_learning_snapshot",
           "build_self_snapshot"]

SCHEMA_ID = "octopus.telegram-glass.v1"
UNKNOWN = "UNKNOWN"

COMMANDS = ("/status", "/self", "/doctor", "/money", "/queue", "/receipts")

# The 7-stage loop vocabulary (Final Plan stage 4). A stage value is
# "done", "skipped" or "refused" — nothing else is emitted.
LOOP_STAGES = ("USER_MESSAGE_ACCEPTED", "INTENT_DETECTED", "MODEL_STARTED",
               "CLAIM_VERIFIED", "PROPOSAL_CREATED", "EXECUTION_RECEIPT",
               "RUN_COMPLETED")

STAGE_DONE = "done"
STAGE_SKIPPED = "skipped"

# status vocabulary: ok = verified and quiet · degraded = verified but the
# verified facts include an alarm · unknown = a source was absent ·
# error = a source was malformed (fail-closed) · unknown_command
STATUS_OK = "ok"
STATUS_DEGRADED = "degraded"
STATUS_UNKNOWN = "unknown"
STATUS_ERROR = "error"
STATUS_UNKNOWN_COMMAND = "unknown_command"
_CLAIM_VERIFIED_STATUSES = (STATUS_OK, STATUS_DEGRADED)
_ALARM_VALUES = ("incoherent",)   # verified values that are alarms, not oks

# Node tags from the owner's three-machine plan. Answers are tagged with
# where they were produced; an untagged answer is not ours to send.
NODE_IDS = ("BUSINESS", "SENSORIUM", "LAPTOP")
DEFAULT_NODE_ID = "LAPTOP"

MAX_RECEIPTS_SHOWN = 5

LEDGER_SOURCE = "ofn/learning/ledger.py (EconomicLearningLedger JSONL)"
SELF_MODEL_SOURCE = "ofn/adapters/self_model_producer.py (octopus.self-model.v2)"

PAYMENT_KIND = "payment_claim"
QUOTE_KIND = "quote"
VERIFIED = "VERIFIED"


# ── internal helpers ─────────────────────────────────────────────────────


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_mapping(value: Any, *, what: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FailClosedError(f"malformed source, mapping required: {what}")
    return value


def _require_int(value: Any, *, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"malformed source, int required: {what}={value!r}")
    return value


def _require_str(value: Any, *, what: str) -> str:
    if not isinstance(value, str):
        raise FailClosedError(f"malformed source, str required: {what}={value!r}")
    return value


def _source_entry(field: str, source: str, state: str) -> dict:
    return {"field": field, "source": source, "state": state}


# ── snapshot builders (local, read-only; no network) ────────────────────


def build_status_snapshot(repo_root: Path | str | None = None) -> dict:
    """Repo facts from local git only. Board config hashes are NOT collected
    here (no ssh/board access from this lane) — the caller may supply them;
    their absence is answered UNKNOWN, not guessed."""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return {"git_head": None, "dirty_files": None,
                "git_error": "git-unavailable"}
    return {"git_head": head or None, "dirty_files": len(dirty)}


def build_learning_snapshot(ledger_path: Path | str | None) -> dict:
    """Parse the economic learning ledger read-only.

    EconomicLearningLedger's constructor creates and heals the file — both
    are mutations, so this builder never instantiates it; it parses the
    JSONL directly. A missing file is named, not invented; a malformed
    line fails closed (the ledger is tamper-evident, guessing defeats it).
    """
    if ledger_path is None:
        return {"ledger_rows": None, "ledger_path": None}
    path = Path(ledger_path)
    if not path.is_file():
        return {"ledger_rows": None, "ledger_path": path.as_posix(),
                "ledger_error": "file-absent"}
    rows = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError as exc:
            raise FailClosedError(
                f"malformed ledger {path} line {n}: {exc}") from None
        if not isinstance(row, dict):
            raise FailClosedError(f"malformed ledger {path} line {n}: not an object")
        rows.append(row)
    return {"ledger_rows": rows, "ledger_path": path.as_posix()}


def build_self_snapshot(producer: Callable[[], Mapping] | None = None) -> dict:
    """Self-model envelope from an injected producer callable (typically
    functools.partial(self_model_producer.produce, repo_root=...)). The
    glass lane itself never probes ports or shells out; with no producer
    the field is honestly absent."""
    if producer is None:
        return {"self_model_envelope": None}
    envelope = producer()
    _require_mapping(envelope, what="self_model_envelope")
    return {"self_model_envelope": dict(envelope)}


# ── per-command readers (snapshot → data + sources) ─────────────────────


def _read_status(snapshot: Mapping) -> tuple[dict, list]:
    data, sources = {}, []
    head = snapshot.get("git_head")
    if head is None:
        data["git_head"] = UNKNOWN
        state = "absent" if "git_error" not in snapshot else "error"
        sources.append(_source_entry("git_head", "git rev-parse HEAD (local)", state))
    else:
        data["git_head"] = _require_str(head, what="git_head")
        sources.append(_source_entry("git_head", "git rev-parse HEAD (local)", "read"))
    dirty = snapshot.get("dirty_files")
    if dirty is None:
        data["dirty_files"] = UNKNOWN
        sources.append(_source_entry("dirty_files", "git status --porcelain (local)",
                                     "absent" if "git_error" not in snapshot else "error"))
    else:
        data["dirty_files"] = _require_int(dirty, what="dirty_files")
        sources.append(_source_entry("dirty_files", "git status --porcelain (local)", "read"))
    hashes = snapshot.get("board_config_hashes")
    field, source = "board_config_coherence", "supplied:board_config_hashes"
    if hashes is None:
        data[field] = UNKNOWN
        sources.append(_source_entry(field, source, "absent"))
    else:
        _require_mapping(hashes, what="board_config_hashes")
        values = [_require_str(v, what=f"board_config_hashes[{k}]")
                  for k, v in hashes.items()]
        if len(values) < 2:
            data[field] = UNKNOWN        # one reporter cannot prove coherence
        elif len(set(values)) == 1:
            data[field] = "coherent"
        else:
            data[field] = "incoherent"
        data["boards_reporting"] = len(values)
        sources.append(_source_entry(field, source, "read"))
    return data, sources


def _read_self(snapshot: Mapping) -> tuple[dict, list]:
    envelope = snapshot.get("self_model_envelope")
    field = "self_model"
    if envelope is None:
        return ({field: UNKNOWN}, [_source_entry(field, SELF_MODEL_SOURCE, "absent")])
    envelope = _require_mapping(envelope, what="self_model_envelope")
    schema = _require_str(envelope.get("schema"), what="self_model.schema")
    if schema != "octopus.self-model.v2":
        raise FailClosedError(f"malformed source, unexpected self-model schema: {schema!r}")
    body = _require_mapping(envelope.get("data"), what="self_model.data")
    readings = []
    for group in ("sensors", "processes", "capabilities"):
        items = body.get(group)
        if items is not None:
            _require_mapping_items(items, what=f"self_model.{group}")
            readings.extend(items)
    healthy = sum(1 for r in readings if r.get("status") == _sm.HEALTHY)
    data = {
        "status": _require_str(envelope.get("status"), what="self_model.status"),
        "generated_at": envelope.get("generated_at", UNKNOWN),
        "readings_total": len(readings),
        "readings_healthy": healthy,
        "readings_degraded": len(readings) - healthy,
        "warnings": len(envelope.get("warnings") or ()),
        "unknowns_declared": len(body.get("unknowns") or ()),
    }
    return (data, [_source_entry(field, SELF_MODEL_SOURCE, "read")])


def _require_mapping_items(items: Any, *, what: str) -> None:
    if not isinstance(items, (list, tuple)):
        raise FailClosedError(f"malformed source, list required: {what}")
    for item in items:
        _require_mapping(item, what=what)


def _read_doctor(snapshot: Mapping) -> tuple[dict, list]:
    snap = snapshot.get("doctor_snapshot")
    field, source = "doctor_units", "supplied:doctor_snapshot"
    if snap is None:
        return ({field: UNKNOWN, "failed_units": UNKNOWN},
                [_source_entry("failed_units", source, "absent")])
    snap = _require_mapping(snap, what="doctor_snapshot")
    units = snap.get("units")
    if not isinstance(units, (list, tuple)):
        raise FailClosedError("malformed source, doctor_snapshot.units must be a list")
    failed = []
    for unit in units:
        unit = _require_mapping(unit, what="doctor_snapshot.units[]")
        name = _require_str(unit.get("name"), what="doctor unit name")
        state = _require_str(unit.get("state"), what=f"doctor unit state {name}")
        if state == "failed":
            failed.append(name)
    data = {field: len(units), "failed_units": len(failed)}
    if failed:
        data["failed_names"] = failed
    return (data, [_source_entry("failed_units", source, "read")])


def _payment_rows(rows: list, *, source: str) -> tuple[list, list]:
    payments, sources = [], []
    verified = unverified = unpriced_quotes = 0
    for row in rows:
        kind = row.get("kind")
        if kind is not None:
            _require_str(kind, what="ledger row kind")
        if kind == PAYMENT_KIND:
            payments.append(row)
            if row.get("verification_status") == VERIFIED:
                verified += 1
            else:
                unverified += 1
        elif kind == QUOTE_KIND and row.get("amount") is None \
                and row.get("price") is None:
            unpriced_quotes += 1
    if rows:
        sources.append(_source_entry("payments", source, "read"))
    else:
        sources.append(_source_entry("payments", source, "read-empty"))
    return payments, [verified, unverified, unpriced_quotes, sources]


def _read_money(snapshot: Mapping) -> tuple[dict, list]:
    rows = snapshot.get("ledger_rows")
    field, source = "money", LEDGER_SOURCE
    if rows is None:
        named = snapshot.get("ledger_path") or "ledger_path"
        return ({field: UNKNOWN},
                [_source_entry(field, f"{source} @ {named}",
                               snapshot.get("ledger_error", "absent"))])
    if not isinstance(rows, (list, tuple)):
        raise FailClosedError("malformed source, ledger_rows must be a list")
    for row in rows:
        _require_mapping(row, what="ledger_rows[]")
    payments, (verified, unverified, unpriced, sources) = _payment_rows(list(rows), source=source)
    data = {"verified_payment_count": verified,
            "unverified_payment_count": unverified,
            "unpriced_quote_count": unpriced}
    return data, sources


def _read_receipts(snapshot: Mapping) -> tuple[dict, list]:
    rows = snapshot.get("ledger_rows")
    field, source = "receipts", LEDGER_SOURCE
    if rows is None:
        named = snapshot.get("ledger_path") or "ledger_path"
        return ({field: UNKNOWN},
                [_source_entry(field, f"{source} @ {named}",
                               snapshot.get("ledger_error", "absent"))])
    if not isinstance(rows, (list, tuple)):
        raise FailClosedError("malformed source, ledger_rows must be a list")
    for row in rows:
        _require_mapping(row, what="ledger_rows[]")
    payments, (_, _, _, sources) = _payment_rows(list(rows), source=source)
    payments.sort(key=lambda r: str(r.get("ts") or ""), reverse=True)
    shown = [{"record_id": str(r.get("record_id", UNKNOWN)),
              "ts": r.get("ts", UNKNOWN),
              "verification_status": r.get("verification_status", UNKNOWN),
              "lead_id": r.get("lead_id", UNKNOWN),
              "amount": r.get("amount", UNKNOWN)}
             for r in payments[:MAX_RECEIPTS_SHOWN]]
    data = {"receipts": shown, "payment_rows_total": len(payments)}
    return data, sources


def _read_queue(snapshot: Mapping) -> tuple[dict, list]:
    prs = snapshot.get("open_prs")
    field, source = "open_pr_count", "supplied:open_prs"
    if prs is None:
        return ({field: UNKNOWN}, [_source_entry(field, source, "absent")])
    if not isinstance(prs, (list, tuple)):
        raise FailClosedError("malformed source, open_prs must be a list")
    cleaned = []
    for pr in prs:
        pr = _require_mapping(pr, what="open_prs[]")
        cleaned.append({"number": _require_int(pr.get("number"), what="open_prs[].number"),
                        "title": _require_str(pr.get("title"), what="open_prs[].title")})
    return ({field: len(cleaned), "open_prs": cleaned},
            [_source_entry(field, source, "read")])


_READERS = {
    "/status": _read_status,
    "/self": _read_self,
    "/doctor": _read_doctor,
    "/money": _read_money,
    "/queue": _read_queue,
    "/receipts": _read_receipts,
}


# ── the router ───────────────────────────────────────────────────────────


def _loop_marking(status: str, known_command: bool) -> dict:
    """Only the stages that actually occurred are marked done. MODEL_STARTED
    and PROPOSAL_CREATED never occur in a read-only lane."""
    return {
        "USER_MESSAGE_ACCEPTED": STAGE_DONE,
        "INTENT_DETECTED": STAGE_DONE if known_command else STAGE_SKIPPED,
        "MODEL_STARTED": STAGE_SKIPPED,      # never: this lane calls no model
        "CLAIM_VERIFIED": (STAGE_DONE if status in _CLAIM_VERIFIED_STATUSES
                           else STAGE_SKIPPED),
        "PROPOSAL_CREATED": STAGE_SKIPPED,   # never: read-only surface
        "EXECUTION_RECEIPT": STAGE_DONE,     # always: the answer is its receipt
        "RUN_COMPLETED": STAGE_DONE,
    }


def _dispatch(command: str | None, snapshot: Mapping[str, Any] | None) -> tuple:
    snapshot = {} if snapshot is None else _require_mapping(snapshot, what="snapshot")
    cmd = (command or "").strip().lower() or UNKNOWN
    known_command = cmd in _READERS
    status, data, sources, warnings = STATUS_UNKNOWN_COMMAND, {}, [], []
    if not known_command:
        warnings.append(f"unknown command: {cmd!r}")
        data = {"error": "unknown command", "known_commands": list(COMMANDS)}
        # the receipt still names its source: the router's own command table
        sources = [_source_entry("command", "telegram_glass COMMANDS", "absent")]
        return status, cmd, known_command, data, sources, warnings
    data, sources = _READERS[cmd](snapshot)
    unverifiable = sorted(k for k, v in data.items() if v == UNKNOWN)
    alarms = sorted(k for k, v in data.items() if v in _ALARM_VALUES)
    failed = data.get("failed_units")
    if cmd == "/doctor" and isinstance(failed, int) \
            and not isinstance(failed, bool) and failed > 0:
        alarms.append("failed_units")    # failed units are a verified alarm
    if unverifiable:
        status = STATUS_UNKNOWN
    elif alarms:
        status = STATUS_DEGRADED
    else:
        status = STATUS_OK
    if unverifiable:
        warnings.append("UNKNOWN fields: " + ", ".join(unverifiable))
    if alarms:
        warnings.append("verified alarm: " + ", ".join(alarms))
    return status, cmd, known_command, data, sources, warnings


def _refused(command: str | None, run_id: str | None, now_iso: str | None,
             node_id: str, reason: str) -> dict:
    """The fail-closed answer: status error, no claim answered, receipt
    still complete — a refusal is itself a receipted fact."""
    return {
        "schema": SCHEMA_ID,
        "command": command or "",
        "run_id": run_id or str(uuid.uuid4()),
        "ts": now_iso or _now_iso(),
        "node_id": node_id,
        "may_authorize": False,
        "read_only": True,
        "status": STATUS_ERROR,
        "data": {"error": reason},
        "sources": [_source_entry((command or "").lstrip("/"), "snapshot", "malformed")],
        "warnings": ["fail-closed: source refused, nothing answered in its place"],
        "loop": _loop_marking("error", known_command=False),
    }


def route(command: str | None, snapshot: Mapping[str, Any] | None = None, *,
          run_id: str | None = None, now_iso: str | None = None,
          node_id: str = DEFAULT_NODE_ID) -> dict:
    """Pure: (command, snapshot) → response. No network, no token, no send.

    The response IS the receipt: run_id, ts, node_id and sources are
    always present, so an answer without a receipt cannot be constructed.
    A malformed source fails closed INSIDE the response — status "error",
    no claim answered, nothing invented in its place — because a command
    bus that drops the receipt on error would answer "done" unreceipted.
    Only a contract violation (unknown node tag) raises.
    """
    if node_id not in NODE_IDS:
        raise FailClosedError(f"unknown node_id {node_id!r} — tag must be one of {NODE_IDS}")
    try:
        status, cmd, known_command, data, sources, warnings = _dispatch(command, snapshot)
    except FailClosedError as exc:
        response = _refused(command, run_id, now_iso, node_id, str(exc))
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        # a reader tripping on an ill-typed value is the same refusal,
        # never a crash dressed up as an answer
        response = _refused(command, run_id, now_iso, node_id,
                            f"malformed source for {command!r}: {exc!r}")
    else:
        response = {
            "schema": SCHEMA_ID,
            "command": cmd if known_command else (command or ""),
            "run_id": run_id or str(uuid.uuid4()),
            "ts": now_iso or _now_iso(),
            "node_id": node_id,
            "may_authorize": False,          # ALWAYS — read-only command bus
            "read_only": True,
            "status": status,
            "data": data,
            "sources": sources,
            "warnings": warnings,
            "loop": _loop_marking(status, known_command),
        }
    return response


def receipt_of(response: Mapping[str, Any]) -> dict:
    """The receipt a response carries: the four fields every answer must
    have. Missing any of them means the response is not publishable."""
    missing = [k for k in ("run_id", "ts", "node_id", "sources") if k not in response]
    if missing:
        raise FailClosedError(f"response lacks receipt fields: {missing}")
    return {"run_id": response["run_id"], "ts": response["ts"],
            "node_id": response["node_id"], "sources": response["sources"]}


# ── Persian rendering (one screen, honest labels) ────────────────────────

_STATUS_FA = {
    STATUS_OK: "تأییدشده از منبع",
    STATUS_DEGRADED: "دیده‌شد — هشدار تأییدشده، نیازمند توجه مالک",
    STATUS_UNKNOWN: "نامعلوم — منبع در دسترس نیست",
    STATUS_ERROR: "منبع نامعتبر — پاسخ بسته شد",
    STATUS_UNKNOWN_COMMAND: "فرمان ناشناخته",
}


def render_text(response: Mapping[str, Any]) -> str:
    """One screen-readable Persian block. Every rendered line carries the
    receipt head, because a glass answer without its receipt is not ours."""
    head = (f"{response['command']} · {response['node_id']} · "
            f"{response['ts']} · run {response['run_id'][:8]}")
    lines = [head, f"وضعیت: {_STATUS_FA.get(response['status'], response['status'])}"]
    for key, value in response["data"].items():
        if key in ("open_prs", "receipts"):
            continue
        shown = "نامعلوم" if value == UNKNOWN else value
        lines.append(f"{key}: {shown}")
    receipts = response["data"].get("receipts")
    if isinstance(receipts, list):
        for r in receipts:
            lines.append(f"رسید {r.get('record_id')} — {r.get('verification_status')}")
    for warning in response["warnings"]:
        lines.append(f"⚠ {warning}")
    lines.append("فقط‌خواندنی — may_authorize=false")
    return "\n".join(lines)
