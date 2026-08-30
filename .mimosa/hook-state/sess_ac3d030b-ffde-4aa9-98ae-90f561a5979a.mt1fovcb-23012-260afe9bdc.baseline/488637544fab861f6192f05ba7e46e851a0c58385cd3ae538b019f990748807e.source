"""The SDK must have run before a shell asks whether it is inside Telegram.

This is the test that was missing when the studio shell showed nothing to
anybody for a day. The connector held

    const tg = window.Telegram && window.Telegram.WebApp;

in an inline script, and the SDK tag carried `defer`. Inline scripts run while
the document is parsing; deferred ones run after. So `tg` bound `undefined`
once and stayed that way on every platform, phone included, and every launch
reported `no-shell` — "you did not open this from Telegram" — to people who
had opened it from Telegram.

Two things made it survive review. The call site of `boot()` had already been
deferred to DOMContentLoaded *for this exact reason*, with a comment
explaining the hazard — so the file read as though the ordering had been
handled, when what had been handled was the caller and not the read. And the
symptom, a page that comes up blank, looks like an empty account.

Note what is asserted and what is not. Nesting proves nothing here: the old
capture sat inside an IIFE, one brace deep, and an IIFE is invoked
immediately, so "inside a function" and "evaluated later" are different
claims and only the second one matters. Deciding which reads are deferred
needs a JS engine, and there is none on this board. So this pins the property
that is checkable from the text and is sufficient on its own — the SDK
finishes before any script that mentions it starts — and the shells keep the
lazy read as a second layer that no test here can see.
"""

import re
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

SDK = "telegram-web-app.js"
SHELLS = ("studio.html", "panel.html", "ziman.html", "lead.html")

# <script ...> with its attributes, and inline blocks with their bodies.
_SCRIPT_TAG = re.compile(r"<script\b([^>]*)>", re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_JS_BLOCK = re.compile(r"/\*.*?\*/", re.S)


def _blank(pattern, text):
    """Replace matches with spaces, keeping length and line breaks so every
    offset still refers to the same place in the original file."""
    return pattern.sub(
        lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def _code_only(raw):
    """The file with its prose removed.

    Both comment syntaxes, and for the same reason twice: a rule about
    `window.Telegram` cannot be written down next to the code it governs if
    writing it down is what trips it. This test failed on its own explanation
    before it blanked JS block comments — which is the rule working, one level
    up from where it was aimed.
    """
    return _JS_BLOCK.sub(
        lambda m: re.sub(r"[^\n]", " ", m.group()),
        _blank(_COMMENT, raw))


def _sdk_tag(html):
    """Position and attributes of the SDK script tag, ignoring HTML comments."""
    blanked = _blank(_COMMENT, html)
    for m in _SCRIPT_TAG.finditer(blanked):
        if SDK in m.group(1):
            return m.start(), m.group(1)
    return None, None


class ShellBootOrder(unittest.TestCase):
    def test_every_shell_loads_the_sdk(self):
        for name in SHELLS:
            with self.subTest(shell=name):
                at, _ = _sdk_tag((WEB / name).read_text(encoding="utf-8"))
                self.assertIsNotNone(at, f"{name} never loads {SDK}")

    def test_the_sdk_has_run_before_any_shell_reads_it(self):
        """Stated as a property, which is the whole point of the test.

        There are two honest ways to satisfy it and a shell may pick either:

          blocking   the tag has no defer/async and sits before every read, so
                     parsing stops until the SDK exists. What panel, ziman and
                     lead do.
          late read  window.Telegram is never bound to a name, only reached
                     through a function, so the read happens whenever it is
                     called rather than when the file is parsed. Correct under
                     any tag. What studio does.

        Asserting the *mechanism* — "the tag must not say defer" — was tried
        first and was wrong: it collided with the equally real rule that a
        third-party script must not block first paint, a white screen this
        shell had already fixed once. Two true requirements, and a test that
        pinned the wrong one would have forced a regression to satisfy it.

        Binding is what actually breaks. `const tg = window.Telegram && ...`
        freezes whatever existed when that line ran, and no amount of care at
        the call site undoes it — the studio shell already deferred boot() to
        DOMContentLoaded for exactly this reason, and stayed broken, because
        what was deferred was the caller and not the read.
        """
        capture = re.compile(
            r"\b(?:const|let|var)\s+\w+\s*=\s*(?![^;\n]*=>)"
            r"[^;\n]*window\.Telegram")
        for name in SHELLS:
            with self.subTest(shell=name):
                raw = (WEB / name).read_text(encoding="utf-8")
                at, attrs = _sdk_tag(raw)
                self.assertIsNotNone(at, f"{name} never loads {SDK}")
                # Prose is not a read. A comment above the tag that explains
                # this very rule is not the shell touching the SDK, and
                # counting it would make the rule unstatable in place.
                html = _code_only(raw)

                deferred = re.search(r"\b(defer|async)\b", attrs or "")
                reads = [m.start() for m in
                         re.finditer(r"window\.Telegram", html)]
                blocking_first = not deferred and all(p > at for p in reads)
                grabbed = capture.search(html)

                self.assertTrue(
                    blocking_first or not grabbed,
                    f"{name} loads the Telegram SDK with "
                    f"{deferred.group() if deferred else 'no defer'} and "
                    f"captures it at parse time "
                    f"({grabbed.group().strip() if grabbed else ''!r}). "
                    f"That binding is undefined forever, so every launch "
                    f"reports 'not opened from Telegram' — to people who did.")

    def test_boot_waits_for_the_document(self):
        """The other half of the late-read arrangement: deferred scripts have
        run by DOMContentLoaded and not before, so a shell that starts work at
        parse time could still never see the SDK, lazy reads or not."""
        html = (WEB / "studio.html").read_text(encoding="utf-8")
        self.assertIn("DOMContentLoaded", html)


class BootStagesAreDistinct(unittest.TestCase):
    """`no-shell` named two failures with opposite fixes.

    The SDK being absent is a loading failure — the page did not finish
    arriving, and reloading may well fix it. `initData` being empty with the
    SDK present is a routing failure — a real client opened by a path that
    signs nothing, where reloading changes nothing at all. Telling somebody to
    "open it from inside Telegram" when they already did sends them looking in
    the wrong place, so the shell must not be able to say it by accident.
    """

    def setUp(self):
        self.html = (WEB / "studio.html").read_text(encoding="utf-8")

    def test_studio_reports_the_split_stages(self):
        for stage in ("no-sdk", "no-initdata"):
            self.assertIn(f"'{stage}'", self.html,
                          f"studio shell never produces {stage}")

    def test_studio_no_longer_reports_the_merged_stage(self):
        self.assertNotIn("no-shell", self.html,
                         "studio shell still uses the merged label")

    def test_both_stages_have_their_own_sentence(self):
        """Two labels sharing one message is the same bug one layer up."""
        said = {}
        for stage in ("no-sdk", "no-initdata"):
            # From the key to the start of the next REASONS key, then keep
            # only the quoted Persian fragments the partner actually reads.
            m = re.search(rf"^\s*'{stage}':(.*?)^\s*'", self.html,
                          re.S | re.M)
            self.assertIsNotNone(m, f"{stage} has no sentence in REASONS")
            said[stage] = "".join(re.findall(r"'([^']*)'", m.group(1)))
            self.assertTrue(said[stage].strip(),
                            f"{stage} has an empty sentence")
        self.assertNotEqual(said["no-sdk"], said["no-initdata"])

    def test_retry_is_offered_only_where_it_could_work(self):
        """Reload cannot produce a launch blob that the route never had."""
        self.assertIn("kind !== 'no-initdata'", self.html)

    def test_the_platform_rides_along_with_the_failure(self):
        """A bare label still leaves browser-vs-client open; platform closes
        it. Both fields are client properties, so no PII goes to the journal."""
        self.assertRegex(self.html, r"tell\(OFN\.why,\s*OFN\.where\(\)\)")
        self.assertRegex(self.html, r"t\.platform")
        self.assertRegex(self.html, r"t\.version")


class KernelAcceptsTheStages(unittest.TestCase):
    """The stage set is closed on purpose — the route is unauthenticated, so
    nothing the page sends may reach the journal as free text. A shell that
    reports a stage the kernel rejects is silent in exactly the situation the
    report exists for."""

    def test_kernel_accepts_every_stage_the_studio_shell_can_send(self):
        from ofn.adapters.http_api import ApiApp

        html = (WEB / "studio.html").read_text(encoding="utf-8")
        sent = set(re.findall(r"tell\(\s*'([a-z-]+)'", html))
        sent |= set(re.findall(r"why = '([a-z-]+)'", html))
        self.assertIn("no-sdk", sent)      # the scrape found something
        self.assertIn("no-initdata", sent)
        self.assertLessEqual(sent, set(ApiApp._BOOT_STAGES),
                             "studio shell sends a stage the kernel drops")


if __name__ == "__main__":
    unittest.main()
