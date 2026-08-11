#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_outbound_https — طراحیِ اسکلتِ دسترسیِ محدودِ خروجیِ HTTPS (۲۰۲۶-۰۸-۰۷).

ادعاهای باربر:
  ۱) فلگ خاموش (پیش‌فرض) → submit() هیچ jobی نمی‌سازد، هیچ تماسی نمی‌رود.
  ۲) allow-list خالی/غایب → fail-closed BLOCKED، نه allow-all.
  ۳) دامنه/متدِ خارج از allow-list → BLOCKED، صفر job.
  ۴) submit() هرگز خودش تماسِ شبکه‌ای نمی‌زند — فقط execute_if_approved می‌زند،
     و فقط بعد از approve.
  ۵) execute_if_approved قبل از approve → PENDING (صفر تماسِ شبکه).
  ۶) idempotency: دو بار صدازدنِ execute_if_approved بعد از approve دوبار
     نمی‌فرستد (دومی ALREADY_DONE).
  ۷) رسیدها content-free‌اند — هرگز URL/بدنه/headerِ کامل در events.jsonl.

mutation-gate: اگر _check_allowlist خالی‌بودن را «مجاز» تفسیر کند، تستِ
t_empty_allowlist_is_fail_closed قرمز می‌شود.
"""
import json
import os
import sys
from pathlib import Path
from unittest import mock

import harness

ENV = harness.setup("outbound-https")

_OPS_SELF = Path(__file__).resolve().parent.parent
for _p in (str(_OPS_SELF / "integrations"), str(_OPS_SELF / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import outbound_https as oh  # noqa: E402
import approval_store  # noqa: E402


def _wire_approval_port():
    """Bridge outbound_https to the real approval_store via injectable port.

    2026-08-11: _LocalApprovalStore deleted. outbound_https now requires
    an injected approval port. This helper wires the telegram_center
    approval_store as the port so existing behavioral tests continue
    exercising the real store logic."""
    oh._set_approval_port({
        "add_pending": approval_store.add_pending,
        "get": approval_store.get,
        "mark_done": approval_store.mark_done,
    })


class _Flag:
    def __init__(self, name, val):
        self.name, self.val = name, val

    def __enter__(self):
        self.old = os.environ.get(self.name)
        if self.val is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.val
        return self

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(self.name, None)
        else:
            os.environ[self.name] = self.old


def _reset():
    for p in (oh._ALLOWLIST_PATH, oh._EVENTS_PATH):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        approval_store._APPROVALS_JSON.unlink()
    except OSError:
        pass
    _wire_approval_port()


def _write_allowlist(domains):
    oh._ALLOWLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    oh._ALLOWLIST_PATH.write_text(
        json.dumps({"schema": "outbound-https-allowlist.v1", "domains": domains}),
        "utf-8")


# ════════════════════════════════════════════════════════════════════════════
# (۱) فلگ خاموش
# ════════════════════════════════════════════════════════════════════════════
def t_flag_off_submit_creates_nothing():
    _reset()
    with _Flag(oh.FLAG, None):
        r = oh.submit("POST", "https://api.example.com/x")
    assert r == {"ok": False, "status": "OFF", "reason": "flag-off"}, r
    assert approval_store.load_pending() == []


# ════════════════════════════════════════════════════════════════════════════
# (۲) allow-list خالی/غایب — fail-closed
# ════════════════════════════════════════════════════════════════════════════
def t_empty_allowlist_is_fail_closed():
    _reset()
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    assert r["ok"] is False and r["status"] == "BLOCKED", r
    assert r["reason"] == "allowlist_empty_or_missing", r
    assert approval_store.load_pending() == [], "شکست نباید job بسازد"


def t_domain_not_in_allowlist_is_blocked():
    _reset()
    _write_allowlist({"other.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    assert r["ok"] is False and r["reason"] == "domain_not_allowlisted", r


def t_method_not_allowed_for_domain_is_blocked():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["GET"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    assert r["ok"] is False and r["reason"] == "method_not_allowlisted_for_domain", r


def t_http_scheme_is_rejected_https_only():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "http://api.example.com/x")
    assert r["ok"] is False and r["reason"] == "https_only", r


# ════════════════════════════════════════════════════════════════════════════
# (۳)+(۴) submit موفق → صفر تماسِ شبکه، job واقعی در approval_store
# ════════════════════════════════════════════════════════════════════════════
def t_submit_never_calls_the_network_itself():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        with mock.patch("urllib.request.urlopen") as m:
            r = oh.submit("POST", "https://api.example.com/x", purpose="test")
            assert not m.called, "submit هرگز نباید شبکه بزند"
    assert r["ok"] is True and r["status"] == "PENDING_APPROVAL", r
    jobs = approval_store.load_pending()
    assert len(jobs) == 1 and jobs[0]["type"] == "outbound_http", jobs
    assert jobs[0]["risk"] == "high", jobs[0]
    assert jobs[0]["action_sha256"] == oh._action_sha256(
        json.loads(oh._job_path(r["job_id"]).read_text("utf-8")))


# ════════════════════════════════════════════════════════════════════════════
# (۵) execute قبل از approve
# ════════════════════════════════════════════════════════════════════════════
def t_execute_before_approval_is_pending_no_network():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    with mock.patch("urllib.request.urlopen") as m:
        out = oh.execute_if_approved(r["job_id"])
        assert not m.called
    assert out == {"status": "PENDING"}, out


def t_execute_unknown_job_is_not_found():
    _reset()
    assert oh.execute_if_approved("nope-never-existed") == {"status": "NOT_FOUND"}


def t_execute_rejected_job_stays_rejected():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    approval_store.reject(r["job_id"])
    with mock.patch("urllib.request.urlopen") as m:
        out = oh.execute_if_approved(r["job_id"])
        assert not m.called
    assert out == {"status": "REJECTED"}, out


# ════════════════════════════════════════════════════════════════════════════
# (۶) approve → دقیقاً یک تلاش، idempotent
# ════════════════════════════════════════════════════════════════════════════
def t_approved_job_sends_exactly_once_then_idempotent():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    jid = r["job_id"]
    approval_store.approve(jid)

    class _FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    with mock.patch("urllib.request.urlopen", return_value=_FakeResp()) as m:
        out1 = oh.execute_if_approved(jid)
        assert m.call_count == 1, m.call_count
    assert out1 == {"status": "SENT", "http_status": 200}, out1

    with mock.patch("urllib.request.urlopen") as m2:
        out2 = oh.execute_if_approved(jid)
        assert not m2.called, "بعد از mark_done دوباره نباید بفرستد"
    assert out2["status"] == "ALREADY_DONE", out2


def t_expired_approval_is_denied_without_network():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x", body="approved-body")
    jid = r["job_id"]
    approval_store.approve(jid)
    state = approval_store._load_octopus_approvals()
    state["approved"][0]["expires_epoch"] = 0
    approval_store._save_octopus_approvals(state)
    with mock.patch("urllib.request.urlopen") as m:
        out = oh.execute_if_approved(jid)
        assert not m.called
    assert out == {"status": "FAILED", "reason": "approval_expired"}, out


def t_approved_job_with_changed_spec_is_denied_without_network():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x", body="approved-body")
    jid = r["job_id"]
    approval_store.approve(jid)
    spec_path = oh._job_path(jid)
    changed = json.loads(spec_path.read_text("utf-8"))
    changed["body"] = "changed-after-approval"
    spec_path.write_text(json.dumps(changed), "utf-8")
    with mock.patch("urllib.request.urlopen") as m:
        out = oh.execute_if_approved(jid)
        assert not m.called
    assert out == {"status": "FAILED", "reason": "approval_action_mismatch"}, out
    assert approval_store.get(jid)["status"] == "approved"


def t_network_failure_marks_done_not_retryable():
    """۲۰ ثانیه timeout ثابت، بدونِ retry — شکست باید ثبت و done شود، نه
    برای همیشه approved بماند و هر تیک دوباره تلاش کند."""
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        r = oh.submit("POST", "https://api.example.com/x")
    jid = r["job_id"]
    approval_store.approve(jid)
    with mock.patch("urllib.request.urlopen", side_effect=OSError("boom")):
        out = oh.execute_if_approved(jid)
    assert out["status"] == "FAILED", out
    rec = approval_store.get(jid)
    assert rec["status"] == "done", "شکست هم باید done شود، نه approved بماند"


# ════════════════════════════════════════════════════════════════════════════
# (۷) رسیدِ content-free
# ════════════════════════════════════════════════════════════════════════════
def t_receipts_never_contain_full_url_or_body():
    _reset()
    _write_allowlist({"api.example.com": {"methods": ["POST"]}})
    with _Flag(oh.FLAG, "1"):
        oh.submit("POST", "https://api.example.com/secret-path?token=abc123",
                 body="super-secret-body-content", purpose="test")
    raw = oh._EVENTS_PATH.read_text("utf-8") if oh._EVENTS_PATH.exists() else ""
    assert "secret-path" not in raw, raw
    assert "super-secret-body-content" not in raw, raw
    assert "token=abc123" not in raw, raw
    assert "api.example.com" in raw, "دامنه (نه مسیر/کوئری) باید در رسید بماند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_outbound_https: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
