"""D-28: three fields stay unforgeable; the rest may proceed in parallel."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import unittest

from ofn.adapters.consent_store import ConsentError, ConsentStore
from ofn.adapters.platform_matrix_loader import default_matrix_path, load_matrix
from ofn.kernel.advisor_gate import Collection, Sensitivity, may_send_image
from ofn.config import GATE_OPEN_UNTIL_UTC
from octopus_survival.paint_followup import (
    RULE_NOT_ON_BODY,
    PaintFollowUpError,
    propose_follow_up,
)
from ofn.kernel.release_switch import RULE_OWNER_TWO_STEP
from tools.partner_attestation import independently_observed, list_receipts
from tests.tmpdir import temp_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRECTIVE = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "D-28-OWNER-DIRECTIVE.json",
)
D26 = os.path.join(
    ROOT,
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "OWNER-RATIFICATION.json",
)
SABA_TEMPLATE = os.path.join(ROOT, "docs", "consent", "SABA-RELEASE-20260902.md")
ADVISOR = os.path.join(ROOT, "ofn", "kernel", "advisor_gate.py")


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestThreeFieldsStayUnforged(unittest.TestCase):
    def test_partner_voices_still_false_without_three_hashes(self):
        d26 = _load(D26)
        d28 = _load(DIRECTIVE)
        self.assertFalse(d26["partner_voices_independently_observed"])
        self.assertFalse(d28["partner_voices_independently_observed"])
        report = independently_observed(list_receipts(ROOT))
        self.assertFalse(report["independently_observed"])
        self.assertFalse(report["ready"])

    def test_secret_rotation_receipt_is_unrotated_not_rotated(self):
        data = _load(DIRECTIVE)
        self.assertEqual(data["secret_rotation"], "risk_accepted_unrotated")
        self.assertNotEqual(data["secret_rotation"], "rotated")
        self.assertEqual(data["gate_open_until_utc"], "2026-09-16")
        self.assertEqual(GATE_OPEN_UNTIL_UTC, "2026-09-16")
        self.assertFalse(data["keep_gates_open_committed_default"])
        self.assertFalse(data["wire_outbound_committed_default"])

    def test_saba_release_is_not_a_boolean_and_was_not_recorded(self):
        data = _load(DIRECTIVE)
        self.assertEqual(data["saba_release"]["status"], "unsigned_template_only")
        self.assertFalse(data["saba_release"]["record_release_called"])
        self.assertFalse(data["saba_release"]["pdf_in_git"])
        self.assertTrue(os.path.isfile(SABA_TEMPLATE))
        with open(SABA_TEMPLATE, encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn("امضانشده", body)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.assertEqual(len(digest), 64)
        status = _load(os.path.join(ROOT, "docs", "consent",
                                    "SABA-RELEASE-STATUS.json"))
        self.assertFalse(status["signed"])
        self.assertFalse(status["record_release_called"])
        self.assertEqual(status["template_sha256"], digest)
        self.assertIn("not a signed-document hash", status["note"])


class TestConsentStoreStillRefusesShortcuts(unittest.TestCase):
    def test_record_release_requires_hash_ref_subject(self):
        path = os.path.join(temp_dir(self), "consent.sqlite")
        store = ConsentStore(path)
        self.addCleanup(store.close)
        with self.assertRaises(ConsentError):
            store.record_release(
                "saba-release-20260902",
                "saba",
                scope="telegram_channel bluesky",
                signed_at=1,
                document_ref="docs/consent/x.pdf",
                document_sha256="a" * 64,
                recorded_by="owner",
            )
        store.add_subject("studio", "saba", "Saba", now_epoch_s=1)
        with self.assertRaises(ConsentError):
            store.record_release(
                "saba-release-20260902",
                "saba",
                scope="telegram_channel bluesky",
                signed_at=1,
                document_ref="docs/consent/x.pdf",
                document_sha256="",
                recorded_by="owner",
            )


class TestAdvisorGateStaysParameterless(unittest.TestCase):
    def test_no_ask_sensitivity_and_restricted_never_leaves(self):
        with open(ADVISOR, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src, filename=ADVISOR)
        names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        self.assertIn("may_send_image", names)
        self.assertEqual({item.value for item in Sensitivity},
                         {"restricted", "general"})
        self.assertIn('A third — "ask me"', src)
        restricted = Collection("c1", "x", "y", Sensitivity.RESTRICTED)
        self.assertFalse(may_send_image(restricted))
        general = Collection("c1", "x", "y", Sensitivity.GENERAL)
        self.assertTrue(may_send_image(general))


class TestMatrixEdgeStaysInsideTos(unittest.TestCase):
    def test_minors_and_restricted_still_refused(self):
        matrix = load_matrix(default_matrix_path())
        for key in matrix.rules:
            v = matrix.screen(
                platform=key, caption="hi", framing="beauty",
                sensitivity="restricted",
            )
            self.assertFalse(v.ok)
            denied = matrix.screen(
                platform=key, caption="hi", framing="beauty",
                sensitivity="general", targets_minors=True,
            )
            self.assertEqual(denied.rule, "safety:minor-targeting-denied")

    def test_invite_opt_in_is_allowed_on_public_wellness(self):
        matrix = load_matrix(default_matrix_path())
        v = matrix.screen(
            platform="instagram",
            caption="atelier hours this week — join the private list",
            framing="invite_opt_in",
            sensitivity="general",
        )
        self.assertTrue(v.ok, v.rule)

    def test_layer_c_still_blocks_direct_adult_link(self):
        matrix = load_matrix(default_matrix_path())
        v = matrix.screen(
            platform="instagram",
            caption="see my onlyfans",
            framing="beauty",
            sensitivity="general",
        )
        self.assertFalse(v.ok)


class TestPaintFollowUpDoesNotSendHere(unittest.TestCase):
    def test_two_step_required_and_dry_run_default(self):
        with self.assertRaises(PaintFollowUpError) as ctx:
            propose_follow_up(
                lead_id="PAINT-L5-001",
                body="quote ready",
                owner_step1=True,
                owner_step2=False,
            )
        self.assertEqual(str(ctx.exception), RULE_OWNER_TWO_STEP)
        draft = propose_follow_up(
            lead_id="PAINT-L5-001",
            body="quote ready for Cheltenham",
            owner_step1=True,
            owner_step2=True,
        )
        self.assertTrue(draft["dry_run"])
        self.assertFalse(draft["sent"])

    def test_live_send_refused_off_the_lead_body(self):
        with self.assertRaises(PaintFollowUpError) as ctx:
            propose_follow_up(
                lead_id="PAINT-L5-001",
                body="quote ready",
                owner_step1=True,
                owner_step2=True,
                dry_run=False,
                on_lead_body=False,
            )
        self.assertEqual(str(ctx.exception), RULE_NOT_ON_BODY)
