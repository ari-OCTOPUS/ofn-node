"""
Worker B -- Audience / Sentiment (KB-01, Phase 1)
Haiku-powered review sentiment classification + static seasonal demand index.

Model: claude-haiku-4-5 (cheap-first -- KB-02 s2.1)
Haiku pricing (Jun 2026): input $0.80/Mtok, output $4.00/Mtok

Governance:
  - read-only: never modifies external state.
  - Output used by Worker C to personalise content tone.
  - PII: review text processed in-memory only, not stored (KB-04).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:  # SDK absent -> sentiment falls back to neutral stub
    Anthropic = None

from ..config import config
from ..governance import check_and_enforce, log_cost
from ..resilience import call_with_retry, new_idempotency_key

logger = logging.getLogger(__name__)

_HAIKU_INPUT_USD_PER_TOK  = 0.80 / 1_000_000
_HAIKU_OUTPUT_USD_PER_TOK = 4.00 / 1_000_000
_EST_SENTIMENT_AUD = 0.002  # ~per review classification (KB-02 s3.1)

_SENTIMENT_PROMPT = (
    "You are a sentiment analyser for a painting business.\n"
    "Classify the review and return ONLY valid JSON (no markdown):\n"
    '{{"sentiment": "positive|negative|neutral", "score": 0.0_to_1.0, "key_themes": []}}\n\n'
    "Themes (use exact strings): price_concern, quality_praise, quality_complaint,\n"
    "timeliness, communication, cleanliness, value_for_money, professionalism,\n"
    "repeat_customer, referral_intent\n\n"
    "Review (platform: {platform}):\n<review>\n{review_text}\n</review>"
)

# Sydney seasonal demand index (KB-12)
# Autumn (Mar-May) = peak: ideal temp/humidity, high homeowner intent.
# Winter (Jun-Aug) = slowest: damp, short days, fewer exterior jobs.
_SEASONAL_INDEX: dict[int, float] = {
    1: 0.70,   # January   -- summer heat limits exterior
    2: 0.70,   # February  -- humid, some rain
    3: 1.00,   # March     -- autumn peak
    4: 1.00,   # April     -- autumn peak
    5: 0.90,   # May       -- late autumn, still good
    6: 0.50,   # June      -- winter slow
    7: 0.50,   # July      -- winter slow
    8: 0.55,   # August    -- winter tail
    9: 0.85,   # September -- spring ramp-up
   10: 0.90,   # October   -- spring strong
   11: 0.90,   # November  -- spring strong
   12: 0.70,   # December  -- holiday slowdown
}


def _season_label(month: int) -> str:
    if month in (12, 1, 2):
        return "summer"
    if month in (3, 4, 5):
        return "autumn_peak"
    if month in (6, 7, 8):
        return "winter"
    return "spring"


@dataclass
class SentimentResult:
    source: str          # platform (google, facebook, hipages, etc.)
    sentiment: str       # "positive" | "negative" | "neutral"
    score: float         # 0.0-1.0
    key_themes: list[str]
    agent_id: str = "B_audience"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


class AudienceAgent:
    """
    Worker B: read-only sentiment and audience analysis.
    Output used by Worker C to personalise content tone.
    """
    AGENT_ID = "B_audience"

    def __init__(self) -> None:
        if config.ANTHROPIC_API_KEY and Anthropic is not None:
            self._llm: Optional[Anthropic] = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        else:
            self._llm = None
            logger.warning(
                "ANTHROPIC_API_KEY not set -- Worker B sentiment returns neutral stub."
            )

    def analyse_review(self, review_text: str, platform: str) -> SentimentResult:
        """
        Classify sentiment of an inbound review via Haiku.
        Truncates review to 2000 chars to cap token cost.
        Falls back to neutral stub if LLM unavailable or JSON parse fails.
        """
        if not self._llm:
            return SentimentResult(
                source=platform, sentiment="neutral", score=0.5,
                key_themes=[], agent_id=self.AGENT_ID,
            )

        # INV-3: governance gate BEFORE the paid call (was missing -- fixed
        # 2026-07-02: this call previously bypassed kill switch + spend cap
        # and never logged its cost to cost_events).
        check_and_enforce(_EST_SENTIMENT_AUD, self.AGENT_ID)

        prompt = _SENTIMENT_PROMPT.format(
            platform=platform,
            review_text=review_text[:2000],
        )
        idem = new_idempotency_key()
        try:
            msg = call_with_retry(
                lambda: self._llm.messages.create(
                    model=config.MODEL_CHEAP,  # Haiku
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                    extra_headers={"Idempotency-Key": idem},
                ),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(
                    _EST_SENTIMENT_AUD, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
            parsed = json.loads(msg.content[0].text.strip())
            tok_in  = msg.usage.input_tokens
            tok_out = msg.usage.output_tokens
            cost    = tok_in * _HAIKU_INPUT_USD_PER_TOK + tok_out * _HAIKU_OUTPUT_USD_PER_TOK
            log_cost("llm_call", self.AGENT_ID, config.MODEL_CHEAP,
                     round(cost, 8), tok_in, tok_out)
            return SentimentResult(
                source=platform,
                sentiment=str(parsed.get("sentiment", "neutral")),
                score=float(parsed.get("score", 0.5)),
                key_themes=list(parsed.get("key_themes", [])),
                agent_id=self.AGENT_ID,
                tokens_in=tok_in,
                tokens_out=tok_out,
                cost_usd=round(cost, 8),
            )
        except json.JSONDecodeError:
            logger.error("Haiku returned invalid JSON for sentiment on platform=%r", platform)
        except Exception as exc:
            logger.error("Sentiment analysis failed (platform=%r): %s", platform, exc)

        return SentimentResult(
            source=platform, sentiment="neutral", score=0.5,
            key_themes=["parse_error"], agent_id=self.AGENT_ID,
        )

    def get_seasonal_demand(self, suburb: str, month: int) -> dict:
        """
        Seasonal painting demand signal for a suburb (KB-12).
        Returns demand_index 0.0-1.0 (1.0 = peak).
        No external API call -- static index based on Sydney climate data.
        For suburb-level nuance, pair with Worker A.search_suburb().
        """
        if not (1 <= month <= 12):
            logger.warning("Invalid month=%d; clamping.", month)
            month = max(1, min(12, month))
        return {
            "suburb": suburb,
            "month": month,
            "season": _season_label(month),
            "demand_index": _SEASONAL_INDEX[month],
            "note": "Static Sydney seasonal index (KB-12). Autumn peak, winter slow.",
            "agent_id": self.AGENT_ID,
        }
