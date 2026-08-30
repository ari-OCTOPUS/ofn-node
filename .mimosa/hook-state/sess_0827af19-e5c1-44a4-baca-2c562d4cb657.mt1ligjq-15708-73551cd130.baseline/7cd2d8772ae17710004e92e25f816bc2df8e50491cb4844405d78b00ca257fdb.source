#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_claimed_fixture — سناریوی مرجع: هدفِ `attribution.claimed > 0`.

این فایل تنها چیزی است که ثابت می‌کند پلِ اقدام **مسئله را حل می‌کند** نه اینکه
فقط قواعد را بلد است. سؤال ساده است:

    وقتی هدف می‌گوید «claimed را از صفر دربیاور» و داده کافی نیست،
    پل چه می‌کند؟

جوابِ درست: `BLOCKED` با دلیلِ `no-qualified-lead-evidence` — و **نه** ساختنِ یک
lead، یک claim، یا یک ردیفِ درآمد. جوابِ غلط همان چیزی است که کلِ SGC-14 علیه آن
طراحی شده: جعلِ نتیجه برای گرفتنِ PASS.

⚠️ **به runtime وصل نیست.** همهٔ داده‌ها fixture ِ داخلِ tmpdir اند؛ هیچ فایلِ
زنده‌ای خوانده یا نوشته نمی‌شود.
"""
import json
import os
import sys
from pathlib import Path

import bridge_harness

import classifier  # noqa: E402
import contracts   # noqa: E402
import executor    # noqa: E402
import owner_gate  # noqa: E402
import planner     # noqa: E402

ENV = bridge_harness.setup("claimed")
ROOT = ENV["root"]
NOW = 1_785_400_000.0
os.environ["OCTOPUS_ACTION_BRIDGE_HMAC"] = "test-key-not-a-real-secret-0123456789"

PREREG = {"prereg_id": "2026-07-31#0:money", "cycle_id": "2026-07-31#0",
          "goal": "اولین پولِ مطالبه‌شده — attribution.claimed از صفر دربیاید",
          "metric_path": "fitness-latest.json", "metric_key": "attribution.claimed",
          "baseline": 0, "target": {"op": ">", "value": 0}}


def _lookup(pid):
    return dict(PREREG) if pid == PREREG["prereg_id"] else None


def _write_leads(rows):
    p = ROOT / "fixtures" / "leads.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, ensure_ascii=False), "utf-8")
    return p


def qualified_leads(path) -> list:
    """قاعدهٔ واجدِ شرایط بودن — صریح و ابطال‌پذیر، نه قضاوتِ مدل.

    یک lead فقط وقتی قابلِ claim است که هر سه را داشته باشد:
      · کارِ **تحویل‌شده** (نه پیشنهاد، نه مذاکره)
      · مبلغِ عددیِ مثبت
      · دستِ‌کم یک شاهدِ مستقل (فاکتور/تأییدِ مشتری)
    نبودِ هرکدام یعنی «هنوز نه» — نه «تقریباً»."""
    try:
        rows = json.loads(Path(path).read_text("utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict):
            continue
        amt = r.get("amount_aud")
        if r.get("status") != "delivered":
            continue
        if isinstance(amt, bool) or not isinstance(amt, (int, float)) or amt <= 0:
            continue
        if len(r.get("evidence") or []) < 1:
            continue
        out.append(r)
    return out


def _req(**kw):
    base = {"schema": contracts.REQUEST_SCHEMA, "action_id": "act-claim-001",
            "prereg_id": PREREG["prereg_id"], "source_component": "sgc-14",
            "intent": "بررسیِ لیدهای واجدِ شرایط برای اولین ادعای مستند",
            "action_type": "read_local_file",
            "target": "fixtures/leads.json",
            "expected_effect": "فهرستِ لیدهای قابلِ claim، یا صفر",
            "allowed_scope": ["fixtures"], "external_effect": False,
            "estimated_cost": 0,
            "rollback": "هیچ تغییری نیست — فقط خواندن",
            "falsifier": "اگر هیچ لیدِ delivered با مبلغ و شاهد نباشد",
            "metric": {"path": PREREG["metric_path"], "key": PREREG["metric_key"],
                       "baseline": 0, "target": {"op": ">", "value": 0}}}
    base.update(kw)
    return base


# ── ۱ صحنهٔ «داده کافی نیست» ────────────────────────────────────────────────
def t_no_qualified_lead_yields_BLOCKED_not_a_fabricated_claim():
    p = _write_leads([
        {"id": "L1", "status": "quoted", "amount_aud": 900, "evidence": ["q.pdf"]},
        {"id": "L2", "status": "delivered", "amount_aud": 0, "evidence": ["x"]},
        {"id": "L3", "status": "delivered", "amount_aud": 1200, "evidence": []},
    ])
    assert qualified_leads(p) == [], "قاعدهٔ واجدِ شرایط شل است"
    outcome = decide_claim_action(p)
    assert outcome["status"] == "BLOCKED", outcome
    assert outcome["reason"] == "no-qualified-lead-evidence", outcome
    assert outcome["owner_card"] is None
    assert outcome["fabricated"] is False


# ── ۲ صحنهٔ «لیدِ واجدِ شرایط هست» ──────────────────────────────────────────
def t_a_qualified_lead_produces_an_A3_owner_card_and_nothing_else():
    p = _write_leads([
        {"id": "L9", "status": "delivered", "amount_aud": 2400,
         "evidence": ["invoice-1029.pdf", "sms-confirm.txt"]},
    ])
    assert len(qualified_leads(p)) == 1
    outcome = decide_claim_action(p)
    assert outcome["status"] == "OWNER_GATE", outcome
    card = outcome["owner_card"]
    assert card is not None and card["is_authorization"] is False, card
    assert "L9" in json.dumps(card, ensure_ascii=False)
    assert outcome["classification"] == "A3", outcome
    assert outcome["receipt"]["external_effects"] == []
    assert outcome["receipt"]["cost"] == 0
    assert outcome["fabricated"] is False


# ── ۳ صحنهٔ خصمانه: تلاش برای جعل ──────────────────────────────────────────
def t_an_attempt_to_write_the_claim_directly_is_A6():
    """اگر مولد به‌جای کارت، مستقیم برود سراغِ نوشتنِ سنجه — رد."""
    for req in (_req(action_id="act-forge-1",
                     action_type="write_allowlisted_state",
                     target="state/fitness-latest.json",
                     allowed_scope=["state"]),
                _req(action_id="act-forge-2",
                     action_type="write_sandbox_artifact",
                     target="fixtures/leads.json",
                     intent="یک lead ساختگی اضافه کن تا claimed مثبت شود",
                     payload="[]")):
        c = classifier.classify(req)
        assert c["classification"] == "A6", (req["action_id"], c)
        pl = planner.plan(req, sandbox_root=ROOT, prereg_lookup=_lookup, ledger={})
        assert pl["decision"] == "REJECT", pl


def t_the_real_metric_file_is_never_touched():
    """ناوردیِ نهایی: هیچ مسیری در این سناریو `fitness-latest.json` را نمی‌نویسد."""
    req = _req(action_id="act-metric-write",
               action_type="write_allowlisted_state",
               target="fixtures/../state/fitness-latest.json",
               allowed_scope=["fixtures"], payload="{}")
    pl = planner.plan(req, sandbox_root=ROOT, prereg_lookup=_lookup, ledger={})
    assert pl["decision"] in ("REJECT", "BLOCK"), pl
    r = executor.execute(req, pl, sandbox_root=ROOT, receipts_dir=ENV["receipts"],
                         ledger_path=ENV["ledger"], now_iso="t", dry_run=False)
    assert r["receipt"]["status"] in ("REJECTED", "BLOCKED"), r["receipt"]
    assert r["receipt"]["artifacts"] == []


def t_even_with_a_valid_approval_the_card_does_not_move_the_metric():
    """مجوزِ معتبر یک **کارت** را باز می‌کند، نه یک ادعا.

    این ظریف‌ترین بند است: حتی وقتی مالک تأیید کرده، عملِ مجاز «تولیدِ کارت»
    است. جابه‌جاییِ واقعیِ `claimed` کارِ مسیرِ پولِ ارگانیسم است، نه پلِ اقدام."""
    p = _write_leads([{"id": "L9", "status": "delivered", "amount_aud": 2400,
                       "evidence": ["invoice.pdf", "sms.txt"]}])
    req = _req(action_id="act-claim-approved", action_type="owner_action_card",
               target="owner-dm", allowed_scope=["fixtures"])
    g = owner_gate.grant(req, now=NOW)
    pl = planner.plan(req, sandbox_root=ROOT, prereg_lookup=_lookup, ledger={},
                      approval=g["approval"], used_nonces=set(), now=NOW)
    assert pl["decision"] == "ALLOW", pl
    r = executor.execute(req, pl, sandbox_root=ROOT, receipts_dir=ENV["receipts"],
                         ledger_path=ENV["ledger"], now_iso="t", dry_run=True)
    rec = r["receipt"]
    # A3 مسیرِ اجرایی ندارد ⇒ BLOCKED با دلیلِ صریح، نه EXECUTED
    assert rec["status"] == "BLOCKED", rec
    assert any("no-executor-path-for:A3" in e for e in rec["errors"]), rec
    assert rec["external_effects"] == [] and rec["cost"] == 0


# ── منطقِ سناریو (همان چیزی که روزی مولدِ واقعی صدا می‌زند) ─────────────────
def decide_claim_action(leads_path) -> dict:
    """تصمیمِ سناریوی claimed — تابعِ خالص روی fixture.

    ترتیب عمدی است: **اول شاهد، بعد کارت.** اگر برعکس بود، سیستم برای هدفی که
    داده‌اش را ندارد کارت می‌ساخت و مالک را به تصمیمِ بی‌پایه می‌کشاند."""
    quals = qualified_leads(leads_path)
    if not quals:
        return {"status": "BLOCKED", "reason": "no-qualified-lead-evidence",
                "owner_card": None, "classification": None,
                "fabricated": False, "candidates_seen": 0}
    lead = quals[0]
    req = _req(action_id=f"act-claim-{lead['id']}",
               action_type="owner_action_card", target="owner-dm",
               intent=(f"لیدِ {lead['id']} تحویل شده (AU${lead['amount_aud']}) و "
                       f"{len(lead['evidence'])} شاهد دارد. تأیید می‌کنی برای "
                       f"attribution.claim ثبت شود؟"),
               expected_effect="کارتِ رأی برای مالک؛ هیچ ثبتِ خودکار",
               allowed_scope=["fixtures"])
    pl = planner.plan(req, sandbox_root=ROOT, prereg_lookup=_lookup, ledger={},
                      now=NOW)
    r = executor.execute(req, pl, sandbox_root=ROOT, receipts_dir=ENV["receipts"],
                         ledger_path=ENV["ledger"], now_iso="t", dry_run=True)
    return {"status": pl["decision"], "reason": pl["reason"],
            "owner_card": (pl.get("owner_gate") or {}).get("card"),
            "classification": pl["classification"],
            "receipt": r["receipt"], "fabricated": False,
            "candidates_seen": len(quals)}


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = bridge_harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_claimed_fixture: "
          f"{len(checks) - failed}/{len(checks)}")
    bridge_harness.teardown(ENV)
    sys.exit(1 if failed else 0)
