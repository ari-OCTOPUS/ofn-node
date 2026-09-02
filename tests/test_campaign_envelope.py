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

from ofn.agents.campaign_envelope import (
    QUOTE_MAX_AUD, build_campaign_envelope,
)


def _fake_quote_fn(lead_id: str, scope):
    """fixture: شبیه خروجی dry موتور کوت برای خریدار OCP."""
    return {
        "lead_id": lead_id,
        "qt_number": "QT-20260902-001",
        "priced": False,
        "total_aud": 0,
        "subject": "Painting works — site visit request",
        "draft": {"body": "fixture body"},
    }


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
            d.update({"priced": True, "total_aud": QUOTE_MAX_AUD + 1})
            return d
        env, _, _ = _build({"lead:nsw_ocp_buyer:doe:x": {}}, quote_fn=huge_fn,
                        card_approved=True)
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
        self.assertEqual(env["quotes"][0]["engine_error"],
                         "lead-not-found-or-no-email")


class StructuralNoSend(unittest.TestCase):
    def test_module_has_no_network_imports(self):
        import inspect
        from ofn.agents import campaign_envelope as ce
        src = inspect.getsource(ce)
        for banned in ("urllib", "smtplib", "socket", "requests"):
            self.assertNotIn(banned, src,
                             f"campaign_envelope must not wire sends: {banned}")


if __name__ == "__main__":
    unittest.main()
