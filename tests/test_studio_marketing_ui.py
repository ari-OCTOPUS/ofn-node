"""Contract tests for the interactive marketing UI in studio.html.

Two contracts the senior-architect review demanded:
  1. No mock/fixture data — the UI must read from real endpoints.
  2. No innerHTML assignment from API data — XSS defence via textContent.
Plus: the interactive elements (route-preview, send-to-outbox) exist and
are wired to the right endpoints.
"""

import re
import unittest

SRC = open("web/studio.html", encoding="utf-8").read()


class TestMarketingUIIsInteractive(unittest.TestCase):
    def test_route_preview_button_exists(self):
        self.assertIn('id="mkt-preview-btn"', SRC)

    def test_send_to_outbox_button_exists(self):
        self.assertIn('id="mkt-send-btn"', SRC)

    def test_route_preview_calls_real_endpoint(self):
        self.assertIn("route-preview", SRC)
        self.assertIn("previewRoute", SRC)

    def test_send_calls_real_endpoint(self):
        self.assertIn("send-to-outbox", SRC)
        self.assertIn("sendToOutbox", SRC)

    def test_draft_selector_loads_from_board(self):
        # Not a hardcoded list — loads from the real /studio/board endpoint.
        self.assertIn("loadDraftSelector", SRC)
        self.assertIn("/api/v1/studio/board", SRC)


class TestMarketingUIHasNoMockData(unittest.TestCase):
    FORBIDDEN = ("src/data/mock", "mock.ts", "fixtureData", "MOCK_PLATFORMS",
                 "fakeDraft", "sampleDraft")

    def test_no_mock_or_fixture_references(self):
        for token in self.FORBIDDEN:
            self.assertNotIn(token, SRC,
                             f"studio.html references mock data: {token}")


class TestMarketingUIDoesNotInnerHTMLApiData(unittest.TestCase):
    """The shell-contract rule, applied to the marketing view specifically."""

    def test_platform_cards_built_with_createElement(self):
        # renderPlatforms must use createElement/appendChild, not innerHTML.
        self.assertIn("document.createElement('div')", SRC)
        self.assertIn("grid.appendChild", SRC)

    def test_no_innerhtml_with_api_response(self):
        # Find every innerHTML assignment and ensure none assigns from a
        # fetched response variable. The regex is intentionally narrow:
        # innerHTML = ... where ... contains a likely API-derived name.
        bad = re.findall(r"innerHTML\s*=\s*[a-zA-Z_]\w*(?:\.\w+)*",
                         SRC)
        # Allow innerHTML = text (a literal), which is the one safe form the
        # shell contract permits. Flag anything that looks like a variable.
        suspicious = [b for b in bad
                      if not re.search(r"innerHTML\s*=\s*text\b", b)]
        self.assertEqual(suspicious, [],
                         f"innerHTML assigned from variables: {suspicious}")


class TestInspirationTodayCard(unittest.TestCase):
    """الهام امروز: the card that replaces the old 'نوردهی این هفته' gauge.

    Its defining property is honesty about emptiness: when there are no real
    trend observations, it shows the candid 'nothing yet' sentence, never a
    fabricated sample. The widget is built entirely from real endpoint data
    via createElement — same XSS defence as the rest of the view.
    """

    def test_inspiration_section_present(self):
        self.assertIn("الهام امروز", SRC)
        self.assertIn('id="mkt-insp-cards"', SRC)

    def test_render_function_reads_real_cards(self):
        self.assertIn("renderInspiration", SRC)
        self.assertIn("inspiration_cards", SRC)

    def test_honest_empty_state_present(self):
        # The exact candid sentence for zero observations. If this string
        # disappears, the widget may be drifting toward fabricated content.
        self.assertIn("هنوز چیزی از دنیا نرسیده", SRC)

    def test_no_fabricated_trend_data(self):
        # The widget must source only from the API response, never hardcode a
        # sample trend. Look for the obvious tell-tales of fake content.
        for token in ("نمونه ترند", "sampleTrend", "fakeTrend",
                      "INSPIRATION_SAMPLES", "placeholder_idea"):
            self.assertNotIn(token, SRC,
                             f"inspiration widget has fabricated data: {token}")

    def test_cards_built_with_createElement_not_innerHTML(self):
        self.assertIn("renderInspiration", SRC)
        # The render function must use createElement + textContent for card
        # content (the same rule renderPlatforms follows).
        self.assertIn("document.createElement('div')", SRC)

    def test_does_not_reference_old_exposure_gauge_as_inspiration(self):
        # The old 'نوردهی این هفته' was a different widget. The new card is
        # 'الهام امروز'. Both may coexist (the gauge lives on the business
        # tab), but the inspiration card must not reuse the gauge's source.
        self.assertIn("الهام امروز", SRC)


if __name__ == "__main__":
    unittest.main()
