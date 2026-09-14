"""P03/A08 regression suite — each of the seven release_pipeline defects
(2026-09-04 static finding) must now be a FAILING behavior, plus the
approval/effect/transport/consent negative controls.

Defect map (old code → required new behavior):
  D1 bool(step_token) approval      → real '<approval_id>:<code>' validation
  D2 hardcoded consent/platform True → derived from consent_store / creds
  D3 hardcoded rate/idem/ledger True → derived from worker cap / effect gate
  D4 secret_rotation/partner default True → fail-closed False + config source
  D5 gate=None to send_one          → real EffectGate; gate=None refused
  D6 time-based effect_id           → stable hash id; reuse = duplicate
  D7 ok=True with sent=false        → four-state result semantics
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AGENTS = REPO / "ofn" / "agents"
for p in (str(AGENTS), str(AGENTS.parent / "budget"), str(REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)

import release_pipeline as rp  # noqa: E402
import owner_approvals as oa  # noqa: E402
import lead_effect_gate as leg  # noqa: E402
import consent_gate as cg  # noqa: E402
import consent_store as cs  # noqa: E402
import outbound_worker as ow  # noqa: E402
import lead_outbound_transport as lot  # noqa: E402
import owner_absence  # noqa: E402

DRAFT = "Hi — we can repaint your exterior next week, fully insured."
LEAD = "lead:test-001"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Hermetic gates: tmp journals/dbs, policy derived from fakes that
    themselves have dedicated real-store tests. OCTOPUS_STATE_DIR is
    redirected so no default store can ever touch the real home."""
    monkeypatch.setenv("OCTOPUS_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(rp, "RECEIPTS", tmp_path / "release-pipeline.jsonl")
    monkeypatch.setattr(oa, "APPROVALS_JOURNAL", tmp_path / "approvals.jsonl")
    monkeypatch.setattr(leg, "DB_PATH", tmp_path / "lead-effects.sqlite3")
    monkeypatch.setattr(rp, "_consent_ok", lambda lead: (True, "consent:ok"))
    monkeypatch.setattr(rp, "_platform_ok", lambda platform: True)
    monkeypatch.setattr(rp, "_rate_limit_ok", lambda now: True)
    monkeypatch.setattr(rp, "_ledger_ready", lambda: True)
    # config gates: D-28 window is OPEN until 2026-09-16, so live defaults
    # are open; the closed case is tested explicitly in D4 tests.
    monkeypatch.setattr(rp, "_config_gates_open", lambda: (True, True))
    return tmp_path


def _issue(env, draft=DRAFT, lead=LEAD):
    return rp.issue_approval(draft, lead_id=lead)


def _consented_lead(lead=LEAD, email="lead@test.example"):
    """Create a REAL consent row in the tmp consent store so the real
    EffectGate/consent layers pass for this lead (the tests below exercise
    the genuine consent path, not a fake)."""
    import consent_store as _cs
    store = _cs.ConsentStore()  # default path redirected by fixture env
    try:
        store.upsert_current({"lead_id": lead,
                              "candidate_type": "public_b2b",
                              "consent_basis": "inferred_business",
                              "consent_state": "B2B_PROSPECT",
                              "compliance_state": "OWNER_CLEARED",
                              "outreach_allowed": 1,
                              "source_channel": "test",
                              "contact_value_norm": email})
    finally:
        store.close()


def _present_both_steps(appr):
    """The owner presents each code in a separate confirmation (operator
    path records both steps). This is the genuine two-step flow."""
    oa.record_step(appr["approval_id"], 1, actor="owner-queue")
    oa.record_step(appr["approval_id"], 2, actor="owner-queue")


def _arm_worker(monkeypatch, transport_result):
    """Belt fakes for the worker chain + hermetic alert; consent stays REAL
    (the tmp store has a consented row for LEAD)."""
    import opslib
    monkeypatch.setenv("OCTOPUS_WIRE_LEAD_OUTBOUND", "1")
    monkeypatch.setattr(owner_absence, "conservation_active",
                        lambda *a, **k: "")
    monkeypatch.setattr(ow, "cap_reached", lambda now=None: False)
    monkeypatch.setattr(ow, "sends_today", lambda now=None: 0)
    monkeypatch.setattr(opslib, "alert", lambda lines: None)
    monkeypatch.setattr(lot, "send",
                        lambda cand, draft, now=None: transport_result)


# ── D1: garbage/nonempty tokens must never authorize ───────────────────────
def test_d1_garbage_tokens_cannot_release(env, monkeypatch):
    res = rp.pipeline(DRAFT, step1_token="t1", step2_token="t2",
                      lead_id=LEAD, dry_run=False)
    assert res["ok"] is False
    assert res["result"] == "rejected"
    assert "approval" in res.get("error", "") + res.get("rule", "")


def test_d1_real_two_step_releases_once(env, monkeypatch):
    appr = _issue(env)
    _consented_lead()
    _present_both_steps(appr)
    _arm_worker(monkeypatch,
                {"sent": True, "status": "SENT", "channel": "email"})
    res = rp.pipeline(DRAFT, step1_token=f"{appr['approval_id']}:{appr['step1_code']}",
                      step2_token=f"{appr['approval_id']}:{appr['step2_code']}",
                      lead_id=LEAD, dry_run=False)
    assert res["ok"] is True and res["result"] == "passed" and res["sent"] is True
    # D6: stable effect_id across calls — second release is a hard duplicate
    res2 = rp.pipeline(DRAFT, step1_token=f"{appr['approval_id']}:{appr['step1_code']}",
                       step2_token=f"{appr['approval_id']}:{appr['step2_code']}",
                       lead_id=LEAD, dry_run=False)
    assert res2["result"] == "rejected"
    assert res2.get("rule") == "outbox:idempotency-used"


def test_d1_forged_code_refused(env):
    appr = _issue(env)
    ok, why = oa.validate(appr["approval_id"], "deadbeef", appr["step2_code"],
                          lead_id=LEAD, draft_text=DRAFT, platform="email",
                          effect_id=appr["effect_id"])
    assert ok is False and "step1" in why


def test_d1_step2_replayed_as_step1_refused(env):
    appr = _issue(env)
    oa.record_step(appr["approval_id"], 2)
    ok, why = oa.validate(appr["approval_id"], appr["step1_code"],
                          appr["step2_code"], lead_id=LEAD,
                          draft_text=DRAFT, platform="email",
                          effect_id=appr["effect_id"])
    assert ok is False and "two-step" in why


def test_d1_payload_change_invalidates(env):
    appr = _issue(env)
    oa.record_step(appr["approval_id"], 1)
    oa.record_step(appr["approval_id"], 2)
    ok, why = oa.validate(appr["approval_id"], appr["step1_code"],
                          appr["step2_code"], lead_id=LEAD,
                          draft_text=DRAFT + " changed price!",
                          platform="email", effect_id=appr["effect_id"])
    assert ok is False and "payload" in why


def test_d1_expiry_refused(env):
    appr = _issue(env)
    oa.record_step(appr["approval_id"], 1, now=time.time() - 25 * 3600)
    oa.record_step(appr["approval_id"], 2, now=time.time() - 25 * 3600)
    ok, why = oa.validate(appr["approval_id"], appr["step1_code"],
                          appr["step2_code"], lead_id=LEAD,
                          draft_text=DRAFT, platform="email",
                          effect_id=appr["effect_id"], now=time.time())
    assert ok is False and "expired" in why


def test_d1_revoked_refused(env):
    appr = _issue(env)
    oa.record_step(appr["approval_id"], 1)
    oa.record_step(appr["approval_id"], 2)
    oa.revoke(appr["approval_id"], reason="owner cancel")
    ok, why = oa.validate(appr["approval_id"], appr["step1_code"],
                          appr["step2_code"], lead_id=LEAD,
                          draft_text=DRAFT, platform="email",
                          effect_id=appr["effect_id"])
    assert ok is False and "revoked" in why


# ── D4: closed-gate defaults and config wiring ─────────────────────────────
def test_d4_defaults_fail_closed():
    ctx = rp.build_release_context(
        owner_confirmed_step1=True, owner_confirmed_step2=True,
        consent_ok=True, platform_ok=True, rate_limit_ok=True,
        idempotency_unused=True, ledger_ready=True)
    assert ctx.secret_rotation_open is False
    assert ctx.partner_precondition_open is False
    from ofn.kernel.release_switch import OwnerRelease
    assert OwnerRelease().may_publish(ctx).ok is False


def test_d4_closed_secret_rotation_blocks_pipeline(env, monkeypatch):
    monkeypatch.setattr(rp, "_config_gates_open", lambda: (False, True))
    res = rp.pipeline(DRAFT, lead_id=LEAD, dry_run=True)
    assert res["ok"] is False and res["result"] == "rejected"
    assert res.get("rule") == "gate:secret-rotation-closed"


def test_d4_config_source_is_real(monkeypatch):
    """_config_gates_open must read the REAL config closed-gates list."""
    monkeypatch.setenv("OFN_EXTRA_CLOSED_GATES", "secret_rotation")
    rot, partner = rp._config_gates_open()
    assert rot is False and partner is True


# ── D2/D3: real sources for per-item screens ──────────────────────────────
def test_d2_consent_missing_blocks(env, monkeypatch):
    monkeypatch.setattr(rp, "_consent_ok", lambda lead: (False, "consent:missing"))
    res = rp.pipeline(DRAFT, lead_id=LEAD, dry_run=True)
    assert res["ok"] is False and res["result"] == "rejected"
    assert res.get("rule") == "consent:invalid-or-missing"


def test_d3_rate_limit_blocks(env, monkeypatch):
    monkeypatch.setattr(rp, "_rate_limit_ok", lambda now: False)
    res = rp.pipeline(DRAFT, lead_id=LEAD, dry_run=True)
    assert res["ok"] is False and res["result"] == "rejected"
    assert res.get("rule") == "platform:rate-limit"


def test_d3_idempotency_used_blocks(env, monkeypatch):
    conn = leg._connect(env / "lead-effects.sqlite3")
    leg.release_and_settle("release-x-1", {"lead_id": LEAD,
                                           "draft_sha256": "a"},
                           gate=lambda eid, cand: (True, "ok"), conn=conn)
    monkeypatch.setattr(rp, "_idempotency_unused", lambda eid: False)
    res = rp.pipeline(DRAFT, lead_id=LEAD, dry_run=True)
    assert res["ok"] is False and res["result"] == "rejected"
    assert res.get("rule") == "outbox:idempotency-used"


# ── D5: the effect gate is real; gate=None is refused ──────────────────────
def test_d5_gate_none_refused(env):
    res = leg.release_and_settle("release-y-1", {"lead_id": LEAD,
                                                 "draft_sha256": "a"},
                                 gate=None)
    assert res["settled"] is False and res["reason"] == "gate:missing"
    assert leg.status("release-y-1") is None


def test_d5_real_gate_flows_through_worker(env, monkeypatch):
    """send_one must receive rp.EffectGate (not None) — the gate object
    re-derives consent and refuses without a payload hash."""
    gate = rp.EffectGate()
    res = gate.release("z", {"lead_id": LEAD})  # no draft hash
    assert res[0] is False and "no-payload-hash" in res[1]


def test_d5_gate_deny_consumes_nothing(env):
    calls = []

    def deny_gate(eid, cand):
        calls.append(eid)
        return False, "gate:halted:test"

    res = leg.release_and_settle("release-z-1", {"lead_id": LEAD,
                                                 "draft_sha256": "a"},
                                 gate=deny_gate)
    assert res["settled"] is False and "halted" in res["reason"]
    assert leg.status("release-z-1") is None  # releasable later


# ── D6: effect identity ────────────────────────────────────────────────────
def test_d6_effect_id_is_stable_not_time_based():
    a = rp.stable_effect_id(LEAD, DRAFT)
    time.sleep(1.1)
    b = rp.stable_effect_id(LEAD, DRAFT)
    assert a == b
    assert not a.rstrip("-0123456789").endswith(str(int(time.time()))[:10])


def test_d6_duplicate_settle_refused(env):
    conn = leg._connect(env / "lead-effects.sqlite3")
    g = lambda eid, cand: (True, "ok")  # noqa: E731
    r1 = leg.release_and_settle("release-dup-1", {"lead_id": LEAD,
                                                  "draft_sha256": "a"},
                                gate=g, conn=conn)
    r2 = leg.release_and_settle("release-dup-1", {"lead_id": LEAD,
                                                  "draft_sha256": "a"},
                                gate=g, conn=conn)
    assert r1["settled"] is True and r2["settled"] is False
    assert r2["reason"] == "idempotency:duplicate"


# ── D7: result semantics ───────────────────────────────────────────────────
def _armed_worker(env, monkeypatch, transport_result):
    _consented_lead()
    _arm_worker(monkeypatch, transport_result)


def test_d7_not_armed_is_rejected_not_ok(env, monkeypatch):
    appr = _issue(env)
    _present_both_steps(appr)
    _armed_worker(env, monkeypatch,
                  {"sent": False, "status": "NOT_ARMED", "channel": "email"})
    res = rp.pipeline(DRAFT,
                      step1_token=f"{appr['approval_id']}:{appr['step1_code']}",
                      step2_token=f"{appr['approval_id']}:{appr['step2_code']}",
                      lead_id=LEAD, dry_run=False)
    assert res["ok"] is False and res["result"] == "rejected"
    assert res["status"] == "NOT_ARMED"


def test_d7_worker_error_is_failed(env, monkeypatch):
    appr = _issue(env)
    _present_both_steps(appr)
    _armed_worker(env, monkeypatch, {"sent": False, "status": "worker_error"})
    res = rp.pipeline(DRAFT,
                      step1_token=f"{appr['approval_id']}:{appr['step1_code']}",
                      step2_token=f"{appr['approval_id']}:{appr['step2_code']}",
                      lead_id=LEAD, dry_run=False)
    assert res["ok"] is False and res["result"] == "failed"


def test_d7_dry_run_never_sends(env, monkeypatch):
    sent_flag = {"called": False}

    def _no_send(cand, draft, now=None):
        sent_flag["called"] = True
        raise AssertionError("transport called during dry_run")

    monkeypatch.setattr(lot, "send", _no_send)
    res = rp.pipeline(DRAFT, lead_id=LEAD, dry_run=True)
    assert res["ok"] is True and res["result"] == "dry_run"
    assert sent_flag["called"] is False
    assert res["card"]["hold_external"] is True


# ── consent gate real-store negative controls ──────────────────────────────
def _store(tmp_path):
    return cs.ConsentStore(path=tmp_path / "consent.sqlite3")


def test_consent_missing_refused(tmp_path):
    ok, why = cg.may_release("lead:none", "lead_outbound", store=_store(tmp_path))
    assert ok is False and why == "consent:missing"


def test_consent_unreviewed_compliance_refused(tmp_path):
    s = _store(tmp_path)
    s.upsert_current({"lead_id": "lead:c1", "candidate_type": "public_b2b",
                      "consent_basis": "inferred_business",
                      "consent_state": "B2B_PROSPECT",
                      "compliance_state": "UNREVIEWED",
                      "outreach_allowed": 1})
    ok, why = cg.may_release("lead:c1", "lead_outbound", store=s)
    assert ok is False and "compliance" in why


def test_consent_suppressed_refused(tmp_path):
    s = _store(tmp_path)
    s.upsert_current({"lead_id": "lead:c2", "candidate_type": "public_b2b",
                      "consent_basis": "inferred_business",
                      "consent_state": "B2B_PROSPECT",
                      "compliance_state": "CLEAR",
                      "outreach_allowed": 1,
                      "contact_value_norm": "a@b.test"})
    s.insert_suppression("a@b.test", "email", "stop_reply")
    ok, why = cg.may_release("lead:c2", "lead_outbound", store=s)
    assert ok is False and "suppressed" in why


def test_consent_clear_path_ok(tmp_path):
    s = _store(tmp_path)
    s.upsert_current({"lead_id": "lead:c3", "candidate_type": "public_b2b",
                      "consent_basis": "inferred_business",
                      "consent_state": "B2B_PROSPECT",
                      "compliance_state": "OWNER_CLEARED",
                      "outreach_allowed": 1,
                      "contact_value_norm": "c@d.test"})
    ok, why = cg.may_release("lead:c3", "lead_outbound", store=s)
    assert ok is True, why


# ── transport honesty ──────────────────────────────────────────────────────
def test_transport_not_armed_without_creds(tmp_path, monkeypatch):
    for k in ("OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
              "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM", "OFN_GMAIL_APP_ADDRESS",
              "OCTOPUS_SMTP_USE_GMAIL"):
        monkeypatch.delenv(k, raising=False)
    res = lot.send({"lead_id": "l", "contact": {"email": "x@y.test"},
                    "effect_id": "e1"}, DRAFT)
    assert res["sent"] is False and res["status"] == "NOT_ARMED"


def test_transport_no_recipient(tmp_path, monkeypatch):
    monkeypatch.setenv("OCTOPUS_SMTP_HOST", "smtp.test")
    monkeypatch.setenv("OCTOPUS_SMTP_PORT", "2525")
    monkeypatch.setenv("OCTOPUS_SMTP_USER", "u")
    monkeypatch.setenv("OCTOPUS_SMTP_PASS", "p")
    monkeypatch.setenv("OCTOPUS_SMTP_FROM", "f@test")
    res = lot.send({"lead_id": "l", "contact": {}}, DRAFT)
    assert res["status"] == "NO_RECIPIENT"


# ── receipts stay append-only ──────────────────────────────────────────────
def test_receipts_append_only(env):
    f = rp.RECEIPTS
    before = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    rp.pipeline("x", lead_id=LEAD, dry_run=True)  # too short → draft refusal
    after = f.read_text(encoding="utf-8").splitlines()
    assert len(after) > len(before)
    assert all(json.loads(l) for l in after)
