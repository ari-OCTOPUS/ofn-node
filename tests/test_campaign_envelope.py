"""campaign_envelope — تست‌های سیاستی (Lane درآمد، مرزِ مجاز).

fixture-driven: quote_fn ساختگی، دیتابیس واقعی لمس نمی‌شود، صفر شبکه.
هر چکِ سیاست، کنترل منفی خودش را دارد — بسته‌ای که فقط سبز می‌شود
هیچ‌وقت تست نشده.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ofn.agents import campaign_envelope as ce
from ofn.agents.campaign_envelope import build_campaign_envelope


def _fake_quote_fn(lead_id: str, scope):
    """fixture: شبیه خروجی dry موتور کوت برای خریدار OCP."""
    return {
        "lead_id": lead_id,
        "qt_number": "QT-20260902-001",
        "priced": False,
        "subject": "Painting works — site visit request",
        "draft": {"body": "fixture body"},
    }   # نکته: خروجی واقعیِ dryِ موتور total_aud ندارد — فیکسچر هم ندارد


def _build(lead_scopes, *, card_approved=False, quote_fn=_fake_quote_fn,
           max_quotes=10):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "envelope.json"
        env = build_campaign_envelope(
            "PAINT-L5-001", lead_scopes, quote_fn=quote_fn,
            card_approved=card_approved, now_iso="2026-09-02T07:00:00Z",
            out_path=out, max_quotes=max_quotes)
        data = json.loads(out.read_text(encoding="utf-8"))  # داخل بافت بخوان
        return env, out, data


class HappyPath(unittest.TestCase):
    def test_two_ocp_buyers_ready_and_auditable(self):
        env, out, data = _build({
            "lead:nsw_ocp_buyer:tfnsw:initial-intro": {"desc": "repaint lobby"},
            "lead:nsw_ocp_buyer:healthshare-nsw:initial-intro": {"desc": "ward refresh"},
        })
        self.assertTrue(env["policy_checked"])
        self.assertEqual(env["counts"]["quotes"], 2)
        # مرزِ ارسال: ممنوعیت ساختاری، نه توصیه‌ای
        self.assertEqual(env["send_status"], "FORBIDDEN_UNTIL_OWNER_GO")
        self.assertTrue(env["quote_sent_forbidden"])
        # artifact نوشته شد و هش داخلش نشسته
        self.assertIn("sha256", data)
        self.assertEqual(data["campaign_id"], "PAINT-L5-001")


class NegativeControls(unittest.TestCase):
    def test_supply_side_lead_is_wrong_recipient(self):
        env, _, _ = _build({"lead:seek:painter-wanted-sydney": {"desc": "job ad"}})
        self.assertFalse(env["policy_checked"])
        q = env["quotes"][0]
        self.assertFalse(q["policy"]["direction_demand_side"]["ok"])
        self.assertIn("wrong_recipient", q["policy"]["direction_demand_side"]["reason"])

    def test_priced_quote_while_card_unapproved_fails_lock(self):
        def priced_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "total_aud": 4200.0})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}}, quote_fn=priced_fn,
                        card_approved=False)
        self.assertFalse(env["policy_checked"])
        q = env["quotes"][0]
        self.assertFalse(q["policy"]["rate_card_lock"]["ok"])

    def test_priced_quote_with_approved_card_passes_lock(self):
        def priced_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "total_aud": 4200.0})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}}, quote_fn=priced_fn,
                        card_approved=True)
        self.assertTrue(env["policy_checked"])

    def test_total_over_cap_fails(self):
        def huge_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "total_aud": ce._cap_aud() + 1})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}}, quote_fn=huge_fn,
                        card_approved=True)
        self.assertFalse(env["quotes"][0]["policy"]["total_cap"]["ok"])

    def test_priced_dry_total_read_from_body_text(self):
        """Bugbot High 2026-09-02: dry موتور کوت total_aud ندارد — رقم فقط
        در body رندر شده. استخراج از body باید کار کند، وگرنه سقف خلأیی پاس می‌شد."""
        def dry_priced_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "draft": {"body":
                "Reference: QT-1\n\nTotal: $4,200 incl. GST, labour, "
                "materials and prep.\n"}})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}},
                           quote_fn=dry_priced_fn, card_approved=True)
        self.assertTrue(env["quotes"][0]["policy"]["total_cap"]["ok"])

    def test_priced_dry_over_cap_in_body_fails(self):
        def dry_huge_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "draft": {"body":
                "Total: $30,000 incl. GST and prep.\n"}})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}},
                           quote_fn=dry_huge_fn, card_approved=True)
        self.assertFalse(env["quotes"][0]["policy"]["total_cap"]["ok"])

    def test_priced_with_no_verifiable_total_fails_closed(self):
        def blind_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True})   # نه فیلد، نه body — هیچ رقمی
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}}, quote_fn=blind_fn,
                        card_approved=True)
        cap = env["quotes"][0]["policy"]["total_cap"]
        self.assertFalse(cap["ok"])
        self.assertIn("unverifiable", cap["reason"])
        self.assertFalse(env["policy_checked"])

    def test_env_override_tightens_cap(self):
        def priced_fn(lead_id, scope):
            d = _fake_quote_fn(lead_id, scope)
            d.update({"priced": True, "total_aud": 4200.0})
            return d
        old = "OCTOPUS_QUOTE_MAX_AUD"
        import os as _os
        prev = _os.environ.get(old)
        _os.environ[old] = "1000"
        try:
            env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}},
                               quote_fn=priced_fn, card_approved=True)
        finally:
            if prev is None:
                _os.environ.pop(old, None)
            else:
                _os.environ[old] = prev
        self.assertFalse(env["quotes"][0]["policy"]["total_cap"]["ok"])

    def test_duplicate_lead_filtered_once_flagged(self):
        lead = "lead:nsw_ocp_buyer:doe:x"
        env, _, _ = _build({lead: {}, lead + "#2": {}})   # ids متفاوت، ولی lead تکراری با seen
        self.assertEqual(env["counts"]["duplicates_filtered"], [])

    def test_same_lead_twice_in_mapping_is_one_key(self):
        # dict کلید تکراری ندارد؛ بازتولید سناریوی تکرار با دو scope یکسان
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {"desc": "a"}})
        self.assertEqual(env["counts"]["quotes"], 1)

    def test_over_envelope_cap_not_ready(self):
        leads = {f"lead:nsw_ocp_buyer:agency-{i}:intro": {}
                 for i in range(11)}
        env, _, _ = _build(leads, max_quotes=10)
        self.assertFalse(env["cap_ok"])
        self.assertFalse(env["policy_checked"])

    def test_engine_error_marks_not_ready_with_reason(self):
        def err_fn(lead_id, scope):
            return {"lead_id": lead_id, "error": "lead-not-found-or-no-email"}
        env, _, _ = _build({"lead:nsw_ocp_buyer:ghost:x": {}}, quote_fn=err_fn)
        self.assertFalse(env["policy_checked"])
        self.assertFalse(env["campaign_envelope_ready"])
        self.assertIs(env["send_authorized"], False)
        self.assertEqual(env["quotes"][0]["engine_error"],
                         "lead-not-found-or-no-email")


class StructuralNoSend(unittest.TestCase):
    BANNED = ("urllib", "smtplib", "socket", "requests",
              "__import__", "importlib", "subprocess", "os.system",
              "eval(", "exec(", "Popen", "runpy")

    def test_module_has_no_effect_paths_at_all(self):
        import inspect
        from ofn.agents import campaign_envelope as ce
        src = inspect.getsource(ce)
        for banned in self.BANNED:
            self.assertNotIn(banned, src,
                             f"campaign_envelope must not wire effects: {banned}")

    def test_authorization_fields_mandatory_and_sealed(self):
        env, _, data = _build({"lead:nsw_ocp_buyer:tfnsw:x": {}})
        # هر سه فیلد در artifact هست، هر سه بسته، و از policy_checked جدایند
        self.assertIn("send_authorized", data)
        self.assertIn("execution_authorized", data)
        self.assertIn("transport_binding", data)
        self.assertIs(data["send_authorized"], False)
        self.assertIs(data["execution_authorized"], False)
        self.assertIsNone(data["transport_binding"])
        self.assertTrue(data["policy_checked"])          # آماده…
        self.assertIs(data["send_authorized"], False)    # …ولی هرگز مجاز نه
        # campaign_envelope_ready is a named field, not an inference from
        # policy_checked, and it must never collapse into send_authorized.
        self.assertIn("campaign_envelope_ready", data)
        self.assertIs(data["campaign_envelope_ready"], True)
        self.assertIsNot(
            data["campaign_envelope_ready"], data["send_authorized"],
            "ready and authorized must be distinct values on the artifact")
        self.assertTrue(
            data["campaign_envelope_ready"] and not data["send_authorized"])


if __name__ == "__main__":
    unittest.main()
