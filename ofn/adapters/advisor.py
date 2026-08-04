"""The tier-0 advisor: numbers and labels out, a sentence back.

Sits between the stores and the model, and its whole job is that nothing but
`Evidence` can cross. It never reads an image, never opens the media root,
and does not know where the media root is — the import list is the first
place to check that, and it is short on purpose.

Two rules from the brief, both enforced here rather than intended:

    every suggestion carries its provenance
    nothing escalates to the expensive rung on its own

The second is worth stating plainly: silence means do not spend. A rung that
can be reached because a cheaper one was merely brief is a rung that gets
reached constantly, and the bill arrives monthly.

Tier 1 — sending one chosen image — is deliberately absent rather than
present and disabled. Saba has not been asked, the answer is hers, and code
that exists gets run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel.advisor import (
    Disposition, Evidence, Finding, Memory, Provenance, extract,
)
from ..kernel.advisor_gate import assert_no_pixels
from ..kernel.errors import FailClosedError
from ..kernel.routing import Rung

# What the pack is allowed to measure and hand over. Whitelisted by name:
# anything not here is not evidence, however harmless it looks.
DEFAULT_MEASURES: tuple[str, ...] = (
    "posts_counted", "window_days", "median_caption_chars",
    "media_per_post", "hour_of_day", "retention_pct",
    "single_subject_share", "soft_light_share",
)

# Below this there is nothing to say, and saying it anyway is how a tool
# teaches somebody that its advice is noise. Chosen to be visibly arbitrary
# rather than tuned: it is a floor on honesty, not a statistical threshold.
MIN_SAMPLE = 12


@dataclass(frozen=True)
class AdvisorRequest:
    """Exactly what leaves. There is no field here that could hold a photo."""

    evidence: Sequence[Evidence]
    provenance: Provenance
    rung: Rung = Rung.REMOTE

    def render(self) -> str:
        """The prompt, built from evidence rather than from free text.

        A caller cannot append a sentence: the prompt has no slot for one.
        That is the same reason `Evidence` has no free-text field — a slot
        for prose is a slot for a caption, and a caption is content.
        """
        lines = [f"{e.name}={e.value:g}" + (f" {e.unit}" if e.unit else "")
                 for e in self.evidence]
        return (
            "این اعداد از کار یک تولیدکنندهٔ محتوا آمده‌اند. هیچ تصویری، نامی "
            "یا شناسه‌ای همراهشان نیست.\n"
            + "\n".join(sorted(lines)) + "\n\n"
            "یک جملهٔ کوتاه بنویس که فقط از همین اعداد نتیجه گرفته شود. "
            "اگر این اعداد برای نتیجه‌گیری کافی نیستند، بنویس «کافی نیست» "
            "و چیز دیگری ننویس."
        )


class Advisor:
    """Builds the request, refuses anything that is not evidence, and turns a
    reply into findings that carry their source."""

    def __init__(self, *, measures: Sequence[str] = DEFAULT_MEASURES,
                 memory: Memory | None = None) -> None:
        self._measures = tuple(measures)
        self.memory = memory or Memory()

    def prepare(self, raw: Mapping[str, object], *, sample: int,
                window_days: int) -> AdvisorRequest:
        """Measurements in, a request out — or an exception.

        `assert_no_pixels` runs on the raw input as well as on the built
        request. Once is the type system; twice is because this is the one
        boundary where being wrong cannot be undone by a later fix.
        """
        assert_no_pixels(raw)
        if sample < MIN_SAMPLE:
            raise FailClosedError(
                f"نمونه کم است ({sample} < {MIN_SAMPLE}) — چیزی برای گفتن نیست")
        evidence = extract(raw, allowed=self._measures)
        if not evidence:
            raise FailClosedError("هیچ سنجش قابل استفاده‌ای نبود")
        request = AdvisorRequest(
            evidence=evidence,
            provenance=Provenance(sample=sample, window_days=window_days))
        assert_no_pixels(request.render())
        return request

    def interpret(self, request: AdvisorRequest, reply: str, *,
                  key: str) -> Finding | None:
        """A reply becomes a finding, or nothing.

        "Not enough" is a real answer and returns None rather than an empty
        finding — a model that declines has done the right thing, and
        recording it as a suggestion with no content would make declining
        look like failing.
        """
        text = (reply or "").strip()
        if not text or "کافی نیست" in text:
            return None
        # One sentence. A model that writes three paragraphs has stopped
        # answering the question that was asked.
        claim = text.split("\n")[0].strip()[:280]
        if not claim:
            return None
        return Finding(key=key, claim=claim, evidence=request.evidence,
                       provenance=request.provenance)

    def offer(self, findings: Sequence[Finding]) -> tuple[Finding, ...]:
        """What may be shown, after the ratchet."""
        keep = self.memory.filter(findings)
        for finding in keep:
            self.memory.remember(finding.key, Disposition.OFFERED)
        return keep

    def record(self, key: str, disposition: Disposition) -> None:
        self.memory.remember(key, disposition)

    @staticmethod
    def rung_for(_request: AdvisorRequest) -> Rung:
        """Always the standard rung.

        A method rather than a constant so the intent is visible: there is no
        condition under which this returns the expensive one. Escalation
        needs a human saying so, and silence means do not spend.
        """
        return Rung.REMOTE


def render_for_screen(finding: Finding) -> dict:
    """A finding as a screen shows it — claim and source, never separable.

    Returned together in one object because a template that can print the
    claim without the source will eventually be written, and then the advice
    is back to being unarguable.
    """
    return {
        "key": finding.key,
        "claim": finding.claim,
        "source": finding.provenance.render(),
        "sample": finding.provenance.sample,
        "window_days": finding.provenance.window_days,
    }
