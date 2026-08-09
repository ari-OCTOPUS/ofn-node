"""A container that starts hidden must have something on the boot path show it.

`lead.html` carries `<div class="crm" id="leadcrm" hidden>`. The only code that
clears that attribute is `refreshLeadCrm()`, and `boot()` never called it — so
the partner opened the app and the CRM was never there. Everything else about
it worked: the endpoint answered, the renderer was correct, the styles existed.
The audit found it by reading; nothing failed, because nothing checked that the
renderer was reached.

That is a shape, not an incident. Any shell can grow a panel that is built,
styled, tested in isolation and never called, and the symptom — a section that
simply is not on the screen — looks like a design decision.

So: for every element that ships with `hidden`, find the function that clears
it, and require that function to be reachable from `boot()`.

What this does not do: reachability here is textual, over function names. It
cannot see a call made through a variable or a dispatch table, so a shell doing
that would need an entry in ALLOWED with the reason. It does not prove the call
runs — only that the wiring exists. `test_shell_boot_order` covers the other
half, that scripts evaluate in the right order.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
SHELLS = ("panel.html", "ziman.html", "lead.html", "studio.html")

# Containers whose reveal is genuinely not on the boot path, with the reason.
# An entry here is a claim that a human decides to show this, not the shell.
ALLOWED: dict[tuple[str, str], str] = {
    ("lead.html", "state"):
        "status banner, revealed by showState() on a connection failure",
    ("panel.html", "conn"):
        "connection-failure panel, revealed by showDead()",
    ("panel.html", "stale"):
        "staleness warning, revealed when a poll fails",
    ("panel.html", "killBanner"):
        "kill-switch banner, revealed by renderKill() after an owner action",
    ("studio.html", "state"):
        "status banner, revealed on a connection failure",
}


def script_text(html: str) -> str:
    return "\n".join(re.findall(r"<script>(.*?)</script>", html, re.DOTALL))


def hidden_ids(html: str) -> set[str]:
    """Elements that ship with the `hidden` attribute and carry an id."""
    out = set()
    for tag in re.findall(r"<(?:div|section|form|span)\b[^>]*>", html, re.I):
        if re.search(r"\bhidden\b", tag):
            m = re.search(r'id="([\w-]+)"', tag)
            if m:
                out.add(m.group(1))
    return out


def functions(js: str) -> dict[str, str]:
    """Function name -> body, for `function f(){}` and `const f = ... => {}`."""
    out = {}
    for m in re.finditer(r"(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{", js):
        out[m.group(1)] = _brace_body(js, m.end())
    for m in re.finditer(
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{", js):
        out[m.group(1)] = _brace_body(js, m.end())
    return out


def _brace_body(js: str, start: int) -> str:
    depth, i = 1, start
    while depth and i < len(js):
        depth += (js[i] == "{") - (js[i] == "}")
        i += 1
    return js[start:i]


def reachable_from_boot(funcs: dict[str, str]) -> set[str]:
    """Names textually reachable from boot(), following call edges."""
    seen, stack = set(), ["boot"]
    while stack:
        name = stack.pop()
        if name in seen or name not in funcs:
            continue
        seen.add(name)
        for other in funcs:
            if other != name and re.search(rf"\b{re.escape(other)}\s*\(",
                                           funcs[name]):
                stack.append(other)
    return seen


def revealer(funcs: dict[str, str], element_id: str) -> str | None:
    """The function that clears `hidden` on this id, if one does."""
    direct = re.compile(
        rf"""getElementById\(\s*['"]{re.escape(element_id)}['"]\s*\)\.hidden\s*=\s*false""")
    for name, body in funcs.items():
        if direct.search(body):
            return name
        # `const box = document.getElementById('x'); ... box.hidden = false`
        m = re.search(
            rf"""(\w+)\s*=\s*document\.getElementById\(\s*['"]{re.escape(element_id)}['"]\s*\)""",
            body)
        if m and re.search(rf"\b{re.escape(m.group(1))}\.hidden\s*=\s*false", body):
            return name
    return None


class TestHiddenContainersAreReached(unittest.TestCase):
    def test_every_hidden_container_is_revealed_from_boot(self):
        problems = []
        for shell in SHELLS:
            html = (WEB / shell).read_text(encoding="utf-8")
            funcs = functions(script_text(html))
            self.assertIn("boot", funcs, f"{shell} has no boot()")
            live = reachable_from_boot(funcs)
            for element_id in sorted(hidden_ids(html)):
                if (shell, element_id) in ALLOWED:
                    continue
                fn = revealer(funcs, element_id)
                if fn is None:
                    continue          # nothing ever shows it; a separate concern
                if fn not in live:
                    problems.append(
                        f"{shell}: #{element_id} is only revealed by {fn}(), "
                        f"which boot() never reaches")
        self.assertEqual(problems, [], "\n  " + "\n  ".join(problems))

    def test_allowlist_entries_are_real(self):
        """An excuse for an element that no longer exists hides a regression."""
        for (shell, element_id), reason in ALLOWED.items():
            html = (WEB / shell).read_text(encoding="utf-8")
            self.assertIn(element_id, hidden_ids(html),
                          f"{shell}: #{element_id} is excused but not hidden")
            self.assertGreater(len(reason), 20,
                               f"{shell}: #{element_id} excused without a reason")


if __name__ == "__main__":
    unittest.main()
