"""One owner inbox and proposal lineage. No execution or approval-by-silence."""
from pathlib import Path
import re
from shadow_homeostasis.canonical import digest
from .checkpoint import atomic_bytes

PROTECTED = {"shadow_homeostasis/metacontrol.py", "shadow_homeostasis/registry.py"}


def request_owner(store, issue, evidence):
    issue_id = "owner:" + digest({"issue": issue})
    store.append_record("owner_request", issue_id, {"issue_id": issue_id, "issue": issue,
                        "state": "PENDING", "executable": False})
    store.append_record("owner_evidence", issue_id + ":evidence:" + digest(evidence),
                        {"issue_id": issue_id, "evidence": evidence, "executable": False})
    return issue_id


def cancel_owner(store, issue_id, reason):
    requests = {r["event_id"] for r in store.records if r["kind"] == "owner_request"}
    if issue_id not in requests or not reason:
        raise ValueError("existing issue and cancellation reason required")
    return store.append_record("owner_cancel", "cancel:" + issue_id,
                               {"issue_id": issue_id, "state": "CANCELLED", "reason": reason, "executable": False})


def owner_states(store):
    records = store.records
    states = {r["event_id"]: dict(r["payload"], evidence=[]) for r in records if r["kind"] == "owner_request"}
    for rec in records:
        if rec["kind"] == "owner_evidence":
            states[rec["payload"]["issue_id"]]["evidence"].append(rec["payload"]["evidence"])
        if rec["kind"] == "owner_cancel":
            states[rec["payload"]["issue_id"]] = dict(states[rec["payload"]["issue_id"]], **rec["payload"])
    return [states[key] for key in sorted(states)]


def write_inbox(store, path, budget=None):
    lines = ["# EXEC-001 owner inbox", "", "Silence is PENDING, never approval. No item can execute code.", ""]
    for item in owner_states(store):
        # Render untrusted text inside a JSON string; never interpret it as instructions.
        from shadow_homeostasis.canonical import canonical
        lines.append("- " + item["issue_id"] + " | " + item["state"] + " | " + canonical(item["issue"]))
    atomic_bytes(path, ("\n".join(lines) + "\n").encode("utf-8"), budget)


def validate_proposal(proposal):
    for key in ("parent_manifest_hash", "candidate_source_hash", "test_receipts", "rollback_refs", "changes"):
        if not proposal.get(key):
            raise ValueError("missing ancestry/tests/rollback: " + key)
    for key in ("parent_manifest_hash", "candidate_source_hash"):
        if not isinstance(proposal[key], str) or not re.fullmatch(r"[a-f0-9]{64}", proposal[key]):
            raise ValueError("SHA-256 required: " + key)
    for key in ("test_receipts", "rollback_refs", "changes"):
        if not isinstance(proposal[key], list) or not proposal[key]:
            raise ValueError("nonempty list required: " + key)
    if not all(isinstance(ref, str) and ref for key in ("test_receipts", "rollback_refs") for ref in proposal[key]):
        raise ValueError("receipt and rollback path strings required")
    for change in proposal["changes"]:
        rel = change["path"].replace("\\", "/")
        segments = rel.split("/")
        if any(not s or s in (".", "..") or s != s.rstrip(" .") for s in segments):
            raise ValueError("proposal path alias rejected")
        if rel.casefold() in PROTECTED:
            raise ValueError("protected-file change rejected")
        if rel.startswith("/") or ":" in rel or ".." in rel.split("/"):
            raise ValueError("proposal path escape")
        if not change.get("new_hash") or (change.get("operation") != "add" and not change.get("parent_hash")):
            raise ValueError("change hashes required")
        if change.get("operation") not in ("add", "modify"):
            raise ValueError("unsupported change operation")
        for key in ("new_hash",) if change["operation"] == "add" else ("new_hash", "parent_hash"):
            if not isinstance(change[key], str) or not re.fullmatch(r"[a-f0-9]{64}", change[key]):
                raise ValueError("invalid change hash")
    return dict(proposal, state="CANDIDATE_NOT_DEPLOYED", executable=False,
                validation_scope="structural; bundle builder separately verifies local file receipts")
