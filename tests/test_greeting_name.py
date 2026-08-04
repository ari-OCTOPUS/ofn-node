"""Where a partner's name comes from, and where it must not.

The shells used to carry the name in their markup. That meant the name was in
the bytes served to anyone who reached the URL — before the node had any idea
who was asking, and regardless of whether they ever authenticated. It was not
a data breach; it was one given name, and on `lead` a surname. It broke a
smaller and more load-bearing rule: the page said something while it was
still blind.

Nothing in the suite found it. The tests read the header and asserted the
words in it were the right words, which is a question about content when the
bug was about audience. It was found by opening the real URL in an ordinary
browser and reading what came back.

The name now travels on the auth response — after the signature and the
allowlist — and is written into the page by script.
"""

from __future__ import annotations

import os
import re
import unittest

from ofn.kernel.auth import verify_init_data

from .test_auth import BOT_TOKEN, NOW, sign

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
SHELLS = ("ziman.html", "lead.html", "studio.html", "panel.html")

# The real people this node is for. None of them may appear in a file that is
# served before anybody has proved who they are.
PEOPLE = ("ملیحه", "عباس", "اسدی", "سبا")


def fields(user_json: str, auth_date: int = NOW) -> dict[str, str]:
    return {"auth_date": str(auth_date), "query_id": "AAxyz", "user": user_json}


class TestNoShellNamesAPerson(unittest.TestCase):
    def test_no_partner_name_is_compiled_into_any_shell(self):
        for name in SHELLS:
            with self.subTest(shell=name):
                src = open(os.path.join(WEB, name), encoding="utf-8").read()
                for person in PEOPLE:
                    # Comments are allowed to name what they warn about; the
                    # rest of the file is not.
                    stripped = re.sub(r"<!--.*?-->|/\*.*?\*/", "", src, flags=re.S)
                    self.assertNotIn(
                        person, stripped,
                        f"{name} names {person} in markup or script — it is "
                        f"served before anyone has authenticated")

    def test_no_shell_title_names_a_person(self):
        """The title is the first thing served and the last thing anyone
        thinks to check."""
        for name in SHELLS:
            with self.subTest(shell=name):
                src = open(os.path.join(WEB, name), encoding="utf-8").read()
                title = re.search(r"<title>(.*?)</title>", src, re.S)
                self.assertIsNotNone(title)
                for person in PEOPLE:
                    self.assertNotIn(person, title.group(1))

    def test_partner_shells_take_the_name_from_the_session(self):
        for name in ("ziman.html", "lead.html", "studio.html"):
            with self.subTest(shell=name):
                src = open(os.path.join(WEB, name), encoding="utf-8").read()
                self.assertIn("out.first_name", src)
                self.assertIn("greet(OFN.who)", src)

    def test_the_name_is_written_as_text_not_markup(self):
        """It arrives inside a signed payload, which makes it trustworthy
        about *who*, not about what characters it contains."""
        for name in ("ziman.html", "lead.html", "studio.html"):
            with self.subTest(shell=name):
                src = open(os.path.join(WEB, name), encoding="utf-8").read()
                body = re.search(r"function greet\(name\)\s*\{(.*?)\n\}", src, re.S)
                self.assertIsNotNone(body, f"{name}: no greet()")
                self.assertIn("textContent", body.group(1))
                self.assertNotIn("innerHTML", body.group(1))


class TestFirstNameComesOutOfTheSignedPayload(unittest.TestCase):
    def test_a_plain_name_is_read(self):
        u = verify_init_data(
            sign(fields('{"id":7,"first_name":"Sara","username":"s"}')),
            BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "Sara")

    def test_an_escaped_persian_name_is_decoded(self):
        """This is the wire form, not a contrived one: the platform escapes
        every non-ASCII character, so every Persian name arrives like this.
        Left raw the partner would be greeted as `\\u0645\\u0644...`."""
        escaped = r'{"id":7,"first_name":"ملیحه"}'
        u = verify_init_data(sign(fields(escaped)), BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "ملیحه")

    def test_an_unescaped_name_is_left_alone(self):
        """Some clients send it raw. Both forms have to work."""
        u = verify_init_data(sign(fields('{"id":7,"first_name":"ملیحه"}')),
                             BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "ملیحه")

    def test_a_name_containing_an_emoji_survives(self):
        """Escaped as a surrogate pair. Decoding each half on its own gives
        two unpaired code points, and the resulting string cannot be encoded
        back out — the greeting would raise instead of rendering."""
        escaped = r'{"id":7,"first_name":"Sara 🌸"}'
        u = verify_init_data(sign(fields(escaped)), BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "Sara 🌸")
        u.first_name.encode("utf-8")      # would raise on lone surrogates

    def test_a_backslash_escape_does_not_survive_as_a_backslash(self):
        escaped = r'{"id":7,"first_name":"A\\B"}'
        u = verify_init_data(sign(fields(escaped)), BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "A\\B")

    def test_a_missing_first_name_is_empty_not_an_error(self):
        """Nobody is locked out for having an unusual profile."""
        u = verify_init_data(sign(fields('{"id":7,"username":"s"}')),
                             BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "")

    def test_the_surname_is_never_read(self):
        """A given name says hello. A surname identifies somebody outside
        their own circle, and no screen here needs that."""
        u = verify_init_data(
            sign(fields('{"id":7,"first_name":"Abbas","last_name":"Asadi"}')),
            BOT_TOKEN, now_epoch_s=NOW)
        self.assertEqual(u.first_name, "Abbas")
        self.assertNotIn("Asadi", repr(u.first_name))

    def test_a_name_in_an_unsigned_copy_is_not_believed(self):
        """Only the signed `user` field is read. Tampering with it breaks the
        signature, so there is no path by which a caller chooses the name the
        page will greet them with."""
        f = sign(fields('{"id":7,"first_name":"Sara"}'))
        f["user"] = '{"id":7,"first_name":"Somebody Else"}'
        from ofn.kernel.auth import AuthError
        with self.assertRaises(AuthError):
            verify_init_data(f, BOT_TOKEN, now_epoch_s=NOW)


if __name__ == "__main__":
    unittest.main()
