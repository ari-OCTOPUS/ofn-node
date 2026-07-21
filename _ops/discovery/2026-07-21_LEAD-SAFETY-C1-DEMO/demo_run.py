#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo_run.py — LEAD-SAFETY-C1 dry-run demo (worktree-only, sandboxed, ZERO real send).

مالک fork (1) را خواست: یک لیدِ synthetic از قوسِ reachable عبور کند و **قبل از هر ارسال بایستد**،
با receiptهای خواندنی. این درایور همه‌چیز را در یک OPS_DIRِ موقت (sandbox) اجرا می‌کند تا نه درختِ
زنده، نه stateِ tracked لمس شود. فلگ‌ها فقط در env همین پروسه set می‌شوند (نه فایلِ زنده، نه PAPER_FULL).

قوانین: صفر شبکه · transport = NOT_ARMED · STOP دست‌نخورده (STOPِ تستی در sandbox ساخته/پاک می‌شود) ·
هیچ شماره/ایمیلِ واقعیِ غریبه (فقط fixtureِ تست با مقدارِ placeholder).

اجرا:  python -X utf8 demo_run.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# ── sandbox: OPS_DIR موقت پیش از هر import (opslib.STATE_DIR از این خوانده می‌شود) ──
_SANDBOX = tempfile.mkdtemp(prefix="lead-c1-demo-")
os.environ["OPS_DIR"] = _SANDBOX
# فلگ‌های worktree را موقتاً arm کن (فقط env همین پروسه)
os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"    # همچنان NOT_ARMED (transport مسلح نیست)

_OPS = Path(__file__).resolve().parents[2]        # …/_ops
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                       # noqa: E402
import consent_firewall as cf       # noqa: E402
import lead_candidate_inbox as lci  # noqa: E402
import lead_sense                   # noqa: E402
import lead_scorer                  # noqa: E402
import chrono                       # noqa: E402
import lead_effect_gate as leg      # noqa: E402
import outbound_worker as ow        # noqa: E402

RESULTS: list[dict] = []


def _step(n, name, passed, detail):
    RESULTS.append({"step": n, "name": name, "pass": bool(passed), "detail": detail})
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {n}. {name} :: {detail}")


def _gate():
    db = chrono.ChronoDB(str(opslib.STATE_DIR / "chrono.db"))
    return chrono.EffectorGate(db)


def _events_tail(n=40):
    p = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text("utf-8").splitlines():
        try:
            r = json.loads(line)
            rows.append({"event_type": r.get("event_type"), "correlation_id": r.get("correlation_id"),
                         "outcome": (r.get("payload") or {}).get("outcome"),
                         "kind": (r.get("payload") or {}).get("kind")})
        except ValueError:
            continue
    return rows[-n:]


def main():
    print("=" * 72)
    print("LEAD-SAFETY-C1 DRY-RUN DEMO — worktree-only sandbox")
    print("sandbox OPS_DIR:", _SANDBOX)
    print("flags armed (this process only):", "LEAD_CANDIDATES=1 LEAD_OUTBOUND=1")
    print("=" * 72)
    gate = _gate()

    # ── PROBE 1: لیدِ SYNTHETIC (payloadِ اصلی) — از قوسِ داخلی عبور، در گیت DENY ──
    print("\n── PROBE 1: synthetic lead (must traverse internal arc, then be BLOCKED at gate) ──")
    syn = {"schema_version": "1.1",
           "source": {"channel": "synthetic_test", "source_id": "owner", "external_id": "DEMO-SYN-1"},
           "candidate_type": "consented_inbound",
           "consent": {"basis": "explicit", "evidence": "synthetic_demo"},
           "request": {"scope_text": "TEST | interior painting | Mosman"}}
    r1 = lci.submit_candidate(syn, source_id="owner")
    _step(1, "submit_candidate → firewall receipt",
          r1.get("ok") and r1.get("status") == "accepted",
          f"status={r1.get('status')} lead_id={r1.get('lead_id')} outreach_allowed={r1.get('outreach_allowed')}")
    seen = lead_sense.read_inbox()
    lands = any(d.get("lead_id") == r1.get("lead_id") and d.get("description") for _, d in seen)
    top_names = sorted(p.name for p, _ in seen)
    _step(2, "file lands where lead_sense expects (uuid.json, not LD-*)",
          lands and all(not n.startswith("LD-") for n in top_names),
          f"lead_sense sees {top_names}")
    # scorer (تا جایی که هست، بدونِ spam)
    the = next((d for _, d in seen if d.get("lead_id") == r1.get("lead_id")), {})
    sc = lead_scorer.LeadScorer().score(the).as_dict()
    _step(3, "scorer runs on the candidate (no human spam)",
          "score" in sc or "action" in sc, f"score={sc.get('score')} action={sc.get('action')}")
    # کارت/لاگِ قابل‌مشاهدهٔ اپراتور = receiptهای events.jsonl
    ev = _events_tail()
    _step(4, "operator-visible audit receipts written",
          any(e["event_type"] == "lead.candidate.received" for e in ev),
          f"{len([e for e in ev if e['event_type']=='lead.candidate.received'])} received receipt(s)")
    # effect-gate: authorize → may_release → attempt (synthetic باید DENY شود)
    eid1 = gate.request("lead_outbound", r1.get("lead_id") or "syn", beat=1)
    leg.authorize(eid1, r1.get("lead_id") or "syn", "owner-verdict-token-1")
    mr1 = leg.may_release(eid1, syn, gate=gate)
    out1 = ow.send_one(eid1, syn, gate=gate)
    _step(5, "authorize→may_release: SYNTHETIC blocked at gate (defense in depth)",
          mr1.get("allow") is False and "synthetic" in mr1.get("reason", ""),
          f"may_release={mr1.get('reason')} · outbound={out1.get('status')}")

    # ── PROBE 2: fixtureِ تستِ consented (placeholder) — تا NOT_ARMED برسد ──
    print("\n── PROBE 2: consented TEST-FIXTURE (owner placeholder) → gate ALLOW → transport NOT_ARMED ──")
    fix = {"schema_version": "1.1",
           "source": {"channel": "telegram_manual", "source_id": "owner", "external_id": "DEMO-FIX-1"},
           "candidate_type": "consented_inbound",
           "consent": {"basis": "explicit", "evidence": "owner_test_fixture"},
           "contact": {"preferred_channel": "sms", "phone": "TEST-FIXTURE-NOT-REAL"},
           "request": {"scope_text": "owner test fixture — placeholder contact, never a stranger"}}
    r2 = lci.submit_candidate(fix, source_id="owner")
    eid2 = gate.request("lead_outbound", r2.get("lead_id") or "fix", beat=1)
    leg.authorize(eid2, r2.get("lead_id") or "fix", "owner-verdict-token-2")
    out2 = ow.send_one(eid2, fix, gate=gate)
    _step(6, "outbound_worker returns NOT_ARMED (gate allowed a sendable lead; transport cannot send)",
          out2.get("ok") is True and out2.get("sent") is False and out2.get("status") == "NOT_ARMED",
          f"outbound={out2}")

    # ── PROBE 3: market_signal — firewall باید outreach را رد کند ──
    print("\n── PROBE 3: market_signal (SECOND check) → refused for outreach ──")
    sig = {"schema_version": "1.1",
           "source": {"channel": "nsw_da", "source_id": "n8n_da", "external_id": "DA-DEMO-1"},
           "candidate_type": "market_signal", "consent": {"basis": "none"},
           "request": {"scope_text": "DA approved alterations (a signal, never a lead)"}}
    r3 = lci.submit_candidate(sig, source_id="n8n_da")
    fw = cf.evaluate(sig)
    # هیچ فایلِ کاندیدِ top-level نباید ساخته باشد (market_signal → signals/)
    seen2 = lead_sense.read_inbox()
    no_sig_top = all(d.get("lead_id") != r3.get("lead_id") for _, d in seen2)
    _step(7, "market_signal refused for outreach + no top-level draftable file",
          r3.get("status") == "signal_recorded" and fw.get("outreach_allowed") is False and no_sig_top,
          f"status={r3.get('status')} outreach_allowed={fw.get('outreach_allowed')} top_level_file=no")

    # ── STEP 8: chrono batch proof (یک رأی، lead_outbound pending می‌ماند؛ پول batch) ──
    print("\n── STEP 8: chrono batch-release footgun proof ──")
    e_pay = gate.request("PAY", "bill-demo", beat=1)
    e_cust = gate.request("lead_outbound", "cust-demo", beat=1)
    e_up = gate.request("LEAD_OUTBOUND", "cust-demo-2", beat=1)   # casing نباید allowlist را دور بزند
    gate.release_gated_effects({"hash": "one-human-append"})
    _step(8, "batch: PAY→releasable; lead_outbound/LEAD_OUTBOUND→pending (footgun closed)",
          gate.status_of(e_pay) == "releasable" and gate.status_of(e_cust) == "pending"
          and gate.status_of(e_up) == "pending",
          f"PAY={gate.status_of(e_pay)} lead_outbound={gate.status_of(e_cust)} "
          f"LEAD_OUTBOUND={gate.status_of(e_up)}")

    # ── STEP 9 (اختیاریِ ترجیح‌شده): STOP در sandbox → همه release deny ──
    print("\n── STEP 9 (preferred): STOP/halt blocks release ──")
    stop = opslib.STOP_ORGANISM
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("demo-stop", "utf-8")
    try:
        eid_h = gate.request("lead_outbound", "halt-demo", beat=1)
        leg.authorize(eid_h, "halt-demo", "tok")
        mr_h = leg.may_release(eid_h, fix, gate=gate)
        _step(9, "STOP present → may_release denied (kill supreme)",
              mr_h.get("allow") is False and "halt" in mr_h.get("reason", ""),
              f"may_release={mr_h.get('reason')}")
    finally:
        try:
            stop.unlink()   # STOPِ تستیِ sandbox (نه STOPِ زندهٔ مالک)
        except OSError:
            pass

    # ── خروجی: چک‌لیست + receiptها ──
    passed = sum(1 for r in RESULTS if r["pass"])
    total = len(RESULTS)
    print("\n" + "=" * 72)
    print(f"CHECKLIST: {passed}/{total} PASS")
    print("=" * 72)
    receipts = {
        "sandbox": _SANDBOX,
        "flags_armed": {"OCTOPUS_WIRE_LEAD_CANDIDATES": "1", "OCTOPUS_WIRE_LEAD_OUTBOUND": "1"},
        "checklist": RESULTS,
        "synthetic_lead_id": r1.get("lead_id"),
        "fixture_lead_id": r2.get("lead_id"),
        "market_signal_lead_id": r3.get("lead_id"),
        "events_tail": _events_tail(60),
        "top_level_inbox_files": sorted(p.name for p, _ in lead_sense.read_inbox()),
    }
    out_json = Path(__file__).resolve().parent / "last-run-receipts.json"
    out_json.write_text(json.dumps(receipts, ensure_ascii=False, indent=2), "utf-8")
    print("receipts written:", out_json)
    print("ALL-PASS" if passed == total else "SOME-FAIL")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
