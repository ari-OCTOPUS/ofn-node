"""Read-only calibration snapshot. Execute exact file bytes over SSH stdin.
No runtime imports, remote writes, generation, metric recomputation, or mutation.
"""
import collections
import datetime
import hashlib
import json
import math
import os
import re
import socket

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def stat_fields(value):
    return {"size_bytes": value.st_size, "inode": value.st_ino,
            "device": value.st_dev, "mtime_ns": value.st_mtime_ns}

def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def safe_label(value):
    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        return value
    return "UNEXPECTED_VALUE_REDACTED"

def summarize(row, line_number):
    if not isinstance(row, dict):
        return {"line": line_number, "record_type": type(row).__name__}
    safe = {}
    for field in ("outcome", "outcome_source"):
        if field in row:
            safe[field] = safe_label(row[field])
    if "calibration_error" in row:
        value = row["calibration_error"]
        if is_number(value):
            safe["calibration_error"] = value if math.isfinite(value) else "NONFINITE"
        elif value is None:
            safe["calibration_error"] = None
        else:
            safe["calibration_error"] = "NONNUMERIC_VALUE_REDACTED"
    if "seq" in row and isinstance(row["seq"], int) and not isinstance(row["seq"], bool):
        safe["seq"] = row["seq"]
    fields = ("loaded_source_revision", "consumer_path", "read_receipt_id",
              "truth_source", "claim_id", "outcome_evidence", "event_time",
              "record_time", "read_snapshot", "snapshot_hash", "prediction_id",
              "cycle_id", "resolved_at", "submitted_at", "as_of", "known_at",
              "scope", "supersedes")
    return {"line": line_number, "kind": safe_label(row.get("kind")),
            "safe_fields": safe, "field_presence": {k: k in row for k in fields}}

out = {"schema": "read_only.calibration_verification.v1",
       "started_at_utc": now(), "hostname": socket.gethostname(),
       "loaded_process_revision": "UNKNOWN", "runtime_imports": 0,
       "remote_writes_requested": 0}
path = "/home/ari/octopus-mesh/calibration/calibration_data.jsonl"
read_start = now()
with open(path, "rb") as stream:
    before = os.fstat(stream.fileno())
    blob = stream.read(before.st_size)
    after = os.fstat(stream.fileno())
out["snapshot"] = {
    "path": path, "read_started_at_utc": read_start, "read_ended_at_utc": now(),
    "fstat_before": stat_fields(before), "fstat_after": stat_fields(after),
    "path_stat_after": stat_fields(os.stat(path)), "read_bytes": len(blob),
    "complete_initial_bound": len(blob) == before.st_size,
    "sha256": hashlib.sha256(blob).hexdigest(), "ends_newline": blob.endswith(b"\n")}
parse_errors = non_dicts = records = metric_fields = numeric_metrics = nonfinite_metrics = 0
unresolved_numeric = unresolved_numeric_outcomes = 0
kinds = collections.Counter()
outcomes = collections.Counter()
outcome_numeric = collections.Counter()
tail = collections.deque(maxlen=3)
for line_number, line in enumerate(blob.splitlines(), 1):
    try:
        row = json.loads(line)
    except Exception:
        parse_errors += 1
        tail.append({"line": line_number, "parse_error": True})
        continue
    records += 1
    tail.append(summarize(row, line_number))
    if not isinstance(row, dict):
        non_dicts += 1
        continue
    kind = safe_label(row.get("kind"))
    kinds[kind] += 1
    has_metric = "calibration_error" in row
    metric_fields += int(has_metric)
    numeric = has_metric and is_number(row["calibration_error"])
    numeric_metrics += int(numeric)
    nonfinite_metrics += int(numeric and not math.isfinite(row["calibration_error"]))
    if row.get("outcome") == "unresolved" and numeric:
        unresolved_numeric += 1
        unresolved_numeric_outcomes += int(row.get("kind") == "outcome")
    if row.get("kind") == "outcome":
        status = safe_label(row.get("outcome"))
        outcomes[status] += 1
        outcome_numeric[status] += int(numeric)
out["counts"] = {
    "line_count": len(blob.splitlines()), "parsed_records": records,
    "parse_errors": parse_errors, "non_dict_records": non_dicts,
    "kind_counts": dict(kinds), "outcome_status_counts_kind_outcome_only": dict(outcomes),
    "calibration_error_field_count_all_dicts": metric_fields,
    "numeric_calibration_error_count_all_dicts": numeric_metrics,
    "nonfinite_numeric_calibration_error_count": nonfinite_metrics,
    "numeric_calibration_error_by_outcome_status_kind_outcome_only": dict(outcome_numeric),
    "unresolved_with_numeric_metric_all_dicts": unresolved_numeric,
    "unresolved_with_numeric_metric_kind_outcome_only": unresolved_numeric_outcomes}
out["last_three_physical_records_sanitized"] = list(tail)
out["interpretation"] = {
    "numeric_definition": "JSON int/float excluding bool; finite/nonfinite separately counted",
    "scope": "Stored values were counted, not recomputed or assumed scientifically valid.",
    "unresolved_numeric": "Co-presence of unresolved outcome and numeric field is measured; validity requires a separately established truth contract.",
    "privacy": "No cycle/prediction IDs, payloads, contacts, or outcome evidence contents emitted."}
out["ended_at_utc"] = now()
print(json.dumps(out, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
