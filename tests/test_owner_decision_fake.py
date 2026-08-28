"""The decision card: whole, one at a time, and honest about its limits.

The card is the owner's only view of what she is approving, so these tests
read it the way she does. Every one of the twelve fields must be on it —
a field the card omits is a question the owner never got to ask. The three
buttons must be there, and two decisions must never share a message,
because an approve button pressed for one question must not spend itself on
another.

`validate` is the gate before a card is shown at all: presence, sha
formats, the one expiry format. What it deliberately does NOT check is
whether payload_sha actually hashes exact_payload — that binding is the
executor's to enforce at send time (see test_executor_fake), and a card
that silently "fixed" a mismatch would hide exactly the tampering the
hash is there to catch.
"""

import hashlib
import unittest

from ofn.adapters.owner_decision import (
    APPROVE_ONCE,
    BUTTONS,
    DECISION_FIELDS,
    DETAILS,
    OwnerDecision,
    REJECT,
    render_fake,
    validate,
)

PAYLOAD = "Follow up on the exterior repaint quote in Newtown."
EXPIRY = "2027-01-15T09:00:00Z"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make(**over) -> OwnerDecision:
    values = dict(
        decision_id="D-138-0001",
        run_id="run-138-1",
        lane="painting",
        action="send_follow_up",
        recipient_masked="telegram:98***21",
        exact_payload=PAYLOAD,
        payload_sha=sha(PAYLOAD),
        artifact_sha=sha("artifact-bytes"),
        verdict_sha=sha("verdict-bytes"),
        idempotency_key="idem-138-1",
        expires_at=EXPIRY,
        rollback="pause the painting lane; recall nothing (nothing sent)",
    )
    values.update(over)
    return OwnerDecision(**values)


class RenderTests(unittest.TestCase):
    def test_card_shows_every_field_and_every_button(self):
        decision = make()
        card = render_fake(decision)
        self.assertEqual(len(DECISION_FIELDS), 12)
        for name in DECISION_FIELDS:
            self.assertIn(name, card)
            self.assertIn(getattr(decision, name), card)
        for label in (APPROVE_ONCE, REJECT, DETAILS):
            self.assertEqual(card.count(f"[{label}]"), 1, label)
        self.assertEqual(BUTTONS, (APPROVE_ONCE, REJECT, DETAILS))
        # It is a plain-text card: nothing to click, nothing to render.
        self.assertNotIn("<", card)

    def test_one_decision_per_message(self):
        with self.assertRaises(ValueError):
            render_fake([make(), make(decision_id="D-138-0002")])
        # A container of exactly one is fine; a card is still one question.
        solo = render_fake([make()])
        self.assertIn("D-138-0001", solo)
        with self.assertRaises(ValueError):
            render_fake([])
        with self.assertRaises(TypeError):
            render_fake("not a decision")

    def test_rendering_sends_nothing(self):
        # render_fake returns a string and touches nothing else: the same
        # decision rendered twice is the same card, and no channel exists
        # here to carry it. This test exists so that if a "render" ever
        # starts returning a sendable object, it fails loudly.
        card = render_fake(make())
        self.assertIsInstance(card, str)
        self.assertEqual(card, render_fake(make()))


class ValidateTests(unittest.TestCase):
    def test_a_whole_decision_validates(self):
        self.assertEqual(validate(make()), [])

    def test_missing_fields_are_named(self):
        for blank in ("", "   "):
            errors = validate(make(decision_id=blank))
            self.assertTrue(any("decision_id" in e for e in errors), errors)
        errors = validate(make(rollback=""))
        self.assertTrue(any("rollback" in e for e in errors), errors)
        # Everything else still whole: exactly one complaint.
        self.assertEqual(len(errors), 1)

    def test_sha_fields_must_be_64_lowercase_hex(self):
        for field in ("payload_sha", "artifact_sha", "verdict_sha"):
            for bad in ("deadbeef", "X" * 64, "z" * 64, "a" * 63, ""):
                errors = validate(make(**{field: bad}))
                if bad == "":
                    self.assertTrue(any(f"{field}: missing" in e
                                        for e in errors))
                else:
                    self.assertTrue(any(field in e for e in errors), bad)
            self.assertEqual(validate(make(**{field: "a" * 64})), [])

    def test_expiry_has_exactly_one_format(self):
        for bad in ("2026-08-28", "2026-8-28T00:00:00Z",
                    "2026-08-28T00:00:00", "2026-08-28 00:00:00Z",
                    "2026-08-28T00:00:00.000Z", "2026-13-40T99:99:99Z"):
            errors = validate(make(expires_at=bad))
            self.assertTrue(any("expires_at" in e for e in errors), bad)
        self.assertEqual(validate(make(expires_at=EXPIRY)), [])

    def test_validate_does_not_verify_the_payload_binding(self):
        # A decision whose payload_sha does not hash its own exact_payload
        # is structurally valid and executably wrong. validate() passes it
        # through; the executor is what must refuse it.
        mismatched = make(payload_sha=sha("different bytes"))
        self.assertEqual(validate(mismatched), [])
        self.assertNotEqual(mismatched.payload_sha, sha(mismatched.exact_payload))


if __name__ == "__main__":
    unittest.main()
