"""ST-3 — the studio shell, checked against the directive's hard budgets.

`DESIGN-DIRECTIVE.md` says its numbers are not negotiable, so they are
assertions rather than intentions. Every one of them came from a real
failure, and a budget nobody measures is a preference.

The reference file `web/saba-stack.html` is kept unchanged as the design
source. `web/studio.html` is what is served, and it is the one tested here —
the reference broke several of its own rules, which is exactly why the rules
needed a test rather than a reader.
"""

from __future__ import annotations

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL = os.path.join(ROOT, "web", "studio.html")
SRC = open(SHELL, encoding="utf-8").read()
CSS = re.search(r"<style>(.*?)</style>", SRC, re.S).group(1)
JS = re.sub(r"/\*.*?\*/|<!--.*?-->", "", SRC, flags=re.S)

PEOPLE = ("سبا", "ملیحه", "عباس", "اسدی")


class TestNobodyIsNamedBeforeAuth(unittest.TestCase):
    """The directive's fourth self-check, and the ziman lesson that produced
    it. The reference file failed this in its `<title>`."""

    def test_the_title_names_nobody(self):
        title = re.search(r"<title>(.*?)</title>", SRC, re.S).group(1)
        for person in PEOPLE:
            self.assertNotIn(person, title)

    def test_no_person_is_written_into_the_markup(self):
        body = re.sub(r"<!--.*?-->", "", SRC, flags=re.S)
        for person in PEOPLE:
            self.assertNotIn(person, body,
                             f"{person} is served before anyone authenticates")

    def test_the_name_comes_from_the_verified_session(self):
        self.assertIn("out.first_name", JS)
        self.assertIn("greet(OFN.who)", JS)

    def test_the_greeting_is_written_as_text_not_markup(self):
        body = re.search(r"function greet\(name\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(body)
        self.assertIn("textContent", body.group(1))
        self.assertNotIn("innerHTML", body.group(1))


class TestMotionBudget(unittest.TestCase):
    """One ambient animation, slower than 60s. Everything else must report a
    state change — "if you cannot say what a movement announces, delete it"."""

    def test_exactly_one_ambient_animation(self):
        infinite = re.findall(r"animation:\s*([\w-]+)\s+([\d.]+)s[^;]*infinite", CSS)
        self.assertEqual(len(infinite), 1,
                         f"ambient animations: {[n for n, _ in infinite]}")

    def test_the_ambient_animation_is_slower_than_sixty_seconds(self):
        name, secs = re.findall(
            r"animation:\s*([\w-]+)\s+([\d.]+)s[^;]*infinite", CSS)[0]
        self.assertGreaterEqual(float(secs), 60.0, f"{name} is too fast")

    def test_no_bounce_or_overshoot(self):
        """The easing must not go outside 0..1 on the second control point."""
        for curve in re.findall(r"cubic-bezier\(([^)]*)\)", CSS):
            nums = [float(x) for x in curve.split(",")]
            self.assertGreaterEqual(nums[3], 0.0, curve)
            self.assertLessEqual(nums[3], 1.0, curve)

    def test_transitions_stay_within_the_stated_ceiling(self):
        self.assertRegex(CSS, r"--t:\s*3[0-4]\dms")


class TestDepthMeansOneThing(unittest.TestCase):
    """"Closer = more decided". Three layers, back layers textless."""

    def test_at_most_three_z_layers(self):
        """Distinct depths, not occurrences. `:active` restates the front
        layer's own depth so the press does not also move it forward —
        counting text matches called that a fourth layer."""
        depths = set(re.findall(r"translateZ\((-?[\d.]+)px\)", CSS))
        self.assertLessEqual(len(depths), 3, f"z depths: {sorted(depths)}")

    def test_the_back_layers_carry_no_text(self):
        """If their headings could be read they would become three
        simultaneous decisions, which is the whole thing this is against."""
        for cls in ("b2", "b3"):
            tag = re.search(rf'<div class="sheet back {cls}"\s*>(.*?)</div>',
                            SRC, re.S)
            self.assertIsNotNone(tag, cls)
            self.assertEqual(tag.group(1).strip(), "")

    def test_reduced_motion_flattens_the_stack_into_a_list(self):
        """Not just "stop animating" — cards on top of each other without
        movement are unusable."""
        block = re.search(r"@media \(prefers-reduced-motion:reduce\)\{(.*?)\n\}",
                          CSS, re.S)
        self.assertIsNotNone(block)
        self.assertIn("position:static", block.group(1))


class TestTheThreeBranchesThatAreNotOptional(unittest.TestCase):
    def test_reduced_motion(self):
        self.assertIn("@media (prefers-reduced-motion:reduce)", CSS)

    def test_reduced_transparency(self):
        """Missing from the reference file. Glass becomes a solid surface,
        not merely a fainter glass."""
        self.assertIn("@media (prefers-reduced-transparency:reduce)", CSS)

    def test_forced_colors(self):
        self.assertIn("@media (forced-colors:active)", CSS)


class TestGatesWorkOnTheOldestDevice(unittest.TestCase):
    """"A gate that is open on the oldest device is not a gate."" Both of
    these are gates, and both rely on features newer than the Telegram
    WebView floor."""

    def test_the_consent_lock_has_a_script_fallback(self):
        """Without `:has()` the publish button would be live with no consent
        recorded — a gate that fails OPEN, the only kind that matters."""
        self.assertIn("selector(:has(*))", JS)
        self.assertIn("gate.classList.toggle('locked'", JS)
        self.assertIn(".gate.locked .cta-main", CSS)

    def test_the_confirm_sheet_has_a_script_fallback(self):
        self.assertIn("HTMLElement.prototype.hasOwnProperty('popover')", JS)
        self.assertIn("function openTray", JS)
        self.assertIn("[popover][data-open]", CSS)

    def test_the_consent_target_is_at_least_forty_four_pixels(self):
        self.assertRegex(CSS, r"\.tick\{width:44px;height:44px")


class TestNoAmbiguousLabels(unittest.TestCase):
    def test_the_primary_button_says_what_happens(self):
        self.assertIn("همین را منتشر کن", SRC)
        self.assertNotIn(">تأیید<", SRC)

    def test_a_safe_option_sits_beside_it(self):
        """Otherwise opening the app is itself an irreversible decision."""
        self.assertIn("فعلاً بماند", SRC)

    def test_the_confirm_sheet_says_where_it_goes(self):
        """To the outbox, and no further. Nothing here reaches a platform."""
        self.assertIn("صف خروج", SRC)
        self.assertIn("تا\n      تأیید آری هیچ‌جا نمی‌رود", SRC)


class TestPersianAndRtl(unittest.TestCase):
    def test_letter_spacing_is_zero(self):
        """Any tracking breaks the joins between Arabic letters."""
        self.assertIn("letter-spacing:0", CSS)
        self.assertNotIn("letter-spacing:normal", CSS)

    def test_line_height_has_room_for_diacritics(self):
        self.assertIn("line-height:1.85", CSS)

    def test_no_caption_is_smaller_than_thirteen_pixels(self):
        """Below 13px the diacritics sit in the baseline on a 2x screen. The
        reference file broke this in six places."""
        small = [s for s in re.findall(r"font-size:([\d.]+)px", CSS)
                 if float(s) < 13.0]
        self.assertEqual(small, [], f"font sizes below 13px: {small}")

    def test_layout_uses_logical_properties(self):
        self.assertIn("inset-inline", CSS)
        self.assertNotRegex(CSS, r"\bmargin-left:|\bpadding-right:")

    def test_no_external_font_is_fetched(self):
        """fonts.gstatic.com does not open from Iran."""
        self.assertNotIn("fonts.googleapis.com", SRC)
        self.assertNotIn("fonts.gstatic.com", SRC)


class TestHardBudgets(unittest.TestCase):
    def test_at_most_two_backdrop_filters(self):
        uses = [u for u in re.findall(r"backdrop-filter:([^;}]+)", CSS)
                if "none" not in u]
        self.assertLessEqual(len(uses), 4)      # each is paired with -webkit-

    def test_no_backdrop_filter_is_animated(self):
        for block in re.findall(r"transition:([^;}]+)", CSS):
            self.assertNotIn("backdrop-filter", block)

    def test_the_primary_button_is_sixteen_pixels(self):
        cta = re.search(r"\.cta\{(.*?)\}", CSS, re.S).group(1)
        self.assertIn("font-size:16px", cta)
        self.assertIn("font-weight:600", cta)


class TestNothingIsInvented(unittest.TestCase):
    """The mock had a date, a caption, a gauge reading and an advisor
    sentence, all made up. A studio screen that looks alive while
    disconnected shows a publish button that does nothing."""

    def test_no_sample_mode(self):
        # `JS`, not `SRC`: comments legitimately name the thing they warn
        # against, and one here explains why "نمونه" alone was not enough.
        self.assertNotIn("نمونه", JS)

    def test_the_disconnected_state_disables_every_action(self):
        block = re.search(r"function showState\([^)]*\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(block)
        self.assertIn("pointerEvents = 'none'", block.group(1))

    def test_the_advisor_line_starts_empty(self):
        self.assertIn('id="n-body"', SRC)
        self.assertNotIn("۳۸ پست", SRC)

    def test_the_gauge_starts_with_nothing_measured(self):
        self.assertIn("هنوز چیزی اندازه گرفته نشده", SRC)

    def test_the_connection_reason_is_specific(self):
        for kind in ("no-shell", "rejected", "unreachable", "not-allowed"):
            self.assertIn(f"'{kind}'", JS)


if __name__ == "__main__":
    unittest.main()


class TestTheShellIsWiredToTheNode(unittest.TestCase):
    """The mini app has to actually do something. Every route it needs, and
    the two places where it must not decide for itself."""

    def test_it_reads_the_board_in_one_request(self):
        """Four requests would let the parts arrive out of order and render a
        card whose consent state belongs to a different draft."""
        self.assertIn("/api/v1/studio/board", JS)

    def test_it_publishes_through_the_node(self):
        self.assertIn("/publish", JS)
        self.assertIn("function publishCurrent", JS)

    def test_the_consent_tick_is_not_an_input_she_can_assert(self):
        """The node decides consent. A tick that could be checked here would
        be a second implementation of the rule, and the screen's copy would
        be the one that is wrong."""
        self.assertIn("box.disabled = true", JS)
        self.assertIn("d.consent_ok", JS)

    def test_the_page_does_not_rebuild_the_consent_rule(self):
        """It reads the verdict. It does not look at releases, dates or
        scopes — those are ingredients, and re-deriving from them is how two
        implementations drift."""
        # Field reads, not substrings: `out_of_scope` is a refusal *name* the
        # page is supposed to have words for, and matching it as "scope"
        # failed a page that was doing the right thing.
        for ingredient in ("expires_at", "revoked_at", "signed_at",
                           "releases", "document_sha256"):
            self.assertNotRegex(JS, rf"[.\[]\s*['\"]?{ingredient}\b",
                                f"the shell reads {ingredient}")

    def test_every_refusal_reason_has_words(self):
        """A gap shown as `out_of_scope` sends her looking through a folder
        instead of at one name."""
        for reason in ("no_release", "expired", "revoked", "out_of_scope",
                       "not_yet_in_force"):
            self.assertIn(reason, JS)

    def test_the_safe_option_actually_does_something(self):
        """A safe option with no effect teaches that buttons sometimes have
        no effect."""
        self.assertIn("id=\"later\"", SRC)
        self.assertIn("cursor = (cursor + 1)", JS)

    def test_questions_come_before_decisions(self):
        """A decision made on a stale fact is worse than a decision
        deferred."""
        body = re.search(r"function drawFront\(\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(body)
        self.assertLess(body.group(1).index("at < queue.length"),
                        body.group(1).index("currentDraft()"))
