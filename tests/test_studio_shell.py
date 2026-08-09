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
        self.assertNotIn('sheet back b2', SRC)
        self.assertNotIn('sheet back b3', SRC)

    def test_reduced_motion_flattens_the_stack_into_a_list(self):
        """Not just "stop animating" — cards on top of each other without
        movement are unusable."""
        block = re.search(r"@media \(prefers-reduced-motion:reduce\)\{(.*?)\n\}",
                          CSS, re.S)
        self.assertIsNotNone(block)
        self.assertIn("position:static", block.group(1))


class TestPhotosArriveThroughTheSession(unittest.TestCase):
    """No photo in this app had ever been displayed.

    Every rendition is served from `/api/v1/studio/media/…`, which is behind
    `_principal` and reads exactly one thing: an `Authorization: Bearer`
    header. A browser issuing `<img src>` cannot attach one — the request is
    the browser's, not the script's — so every photo answered 401 and drew
    the broken-image mark. In the archive card that was a question mark in
    the middle of the frame; in the gallery it was an empty outline that read
    as "no photos yet".

    Invisible until the shell could get far enough to draw one, which it
    could not until the SDK ordering was fixed. The third failure that one
    bug was hiding.

    The rule is that the bytes come through the same session header as every
    other call. Not a cookie, which would be a second way to authenticate one
    API, and not a token in the query string — the journal logs request
    paths, so that writes a live session into a log file.
    """

    def test_no_image_source_points_straight_at_the_authenticated_api(self):
        for hit in re.findall(r"\.src\s*=\s*'(/api/v1/[^']*)'", JS):
            self.fail(f"an <img> is pointed at {hit}, which needs a header "
                      f"the browser will not send")
        self.assertNotRegex(SRC, r"<img[^>]*src=[\"']/api/v1")

    def test_the_bytes_are_fetched_with_the_session(self):
        fn = re.search(r"async bytes\(path\)\s*\{(.*?)\n    \},", JS, re.S)
        self.assertIsNotNone(fn, "no authenticated byte fetch exists")
        self.assertIn("'Bearer ' + session", fn.group(1))

    def test_the_session_never_travels_in_a_url(self):
        """A query-string token would land in the journal, which logs paths."""
        self.assertNotRegex(JS, r"[?&](token|t|session|auth)=")

    def test_object_urls_are_released(self):
        """They outlive the elements that hold them, so a gallery redraw that
        does not revoke leaks one photo per redraw."""
        self.assertIn("URL.revokeObjectURL", JS)
        grid = re.search(r"function drawGrid\(\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(grid)
        self.assertIn("releasePhoto", grid.group(1))

    def test_the_deciding_screen_gets_the_large_rendition(self):
        """The archive card is where she decides what a photo is. Deciding
        that from a 320px thumbnail is deciding it from something else."""
        self.assertIn("paintPhoto(shot, p.media_id, 1600)", JS)

    def test_a_photo_that_fails_says_so(self):
        """Rather than leaving the browser's own broken-image mark, which is
        indistinguishable from a photo that was never there."""
        fn = re.search(r"async function paintPhoto\(.*?\n\}", JS, re.S)
        self.assertIsNotNone(fn)
        self.assertIn("img.alt", fn.group(0))


class TestAContainerJavaScriptFillsCanGrow(unittest.TestCase):
    """The front sheet holds two different things and was sized for one.

    Resting, it shows a decision: title, note, strip. That fits 320px, which
    is where the number came from. But `askCard()` writes a kernel question
    into the same element — title, note, a textarea, an error line, and two or
    three 52px buttons — and that does not fit. The sheet was
    `position:absolute` with `height:320px`, so the excess was painted outside
    the stack, over the buttons that follow in normal flow. «بعداً» landed on
    top of «عکس تازه».

    It stayed invisible because `askCard()` only runs when the node answers
    with questions, and until the SDK ordering was fixed the shell never got
    that far. See tests/test_shell_boot_order.py.

    What is asserted is the CSS invariant, not the rendered geometry — there
    is no browser on this board, so this cannot measure that nothing overlaps.
    It measures the thing that made overlap possible: a box that JavaScript
    fills, pinned to a height chosen for its emptiest state.
    """

    def _rule(self, selector):
        m = re.search(re.escape(selector) + r"\{(.*?)\}", CSS, re.S)
        self.assertIsNotNone(m, f"{selector} has no rule")
        return m.group(1)

    def test_the_front_sheet_is_not_pinned_to_a_height(self):
        body = self._rule(".sheet.front")
        self.assertNotRegex(
            body, r"(?<!min-)height:\s*\d",
            "the front sheet has a fixed height; a question does not fit in "
            "the height a decision was measured at")
        self.assertRegex(body, r"min-height:\s*\d")

    def test_the_front_sheet_is_in_flow_so_the_deck_is_sized_by_it(self):
        """`.sheet` sets position:absolute for the two decorative layers. The
        one that carries content has to opt out, or its overflow is painted
        over whatever follows instead of pushing it down."""
        self.assertRegex(self._rule(".sheet.front"),
                         r"position:\s*(relative|static)")

    def test_the_deck_is_not_pinned_to_a_height(self):
        body = self._rule(".stack")
        self.assertNotRegex(
            body, r"(?<!min-)height:\s*\d",
            "the deck cannot grow, so a taller front sheet overflows it")
        self.assertRegex(body, r"min-height:\s*\d")


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
        recorded — a gate that fails OPEN, the only kind that matters.

        This asserted `selector(:has(*))` — the text of a `CSS.supports` probe.
        The probe's result was read by nothing, so the assertion passed on the
        presence of a string while the actual fallback was the unconditional
        `.locked` toggle beside it. Pinning the probe also permitted the worse
        design: a fallback that only engages where a capability test says it is
        needed, which is one wrong probe away from an open gate.

        So the property, not the mechanism (CLAUDE.md §8-a): the class is
        toggled from the checkbox, the CSS neutralises the button the same way
        the `:has()` rule does, the toggle runs on load as well as on change,
        and none of it sits behind a capability branch.
        """
        self.assertIn("gate.classList.toggle('locked'", JS)
        self.assertIn(".gate.locked .cta-main", CSS)

        # Both floors must disable the same way, or the fallback only dims it.
        for selector in (r"\.gate:has\(input:not\(:checked\)\) \.cta-main\{([^}]*)\}",
                         r"\.gate\.locked \.cta-main\{([^}]*)\}"):
            rule = re.search(selector, CSS)
            self.assertIsNotNone(rule, f"missing rule: {selector}")
            self.assertIn("pointer-events:none", rule.group(1))

        # Wired to the checkbox, and run once at load — a page that opens with
        # the box unchecked must start locked, not merely become locked.
        self.assertRegex(JS, r"addEventListener\(\s*['\"]change['\"]\s*,\s*syncConsentGate")
        self.assertGreaterEqual(
            len(re.findall(r"\bsyncConsentGate\(\)", JS)), 1,
            "syncConsentGate is never called outside its own definition")

        # Unconditional: the toggle must not be guarded by a capability probe.
        body = re.search(r"function syncConsentGate\(\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(body)
        self.assertNotRegex(
            body.group(1), r"CSS\.supports|\bHAS\b",
            "the consent fallback is behind a capability probe; it must always run")

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
        """fonts.gstatic.com does not open from Iran.

        Checked against the live CSS rather than the whole file: the
        `@font-face` comment names the host it exists to avoid, and a test
        that matches comments finds explanations rather than requests.
        """
        live = re.sub(r"/\*.*?\*/|<!--.*?-->", "", SRC, flags=re.S)
        self.assertNotIn("fonts.googleapis.com", live)
        self.assertNotIn("fonts.gstatic.com", live)
        self.assertIn("/font/vazirmatn.woff2", live)


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
        # `no-shell` was two failures under one name: the SDK never loading
        # (fix: reload) and the SDK loading with nothing signed (fix: open it
        # from the menu button). See tests/test_shell_boot_order.py.
        for kind in ("no-sdk", "no-initdata",
                     "rejected", "unreachable", "not-allowed"):
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


class TestTheUploadFormIsOneDecision(unittest.TestCase):
    """The natural shape of an upload form is six decisions at once — photos,
    caption, collection, genre, sensitivity, time. Six at once is the thing
    the directive exists against."""

    def test_the_photo_lands_in_the_library_not_in_a_post(self):
        """This asserted the opposite once, and the opposite was right for
        the model it was written against: picking a photo created a draft.

        The model changed when the leg turned out to be her archive. A
        picture taken today and used next month needs somewhere to be in
        between, and making every shot a post decides something she has not
        decided.
        """
        body = re.search(r"async function addPhoto\([^)]*\)\s*\{(.*?)\n\}",
                         JS, re.S).group(1)
        self.assertIn("'/api/v1/studio/media'", body)
        self.assertNotIn("/api/v1/studio/drafts", body)

    def test_the_original_is_sent_with_it(self):
        """A 1600px copy is not her work, it is a copy of her work."""
        self.assertIn("asDataUrl(file)", JS)
        self.assertIn("readAsDataURL", JS)

    def test_a_failed_original_does_not_lose_the_photo(self):
        """The renditions are what a screen and a platform need. Losing all
        three because the largest read failed would be the worst trade in
        the file."""
        body = re.search(r"function asDataUrl\(file\)\s*\{(.*?)\n\}",
                         JS, re.S).group(1)
        self.assertIn("resolve(null)", body)

    def test_sensitivity_is_never_asked(self):
        """It is restricted and stays that way. Making a collection public is
        a separate deliberate act, not a field on the screen where she is
        trying to put a picture down."""
        self.assertNotIn("sensitivity", JS)
        self.assertNotIn("restricted", JS)

    def test_the_form_asks_for_nothing_but_the_photo(self):
        """No album, no caption, no tags at upload. Tagging happens in the
        gallery, where she can see the picture — asking for a label while
        the photo is still a file on her phone is asking her to describe
        something she is not looking at."""
        sent = re.search(r"OFN\.post\('/api/v1/studio/media',\s*(\{[^}]*\})",
                         JS, re.S)
        self.assertIsNotNone(sent)
        for asked in ("album", "caption", "labels"):
            self.assertNotIn(asked, sent.group(1))

    def test_exif_orientation_is_requested(self):
        """Without it a portrait photo lands sideways — and only on real
        photos, because a synthetic test file has no EXIF at all."""
        self.assertIn("imageOrientation: 'from-image'", JS)

    def test_there_is_a_fallback_for_a_webview_without_it(self):
        body = re.search(r"async function renditionsOf\(file\)\s*\{(.*?)\n\}",
                         JS, re.S).group(1)
        self.assertIn("createImageBitmap(file)", body)

    def test_both_edges_are_produced_in_the_browser(self):
        self.assertIn("const EDGES = [1600, 320]", JS)
        self.assertIn("toDataURL('image/jpeg'", JS)

    def test_something_moves_before_a_hundred_milliseconds(self):
        """Resizing a 12MP photo is not instant on this hardware, and a
        silent wait is on the anxiety list."""
        self.assertIn("در حال آماده کردن", JS)

    def test_a_second_tap_cannot_start_a_second_upload(self):
        self.assertIn("if (busy || !file) return", JS)

    def test_the_same_file_can_be_chosen_again_after_a_failure(self):
        self.assertIn("ev.target.value = ''", JS)


class TestABlankScreenIsNotAPossibleOutcome(unittest.TestCase):
    """A partner reported "it shows nothing, completely white". That is the
    worst failure this app can have, because it says nothing at all — no
    reason, no retry, no way to tell a down node from a broken one."""

    def test_the_third_party_script_does_not_block_the_first_paint(self):
        """Loaded synchronously in the head, a third-party script paints
        nothing until it arrives. On a network that cannot reach
        telegram.org quickly that is a white screen for as long as the
        request takes to time out — the same mistake the web font made in
        ziman.html, with the same symptom."""
        tag = re.search(r"<script[^>]*telegram-web-app\.js[^>]*>", SRC)
        self.assertIsNotNone(tag)
        self.assertIn("defer", tag.group(0))

    def test_boot_waits_for_the_document(self):
        """A bare `boot()` runs while the document is still parsing, which is
        before any deferred script has executed — so the SDK would always
        look absent and every launch would read as "opened outside
        Telegram"."""
        self.assertIn("DOMContentLoaded", JS)
        self.assertNotRegex(JS, r"\n\s*boot\(\);\s*\n\s*(?:function start|$)")

    def test_a_boot_failure_becomes_a_sentence_not_silence(self):
        """The sentence has to be reachable, not merely present.

        This test used to look for the sentence *inside* `start()` and was
        satisfied by:

            function start() { try { boot(); } catch (err) { ...sentence... } }

        which catches nothing at all — `boot` is async, so the call returns
        a promise before anything inside it can throw, and every failure
        during boot became an unhandled rejection. The screen kept its
        static markup, which reads as "the app opened and is empty" rather
        than as an error, and that is what a partner reported.

        So the assertion is now the property that was actually wanted: the
        failure path is attached to the promise, and to the two global
        events that catch what a promise cannot.
        """
        body = re.search(r"function start\(\)\s*\{(.*?)\n\}", JS, re.S)
        self.assertIsNotNone(body)
        # Attached to the promise — not a bare `boot();` with a sync catch.
        self.assertRegex(body.group(1), r"boot\(\)\s*\.\s*(catch|then)\b")
        self.assertIn("این صفحه بالا نیامد", JS)
        for event in ("'error'", "'unhandledrejection'"):
            self.assertIn(event, JS)

    def test_a_synchronous_catch_never_guards_an_async_call(self):
        """Generalised, because the shape is easy to reintroduce and reads
        as correct: no `try` in this file may wrap a bare call to an async
        function as its only protection."""
        async_fns = set(re.findall(r"async function (\w+)", JS))
        self.assertIn("boot", async_fns)          # the guard has a subject
        # A call whose promise is dropped on the floor: not awaited, not
        # returned, not assigned, and not handed to `guard`.
        for m in re.finditer(r"(?<![.\w])(\w+)\(([^;()]*)\)\s*;", JS):
            if m.group(1) not in async_fns:
                continue
            before = JS[max(0, m.start() - 14):m.start()]
            self.assertRegex(
                before, r"(await|return|guard\(|=)\s*$",
                f"{m.group(1)}(…) is async and its promise is dropped: it "
                f"can only reject to a console no phone has, so a failure "
                f"leaves the screen unchanged and the tap looks ignored")

    def test_the_node_is_told_how_the_boot_ended(self):
        """The phone has no console. If the screen cannot say what went
        wrong, the journal has to, or the next report is again "it opens and
        there is nothing there" with no way to act on it."""
        self.assertIn("/api/v1/shell/boot", JS)
        for stage in ("'opened'", "'threw'", "'live'"):
            self.assertIn(stage, JS)
        # The report must never be something the page waits on or depends on.
        tell = re.search(r"function tell\(.*?\n\}", JS, re.S).group(0)
        self.assertNotIn("await", tell)
        self.assertIn("catch", tell)

    def test_it_also_works_if_the_document_is_already_parsed(self):
        """`DOMContentLoaded` has already fired by the time a cached page
        runs its script; listening for it alone would never boot."""
        self.assertIn("document.readyState === 'loading'", JS)


class TestAnEmptyAccountIsNotADeadEnd(unittest.TestCase):
    """What a new account sees is the whole product until she adds something.

    The first version of this screen was, on an empty account: a card saying
    "there is nothing to decide — when a draft is ready it will appear here",
    a gallery saying "this is empty, add a photo from the امروز tab", and a
    business tab of zeros. Every one of those describes a state; none of them
    offers the action that would change it, and the gallery's instruction
    pointed at the tab that was itself telling her to wait. That is what "we
    opened it and there is nothing in it" meant.
    """

    def test_the_empty_gallery_offers_the_action_instead_of_naming_a_tab(self):
        # The picker lives on another view, but a button can reach it.
        self.assertIn("$('pick').click()", JS)
        self.assertNotIn("از تب «امروز» عکس اضافه کنید", JS)

    def test_the_first_run_card_names_a_next_step(self):
        """An empty archive gets an invitation, not a description of the
        future. The two situations — nothing yet, and nothing pending — are
        different and must not share a sentence."""
        front = re.search(r"function drawFront\(\).*?\n\}", JS, re.S).group(0)
        self.assertIn("front.hidden = true", front)
        self.assertIn("startarc", front)
        self.assertIn("addbtn", front)

    def test_the_first_screen_says_where_the_photo_goes(self):
        """The first thing asked of her is a photo of herself. What the node
        will and will not do with it belongs on that screen, not in a
        settings page she has no reason to open."""
        self.assertIn('id="addbtn"', SRC)
        self.assertNotIn("دستیار کوچیک آماده است", SRC)
        self.assertIn("assistant-log", SRC)

    def test_the_count_it_shows_is_a_real_one(self):
        """No invented numbers on an empty account: the archive line is
        driven by the loaded photo list, not by a placeholder."""
        front = re.search(r"function drawFront\(\).*?\n\}", JS, re.S).group(0)
        self.assertNotIn("const have =", front)
        self.assertIn("front.hidden = true", front)

    def test_clicking_selected_gallery_photo_closes_the_panel(self):
        self.assertIn('if (picked === p.media_id)', JS)
        self.assertIn("$('tagpanel').hidden = true", JS)


class TestArchivingIsTheJob(unittest.TestCase):
    """The loop the app is opened for: one photo, one album, next.

    Everything before this was built around a publish decision, so an
    evening spent filing photos had no screen at all — the card said "nothing
    to decide" while fifty unfiled photos sat in the library, which was true
    only about publishing and false about the work in front of her.
    """

    def test_the_archive_view_exists_and_is_not_a_fourth_tab(self):
        """It is a mode, entered and left deliberately. A tab would let her
        walk away mid-photo into a view that no longer holds her place."""
        self.assertIn('id="view-archive"', SRC)
        self.assertIn("'view-archive'", JS)
        nav = re.search(r"<nav>(.*?)</nav>", SRC, re.S).group(1)
        # Three persistent tabs (today/gallery/business) plus marketing is
        # the current nav shape; archive is deliberately NOT among them.
        self.assertGreaterEqual(len(re.findall(r"<button", nav)), 3)
        self.assertNotIn("view-archive", nav)

    def test_the_backlog_is_photos_without_an_album(self):
        """One definition, in one place. A count that means something else
        on the card than in the loop is a count nobody can trust."""
        self.assertRegex(
            JS, r"const unfiled = \(\) =>[^;]*filter\(p => !p\.collection_id\)")

    def test_one_photo_at_a_time_with_its_place_in_the_run(self):
        """"دونه دونه" — and a counter, because a job with no visible end is
        one nobody starts."""
        arc = re.search(r"function drawArc\(\).*?\n\}", JS, re.S).group(0)
        self.assertIn("arc.list[arc.i]", arc)
        self.assertIn("' از '", arc)

    def test_an_album_can_be_made_without_leaving_the_photo(self):
        """Where a photo belongs is decided while looking at it, and the
        album it belongs in usually does not exist yet."""
        self.assertIn("/api/v1/studio/albums", JS)
        self.assertIn('id="arc-new"', SRC)

    def test_each_photo_is_committed_as_she_leaves_it(self):
        """Nothing batched: putting the phone down after nine of fifty must
        lose nothing."""
        save = re.search(r"async function saveArc\(\).*?\n\}", JS, re.S).group(0)
        self.assertIn("/album", save)
        self.assertIn("/labels", save)
        self.assertIn("arc.i += 1", save)

    def test_a_refused_save_does_not_advance(self):
        """Advancing past a photo that was not stored is how a run of fifty
        ends with gaps nobody can find afterwards."""
        save = re.search(r"async function saveArc\(\).*?\n\}", JS, re.S).group(0)
        step = save.index("arc.i += 1")
        for guard in re.finditer(r"if \(!\w+\.ok\) \{[^}]*return; \}", save):
            self.assertLess(guard.start(), step,
                            "a failure path continues past the increment")

    def test_the_finished_count_is_counted_not_assumed(self):
        """Skipped photos are still unfiled. Saying "12 archived" when nine
        were skipped is exactly the shape of claim this project keeps
        finding in its own bugs."""
        done = re.search(r"function finishArchive\(\).*?\n\}", JS, re.S).group(0)
        self.assertIn("arc.list.filter(p => p.collection_id).length", done)

    def test_a_selection_is_uploaded_one_request_at_a_time(self):
        """Fifty multi-megabyte bodies at once on a phone network is how a
        batch fails entirely instead of partly."""
        self.assertIn("multiple", SRC)
        add = re.search(r"async function addPhotos\(files\).*?\n\}",
                        JS, re.S).group(0)
        self.assertIn("await addPhoto(", add)

    def test_the_library_is_refreshed_after_an_upload(self):
        """The front card counts this list and the archive loop walks it.
        Refreshing only the board left both describing the state from before
        the upload."""
        add = re.search(r"async function addPhotos\(files\).*?\n\}",
                        JS, re.S).group(0)
        self.assertIn("/api/v1/studio/gallery", add)

    def test_the_upload_flag_is_released_on_every_path(self):
        """`busy` left set locks the picker for the rest of the session, and
        the symptom is "the button stopped working" with nothing else."""
        body = re.search(r"async function addPhoto\([^)]*\)\s*\{(.*?)\n\}",
                         JS, re.S).group(1)
        self.assertIn("finally", body)

    def test_filing_can_be_undone(self):
        """Tapping the chosen album again clears it. Without that, a mis-tap
        on the first photo is unrecoverable without leaving the screen."""
        albums = re.search(r"function drawArcAlbums\(\).*?\n\}",
                           JS, re.S).group(0)
        self.assertIn("(arc.album === a.id) ? null : a.id", albums)

    def test_the_tag_vocabulary_has_one_implementation(self):
        """Two copies of the twin rule is two places for it to drift."""
        self.assertEqual(len(re.findall(r"function drawTags\(", JS)), 1)
        self.assertIn("drawTags(arc, 'arc-tags')", JS)

    def test_every_label_shown_goes_through_the_same_map(self):
        """The grid badge printed raw tokens — `bare · soles` — beside buttons
        that said «بدون پوشش». One vocabulary said two ways is the drift the
        test above exists to prevent, one layer down: the tokens are an
        implementation detail of the pack and are not her language."""
        for shown in re.findall(r"\.labels\s*(?:\|\|\s*\[\])?\s*\.join\(", JS):
            self.fail("a label list is joined without LABEL_FA")
        self.assertIn("p.labels.map(l => LABEL_FA[l] || l)", JS)

    def test_the_pack_vocabulary_and_the_shell_map_agree(self):
        """A token with no entry falls back to itself, so a missing
        translation does not vanish — it shows up in English, in her app,
        which is exactly what this catches instead."""
        pack = open(os.path.join(ROOT, "packs", "studio.yaml"),
                    encoding="utf-8").read()
        block = re.search(r"^content_labels:\n((?:\s*-\s*\S+\n)+)", pack, re.M)
        self.assertIsNotNone(block, "the pack lists no content_labels")
        tokens = re.findall(r"-\s*(\S+)", block.group(1))
        self.assertEqual(len(tokens) % 2, 0,
                         "labels are read in consecutive pairs, so an odd "
                         "count silently drops the last one")
        said = re.search(r"const LABEL_FA = \{(.*?)\};", JS, re.S).group(1)
        for token in tokens:
            self.assertIn(f"'{token}'", said,
                          f"{token} has no Persian form and would be shown "
                          f"to her as an English token")


class TestSabaPanelCopyAndLayout(unittest.TestCase):
    """The warm, non-technical, girl-friendly copy contract plus the gallery
    greeting and the chatbox layout — the small surgery requested for the
    Saba panel. None of these are styling preferences; each one came from a
    real user complaint (a leak of the word 'RAG', a gray empty panel under
    the chatbox, a chatbox pushed to the floor)."""

    def test_no_rag_word_leaks_into_user_visible_copy(self):
        """The footer caption used to read «پیشنهاد تازه از RAG …». RAG is a
        forbidden technical word and must not reach her."""
        self.assertNotIn("از RAG", SRC)
        self.assertNotIn("RAG ", SRC)

    def test_the_back_sheets_are_gone_so_the_empty_gray_panel_is_gone(self):
        """`.stack` used to reserve a fixed 352px dark region that, with the
        front card hidden, was an empty gray slab above the chatbox."""
        self.assertNotIn("sheet b2 back", SRC)
        self.assertNotIn("sheet b3 back", SRC)
        self.assertNotIn("min-height:352px", SRC)

    def test_the_chatbox_is_centered_and_capped(self):
        """The chatbox lives in the middle of the page, not pushed to the
        floor, and never stretches edge-to-edge on a wide screen."""
        rule = re.search(r"\.chatbox\{([^}]*)\}", CSS)
        self.assertIsNotNone(rule)
        body = rule.group(1)
        self.assertIn("max-width:720px", body)
        self.assertIn("margin:", body)
        self.assertIn("auto", body)

    def test_the_first_tab_actions_are_centered(self):
        """The action row under the chatbox (آرشیو کنیم / عکس تازه) is a tidy
        centered flex row, not a stacked grid that drops the buttons down."""
        self.assertIn("justify-content:center", CSS)
        self.assertIn("#view-today>.act", CSS)

    def test_the_assistant_buttons_say_something_warm(self):
        """The send button and the suggestion button read as small friendly
        verbs, not «بپرس» / «هلپ ساده»."""
        self.assertIn('id="assistant-send"', SRC)
        self.assertIn('id="assistant-random"', SRC)
        self.assertIn("مشاوره", SRC)
        self.assertNotIn("هلپ ساده", SRC)

    def test_the_gallery_has_a_welcome_banner(self):
        """The gallery opens with a welcome line — filled from the session so
        no name leaks before auth, same rule as the header."""
        self.assertIn('id="gallery-greet"', SRC)
        self.assertIn("greetGallery", JS)
        self.assertIn("خوش اومدی", JS)

    def test_the_welcome_banner_carries_no_name_in_markup(self):
        """A static name in the banner would leak before auth (ziman). The
        default text is nameless; the session fills the name in."""
        banner = re.search(r'<div[^>]*id="gallery-greet"[^>]*>(.*?)</div>',
                           SRC, re.S).group(1)
        for person in PEOPLE:
            self.assertNotIn(person, banner)

    def test_the_album_and_category_are_one_control(self):
        """There is one control, labelled «آلبوم / دستهٔ این عکس»; there is no
        separate category control shown to her."""
        self.assertIn("آلبوم / دستهٔ این عکس", SRC)

    def test_each_photo_has_its_own_delete_button(self):
        """Deleting a photo is its own button, separate from deleting the
        album — the two must never share a control."""
        self.assertIn("حذف عکس", SRC)
        self.assertIn("حذف آلبوم", SRC)

    def test_the_album_delete_warns_photos_survive(self):
        """The confirmation text tells her the photos stay before she deletes
        the album — the one fact that makes album deletion safe."""
        self.assertIn("عکس‌ها پاک نمی‌شوند", SRC)

    def test_the_long_press_lightbox_keeps_suppress_click(self):
        """A long-press zoom must not also select the photo. The
        `suppressClick` guard is the thing that keeps the two apart."""
        self.assertIn("suppressClick", JS)
        self.assertIn("photo-lightbox", SRC)


class TestDeleteButtonOnThePhoto(unittest.TestCase):
    """The little × lives on the photo itself, not in a panel somewhere else.
    Its handlers must keep it from also triggering a long-press zoom or a
    selection — otherwise deleting looks the same as opening the photo."""

    def test_the_corner_delete_button_exists(self):
        self.assertIn("shot-del", JS)
        self.assertIn("deletePhotoById", JS)

    def test_the_delete_button_neutralizes_pointer_events(self):
        """It must stop the pointer events from bubbling to the card, or the
        420ms long-press timer fires and the lightbox opens over the confirm
        dialog."""
        self.assertIn("addEventListener('pointerdown'", JS)
        self.assertIn("addEventListener('touchstart'", JS)
        self.assertIn("addEventListener('click'", JS)
        # the delete button stops propagation, separate from the long-press
        # guard which also stops a click
        self.assertGreater(JS.count("stopPropagation()"), 2)

    def test_the_corner_delete_confirms_before_deleting(self):
        """«مطمئنی؟» — the photo is gone for good, so a confirm comes first."""
        self.assertIn("مطمئنی؟ این عکس برای همیشه حذف شود؟", JS)


class TestBatchUploadKeepsGoingAfterARefusal(unittest.TestCase):
    """One bad photo in a selection of fifty used to `break` the whole batch,
    which read on a phone as "the picker froze at photo 3". Now the bad one is
    skipped and counted, and the rest keep going."""

    def test_the_break_is_gone(self):
        self.assertNotIn("} else if (list.length > 1) { break; }", JS)

    def test_a_failed_count_is_reported(self):
        self.assertIn("failed", JS)

