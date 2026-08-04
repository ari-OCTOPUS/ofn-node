"""Questions this node already knows the answer to.

The first thing put in front of a model must not be something with no way of
checking it. That is how a pipeline gets declared working on the strength of
an answer nobody could grade.

    ask something the kernel has already computed,
    then put the two answers side by side

If they agree, both the wiring and the model are worth something. If they
disagree, that is a finding either way — a broken pipe, a substituted model,
or a model that cannot do arithmetic it claimed to. Every outcome teaches.

This is what cryptography does with published test vectors: an implementation
is not believed because it looks right, it is believed because it reproduces
answers computed elsewhere. Here "elsewhere" is the kernel, whose answers are
deterministic and already under test.

Kernel purity: no clock, no I/O. The questions are data and the comparison is
arithmetic.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Callable, Sequence


class Grade(enum.Enum):
    AGREED = "agreed"
    DISAGREED = "disagreed"
    UNREADABLE = "unreadable"   # answered, but not in a form that can be graded
    REFUSED = "refused"         # the rung declined or the call failed


@dataclass(frozen=True)
class KnownAnswer:
    """One question with an answer that was computed, not looked up."""

    key: str
    prompt: str
    expected: str
    # How to pull the answer out of prose. A model asked for a number will
    # often wrap it in a sentence, and failing that as "disagreed" would
    # blame the model for the grader's rigidity.
    extract: Callable[[str], str | None]

    def grade(self, reply: str) -> Grade:
        if not reply or not reply.strip():
            return Grade.REFUSED
        got = self.extract(reply)
        if got is None:
            return Grade.UNREADABLE
        return Grade.AGREED if got == self.expected else Grade.DISAGREED


def _first_number(text: str) -> str | None:
    """The first integer in the reply, ASCII or Persian digits.

    `[0-9۰-۹]`, because a model answering a Persian prompt may answer in
    Persian digits — and reading that as "no number found" would grade a
    correct answer as unreadable.
    """
    m = re.search(r"[-+]?[0-9۰-۹]+", text)
    if m is None:
        return None
    digits = m.group(0).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    try:
        return str(int(digits))
    except ValueError:
        return None


def _yes_no(text: str) -> str | None:
    lowered = text.strip().lower()
    if re.search(r"\b(yes|true)\b", lowered) or "بله" in lowered:
        return "yes"
    if re.search(r"\b(no|false)\b", lowered) or "خیر" in lowered or "نه" in lowered:
        return "no"
    return None


# Deliberately trivial. The point is not to test the model's intelligence —
# it is to test that the question reached something and the answer came back
# through the same pipe, and that the pipe did not quietly substitute
# anything. A hard question would confound "the wiring is broken" with "the
# model is not good enough", and those need different fixes.
QUESTIONS: Sequence[KnownAnswer] = (
    KnownAnswer(
        key="arithmetic",
        prompt="فقط یک عدد بنویس و هیچ توضیحی نده: ۱۲۷ + ۲۹۸ چند می‌شود؟",
        expected="425",
        extract=_first_number,
    ),
    KnownAnswer(
        key="echo",
        prompt="فقط این عدد را عیناً تکرار کن و چیز دیگری ننویس: 60724",
        expected="60724",
        extract=_first_number,
    ),
    KnownAnswer(
        key="refusal",
        prompt=("فقط «بله» یا «خیر» بنویس. آیا این جمله درست است: "
                "«۱۰ بزرگ‌تر از ۲۰ است»؟"),
        expected="no",
        extract=_yes_no,
    ),
)


@dataclass(frozen=True)
class ProbeResult:
    key: str
    grade: Grade
    model: str          # what answered, per the provider
    requested: str      # what we asked for
    reply_head: str     # first characters only — never a whole model output

    @property
    def model_substituted(self) -> bool | None:
        """None when the provider did not name a model. Unknown is not
        agreement — see D-16."""
        if not self.model or not self.requested:
            return None
        return self.model.split(":")[0] != self.requested


def summarise(results: Sequence[ProbeResult]) -> dict:
    """What the probe run says, in a shape a screen can print.

    `usable` is deliberately strict: anything other than full agreement means
    the pipe has not been shown to work, and a partial pass reported as a
    pass is exactly the self-confirming claim this whole file exists to
    avoid.
    """
    grades = [r.grade for r in results]
    return {
        "asked": len(results),
        "agreed": sum(1 for g in grades if g is Grade.AGREED),
        "disagreed": sum(1 for g in grades if g is Grade.DISAGREED),
        "unreadable": sum(1 for g in grades if g is Grade.UNREADABLE),
        "refused": sum(1 for g in grades if g is Grade.REFUSED),
        "usable": bool(results) and all(g is Grade.AGREED for g in grades),
        "substituted": [r.key for r in results if r.model_substituted],
        "models": sorted({r.model for r in results if r.model}),
    }
