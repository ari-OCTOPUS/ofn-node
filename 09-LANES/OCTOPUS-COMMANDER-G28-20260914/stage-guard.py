"""stage-guard v1 (2026-09-14, lane OCTOPUS-COMMANDER-G28-20260914).

Standing regression guard for the G30 defect class at the artifact boundary:
the patch-document JSON path decodes the escape \\b (and \\u0008 etc.) into a
real backspace byte inside replacement strings, and text-mode staging can also
flip EOLs. This tool validates the FINAL staged bytes before any deploy:
  1. no control bytes except LF (and TAB if --allow-tab);
  2. EOL purity: the file is uniformly LF or uniformly CRLF, never mixed;
  3. every re.compile(...) pattern in the file still compiles and contains no
     control characters;
  4. ast.parse passes (syntax gate).
Exit 0 = clean; exit 1 = violation (printed). Recommended wiring: call from
coding_worker apply/staging before a package is proposed (open item - do not
deploy the worker change without its own slot).
"""
import ast
import pathlib
import re
import sys


def scan(path: str, allow_tab: bool = False) -> int:
    p = pathlib.Path(path)
    raw = p.read_bytes()
    allowed = {0x0a} | ({0x09} if allow_tab else set())
    bad = [(i, c) for i, c in enumerate(raw) if c < 0x20 and c not in allowed]
    if bad:
        print("STAGE-GUARD FAIL %s: %d control byte(s), first at %d (0x%02x) ctx=%r"
              % (path, len(bad), bad[0][0], bad[0][1],
                 raw[max(0, bad[0][0] - 30):bad[0][0] + 30]))
        return 1
    crlf = raw.count(b"\r\n")
    lone_lf = raw.count(b"\n") - crlf
    if crlf and lone_lf:
        print("STAGE-GUARD FAIL %s: mixed EOLs (crlf=%d lone_lf=%d)"
              % (path, crlf, lone_lf))
        return 1
    src = raw.decode("utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print("STAGE-GUARD FAIL %s: ast.parse %s" % (path, e))
        return 1
    n_pat = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "compile" \
                and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "compile":
            continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "compile":
            args = node.args
            if args and isinstance(args[0], ast.Constant) \
                    and isinstance(args[0].value, str):
                pat = args[0].value
                n_pat += 1
                if any(ord(ch) < 0x20 and ch not in "\t\n" for ch in pat):
                    print("STAGE-GUARD FAIL %s: re.compile pattern carries a "
                          "control char: %r" % (path, pat[:60]))
                    return 1
                try:
                    re.compile(pat)
                except re.error as e:
                    print("STAGE-GUARD FAIL %s: pattern %r does not compile: %s"
                          % (path, pat[:60], e))
                    return 1
    print("STAGE-GUARD OK %s bytes=%d eol=%s patterns=%d"
          % (path, len(raw), "CRLF" if crlf else "LF", n_pat))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: stage-guard.py <file.py> [--allow-tab]")
        sys.exit(2)
    sys.exit(scan(sys.argv[1], "--allow-tab" in sys.argv))
