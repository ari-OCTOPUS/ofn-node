"""test_intel_spine.py — intel_spine event schema و redaction verification.

تأیید می‌کند که:
۱. event ثبت می‌شود و event_id برمی‌گردد
۲. PII/token redact می‌شود (نه raw)
۳. append-only کار می‌کند
۴. flag off → None برمی‌گردد
۵. error ثبت می‌شود حتی اگر flag off باشد ( ولی redacted)
۶. read_recent کار می‌کند
۷. stats کار می‌کند
۸. هیچ outbound ندارد

no network، no real telegram.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

# state dir را به temp redirect کن
_TMP = Path(tempfile.mkdtemp())
os.environ["OCTOPUS_INTERACTION_LOG"] = "1"

# patch _STATE before import
import intel_spine
intel_spine._STATE = _TMP / "intel_spine_test"

results = {"pass": 0, "fail": 0, "details": []}


def check(name, cond):
    if cond:
        results["pass"] += 1
        results["details"].append(f"  ✅ {name}")
    else:
        results["fail"] += 1
        results["details"].append(f"  ❌ {name}")


def main():
    # ۱. event ثبت
    eid = intel_spine.log_event(
        source="telegram", direction="in", actor="9999999999",
        text="hello world this is a test message",
        intent_guess="status_query", d_level="D0")
    check("event logged with id", eid is not None)

    # ۲. PII redact شده
    events = intel_spine.read_recent("events", 1)
    check("event readable", len(events) == 1)
    if events:
        ev = events[0]
        check("actor_ref is hash not raw", "9999999999" not in ev.get("actor_ref", "9999999999"))
        check("text is redacted", "hello world" not in ev.get("text_redacted", "hello world"))
        check("text_redacted starts with <redacted", ev.get("text_redacted", "").startswith("<redacted"))

    # ۳. interaction
    iid = intel_spine.log_interaction(
        source="webapp", direction="out", actor="user1",
        channel="dm", text="sensitive data here", kind="response")
    check("interaction logged", iid is not None)
    interactions = intel_spine.read_recent("interactions", 1)
    check("interaction readable", len(interactions) == 1)

    # ۴. fact با provenance
    fid = intel_spine.log_fact(
        claim="arm_gate_enforcing is false",
        evidence=["ORGANISM-STATE.json:76"],
        confidence=1.0, source="deep_scan")
    check("fact logged", fid is not None)

    # ۵. belief
    bid = intel_spine.log_belief(
        belief="arm_gate should be enabled",
        basis=[fid] if fid else [],
        confidence=0.9)
    check("belief logged", bid is not None)

    # ۶. decision
    did = intel_spine.log_decision(
        context="P0 arm_gate fix",
        chosen="enable OCTOPUS_REQUIRE_ARM",
        level="D4", risk="medium",
        rollback="unset OCTOPUS_REQUIRE_ARM")
    check("decision logged", did is not None)

    # ۷. proposal (shadow)
    pid = intel_spine.log_proposal(
        title="Enable arm_gate",
        description="Set OCTOPUS_REQUIRE_ARM=1",
        risk="medium")
    check("proposal logged", pid is not None)

    # ۸. flag off → None
    intel_spine._flag_on = lambda: False
    none_eid = intel_spine.log_event(source="test", direction="in")
    check("flag off returns None", none_eid is None)

    # ۹. error همیشه ثبت (redacted)
    intel_spine._flag_on = lambda: False
    err_id = intel_spine.log_error("some secret token=abc123 leaked", "context")
    check("error logged even when flag off", err_id is not None)
    errors = intel_spine.read_recent("errors", 1)
    if errors:
        check("error redacted (no raw token)", "abc123" not in errors[0].get("error", "abc123"))

    # ۱۰. stats
    s = intel_spine.stats()
    check("stats has keys", "events" in s and "interactions" in s)

    # ۱۱. no outbound — verify no network attribute/function
    module_attrs = dir(intel_spine)
    has_network = any("requests" in a or "http" in a.lower() or "socket" in a.lower() for a in module_attrs)
    check("no network/http/socket in module", not has_network)

    print("test_intel_spine — event schema + redaction + no-outbound")
    for d in results["details"]:
        print(d)
    print(f"\nPass: {results['pass']}, Fail: {results['fail']}")
    return results["fail"] == 0


if __name__ == "__main__":
    ok = main()
    # cleanup
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)
    sys.exit(0 if ok else 1)
