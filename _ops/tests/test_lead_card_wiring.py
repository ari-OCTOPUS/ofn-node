#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_card_wiring — کارتِ لید از امتیازدهی تا دکمهٔ واقعاً روت‌شده.

VQ-DEAD-LEAD-BUTTONS-001 → سیم‌کشیِ صداکننده (۲۰۲۶-۰۸-۰۷). دو رگرسیون از قبل
هستند: `test_lead_card_buttons_live.py` (گیرنده: تپ روی lcall/ldraft در
center.py) و `test_lead_card.py` (خودِ ماژول `lead_card`). این فایل وسطِ آن‌ها
را می‌بندد — **صداکنندهٔ تولیدی**:

  A) flag خاموش (پیش‌فرض) = بایت‌به‌بایتِ امروز؛ فقط کارتِ رأی می‌رود، هیچ
     کارتِ تعاملی، هیچ import ِ اضافه‌ای اثر ندارد.
  B) flag روشن = `lead_pipeline._process_ready` واقعاً `lead_card.render()` و
     `lead_card.deliver()` را صدا می‌زند (نه فقط `card_text()`ِ متنی) — با
     امضا/آرگومان‌های درست؛ کارتِ تعاملی به‌صورتِ پیامِ **دوم و جدا** می‌رود.
  C) کارتِ تعاملی که واقعاً فرستاده شد، همان callback_data ی دارد که از گیتِ
     واقعیِ `input_surface_policy.classify()` در تاپیکِ گروهِ لید عبور می‌کند —
     یعنی سرِ زنجیره (امتیازدهی) تا دمِ زنجیره (سیاستِ ورودی) واقعاً وصل است.
  D) `lcall`/`ldraft` در `GROUP_CALLBACK_VERBS` حاضرند — با mutation-test ِ
     زنده (برداشتن موقتِ آن‌ها از فهرست، سنجیدنِ قرمزی، بازگرداندن، سنجیدنِ سبزی).
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-card-wiring")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"),
           str(_OPS / "telegram_center"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ماشینِ میزبان ممکن است فلگ/راز ِ زنده داشته باشد — تست باید قطعی باشد.
for _k in ("OCTOPUS_CB_SECRET", "OCTOPUS_WIRE_VERDICT_OUTCOME",
           "OCTOPUS_WIRE_LEAD_OUTBOUND", "OCTOPUS_WIRE_LEAD_CARD_CONTACT",
           "OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT", "OCTOPUS_SMTP_USER",
           "OCTOPUS_SMTP_PASS", "OCTOPUS_SMTP_FROM"):
    os.environ.pop(_k, None)

import opslib                          # noqa: E402
import lead_candidate_inbox as lci     # noqa: E402
import lead_pipeline as lp             # noqa: E402
import lead_card as lc                 # noqa: E402
import input_surface_policy as isp     # noqa: E402

NOW = 1_785_500_000.0
# strata_remedial (base 55) + paint_scope (+18، «rendering and repainting») +
# recurring_buyer (+10، «common property») = 83 ≥ draft_threshold(70).
STRATA_SCOPE = ("Remedial works to common property including rendering and "
                "repainting of external facade to residential flat building "
                "of 24 units.")

OWNER = 6150431610
GROUP = -1004475788460
TOPICS = {"lead": 22, "system": 28, "mirror": 205}


class SpySend:
    def __init__(self):
        self.calls = []

    def __call__(self, text, keyboard=None, stream=None):
        self.calls.append({"text": text, "keyboard": keyboard, "stream": stream})
        return True


class FakeLeg:
    def __init__(self):
        self.n = 0

    def intake(self, name, expected_aud, cell="lead.doer", description="", day=None):
        self.n += 1
        return {"ok": True, "attribution_id": f"AT-WIRE-{self.n:03d}"}

    def draft_quote(self, attribution_id, scope="", price_range_aud=(0, 0),
                    assumptions=None):
        class _P:
            def __init__(self, aid):
                self._aid = aid

            def to_dict(self):
                return {"proposal_id": f"P-{self._aid}", "payload": {}}
        return _P(attribution_id)


def _submit(*, phone=None, email=None, address="12 Wattle Crescent, Pyrmont NSW 2009"):
    os.environ["OCTOPUS_WIRE_LEAD_CANDIDATES"] = "1"
    import uuid
    contact = {}
    if email:
        contact["email"] = email
    if phone:
        contact["phone"] = phone
    cand = {"source": {"channel": "synthetic_test", "external_id": uuid.uuid4().hex},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit"},
            "request": {"scope_text": STRATA_SCOPE},
            "property": {"address": address}}
    if contact:
        cand["contact"] = contact
    r = lci.submit_candidate(cand, source_id="wiring-test")
    assert r.get("status") == "accepted", r
    return r["lead_id"]


def _inbox() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox"


def _ready_card(spy):
    """کارتِ رأی (`_card_text` در lead_pipeline.py) — همیشه با «🎨 لیدِ آماده»
    شروع می‌شود. وقتی OCTOPUS_WIRE_LEAD_CARD_CONTACT روشن است، بدنهٔ این کارت
    خودش هم متنِ `render()` را (از راهِ `sc.card()`) در خودش دارد — پس تشخیصِ
    کارتِ تعاملی نباید فقط رویِ زیرمتنِ مشترک تکیه کند (پایین)."""
    hits = [c for c in spy.calls if "لیدِ آماده" in c["text"]]
    assert hits, ("کارتِ رأی نیامد", spy.calls)
    return hits[0]


def _contact_card(spy):
    """کارتِ تعاملیِ جدا: همان سرتیترِ `render()` («لیدِ تازه») را دارد ولی
    برخلافِ کارتِ رأی، هدرِ «لیدِ آماده» ندارد — چون پیامی کاملاً جداست."""
    hits = [c for c in spy.calls
            if "لیدِ تازه" in c["text"] and "لیدِ آماده" not in c["text"]]
    return hits[0] if hits else None


# ═══ A) flag خاموش = بایت‌به‌بایتِ امروز ════════════════════════════════════
def t_a_flag_off_sends_only_the_ready_card():
    os.environ.pop(lc.FLAG, None)
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    lid = _submit(phone="0412345678", email="sarah@example.com",
                  address="12 Wattle Crescent, Pyrmont NSW 2009")
    spy = SpySend()
    r = lp.beat(now=NOW, deps={"send_fn": spy, "lead_leg": FakeLeg()})
    assert r["ok"] and r["ready"] == 1 and r["cards_sent"] == 1, r
    assert r["contact_cards_sent"] == 0, r
    assert len(spy.calls) == 1, ("flag خاموش باید فقط یک کارت بفرستد", spy.calls)
    _ready_card(spy)
    assert lid


# ═══ B) flag روشن = render()+deliver() واقعاً صدا می‌خورند ═════════════════
def t_b_flag_on_genuinely_invokes_render_and_deliver():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    os.environ[lc.FLAG] = "1"
    calls = {"render": [], "deliver": []}
    _orig_render, _orig_deliver = lc.render, lc.deliver

    def _spy_render(*a, **kw):
        calls["render"].append((a, kw))
        return _orig_render(*a, **kw)

    def _spy_deliver(*a, **kw):
        calls["deliver"].append((a, kw))
        return _orig_deliver(*a, **kw)

    lc.render, lc.deliver = _spy_render, _spy_deliver
    try:
        lid = _submit(phone="0412 345 678", email="sarah@example.com",
                      address="45 Harris St, Pyrmont NSW 2009")
        spy = SpySend()
        r = lp.beat(now=NOW + 60, deps={"send_fn": spy, "lead_leg": FakeLeg()})
        assert r["ok"] and r["ready"] == 1, r
        assert r["cards_sent"] == 1, "کارتِ رأی نباید ناپدید شود"
        assert r["contact_cards_sent"] == 1, r

        # render() ممکن است **دوبار** صدا بخورد: یک‌بار داخلِ خودِ
        # `lead_scorer.ScoredLead.card()` (برای متنِ غنیِ کارتِ رأی — بدونِ
        # verbs_ready، پس بدونِ کیبورد) و یک‌بار از سیم‌کشیِ نو (با
        # verbs_ready صریح، برای کارتِ تعاملیِ جدا). سنجهٔ ما دقیقِ همان
        # فراخوانیِ **نو** است، نه شمارشِ کلِ render().
        assert calls["render"], "render() اصلاً صدا نخورد"
        wired_calls = [(a, kw) for a, kw in calls["render"]
                       if kw.get("verbs_ready") == lc.SAFE_VERBS]
        assert len(wired_calls) == 1, (
            "render() با verbs_ready ِ سیم‌کشیِ نو دقیقاً یک‌بار باید صدا بخورد",
            calls["render"])
        args, kwargs = wired_calls[0]
        assert kwargs.get("lead_id") == lid, (kwargs.get("lead_id"), lid)
        sc_arg = kwargs.get("scored")
        assert sc_arg is not None and sc_arg.action == "draft", sc_arg
        assert sc_arg.category == "strata_remedial", sc_arg.category

        assert len(calls["deliver"]) == 1, "deliver() دقیقاً یک‌بار باید صدا بخورد"
        d_args, d_kwargs = calls["deliver"][0]
        assert d_args[0] is spy, "deliver باید همان send_fn ِ تزریقی را بگیرد"

        ready = _ready_card(spy)
        contact = _contact_card(spy)
        assert contact is not None, ("کارتِ تعاملی نیامد", spy.calls)
        assert contact is not ready, "کارتِ تعاملی باید پیامِ **جدا** باشد"
        assert contact["stream"] == "lead", contact
        assert "tel:+61412345678" in contact["text"], contact["text"]
        assert lid in contact["text"], contact["text"]

        kb = contact["keyboard"]
        assert kb is not None, "با تلفنِ معتبر و verbs_ready باید دکمه بیاید"
        verbs = {str(b["callback_data"]).split(":", 1)[0]
                 for row in kb["inline_keyboard"] for b in row}
        assert verbs <= lc.SAFE_VERBS, verbs
        assert "lcall" in verbs, verbs
        cb_lead_ids = {str(b["callback_data"]).split(":", 1)[1]
                       for row in kb["inline_keyboard"] for b in row}
        assert cb_lead_ids == {lid}, (cb_lead_ids, lid)
    finally:
        lc.render, lc.deliver = _orig_render, _orig_deliver
        os.environ.pop(lc.FLAG, None)


# ═══ B2) بدونِ send_fn: هیچ کارتی، ولی beat سالم می‌ماند ═══════════════════
def t_b2_flag_on_without_send_fn_stays_headless():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    os.environ[lc.FLAG] = "1"
    try:
        _submit(phone="0412345678", address="8 Bridge Rd, Glebe NSW 2037")
        r = lp.beat(now=NOW + 120, deps={"lead_leg": FakeLeg()})
        assert r["ok"] and r["ready"] == 1, r
        assert r["cards_sent"] == 0 and r["contact_cards_sent"] == 0, r
    finally:
        os.environ.pop(lc.FLAG, None)


# ═══ C) کارتِ واقعاً فرستاده‌شده از گیتِ واقعیِ سیاست عبور می‌کند ══════════
def t_c_the_sent_callback_data_clears_the_real_policy_gate():
    os.environ["OCTOPUS_WIRE_LEAD_PIPELINE"] = "1"
    os.environ[lc.FLAG] = "1"
    try:
        lid = _submit(phone="0412345678", address="200 Glebe Point Rd, Glebe NSW 2037")
        spy = SpySend()
        r = lp.beat(now=NOW + 180, deps={"send_fn": spy, "lead_leg": FakeLeg()})
        assert r["contact_cards_sent"] == 1, r
        contact = _contact_card(spy)
        assert contact is not None
        kb = contact["keyboard"]
        cbdata = kb["inline_keyboard"][0][0]["callback_data"]
        assert cbdata == f"lcall:{lid}", cbdata

        cbq = {"callback_query": {"from": {"id": OWNER}, "data": cbdata,
                                  "message": {"chat": {"id": GROUP,
                                                       "type": "supergroup"},
                                             "message_thread_id": 22}}}
        d = isp.classify(cbq, bot_role="outer", owner_id=OWNER, group_id=GROUP,
                         topics=TOPICS)
        assert d["allow"] is True, d
        assert d["mode"] == "leg_scoped" and d["leg"] == "lead", d
    finally:
        os.environ.pop(lc.FLAG, None)


# ═══ D) lcall/ldraft در GROUP_CALLBACK_VERBS + mutation-test زنده ══════════
def t_d_lcall_and_ldraft_are_in_group_callback_verbs():
    assert "lcall" in isp.GROUP_CALLBACK_VERBS, isp.GROUP_CALLBACK_VERBS
    assert "ldraft" in isp.GROUP_CALLBACK_VERBS, isp.GROUP_CALLBACK_VERBS
    for data in ("lcall:lead_abc", "ldraft:lead_abc"):
        cbq = {"callback_query": {"from": {"id": OWNER}, "data": data,
                                  "message": {"chat": {"id": GROUP,
                                                       "type": "supergroup"},
                                             "message_thread_id": 22}}}
        d = isp.classify(cbq, bot_role="outer", owner_id=OWNER, group_id=GROUP,
                         topics=TOPICS)
        assert d["allow"] is True and d["mode"] == "leg_scoped", (data, d)
        assert d["leg"] == "lead", (data, d)


def t_e_mutation_removing_lcall_ldraft_flips_the_gate_red():
    """mutation-test زنده: فهرست را موقتاً بدونِ lcall/ldraft می‌کنیم — تپِ
    مالک از گروه باید denied بگیرد. سپس بازمی‌گردانیم و سبزی را دوباره می‌سنجیم.
    این دقیقاً همان سنجه‌ای‌ست که اگر کسی این دو فعل را از فهرست حذف کند،
    این تست باید قرمز شود — یعنی خودِ افزودن، تحتِ پوشش است، نه فقط وجودش."""
    original = isp.GROUP_CALLBACK_VERBS
    try:
        isp.GROUP_CALLBACK_VERBS = frozenset(original - {"lcall", "ldraft"})
        for data in ("lcall:lead_abc", "ldraft:lead_abc"):
            cbq = {"callback_query": {"from": {"id": OWNER}, "data": data,
                                      "message": {"chat": {"id": GROUP,
                                                           "type": "supergroup"},
                                                 "message_thread_id": 22}}}
            d = isp.classify(cbq, bot_role="outer", owner_id=OWNER, group_id=GROUP,
                             topics=TOPICS)
            assert d["allow"] is False, (data, "برداشتنِ فعل باید denied بدهد", d)
            assert d["reason"].startswith("callback-dm-only:"), (data, d)
    finally:
        isp.GROUP_CALLBACK_VERBS = original
    # سبزیِ بازگشته — همان بندِ D.
    t_d_lcall_and_ldraft_are_in_group_callback_verbs()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_card_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
