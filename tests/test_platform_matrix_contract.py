"""Contract tests for the platform policy matrix.

The matrix is what stops a caption from reaching a platform that will ban
the account for it. Its rules are not advisory — each is a structural
refusal. These tests pin every refusal and the one acceptance, so a
change to the screen has to declare itself by breaking a test.
"""

import unittest

from ofn.kernel.platform_matrix import (
    PlatformMatrix, PlatformRule, ScreenVerdict, empty_matrix,
)


def _rule(**kw):
    base = dict(
        name="test", layer="A", risk="YELLOW",
        adult_policy="wellness_only", direct_adult_link_allowed=False,
        caption_max=100,
        allowed_framing=("beauty", "wellness"),
        blocked_framing=("fetish",),
        adult_link_markers=("onlyfans", "nudes"),
        solicitation_markers=("dm for", "escort"),
    )
    base.update(kw)
    return PlatformRule(**base)


class TestEmptyMatrix(unittest.TestCase):
    def test_empty_matrix_refuses_everything_as_unknown(self):
        m = empty_matrix()
        v = m.screen(platform="anything", caption="hi", framing="beauty",
                     sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:unknown")


class TestScreenRefusals(unittest.TestCase):
    def setUp(self):
        self.m = PlatformMatrix({"p": _rule()})

    def test_minor_targeting_refused_first_regardless_of_rest(self):
        v = self.m.screen(platform="p", caption="hi", framing="beauty",
                          sensitivity="general", targets_minors=True)
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "safety:minor-targeting-denied")

    def test_restricted_never_leaves(self):
        v = self.m.screen(platform="p", caption="hi", framing="beauty",
                          sensitivity="restricted")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "advisor:restricted-never-leaves")

    def test_empty_caption_refused(self):
        v = self.m.screen(platform="p", caption="   ", framing="beauty",
                          sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "content:caption-empty")

    def test_caption_too_long_refused(self):
        v = self.m.screen(platform="p", caption="x" * 101, framing="beauty",
                          sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:caption-too-long")

    def test_blocked_framing_refused(self):
        v = self.m.screen(platform="p", caption="hi", framing="fetish",
                          sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:blocked-framing")

    def test_framing_not_in_allowlist_refused(self):
        v = self.m.screen(platform="p", caption="hi", framing="educational",
                          sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:framing-not-allowed")

    def test_direct_adult_link_refused_when_forbidden(self):
        v = self.m.screen(platform="p", caption="check my onlyfans page",
                          framing="beauty", sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:direct-adult-link-blocked")

    def test_wellness_platform_refuses_solicitation_markers(self):
        v = self.m.screen(platform="p", caption="dm for prices",
                          framing="beauty", sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:sexual-solicitation-blocked")

    def test_explicit_adult_link_flag_overrides_caption_sniff(self):
        # Caller knows the bio link is adult even if caption is clean.
        v = self.m.screen(platform="p", caption="clean caption",
                          framing="beauty", sensitivity="general",
                          has_direct_adult_link=True)
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:direct-adult-link-blocked")


class TestScreenAcceptance(unittest.TestCase):
    def setUp(self):
        self.m = PlatformMatrix({"p": _rule()})

    def test_clean_beauty_general_accepted(self):
        v = self.m.screen(platform="p", caption="a soft beauty moment",
                          framing="beauty", sensitivity="general")
        self.assertTrue(v.ok)
        self.assertEqual(v.rule, "platform:ok")


class TestLabeledAdult(unittest.TestCase):
    def test_allowed_labeled_requires_the_label(self):
        rule = _rule(adult_policy="allowed_labeled",
                     direct_adult_link_allowed=True,
                     allowed_framing=("adult_labeled", "beauty"))
        m = PlatformMatrix({"p": rule})
        # Adult framing without the label → refused.
        v = m.screen(platform="p", caption="hi", framing="adult_labeled",
                     sensitivity="general", adult_label=False)
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:adult-label-required")
        # Same with the label → accepted.
        v = m.screen(platform="p", caption="hi", framing="adult_labeled",
                     sensitivity="general", adult_label=True)
        self.assertTrue(v.ok)


if __name__ == "__main__":
    unittest.main()
