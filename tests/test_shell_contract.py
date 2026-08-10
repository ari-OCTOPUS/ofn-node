"""The contract between the four shells and the node they draw.

This file exists because of a specific failure that survived a whole phase:
every shell rendered, every test passed, and none of the four was connected to
anything. The owner's panel had an approve button that reported "ثبت در لجر"
without a request ever leaving the page, and the partner shells asked
hard-coded questions that the kernel had never derived.

There is no JavaScript engine on this board, so these tests cannot execute a
shell. What they can do is pin the two things that were actually wrong:

  * the shells read fields the node does not send, or
  * the shells claim an effect they never asked for.

Both are checked against the real HTML and the real handlers.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_dir
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import Action, Confidence, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
PACKS = os.path.join(ROOT, "packs")

PARTNER_SHELLS = ("ziman.html", "lead.html", "studio.html")
ALL_SHELLS = PARTNER_SHELLS + ("panel.html",)

NOW_S = 1_785_000_000
# Every partner shell now has a door list. These are the accounts the
# tests speak as; anybody else is a stranger, which is the point.
PARTNERS = {"ziman": ["1"], "lead": ["1"], "studio": ["1"]}
NOW_ISO = "2026-08-03T10:00:00Z"


def read(name: str) -> str:
    with open(os.path.join(WEB, name), encoding="utf-8") as fh:
        return fh.read()


def static_markup(html: str) -> str:
    """The markup a browser paints before any script runs.

    `html.split("<script")[0]` was the idiom here, and it stops at the SDK tag
    in `<head>` — so every assertion built on it was inspecting nine lines of
    head and reporting success about a body it never read. Removing the script
    blocks and keeping the rest is what was meant.
    """
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)


def inline_scripts(html: str) -> list[str]:
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)


# ══ what the shells say about themselves ════════════════════════════════
class TestShellsDoNotLie(unittest.TestCase):
    def test_panel_talks_to_the_node(self):
        """The owner's panel shipped with zero API calls in it."""
        src = read("panel.html")
        for endpoint in ("/api/v1/auth/session", "/api/v1/queue",
                         "/api/v1/decide", "/api/v1/owner/status"):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, src)

    def test_panel_has_no_hard_coded_decisions(self):
        """Five fabricated decision cards used to sit in the markup, above a
        button that claimed to write to the ledger."""
        src = read("panel.html")
        body = static_markup(src)
        self.assertNotIn('class="dec r"', body)
        self.assertNotIn('class="dec y"', body)
        self.assertNotIn('class="dec g"', body)

    def test_no_shell_ships_a_reading(self):
        """A figure in the markup is a figure the node never sent.

        `lead.html` shipped ۱۲ / ۵ / ۳ in its KPI strip under the labels
        "لید امروز", "منتظر تو", "کار این هفته". `refreshKpis()` overwrote them,
        but only when its read succeeded — so a partner on a bad connection saw
        three invented numbers wearing today's labels, and nothing on screen
        said otherwise. The panel had the same class of bug and was cleared of
        it; this pins all four.

        The unit under test is the markup before the first `<script>`: whatever
        the browser paints before any fetch resolves. A dash or an ellipsis is
        fine — those read as "not yet". A numeral does not.
        """
        for shell in ALL_SHELLS:
            body = static_markup(read(shell))
            # Value nodes: the classes each shell uses for a rendered figure.
            for cls in ("kv", "pnum", "hnum", "mval", "vv", "num"):
                for m in re.finditer(
                        rf'class="[^"]*\b{cls}\b[^"]*"[^>]*>([^<]+)<', body):
                    text = m.group(1).strip()
                    self.assertFalse(
                        re.search(r"[۰-۹0-9]", text),
                        f"{shell}: a `{cls}` node ships the figure {text!r}; "
                        f"it must start empty or as a placeholder")

    def test_a_ledger_claim_only_follows_a_real_request(self):
        """Any shell that tells a human something was recorded must have
        posted it. Checked by requiring the claim to appear after an await on
        the decide/answers call in the same script."""
        src = read("panel.html")
        script = "\n".join(inline_scripts(src))
        claim = script.index("در لجر ثبت شد")
        posted = script.index("/api/v1/decide")
        self.assertLess(posted, claim,
                        "the panel claims a ledger write before it makes one")

    def test_partner_shells_render_every_question_kind(self):
        """The kernel emits four kinds. A shell that handles three shows a
        blank card for the fourth."""
        for name in PARTNER_SHELLS:
            src = read(name)
            with self.subTest(shell=name):
                for kind in ("number", "choice", "confirm"):
                    self.assertIn(f"'{kind}'", src,
                                  f"{name} does not render {kind} questions")
                self.assertIn("textarea", src, f"{name} has no free-text input")

    def test_partner_shells_post_answers(self):
        for name in PARTNER_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("/api/v1/answers", read(name))

    def test_no_shell_recurses_in_its_haptic_helper(self):
        """`tap()` calling `OFN.tap()` is unbounded recursion — it threw
        RangeError on every Android tap in two of the shells."""
        for name in ALL_SHELLS:
            src = read(name)
            with self.subTest(shell=name):
                for body in re.findall(r"tap\s*\([^)]*\)\s*\{(.*?)\n    \}",
                                       src, re.S):
                    self.assertNotIn("OFN.tap()", body,
                                     f"{name}: tap() calls itself")

    def test_node_data_never_reaches_innerhtml(self):
        """Payloads in the queue originate in customer messages. Every one of
        them is rendered with textContent; the only innerHTML left takes a
        fixed string defined in the file itself."""
        for name in ALL_SHELLS:
            src = read(name)
            with self.subTest(shell=name):
                for raw in src.splitlines():
                    # Comments legitimately name the thing they warn against.
                    line = raw.split("//")[0].split("/*")[0]
                    if "innerHTML" not in line:
                        continue
                    self.assertRegex(
                        line, r"innerHTML\s*=\s*text\b",
                        f"{name}: innerHTML assigned something other than a "
                        f"fixed local string: {raw.strip()}")


class TestNoFakeButtonsInStudio(unittest.TestCase):
    """A real phone touch test surfaced three "buttons that do nothing":

      1. the front sheet had `:active` press feedback but no click handler, so
         a thumb pressing empty space saw it depress and release to nothing;
      2. the marketing draft selector changed its value with no feedback, so
         old platform-preview cards lingered and read as the new draft's verdict;
      3. the archive start button could be tapped with an empty backlog and
         did nothing silently.

    None of these is executable here (no JS engine), but each leaves a mark in
    the source, so these tests pin the fixes against regression.
    """

    def test_front_sheet_has_no_press_animation_without_a_handler(self):
        src = read("studio.html")
        # The `.sheet.front:active` rule was the press feedback on a container
        # that has no click handler. Its absence is the contract: a tap on the
        # sheet's empty space must not pretend to register.
        self.assertNotRegex(
            src, r"\.sheet\.front:active",
            "studio.html: the front sheet has a press animation but no click "
            "handler — a phone user tapping empty space sees it depress and "
            "release to nothing")

    def test_draft_selector_clears_stale_preview_on_change(self):
        src = read("studio.html")
        # Choosing a different draft must invalidate the preview on screen.
        # The change handler is the honest response; its absence lets stale
        # platform cards read as the new draft's verdict.
        self.assertIn("sel.onchange", src,
                      "studio.html: draft selector has no change handler, so a "
                      "stale preview lingers under a newly-picked draft")

    def test_archive_start_gives_feedback_when_backlog_is_empty(self):
        src = read("studio.html")
        # The button is hidden when the backlog is empty, but a race (a sync
        # landing, another archive finishing) can empty it between the check
        # and the tap. Returning silently there read as "the gold button does
        # nothing", so the empty path must surface a visible note.
        self.assertRegex(
            src, r"if\s*\(\s*!\s*arc\.list\.length\s*\)",
            "studio.html: startArchive must handle the empty-backlog race")
        # The honest sentence for that race — if it disappears, the empty path
        # may have gone silent again.
        self.assertIn("عکس آرشیو‌نشده‌ای نمانده", src)


class TestShellsSurviveABadNetwork(unittest.TestCase):
    def test_font_is_not_render_blocking(self):
        """A blocking font request on a slow or filtered network is a white
        screen for as long as it takes to time out.

        Asserted as the property, not as one implementation of it. This used
        to require `media="print"` outright, which failed the studio shell
        for doing something strictly better — fetching no external font at
        all. `fonts.gstatic.com` does not open from Iran, so a shell that
        ships nothing to fetch has nothing to block on.
        """
        for name in ALL_SHELLS:
            src = read(name)
            with self.subTest(shell=name):
                remote = [ln for ln in src.splitlines()
                          if "<link" in ln and "fonts.googleapis.com" in ln]
                if not remote:
                    continue            # nothing to fetch, nothing to block
                self.assertIn('media="print"', src,
                              f"{name} loads its font as a blocking stylesheet")

    def test_persian_fallback_stack_is_declared(self):
        """When the web font does not arrive, Persian must not land on a
        Latin-first face."""
        for name in ALL_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("--fa:", read(name))

    def test_every_shell_honours_reduced_motion(self):
        for name in ALL_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("prefers-reduced-motion", read(name))

    def test_every_shell_explains_why_it_is_not_live(self):
        """"نمونه" alone made a dead node and a design preview identical."""
        for name in ALL_SHELLS:
            src = read(name)
            with self.subTest(shell=name):
                self.assertIn("REASONS", src)
                for reason in ("unreachable", "rejected"):
                    self.assertIn(f"'{reason}'", src)
                # The no-launch-blob case, under whichever name the shell
                # gives it. The studio shell splits it in two — an SDK that
                # never loaded and a route that signs nothing are different
                # failures with different instructions — and the other three
                # still carry the merged name. Either satisfies this; what is
                # not allowed is having no sentence for it at all.
                self.assertTrue(
                    "'no-shell'" in src
                    or ("'no-sdk'" in src and "'no-initdata'" in src),
                    f"{name} never explains being opened outside the client")


class TestInlineScriptsAreWellFormed(unittest.TestCase):
    """No JS engine here, so this catches the failure that hand-editing a
    300-line inline script actually produces: an unbalanced brace, which
    silently kills the whole block and leaves a dead page."""

    OPEN, PAIR = "([{", {")": "(", "]": "[", "}": "{"}
    PRE = set("(,=:[!&|?{};+-*%~^<>") | {"\n"}

    def balance(self, src: str) -> list[str]:
        stack, out = [], []
        i, line, prev = 0, 1, "\n"
        while i < len(src):
            ch = src[i]
            if ch == "\n":
                line += 1
                i += 1
                continue
            if src[i:i + 2] == "//":
                j = src.find("\n", i)
                i = len(src) if j < 0 else j
                continue
            if src[i:i + 2] == "/*":
                j = src.find("*/", i + 2)
                if j < 0:
                    return [f"line {line}: unterminated comment"]
                line += src.count("\n", i, j)
                i = j + 2
                continue
            if ch in "\"'`":
                j, esc = i + 1, False
                while j < len(src):
                    c = src[j]
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == ch:
                        break
                    elif c == "\n" and ch != "`":
                        return [f"line {line}: unterminated string"]
                    j += 1
                if j >= len(src):
                    return [f"line {line}: unterminated string"]
                line += src.count("\n", i, j)
                i, prev = j + 1, ch
                continue
            if ch == "/" and prev in self.PRE:
                j, esc, cls = i + 1, False, False
                while j < len(src):
                    c = src[j]
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == "[":
                        cls = True
                    elif c == "]":
                        cls = False
                    elif c == "/" and not cls:
                        break
                    elif c == "\n":
                        break
                    j += 1
                if j < len(src) and src[j] == "/":
                    i, prev = j + 1, "/"
                    continue
            if ch in self.OPEN:
                stack.append((ch, line))
            elif ch in self.PAIR:
                if not stack:
                    out.append(f"line {line}: stray {ch!r}")
                elif stack[-1][0] != self.PAIR[ch]:
                    o, ol = stack.pop()
                    out.append(f"line {line}: {ch!r} closes {o!r} from line {ol}")
                else:
                    stack.pop()
            if not ch.isspace():
                prev = ch
            i += 1
        return out + [f"line {ol}: {o!r} never closed" for o, ol in stack]

    def test_all_inline_scripts_balance(self):
        for name in ALL_SHELLS:
            for n, script in enumerate(inline_scripts(read(name))):
                with self.subTest(shell=name, block=n):
                    self.assertEqual(self.balance(script), [])


# ══ what the node actually sends ════════════════════════════════════════
class WiredCase(unittest.TestCase):
    """A real node behind a real ApiApp, driven the way a shell drives it."""

    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        d = self._d.name
        packs = load_dir(PACKS)
        self.registry = TenantRegistry(packs)
        self.node = Node(
            registry=self.registry,
            quota=NodeQuota(estimated_capacity_tokens=180_000_000,
                            utilisation=0.40,
                            shares={t: packs[t].quota_share for t in packs}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            base_closed_gates=("secret_rotation", "partner_precondition"))
        self.app = ApiApp(
            self.registry,
            HostMap(tenants={"z.test": "ziman", "l.test": "lead",
                             "s.test": "studio"},
                    owner_host="panel.test"),
            bot_tokens={"ziman": "t", "lead": "t", "studio": "t",
                        "__owner__": "t"},
            session_secret="s", owner_user_ids=("7",),
            partner_user_ids=PARTNERS, now=lambda: NOW_S,
            questions_for=self.node.questions_for,
            submit_answer=self.node.submit_answer,
            status_for=self.node.status_for,
            owner_queue=self.node.owner_queue,
            owner_decide=self.node.owner_decide,
            owner_status=self.node.owner_status,
            owner_events=self.node.recent_events,
        )

    def tearDown(self):
        self.node.close()
        self._d.cleanup()

    def partner(self, tenant="ziman"):
        return issue_session(tenant, "1", "s", now_epoch_s=NOW_S)

    def owner(self):
        return issue_session("owner", "7", "s", now_epoch_s=NOW_S)

    def call(self, method, path, host, token, body=None):
        return self.app.handle(
            method, path,
            {"host": host, "authorization": "Bearer " + token},
            json.dumps(body).encode() if body is not None else b"")

    def queue_one(self):
        self.node.propose(
            self.registry.scope("ziman"),
            Action(tenant=TenantId("ziman"), name="publish_price",
                   leaves_node=True, reversible=False, touches_money=True),
            {"summary": "انتشار قیمت"}, "item-1")


class TestPartnerFieldsArePresent(WiredCase):
    """Each name below is read by at least one partner shell. A missing one
    renders as `undefined` on a phone and as nothing at all in a test that
    only checks status codes."""

    def test_status_carries_what_the_shells_read(self):
        body = self.call("GET", "/api/v1/status", "z.test", self.partner()).body
        for key in ("tenant", "capacity_per_week", "readiness",
                    "pending_decisions", "held", "safe_mode"):
            self.assertIn(key, body)
        self.assertIn("done", body["readiness"])
        self.assertIn("total", body["readiness"])

    def test_questions_carry_wording_not_just_keys(self):
        body = self.call("GET", "/api/v1/questions", "z.test",
                         self.partner()).body
        self.assertTrue(body["questions"])
        for q in body["questions"]:
            for key in ("key", "kind", "why", "missing", "label", "has_label"):
                self.assertIn(key, q)
            self.assertTrue(q["has_label"],
                            f"{q['key']} has no sentence in its pack")
            self.assertNotEqual(q["label"], q["key"])

    def test_choice_questions_arrive_with_their_options(self):
        """A choice with no options is a card a partner cannot answer."""
        for tenant, host in (("ziman", "z.test"), ("lead", "l.test"),
                             ("studio", "s.test")):
            body = self.call("GET", "/api/v1/questions", host,
                             self.partner(tenant)).body
            for q in body["questions"]:
                if q["kind"] == "choice":
                    with self.subTest(question=q["key"]):
                        self.assertTrue(q.get("options"))

    def test_number_questions_arrive_with_bounds(self):
        for tenant, host in (("ziman", "z.test"), ("lead", "l.test")):
            body = self.call("GET", "/api/v1/questions", host,
                             self.partner(tenant)).body
            for q in body["questions"]:
                if q["kind"] == "number":
                    with self.subTest(question=q["key"]):
                        self.assertIn("min", q)
                        self.assertIn("max", q)

    def test_answer_reply_lets_the_shell_advance(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.capacity_by_family", "value": 7}).body
        self.assertTrue(out["ok"])
        for key in ("readiness", "remaining"):
            self.assertIn(key, out)


class TestAnswersRespectThePack(WiredCase):
    """The pack states a range. Before this, the endpoint took anything, and
    a capacity of one billion became owner-confirmed truth."""

    def test_value_above_the_declared_maximum_is_refused(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.capacity_by_family", "value": 10 ** 9}).body
        self.assertFalse(out["ok"])
        self.assertIn("maximum", out["error"])

    def test_value_below_the_declared_minimum_is_refused(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.capacity_by_family", "value": 0}).body
        self.assertFalse(out["ok"])

    def test_text_where_a_number_belongs_is_refused(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.capacity_by_family", "value": "زیاد"}).body
        self.assertFalse(out["ok"])

    def test_choice_outside_the_offered_set_is_refused(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.delivery_model", "value": "هرچه"}).body
        self.assertFalse(out["ok"])

    def test_an_offered_choice_is_accepted(self):
        out = self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                        {"key": "ops.delivery_model", "value": "پست"}).body
        self.assertTrue(out["ok"])

    def test_a_refused_answer_writes_no_fact(self):
        self.call("POST", "/api/v1/answers", "z.test", self.partner(),
                  {"key": "ops.capacity_by_family", "value": 10 ** 9})
        scope = self.registry.scope("ziman")
        self.assertIsNone(self.node.facts.current(scope, "ops",
                                                  "capacity_by_family"))
        self.assertEqual(
            [e for e in self.node.ledger.read(scope) if e.kind == "FACT"], [])


class TestOwnerFieldsArePresent(WiredCase):
    def test_owner_status_carries_what_the_panel_draws(self):
        body = self.call("GET", "/api/v1/owner/status", "panel.test",
                         self.owner()).body
        for key in ("legs", "closed_gates", "quota", "killed"):
            self.assertIn(key, body)
        for leg in body["legs"]:
            for key in ("tenant", "capacity_per_week", "readiness", "pending",
                        "held", "gates", "blocked_gates", "missing_facts"):
                self.assertIn(key, leg)
        for key in ("node_ceiling", "node_spent", "utilisation", "calls",
                    "capacity_is_estimate", "orchestration_multiplier",
                    "tenants"):
            self.assertIn(key, body["quota"])

    def test_owner_status_reports_the_gates_that_are_actually_shut(self):
        body = self.call("GET", "/api/v1/owner/status", "panel.test",
                         self.owner()).body
        self.assertIn("secret_rotation", body["closed_gates"])
        studio = next(l for l in body["legs"] if l["tenant"] == "studio")
        self.assertIn("partner_precondition", studio["blocked_gates"])

    def test_owner_events_are_the_real_ledger(self):
        self.queue_one()
        body = self.call("GET", "/api/v1/owner/events", "panel.test",
                         self.owner()).body
        self.assertTrue(body["events"])
        for e in body["events"]:
            for key in ("ts", "kind", "tenant", "payload", "hash"):
                self.assertIn(key, e)

    def test_a_partner_cannot_read_the_owner_surface(self):
        for path in ("/api/v1/owner/status", "/api/v1/owner/events"):
            with self.subTest(path=path):
                r = self.call("GET", path, "z.test", self.partner())
                self.assertNotEqual(r.status, 200)

    def test_queue_items_tell_the_panel_which_need_two_confirmations(self):
        self.queue_one()
        body = self.call("GET", "/api/v1/queue", "panel.test",
                         self.owner()).body
        self.assertTrue(body["queue"])
        for item in body["queue"]:
            for key in ("id", "tenant", "kind", "tier", "payload",
                        "created_at", "needs_double_confirm"):
                self.assertIn(key, item)

    def test_a_refused_decision_carries_a_reason_the_panel_can_show(self):
        self.queue_one()
        item = self.call("GET", "/api/v1/queue", "panel.test",
                         self.owner()).body["queue"][0]
        out = self.call("POST", "/api/v1/decide", "panel.test", self.owner(),
                        {"id": item["id"], "approve": True}).body
        self.assertFalse(out["ok"])
        self.assertTrue(out.get("error"))

    def test_the_second_confirmation_is_what_lets_red_through(self):
        self.queue_one()
        item = self.call("GET", "/api/v1/queue", "panel.test",
                         self.owner()).body["queue"][0]
        out = self.call("POST", "/api/v1/decide", "panel.test", self.owner(),
                        {"id": item["id"], "approve": True,
                         "confirmed_twice": True}).body
        self.assertTrue(out["ok"])


# ══ the packs the shells depend on ══════════════════════════════════════
class TestEveryQuestionHasWording(unittest.TestCase):
    def test_no_partner_is_ever_shown_a_bare_fact_key(self):
        """The kernel derives the question; only the pack can word it. A fact
        with no wording renders as `offer.cogs_per_family` on a phone."""
        for name, spec in sorted(load_dir(PACKS).items()):
            for key in spec.required_facts:
                with self.subTest(pack=name, fact=key):
                    self.assertIn(key, spec.question_meta,
                                  f"{name}: {key} has no question wording")
                    self.assertTrue(spec.question_meta[key].get("label"))


if __name__ == "__main__":
    unittest.main()


class TestTheFontIsSelfHosted(unittest.TestCase):
    """`fonts.gstatic.com` does not open reliably from Iran, which is where
    the partners are. A font request that never completes is a wasted
    connection on exactly the network that can least afford one — and as a
    render-blocking stylesheet it was a white screen for as long as the
    timeout took."""

    def test_no_shell_fetches_a_font_from_a_cdn(self):
        for name in ALL_SHELLS:
            src = read(name)
            live = re.sub(r"/\*.*?\*/|<!--.*?-->", "", src, flags=re.S)
            with self.subTest(shell=name):
                self.assertNotIn("fonts.googleapis.com", live)
                self.assertNotIn("fonts.gstatic.com", live)

    def test_every_shell_declares_the_local_face(self):
        for name in ALL_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("/font/vazirmatn.woff2", read(name))

    def test_the_file_is_actually_in_the_repository(self):
        """A `@font-face` pointing at a file nobody shipped is worse than no
        font at all: it looks self-hosted and 404s."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "web", "font", "vazirmatn.woff2")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(4), b"wOF2")

    def test_one_file_covers_every_weight(self):
        """Vazirmatn is a variable font, so 400 and 600 come from the same
        bytes. The first attempt downloaded both and shipped two identical
        45 KB files — double the payload for nothing."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        files = os.listdir(os.path.join(root, "web", "font"))
        self.assertEqual([f for f in files if f.endswith(".woff2")],
                         ["vazirmatn.woff2"])
        for name in ALL_SHELLS:
            with self.subTest(shell=name):
                self.assertRegex(read(name), r"font-weight:\s*100 900")

    def test_text_is_readable_before_the_font_arrives(self):
        """`swap`, so a slow font is a font change rather than a blank
        page — the failure this whole item is about."""
        for name in ALL_SHELLS:
            with self.subTest(shell=name):
                self.assertIn("font-display:swap", read(name))

    def test_the_licence_travels_with_it(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        licence = os.path.join(root, "web", "font", "LICENSE.txt")
        self.assertTrue(os.path.isfile(licence))
        with open(licence, encoding="utf-8") as fh:
            self.assertIn("SIL Open Font License", fh.read())


class TestP1SurfacePins(unittest.TestCase):
    """The P1 upgrade surface is pinned: what the panels now draw.

    These are property assertions, not content tests: the point is that
    panel.html calls drawInbox with the observability route, lead.html
    renders score_detail, and neither regresses to raw numbers.
    """

    def test_panel_draws_observability(self):
        src = read("panel.html")
        self.assertIn("/api/v1/owner/observability", src)
        self.assertIn("drawInbox", src)
        self.assertIn("inboxChip", src)

    def test_panel_inbox_shows_counts_without_vendor(self):
        """Finding 45: counts are always drawn; vendor chip is separate."""
        src = read("panel.html")
        self.assertIn("vendors_connected", src)
        # The empty branch must still render the tenant grid.
        self.assertIn("Object.entries(tenants)", src)

    def test_lead_renders_score_detail(self):
        src = read("lead.html")
        self.assertIn("score_detail", src)
        self.assertIn("اولویت بالا", src)

    def test_observability_route_is_owner_read(self):
        """The route must be inside the owner surface (auth required)."""
        api = open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ofn", "adapters", "http_api.py"), encoding="utf-8").read()
        self.assertIn('path == "/api/v1/owner/observability"', api)


class TestP2SurfacePins(unittest.TestCase):
    """Phase I surface pins: ARIA tabs, lead poll, dedup, ziman message."""

    def test_panel_tabs_have_aria(self):
        src = read("panel.html")
        self.assertIn('role="tablist"', src)
        self.assertIn('role="tab"', src)
        self.assertIn("aria-selected", src)

    def test_lead_has_poll_and_visibility_stop(self):
        src = read("lead.html")
        self.assertIn("setInterval(poll, 60000)", src)
        self.assertIn("visibilitychange", src)

    def test_lead_dedups_recent(self):
        src = read("lead.html")
        self.assertIn("__leadDrawnIds", src)
        self.assertIn("mainIds.has", src)

    def test_ziman_channel_block_message_explains(self):
        src = read("ziman.html")
        self.assertIn("کارمزد این کانال هنوز ثبت نشده", src)
        self.assertIn("مالک حداقل یک کانال", src)
