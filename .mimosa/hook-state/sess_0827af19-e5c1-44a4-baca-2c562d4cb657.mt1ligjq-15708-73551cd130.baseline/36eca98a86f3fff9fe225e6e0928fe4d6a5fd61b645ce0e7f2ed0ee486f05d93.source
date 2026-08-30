#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_pipeline — ارکستراتورِ ماشینِ لید (منشور رأی ۱۳/۱۷/۱۸).

اثبات می‌کند:
  · flag خاموش = no-op مطلق؛ صندوق دست‌نخورده.
  · round-trip تولیدی: submit_candidate (کانالِ synthetic_test → سقفِ consented) →
    کشف→تحقیق→امتیاز→پیش‌نویسِ کوت→کارتِ لیدِ آماده با stream="lead" (جاسوسِ send_fn).
  · کاندیدِ بی‌آدرس → کارِ BLOCKED در leg_tasks با سؤالِ فارسی (مسیرِ گیر ِ منشور).
  · جوابِ مالک (ریپلای=رفعِ مانع ِ موجود) → beat ِ بعدی دوباره تحقیق/امتیاز (revive).
  · پیگیریِ خودکار: draft ِ ارسال‌شدهٔ ≥۳ روزِ بی‌جواب → کارتِ پیگیری، idempotent در پنجره.
  · تستِ قاتل: کاندیدِ market_signal با **همهٔ فلگ‌ها روشن** هرگز به transport نمی‌رسد.
"""
import json
import os
import sys
import uuid
from pathlib import Path

import harness

ENV = harness.setup("lead-pipeline")

# ماشینِ میزبان ممکن است secret/flag ِ زنده داشته باشد — تست باید قطعی باشد.
for _k in ("OCTOPUS_CB_SECRET", "OCTOPUS_WIRE_VERDICT_OUTCOME",
           "OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_WIRE_TRADEQUOTE",
           "OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
           "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM"):
    os.environ.pop(_k, None)

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"),
           str(_OPS / "telegram_center"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                          # noqa: E402
import chrono                          # noqa: E402
import lead_candidate_inbox as lci     # noqa: E402
import lead_pipeline as lp             # noqa: E402
import lead_quote                      # noqa: E402
import leg_tasks as lt                 # noqa: E402
import outbound_worker as ow           # noqa: E402
import lead_effect_gate as leg         # noqa: E402
import lead_outbound_transport as lot  # noqa: E402
import consent_gate as cg              # noqa: E402
import consent_store as cs             # noqa: E402

NOW = 1_785_400_000.0
STRATA_SCOPE = ("Remedial works to common property including rendering and "
                "repainting of external facade to residential flat building "
                "of 24 units.")


class SpySend:
    def __init__(self):
        self.calls = []

    def __call__(self, text, keyboard=None, stream=None):
        self.calls.append({"text": text, "keyboard": keyboard, "stream": stream})
        return True


class FakeLeg:
    """قراردادِ LeadLeg (intake/draft_quote) بدونِ لجرِ واقعی."""

    def __init__(self):
        self.n = 0

    def intake(self, name, expected_aud, cell="lead.doer", description="", day=None):
        self.n += 1
        return {"ok": True, "attribution_id": f"AT-PIPE-{self.n:03d}"}

    def draft_quote(self, attribution_id, scope="", price_range_aud=(0, 0),
                    assumptions=None):
        class _P:
            def __init__(self, aid):
                self._aid = aid

            def to_dict(self):
                return {"proposal_id": f"P-{self._aid}", "payload": {}}
        return _P(attribution_id)


def _submit(scope, address=None, email=None, channel="synthetic_test"):
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    cand = {"source": {"channel": channel, "external_id": uuid.uuid4().hex},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit"},
            "request": {"scope_text": scope}}
    if address:
        cand["property"] = {"address": address}
    if email:
        cand["contact"] = {"email": email}
    r = lci.submit_candidate(cand, source_id="pipeline-test")
    assert r.get("status") == "accepted", r
    return r["lead_id"]


def _inbox() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox"


# ── consent_gate D2a wiring (۲۰۲۶-۰۸-۰۷) — کمکِ گرانتِ رضایتِ store-backed ─────────
# outbound_worker.send_one حالا consent_gate.may_release را **قبل از** release_and_settle
# صدا می‌زند (لایهٔ سومِ مستقلِ consent، جدا از consent_firewall ِ داخلِ lead_effect_gate
# که t_f روی آن می‌سنجد). بدونِ این گرانت، consent-denied زودتر از gate_denied می‌رسد و
# ناوردای موردنظرِ t_f (R1 — market_signal حتی با گیتِ effect هم رد می‌شود) را پنهان
# می‌کند. هم‌الگوی test_lead_outbound_transport.py::t_ib — رضایتِ صریح می‌گیریم تا
# دقیقاً همان گیتِ هدف (market_signal_never_sends) سنجیده شود، نه گیتِ زودتر.
def _grant_consent(lead_id: str, *, channel: str = "telegram_manual") -> None:
    os.environ[cg.FLAG] = "1"
    store = cs.ConsentStore()
    try:
        store.upsert_current({
            "lead_id": lead_id, "candidate_type": "consented_inbound",
            "consent_basis": "explicit", "consent_evidence": "quote_form",
            "consent_state": "CONSENTED_INBOUND", "compliance_state": "UNREVIEWED",
            "outreach_allowed": True, "retention_class": "consented_customer",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": channel})
    finally:
        store.close()


def t_a_flag_off_is_absolute_noop():
    os.environ.pop("OCTOPUS_WIRE_LEAD_PIPELINE", None)
    lid = _submit(STRATA_SCOPE, address="12 Wattle Crescent, Pyrmont NSW 2009")
    r = lp.beat(now=NOW, deps={"send_fn": SpySend()})
    assert r == {"ok": False, "status": "flag_off"}, r
    assert (_inbox() / f"{lid}.json").exists(), "flag خاموش نباید صندوق را لمس کند"


def t_b_production_roundtrip_discover_research_score_draft_ready_card():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    spy = SpySend()
    fake = FakeLeg()
    r = lp.beat(now=NOW, deps={"send_fn": spy, "lead_leg": fake})
    assert r["ok"] and r["ready"] == 1 and r["cards_sent"] == 1, r
    assert fake.n == 1, "intake صدا نخورد"
    card = spy.calls[-1]
    assert card["stream"] == "lead", "کارت باید به جریانِ lead برود (رأی ۱۸)"
    assert "لیدِ آماده" in card["text"] and "score:" in card["text"], card["text"]
    assert "کوت" in card["text"], "خلاصهٔ کوت روی کارت نیست"
    # بدونِ OCTOPUS_CB_SECRET دکمهٔ مرده نمی‌سازیم — کارتِ بی‌دکمهٔ صادقانه
    assert card["keyboard"] is None, "بدونِ secret/registry دکمه باید غایب باشد"
    # فایل منتقل شد (نه حذف)
    assert not list(_inbox().glob("*.json")), "صندوق باید خالی شده باشد"
    # پیش‌نویسِ کوت persist شد
    drafts = list((opslib.STATE_DIR / "legs" / "lead-drafts").glob("AT-PIPE-*.json"))
    assert drafts, "draft ِ کوت نوشته نشد"


def t_c_missing_address_becomes_a_blocked_task_with_a_persian_question():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    _submit(STRATA_SCOPE, address=None, email="a.b@example.com")
    spy = SpySend()
    r = lp.beat(now=NOW + 60, deps={"send_fn": spy})
    assert r["ok"] and r["stuck"] == 1, r
    blocked = [t for t in lt.queue("lead") if t.get("state") == lt.BLOCKED]
    assert len(blocked) == 1, blocked
    assert "🎨 لیدِ" in blocked[0]["text"], blocked[0]
    assert "آدرس" in str(blocked[0].get("question")), \
        "سؤالِ فارسیِ آدرس روی کارِ BLOCKED نیست"
    st = json.loads((opslib.STATE_DIR / "legs" / "lead-pipeline.json").read_text("utf-8"))
    assert st["stuck"], "لیدِ گیر باید در state ثبت شود"


def t_d_owner_answer_revives_the_stuck_lead_into_scoring():
    """ریپلای مالک به کارتِ 🚧 (مکانیکِ موجودِ resolve_blocked) → beat بعدی revive."""
    blocked = [t for t in lt.queue("lead") if t.get("state") == lt.BLOCKED]
    assert blocked, "پیش‌نیاز: کارِ BLOCKED از تستِ قبل"
    tid = blocked[0]["id"]
    w = lt.resolve_blocked("lead", tid, "12 Wattle Crescent, Pyrmont NSW 2009",
                           now=NOW + 120)
    assert w and w["state"] == lt.WORKING and "➕ اطلاعات مالک" in w["text"], w
    spy = SpySend()
    r = lp.beat(now=NOW + 180, deps={"send_fn": spy, "lead_leg": FakeLeg()})
    assert r["ok"] and r["revived"] == 1 and r["ready"] >= 1, r
    done = [t for t in lt.queue("lead") if t.get("id") == tid]
    assert not done, "کارِ revive‌شده باید DONE شده باشد (از صفِ باز خارج)"
    st = json.loads((opslib.STATE_DIR / "legs" / "lead-pipeline.json").read_text("utf-8"))
    assert not st["stuck"], "state ِ گیر باید خالی شده باشد"
    assert any("لیدِ آماده" in c["text"] for c in spy.calls), "کارتِ آماده بعد از revive نیامد"


def t_e_followup_minted_after_three_silent_days_and_only_once_per_window():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    # یک draft ِ ارسال‌شده بساز (مسیرِ واقعیِ lead_quote + mark_sent)
    fake = FakeLeg()
    q = lead_quote.create_quote(
        fake, "AT-FOLLOW-001",
        lead_quote.lead_to_intake({"description": STRATA_SCOPE, "size_m2": 200}, None))
    assert q.get("ok"), q
    assert lead_quote.mark_sent("AT-FOLLOW-001") is True
    import time as _t
    later = _t.time() + 4 * 86400          # ۴ روز بعد از sent_ts ِ واقعی
    spy = SpySend()
    r = lp.beat(now=later, deps={"send_fn": spy})
    assert r["ok"] and r["followups"] == 1, r
    assert any("پیگیری" in c["text"] for c in spy.calls), "کارتِ پیگیری نیامد"
    r2 = lp.beat(now=later + 60, deps={"send_fn": spy})
    assert r2["followups"] == 0, "پیگیریِ دوم در همان پنجره = سیل"


def t_f_killer_market_signal_never_reaches_transport_even_all_flags_on():
    """R1 ساختاری: با همهٔ فلگ‌ها روشن و SMTP «مسلح»، سیگنالِ بازار هرگز نمی‌رود."""
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    os.environ.update({"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
                       "OCTOPUS_SMTP_USER": "u", "OCTOPUS_SMTP_PASS": "p",
                       "OCTOPUS_SMTP_FROM": "quotes@example.com"})
    calls = []
    _orig = lot._default_send_impl
    lot._default_send_impl = lambda *a: calls.append(a)
    try:
        # producer ِ متخاصم: فایلِ سیگنال مستقیم در top-level ِ صندوق
        evil = {"lead_id": "evil-ms", "description": STRATA_SCOPE,
                "address": "1 Somewhere St, Sydney NSW", "source": "facebook_group",
                "candidate": {"candidate_type": "market_signal",
                              "consent": {"basis": "none", "outreach_allowed": False},
                              "request": {}},
                "contact": {"email": "victim@example.com"}}
        p = _inbox() / "evil-ms.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(evil, ensure_ascii=False), "utf-8")
        spy = SpySend()
        r = lp.beat(now=NOW + 600, deps={"send_fn": spy, "lead_leg": FakeLeg()})
        assert r["signals"] == 1 and r["ready"] == 0, r
        assert not any("evil-ms" in c["text"] for c in spy.calls), \
            "سیگنال نباید کارتِ آماده بگیرد"
        # حتی با authorize ِ مستقیم و worker ِ روشن: گیت رد می‌کند، transport صفر
        db = chrono.ChronoDB(ENV["OPS_DIR"] + "/state/killer.db")
        gate = chrono.EffectorGate(db)
        cand = {"lead_id": "evil-ms", "source": {"channel": "facebook_group"},
                "candidate_type": "market_signal",
                "consent": {"basis": "none"},
                "contact": {"email": "victim@example.com"}}
        eid = gate.request("lead_outbound", "evil-ms", beat=1)
        leg.authorize(eid, "evil-ms", "tok-evil")
        # consent_gate D2a: این تست ناوردای market_signal_never_sends ِ effect gate
        # را می‌سنجد ("حتی با همهٔ فلگ‌ها روشن")، نه لایهٔ consent_gate را — پس
        # رضایتِ صریحِ store-backed را هم می‌گیریم («حتی با رضایتِ کامل» — هم‌الگوی
        # test_lead_outbound_transport.py::t_ib) تا مطمئن شویم گیتِ **هدف** (نه
        # گیتِ زودترِ consent) واقعاً همان چیزی است که market_signal را رد می‌کند.
        _grant_consent("evil-ms")
        res = ow.send_one(eid, cand, "draft", gate=gate,
                          now_ms=int((NOW + 600) * 1000))
        assert res["sent"] is False and res["status"] == "gate_denied", res
        assert res["gate_reason"] == "market_signal_never_sends", res
        assert not calls, "market_signal به transport رسید — نقضِ R1"
        v = leg.on_lead_verdict("evil-ms", cand, "approve", gate=gate)
        assert v["authorized"] is False, v
    finally:
        lot._default_send_impl = _orig
        os.environ.pop(cg.FLAG, None)
        for k in ("OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_SMTP_HOST",
                  "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER", "OCTOPUS_SMTP_PASS",
                  "OCTOPUS_SMTP_FROM"):
            os.environ.pop(k, None)


def t_g_headless_without_send_fn_no_cards_but_beat_still_works():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    _submit(STRATA_SCOPE, address="30 Kent St, Sydney NSW 2000")
    r = lp.beat(now=NOW + 900, deps={"lead_leg": FakeLeg()})
    assert r["ok"] and r["ready"] == 1 and r["cards_sent"] == 0, r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_pipeline: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
